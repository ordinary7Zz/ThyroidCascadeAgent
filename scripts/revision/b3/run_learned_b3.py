#!/usr/bin/env python3
"""
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

import importlib.util
from pathlib import Path

B3 策略 6（learned）单独跑数：不与 static bundle 的六种策略同批扫图。

learned 推理为 CPU 上逻辑回归；Phase 1–2 已缓存时可用 ``--device cpu`` 避免占 GPU。

示例:
  python scripts/revision/b3/fit_learned_router.py --config config/b3/sample.yaml --random-init
  python scripts/revision/b3/run_learned_b3.py \\
    --config config/b3/sample.yaml \\
    --shared-intermediate output/sample/pipeline_run/intermediate \\
    --output-dir output/ablation/b3/sample/learned \\
    --force-phase3 --device cpu
"""

from __future__ import annotations

import importlib.util
from pathlib import Path



import subprocess
import sys

import repo_path

ROOT = repo_path.install()


def main() -> None:
    argv = list(sys.argv[1:])
    if "--routing-mode" not in argv and "--routing-mode-seg" not in argv:
        argv = ["--routing-mode", "learned"] + argv
    runner = ROOT / "scripts" / "run_routing_ablation.py"
    cmd = [sys.executable, str(runner)] + argv
    raise SystemExit(subprocess.call(cmd, cwd=str(ROOT)))


if __name__ == "__main__":
    main()
