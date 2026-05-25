from datetime import UTC, datetime, time


def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_day_start() -> datetime:
    return datetime.combine(utc_now().date(), time.min, tzinfo=UTC)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
