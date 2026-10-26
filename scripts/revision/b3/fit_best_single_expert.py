#!/usr/bin/env python3
"""在验证集上选择 best_single 专家，写出 artifact JSON。"""

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

import importlib.util
from pathlib import Path

import argparse
import json
from pathlib import Path

import repo_path
import yaml

ROOT = repo_path.install()

from routing.best_single_expert import fit_best_single_on_val, resolve_val_fit_paths


def main():
    parser = argparse.ArgumentParser(description="B3 策略 1：val 上选最优单专家")
    parser.add_argument("--config", default="config/revision/b3/sample.yaml")
    parser.add_argument("--intermediate", required=True, help="含 seg/ cls 的 intermediate 目录")
    parser.add_argument(
        "--out",
        default="artifacts/best_single.json",
        help="输出 artifact 路径",
    )
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    gt_mask_dir, label_file, label_key = resolve_val_fit_paths(config)
    payload = fit_best_single_on_val(
        config,
        Path(args.intermediate),
        gt_mask_dir=gt_mask_dir,
        label_file=label_file,
        label_key=label_key,
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

