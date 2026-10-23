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

检查当前机器/容器是否适合跑 ZJH-8K 等大队列 B3 bundle。

在共享 workspace 的任意节点上运行（各节点 GPU/内存限额可能不同）：

  python scripts/revision/b3/zjh/check_b3_host_capacity.py
  python scripts/revision/b3/zjh/check_b3_host_capacity.py --zjh-intermediate output/ZJH-8K/pipeline_run/intermediate

输出：cgroup 内存上限、可用内存、CPU、GPU、intermediate 体量、针对 B3 的简要建议。
"""

from __future__ import annotations

import importlib.util
from pathlib import Path



import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    import repo_path
    return repo_path.find_repo_root()


def _read_int(path: Path) -> int | None:
    try:
        text = path.read_text().strip()
    except OSError:
        return None
    if text == "max":
        return None
    if text.isdigit():
        return int(text)
    return None


def _gib(n: int | None) -> str:
    if n is None:
        return "—"
    return f"{n / (1024**3):.2f} GiB"


def find_cgroup_memory_limits() -> list[tuple[str, str]]:
    """返回 (文件路径, 人类可读说明)。"""
    found: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add(path: Path, label: str) -> None:
        key = str(path)
        if key in seen:
            return
        seen.add(key)
        found.append((key, label))

    cgroup_txt = Path("/proc/self/cgroup")
    if cgroup_txt.is_file():
        for line in cgroup_txt.read_text().splitlines():
            parts = line.split(":")
            if len(parts) < 3:
                continue
            rel = parts[-1].strip()
            if not rel.startswith("/"):
                rel = "/" + rel
            rel = rel.lstrip("/")
            for base in (Path("/sys/fs/cgroup"), Path("/sys/fs/cgroup/memory")):
                for name in ("memory.max", "memory.limit_in_bytes"):
                    f = base / rel / name if rel else base / name
                    if not f.is_file():
                        continue
                    raw = f.read_text().strip()
                    if name == "memory.max":
                        if raw == "max":
                            add(f, "无 cgroup 硬上限 (memory.max=max)")
                        elif raw.isdigit():
                            add(f, f"cgroup 上限 {_gib(int(raw))}")
                    elif raw.isdigit():
                        v = int(raw)
                        if v > (1 << 62):
                            add(f, "无有效 cgroup 上限 (极大值)")
                        else:
                            add(f, f"cgroup 上限 {_gib(v)}")

    for f in (
        Path("/sys/fs/cgroup/memory.max"),
        Path("/sys/fs/cgroup/memory/memory.limit_in_bytes"),
    ):
        if not f.is_file():
            continue
        raw = f.read_text().strip()
        if f.name == "memory.max":
            if raw == "max":
                add(f, "无 cgroup 硬上限 (memory.max=max)")
            elif raw.isdigit():
                add(f, f"cgroup 上限 {_gib(int(raw))}")
        elif raw.isdigit():
            v = int(raw)
            if v > (1 << 62):
                add(f, "无有效 cgroup 上限 (极大值)")
            else:
                add(f, f"cgroup 上限 {_gib(v)}")

    return found


def meminfo_available_gib() -> float | None:
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                kb = int(line.split()[1])
                return kb / (1024**2)
    except OSError:
        pass
    return None


def dir_size_gib(path: Path) -> float | None:
    if not path.exists():
        return None
    try:
        out = subprocess.run(
            ["du", "-sb", str(path)],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if out.returncode == 0:
            return int(out.stdout.split()[0]) / (1024**3)
    except (OSError, subprocess.TimeoutExpired, ValueError):
        pass
    total = 0
    try:
        for root, _dirs, files in os.walk(path):
            for name in files:
                try:
                    total += (Path(root) / name).stat().st_size
                except OSError:
                    pass
    except OSError:
        return None
    return total / (1024**3)


def gpu_summary() -> list[str]:
    lines: list[str] = []
    nvidia = shutil.which("nvidia-smi")
    if not nvidia:
        lines.append("nvidia-smi: 未找到（仅 CPU 跑 B3 bundle 也可）")
        return lines
    try:
        out = subprocess.run(
            [
                nvidia,
                "--query-gpu=index,name,memory.total,memory.free",
                "--format=csv,noheader",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if out.returncode == 0 and out.stdout.strip():
            for row in out.stdout.strip().splitlines():
                lines.append(f"GPU {row.strip()}")
        else:
            lines.append(f"nvidia-smi 失败: {out.stderr.strip() or out.returncode}")
    except (OSError, subprocess.TimeoutExpired) as e:
        lines.append(f"nvidia-smi 异常: {e}")
    return lines


def parse_cgroup_cap_gib(limits: list[tuple[str, str]]) -> float | None:
    for _path, label in limits:
        if "cgroup 上限" in label:
            # label like "cgroup 上限 37.25 GiB"
            part = label.split("上限", 1)[-1].strip().split()[0]
            try:
                return float(part)
            except ValueError:
                continue
    return None


def recommend_b3_zjh(cgroup_gib: float | None, avail_gib: float | None, inter_gib: float | None) -> list[str]:
    tips: list[str] = []
    # 整包预加载 ZJH seg+cls 粗算需 ~45–80GiB 峰值（含 max_confidence conf）
    preload_need = 72.0
    lazy_ok_ram = 12.0

    if cgroup_gib is not None:
        if cgroup_gib >= 96:
            tips.append(
                "✓ cgroup ≥96GiB：可在 zjh8k.yaml 使用 bundle_lazy_seg_min_images: 99999 "
                "整包预加载，速度接近 TN3K；运行 ./scripts/revision/b3/zjh/run_b3_zjh8k.sh"
            )
        elif cgroup_gib >= 64:
            tips.append(
                "△ cgroup 64–96GiB：整包预加载可能仍 OOM(137)；优先试 preload，失败则去掉 "
                "bundle_lazy_seg_min_images: 99999，用 lazy + 两趟 fast5/static_rule"
            )
        else:
            tips.append(
                "△ cgroup ≤约 40GiB：不要 bundle_lazy_seg_min_images: 99999；用 lazy mmap，"
                "./scripts/revision/b3/zjh/run_b3_zjh8k.sh 两趟；可把 intermediate 拷到本机盘加速"
            )
    else:
        tips.append(
            "未读到 cgroup 上限：以 MemAvailable 与实测为准；若预加载时 exit 137 则改用 lazy"
        )

    if avail_gib is not None:
        if avail_gib >= preload_need:
            tips.append(f"✓ MemAvailable {_gib(int(avail_gib * 1024**3))}：主机层面余量够尝试整包预加载")
        elif avail_gib >= lazy_ok_ram:
            tips.append(
                f"MemAvailable {_gib(int(avail_gib * 1024**3))}：更适合 lazy 或分片 npz，避免整包预加载"
            )
        else:
            tips.append(f"⚠ MemAvailable 偏低 ({avail_gib:.1f} GiB)，大任务易失败")

    if inter_gib is not None:
        tips.append(f"ZJH intermediate 约 {_gib(int(inter_gib * 1024**3))}（du）；lazy 读 NFS 会慢，可拷到本地或 /dev/shm")

    tips.append(
        "Python 建议: PYTHON=/mnt/wangbd8/workspace/envs/thyroid_infer/bin/python "
        "（勿用 NFS 上起不来的 sklearn161）"
    )
    return tips


def main() -> int:
    parser = argparse.ArgumentParser(description="B3 大队列节点能力检查")
    parser.add_argument(
        "--zjh-intermediate",
        default="output/ZJH-8K/pipeline_run/intermediate",
        help="ZJH shared intermediate 相对仓库根目录",
    )
    parser.add_argument(
        "--python",
        default=os.environ.get(
            "PYTHON",
            "/mnt/wangbd8/workspace/envs/thyroid_infer/bin/python",
        ),
        help="待检测的 Python 路径",
    )
    args = parser.parse_args()

    root = _repo_root()
    os.chdir(root)

    print("=" * 60)
    print("B3 节点检查", platform.node())
    print("仓库:", root)
    print("=" * 60)

    print("\n## cgroup 内存限额")
    limits = find_cgroup_memory_limits()
    if limits:
        for path, label in limits:
            print(f"  {label}")
            print(f"    ({path})")
    else:
        print("  未找到 memory.max / memory.limit_in_bytes")
        print("  请查看: cat /proc/self/cgroup")

    cgroup_gib = parse_cgroup_cap_gib(limits)
    avail = meminfo_available_gib()
    print("\n## 内存 (MemAvailable，非 cgroup 上限)")
    print(f"  {avail:.2f} GiB" if avail is not None else "  无法读取")

    print("\n## CPU")
    print(f"  逻辑核: {os.cpu_count()}")

    print("\n## GPU")
    for line in gpu_summary():
        print(f"  {line}")

    inter = root / args.zjh_intermediate
    print("\n## ZJH intermediate")
    print(f"  路径: {inter}")
    if inter.is_dir():
        gib = dir_size_gib(inter)
        print(f"  体量: {_gib(int(gib * 1024**3)) if gib is not None else '计算中失败'}")
        seg = inter / "seg"
        if seg.is_dir():
            npz = list(seg.glob("*.npz"))
            print(f"  seg npz 数量: {len(npz)}")
    else:
        print("  目录不存在（未生成 Phase1–2 缓存）")

    py = Path(args.python)
    print("\n## Python 启动 (20s 超时)")
    print(f"  路径: {py}")
    if not py.is_file():
        print("  ✗ 文件不存在")
    else:
        try:
            r = subprocess.run(
                [str(py), "-c", "print('ok')"],
                capture_output=True,
                text=True,
                timeout=20,
            )
            if r.returncode == 0 and "ok" in r.stdout:
                print("  ✓ 20s 内可启动")
            else:
                print(f"  ✗ 异常 exit={r.returncode} stderr={r.stderr[:200]}")
        except subprocess.TimeoutExpired:
            print("  ✗ 20s 内无响应（常见于 NFS 上 env 卡死）")

    print("\n## 针对 ZJH-8K B3 的建议")
    inter_gib = dir_size_gib(inter) if inter.is_dir() else None
    for tip in recommend_b3_zjh(cgroup_gib, avail, inter_gib):
        print(f"  {tip}")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
