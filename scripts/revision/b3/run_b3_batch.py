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

一次性跑多个 B3 路由组合（波次 0–1），可选末尾汇总 CSV。

mode 列表优先级：--modes > config pipeline.ablation.routing_modes > --preset

config 每项可为:
  - soft_voting
  - { seg: static_rule, cls: soft_voting, name: my_run }

CLI --modes 支持 ``seg:cls`` 简写，如 ``static_rule:soft_voting``。

推荐：**各 routing 策略串行**（默认 ``--jobs 1``）；单次 run 内读 intermediate 的并行见
``pipeline.preload_workers``（Phase 3 预加载 seg/cls 缓存）。

可选 ``--jobs N``：整策略多子进程并行（占 GPU，一般不必开）。
"""

from __future__ import annotations

import importlib.util
from pathlib import Path



import argparse
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import repo_path
import yaml

ROOT = repo_path.install()

from pipeline.routing_ablation import (
    AblationRoutingEntry,
    get_ablation_batch_settings,
    parse_ablation_routing_entry,
)

WAVE1_MODES = (
    "soft_voting",
    "majority",
    "max_confidence",
    "static_rule",
    "best_single",
    "oracle",
)


def _load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _parse_cli_mode_token(token: str):
    token = token.strip()
    if not token:
        raise ValueError("空 mode")
    for sep in (":", "|"):
        if sep in token:
            seg, cls = token.split(sep, 1)
            return parse_ablation_routing_entry({"seg": seg.strip(), "cls": cls.strip()})
    return parse_ablation_routing_entry(token)


def _child_env() -> dict[str, str]:
    env = os.environ.copy()
    root = str(ROOT)
    prev = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = root if not prev else f"{root}{os.pathsep}{prev}"
    return env


def _build_ablation_cmd(
    entry: AblationRoutingEntry,
    *,
    runner: Path,
    config_path: str,
    task: str,
    shared: Path,
    out_root: Path,
    device: str,
    force_phase3: bool,
    skip_eval: bool,
) -> list[str]:
    out_dir = out_root / entry.run_id
    cmd = [
        sys.executable,
        str(runner),
        "--config",
        config_path,
        "--task",
        task,
        "--shared-intermediate",
        str(shared),
        "--output-dir",
        str(out_dir),
        "--device",
        device,
    ]
    if entry.seg == entry.cls:
        cmd.extend(["--routing-mode", entry.seg])
    else:
        cmd.extend([
            "--routing-mode-seg", entry.seg,
            "--routing-mode-cls", entry.cls,
        ])
    if force_phase3:
        cmd.append("--force-phase3")
    if skip_eval:
        cmd.append("--skip-eval")
    return cmd


def _run_one(run_id: str, cmd: list[str], child_env: dict[str, str]) -> tuple[str, int]:
    print(f"[{run_id}] 启动", flush=True)
    rc = subprocess.call(cmd, cwd=str(ROOT), env=child_env)
    mark = "✓" if rc == 0 else "✗"
    print(f"[{run_id}] {mark} 结束 (exit {rc})", flush=True)
    return run_id, rc


def main():
    parser = argparse.ArgumentParser(description="批量运行 B3 routing ablation")
    parser.add_argument("--config", default="config/b3/sample.yaml")
    parser.add_argument("--shared-intermediate", default=None)
    parser.add_argument("--output-root", default=None)
    parser.add_argument(
        "--modes",
        default=None,
        help="逗号分隔；可用 static_rule:soft_voting 表示 seg/cls 不同",
    )
    parser.add_argument("--preset", choices=("wave1", "all_non_llm"), default=None)
    parser.add_argument("--task", choices=("seg", "cls", "both"), default=None)
    parser.add_argument("--force-phase3", action="store_true")
    parser.add_argument("--no-force-phase3", action="store_true")
    parser.add_argument("--device", default="cuda")
    parser.add_argument(
        "--jobs",
        type=int,
        default=None,
        help="并行子进程数（默认 1；可在 config pipeline.ablation.jobs 设置）",
    )
    parser.add_argument("--skip-eval", action="store_true")
    parser.add_argument("--summarize", action="store_true")
    parser.add_argument("--no-summarize", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--legacy-subprocess",
        action="store_true",
        help="每策略单独子进程（慢；默认用 static bundle 单次扫图）",
    )
    parser.add_argument(
        "--start-index",
        type=int,
        default=None,
        help="覆盖 config pipeline.data.start_index（chunk 跑法与 chunk_meta 对齐）",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=None,
        help="覆盖 config pipeline.data.max_images",
    )
    args = parser.parse_args()

    cfg = _load_config(args.config)
    if args.start_index is not None:
        cfg.setdefault("pipeline", {}).setdefault("data", {})["start_index"] = args.start_index
    if args.max_images is not None:
        cfg.setdefault("pipeline", {}).setdefault("data", {})["max_images"] = args.max_images
    batch = get_ablation_batch_settings(cfg)

    entries: list[AblationRoutingEntry]
    if args.modes:
        entries = [_parse_cli_mode_token(t) for t in args.modes.split(",") if t.strip()]
    elif batch["routing_entries"]:
        entries = batch["routing_entries"]
    elif args.preset in ("wave1", "all_non_llm"):
        entries = [parse_ablation_routing_entry(m) for m in WAVE1_MODES]
    else:
        entries = [parse_ablation_routing_entry(m) for m in WAVE1_MODES]

    shared = args.shared_intermediate or batch.get("shared_intermediate")
    if not shared:
        parser.error("需要 --shared-intermediate 或在 config 中设置 pipeline.ablation.shared_intermediate")

    out_root = args.output_root or batch.get("output_root")
    if not out_root:
        parser.error("需要 --output-root 或在 config 中设置 pipeline.ablation.output_root")

    task = args.task or batch.get("task") or "both"
    force_phase3 = batch.get("force_phase3", False)
    if args.force_phase3:
        force_phase3 = True
    if args.no_force_phase3:
        force_phase3 = False

    summarize = batch.get("summarize", False)
    if args.summarize:
        summarize = True
    if args.no_summarize:
        summarize = False

    jobs = args.jobs if args.jobs is not None else batch.get("jobs", 1)
    jobs = max(1, int(jobs))
    if jobs > 1 and len(entries) > 1:
        print(f"并行: jobs={jobs}（共 {len(entries)} 个 mode）")
        if str(args.device).startswith("cuda"):
            print("  ⚠️ 多进程共用同一 --device 时请注意 GPU 显存；必要时 --jobs 1 或 --device cpu")

    out_root = Path(out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    shared = Path(shared).resolve()
    child_env = _child_env()

    if not args.legacy_subprocess:
        if args.dry_run:
            print("bundle 模式（单次扫图），将输出:")
            for e in entries:
                print(f"  - {e.run_id} (seg={e.seg}, cls={e.cls})")
            return
        from pipeline.static_b3_bundle import (
            build_pipeline_for_bundle,
            collect_image_paths,
            load_labels,
            run_static_b3_bundle,
        )

        data_cfg = cfg.get("pipeline", {}).get("data", {})
        img_names, image_paths = collect_image_paths(
            data_cfg["image_input"],
            start_index=data_cfg.get("start_index", 0),
            max_images=data_cfg.get("max_images"),
        )
        labels = load_labels(data_cfg.get("label_file"), data_cfg.get("label_key", "malignancy"))
        pipeline = build_pipeline_for_bundle(cfg, args.device)
        run_static_b3_bundle(
            pipeline,
            cfg,
            entries=entries,
            image_dir=data_cfg["image_input"],
            output_root=out_root,
            shared_intermediate=shared,
            gt_mask_dir=data_cfg.get("gt_mask_dir"),
            labels=labels,
            img_names=img_names,
            image_paths=image_paths,
            task=task,
            force_phase3=force_phase3,
            skip_eval=args.skip_eval,
            input_device_info=data_cfg.get("device_info"),
        )
        if summarize and entries:
            ref = out_root / entries[0].run_id / "intermediate_manifest.json"
            sum_cmd = [
                sys.executable,
                "-m",
                "pipeline.ablation_summary",
                "--root",
                str(out_root),
            ]
            if ref.is_file():
                sum_cmd.extend(["--reference-manifest", str(ref)])
            print(f"\n汇总: {' '.join(sum_cmd)}")
            subprocess.check_call(sum_cmd, cwd=str(ROOT), env=child_env)
        return

    runner = ROOT / "scripts" / "run_routing_ablation.py"

    work: list[tuple[str, list[str]]] = []
    for entry in entries:
        cmd = _build_ablation_cmd(
            entry,
            runner=runner,
            config_path=args.config,
            task=task,
            shared=shared,
            out_root=out_root,
            device=args.device,
            force_phase3=force_phase3,
            skip_eval=args.skip_eval,
        )
        work.append((entry.run_id, cmd))
        if args.dry_run:
            print(f"\n>>> {entry.run_id} (seg={entry.seg}, cls={entry.cls})")
            print(" ".join(cmd))

    if args.dry_run:
        return

    failed: list[str] = []
    if jobs <= 1 or len(work) <= 1:
        for run_id, cmd in work:
            print(f"\n{'='*60}\n>>> {run_id}\n{'='*60}")
            _, rc = _run_one(run_id, cmd, child_env)
            if rc != 0:
                failed.append(run_id)
    else:
        with ThreadPoolExecutor(max_workers=min(jobs, len(work))) as pool:
            futures = {
                pool.submit(_run_one, run_id, cmd, child_env): run_id
                for run_id, cmd in work
            }
            for fut in as_completed(futures):
                run_id, rc = fut.result()
                if rc != 0:
                    failed.append(run_id)

    if failed:
        print(f"\n失败: {sorted(failed)}")
        sys.exit(1)

    if summarize and entries:
        ref = out_root / entries[0].run_id / "intermediate_manifest.json"
        sum_cmd = [
            sys.executable,
            "-m",
            "pipeline.ablation_summary",
            "--root",
            str(out_root),
        ]
        if ref.is_file():
            sum_cmd.extend(["--reference-manifest", str(ref)])
        print(f"\n汇总: {' '.join(sum_cmd)}")
        subprocess.check_call(sum_cmd, cwd=str(ROOT), env=child_env)


if __name__ == "__main__":
    main()
