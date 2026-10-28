"""Shared logic: append history.jsonl and reset current.json."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EMPTY_CURRENT: dict[str, Any] = {
    "schema_version": 1,
    "round_id": None,
    "updated_at": None,
    "comments": [],
}

VALID_ACTIONS = frozenset({"applied", "skipped", "partial"})


def validate_close_payload(current: dict, entries: list) -> str | None:
    comments = current.get("comments") or []
    if not comments:
        return "current has no comments"
    round_id = current.get("round_id")
    if not round_id:
        return "current round_id is empty"
    if not isinstance(entries, list) or not entries:
        return "entries must be a non-empty array"

    known_ids = {c["id"] for c in comments if isinstance(c, dict) and c.get("id")}
    seen: set[str] = set()
    for i, ent in enumerate(entries):
        if not isinstance(ent, dict):
            return f"entries[{i}] is not an object"
        cid = ent.get("comment_id")
        if cid not in known_ids:
            return f"entries[{i}] comment_id {cid!r} not in current comments"
        if cid in seen:
            return f"duplicate comment_id {cid!r}"
        seen.add(cid)
        action = ent.get("action")
        if action not in VALID_ACTIONS:
            return f"entries[{i}] action must be applied|skipped|partial"
        summary = (ent.get("summary") or "").strip()
        if action != "skipped" and not summary:
            return f"entries[{i}] summary required unless action is skipped"

    missing = known_ids - seen
    if missing:
        return f"missing entries for comment ids: {', '.join(sorted(missing))}"

    return None


def build_history_record(current: dict, entries: list) -> dict:
    return {
        "schema_version": 1,
        "round_id": current["round_id"],
        "closed_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "entries": entries,
    }


def execute_close(
    entries: list,
    current_path: Path,
    history_path: Path,
    *,
    dry_run: bool = False,
) -> tuple[dict | None, str | None]:
    """Returns (history_record, error_message)."""
    if not current_path.is_file():
        return None, "current.json not found"
    try:
        current = json.loads(current_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, "current.json is invalid JSON"

    err = validate_close_payload(current, entries)
    if err:
        return None, err

    record = build_history_record(current, entries)
    if dry_run:
        return record, None

    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    current_path.write_text(
        json.dumps(EMPTY_CURRENT, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return record, None
