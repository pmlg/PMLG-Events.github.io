#!/usr/bin/env python3
"""Validate the repository-managed upcoming event feed."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "upcoming-events.json"
required = {"id", "title", "date", "description"}
feed = json.loads(path.read_text(encoding="utf-8"))
if not isinstance(feed, list):
    raise SystemExit("upcoming-events.json must contain a JSON array")

seen: set[str] = set()
for index, event in enumerate(feed, start=1):
    if not isinstance(event, dict):
        raise SystemExit(f"event {index} must be a JSON object")
    missing = sorted(required - event.keys())
    if missing:
        raise SystemExit(f"event {index} is missing: {', '.join(missing)}")
    event_id = event["id"]
    if not isinstance(event_id, str) or not event_id.strip():
        raise SystemExit(f"event {index} has an invalid id")
    if event_id in seen:
        raise SystemExit(f"duplicate event id: {event_id}")
    seen.add(event_id)
    title = event["title"]
    if not isinstance(title, str) or not title.strip():
        raise SystemExit(f"event {event_id} has an invalid title")
    event_date = event["date"]
    if not isinstance(event_date, str):
        raise SystemExit(f"event {event_id} has an invalid date")
    try:
        date.fromisoformat(event_date)
    except ValueError as error:
        raise SystemExit(f"event {event_id} date must use YYYY-MM-DD: {event_date}") from error
    if date.fromisoformat(event_date) < date.today():
        raise SystemExit(f"event {event_id} is dated in the past; move it to the archive")
    if not isinstance(event["description"], str) or not event["description"].strip():
        raise SystemExit(f"event {event_id} needs a non-empty description")

print(f"Validated {len(feed)} upcoming event(s) from {path}")
