from app.models.task import Task


def build_stub_hint(task: Task) -> str:
    return (
        f"Разбери задание N{task.exam_number} по теме «{task.topic}»: "
        "найди ключевое правило в условии, отбрось явно неподходящие варианты и проверь ответ по смыслу. "
        "Я не раскрываю готовый ответ, чтобы ты решил задание сам."
    )
