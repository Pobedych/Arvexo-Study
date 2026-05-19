import argparse
import json
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.models import AIUsage, Task, TaskAttempt  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Arvexo Study task JSON into the local database.")
    parser.add_argument("path", nargs="?", default="data/task.json")
    parser.add_argument("--clear", action="store_true", help="Delete existing tasks before import.")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / path

    tasks = json.loads(path.read_text(encoding="utf-8"))

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if args.clear:
            db.query(AIUsage).delete()
            db.query(TaskAttempt).delete()
            db.query(Task).delete()
            db.flush()

        created = 0
        updated = 0
        for item in tasks:
            source = str(item["source"])
            existing = db.execute(select(Task).where(Task.source == source)).scalar_one_or_none()
            payload = {
                "exam_number": int(item["exam_number"]),
                "topic": str(item["topic"]),
                "condition": str(item["condition"]),
                "correct_answer": str(item["correct_answer"]),
                "accepted_answers": list(item.get("accepted_answers") or []),
                "explanation": item.get("explanation"),
                "difficulty": str(item.get("difficulty") or "medium"),
                "source": source,
                "status": str(item.get("status") or "active"),
            }
            if existing:
                for key, value in payload.items():
                    setattr(existing, key, value)
                updated += 1
            else:
                db.add(Task(**payload))
                created += 1

        db.commit()
        print(f"Imported {len(tasks)} tasks from {path}")
        print(f"Created: {created}")
        print(f"Updated: {updated}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
