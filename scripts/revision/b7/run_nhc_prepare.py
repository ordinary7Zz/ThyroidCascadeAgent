#!/usr/bin/env python3
"""CLI：B7 NHC 原始数据 → processed（中心统计 + labels 含 center_id）。"""

from __future__ import annotations

import importlib.util
from pathlib import Path


def __revision_bootstrap() -> None:
    p = Path(__file__).resolve()
    for d in [p.parent, *p.parents]:
        if d.name == "revision" and (d / "_path_setup.py").is_file():
            spec = importlib.util.spec_from_file_location("_rev_path_setup", d / "_path_setup.py")
            mod = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(mod)
            mod.bootstrap(__file__)
            return
    raise RuntimeError(f"revision _path_setup.py not found above {__file__}")


__revision_bootstrap()

import repo_path

repo_path.install()

from pipeline.revision.b7.nhc_prepare_data import main

if __name__ == "__main__":
    raise SystemExit(main())
