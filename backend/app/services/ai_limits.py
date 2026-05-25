from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core.time import utc_day_start
from app.models.ai_usage import AIUsage
from app.models.user import User


PLAN_DAILY_LIMITS = {
    "free": 5,
    "trial": 150,
    "pro": 150,
}


def get_daily_limit(plan: str) -> int:
    return PLAN_DAILY_LIMITS.get(plan, PLAN_DAILY_LIMITS["free"])


def count_ai_usage_today(db: Session, user_id: str) -> int:
    today_start = utc_day_start()
    stmt: Select[tuple[int]] = select(func.count(AIUsage.id)).where(
        AIUsage.user_id == user_id,
        AIUsage.created_at >= today_start,
        AIUsage.status == "success",
    )
    return int(db.execute(stmt).scalar_one())


def get_remaining_ai_requests(db: Session, user_id: str, plan: str) -> int:
    return max(get_daily_limit(plan) - count_ai_usage_today(db, user_id), 0)


def user_ai_quota_lock_stmt(user_id: str) -> Select[tuple[str]]:
    return select(User.id).where(User.id == user_id).with_for_update()


def reserve_ai_request(
    db: Session,
    user_id: str,
    plan: str,
    *,
    task_id: str | None,
    provider: str,
    model: str,
    prompt_type: str = "task_hint",
) -> int | None:
    db.execute(user_ai_quota_lock_stmt(user_id)).scalar_one()

    remaining = get_daily_limit(plan) - count_ai_usage_today(db, user_id)
    if remaining <= 0:
        return None

    db.add(
        AIUsage(
            user_id=user_id,
            task_id=task_id,
            provider=provider,
            model=model,
            prompt_type=prompt_type,
            status="success",
        )
    )
    db.flush()
    return remaining - 1
