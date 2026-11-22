import pandas as pd
import pytest

from ml_engine.preprocess import load_dataset


def test_load_dataset_trims_labels_and_deduplicates(tmp_path):
    source = tmp_path / "events.csv"
    pd.DataFrame({
        "Flow Duration": [10, 10, 20],
        "Label": [" BENIGN ", " BENIGN ", "Attack"],
        "Unused": [None, None, None],
    }).to_csv(source, index=False)
    result = load_dataset(source)
    assert len(result) == 2
    assert result["Label"].tolist() == ["BENIGN", "Attack"]
    assert "Unused" not in result.columns


def test_missing_target_raises(tmp_path):
    source = tmp_path / "events.csv"
    pd.DataFrame({"value": [1, 2]}).to_csv(source, index=False)
    with pytest.raises(ValueError, match="Target column"):
        load_dataset(source)
