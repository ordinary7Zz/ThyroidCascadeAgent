"""
GT-trained radiomics 特征提取器。

从 autogluon_radiomics_model.py 的特征提取逻辑提取为独立模块，
供 RadiomicsJudge 使用。配置与 pyradiomics_train/extract_radiomics_2d.py 一致。
"""

from __future__ import annotations

import numpy as np


class RadiomicsFeatureExtractor:
    """2D 超声 radiomics 特征提取（pyradiomics）。"""

    def __init__(self, config: dict | None = None):
        """
        Args:
            config: pyradiomics 配置 dict（binWidth, normalization 等）。
                    None 时用默认配置。
        """
        from radiomics import featureextractor

        if config:
            import json as _json
            if isinstance(config, str):
                with open(config, "r") as f:
                    config = _json.load(f)
            self._extractor = featureextractor.RadiomicsFeatureExtractor(**config)
        else:
            self._extractor = featureextractor.RadiomicsFeatureExtractor()
            # 启用所有特征类
            for cls_name in ["firstorder", "glcm", "glrlm", "glszm", "gldm", "ngtdm"]:
                try:
                    self._extractor.enableFeatureClassByName(cls_name)
                except Exception:
                    pass

    def extract(self, image: np.ndarray, mask: np.ndarray) -> dict[str, float]:
        """
        提取 radiomics 特征。

        Args:
            image: (H, W, 3) RGB uint8 或 (H, W) gray uint8。
            mask: (H, W) uint8 [0,255] 或 0/1 二值。

        Returns:
            {feature_name: value}，空 mask 返回 {}。
        """
        import SimpleITK as sitk

        # RGB → grayscale
        if image.ndim == 3:
            gray = np.mean(image, axis=2).astype(np.uint8)
        else:
            gray = image.astype(np.uint8)

        # mask 二值化
        mask_binary = (mask > 0).astype(np.uint8)

        # 检查前景像素
        if mask_binary.sum() < 10:
            return {}

        sitk_image = sitk.GetImageFromArray(gray)
        sitk_mask = sitk.GetImageFromArray(mask_binary)

        try:
            result = self._extractor.execute(sitk_image, sitk_mask)
        except Exception as e:
            print(f"  ⚠️ pyradiomics 特征提取失败: {e}")
            return {}

        # 过滤诊断性字段
        features: dict[str, float] = {}
        for key, val in result.items():
            if not key.startswith("diagnostics_"):
                try:
                    features[key] = float(val)
                except (TypeError, ValueError):
                    continue

        return features
