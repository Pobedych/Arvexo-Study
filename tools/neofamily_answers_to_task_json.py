import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


TASKS_PATH = Path("data/task.json")
NEOFAMILY_INDEX_PATH = Path("data/neofamily_index.json")
NEOFAMILY_DETAIL_CACHE_PATH = Path("data/neofamily_detail_cache.json")
SUBJECT = "russkiy-yazyk"
LIST_URL = "https://backend.neofamily.ru/api/task"
DETAIL_URL = "https://backend.neofamily.ru/api/task/{id}?subject={subject}"
DETAIL_PAGE_URL = "https://neofamily.ru/{subject}/task-bank/{id}"
PER_PAGE = 100
MIN_SCORE = 0.92
MIN_TOKEN_SCORE = 0.90


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


def html_to_text(value: str) -> str:
    parser = TextExtractor()
    parser.feed(value or "")
    text = html.unescape("".join(parser.parts))
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def normalize(value: str) -> str:
    value = html_to_text(value)
    value = value.lower().replace("ё", "е")
    value = re.sub(r"^задание\s*№\s*\d+\s*\.?", "", value)
    value = re.sub(r"^(впишите правильный ответ|выберите один или несколько правильных ответов)\.?", "", value)
    value = value.replace("–", "-").replace("—", "-")
    return re.sub(r"[^0-9a-zа-я]+", "", value)


def token_set(value: str) -> set[str]:
    value = html_to_text(value)
    value = value.lower().replace("ё", "е")
    value = re.sub(r"^задание\s*№\s*\d+\s*\.?", "", value)
    return set(re.findall(r"[0-9a-zа-я]{2,}", value))


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
        except (TimeoutError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url}: {last_error}")


