import re
from dataclasses import dataclass


@dataclass(frozen=True)
class AnswerCheck:
    is_correct: bool
    normalized_user_answer: str
    normalized_correct_answers: list[str]


def normalize_answer(value: str, *, fold_yo: bool = True) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)
    if fold_yo:
        normalized = normalized.replace("ё", "е")
    return normalized


def check_answer(user_answer: str, correct_answer: str, accepted_answers: list[str] | None = None) -> AnswerCheck:
    candidates = [correct_answer, *(accepted_answers or [])]
    normalized_user_answer = normalize_answer(user_answer)
    normalized_correct_answers = [normalize_answer(candidate) for candidate in candidates if candidate.strip()]

    return AnswerCheck(
        is_correct=normalized_user_answer in normalized_correct_answers,
        normalized_user_answer=normalized_user_answer,
        normalized_correct_answers=normalized_correct_answers,
    )
