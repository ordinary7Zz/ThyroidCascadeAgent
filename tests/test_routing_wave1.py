"""B3 波次 1：轻量单测（routing_modes）。"""

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def _load_mod(rel: str, name: str):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class RoutingWave1Test(unittest.TestCase):
    def test_path_b_no_autogluon_contract(self):
        routing_modes = _load_mod("shared/routing_modes.py", "routing_modes")
        self.assertTrue(routing_modes.path_b_includes_autogluon("llm"))
        self.assertFalse(routing_modes.path_b_includes_autogluon("soft_voting"))
        self.assertFalse(routing_modes.path_b_includes_autogluon("learned"))

    def test_normalize_average_alias(self):
        routing_modes = _load_mod("shared/routing_modes.py", "routing_modes")
        self.assertEqual(routing_modes.normalize_routing_mode("average"), "soft_voting")


if __name__ == "__main__":
    unittest.main()
