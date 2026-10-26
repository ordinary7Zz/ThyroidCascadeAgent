#!/usr/bin/env python3
"""从 config 指定路径汇总 B4 组件主表（sample 可占位，正式队列替换 b3_root / l1_metrics）。"""

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

from pipeline.revision.b4.b4_summary import summarize_b4


def main() -> None:
    parser = argparse.ArgumentParser(description="B4 L1–L3 + S4 校验行汇总")
    parser.add_argument("--config", default="config/revision/b4/sample.yaml")
    parser.add_argument("--output-dir", default=None, help="默认 config pipeline.output.output_dir")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    out = args.output_dir or cfg.get("pipeline", {}).get("output", {}).get("output_dir")
    if not out:
        parser.error("需要 --output-dir 或 config pipeline.output.output_dir")

    result = summarize_b4(cfg, Path(out))
    print(json.dumps({k: v for k, v in result.items() if k != "report_doc"}, ensure_ascii=False, indent=2))
    report = result["report_doc"]
    for w in report.get("warnings", []):
        print(f"⚠️ {w}", file=__import__("sys").stderr)
    for w in (report.get("pathb") or {}).get("warnings", []):
        print(f"⚠️ pathb: {w}", file=__import__("sys").stderr)


if __name__ == "__main__":
    main()

import importlib.util
from pathlib import Path


