"""Choose a score threshold under a target false-positive-rate constraint."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def calibrate_threshold(
    labels,
    scores,
    positive_label: str = "ATTACK",
    max_fpr: float = 0.01,
) -> dict:
    """Maximize recall while keeping the false-positive rate <= max_fpr."""
    y_true = np.asarray([str(label).strip() == positive_label.strip() for label in labels], dtype=bool)
    values = np.asarray(scores, dtype=float)
    if y_true.ndim != 1 or values.ndim != 1 or len(y_true) != len(values):
        raise ValueError("Labels and scores must be one-dimensional arrays of equal length.")
    if len(values) == 0 or not np.isfinite(values).all():
        raise ValueError("Scores must be non-empty and finite.")
    if not 0 <= max_fpr <= 1:
        raise ValueError("max_fpr must be between 0 and 1.")
    positives = int(y_true.sum())
    negatives = int((~y_true).sum())
    if positives == 0 or negatives == 0:
        raise ValueError("Calibration data must contain both positive and negative labels.")

    candidates = np.concatenate(([np.nextafter(values.max(), np.inf)], np.unique(values)))
    best = None
    for threshold in candidates:
        predicted = values >= threshold
        tp = int(np.sum(predicted & y_true))
        fp = int(np.sum(predicted & ~y_true))
        fn = positives - tp
        tn = negatives - fp
        fpr = fp / negatives
        recall = tp / positives
        precision = tp / (tp + fp) if tp + fp else 0.0
        if fpr <= max_fpr:
            candidate = {
                "threshold": float(threshold),
                "false_positive_rate": float(fpr),
                "recall": float(recall),
                "precision": float(precision),
                "true_positives": tp,
                "false_positives": fp,
                "true_negatives": tn,
                "false_negatives": fn,
            }
            if best is None or (candidate["recall"], -candidate["false_positive_rate"]) > (
                best["recall"], -best["false_positive_rate"]
            ):
                best = candidate
    return best


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Labelled validation CSV with precomputed scores")
    parser.add_argument("--target", default="Label")
    parser.add_argument("--score-column", default="risk_score")
    parser.add_argument("--positive-label", default="ATTACK")
    parser.add_argument("--max-fpr", type=float, default=0.01)
    parser.add_argument("--output", default="ml-engine/artifacts/threshold_calibration.json")
    args = parser.parse_args()

    frame = pd.read_csv(args.input, low_memory=False)
    for column in (args.target, args.score_column):
        if column not in frame:
            raise ValueError(f"Required column {column!r} is missing.")
    result = calibrate_threshold(
        frame[args.target], frame[args.score_column], args.positive_label, args.max_fpr
    )
    result.update({
        "target": args.target,
        "score_column": args.score_column,
        "positive_label": args.positive_label,
        "max_fpr": args.max_fpr,
        "samples": int(len(frame)),
    })
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2))
    print(f"Recommended threshold: {result['threshold']:.4f}")
    print(f"Validation FPR: {result['false_positive_rate']:.4f}; recall: {result['recall']:.4f}")


if __name__ == "__main__":
    main()
