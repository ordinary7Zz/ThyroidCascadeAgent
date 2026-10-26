#!/usr/bin/env python3
"""B5 元数据消融：固定 routing_mode=llm，遍历 metadata_mode。

示例:
  python scripts/revision/b5/run_b5_batch.py --config config/revision/b5/sample.yaml
  python scripts/revision/b5/run_b5_batch.py --config config/revision/b5/tn3k.yaml --force-phase3 --skip-full
  python scripts/revision/b5/run_b5_batch.py --config config/revision/b5/sample.yaml --modes drop_device quality_only
"""

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

import argparse
import os
import subprocess
import sys

import repo_path
import yaml

ROOT = repo_path.install()

from shared.metadata_prompt import METADATA_MODES, normalize_metadata_mode

DEFAULT_MODES = sorted(METADATA_MODES)


def _load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _child_env() -> dict[str, str]:
    env = os.environ.copy()
    root = str(ROOT)
    prev = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = root if not prev else f"{root}{os.pathsep}{prev}"
    return env


def main() -> None:
    parser = argparse.ArgumentParser(description="B5 metadata_mode batch (LLM routing)")
    parser.add_argument("--config", required=True, help="config/revision/b5/<cohort>.yaml")
    parser.add_argument(
        "--modes",
        nargs="+",
        default=None,
        help=f"metadata_mode 子集，默认 config 或 {DEFAULT_MODES}",
    )
    parser.add_argument("--skip-full", action="store_true", help="跳过 full（复用 B3 llm 目录）")
    parser.add_argument("--b3-llm-dir", default=None, help="B3 llm 输出目录，默认 output/ablation/b3/<cohort>/llm")
    parser.add_argument("--force-phase3", action="store_true")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--skip-eval", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cfg = _load_config(args.config)
    ab = cfg.get("pipeline", {}).get("ablation", {}) or {}
    shared = ab.get("shared_intermediate")
    if not shared:
        parser.error("config 须设置 pipeline.ablation.shared_intermediate")
    out_root = Path(ab.get("output_root") or "output/ablation/b5")
    modes_raw = args.modes or ab.get("metadata_modes") or DEFAULT_MODES
    modes = [normalize_metadata_mode(m) for m in modes_raw]

    cohort = ab.get("dataset_id")
    if args.skip_full and "full" in modes:
        modes = [m for m in modes if m != "full"]

    runner = ROOT / "scripts" / "run_routing_ablation.py"
    child_env = _child_env()
    task = ab.get("task", "both")

    if args.dry_run:
        for mode in modes:
            print(f"would run metadata_mode={mode} -> {out_root / mode}")
        if args.skip_full:
            b3_llm = args.b3_llm_dir or (
                f"output/ablation/b3/{cohort}/llm" if cohort else None
            )
            print(f"skip full; reuse B3 llm metrics from: {b3_llm or '(set --b3-llm-dir)'}")
        return

    for mode in modes:
        out_dir = out_root / mode
        cmd = [
            sys.executable,
            str(runner),
            "--config",
            args.config,
            "--routing-mode",
            "llm",
            "--metadata-mode",
            mode,
            "--task",
            task,
            "--shared-intermediate",
            str(shared),
            "--output-dir",
            str(out_dir),
            "--device",
            args.device,
        ]
        if args.force_phase3 or ab.get("force_phase3"):
            cmd.append("--force-phase3")
        if args.skip_eval:
            cmd.append("--skip-eval")
        print(f"\n>>> B5 {mode} -> {out_dir}")
        subprocess.check_call(cmd, cwd=str(ROOT), env=child_env)

    if args.skip_full:
        b3_llm = args.b3_llm_dir
        if not b3_llm and cohort:
            b3_llm = f"output/ablation/b3/{cohort}/llm"
        if b3_llm:
            print(f"提示: full 指标请从 B3 复制或软链: {b3_llm}")


if __name__ == "__main__":
    main()
