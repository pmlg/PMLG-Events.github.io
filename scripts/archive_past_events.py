"""Automated script to migrate past events from upcoming-events.json into events-archive.json at the repository root."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPCOMING_PATH = ROOT / "upcoming-events.json"
ARCHIVE_PATH = ROOT / "events-archive.json"


def main() -> None:
    if not UPCOMING_PATH.exists():
        print(f"No upcoming-events.json found at {UPCOMING_PATH}; nothing to migrate.")
        return

    upcoming_raw = json.loads(UPCOMING_PATH.read_text(encoding="utf-8"))
    if not isinstance(upcoming_raw, list):
        raise SystemExit("upcoming-events.json must contain a JSON array.")

    today = date.today()
    active_upcoming = []
    migrated_count = 0

    archive_raw = json.loads(ARCHIVE_PATH.read_text(encoding="utf-8")) if ARCHIVE_PATH.exists() else []
    if not isinstance(archive_raw, list):
        archive_raw = []

    existing_ids = {item.get("id") for item in archive_raw if isinstance(item, dict) and "id" in item}

    for event in upcoming_raw:
        if not isinstance(event, dict):
            continue
        event_date_str = event.get("date", "")
        try:
            event_date = date.fromisoformat(event_date_str)
        except ValueError:
            active_upcoming.append(event)
            continue

        if event_date < today:
            event["status"] = "past"
            event_id = event.get("id")
            if event_id not in existing_ids:
                archive_raw.append(event)
                existing_ids.add(event_id)
            migrated_count += 1
            print(f"Migrated past event to archive: {event.get('title')} ({event_date_str})")
        else:
            active_upcoming.append(event)

    if migrated_count > 0:
        archive_raw.sort(key=lambda x: x.get("date", ""), reverse=True)
        ARCHIVE_PATH.write_text(json.dumps(archive_raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        UPCOMING_PATH.write_text(json.dumps(active_upcoming, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Successfully migrated {migrated_count} past event(s). Archive now has {len(archive_raw)} records.")
    else:
        print("No past events found in upcoming-events.json; no migration needed.")


if __name__ == "__main__":
    main()
