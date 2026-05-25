from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import as_utc, utc_now
from app.models.subscription import Subscription
from app.models.user import User


def get_effective_plan(db: Session, user: User) -> str:
    now = utc_now()
    subscriptions = (
        db.execute(
            select(Subscription)
            .where(Subscription.user_id == user.id)
            .order_by(Subscription.updated_at.desc(), Subscription.created_at.desc())
        )
        .scalars()
        .all()
    )

    for subscription in subscriptions:
        if subscription.status not in {"active", "trial", "trialing"}:
            continue
        if subscription.plan == "pro" and (subscription.ends_at is None or as_utc(subscription.ends_at) >= now):
            return "pro"
        if subscription.plan == "trial" and subscription.trial_ends_at and as_utc(subscription.trial_ends_at) >= now:
            return "trial"

    return "free"
