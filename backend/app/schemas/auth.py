from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=2, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TelegramAuthRequest(BaseModel):
    id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None
    auth_date: int
    hash: str


class UserRead(BaseModel):
    id: str
    email: str
    name: str
    role: str
    avatar_url: str | None = None
    telegram_id: str | None = None

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    user: UserRead
