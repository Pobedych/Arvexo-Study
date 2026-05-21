import hashlib
import hmac
import secrets
import time
from datetime import datetime
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.ai_usage import AIUsage
from app.models.auth_identity import AuthIdentity
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.task import TaskAttempt
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, TelegramAuthRequest, UserRead, UserUpdateRequest
from app.services.auth import (
    SESSION_COOKIE,
    create_access_token,
    get_current_user,
    get_optional_user,
    get_user_by_email,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])
OAUTH_STATE_COOKIE = "arvexo_oauth_state"
OAUTH_STATE_MAX_AGE = 10 * 60


def set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )


def oauth_redirect_uri(provider: str) -> str:
    settings = get_settings()
    return f"{settings.public_api_url.rstrip('/')}/auth/{provider}/callback"


def oauth_error_redirect(reason: str) -> RedirectResponse:
    settings = get_settings()
    return RedirectResponse(f"{settings.public_site_url.rstrip('/')}/login?oauth_error={reason}", status_code=status.HTTP_303_SEE_OTHER)


def oauth_state_value(provider: str, mode: str, state: str) -> str:
    return f"{provider}:{mode}:{state}"


def set_oauth_state_cookie(response: Response, provider: str, state: str, mode: str = "login") -> None:
    settings = get_settings()
    response.set_cookie(
        key=OAUTH_STATE_COOKIE,
        value=oauth_state_value(provider, mode, state),
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=OAUTH_STATE_MAX_AGE,
        path="/auth",
    )


def clear_oauth_state_cookie(response: Response) -> None:
    response.delete_cookie(OAUTH_STATE_COOKIE, path="/auth")


def get_oauth_state_mode(request: Request, provider: str, state: str | None) -> str | None:
    expected = request.cookies.get(OAUTH_STATE_COOKIE)
    if not state:
        return None
    for mode in ("login", "connect"):
        if expected == oauth_state_value(provider, mode, state):
            return mode
    return None


def login_redirect(user: User) -> RedirectResponse:
    settings = get_settings()
    response = RedirectResponse(f"{settings.public_site_url.rstrip('/')}/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    set_session_cookie(response, create_access_token(user))
    clear_oauth_state_cookie(response)
    return response


def connect_redirect(provider: str) -> RedirectResponse:
    settings = get_settings()
    response = RedirectResponse(
        f"{settings.public_site_url.rstrip('/')}/profile?connected={provider}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
    clear_oauth_state_cookie(response)
    return response


def identity_conflict_redirect(provider: str) -> RedirectResponse:
    settings = get_settings()
    response = RedirectResponse(
        f"{settings.public_site_url.rstrip('/')}/profile?connect_error={provider}_already_linked",
        status_code=status.HTTP_303_SEE_OTHER,
    )
    clear_oauth_state_cookie(response)
    return response


def get_identity(db: Session, provider: str, provider_user_id: str) -> AuthIdentity | None:
    return (
        db.query(AuthIdentity)
        .filter(AuthIdentity.provider == provider, AuthIdentity.provider_user_id == provider_user_id)
        .one_or_none()
    )


def attach_identity(
    db: Session,
    user: User,
    *,
    provider: str,
    provider_user_id: str,
    provider_email: str | None = None,
) -> AuthIdentity:
    identity = get_identity(db, provider, provider_user_id)
    if identity:
        if identity.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"{provider} account is already linked")
        if provider_email and identity.provider_email != provider_email:
            identity.provider_email = provider_email
        return identity

    identity = AuthIdentity(
        user_id=user.id,
        provider=provider,
        provider_user_id=provider_user_id,
        provider_email=provider_email,
    )
    db.add(identity)
    return identity


def verify_telegram_payload(payload: TelegramAuthRequest) -> str:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Telegram login is not configured")

    if int(time.time()) - payload.auth_date > settings.telegram_login_max_age_seconds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Telegram auth data expired")

    data = payload.model_dump()
    received_hash = str(data.pop("hash"))
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(data.items()) if value is not None)
    secret_key = hashlib.sha256(settings.telegram_bot_token.encode("utf-8")).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram auth data")

    return str(payload.id)


