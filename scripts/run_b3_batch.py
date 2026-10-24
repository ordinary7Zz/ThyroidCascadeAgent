#!/usr/bin/env python3
"""兼容入口：旧命令 `python scripts/run_b3_batch.py` → revision/b3/run_b3_batch.py。"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

_TARGET = Path(__file__).resolve().parent / "revision" / "b3" / "run_b3_batch.py"
if not _TARGET.is_file():
    raise SystemExit(f"找不到 {_TARGET}")

sys.argv[0] = str(_TARGET)
runpy.run_path(str(_TARGET), run_name="__main__")
