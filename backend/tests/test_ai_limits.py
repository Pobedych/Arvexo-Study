from app.services.ai_limits import get_daily_limit


def test_free_limit() -> None:
    assert get_daily_limit("free") == 5


def test_pro_limit() -> None:
    assert get_daily_limit("pro") == 150


def test_unknown_plan_falls_back_to_free() -> None:
    assert get_daily_limit("unknown") == 5
