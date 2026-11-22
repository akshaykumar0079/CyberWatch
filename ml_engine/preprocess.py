"""Validate and normalize common intrusion-detection CSV exports."""
from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd


def load_dataset(path: str | Path, target: str = "Label") -> pd.DataFrame:
    frame = pd.read_csv(path, low_memory=False)
    frame.columns = [str(column).strip() for column in frame.columns]
    if frame.empty:
        raise ValueError("The input dataset contains no rows.")
    if target not in frame.columns:
        raise ValueError(
            f"Target column {target!r} was not found. Available columns: "
            + ", ".join(frame.columns)
        )
    frame = frame.loc[:, ~frame.columns.str.match(r"^Unnamed")]
    frame = frame.dropna(axis=1, how="all")
    frame[target] = frame[target].astype(str).str.strip()
    frame = frame[frame[target].ne("")]
    frame = frame.replace([float("inf"), float("-inf")], pd.NA)
    return frame.drop_duplicates().reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Source IDS CSV")
    parser.add_argument("--output", required=True, help="Cleaned CSV destination")
    parser.add_argument("--target", default="Label", help="Target label column")
    args = parser.parse_args()

    cleaned = load_dataset(args.input, args.target)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(destination, index=False)
    print(f"Saved {len(cleaned):,} rows and {len(cleaned.columns):,} columns to {destination}")


if __name__ == "__main__":
    main()
