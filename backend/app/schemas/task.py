from datetime import datetime

from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    exam_number: int = Field(ge=1, le=18)
    topic: str
    condition: str
    correct_answer: str
    accepted_answers: list[str] = []
    explanation: str | None = None
    difficulty: str = "medium"
    source: str = "manual"
    status: str = "active"


class TaskCreate(TaskBase):
    pass


class TaskRead(TaskBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskListItem(BaseModel):
    id: str
    exam_number: int
    topic: str
    difficulty: str
    status: str
    user_status: str = "unsolved"
    attempts_count: int = 0

    model_config = {"from_attributes": True}


class SubmitAnswerRequest(BaseModel):
    answer: str
    time_spent_seconds: int | None = Field(default=None, ge=0)


class SubmitAnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    normalized_answer: str
    explanation: str | None = None


class HintResponse(BaseModel):
    hint: str
    remaining_today: int
