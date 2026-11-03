"""Tests for centre-level meta heterogeneity from supplement tables."""

from pipeline.revision.b7.supplement_center_meta import (
    CenterEstimate,
    cochrane_q_i2_tau2,
    unweighted_macro,
)


def test_macro_two_centers():
    est = [
        CenterEstimate("A", 2, 0.833),
        CenterEstimate("B", 8, 0.960),
    ]
    assert abs(unweighted_macro(est) - 0.8965) < 0.001


def test_i2_two_centers_high():
    est = [
        CenterEstimate("A", 2, 0.833, se=0.05),
        CenterEstimate("B", 8, 0.960, se=0.02),
    ]
    out = cochrane_q_i2_tau2(est)
    assert out["n_groups"] == 2
    assert out["i2_percent"] is not None
    assert out["i2_percent"] > 50
