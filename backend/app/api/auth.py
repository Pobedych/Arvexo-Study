import hashlib
import hmac
import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, TelegramAuthRequest, UserRead, UserUpdateRequest
from app.services.auth import (
    SESSION_COOKIE,
    create_access_token,
    get_current_user,
    get_user_by_email,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


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


@router.post("/telegram", response_model=AuthResponse)
def telegram_login(payload: TelegramAuthRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
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

    telegram_id = str(payload.id)
    user = db.query(User).filter(User.telegram_id == telegram_id).one_or_none()
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
    else:
        user.last_login_at = datetime.utcnow()
        if payload.photo_url:
            user.avatar_url = payload.photo_url

    db.commit()
    db.refresh(user)

    set_session_cookie(response, create_access_token(user))
    return AuthResponse(user=UserRead.model_validate(user))


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
