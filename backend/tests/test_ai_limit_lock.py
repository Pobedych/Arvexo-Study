import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.core.database import Base
from app.models.user import User
from app.services.ai_limits import reserve_ai_request, user_ai_quota_lock_stmt


def test_ai_quota_lock_uses_postgres_row_lock() -> None:
    sql = str(
        user_ai_quota_lock_stmt("user-id").compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    assert "FOR UPDATE" in sql


def test_postgres_ai_quota_lock_blocks_concurrent_reservation() -> None:
    database_url = os.environ.get("POSTGRES_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("POSTGRES_TEST_DATABASE_URL is not configured")

    engine = create_engine(database_url, pool_pre_ping=True)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    user_id = str(uuid4())

    setup_db = Session()
    try:
        setup_db.add(User(id=user_id, email=f"{user_id}@example.com", name="Quota Lock"))
        setup_db.commit()
    finally:
        setup_db.close()

    first_db = Session()
    second_db = Session()
    try:
        assert (
            reserve_ai_request(
                first_db,
                user_id,
                "free",
                task_id=None,
                provider="test",
                model="test",
            )
            == 4
        )

        second_db.execute(text("SET LOCAL lock_timeout = '200ms'"))
        with pytest.raises(OperationalError):
            reserve_ai_request(
                second_db,
                user_id,
                "free",
                task_id=None,
                provider="test",
                model="test",
            )
    finally:
        second_db.rollback()
        second_db.close()
        first_db.rollback()
        first_db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
