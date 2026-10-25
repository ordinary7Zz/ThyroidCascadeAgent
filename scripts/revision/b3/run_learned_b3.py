#!/usr/bin/env python3
"""B3 策略 6（learned）：委托 run_routing_ablation.py，默认 --routing-mode learned。

learned 推理为 CPU 逻辑回归；Phase 1–2 已缓存时建议 --device cpu。

示例:
  python scripts/revision/b3/fit_learned_router.py --config config/b3/tn3k.yaml
  python scripts/revision/b3/run_learned_b3.py \\
    --config config/b3/tn3k.yaml \\
    --shared-intermediate output/TN3K/pipeline_run/intermediate \\
    --output-dir output/ablation/b3/tn3k/learned \\
    --force-phase3 --device cpu
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
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

import yaml

import repo_path

ROOT = repo_path.install()


def _task_from_config(config_path: str) -> str:
    path = Path(config_path)
    if not path.is_absolute():
        path = ROOT / path
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return str(cfg.get("pipeline", {}).get("ablation", {}).get("task") or "both")


def main() -> None:
    argv = list(sys.argv[1:])
    if "--routing-mode" not in argv and "--routing-mode-seg" not in argv:
        argv = ["--routing-mode", "learned"] + argv
    if "--task" not in argv:
        cfg_path = None
        for i, a in enumerate(argv):
            if a == "--config" and i + 1 < len(argv):
                cfg_path = argv[i + 1]
                break
        if cfg_path:
            argv = argv + ["--task", _task_from_config(cfg_path)]
    runner = ROOT / "scripts" / "run_routing_ablation.py"
    cmd = [sys.executable, str(runner)] + argv
    raise SystemExit(subprocess.call(cmd, cwd=str(ROOT)))


if __name__ == "__main__":
    main()
