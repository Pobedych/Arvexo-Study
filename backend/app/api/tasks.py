from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.ai_usage import AIUsage
from app.models.task import Task, TaskAttempt
from app.models.user import User
from app.schemas.task import HintResponse, SubmitAnswerRequest, SubmitAnswerResponse, TaskListItem, TaskRead
from app.services.ai_hints import build_stub_hint
from app.services.ai_limits import get_remaining_ai_requests
from app.services.answers import check_answer
from app.services.auth import SESSION_COOKIE, decode_access_token, get_current_user
from app.services.subscriptions import get_effective_plan

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskListItem])
def list_tasks(
    request: Request,
    exam_number: int | None = Query(default=None, ge=1, le=18),
    difficulty: str | None = None,
    status: str = "active",
    db: Session = Depends(get_db),
) -> list[TaskListItem]:
    stmt = select(Task).where(Task.status == status).order_by(Task.exam_number, Task.created_at)
    if exam_number is not None:
        stmt = stmt.where(Task.exam_number == exam_number)
    if difficulty:
        stmt = stmt.where(Task.difficulty == difficulty)
    tasks = list(db.execute(stmt).scalars().all())

    user_id = get_optional_user_id(request, db)
    attempts_by_task: dict[str, list[TaskAttempt]] = {}
    if user_id and tasks:
        task_ids = [task.id for task in tasks]
        attempts = db.execute(
            select(TaskAttempt)
            .where(TaskAttempt.user_id == user_id, TaskAttempt.task_id.in_(task_ids))
            .order_by(TaskAttempt.created_at.asc())
        ).scalars().all()
        for attempt in attempts:
            attempts_by_task.setdefault(attempt.task_id, []).append(attempt)

    output: list[TaskListItem] = []
    for task in tasks:
        task_attempts = attempts_by_task.get(task.id, [])
        user_status = "unsolved"
        if task_attempts:
            user_status = "correct" if task_attempts[-1].is_correct else "wrong"

        item = TaskListItem.model_validate(task).model_copy(
            update={
                "user_status": user_status,
                "attempts_count": len(task_attempts),
            }
        )
        output.append(item)
    return output


def get_optional_user_id(request: Request, db: Session) -> str | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    try:
        user_id = decode_access_token(token)
    except HTTPException:
        return None
    user = db.get(User, user_id)
    if not user or not user.is_active or user.is_banned:
        return None
    return user.id


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: str, db: Session = Depends(get_db)) -> Task:
    task = db.get(Task, task_id)
    if not task or task.status == "archived":
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/submit", response_model=SubmitAnswerResponse)
def submit_answer(
    task_id: str,
    payload: SubmitAnswerRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> SubmitAnswerResponse:
    user = get_current_user(request, db)
    task = db.get(Task, task_id)
    if not task or task.status != "active":
        raise HTTPException(status_code=404, detail="Task not found")

    result = check_answer(payload.answer, task.correct_answer, task.accepted_answers)
    attempt = TaskAttempt(
        user_id=user.id,
        task_id=task.id,
        user_answer=payload.answer,
        normalized_answer=result.normalized_user_answer,
        is_correct=result.is_correct,
        time_spent_seconds=payload.time_spent_seconds,
    )
    db.add(attempt)
    db.commit()

    return SubmitAnswerResponse(
        is_correct=result.is_correct,
        correct_answer=task.correct_answer,
        normalized_answer=result.normalized_user_answer,
        explanation=task.explanation,
    )


@router.post("/{task_id}/hint", response_model=HintResponse)
def get_hint(
    task_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> HintResponse:
    user = get_current_user(request, db)
    task = db.get(Task, task_id)
    if not task or task.status != "active":
        raise HTTPException(status_code=404, detail="Task not found")

    plan = get_effective_plan(db, user)
    remaining = get_remaining_ai_requests(db, user.id, plan)
    if remaining <= 0:
        raise HTTPException(status_code=429, detail="AI daily limit exceeded")

    settings = get_settings()
    db.add(
        AIUsage(
            user_id=user.id,
            task_id=task.id,
            provider=settings.ai_provider,
            model=settings.ai_model,
            prompt_type="task_hint",
            status="success",
        )
    )
    db.commit()

    return HintResponse(hint=build_stub_hint(task), remaining_today=remaining - 1)
