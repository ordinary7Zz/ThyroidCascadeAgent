"""从补充表 S7–S12 同构的「每中心点估计 + n (+ CI)」汇总 macro 与 meta 异质性。"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass
class CenterEstimate:
    center_id: str
    n: int
    point: float
    se: Optional[float] = None


def parse_ci_field(s: str) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """'0.8520 [0.8100,0.8900]' 或 '0.8520' → (point, lo, hi)。"""
    if not s or not str(s).strip() or str(s).strip() in ("—", "-", "NE", "N/A"):
        return None, None, None
    text = str(s).strip()
    m = re.match(r"([\d.]+)\s*\[\s*([\d.]+)\s*,\s*([\d.]+)\s*\]", text)
    if m:
        return float(m.group(1)), float(m.group(2)), float(m.group(3))
    m2 = re.match(r"([\d.]+)", text)
    if m2:
        v = float(m2.group(1))
        return v, None, None
    return None, None, None


def se_from_ci(lo: float, hi: float, z: float = 1.96) -> float:
    return max((hi - lo) / (2.0 * z), 1e-6)


def crude_se_dice(p: float, n: int) -> float:
    """无 CI 时对 [0,1] 指标用 crude binomial SE（仅 meta 权重近似）。"""
    p = min(max(p, 1e-6), 1.0 - 1e-6)
    return max(math.sqrt(p * (1.0 - p) / max(n, 1)), 1e-6)


def unweighted_macro(estimates: Iterable[CenterEstimate]) -> Optional[float]:
    vals = [e.point for e in estimates if e.point is not None]
    if not vals:
        return None
    return sum(vals) / len(vals)


def pooled_weighted_mean(estimates: Iterable[CenterEstimate]) -> Optional[float]:
    num = 0.0
    den = 0.0
    for e in estimates:
        if e.point is None or e.n <= 0:
            continue
        num += e.point * e.n
        den += e.n
    if den <= 0:
        return None
    return num / den


def cochrane_q_i2_tau2(estimates: list[CenterEstimate]) -> dict[str, Optional[float]]:
    """
    逆方差加权 Cochrane Q / I² / τ²（中心级 meta，与稿面 S 表 + n 一致）。
    """
    rows = [e for e in estimates if e.point is not None and e.n > 0]
    k = len(rows)
    if k < 2:
        return {"i2_percent": None, "tau2": None, "q": None, "df": None, "n_groups": k}

    ys = []
    ws = []
    for e in rows:
        if e.se is not None and e.se > 0:
            v = e.se ** 2
        else:
            v = crude_se_dice(e.point, e.n) ** 2
        ys.append(e.point)
        ws.append(1.0 / v)

    w_sum = sum(ws)
    if w_sum <= 0:
        return {"i2_percent": None, "tau2": None, "q": None, "df": k - 1, "n_groups": k}

    y_bar = sum(w * y for w, y in zip(ws, ys)) / w_sum
    q = sum(w * (y - y_bar) ** 2 for w, y in zip(ws, ys))
    df = k - 1
    c = w_sum - sum(w * w for w in ws) / w_sum
    if c <= 0:
        return {"i2_percent": 0.0, "tau2": 0.0, "q": float(q), "df": df, "n_groups": k}

    tau2 = max(0.0, (q - df) / c)
    i2 = max(0.0, (q - df) / q) * 100.0 if q > 0 else 0.0
    return {
        "i2_percent": float(i2),
        "tau2": float(tau2),
        "q": float(q),
        "df": int(df),
        "n_groups": k,
    }


def fmt_pct(x: Optional[float], digits: int = 1) -> str:
    if x is None:
        return "---"
    return f"{100.0 * x:.{digits}f}"


def fmt_auroc(x: Optional[float]) -> str:
    if x is None:
        return "NE"
    return f"{x:.3f}"


def fmt_hd95(x: Optional[float], digits: int = 1) -> str:
    if x is None:
        return "---"
    return f"{x:.{digits}f}"
