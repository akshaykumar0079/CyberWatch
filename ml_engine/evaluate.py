"""Evaluate a saved CyberWatch classifier on a labelled CSV holdout file."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


def evaluate(frame: pd.DataFrame, target: str, model):
    if target not in frame:
        raise ValueError(f"Target column {target!r} is missing.")
    data = frame.dropna(subset=[target]).copy()
    y_true = data.pop(target).astype(str)
    y_pred = model.predict(data)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "classification_report": classification_report(
            y_true, y_pred, output_dict=True, zero_division=0
        ),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
        "labels": sorted(y_true.unique().tolist()),
        "samples": int(len(y_true)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--target", default="Label")
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", default="ml-engine/artifacts/evaluation.json")
    args = parser.parse_args()
    result = evaluate(pd.read_csv(args.input, low_memory=False), args.target, joblib.load(args.model))
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2))
    print(f"Accuracy: {result['accuracy']:.4f} across {result['samples']:,} samples")
    print(f"Evaluation report saved to {destination}")


if __name__ == "__main__":
    main()
