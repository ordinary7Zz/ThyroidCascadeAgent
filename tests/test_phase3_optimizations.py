"""Phase 3 加速与断点续跑配置辅助函数。"""

from shared.phase3_options import (
    phase3_checkpoint_every,
    phase3_expert_judge_enabled,
    validate_phase3_checkpoint,
)


def test_phase3_expert_judge_default_true():
    assert phase3_expert_judge_enabled({}) is True
    assert phase3_expert_judge_enabled({"pipeline": {}}) is True


def test_phase3_expert_judge_pipeline_flag():
    cfg = {"pipeline": {"phase3_expert_judge": False}}
    assert phase3_expert_judge_enabled(cfg) is False


def test_phase3_checkpoint_every():
    assert phase3_checkpoint_every({}) == 0
    assert phase3_checkpoint_every({"pipeline": {"phase3_checkpoint_every": 50}}) == 50


def test_validate_phase3_checkpoint():
    names = ["a.jpg", "b.jpg", "c.jpg"]
    assert validate_phase3_checkpoint(names, []) is True
    assert validate_phase3_checkpoint(names, ["a.jpg", "b.jpg"]) is True
    assert validate_phase3_checkpoint(names, ["a.jpg", "x.jpg"]) is False
    assert validate_phase3_checkpoint(names, names + ["d.jpg"]) is False
