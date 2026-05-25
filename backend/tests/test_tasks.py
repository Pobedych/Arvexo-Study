from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ai_usage import AIUsage
from app.models.task import Task


def test_get_task_does_not_expose_answer_before_submit(client: TestClient) -> None:
    tasks_response = client.get("/tasks?exam_number=5")
    assert tasks_response.status_code == 200
    task_id = tasks_response.json()[0]["id"]

    task_response = client.get(f"/tasks/{task_id}")
    assert task_response.status_code == 200
    payload = task_response.json()

    assert "correct_answer" not in payload
    assert "accepted_answers" not in payload
    assert "explanation" not in payload


def test_public_tasks_ignore_status_query_and_hide_drafts(client: TestClient, db_session: Session) -> None:
    draft = create_task(db_session, status="draft")

    list_response = client.get("/tasks?status=draft")
    assert list_response.status_code == 200
    assert all(task["id"] != draft.id for task in list_response.json())

    detail_response = client.get(f"/tasks/{draft.id}")
    assert detail_response.status_code == 404


def test_submit_returns_answer_after_authenticated_attempt(client: TestClient) -> None:
    email = f"task-submit-{uuid4()}@example.com"
    register_response = client.post(
        "/auth/register",
        json={"email": email, "password": "strong-password", "name": "Task Submit"},
    )
    assert register_response.status_code == 201

    tasks_response = client.get("/tasks?exam_number=5")
    assert tasks_response.status_code == 200
    task_id = tasks_response.json()[0]["id"]

    submit_response = client.post(f"/tasks/{task_id}/submit", json={"answer": "wrong"})
    assert submit_response.status_code == 200
    payload = submit_response.json()

    assert payload["is_correct"] is False
    assert payload["correct_answer"]
    assert "accepted_answers" not in payload


def test_hint_does_not_record_usage_after_daily_limit(client: TestClient, db_session: Session) -> None:
    email = f"hint-limit-{uuid4()}@example.com"
    register_response = client.post(
        "/auth/register",
        json={"email": email, "password": "strong-password", "name": "Hint Limit"},
    )
    assert register_response.status_code == 201
    user_id = register_response.json()["user"]["id"]

    tasks_response = client.get("/tasks?exam_number=5")
    assert tasks_response.status_code == 200
    task_id = tasks_response.json()[0]["id"]
    add_ai_usage(db_session, user_id, task_id, count=5)

    hint_response = client.post(f"/tasks/{task_id}/hint")
    assert hint_response.status_code == 429
    assert count_ai_usage(db_session, user_id) == 5


def create_task(db: Session, status: str) -> Task:
    task = Task(
        exam_number=5,
        topic=f"Draft leak check {uuid4()}",
        condition="Draft-only condition",
        correct_answer="secret",
        accepted_answers=["also-secret"],
        explanation="Draft-only explanation",
        difficulty="medium",
        source="test",
        status=status,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def add_ai_usage(db: Session, user_id: str, task_id: str, count: int) -> None:
    db.add_all(
        [
            AIUsage(
                user_id=user_id,
                task_id=task_id,
                provider="test",
                model="test",
                prompt_type="task_hint",
                status="success",
            )
            for _ in range(count)
        ]
    )
    db.commit()


def count_ai_usage(db: Session, user_id: str) -> int:
    return int(
        db.execute(
            select(func.count(AIUsage.id)).where(
                AIUsage.user_id == user_id,
                AIUsage.status == "success",
            )
        ).scalar_one()
    )
