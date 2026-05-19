import argparse
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


SUBJECT = "russkiy-yazyk"
LIST_URL = "https://backend.neofamily.ru/api/task"
DETAIL_URL = "https://backend.neofamily.ru/api/task/{id}?subject={subject}"
DETAIL_PAGE_URL = "https://neofamily.ru/{subject}/task-bank/{id}"
INDEX_PATH = Path("data/neofamily_index.json")
DETAIL_CACHE_PATH = Path("data/neofamily_detail_cache.json")
OUTPUT_PATH = Path("data/task.json")
SNAPSHOT_PATH = Path("data/task.fipi_snapshot.json")
PER_PAGE = 100


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self.skip_depth += 1
        if not self.skip_depth and tag in {"br", "p", "tr", "div", "li"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self.skip_depth:
            self.skip_depth -= 1
        if not self.skip_depth and tag in {"p", "tr", "div", "li"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append(data)


def html_to_text(value: str | None) -> str:
    parser = TextExtractor()
    parser.feed(value or "")
    text = html.unescape("".join(parser.parts))
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json,text/plain,*/*",
        },
    )
    last_error: Exception | None = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.loads(response.read().decode("utf-8"))
        except (
            TimeoutError,
            ConnectionResetError,
            OSError,
            urllib.error.URLError,
            urllib.error.HTTPError,
            json.JSONDecodeError,
        ) as exc:
            last_error = exc
            time.sleep(1.25 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url}: {last_error}")


def load_or_fetch_index(force: bool = False) -> list[dict[str, Any]]:
    if INDEX_PATH.exists() and not force:
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))

    params = {
        "sort[id]": "asc",
        "only": "score,question,additional_info,subject_id,is_hidden,is_informal,free_answer,is_related,id,task_answer_size,status,is_favorite,is_briefcase,criteria,has_custom_answers,task_line,themes,files",
        "except_solved": "0",
        "is_hidden": "0",
        "subject": SUBJECT,
        "perPage": str(PER_PAGE),
        "exclude_all_variant_ids": "0",
    }
    encoded = urllib.parse.urlencode(params)

    tasks: list[dict[str, Any]] = []
    page = 1
    total_pages = None
    while total_pages is None or page <= total_pages:
        payload = fetch_json(f"{LIST_URL}?{encoded}&page={page}")
        tasks.extend(payload.get("data", []))
        pagination = payload.get("pagination") or {}
        total_pages = int(pagination.get("totalPages") or page)
        print(f"NeoFamily index page {page}/{total_pages}: {len(tasks)}")
        page += 1
        time.sleep(0.15)

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    return tasks


def load_detail_cache() -> dict[str, dict[str, Any]]:
    if not DETAIL_CACHE_PATH.exists():
        return {}
    return json.loads(DETAIL_CACHE_PATH.read_text(encoding="utf-8"))


def save_detail_cache(cache: dict[str, dict[str, Any]]) -> None:
    DETAIL_CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def get_detail(task_id: int, cache: dict[str, dict[str, Any]]) -> dict[str, Any]:
    cache_key = str(task_id)
    if cache_key in cache:
        return cache[cache_key]

    payload = fetch_json(DETAIL_URL.format(id=task_id, subject=SUBJECT))
    detail = payload["data"]
    cache[cache_key] = detail
    if len(cache) % 25 == 0:
        save_detail_cache(cache)
    time.sleep(0.08)
    return detail


def fetch_detail(task_id: int) -> dict[str, Any]:
    payload = fetch_json(DETAIL_URL.format(id=task_id, subject=SUBJECT))
    return payload["data"]


def load_chunk_details(
    task_ids: list[int],
    cache: dict[str, dict[str, Any]],
    workers: int,
) -> dict[int, dict[str, Any]]:
    details: dict[int, dict[str, Any]] = {}
    missing: list[int] = []

    for task_id in task_ids:
        cached = cache.get(str(task_id))
        if cached:
            details[task_id] = cached
        else:
            missing.append(task_id)

    if not missing:
        return details

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(fetch_detail, task_id): task_id for task_id in missing}
        for future in as_completed(futures):
            task_id = futures[future]
            try:
                detail = future.result()
            except Exception as exc:
                print(f"Skip NeoFamily task {task_id}: {exc}", flush=True)
                continue
            cache[str(task_id)] = detail
            details[task_id] = detail

    save_detail_cache(cache)
    return details


def topic_from_detail(detail: dict[str, Any], fallback: str) -> str:
    themes = detail.get("themes") or []
    if themes:
        name = str(themes[0].get("name") or "").strip()
        if name:
            return name
    return fallback


def condition_from_detail(detail: dict[str, Any]) -> str:
    additional = html_to_text(detail.get("additional_info"))
    question = html_to_text(detail.get("question"))
    if additional and question:
        return f"{additional}\n\n{question}"
    return question or additional


def task_from_detail(detail: dict[str, Any]) -> dict[str, object] | None:
    line = detail.get("task_line") or {}
    line_name = str(line.get("name") or "")
    if not line_name.isdigit():
        return None

    exam_number = int(line_name)
    if exam_number < 1 or exam_number > 18:
        return None

    answers = [str(answer).strip() for answer in detail.get("answer", []) if str(answer).strip()]
    condition = condition_from_detail(detail)
    if not answers or not condition:
        return None

    task_id = int(detail["id"])
    fallback_topic = f"Задание {exam_number}"
    solution = html_to_text(detail.get("solution"))

    return {
        "exam_number": exam_number,
        "topic": topic_from_detail(detail, fallback_topic),
        "condition": condition,
        "correct_answer": answers[0],
        "accepted_answers": answers[1:],
        "explanation": solution or None,
        "difficulty": "medium",
        "source": f"neofamily:{task_id}:{DETAIL_PAGE_URL.format(subject=SUBJECT, id=task_id)}",
        "status": "active",
    }


def build_tasks(
    index: list[dict[str, Any]],
    max_per_number: int,
    cache: dict[str, dict[str, Any]],
    workers: int,
    chunk_size: int,
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    counts = {number: 0 for number in range(1, 19)}
    by_number: dict[int, list[dict[str, Any]]] = {number: [] for number in range(1, 19)}

    for item in index:
        line = item.get("task_line") or {}
        line_name = str(line.get("name") or "")
        if not line_name.isdigit():
            continue
        exam_number = int(line_name)
        if exam_number < 1 or exam_number > 18:
            continue
        by_number[exam_number].append(item)

    for exam_number in range(1, 19):
        candidates = by_number[exam_number]
        for start in range(0, len(candidates), chunk_size):
            if max_per_number > 0 and counts[exam_number] >= max_per_number:
                break

            chunk = candidates[start : start + chunk_size]
            task_ids = [int(item["id"]) for item in chunk]
            details = load_chunk_details(task_ids, cache, workers)

            for task_id in task_ids:
                detail = details.get(task_id)
                if not detail:
                    continue
                task = task_from_detail(detail)
                if not task:
                    continue

                output.append(task)
                counts[exam_number] += 1

                if max_per_number > 0 and counts[exam_number] >= max_per_number:
                    break

            print(
                f"Exam {exam_number}: {counts[exam_number]}/{max_per_number or 'all'} "
                f"(collected total {len(output)})",
                flush=True,
            )

    save_detail_cache(cache)
    return output


def snapshot_existing_output() -> None:
    if OUTPUT_PATH.exists() and not SNAPSHOT_PATH.exists():
        SNAPSHOT_PATH.write_text(OUTPUT_PATH.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export NeoFamily task bank tasks with answers to Arvexo Study JSON.")
    parser.add_argument("--max-per-number", type=int, default=100, help="Limit per EGE task number. Use 0 for all.")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--chunk-size", type=int, default=50)
    parser.add_argument("--force-index", action="store_true", help="Refetch NeoFamily index even if cache exists.")
    parser.add_argument("--no-snapshot", action="store_true", help="Do not save the existing data/task.json snapshot.")
    args = parser.parse_args()

    if args.output == OUTPUT_PATH and not args.no_snapshot:
        snapshot_existing_output()

    index = load_or_fetch_index(force=args.force_index)
    cache = load_detail_cache()
    tasks = build_tasks(index, args.max_per_number, cache, args.workers, args.chunk_size)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Written: {len(tasks)} -> {args.output}")
    for number in range(1, 19):
        count = sum(1 for task in tasks if task["exam_number"] == number)
        print(f"{number}: {count}")


if __name__ == "__main__":
    main()
