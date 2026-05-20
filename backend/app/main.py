from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, select, text

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.stats import router as stats_router
from app.api.tasks import router as tasks_router
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.models import Task, User


def ensure_user_profile_columns() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("users")}
    statements = []
    if "last_name" not in existing_columns:
        statements.append("ALTER TABLE users ADD COLUMN last_name VARCHAR(120)")
    if "phone" not in existing_columns:
        statements.append("ALTER TABLE users ADD COLUMN phone VARCHAR(32)")

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def seed_demo_data() -> None:
    db = SessionLocal()
    try:
        task_exists = db.execute(select(Task.id).limit(1)).first()
        if not task_exists:
            db.add_all(
                [
                    Task(
                        exam_number=5,
                        topic="Паронимы",
                        condition="Укажите слово, которое нужно поставить вместо пропуска: ... поступок.",
                        correct_answer="эффектный",
                        accepted_answers=["эффектный"],
                        explanation="Эффектный значит производящий сильное впечатление.",
                        difficulty="medium",
                        source="demo",
                        status="active",
                    ),
                    Task(
                        exam_number=9,
                        topic="Правописание корней",
                        condition="Укажите варианты ответов, в которых во всех словах пропущена одна и та же буква.",
                        correct_answer="25",
                        accepted_answers=["52"],
                        explanation="Для этого типа ответа порядок цифр может быть допустимым вариантом, если это задано в данных.",
                        difficulty="hard",
                        source="demo",
                        status="active",
                    ),
                ]
            )
        user_exists = db.get(User, "demo-user")
        if not user_exists:
            db.add(User(id="demo-user", email="demo@study.arvexo.ru", name="Демо ученик"))
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_user_profile_columns()
    seed_demo_data()
    yield


settings = get_settings()
app = FastAPI(title="Arvexo Study API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(stats_router)
