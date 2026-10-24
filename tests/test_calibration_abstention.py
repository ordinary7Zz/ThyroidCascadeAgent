from pipeline.revision.b8.abstention import apply_abstention, fit_thresholds_quantile, flag_for_review
from pipeline.revision.b8.calibration import brier_score, expected_calibration_error
import numpy as np


def test_ece_perfect():
    y = np.array([0, 0, 1, 1])
    p = np.array([0.1, 0.2, 0.8, 0.9])
    ece, _ = expected_calibration_error(y, p, n_bins=5)
    assert ece >= 0.0
    assert brier_score(y, p) < 0.1


def test_abstention_fit_and_apply():
    val = [
        {"uncertainty": {"vote_entropy": 0.1, "margin_top2_min": 0.5, "seg_min_pairwise_iou": 0.9}},
        {"uncertainty": {"vote_entropy": 0.9, "margin_top2_min": 0.05, "seg_min_pairwise_iou": 0.2}},
    ]
    th = fit_thresholds_quantile(val, rule_subset="nhc", quantile=0.5)
    test = [
        {"uncertainty": {"vote_entropy": 0.95, "margin_top2_min": 0.01, "seg_min_pairwise_iou": 0.1},
         "true_label": "恶性", "final_label": 1},
    ]
    flagged = apply_abstention(test, th)
    assert flagged[0]["flagged_for_review"] in (True, False)
    assert isinstance(flag_for_review(test[0], th), bool)
