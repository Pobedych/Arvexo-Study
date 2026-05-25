from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.time import utc_day_start
from app.models.task import Task, TaskAttempt
from app.schemas.stats import RecentAttemptResponse, StatsResponse
from app.services.ai_limits import get_daily_limit, get_remaining_ai_requests
from app.services.auth import get_current_user
from app.services.subscriptions import get_effective_plan

router = APIRouter(prefix="/stats", tags=["statistics"])


@router.get("/me", response_model=StatsResponse)
def get_my_stats(
    request: Request,
    db: Session = Depends(get_db),
) -> StatsResponse:
    user = get_current_user(request, db)
    plan = get_effective_plan(db, user)
    user_id = user.id
    attempts = db.execute(select(TaskAttempt).where(TaskAttempt.user_id == user_id)).scalars().all()
    total = len(attempts)
    correct = sum(1 for attempt in attempts if attempt.is_correct)
    wrong = total - correct
    today_start = utc_day_start()
    solved_today = int(
        db.execute(
            select(func.count(TaskAttempt.id)).where(
                TaskAttempt.user_id == user_id,
                TaskAttempt.created_at >= today_start,
            )
        ).scalar_one()
    )

    weak_stmt = (
        select(Task.exam_number, func.count(TaskAttempt.id).label("wrong_count"))
        .join(TaskAttempt, TaskAttempt.task_id == Task.id)
        .where(TaskAttempt.user_id == user_id, TaskAttempt.is_correct.is_(False))
        .group_by(Task.exam_number)
        .order_by(func.count(TaskAttempt.id).desc())
        .limit(5)
    )
    weak_exam_numbers = [row[0] for row in db.execute(weak_stmt).all()]
    recent_stmt = (
        select(TaskAttempt, Task)
        .join(Task, TaskAttempt.task_id == Task.id)
        .where(TaskAttempt.user_id == user_id)
        .order_by(TaskAttempt.created_at.desc())
        .limit(5)
    )
    recent_attempts = [
        RecentAttemptResponse(
            task_id=task.id,
            exam_number=task.exam_number,
            topic=task.topic,
            is_correct=attempt.is_correct,
            created_at=attempt.created_at,
        )
        for attempt, task in db.execute(recent_stmt).all()
    ]

    return StatsResponse(
        total_attempts=total,
        solved_today=solved_today,
        correct_attempts=correct,
        wrong_attempts=wrong,
        accuracy_percent=round((correct / total) * 100, 2) if total else 0,
        weak_exam_numbers=weak_exam_numbers,
        ai_daily_limit=get_daily_limit(plan),
        ai_remaining_today=get_remaining_ai_requests(db, user_id, plan),
        recent_attempts=recent_attempts,
    )
