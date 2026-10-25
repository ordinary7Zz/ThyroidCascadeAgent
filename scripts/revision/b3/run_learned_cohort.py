#!/usr/bin/env python3
"""单队列 B3 learned：按 ablation.task 做 fit（可选）→ infer → eval。

大队列 chunk 推理见 config/revision/b3/learned_wave3_cohorts.yaml 的 chunked_infer。
"""

from __future__ import annotations

import importlib.util
import json
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

import argparse

import repo_path
import yaml

ROOT = repo_path.install()

from routing.learned_router import ablation_task


def _load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _chunk_shared_dir(chunk_dir: Path) -> Path:
    inner = chunk_dir / "intermediate"
    if (inner / "seg").is_dir() or (inner / "cls").is_dir():
        return inner
    return chunk_dir


def _chunk_meta(chunk_dir: Path, chunk_size: int) -> tuple[int, int]:
    meta_path = chunk_dir / "chunk_meta.json"
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        return int(meta["start_index"]), int(meta["count"])
    base = chunk_dir.name
    idx = int(base.replace("chunk_", ""), 10)
    return idx * chunk_size, chunk_size


def _run(cmd: list[str], *, cwd: Path) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=str(cwd), check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="B3 learned 单 cohort")
    parser.add_argument("--config", default=None, help="config/b3/<id>.yaml（可与 --cohort-meta 二选一）")
    parser.add_argument(
        "--cohort-meta",
        required=True,
        help="learned_wave3_cohorts.yaml 中该 cohort 的键名（如 tn5k）",
    )
    parser.add_argument("--skip-fit", action="store_true")
    parser.add_argument("--skip-infer", action="store_true")
    parser.add_argument("--skip-eval", action="store_true")
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--manifest",
        default="config/revision/b3/learned_wave3_cohorts.yaml",
    )
    args = parser.parse_args()

    manifest_path = ROOT / args.manifest
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    manifest = _load_yaml(manifest_path)
    meta = (manifest.get("cohorts") or {}).get(args.cohort_meta) or {}
    if not meta:
        raise KeyError(f"manifest 无 cohort: {args.cohort_meta}")

    cfg_rel = args.config or meta.get("config")
    if not cfg_rel:
        raise ValueError("须指定 --config 或在 manifest 中配置 config")
    cfg_path = Path(cfg_rel)
    if not cfg_path.is_absolute():
        cfg_path = ROOT / cfg_path
    config = _load_yaml(cfg_path)
    ab = config.get("pipeline", {}).get("ablation", {}) or {}
    task = ablation_task(config)

    val_int = meta.get("val_intermediate") or ab.get("val_intermediate")
    test_int = meta.get("test_intermediate") or ab.get("shared_intermediate")
    out_dir = meta.get("output_dir") or f"{ab.get('output_root', 'output/ablation/b3')}/learned"
    out_path = Path(out_dir)
    if not out_path.is_absolute():
        out_path = ROOT / out_path

    py = sys.executable
    fit_script = ROOT / "scripts/revision/b3/fit_learned_router.py"
    infer_script = ROOT / "scripts/revision/b3/run_learned_b3.py"
    eval_script = ROOT / "scripts/revision/b3/eval_merged_b3_cohort.py"
    merge_script = ROOT / "scripts/revision/b3/zjh/merge_b3_chunk_outputs.py"

    if not args.skip_fit:
        if not val_int:
            raise ValueError(
                f"[{args.cohort_meta}] 未配置 val_intermediate（见 config 与 {manifest_path.name}）"
            )
        else:
            val_path = Path(val_int)
            if not val_path.is_absolute():
                val_path = ROOT / val_path
            if not (val_path / "seg").is_dir() and task in ("seg", "both"):
                if not (val_path / "cls").is_dir():
                    raise FileNotFoundError(f"val intermediate 不存在: {val_path}")
            fit_cmd = [
                py,
                str(fit_script),
                "--config",
                str(cfg_path),
                "--intermediate",
                str(val_path),
                "--task",
                task,
            ]
            _run(fit_cmd, cwd=ROOT)

    chunked = meta.get("chunked_infer") or {}
    chunk_root = chunked.get("chunk_root")

    if not args.skip_infer:
        if chunk_root:
            chunk_root_path = Path(chunk_root)
            if not chunk_root_path.is_absolute():
                chunk_root_path = ROOT / chunk_root_path
            out_chunks = Path(chunked.get("output_chunks") or f"{out_path.parent}_learned_chunks")
            if not out_chunks.is_absolute():
                out_chunks = ROOT / out_chunks
            chunk_size = int(chunked.get("chunk_size", 1000))
            chunk_dirs = sorted(chunk_root_path.glob("chunk_*"))
            if not chunk_dirs:
                raise FileNotFoundError(f"无 chunk 目录: {chunk_root_path}")
            runner = ROOT / "scripts" / "run_routing_ablation.py"
            for chunk_dir in chunk_dirs:
                shared = _chunk_shared_dir(chunk_dir)
                start, count = _chunk_meta(chunk_dir, chunk_size)
                chunk_out = out_chunks / chunk_dir.name / "learned"
                chunk_out.mkdir(parents=True, exist_ok=True)
                infer_cmd = [
                    py,
                    str(runner),
                    "--config",
                    str(cfg_path),
                    "--routing-mode",
                    "learned",
                    "--shared-intermediate",
                    str(shared),
                    "--output-dir",
                    str(chunk_out),
                    "--force-phase3",
                    "--device",
                    args.device,
                    "--task",
                    task,
                    "--start-index",
                    str(start),
                    "--max-images",
                    str(count),
                ]
                _run(infer_cmd, cwd=ROOT)

            dest = Path(chunked.get("merge_dest") or out_path.parent)
            if not dest.is_absolute():
                dest = ROOT / dest
            _run(
                [
                    py,
                    str(merge_script),
                    "--chunks",
                    str(out_chunks),
                    "--dest",
                    str(dest),
                    "--modes",
                    "learned",
                    "--summarize",
                ],
                cwd=ROOT,
            )
        else:
            if not test_int:
                raise ValueError("未配置 test shared_intermediate")
            test_path = Path(test_int)
            if not test_path.is_absolute():
                test_path = ROOT / test_path
            out_path.mkdir(parents=True, exist_ok=True)
            _run(
                [
                    py,
                    str(infer_script),
                    "--config",
                    str(cfg_path),
                    "--shared-intermediate",
                    str(test_path),
                    "--output-dir",
                    str(out_path),
                    "--force-phase3",
                    "--device",
                    args.device,
                ],
                cwd=ROOT,
            )

    if not args.skip_eval:
        eval_root = Path(chunked.get("merge_dest") or out_path.parent)
        if not eval_root.is_absolute():
            eval_root = ROOT / eval_root
        _run(
            [
                py,
                str(eval_script),
                "--config",
                str(cfg_path),
                "--root",
                str(eval_root),
                "--modes",
                "learned",
            ],
            cwd=ROOT,
        )

    print(f"完成 cohort config={cfg_path.name} task={task}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
