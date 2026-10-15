#!/usr/bin/env python3
"""
B3 策略 6（learned）单独跑数：不与 static bundle 的六种策略同批扫图。

learned 推理为 CPU 上逻辑回归；Phase 1–2 已缓存时可用 ``--device cpu`` 避免占 GPU。

示例:
  python scripts/fit_learned_router.py --config config/b3/sample.yaml --random-init
  python scripts/run_learned_b3.py \\
    --config config/b3/sample.yaml \\
    --shared-intermediate output/sample/pipeline_run/intermediate \\
    --output-dir output/ablation/b3/sample/learned \\
    --force-phase3 --device cpu
"""

from __future__ import annotations

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