def upsert_oauth_user(
    db: Session,
    *,
    email: str,
    name: str,
    provider: str,
    provider_user_id: str,
    avatar_url: str | None = None,
    last_name: str | None = None,
) -> User:
    identity = get_identity(db, provider, provider_user_id)
    user = identity.user if identity else get_user_by_email(db, email)
    if user:
        if not user.is_active or user.is_banned:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is blocked")
        user.last_login_at = datetime.utcnow()
        if avatar_url and not user.avatar_url:
            user.avatar_url = avatar_url
        if last_name and not user.last_name:
            user.last_name = last_name
        attach_identity(db, user, provider=provider, provider_user_id=provider_user_id, provider_email=email)
        db.commit()
        db.refresh(user)
        return user

    user = User(
        email=email,
        name=name or "Ученик",
        last_name=last_name,
        avatar_url=avatar_url,
        password_hash=None,
        auth_provider=provider,
        role="student",
        last_login_at=datetime.utcnow(),
    )
    db.add(user)
    db.flush()
    attach_identity(db, user, provider=provider, provider_user_id=provider_user_id, provider_email=email)
    db.commit()
    db.refresh(user)
    return user


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    email = payload.email.strip().lower()
    if get_user_by_email(db, email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=email,
        name=payload.name.strip(),
        password_hash=hash_password(payload.password),
        auth_provider="email",
        role="student",
        last_login_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    set_session_cookie(response, create_access_token(user))
    return AuthResponse(user=UserRead.model_validate(user))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    user = get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active or user.is_banned:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is blocked")

    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    set_session_cookie(response, create_access_token(user))
    return AuthResponse(user=UserRead.model_validate(user))


@router.get("/google")
def google_oauth_start() -> RedirectResponse:
    settings = get_settings()
    if not settings.google_client_id or not settings.google_client_secret:
        return oauth_error_redirect("google_not_configured")

    state = secrets.token_urlsafe(32)
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": oauth_redirect_uri("google"),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }
    response = RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}")
    set_oauth_state_cookie(response, "google", state)
    return response


@router.get("/google/connect")
def google_oauth_connect(request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    get_current_user(request, db)
    settings = get_settings()
    if not settings.google_client_id or not settings.google_client_secret:
        return oauth_error_redirect("google_not_configured")

    state = secrets.token_urlsafe(32)
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": oauth_redirect_uri("google"),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }
    response = RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}")
    set_oauth_state_cookie(response, "google", state, mode="connect")
    return response


@router.get("/google/callback")
def google_oauth_callback(
    request: Request,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    settings = get_settings()
    if error or not code:
        return oauth_error_redirect("google_denied")
    mode = get_oauth_state_mode(request, "google", state)
    if not mode:
        return oauth_error_redirect("invalid_state")

    try:
        with httpx.Client(timeout=10) as client:
            token_response = client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": oauth_redirect_uri("google"),
                },
            )
            token_response.raise_for_status()
            access_token = token_response.json().get("access_token")
            if not access_token:
                return oauth_error_redirect("google_token")

            profile_response = client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            profile_response.raise_for_status()
            profile = profile_response.json()
    except httpx.HTTPError:
        return oauth_error_redirect("google_token")

    email = str(profile.get("email") or "").strip().lower()
    if not email:
        return oauth_error_redirect("google_email")
    provider_user_id = str(profile.get("sub") or "").strip()
    if not provider_user_id:
        return oauth_error_redirect("google_token")

    if mode == "connect":
        current_user = get_optional_user(request, db)
        if not current_user:
            return oauth_error_redirect("invalid_state")
        try:
            attach_identity(db, current_user, provider="google", provider_user_id=provider_user_id, provider_email=email)
        except HTTPException:
            return identity_conflict_redirect("google")
        if profile.get("picture") and not current_user.avatar_url:
            current_user.avatar_url = profile.get("picture")
        if profile.get("family_name") and not current_user.last_name:
            current_user.last_name = profile.get("family_name")
        db.commit()
        return connect_redirect("google")

    user = upsert_oauth_user(
        db,
        email=email,
        name=str(profile.get("given_name") or profile.get("name") or email.split("@")[0]),
        last_name=profile.get("family_name"),
        avatar_url=profile.get("picture"),
        provider="google",
        provider_user_id=provider_user_id,
    )
    return login_redirect(user)


