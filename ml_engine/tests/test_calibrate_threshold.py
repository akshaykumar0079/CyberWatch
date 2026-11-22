import pytest

from ml_engine.calibrate_threshold import calibrate_threshold


def test_threshold_calibration_maximizes_recall_under_fpr_limit():
    result = calibrate_threshold(
        ["BENIGN", "BENIGN", "ATTACK", "ATTACK"],
        [10, 20, 70, 90],
        positive_label="ATTACK",
        max_fpr=0.0,
    )
    assert result["threshold"] == 70.0
    assert result["false_positive_rate"] == 0.0
    assert result["recall"] == 1.0
    assert result["true_positives"] == 2
    assert result["false_positives"] == 0


def test_threshold_calibration_rejects_single_class_data():
    with pytest.raises(ValueError, match="both positive and negative"):
        calibrate_threshold(["BENIGN", "BENIGN"], [1, 2])


def test_threshold_calibration_rejects_invalid_scores():
    with pytest.raises(ValueError, match="finite"):
        calibrate_threshold(["BENIGN", "ATTACK"], [1, float("nan")])
