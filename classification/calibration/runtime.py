"""
分类概率校准（运行时）。

由离线脚本生成 JSON 校准参数，推理时通过 maybe_apply_calibration_map 应用温度缩放。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np

from ..base_model import ClsModelOutput


def load_calibration_map(artifacts_dir: str) -> dict:
    """从目录加载所有模型的校准参数。"""
    cal_map: dict = {}
    path = Path(artifacts_dir)
    if not path.exists():
        return cal_map
    for f in path.glob("*.json"):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            model_name = data.get("model_name", f.stem)
            cal_map[model_name] = data
        except (json.JSONDecodeError, IOError):
            continue
    return cal_map


def maybe_apply_calibration_map(
    output: ClsModelOutput,
    calibration_map: Optional[dict],
) -> ClsModelOutput:
    """
    若 calibration_map 有该模型的校准参数，对 predictions 做温度缩放。

    温度缩放: p' = sigmoid(logit(p) / temperature)
    二分类: p_malignant → 温度缩放 → p_benign = 1 - p_malignant
    """
    if not calibration_map:
        return output

    cal = calibration_map.get(output.model_name)
    if not cal:
        return output

    temperature = cal.get("temperature", 1.0)
    if temperature <= 0 or abs(temperature - 1.0) < 1e-6:
        return output

    preds = dict(output.predictions)
    if len(preds) != 2:
        return output

    cls_names = list(preds.keys())
    p0 = float(preds[cls_names[0]])
    p1 = float(preds[cls_names[1]])

    # 判断哪个是 malignant（第二个通常是恶性）
    mal_idx = 1 if ("恶" in cls_names[1] or "mal" in cls_names[1].lower()) else 0
    p_mal = p1 if mal_idx == 1 else p0
    p_mal = max(1e-6, min(1 - 1e-6, p_mal))

    logit = np.log(p_mal / (1 - p_mal))
    p_mal_cal = 1.0 / (1.0 + np.exp(-logit / temperature))

    ben_idx = 1 - mal_idx
    preds[cls_names[mal_idx]] = float(p_mal_cal)
    preds[cls_names[ben_idx]] = float(1 - p_mal_cal)

    top_cls = max(preds, key=preds.get)
    return ClsModelOutput(
        model_name=output.model_name,
        predictions=preds,
        top_class=top_cls,
        top_confidence=preds[top_cls],
        requires_mask=output.requires_mask,
        metadata={
            **output.metadata,
            "classification_uncertainty": {
                **output.metadata.get("classification_uncertainty", {}),
                "top_confidence_calibrated": preds[top_cls],
                "top_confidence_raw": output.top_confidence,
            },
        },
    )
