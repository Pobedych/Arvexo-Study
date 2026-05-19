from app.services.answers import check_answer, normalize_answer


def test_normalize_answer_strips_spaces_and_case() -> None:
    assert normalize_answer("  ЭФФЕКТНЫЙ  ") == "эффектный"


def test_normalize_answer_folds_yo() -> None:
    assert normalize_answer("жёлтый") == "желтый"


def test_check_answer_accepts_additional_variants() -> None:
    result = check_answer("52", "25", ["52"])
    assert result.is_correct is True


def test_check_answer_rejects_wrong_answer() -> None:
    result = check_answer("эффективный", "эффектный")
    assert result.is_correct is False
