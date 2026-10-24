"""parse_ablation_routing_entry 单测。"""

import unittest

from pipeline.revision.b3.routing_ablation import parse_ablation_routing_entry


class ParseRoutingEntryTest(unittest.TestCase):
    def test_string(self):
        e = parse_ablation_routing_entry("soft_voting")
        self.assertEqual(e.seg, "soft_voting")
        self.assertEqual(e.cls, "soft_voting")
        self.assertEqual(e.run_id, "soft_voting")

    def test_dict_split(self):
        e = parse_ablation_routing_entry({
            "seg": "static_rule",
            "cls": "majority",
            "name": "custom",
        })
        self.assertEqual(e.seg, "static_rule")
        self.assertEqual(e.cls, "majority")
        self.assertEqual(e.run_id, "custom")

    def test_auto_run_id(self):
        e = parse_ablation_routing_entry({"seg": "oracle", "cls": "soft_voting"})
        self.assertEqual(e.run_id, "oracle__soft_voting")


if __name__ == "__main__":
    unittest.main()
