#!/usr/bin/env python3
"""Wrapper: run Classification_Models/b9_oof/export_folds.py from any cwd."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[3]  # ThyroidCascadeAgent
B9_OOF = repo.parent / "Classification_Models" / "b9_oof" / "export_folds.py"

if not B9_OOF.is_file():
    sys.stderr.write(f"Cannot find b9_oof export_folds.py (tried {B9_OOF})\n")
    sys.exit(1)

sys.argv[0] = str(B9_OOF)
runpy.run_path(str(B9_OOF), run_name="__main__")