@router.get("/yandex")
def yandex_oauth_start() -> RedirectResponse:
    settings = get_settings()
    if not settings.yandex_client_id or not settings.yandex_client_secret:
        return oauth_error_redirect("yandex_not_configured")

    state = secrets.token_urlsafe(32)
    params = {
        "client_id": settings.yandex_client_id,
        "redirect_uri": oauth_redirect_uri("yandex"),
        "response_type": "code",
        "scope": "login:email login:info",
        "state": state,
    }
    response = RedirectResponse(f"https://oauth.yandex.ru/authorize?{urlencode(params)}")
    set_oauth_state_cookie(response, "yandex", state)
    return response


@router.get("/yandex/connect")
def yandex_oauth_connect(request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    get_current_user(request, db)
    settings = get_settings()
    if not settings.yandex_client_id or not settings.yandex_client_secret:
        return oauth_error_redirect("yandex_not_configured")

    state = secrets.token_urlsafe(32)
    params = {
        "client_id": settings.yandex_client_id,
        "redirect_uri": oauth_redirect_uri("yandex"),
        "response_type": "code",
        "scope": "login:email login:info",
        "state": state,
    }
    response = RedirectResponse(f"https://oauth.yandex.ru/authorize?{urlencode(params)}")
    set_oauth_state_cookie(response, "yandex", state, mode="connect")
    return response


@router.get("/yandex/callback")
def yandex_oauth_callback(
    request: Request,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    settings = get_settings()
    if error or not code:
        return oauth_error_redirect("yandex_denied")
    mode = get_oauth_state_mode(request, "yandex", state)
    if not mode:
        return oauth_error_redirect("invalid_state")

    try:
        with httpx.Client(timeout=10) as client:
            token_response = client.post(
                "https://oauth.yandex.ru/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": settings.yandex_client_id,
                    "client_secret": settings.yandex_client_secret,
                    "redirect_uri": oauth_redirect_uri("yandex"),
                },
            )
            token_response.raise_for_status()
            access_token = token_response.json().get("access_token")
            if not access_token:
                return oauth_error_redirect("yandex_token")

            profile_response = client.get(
                "https://login.yandex.ru/info",
                params={"format": "json"},
                headers={"Authorization": f"OAuth {access_token}"},
            )
            profile_response.raise_for_status()
            profile = profile_response.json()
    except httpx.HTTPError:
        return oauth_error_redirect("yandex_token")

    email = str(profile.get("default_email") or "").strip().lower()
    if not email:
        emails = profile.get("emails") or []
        email = str(emails[0]).strip().lower() if emails else ""
    if not email:
        return oauth_error_redirect("yandex_email")
    provider_user_id = str(profile.get("id") or "").strip()
    if not provider_user_id:
        return oauth_error_redirect("yandex_token")

    if mode == "connect":
        current_user = get_optional_user(request, db)
        if not current_user:
            return oauth_error_redirect("invalid_state")
        try:
            attach_identity(db, current_user, provider="yandex", provider_user_id=provider_user_id, provider_email=email)
        except HTTPException:
            return identity_conflict_redirect("yandex")
        if profile.get("last_name") and not current_user.last_name:
            current_user.last_name = profile.get("last_name")
        db.commit()
        return connect_redirect("yandex")

    user = upsert_oauth_user(
        db,
        email=email,
        name=str(profile.get("first_name") or profile.get("display_name") or profile.get("login") or email.split("@")[0]),
        last_name=profile.get("last_name"),
        avatar_url=None,
        provider="yandex",
        provider_user_id=provider_user_id,
    )
    return login_redirect(user)


@router.post("/telegram", response_model=AuthResponse)
def telegram_login(payload: TelegramAuthRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    telegram_id = verify_telegram_payload(payload)
    linked_user = db.query(User).filter(User.telegram_id == telegram_id).one_or_none()
    identity = get_identity(db, "telegram", telegram_id)

    user = identity.user if identity else linked_user
    if not user:
        name_parts = [payload.first_name, payload.last_name]
        name = " ".join(part.strip() for part in name_parts if part and part.strip()) or payload.username or "Telegram user"
        user = User(
            email=f"telegram-{telegram_id}@telegram.study.arvexo.ru",
            name=name,
            avatar_url=payload.photo_url,
            telegram_id=telegram_id,
            auth_provider="telegram",
            role="student",
            last_login_at=datetime.utcnow(),
        )
        db.add(user)
        db.flush()
        attach_identity(db, user, provider="telegram", provider_user_id=telegram_id, provider_email=None)
    else:
        user.last_login_at = datetime.utcnow()
        if payload.photo_url:
            user.avatar_url = payload.photo_url
        if not user.telegram_id:
            user.telegram_id = telegram_id
        attach_identity(db, user, provider="telegram", provider_user_id=telegram_id, provider_email=None)

    db.commit()
    db.refresh(user)

    set_session_cookie(response, create_access_token(user))
    return AuthResponse(user=UserRead.model_validate(user))


@router.post("/telegram/connect", response_model=AuthResponse)
def telegram_connect(payload: TelegramAuthRequest, request: Request, db: Session = Depends(get_db)) -> AuthResponse:
    current_user = get_current_user(request, db)
    telegram_id = verify_telegram_payload(payload)
    linked_user = db.query(User).filter(User.telegram_id == telegram_id).one_or_none()
    identity = get_identity(db, "telegram", telegram_id)

    if linked_user and linked_user.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Telegram account is already linked")
    if identity and identity.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Telegram account is already linked")

    current_user.telegram_id = telegram_id
    if payload.photo_url and not current_user.avatar_url:
        current_user.avatar_url = payload.photo_url
    attach_identity(db, current_user, provider="telegram", provider_user_id=telegram_id, provider_email=None)
    db.commit()
    db.refresh(current_user)
    return AuthResponse(user=UserRead.model_validate(current_user))


@router.post("/logout")
def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"status": "ok"}


@router.get("/me", response_model=UserRead)
def me(request: Request, db: Session = Depends(get_db)) -> User:
    return get_current_user(request, db)


@router.patch("/me", response_model=UserRead)
def update_me(payload: UserUpdateRequest, request: Request, db: Session = Depends(get_db)) -> User:
    user = get_current_user(request, db)
    user.name = payload.name.strip()
    user.last_name = payload.last_name.strip() if payload.last_name and payload.last_name.strip() else None
    user.phone = payload.phone.strip() if payload.phone and payload.phone.strip() else None
    db.commit()
    db.refresh(user)
    return user


@router.delete("/me")
def delete_me(request: Request, response: Response, db: Session = Depends(get_db)) -> dict[str, str]:
    user = get_current_user(request, db)

    db.query(AuthIdentity).filter(AuthIdentity.user_id == user.id).delete(synchronize_session=False)
    db.query(AIUsage).filter(AIUsage.user_id == user.id).delete(synchronize_session=False)
    db.query(TaskAttempt).filter(TaskAttempt.user_id == user.id).delete(synchronize_session=False)
    db.query(Subscription).filter(Subscription.user_id == user.id).delete(synchronize_session=False)
    db.query(Payment).filter(Payment.user_id == user.id).delete(synchronize_session=False)
    db.delete(user)
    db.commit()

    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"status": "deleted"}
