import pandas as pd

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
    result = evaluate(frame, "Label", model)
    assert "duration" in features
    assert "weighted avg" in report
    assert 0 <= result["accuracy"] <= 1
    assert result["samples"] == len(frame)
