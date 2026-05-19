import html
import json
import re
import time
import urllib.error
import urllib.request
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path


PROJECT_ID = "AF0ED3F2557F8FFC4C06F80B6803FD26"
BASE_URL = "https://ege.fipi.ru/bank/questions.php"
OUTPUT_PATH = Path("data/task.json")
PAGE_SIZE = 100
MAX_PER_NUMBER = 100
SOURCE = "fipi"


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "select"}:
            self.skip_depth += 1
        if not self.skip_depth and tag in {"br", "p", "tr", "div", "li"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "select"} and self.skip_depth:
            self.skip_depth -= 1
        if not self.skip_depth and tag in {"p", "tr", "div", "li"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append(data)


def html_to_text(value: str) -> str:
    parser = TextExtractor()
    parser.feed(value)
    text = html.unescape("".join(parser.parts))
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def fetch_page(page: int) -> str:
    url = f"{BASE_URL}?proj={PROJECT_ID}&page={page}&pagesize={PAGE_SIZE}"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    last_error: Exception | None = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return response.read().decode("cp1251", errors="replace")
        except (TimeoutError, urllib.error.URLError, urllib.error.HTTPError) as exc:
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch FIPI page {page}: {last_error}")


def extract_tasks(page_html: str) -> list[dict[str, str | list[str]]]:
    starts = list(re.finditer(r"<div class=\"qblock\" id='q([^']+)'>", page_html))
    tasks: list[dict[str, str | list[str]]] = []

    for index, match in enumerate(starts):
        short_id = match.group(1)
        end = starts[index + 1].start() if index + 1 < len(starts) else page_html.find("<div id='bottom_marker'", match.end())
        if end == -1:
            end = len(page_html)
        segment = page_html[match.start() : end]

        info_marker = f"<div id='i{short_id}'>"
        info_start = segment.find(info_marker)
        question_html = segment if info_start == -1 else segment[:info_start]
        info_html = "" if info_start == -1 else segment[info_start:]

        guid_match = re.search(r"name=[\"']guid[\"']\s+value=[\"']([^\"']+)[\"']", question_html)
        guid = guid_match.group(1) if guid_match else ""

        kes_block_match = re.search(r"<td class=\"param-row\">(.*?)</td>", info_html, re.S)
        kes_items = []
        if kes_block_match:
            kes_items = [html_to_text(item) for item in re.findall(r"<div>(.*?)</div>", kes_block_match.group(1), re.S)]

        type_match = re.search(r"<td class=\"param-name\">Тип ответа:</td><td>(.*?)</td>", info_html, re.S)
        answer_type = html_to_text(type_match.group(1)) if type_match else ""

        number_match = re.search(r"<span class=\"canselect\">([^<]+)</span>", info_html)
        source_id = number_match.group(1) if number_match else short_id

        condition = html_to_text(question_html)
        condition = re.sub(r"^Впишите правильный ответ\.\s*", "", condition)
        condition = re.sub(r"^Выберите один или несколько правильных ответов\.\s*", "", condition)

        if condition:
            tasks.append(
                {
                    "source_id": source_id,
                    "source_guid": guid,
                    "condition": condition,
                    "kes": kes_items,
                    "answer_type": answer_type,
                }
            )

    return tasks


def infer_exam_number(task: dict[str, str | list[str]]) -> int | None:
    condition = str(task["condition"]).lower()
    kes_items = [str(item) for item in task.get("kes", [])]
    kes_text = " ".join(kes_items)
    kes_codes = [match.group(1) for item in kes_items if (match := re.match(r"^(\d+(?:\.\d+)*)\b", item))]

    if any(code in {"1.2", "1.3", "1.4", "1.5"} for code in kes_codes):
        return 1
    if any(code == "2" or code.startswith("2.") for code in kes_codes):
        return 2
    if "3.2.3" in kes_text:
        return 4
    if "пароним" in condition:
        return 5
    if "лишнее слово" in condition or "лексическ" in condition:
        return 6
    if any(code in kes_text for code in ("3.5.2", "3.5.3", "3.5.4", "3.5.5", "3.5.6")):
        return 7
    if any(code in kes_text for code in ("3.6.3", "3.6.4", "3.6.5", "3.6.6", "3.6.7")):
        return 8
    if "3.7.2" in kes_text:
        return 9
    if "3.7.3" in kes_text:
        return 10
    if "3.7.4" in kes_text or "3.7.5" in kes_text:
        return 11
    if "3.7.6" in kes_text or "3.7.8" in kes_text:
        return 12
    if "3.7.7" in kes_text:
        return 13
    if "3.7.9" in kes_text:
        return 14
    if "н и нн" in kes_text.lower() or "нн" in condition:
        return 15
    if "3.8.4" in kes_text:
        return 16
    if "3.8.5" in kes_text:
        return 17
    if "3.8.6" in kes_text:
        return 18
    if any(code.startswith("3.3.") for code in kes_codes):
        return 3
    return None


def topic_from_kes(task: dict[str, str | list[str]]) -> str:
    kes = task.get("kes", [])
    if isinstance(kes, list) and kes:
        return re.sub(r"^\d+(?:\.\d+)*\s+", "", str(kes[0])).strip()
    answer_type = str(task.get("answer_type") or "").strip()
    return answer_type or "Русский язык"


def main() -> None:
    collected: list[dict[str, str | list[str]]] = []

    seen_sources: set[tuple[str, str]] = set()
    duplicate_pages = 0
    duplicate_rows = 0
    page = 0
    while page < 50:
        page_html = fetch_page(page)
        page_tasks = extract_tasks(page_html)
        if not page_tasks:
            break

        new_on_page = 0
        for task in page_tasks:
            source_key = (str(task["source_id"]), str(task["source_guid"]))
            if source_key in seen_sources:
                duplicate_rows += 1
                continue
            seen_sources.add(source_key)
            collected.append(task)
            new_on_page += 1

        if new_on_page == 0:
            duplicate_pages += 1
            if duplicate_pages >= 2:
                break
        else:
            duplicate_pages = 0
        page += 1

    grouped: dict[int, list[dict[str, object]]] = defaultdict(list)
    skipped = 0

    for raw_task in collected:
        exam_number = infer_exam_number(raw_task)
        if exam_number is None or exam_number < 1 or exam_number > 18:
            skipped += 1
            continue
        if len(grouped[exam_number]) >= MAX_PER_NUMBER:
            continue

        source_id = str(raw_task["source_id"])
        source_guid = str(raw_task["source_guid"])
        grouped[exam_number].append(
            {
                "exam_number": exam_number,
                "topic": topic_from_kes(raw_task),
                "condition": str(raw_task["condition"]),
                "correct_answer": "",
                "accepted_answers": [],
                "explanation": None,
                "difficulty": "medium",
                "source": f"{SOURCE}:{source_id}:{source_guid}",
                "status": "draft",
            }
        )

    output: list[dict[str, object]] = []
    for exam_number in range(1, 19):
        output.extend(grouped.get(exam_number, []))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Fetched: {len(collected)}")
    print(f"Duplicates skipped: {duplicate_rows}")
    print(f"Written: {len(output)}")
    print(f"Skipped without 1-18 mapping: {skipped}")
    for exam_number in range(1, 19):
        print(f"{exam_number}: {len(grouped.get(exam_number, []))}")


if __name__ == "__main__":
    main()
