"""波次 0–1：Path B 分类 method 互异 + 离线分割 mode 指纹互异。"""

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(rel: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class RoutingMethodsDistinctTest(unittest.TestCase):
    def test_path_b_cls_methods_unique(self):
        from classification.base_model import ClsModelOutput
        from routing.path_b_cls import resolve_path_b_indie_only as resolve

        def pred(name, cls, conf):
            return ClsModelOutput(
                model_name=name,
                predictions={
                    "良性": conf if cls == "良性" else 1 - conf,
                    "恶性": conf if cls == "恶性" else 1 - conf,
                },
                top_class=cls,
                top_confidence=conf,
                requires_mask=False,
                metadata={"entropy": 0.1 if name == "a" else 0.9},
            )

        preds = [pred("a", "良性", 0.9), pred("b", "恶性", 0.85), pred("c", "恶性", 0.4)]
        modes = ["soft_voting", "majority", "max_confidence", "static_rule"]
        methods = {resolve(m, preds).method for m in modes}
        self.assertEqual(len(methods), len(modes))

    def test_offline_seg_mode_methods_unique(self):
        seg_offline = _load("pipeline/seg_routing_offline.py", "seg_offline")
        inter = ROOT / "output/sample/pipeline_run/intermediate"
        if not (inter / "seg").is_dir():
            self.skipTest("无 sample intermediate")
        gt = ROOT / "config/revision/b3/sample.yaml"
        if not gt.is_file():
            self.skipTest("无 ablation 配置")
        import yaml
        with open(gt, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        gt_dir = cfg["pipeline"]["data"]["gt_mask_dir"]
        modes = ["soft_voting", "majority", "max_confidence"]
        method_sets = []
        for m in modes:
            row = seg_offline.evaluate_seg_routing_mode_offline(inter, gt_dir, m)
            method_sets.append(tuple(row["methods"]))
        self.assertEqual(len(set(method_sets)), len(modes))


if __name__ == "__main__":
    unittest.main()
