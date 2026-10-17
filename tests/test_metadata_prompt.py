"""B5 metadata_mode 字段过滤单测。"""

import unittest

from shared.metadata_prompt import (
    METADATA_MODES,
    cls_device_line,
    filter_cls_routing_envelope,
    filter_seg_routing_payload,
    normalize_metadata_mode,
    seg_user_prefix_lines,
)


def _sample_seg_payload() -> dict:
    return {
        "num_models": 2,
        "input_device_info": ["GE E9"],
        "input_data_info": {"dataset_name": "TN3K"},
        "models": [
            {
                "model_name": "m1",
                "training_devices": ["Siemens"],
                "dataset_size": 1000,
                "mask_statistics": {"area": 10},
                "radiomics_judge": {"malignant_prob": 0.1, "confidence": 0.9, "top_features": ["a"]},
            }
        ],
        "classification_anchor": {"class": "良性", "source": "x"},
    }


class TestMetadataPrompt(unittest.TestCase):
    def test_normalize_metadata_mode_invalid(self):
        with self.assertRaises(ValueError):
            normalize_metadata_mode("invalid")

    def test_all_modes_registered(self):
        self.assertEqual(len(METADATA_MODES), 5)

    def test_drop_device_seg(self):
        self._test_drop_device_seg()

    def _test_drop_device_seg(self):
        data = filter_seg_routing_payload(_sample_seg_payload(), "drop_device")
        self.assertNotIn("input_device_info", data)
        self.assertEqual(data["input_data_info"]["dataset_name"], "TN3K")
        self.assertNotIn("training_devices", data["models"][0])
        self.assertEqual(data["models"][0]["dataset_size"], 1000)

    def test_drop_both_seg(self):
        data = filter_seg_routing_payload(_sample_seg_payload(), "drop_both")
        self.assertNotIn("input_device_info", data)
        self.assertNotIn("input_data_info", data)
        self.assertNotIn("dataset_size", data["models"][0])

    def test_quality_only_seg(self):
        data = filter_seg_routing_payload(_sample_seg_payload(), "quality_only")
        m = data["models"][0]
        self.assertEqual(m["model_name"], "m1")
        self.assertNotIn("training_devices", m)
        self.assertNotIn("top_features", m.get("radiomics_judge", {}))

    def test_cls_envelope_drop_source(self):
        env = {
            "num_models": 2,
            "vote_entropy": 0.5,
            "predictions": [
                {
                    "model_name": "m1",
                    "metadata": {"training_devices": ["a"], "dataset_size": 9, "entropy": 0.1},
                }
            ],
        }
        out = filter_cls_routing_envelope(env, "drop_source")
        meta = out["predictions"][0]["metadata"]
        self.assertNotIn("dataset_size", meta)
        self.assertEqual(meta["training_devices"], ["a"])

    def test_cls_device_line(self):
        self.assertIn("GE", cls_device_line("full", ["GE E9"]))
        self.assertEqual(cls_device_line("drop_device", ["GE E9"]), "")

    def test_seg_user_prefix_lines(self):
        d, t = seg_user_prefix_lines("full", ["GE"], {"k": 1})
        self.assertIn("GE", d)
        self.assertIn("k", t)
        d2, t2 = seg_user_prefix_lines("drop_both", ["GE"], {"k": 1})
        self.assertEqual(d2, "")
        self.assertEqual(t2, "")


if __name__ == "__main__":
    unittest.main()
