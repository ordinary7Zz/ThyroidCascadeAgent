#!/usr/bin/env python3
"""Build ZJH exclude list: images matching stacked train (dHash H=0 by default)."""

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


def load_exclude_names(pairs_path: Path, hamming_max: int) -> list[str]:
    pairs = json.loads(pairs_path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for pair in pairs:
        if int(pair["hamming"]) <= hamming_max:
            names.add(pair["right"])
    return sorted(names)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pairs",
        type=Path,
        default=Path("docs/revision/b1/tables/near_dup_pairs/stacked_train_vs_ZJH-8K.pairs.json"),
    )
    parser.add_argument("--hamming-max", type=int, default=0)
    parser.add_argument(
        "--out-txt",
        type=Path,
        default=Path("docs/revision/b1/tables/zjh_excl_train_dhash0.txt"),
    )
    parser.add_argument(
        "--out-manifest",
        type=Path,
        default=Path("docs/revision/b1/tables/zjh_excl_train_dhash0_manifest.json"),
    )
    args = parser.parse_args()

    if not args.pairs.exists():
        raise SystemExit(
            f"Missing {args.pairs}. Run:\n"
            "  python scripts/revision/b1/audit_near_duplicates.py --preset stacked_vs_zjh "
            "--hamming-max 5 --export-pairs-dir docs/revision/b1/tables/near_dup_pairs"
        )

    names = load_exclude_names(args.pairs, args.hamming_max)
    args.out_txt.parent.mkdir(parents=True, exist_ok=True)
    header = (
        f"# ZJH-8K exclude: dHash to stacked train (hamming<={args.hamming_max})\n"
        f"# pairs: {args.pairs}\n"
    )
    args.out_txt.write_text(header + "\n".join(names) + ("\n" if names else ""), encoding="utf-8")

    manifest = {
        "pairs_file": str(args.pairs.resolve()),
        "hamming_max": args.hamming_max,
        "n_images": len(names),
        "images": names,
    }
    args.out_manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(names)} exclude names -> {args.out_txt}")


if __name__ == "__main__":
    main()

import importlib.util
from pathlib import Path


