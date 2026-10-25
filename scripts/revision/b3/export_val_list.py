#!/usr/bin/env python3
"""从图像目录或 label JSON 导出 B3 val_list（文件名列表，供 pipeline.ablation.val_list 引用）。"""

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

import repo_path

repo_path.install()

_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def _stems_from_image_dir(image_dir: Path) -> list[str]:
    names = sorted(
        p.name for p in image_dir.iterdir() if p.suffix.lower() in _IMAGE_SUFFIXES
    )
    return names


def _stems_from_label_json(label_path: Path) -> list[str]:
    with open(label_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        if "images" in data and isinstance(data["images"], list):
            return sorted(str(x) for x in data["images"])
        return sorted(str(k) for k in data.keys())
    if isinstance(data, list):
        out: list[str] = []
        for item in data:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict):
                for key in ("image", "file_name", "filename", "path"):
                    if key in item:
                        out.append(str(item[key]))
                        break
        return sorted(out)
    raise ValueError(f"无法从 label JSON 解析图像列表: {label_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="导出 B3 val_list JSON")
    parser.add_argument(
        "--image-dir",
        type=Path,
        help="valid/images 等目录（按文件名排序写出完整文件名）",
    )
    parser.add_argument(
        "--label-json",
        type=Path,
        help="标签 JSON（键或 images 字段为 stem/文件名）",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="输出路径，如 config/revision/b3/val_lists/tn3k.json",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=None,
        help="最多写入前 N 条（调试用）",
    )
    args = parser.parse_args()
    if not args.image_dir and not args.label_json:
        parser.error("须指定 --image-dir 或 --label-json")
    if args.image_dir:
        names = _stems_from_image_dir(args.image_dir)
    else:
        names = _stems_from_label_json(args.label_json)
    if args.max is not None:
        names = names[: args.max]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(names, f, ensure_ascii=False, indent=2)
    print(json.dumps({"out": str(args.out), "n": len(names)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
