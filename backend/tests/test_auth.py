from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.auth import OAuthEmailNotVerified, upsert_oauth_user
from app.core.time import utc_now
from app.models.auth_identity import AuthIdentity
from app.models.subscription import Subscription


def test_register_login_me_logout_flow(client: TestClient) -> None:
    email = f"new-user-{uuid4()}@example.com"
    password = "strong-password"

    register_response = client.post(
        "/auth/register",
        json={"email": email, "password": password, "name": "Новый ученик"},
    )
    assert register_response.status_code == 201
    assert register_response.json()["user"]["email"] == email

    me_response = client.get("/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["name"] == "Новый ученик"

    logout_response = client.post("/auth/logout")
    assert logout_response.status_code == 200

    unauthorized_response = client.get("/auth/me")
    assert unauthorized_response.status_code == 401

    login_response = client.post("/auth/login", json={"email": email, "password": password})
    assert login_response.status_code == 200
    assert login_response.json()["user"]["email"] == email


def test_register_rejects_blank_name_after_trim(client: TestClient) -> None:
    register_response = client.post(
        "/auth/register",
        json={"email": f"blank-name-{uuid4()}@example.com", "password": "strong-password", "name": "   "},
    )

    assert register_response.status_code == 422


def test_stats_ignores_client_plan_query(client: TestClient) -> None:
    email = f"plan-check-{uuid4()}@example.com"
    register_response = client.post(
        "/auth/register",
        json={"email": email, "password": "strong-password", "name": "Plan Check"},
    )
    assert register_response.status_code == 201

    stats_response = client.get("/stats/me?plan=pro")
    assert stats_response.status_code == 200
    assert stats_response.json()["ai_daily_limit"] == 5


def test_stats_handles_timezone_aware_subscription_dates(
    client: TestClient,
    db_session: Session,
) -> None:
    email = f"aware-subscription-{uuid4()}@example.com"
    register_response = client.post(
        "/auth/register",
        json={"email": email, "password": "strong-password", "name": "Aware Subscription"},
    )
    assert register_response.status_code == 201
    user_id = register_response.json()["user"]["id"]
    db_session.add(
        Subscription(
            user_id=user_id,
            plan="pro",
            status="active",
            started_at=utc_now(),
            ends_at=utc_now() + timedelta(days=1),
        )
    )
    db_session.commit()

    stats_response = client.get("/stats/me")

    assert stats_response.status_code == 200
    assert stats_response.json()["ai_daily_limit"] == 150


def test_delete_me_removes_session(client: TestClient) -> None:
    email = f"delete-me-{uuid4()}@example.com"
    register_response = client.post(
        "/auth/register",
        json={"email": email, "password": "strong-password", "name": "Delete Me"},
    )
    assert register_response.status_code == 201

    delete_response = client.delete("/auth/me")
    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == "deleted"

    me_response = client.get("/auth/me")
    assert me_response.status_code == 401

    login_response = client.post("/auth/login", json={"email": email, "password": "strong-password"})
    assert login_response.status_code == 401


def test_update_me_rejects_blank_name_after_trim(client: TestClient) -> None:
    email = f"profile-blank-name-{uuid4()}@example.com"
    register_response = client.post(
        "/auth/register",
        json={"email": email, "password": "strong-password", "name": "Profile User"},
    )
    assert register_response.status_code == 201

    update_response = client.patch("/auth/me", json={"name": "   "})

    assert update_response.status_code == 422


def test_oauth_does_not_auto_link_existing_user_with_unverified_email(
    client: TestClient,
    db_session: Session,
) -> None:
    email = f"oauth-unverified-{uuid4()}@example.com"
    register_response = client.post(
        "/auth/register",
        json={"email": email, "password": "strong-password", "name": "OAuth User"},
    )
    assert register_response.status_code == 201

    with pytest.raises(OAuthEmailNotVerified):
        upsert_oauth_user(
            db_session,
            email=email,
            name="OAuth User",
            provider="google",
            provider_user_id=f"google-{uuid4()}",
            email_verified=False,
        )

    identity = db_session.query(AuthIdentity).filter(AuthIdentity.provider_email == email).one_or_none()
    assert identity is None


def test_oauth_auto_links_existing_user_with_verified_email(
    client: TestClient,
    db_session: Session,
) -> None:
    email = f"oauth-verified-{uuid4()}@example.com"
    register_response = client.post(
        "/auth/register",
        json={"email": email, "password": "strong-password", "name": "OAuth User"},
    )
    assert register_response.status_code == 201
    user_id = register_response.json()["user"]["id"]

    user = upsert_oauth_user(
        db_session,
        email=email,
        name="OAuth User",
        provider="google",
        provider_user_id=f"google-{uuid4()}",
        email_verified=True,
    )

    assert user.id == user_id
    identity = db_session.query(AuthIdentity).filter(AuthIdentity.provider_email == email).one()
    assert identity.user_id == user_id
