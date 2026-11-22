"""Train a reproducible Random Forest classifier on a labelled IDS CSV."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report
from .pipeline import build_preprocessor


def train(
    frame: pd.DataFrame,
    target: str = "Label",
    seed: int = 42,
    group_column: str | None = None,
    time_column: str | None = None,
):
    if target not in frame:
        raise ValueError(f"Target column {target!r} is missing.")
    if group_column and time_column:
        raise ValueError("Choose either group_column or time_column, not both.")
    data = frame.dropna(subset=[target]).copy()
    y = data.pop(target).astype(str)
    if y.nunique() < 2:
        raise ValueError("Supervised training requires at least two target classes.")

    if group_column:
        if group_column not in data:
            raise ValueError(f"Group column {group_column!r} is missing.")
        groups = data.pop(group_column)
        if groups.isna().any():
            raise ValueError(f"Group column {group_column!r} contains missing values.")
        splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed)
        train_idx, test_idx = next(splitter.split(data, y, groups))
        X_train, X_test = data.iloc[train_idx], data.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    elif time_column:
        if time_column not in data:
            raise ValueError(f"Time column {time_column!r} is missing.")
        timestamps = pd.to_datetime(data.pop(time_column), utc=True, errors="coerce")
        if timestamps.isna().any():
            raise ValueError(f"Time column {time_column!r} contains invalid timestamps.")
        ordered = timestamps.sort_values(kind="stable").index
        split_at = int(len(ordered) * 0.8)
        if split_at <= 0 or split_at >= len(ordered):
            raise ValueError("Not enough rows for a chronological holdout split.")
        train_idx, test_idx = ordered[:split_at], ordered[split_at:]
        X_train, X_test = data.loc[train_idx], data.loc[test_idx]
        y_train, y_test = y.loc[train_idx], y.loc[test_idx]
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            data, y, test_size=0.2, random_state=seed, stratify=y
        )

    if y_train.nunique() < 2:
        raise ValueError("The selected training split contains fewer than two classes.")
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
    parser.add_argument("--group-column", help="Optional session/host/group field for leakage-resistant splitting")
    parser.add_argument("--time-column", help="Optional timestamp field for chronological holdout splitting")
    args = parser.parse_args()
    frame = pd.read_csv(args.input, low_memory=False)
    model, report, features = train(frame, args.target, args.seed, args.group_column, args.time_column)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output / "random_forest.joblib")
    (output / "training_report.json").write_text(json.dumps({
        "target": args.target, "features": features, "metrics": report,
        "random_state": args.seed,
        "split_strategy": "group" if args.group_column else "chronological" if args.time_column else "stratified_random",
        "group_column": args.group_column,
        "time_column": args.time_column,
        "test_size": 0.2,
    }, indent=2))
    print(f"Model saved to {output / 'random_forest.joblib'}")
    print(f"Weighted F1: {report.get('weighted avg', {}).get('f1-score', 0):.4f}")


if __name__ == "__main__":
    main()
