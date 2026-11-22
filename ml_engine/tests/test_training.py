import pandas as pd
import pytest

from ml_engine.train import train
from ml_engine.evaluate import evaluate


def sample_frame():
    return pd.DataFrame({
        "duration": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
        "protocol": ["tcp", "udp"] * 10,
        "Label": ["BENIGN"] * 10 + ["ATTACK"] * 10,
    })


def test_random_forest_training_and_evaluation():
    frame = sample_frame()
    model, report, features = train(frame, seed=7)
    holdout = pd.DataFrame({
        "duration": [21, 22, 23, 24, 25, 26, 27, 28, 29, 30],
        "protocol": ["tcp", "udp"] * 5,
        "Label": ["BENIGN"] * 5 + ["ATTACK"] * 5,
    })
    result = evaluate(holdout, "Label", model)
    assert "duration" in features
    assert "weighted avg" in report
    assert 0 <= result["accuracy"] <= 1
    assert result["samples"] == len(holdout)


def test_group_aware_split_excludes_group_identifier():
    frame = pd.DataFrame({
        "duration": list(range(1, 21)),
        "protocol": ["tcp", "udp"] * 10,
        "session_id": [f"session-{index // 2}" for index in range(20)],
        "Label": ["BENIGN", "ATTACK"] * 10,
    })
    _, report, features = train(frame, group_column="session_id", seed=13)
    assert "weighted avg" in report
    assert "session_id" not in features


def test_chronological_split_excludes_timestamp_feature():
    frame = sample_frame()
    frame["timestamp"] = pd.date_range("2026-01-01", periods=len(frame), freq="h")
    _, report, features = train(frame, time_column="timestamp", seed=17)
    assert "weighted avg" in report
    assert "timestamp" not in features


def test_group_aware_split_rejects_missing_group_identifiers():
    frame = pd.DataFrame({
        "duration": list(range(1, 11)),
        "session_id": ["session-a"] * 5 + [None] * 5,
        "Label": ["BENIGN", "ATTACK"] * 5,
    })
    with pytest.raises(ValueError, match="contains missing values"):
        train(frame, group_column="session_id")
