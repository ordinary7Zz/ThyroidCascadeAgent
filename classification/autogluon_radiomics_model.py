"""
AutoGluon Radiomics 分类模型。

重写自 Classification_Agent/models/autogluon_radiomics_model.py。
requires_mask = True：输入 image + mask，用 pyradiomics 提特征 → AutoGluon 推理。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import numpy as np

from .base_model import BaseClassificationModel, ClsModelOutput
from .model_factory import register_cls_model


BINARY_CLASS_NAMES = ["良性", "恶性"]


@register_cls_model("autogluon_radiomics")
class AutoGluonRadiomicsModel(BaseClassificationModel):
    """pyradiomics 特征 + AutoGluon TabularPredictor 分类。"""

    def __init__(
        self,
        model_name: str,
        model_dir: str,
        base_dataset_performance: Optional[dict] = None,
        dataset_info: Optional[dict] = None,
        device: str = "cpu",
        **kwargs,
    ):
        super().__init__(
            model_name=model_name,
            model_path=model_dir,
            use_tirads=False,
            base_dataset_performance=base_dataset_performance,
            dataset_info=dataset_info,
            device=device,
            **kwargs,
        )
        self.model_dir = model_dir
        self._predictor = None
        self._feature_names: Optional[list[str]] = None

    @property
    def requires_mask(self) -> bool:
        return True

    def load_model(self) -> None:
        """延迟加载 AutoGluon TabularPredictor。"""
        print(f"  加载 AutoGluon 模型 {self.model_name} 从 {self.model_dir}")

        path = Path(self.model_dir)
        if not path.exists():
            raise FileNotFoundError(f"模型目录不存在: {path}")

        from autogluon.tabular import TabularPredictor

        self._predictor = TabularPredictor.load(str(path))
        self.is_loaded = True

        # 获取特征名（从训练数据推断）
        try:
            self._feature_names = list(self._predictor.feature_metadata_in.get_features())
        except Exception:
            self._feature_names = None

        print(f"    ✓ AutoGluon 加载成功")

    def validate_inputs(self, image: np.ndarray, mask: Optional[np.ndarray] = None) -> None:
        if image is None:
            raise ValueError("image 不能为 None")
        if mask is None:
            raise ValueError(f"{self.model_name} 需要 mask 输入")

    def predict(self, image: np.ndarray, mask: Optional[np.ndarray] = None) -> ClsModelOutput:
        """radiomics 特征提取 → AutoGluon 推理。"""
        if not self.is_loaded:
            self.load_model()

        self.validate_inputs(image, mask)
        features = self._extract_radiomics_features(image, mask)

        if not features:
            # 空 mask 或提取失败
            return ClsModelOutput(
                model_name=self.model_name,
                predictions={"良性": 0.5, "恶性": 0.5},
                top_class="良性",
                top_confidence=0.5,
                requires_mask=True,
                metadata={**self.get_info(), "feature_extraction_failed": True},
            )

        import pandas as pd

        df = pd.DataFrame([features])
        # 对齐特征列
        if self._feature_names:
            for col in self._feature_names:
                if col not in df.columns:
                    df[col] = 0.0
            df = df.reindex(columns=self._feature_names, fill_value=0.0)

        pred_proba = self._predictor.predict_proba(df)

        # 获取类别名
        classes = list(pred_proba.columns)
        if len(classes) == 2:
            # 假设 1=恶性, 0=良性
            if 1 in pred_proba.columns or "1" in [str(c) for c in pred_proba.columns]:
                p_mal = float(pred_proba.iloc[0].get(1, pred_proba.iloc[0].iloc[1]))
            else:
                p_mal = float(pred_proba.iloc[0].iloc[1])
            predictions = {"良性": 1.0 - p_mal, "恶性": p_mal}
        else:
            predictions = {str(c): float(p) for c, p in zip(classes, pred_proba.iloc[0])}

        top_class = max(predictions, key=predictions.get)

        return ClsModelOutput(
            model_name=self.model_name,
            predictions=predictions,
            top_class=top_class,
            top_confidence=predictions[top_class],
            requires_mask=True,
            metadata=self.get_info(),
        )

    def _extract_radiomics_features(self, image: np.ndarray, mask: np.ndarray) -> dict[str, float]:
        """
        用 pyradiomics 提取 2D radiomics 特征。

        Args:
            image: (H, W, 3) RGB uint8
            mask: (H, W) uint8 [0,255]
        """
        import SimpleITK as sitk
        from radiomics import featureextractor

        # RGB → grayscale
        if image.ndim == 3:
            gray = np.mean(image, axis=2).astype(np.uint8)
        else:
            gray = image.astype(np.uint8)

        # mask 二值化
        mask_binary = (mask > 0).astype(np.uint8)

        # 检查 mask 是否有前景
        if mask_binary.sum() < 10:
            return {}

        # numpy → SimpleITK
        sitk_image = sitk.GetImageFromArray(gray)
        sitk_mask = sitk.GetImageFromArray(mask_binary)

        # 配置 extractor
        extractor = featureextractor.RadiomicsFeatureExtractor()
        extractor.enableFeatureClassByName("firstorder")
        extractor.enableFeatureClassByName("glcm")
        extractor.enableFeatureClassByName("glrlm")
        extractor.enableFeatureClassByName("glszm")
        extractor.enableFeatureClassByName("gldm")
        extractor.enableFeatureClassByName("ngtdm")

        try:
            result = extractor.execute(sitk_image, sitk_mask)
        except Exception as e:
            print(f"  ⚠️ pyradiomics 特征提取失败: {e}")
            return {}

        # 过滤诊断性字段，只留特征
        features: dict[str, float] = {}
        for key, val in result.items():
            if not key.startswith("diagnostics_"):
                try:
                    features[key] = float(val)
                except (TypeError, ValueError):
                    continue

        return features
