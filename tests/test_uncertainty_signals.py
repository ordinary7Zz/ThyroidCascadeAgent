import numpy as np

from classification.base_model import ClsModelOutput
from shared.uncertainty_signals import (
    cls_disagreement_features,
    seg_disagreement_from_masks,
)


def test_cls_vote_entropy_split():
    preds = [
        ClsModelOutput("a", {"良性": 0.9, "恶性": 0.1}, "良性", 0.9, False, {}),
        ClsModelOutput("b", {"良性": 0.1, "恶性": 0.9}, "恶性", 0.9, False, {}),
    ]
    f = cls_disagreement_features(preds)
    assert f["num_indie_cls_models"] == 2
    assert f["vote_entropy"] > 0.5
    assert not f["classification_unanimous"]


def test_seg_min_pairwise_iou():
    m1 = np.zeros((10, 10), dtype=np.uint8)
    m2 = np.zeros((10, 10), dtype=np.uint8)
    m1[2:6, 2:6] = 1
    m2[2:6, 3:7] = 1
    s = seg_disagreement_from_masks([m1, m2])
    assert 0.0 < s["seg_min_pairwise_iou"] < 1.0
