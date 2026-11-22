# Preparing an intrusion-detection dataset

## CIC-IDS2017

1. Read the dataset page and its terms: https://www.unb.ca/cic/datasets/ids-2017.html
2. Download the flow CSV files from the official source.
3. Keep downloaded files outside the repository (they can be large and may have separate terms).
4. Combine only compatible flow CSV exports into a local CSV if needed.
5. Inspect the label column and pass its exact name to the scripts.

Example:

```bash
python -m ml_engine.preprocess --input ~/datasets/cicids2017.csv --output /tmp/cicids_clean.csv --target Label
python -m ml_engine.train --input /tmp/cicids_clean.csv --target Label
```

## UNSW-NB15

Official page: https://research.unsw.edu.au/projects/unsw-nb15-dataset

UNSW-NB15 exports may use a label field such as `label` rather than `Label`. Supply it explicitly:

```bash
python -m ml_engine.preprocess --input ~/datasets/UNSW_NB15.csv --output /tmp/unsw_clean.csv --target label
python -m ml_engine.train --input /tmp/unsw_clean.csv --target label
```

## Reproducibility checklist

- Record the exact downloaded dataset version and source.
- Record the selected files, target field, random seed and preprocessing choices.
- Remove identifiers and duplicate records where appropriate.
- Avoid random row splitting when records from the same flow/session can leak across splits; prefer time/session/group-aware evaluation.
- Report per-class precision, recall and F1, not only accuracy.
- Do not compare scores across datasets without explaining label mapping and feature differences.
