"""B3 learned 路由：特征维度与随机占位推理。"""

import sys
import unittest
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from routing.learned_router import (  # noqa: E402
    LearnedRouterParams,
    build_cls_features,
    build_router_random,
    build_seg_features,
    seg_feature_names,
)


class LearnedRouterTest(unittest.TestCase):
    def test_random_router_picks_valid_expert(self):
        @dataclass
        class _Pred:
            model_name: str
            top_class: str
            top_confidence: float
            metadata: dict

            def to_dict(self):
                return {
                    "model_name": self.model_name,
                    "top_class": self.top_class,
                    "top_confidence": self.top_confidence,
                    "metadata": self.metadata,
                }

        names = ["m_a", "m_b"]
        params = LearnedRouterParams(random_init=True, random_state=0)
        router = build_router_random("cls", names, params)
        preds = [
            _Pred("m_a", "良性", 0.6, {"entropy": 0.5, "margin_top2": 0.1}),
            _Pred("m_b", "恶性", 0.8, {"entropy": 0.3, "margin_top2": 0.2}),
        ]
        idx = router.predict_expert_index(build_cls_features(preds, model_names=names))
        self.assertIn(names[idx], names)

    def test_seg_feature_length(self):
        @dataclass
        class _Seg:
            model_name: str
            mask: np.ndarray

        names = ["s1", "s2"]
        preds = [
            _Seg("s1", np.ones((4, 4), dtype=np.uint8)),
            _Seg("s2", np.zeros((4, 4), dtype=np.uint8)),
        ]
        quality = {
            "agreement_metrics": {"average_agreement": [0.9, 0.5]},
            "individual_quality": [
                {"circularity": 0.8, "num_components": 1},
                {"circularity": 0.4, "num_components": 2},
            ],
        }
        vec = build_seg_features(preds, quality, anchor_class=None, model_names=names)
        self.assertEqual(vec.shape[0], len(seg_feature_names(names)))


if __name__ == "__main__":
    unittest.main()
