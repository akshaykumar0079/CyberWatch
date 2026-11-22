"""Train a reproducible Random Forest classifier on a labelled IDS CSV."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report
from .pipeline import build_preprocessor


def train(frame: pd.DataFrame, target: str = "Label", seed: int = 42):
    if target not in frame:
        raise ValueError(f"Target column {target!r} is missing.")
    data = frame.dropna(subset=[target]).copy()
    y = data.pop(target).astype(str)
    if y.nunique() < 2:
        raise ValueError("Supervised training requires at least two target classes.")
    X_train, X_test, y_train, y_test = train_test_split(
        data, y, test_size=0.2, random_state=seed, stratify=y
    )
    model = Pipeline([
        ("preprocess", build_preprocessor(X_train)),
        ("classifier", RandomForestClassifier(
            n_estimators=250, class_weight="balanced_subsample",
            random_state=seed, n_jobs=-1, min_samples_leaf=2
        )),
    ])
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    report = classification_report(y_test, predictions, output_dict=True, zero_division=0)
    return model, report, list(X_train.columns)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--target", default="Label")
    parser.add_argument("--output", default="ml-engine/artifacts")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    frame = pd.read_csv(args.input, low_memory=False)
    model, report, features = train(frame, args.target, args.seed)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output / "random_forest.joblib")
    (output / "training_report.json").write_text(json.dumps({
        "target": args.target, "features": features, "metrics": report,
        "random_state": args.seed,
    }, indent=2))
    print(f"Model saved to {output / 'random_forest.joblib'}")
    print(f"Weighted F1: {report.get('weighted avg', {}).get('f1-score', 0):.4f}")


if __name__ == "__main__":
    main()
