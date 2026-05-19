from datetime import datetime, time

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.ai_usage import AIUsage


PLAN_DAILY_LIMITS = {
    "free": 5,
    "trial": 150,
    "pro": 150,
}


def get_daily_limit(plan: str) -> int:
    return PLAN_DAILY_LIMITS.get(plan, PLAN_DAILY_LIMITS["free"])


def count_ai_usage_today(db: Session, user_id: str) -> int:
    today_start = datetime.combine(datetime.utcnow().date(), time.min)
    stmt: Select[tuple[int]] = select(func.count(AIUsage.id)).where(
        AIUsage.user_id == user_id,
        AIUsage.created_at >= today_start,
        AIUsage.status == "success",
    )
    return int(db.execute(stmt).scalar_one())


def get_remaining_ai_requests(db: Session, user_id: str, plan: str) -> int:
    return max(get_daily_limit(plan) - count_ai_usage_today(db, user_id), 0)
