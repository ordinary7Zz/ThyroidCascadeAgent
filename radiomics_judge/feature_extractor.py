"""
GT-trained radiomics 特征提取器。

特征提取逻辑与 pyradiomics_train/extract_radiomics_2d.py 完全一致：
  - 用 PIL convert("L") 做灰度转换（ITU-R 601-2 luma 加权）
  - 图像转 float32（与训练侧 sitk.GetImageFromArray 一致）
  - 设置 spacing (1.0, 1.0)（correctMask 依赖）
  - 加载与训练相同的 radiomics_2d.yaml 配置（normalize + 多滤波器 + shape2D）

供 RadiomicsJudge 和 AutoGluonRadiomicsModel 共用，避免两处特征提取不一致。
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import numpy as np

# 抑制 pyradiomics 的大量 INFO 日志（Computing firstorder / glcm / ...）
logging.getLogger("radiomics").setLevel(logging.WARNING)


# 默认 YAML 配置路径：与本模块同目录的 radiomics_2d.yaml
_DEFAULT_PARAMS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "radiomics_2d.yaml")


class RadiomicsFeatureExtractor:
    """2D 超声 radiomics 特征提取（pyradiomics），配置与训练侧完全一致。"""

    def __init__(
        self,
        params_path: Optional[str] = None,
        spacing: tuple[float, float] = (1.0, 1.0),
        mask_threshold: int = 0,
    ):
        """
        Args:
            params_path: pyradiomics YAML 参数文件路径。
                         None 时使用本模块同目录的 radiomics_2d.yaml（与训练侧一致）。
            spacing: 像素间距 (x, y)，默认 (1.0, 1.0)，与训练侧一致。
            mask_threshold: mask 二值化阈值，mask > threshold 为前景，默认 0。
        """
        from radiomics import featureextractor

        if params_path is None:
            params_path = _DEFAULT_PARAMS_PATH

        if not os.path.isfile(params_path):
            raise FileNotFoundError(
                f"pyradiomics 参数文件不存在: {params_path}\n"
                f"请确保 radiomics_2d.yaml 已复制到 ThyroidCascadeAgent/radiomics_judge/ 目录"
            )

        self._extractor = featureextractor.RadiomicsFeatureExtractor(params_path)
        self._spacing = spacing
        self._mask_threshold = mask_threshold

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
        from PIL import Image as PILImage

        # ---- 灰度转换：用 PIL convert("L") 与训练侧 _read_gray 一致 ----
        if image.ndim == 3:
            # RGB → grayscale via PIL (ITU-R 601-2 luma: 0.299R + 0.587G + 0.114B)
            pil_img = PILImage.fromarray(image)
            gray = np.asarray(pil_img.convert("L"))
        else:
            gray = np.asarray(image)
            if gray.ndim != 2:
                gray = np.asarray(PILImage.fromarray(gray).convert("L"))

        # ---- mask 二值化：与训练侧 _read_mask 一致 (arr > threshold) ----
        mask_arr = np.asarray(mask)
        if mask_arr.ndim == 3:
            mask_arr = mask_arr[:, :, 0]
        mask_binary = (mask_arr > self._mask_threshold).astype(np.uint8)

        # ---- 检查前景像素 ----
        if int(mask_binary.sum()) == 0:
            return {}

        # ---- numpy → SimpleITK ----
        # 图像转 float32（与训练侧 sitk.GetImageFromArray(image.astype(np.float32)) 一致）
        img_sitk = sitk.GetImageFromArray(gray.astype(np.float32))
        msk_sitk = sitk.GetImageFromArray(mask_binary.astype(np.uint8))

        # 设置 spacing（correctMask: true 依赖）
        img_sitk.SetSpacing(self._spacing)
        msk_sitk.SetSpacing(self._spacing)

        try:
            result = self._extractor.execute(img_sitk, msk_sitk, label=1)
        except Exception as e:
            print(f"  ⚠️ pyradiomics 特征提取失败: {e}")
            return {}

        # 过滤诊断性字段，只留特征
        features: dict[str, float] = {}
        for key, val in result.items():
            if not str(key).startswith("diagnostics_"):
                try:
                    features[key] = float(val)
                except (TypeError, ValueError):
                    continue

        return features
