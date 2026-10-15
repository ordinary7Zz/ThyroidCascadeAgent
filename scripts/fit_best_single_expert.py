#!/usr/bin/env python3
"""在验证集上选择 best_single 专家，写出 artifact JSON。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import repo_path
import yaml

ROOT = repo_path.install()

from routing.best_single_expert import fit_best_single_on_val


def main():
    parser = argparse.ArgumentParser(description="B3 策略 1：val 上选最优单专家")
    parser.add_argument("--config", default="config/b3/sample.yaml")
    parser.add_argument("--intermediate", required=True, help="含 seg/ cls 的 intermediate 目录")
    parser.add_argument(
        "--out",
        default="artifacts/best_single.json",
        help="输出 artifact 路径",
    )
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    data = config.get("pipeline", {}).get("data", {})
    payload = fit_best_single_on_val(
        config,
        Path(args.intermediate),
        gt_mask_dir=Path(data["gt_mask_dir"]),
        label_file=data["label_file"],
        label_key=data.get("label_key", "malignancy"),
        artifact_path=Path(args.out),
    )
    print(json.dumps({
        "artifact": args.out,
        "best_single_seg": payload["best_single_seg"],
        "best_single_cls": payload["best_single_cls"],
        "n_val": len(payload["val_stems"]),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
