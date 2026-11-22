from ml_engine.train import train
from ml_engine.tests.test_training import sample_frame
from ml_engine.feature_importance import get_importances


def test_importance_is_sorted_and_non_negative():
    model, _, _ = train(sample_frame(), seed=11)
    ranked = get_importances(model)
    assert ranked
    assert all(item["importance"] >= 0 for item in ranked)
    assert [x["importance"] for x in ranked] == sorted(
        [x["importance"] for x in ranked], reverse=True
    )
