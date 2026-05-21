from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app


def test_register_login_me_logout_flow() -> None:
    with TestClient(app) as client:
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


def test_stats_ignores_client_plan_query() -> None:
    with TestClient(app) as client:
        email = f"plan-check-{uuid4()}@example.com"
        register_response = client.post(
            "/auth/register",
            json={"email": email, "password": "strong-password", "name": "Plan Check"},
        )
        assert register_response.status_code == 201

        stats_response = client.get("/stats/me?plan=pro")
        assert stats_response.status_code == 200
        assert stats_response.json()["ai_daily_limit"] == 5


def test_delete_me_removes_session() -> None:
    with TestClient(app) as client:
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
