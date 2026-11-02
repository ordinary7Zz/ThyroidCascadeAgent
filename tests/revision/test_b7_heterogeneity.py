"""B7 异质性与中心内汇总单元测试。"""

from pipeline.revision.b7.meta_regression import heterogeneity_i2_tau2
from pipeline.revision.b7.within_center import within_center_summary


def test_heterogeneity_i2_two_centers():
    values = {
        "A": [0.9, 0.92, 0.88],
        "B": [0.5, 0.55, 0.52],
    }
    out = heterogeneity_i2_tau2(values)
    assert out["n_groups"] == 2
    assert out["i2_percent"] is not None
    assert out["i2_percent"] > 0


def test_within_center_cv():
    values = {"C1": [0.8, 0.82, 0.78, 0.81]}
    w = within_center_summary(values)
    assert w["C1"]["n"] == 4
    assert w["C1"]["std"] > 0
    assert w["C1"]["cv_percent"] is not None


def test_center_auroc_ne_single_class():
    from pipeline.revision.b7.nhc_heterogeneity import aggregate_by_center

    cls = [
        {"stem": "a1", "center_id": "C1", "true_label": 1, "score_malignant": 0.9},
        {"stem": "a2", "center_id": "C1", "true_label": 1, "score_malignant": 0.8},
    ]
    out = aggregate_by_center(per_image_seg=[], per_image_cls=cls)
    assert out["centers"]["C1"]["auroc_estimable"] is False
    assert out["centers"]["C1"]["auroc"] is None


def test_center_auroc_estimable_with_two_classes():
    from pipeline.revision.b7.nhc_heterogeneity import aggregate_by_center

    cls = []
    for i in range(6):
        cls.append(
            {
                "stem": f"s{i}",
                "center_id": "C1",
                "true_label": i % 2,
                "score_malignant": 0.2 + 0.1 * i,
            }
        )
    out = aggregate_by_center(per_image_seg=[], per_image_cls=cls)
    assert out["centers"]["C1"]["auroc_estimable"] is True
    assert out["centers"]["C1"]["auroc"] is not None
