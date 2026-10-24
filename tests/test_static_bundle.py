"""B3 static bundle 轻量测试。"""

import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]


def _load(rel: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class StaticBundleTest(unittest.TestCase):
    def test_phase3_expert_judge_skips_bundle_judge_batch(self):
        from pipeline.revision.b3.static_b3_bundle import _pick_seg_decision

        pipeline = MagicMock()
        pipeline._select_mask_static.return_value = (MagicMock(selected_mask=None), {})
        judge = MagicMock()
        judge.judge_batch = MagicMock()
        pipeline.seg_agent.radiomics_judge = judge

        _pick_seg_decision(
            pipeline,
            "static_rule",
            image=MagicMock(),
            seg_preds=[MagicMock(mask=MagicMock())],
            anchor_class="恶性",
            gt_mask=None,
            judge_results=None,
            best_single_seg=None,
            input_device_info=None,
            input_data_info=None,
            skip_radiomics=True,
        )
        pipeline._select_mask_static.assert_called_once()
        call_kw = pipeline._select_mask_static.call_args.kwargs
        self.assertTrue(call_kw.get("skip_radiomics"))

    def test_static_modes_only(self):
        bundle = _load("pipeline/static_b3_bundle.py", "static_b3_bundle")
        self.assertIn("soft_voting", bundle.STATIC_B3_MODES)
        with self.assertRaises(ValueError):
            bundle._assert_static_mode("llm", side="seg")

    def test_bundle_smoke_outputs(self):
        inter = ROOT / "output/sample/pipeline_run/intermediate"
        if not (inter / "seg").is_dir():
            self.skipTest("无 sample intermediate")
        import yaml

        with open(ROOT / "config/b3/sample.yaml", "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        from pipeline.revision.b3.routing_ablation import parse_ablation_routing_entry
        from pipeline.revision.b3.static_b3_bundle import (
            build_pipeline_for_bundle,
            collect_image_paths,
            load_labels,
            run_static_b3_bundle,
        )

        out = ROOT / "output/ablation/b3/test_bundle_smoke"
        data = cfg["pipeline"]["data"]
        img_names, image_paths = collect_image_paths(
            data["image_input"],
            start_index=data.get("start_index", 0),
            max_images=3,
        )
        labels = load_labels(data.get("label_file"), data.get("label_key", "malignancy"))
        pipeline = build_pipeline_for_bundle(cfg, "cpu")
        entries = [
            parse_ablation_routing_entry("soft_voting"),
            parse_ablation_routing_entry("majority"),
        ]
        run_static_b3_bundle(
            pipeline,
            cfg,
            entries=entries,
            image_dir=data["image_input"],
            output_root=out,
            shared_intermediate=inter,
            gt_mask_dir=data.get("gt_mask_dir"),
            labels=labels,
            img_names=img_names,
            image_paths=image_paths,
            task="both",
            force_phase3=True,
            skip_eval=False,
        )
        for mode in ("soft_voting", "majority"):
            mpath = out / mode / "b3_metrics.json"
            self.assertTrue(mpath.is_file(), mpath)
            with open(mpath, "r", encoding="utf-8") as f:
                doc = json.load(f)
            self.assertEqual(doc.get("routing_mode_seg"), mode)
            self.assertTrue((out / mode / "results.json").is_file())


if __name__ == "__main__":
    unittest.main()
