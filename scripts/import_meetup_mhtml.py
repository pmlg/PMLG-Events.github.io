#!/usr/bin/env python3
"""Extract compact Meetup event records from saved MHTML files or ZIP archives.

The importer stores event metadata and description text only. It applies a
transparent fallback for legacy events without descriptions, and never copies
original MHTML files, embedded images, scripts, cookies, or Meetup chrome.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Iterable, Iterator
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

TIME_RANGE_RE = re.compile(
    r"(?P<start>\d{1,2}:\d{2}\s*[AP]M)"
    r"(?:\s*to\s*(?P<end>\d{1,2}:\d{2}\s*[AP]M))?"
    r"(?:\s+(?P<timezone>[A-Z]{2,8}))?",
    re.IGNORECASE,
)
EVENT_ID_RE = re.compile(r"/events/(\d+)(?:/|$)")

FALLBACK_DESCRIPTION = (
    "Event details were not available in the archived Meetup page. "
    "The event title, date, and location have been preserved where recorded."
)


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"\s+", " ", value.replace("\xa0", " "))
    return value.strip()


def first_text(tag: Tag | None) -> str:
    return clean_text(tag.get_text(" ", strip=True) if tag else "")


def first_html_part(message) -> tuple[str, str]:
    for part in message.walk():
        if part.get_content_type() == "text/html":
            payload = part.get_payload(decode=True) or b""
            charset = part.get_content_charset() or "utf-8"
            return payload.decode(charset, errors="replace"), part.get("Content-Location", "")
    return "", ""


def canonical_url(soup: BeautifulSoup, content_location: str) -> str:
    og_url = soup.find("meta", attrs={"property": "og:url"})
    candidate = content_location or (og_url.get("content", "") if og_url else "")
    if not candidate:
        return ""
    parsed = urlparse(candidate)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    return candidate.split("?", 1)[0]


def event_id(url: str, title: str, date: str, source_file: str) -> str:
    match = EVENT_ID_RE.search(url)
    if match:
        return match.group(1)
    seed = "|".join([title, date, source_file])
    return "mhtml-" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]


def extract_time_fields(time_node: Tag | None) -> tuple[str, str, str, str]:
    if not time_node:
        return "", "", "", ""
    datetime_value = clean_text(time_node.get("datetime", ""))
    date = datetime_value[:10] if re.match(r"^\d{4}-\d{2}-\d{2}", datetime_value) else ""
    display = first_text(time_node)
    match = TIME_RANGE_RE.search(display)
    if not match:
        return date, "", "", ""
    return (
        date,
        clean_text(match.group("start")).upper(),
        clean_text(match.group("end")).upper(),
        clean_text(match.group("timezone")).upper(),
    )


def extract_description(soup: BeautifulSoup) -> str:
    meta = soup.find("meta", attrs={"name": "description"})
    fallback = clean_text(meta.get("content", "") if meta else "")

    details_label = soup.find(string=lambda value: value and value.strip().lower() == "details")
    if details_label:
        section = details_label.find_parent("section")
        if section:
            preferred = section.select_one("div.break-words")
            if preferred:
                text = clean_text(preferred.get_text(" ", strip=True))
                if len(text) >= 40:
                    return text
            candidates = []
            for tag in section.find_all(["p", "div"]):
                text = clean_text(tag.get_text(" ", strip=True))
                classes = " ".join(tag.get("class", []))
                if len(text) >= 40 and "details" not in text[:30].lower() and "break-words" in classes:
                    candidates.append(text)
            if candidates:
                return min(candidates, key=len)

    if len(fallback) >= 40:
        return fallback

    return FALLBACK_DESCRIPTION


def extract_organisers(soup: BeautifulSoup) -> list[str]:
    link = soup.find(attrs={"data-event-label": "hosted-by"})
    if not link:
        return []
    label = clean_text(link.get("aria-label", "")) or first_text(link)
    label = re.sub(r"^Hosted by\s*", "", label, flags=re.IGNORECASE)
    if not label:
        return []
    return [clean_text(part) for part in re.split(r"\s+and\s+|,", label) if clean_text(part)]


def extract_location(soup: BeautifulSoup, time_node: Tag | None) -> str:
    if not time_node:
        return ""
    aside = time_node.find_parent("aside")
    if not aside:
        return ""
    paragraphs = aside.find_all("p")
    time_text = first_text(time_node)
    for index, paragraph in enumerate(paragraphs):
        if first_text(paragraph) == time_text:
            venue = first_text(paragraphs[index + 1]) if index + 1 < len(paragraphs) else ""
            address = first_text(paragraphs[index + 2]) if index + 2 < len(paragraphs) else ""
            return " · ".join(part for part in [venue, address] if part)
    return ""


def extract_attendees(soup: BeautifulSoup) -> int | None:
    heading = next(
        (
            tag
            for tag in soup.find_all(["h2", "h3"])
            if clean_text(tag.get_text(" ", strip=True)).lower() == "attendees"
        ),
        None,
    )
    if not heading:
        return None
    current = heading
    for _ in range(4):
        current = current.parent if current else None
        if not current:
            break
        for span in current.find_all("span"):
            text = clean_text(span.get_text(" ", strip=True)).replace(",", "")
            if text.isdigit():
                return int(text)
    return None


def infer_status(date: str, as_of: datetime) -> str:
    if not date:
        return "past"
    try:
        event_date = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return "past"
    return "upcoming" if event_date.date() >= as_of.date() else "past"


def extract_event_from_bytes(content: bytes, filename: str, as_of: datetime) -> dict:
    message = BytesParser(policy=policy.default).parsebytes(content)
    html, content_location = first_html_part(message)
    soup = BeautifulSoup(html, "html.parser")
    title = first_text(soup.find("h1"))
    time_node = soup.find("time", attrs={"datetime": True})
    date, start_time, end_time, tz_name = extract_time_fields(time_node)
    url = canonical_url(soup, content_location)
    record = {
        "id": event_id(url, title, date, filename),
        "title": title or filename,
        "date": date,
        "time": start_time,
        "endTime": end_time,
        "timezone": tz_name,
        "location": extract_location(soup, time_node),
        "description": extract_description(soup),
        "attendees": extract_attendees(soup),
        "organisers": extract_organisers(soup),
        "topics": [],
        "status": infer_status(date, as_of),
        "url": url,
        "sourceFile": filename,
    }
    return {key: value for key, value in record.items() if value not in ("", [], None)}


def iter_sources(input_path: Path) -> Iterator[tuple[str, bytes]]:
    if input_path.is_file():
        if input_path.suffix.lower() in {".mhtml", ".mht"}:
            yield input_path.name, input_path.read_bytes()
            return
        if input_path.suffix.lower() == ".zip":
            with zipfile.ZipFile(input_path, "r") as zf:
                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    name_lower = info.filename.lower()
                    if name_lower.endswith((".mhtml", ".mht")) and not info.filename.startswith("__MACOSX/"):
                        with zf.open(info) as f:
                            yield Path(info.filename).name, f.read()
            return
    if input_path.is_dir():
        for path in sorted(input_path.rglob("*")):
            if path.is_file() and path.suffix.lower() in {".mhtml", ".mht"}:
                yield path.name, path.read_bytes()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path, help="MHTML files, directories, or ZIP archives")
    parser.add_argument("--output", type=Path, default=Path("client/src/data/events-archive.json"), help="Output JSON path")
    parser.add_argument("--as-of", default="", help="ISO date used to classify upcoming events")
    # pnpm may forward a literal separator; remove it before argparse so the
    # following --output and --as-of options are still interpreted as flags.
    args = parser.parse_args([value for value in sys.argv[1:] if value != "--"])

    as_of = datetime.now(timezone.utc)
    if args.as_of:
        as_of = datetime.fromisoformat(args.as_of).replace(tzinfo=timezone.utc)

    existing_records = []
    if args.output.is_file():
        try:
            existing_records = json.loads(args.output.read_text(encoding="utf-8"))
        except Exception:
            existing_records = []

    records_map = {
        record.get("id"): record
        for record in existing_records
        if record.get("id") and record.get("title") and record.get("date") and record.get("title") != "Error"
    }
    files_found = 0
    failures = []
    skipped = []

    for input_path in args.inputs:
        if not input_path.exists():
            failures.append({"input": str(input_path), "error": "Path does not exist"})
            continue
        for filename, content in iter_sources(input_path):
            files_found += 1
            try:
                record = extract_event_from_bytes(content, filename, as_of)
                if record.get("title") and record.get("date") and record.get("title") != "Error":
                    records_map[record["id"]] = record
                else:
                    skipped.append({
                        "file": filename,
                        "reason": "Missing a valid event title or date; likely an error/not-found page",
                        "title": record.get("title", ""),
                    })
            except Exception as exc:
                failures.append({"file": filename, "error": str(exc)})

    ordered = sorted(records_map.values(), key=lambda record: (record.get("date", ""), record.get("title", "")), reverse=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "filesProcessed": files_found,
                "totalArchiveRecords": len(ordered),
                "skipped": skipped,
                "failures": failures,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
