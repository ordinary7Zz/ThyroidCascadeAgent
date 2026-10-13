#!/usr/bin/env python3
"""离线评测多种分割 routing_mode（读 intermediate，与 compare_models 指标一致）。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import repo_path
import yaml

ROOT = repo_path.install()

from pipeline.routing_ablation import get_best_single_names
from pipeline.seg_routing_offline import evaluate_seg_mode_ladder


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/ablation_b3.yaml")
    parser.add_argument("--intermediate", required=True)
    parser.add_argument(
        "--modes",
        default="soft_voting,majority,max_confidence,best_single,oracle",
    )
    parser.add_argument("--out", default=None, help="JSON 输出路径")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    gt = cfg["pipeline"]["data"]["gt_mask_dir"]
    modes = [m.strip() for m in args.modes.split(",") if m.strip()]
    best_seg, _ = get_best_single_names(cfg)

    rows = evaluate_seg_mode_ladder(Path(args.intermediate), gt, modes, best_single_model=best_seg)
    out_path = Path(args.out) if args.out else Path(args.intermediate).parent / "seg_routing_offline.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"已写入 {out_path}")


if __name__ == "__main__":
    main()
