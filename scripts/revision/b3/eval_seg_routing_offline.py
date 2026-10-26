#!/usr/bin/env python3
"""离线评测多种分割 routing_mode（读 intermediate，与 compare_models 指标一致）。"""

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

from routing.best_single_expert import get_best_single_names
from pipeline.revision.b3.seg_routing_offline import evaluate_seg_mode_ladder


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/revision/b3/sample.yaml")
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

import importlib.util
from pathlib import Path


