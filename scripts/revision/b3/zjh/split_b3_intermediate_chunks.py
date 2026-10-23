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

将大队列 B3 shared intermediate 按图像顺序切成多份（每份像 TN3K 规模的小 npz）。

不复制原图、不重跑 Phase1–2；仅在 NFS 上写出 intermediate_chunks/chunk_XX/。

每份 chunk 的 npz 只含该段图像，B3 bundle 预加载时内存≈单段大小（适合 ~40G cgroup）。

用法:
  python scripts/revision/b3/zjh/split_b3_intermediate_chunks.py \\
    --source output/ZJH-8K/pipeline_run/intermediate \\
    --dest output/ZJH-8K/pipeline_run/intermediate_chunks \\
    --chunk-size 1000
"""

from __future__ import annotations

import importlib.util
from pathlib import Path



import argparse
import json
import pickle
import shutil
from pathlib import Path

import numpy as np

import repo_path

repo_path.install()

from pipeline.cascade import CascadePipeline


def _slice_seg_npz(src: Path, dst: Path, i0: int, i1: int) -> None:
    data = np.load(str(src), allow_pickle=True, mmap_mode="r")
    names = list(data["image_names"][i0:i1])
    if not names:
        raise ValueError(f"空切片 {src} [{i0}:{i1}]")

    from segmentation.base_model import SegModelOutput

    metas = pickle.loads(data["metadata"].item())
    outputs = []
    for j in range(i0, i1):
        mask = np.asarray(data["masks"][j], dtype=np.uint8)
        conf = data["confidence_maps"][j]
        has_conf = conf.shape != (1, 1)
        conf_val = np.asarray(conf, dtype=np.float32) if has_conf else None
        meta = metas[j] if j < len(metas) else {}
        model_name = str(data["model_names"][j]) if "model_names" in data else str(meta.get("model_name", ""))
        outputs.append(
            SegModelOutput(
                model_name=model_name,
                mask=mask,
                confidence_map=conf_val,
                metadata=meta,
            )
        )
    data.close()
    CascadePipeline._save_seg_npz(dst, names, outputs)


def _slice_cls_json(src: Path, dst: Path, image_names: list[str]) -> None:
    with open(src, "r", encoding="utf-8") as f:
        data = json.load(f)
    all_results = data.get("results", {})
    ordered = {name: all_results[name] for name in image_names if name in all_results}
    missing = [n for n in image_names if n not in all_results]
    if missing:
        raise KeyError(f"{src.name} 缺少 {len(missing)} 条分类结果，例: {missing[:3]}")
    out = {"model_name": data.get("model_name", ""), "results": ordered}
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="切分 B3 intermediate 为多个 chunk")
    parser.add_argument("--source", required=True, help="原 intermediate 目录")
    parser.add_argument("--dest", required=True, help="输出 intermediate_chunks 根目录")
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    src_root = Path(args.source).resolve()
    dest_root = Path(args.dest).resolve()
    seg_dir = src_root / "seg"
    cls_dir = src_root / "cls"
    if not seg_dir.is_dir():
        raise SystemExit(f"缺少 {seg_dir}")

    ref_npz = sorted(seg_dir.glob("*.npz"))[0]
    ref = np.load(str(ref_npz), allow_pickle=True, mmap_mode="r")
    n_total = len(ref["image_names"])
    all_names = [str(x) for x in ref["image_names"]]
    ref.close()

    chunk_size = max(1, args.chunk_size)
    n_chunks = (n_total + chunk_size - 1) // chunk_size
    print(f"参考: {ref_npz.name}，共 {n_total} 张 → {n_chunks} 个 chunk（每段 ≤{chunk_size} 张）")

    if args.dry_run:
        for c in range(n_chunks):
            i0, i1 = c * chunk_size, min((c + 1) * chunk_size, n_total)
            print(f"  chunk_{c:02d}: [{i0}:{i1}) = {i1 - i0} 张")
        return

    dest_root.mkdir(parents=True, exist_ok=True)
    seg_files = sorted(seg_dir.glob("*.npz"))
    cls_files = sorted(cls_dir.glob("*.json")) if cls_dir.is_dir() else []

    for c in range(n_chunks):
        i0 = c * chunk_size
        i1 = min((c + 1) * chunk_size, n_total)
        chunk_names = all_names[i0:i1]
        chunk_dir = dest_root / f"chunk_{c:02d}"
        (chunk_dir / "seg").mkdir(parents=True, exist_ok=True)
        (chunk_dir / "cls").mkdir(parents=True, exist_ok=True)

        meta = {
            "chunk_index": c,
            "start_index": i0,
            "end_index": i1,
            "count": i1 - i0,
            "image_names": chunk_names,
        }
        with open(chunk_dir / "chunk_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        for npz in seg_files:
            print(f"  chunk_{c:02d} seg {npz.name} ...", flush=True)
            _slice_seg_npz(npz, chunk_dir / "seg" / npz.name, i0, i1)

        for js in cls_files:
            print(f"  chunk_{c:02d} cls {js.name} ...", flush=True)
            _slice_cls_json(js, chunk_dir / "cls" / js.name, chunk_names)

        ag = src_root / "autogluon.json"
        if ag.is_file():
            dst_ag = chunk_dir / "autogluon.json"
            if dst_ag.exists() or dst_ag.is_symlink():
                dst_ag.unlink()
            shutil.copy2(ag, dst_ag)

    print(f"完成: {dest_root}（{n_chunks} 个 chunk）")


if __name__ == "__main__":
    main()
