"""Export ranked feature importance from a trained Random Forest pipeline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import joblib


def get_importances(model):
    classifier = model.named_steps["classifier"]
    preprocessor = model.named_steps["preprocess"]
    names = preprocessor.get_feature_names_out()
    values = classifier.feature_importances_
    if len(names) != len(values):
        raise ValueError("Feature names and importance values do not align.")
    return sorted(
        [{"feature": str(name), "importance": float(value)} for name, value in zip(names, values)],
        key=lambda item: item["importance"],
        reverse=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", default="ml-engine/artifacts/feature_importance.json")
    args = parser.parse_args()
    ranked = get_importances(joblib.load(args.model))
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(ranked, indent=2))
    print(f"Saved {len(ranked)} feature rankings to {destination}")


if __name__ == "__main__":
    main()