def load_or_fetch_index() -> list[dict[str, Any]]:
    if NEOFAMILY_INDEX_PATH.exists():
        return json.loads(NEOFAMILY_INDEX_PATH.read_text(encoding="utf-8"))

    params = {
        "sort[id]": "asc",
        "only": "score,question,additional_info,subject_id,is_hidden,is_informal,free_answer,is_related,id,task_answer_size,status,is_favorite,is_briefcase,criteria,has_custom_answers",
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

    NEOFAMILY_INDEX_PATH.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    return tasks


def best_match(
    task: dict[str, Any],
    candidates: list[dict[str, Any]],
    exact_by_line: dict[int, dict[str, list[dict[str, Any]]]],
) -> tuple[dict[str, Any] | None, float]:
    needle = normalize(str(task["condition"]))
    if not needle:
        return None, 0.0

    exact_matches = exact_by_line.get(int(task["exam_number"]), {}).get(needle, [])
    if exact_matches:
        return exact_matches[0], 1.0

    best: dict[str, Any] | None = None
    best_score = 0.0
    for candidate in candidates:
        haystack = candidate["normalized_question"]
        if not haystack:
            continue
        if needle in haystack or haystack in needle:
            score = min(len(needle), len(haystack)) / max(len(needle), len(haystack))
            if score > best_score:
                best = candidate
                best_score = score

    if best_score >= MIN_SCORE:
        return best, best_score

    needle_tokens = token_set(str(task["condition"]))
    if len(needle_tokens) < 8:
        return best, best_score

    for candidate in candidates:
        haystack_tokens = candidate.get("question_tokens")
        if not haystack_tokens:
            continue
        union = len(needle_tokens | haystack_tokens)
        score = len(needle_tokens & haystack_tokens) / union if union else 0.0
        if score >= MIN_TOKEN_SCORE and score > best_score:
            best = candidate
            best_score = score

    return best, best_score


def get_detail(task_id: int) -> dict[str, Any]:
    request = urllib.request.Request(
        DETAIL_PAGE_URL.format(id=task_id, subject=SUBJECT),
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                page_html = response.read().decode("utf-8", errors="replace")
            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', page_html, re.S)
            if not match:
                raise RuntimeError("__NEXT_DATA__ not found")
            next_data = json.loads(html.unescape(match.group(1)))
            queries = next_data["props"]["pageProps"]["dehydratedState"]["queries"]
            for query in queries:
                key = query.get("queryKey", [])
                data = query.get("state", {}).get("data")
                if key and key[0] == "TASK_DETAIL" and isinstance(data, dict):
                    return data
            raise RuntimeError("TASK_DETAIL query not found")
        except (
            TimeoutError,
            ConnectionResetError,
            OSError,
            urllib.error.URLError,
            urllib.error.HTTPError,
            json.JSONDecodeError,
            KeyError,
            RuntimeError,
        ) as exc:
            last_error = exc
            time.sleep(1.0 * (attempt + 1))

    # Fallback to direct backend API; it can be slower, but sometimes succeeds when SSR is unavailable.
    payload = fetch_json(DETAIL_URL.format(id=task_id, subject=SUBJECT))
    return payload["data"]


def main() -> None:
    tasks = json.loads(TASKS_PATH.read_text(encoding="utf-8"))
    neofamily_tasks = load_or_fetch_index()
    details_cache: dict[str, dict[str, Any]] = {}
    if NEOFAMILY_DETAIL_CACHE_PATH.exists():
        details_cache = json.loads(NEOFAMILY_DETAIL_CACHE_PATH.read_text(encoding="utf-8"))

    by_line: dict[int, list[dict[str, Any]]] = {}
    exact_by_line: dict[int, dict[str, list[dict[str, Any]]]] = {}
    for item in neofamily_tasks:
        line = item.get("task_line") or {}
        line_name = str(line.get("name") or "")
        if not line_name.isdigit():
            continue
        item["normalized_question"] = normalize(str(item.get("question") or ""))
        item["question_tokens"] = token_set(str(item.get("question") or ""))
        line_number = int(line_name)
        by_line.setdefault(line_number, []).append(item)
        exact_by_line.setdefault(line_number, {}).setdefault(item["normalized_question"], []).append(item)

    matched = 0
    no_answer = 0
    low_confidence = 0

    for index, task in enumerate(tasks, start=1):
        if task.get("correct_answer"):
            continue
        exam_number = int(task["exam_number"])
        match, score = best_match(task, by_line.get(exam_number, []), exact_by_line)
        if not match or score < MIN_SCORE:
            low_confidence += 1
            continue

        neofamily_id = int(match["id"])
        cache_key = str(neofamily_id)
        if cache_key not in details_cache:
            details_cache[cache_key] = get_detail(neofamily_id)
            NEOFAMILY_DETAIL_CACHE_PATH.write_text(json.dumps(details_cache, ensure_ascii=False, indent=2), encoding="utf-8")
            time.sleep(0.05)

        detail = details_cache[cache_key]
        answers = [str(answer).strip() for answer in detail.get("answer", []) if str(answer).strip()]
        if not answers:
            no_answer += 1
            continue

        task["correct_answer"] = answers[0]
        task["accepted_answers"] = answers[1:]
        task["source"] = f"{task['source']};neofamily:{neofamily_id}"
        task["status"] = "active"

        # Keep the payload compact: store attribution and match score, not the full external solution.
        task["explanation"] = f"Ответ сопоставлен с NeoFamily, задание {neofamily_id}, confidence={score:.3f}."
        matched += 1
        TASKS_PATH.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")

        if index % 100 == 0:
            print(f"Processed {index}/{len(tasks)}, matched {matched}")

    TASKS_PATH.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Total local tasks: {len(tasks)}")
    print(f"NeoFamily index tasks: {len(neofamily_tasks)}")
    print(f"Matched with answers: {matched}")
    print(f"Low confidence/no match: {low_confidence}")
    print(f"Matched but no answer in NeoFamily: {no_answer}")


if __name__ == "__main__":
    main()
