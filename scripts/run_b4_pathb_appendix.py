#!/usr/bin/env python3
"""
B4 Path B 附录 B-b：独立模型 + AutoGluon 静态软投票（无 LLM）。

分割侧应与 L3 相同 mask 协议；sample 占位可与 L2 同用 soft_voting 的 selected_masks，
正式实验应使用 L3/llm 的 selected_masks.npz（见 REVISION_B3_B4_PLAN §5.1.2）。

示例（cls 重跑 Phase 4–5，seg 与 soft_voting 一致）:
  python scripts/run_b4_pathb_appendix.py \\
    --config config/b4/sample.yaml \\
    --shared-intermediate output/sample/pipeline_run/intermediate \\
    --output-dir output/ablation/b4/sample/path_b_autogluon \\
    --seg-mode soft_voting \\
    --force-phase3
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import repo_path

ROOT = repo_path.install()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="B4 Path B 附录 B-b 跑数")
    parser.add_argument("--config", default="config/b3/sample.yaml")
    parser.add_argument("--shared-intermediate", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--seg-mode", default="soft_voting", help="与 L3 对齐时改为 llm")
    parser.add_argument("--force-phase3", action="store_true")
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()

    runner = ROOT / "scripts" / "run_routing_ablation.py"
    cmd = [
        sys.executable,
        str(runner),
        "--config",
        args.config,
        "--routing-mode-seg",
        args.seg_mode,
        "--routing-mode-cls",
        "path_b_autogluon",
        "--task",
        "both",
        "--shared-intermediate",
        args.shared_intermediate,
        "--output-dir",
        args.output_dir,
        "--device",
        args.device,
    ]
    if args.force_phase3:
        cmd.append("--force-phase3")
    print(" ".join(cmd))
    raise SystemExit(subprocess.call(cmd, cwd=str(ROOT)))


if __name__ == "__main__":
    main()
