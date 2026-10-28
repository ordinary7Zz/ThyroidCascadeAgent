#!/usr/bin/env python3
"""由你本人在确认 AI 改稿后调用：追加 history.jsonl，并清空 current.json。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from round_close import execute_close

HERE = Path(__file__).resolve().parent
CURRENT = HERE / "current.json"
HISTORY = HERE / "history.jsonl"


def main() -> int:
    parser = argparse.ArgumentParser(description="Close review round: append history, clear current.")
    parser.add_argument("--entries", required=True, type=Path, help='JSON with {"entries": [...]}')
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.entries.is_file():
        print(f"Missing entries file: {args.entries}", file=sys.stderr)
        return 1
    payload = json.loads(args.entries.read_text(encoding="utf-8"))
    entries = payload.get("entries")
    record, err = execute_close(entries, CURRENT, HISTORY, dry_run=args.dry_run)
    if err:
        print(err, file=sys.stderr)
        return 1
    if args.dry_run:
        print(json.dumps(record, ensure_ascii=False, indent=2))
        print("Would reset current.json to empty round.")
        return 0
    print(f"Appended round {record['round_id']} to history.jsonl and cleared current.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
