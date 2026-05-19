from datetime import datetime

from pydantic import BaseModel


class RecentAttemptResponse(BaseModel):
    task_id: str
    exam_number: int
    topic: str
    is_correct: bool
    created_at: datetime


class StatsResponse(BaseModel):
    total_attempts: int
    solved_today: int
    correct_attempts: int
    wrong_attempts: int
    accuracy_percent: float
    weak_exam_numbers: list[int]
    ai_daily_limit: int
    ai_remaining_today: int
    recent_attempts: list[RecentAttemptResponse]
