#!/usr/bin/env python3
"""合并各 chunk 的 B3 输出到单一 output_root（按 image 全队列排序）。

  python scripts/revision/b3/zjh/merge_b3_chunk_outputs.py \\
    --chunks output/ablation/b3/zjh8k_chunks \\
    --dest output/ablation/b3/zjh8k \\
    --modes soft_voting,majority,max_confidence,best_single,oracle,static_rule

合并后可在 --dest 上运行 pipeline.revision.b3.ablation_summary。
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
import json
import pickle
import subprocess
import sys
from pathlib import Path

import numpy as np

import repo_path

ROOT = repo_path.install()


def _load_results(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return data.get("results", data)


def _merge_results_json(chunk_dirs: list[Path], mode: str, dest_mode: Path) -> int:
    merged: list[dict] = []
    seen: set[str] = set()
    for ch in chunk_dirs:
        p = ch / mode / "results.json"
        if not p.is_file():
            raise FileNotFoundError(p)
        for row in _load_results(p):
            name = row.get("image_name", "")
            if name in seen:
                raise ValueError(f"重复 image_name {name} in {p}")
            seen.add(name)
            merged.append(row)
    merged.sort(key=lambda r: r.get("image_name", ""))
    dest_mode.mkdir(parents=True, exist_ok=True)
    out = dest_mode / "results.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    return len(merged)


def _merge_selected_masks(chunk_dirs: list[Path], mode: str, dest_mode: Path) -> None:
    names: list[str] = []
    masks: list[np.ndarray] = []
    decisions: list[dict] = []
    for ch in sorted(chunk_dirs):
        p = ch / mode / "intermediate" / "selected_masks.npz"
        if not p.is_file():
            continue
        data = np.load(str(p), allow_pickle=True)
        chunk_names = list(data["image_names"])
        chunk_masks = list(data["selected_masks"])
        chunk_dec = pickle.loads(data["seg_decisions"].item())
        names.extend(chunk_names)
        masks.extend(chunk_masks)
        decisions.extend(chunk_dec)

    if not names:
        return
    inter = dest_mode / "intermediate"
    inter.mkdir(parents=True, exist_ok=True)
    from pipeline.cascade import CascadePipeline

    CascadePipeline._save_selected_masks_npz(
        inter / "selected_masks.npz", names, masks, decisions
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="合并 B3 chunk 输出")
    parser.add_argument("--chunks", required=True, help="各 chunk 输出根目录（含 chunk_00/...）")
    parser.add_argument("--dest", required=True, help="合并后的 output_root")
    parser.add_argument("--modes", required=True, help="逗号分隔 mode 目录名")
    parser.add_argument("--summarize", action="store_true")
    args = parser.parse_args()

    chunks_root = Path(args.chunks)
    chunk_dirs = sorted(chunks_root.glob("chunk_*"))
    if not chunk_dirs:
        raise SystemExit(f"未找到 chunk_* 于 {chunks_root}")

    dest = Path(args.dest)
    modes = [m.strip() for m in args.modes.split(",") if m.strip()]

    for mode in modes:
        n = _merge_results_json(chunk_dirs, mode, dest / mode)
        print(f"  {mode}: results.json × {n}")
        _merge_selected_masks(chunk_dirs, mode, dest / mode)

    if args.summarize:
        cmd = [
            sys.executable,
            "-m",
            "pipeline.revision.b3.ablation_summary",
            "--root",
            str(dest),
        ]
        ref = dest / modes[0] / "intermediate_manifest.json"
        if ref.is_file():
            cmd.extend(["--reference-manifest", str(ref)])
        print("汇总:", " ".join(cmd))
        subprocess.check_call(cmd, cwd=str(ROOT))

    print(f"合并完成: {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
