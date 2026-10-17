"""build_test_for_llm 分层配额单测。"""

import importlib.util
import unittest
from collections import Counter
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "build_test_for_llm",
    Path(__file__).resolve().parents[1] / "scripts" / "build_test_for_llm.py",
)
_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mod)
_allocate_stratified = _mod._allocate_stratified


class TestAllocateStratified(unittest.TestCase):
    def test_sums_to_n(self):
        counts = Counter({0: 378, 1: 236})
        alloc = _allocate_stratified(counts, 100)
        self.assertEqual(sum(alloc.values()), 100)

    def test_multiclass(self):
        counts = Counter({"A": 10, "B": 20, "C": 30})
        alloc = _allocate_stratified(counts, 60)
        self.assertEqual(sum(alloc.values()), 60)
        self.assertEqual(alloc["A"], 10)
        self.assertEqual(alloc["B"], 20)
        self.assertEqual(alloc["C"], 30)


if __name__ == "__main__":
    unittest.main()
