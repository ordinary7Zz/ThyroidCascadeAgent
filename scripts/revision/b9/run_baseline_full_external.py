#!/usr/bin/env python3
"""Wrapper: Classification_Models/b9_oof/run_baseline_full_external.py"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[3]
target = repo.parent / "Classification_Models" / "b9_oof" / "run_baseline_full_external.py"
if not target.is_file():
    sys.stderr.write(f"Missing {target}\n")
    sys.exit(1)
sys.argv[0] = str(target)
runpy.run_path(str(target), run_name="__main__")
