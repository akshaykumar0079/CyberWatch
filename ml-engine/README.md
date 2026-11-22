# CyberWatch ML Engine

This directory contains offline, reproducible training and evaluation tools. The API's current online detector remains a lightweight demo model trained on a synthetic baseline. These scripts let you train models from a locally downloaded, permitted IDS CSV without committing raw datasets.

## Quick start

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python -m ml_engine.preprocess --input /path/to/ids.csv --output ml-engine/processed/ids_clean.csv
python -m ml_engine.train --input ml-engine/processed/ids_clean.csv --target Label --output ml-engine/artifacts
python -m ml_engine.evaluate --input ml-engine/processed/ids_clean.csv --target Label --model ml-engine/artifacts/random_forest.joblib
```

Run modules from the repository root. For a dataset whose label column is not named `Label`, pass the actual column name using `--target`.

## Dataset guidance

CIC-IDS2017: https://www.unb.ca/cic/datasets/ids-2017.html  
UNSW-NB15: https://research.unsw.edu.au/projects/unsw-nb15-dataset

Review each dataset's terms before use. Keep raw data outside Git. Start with a representative subset while developing.

## Methodology

- Numeric feature columns are median-imputed and standardized.
- Categorical columns are most-frequent-imputed and one-hot encoded.
- A stratified holdout split is used for supervised classification.
- The target label is excluded from the feature matrix.
- Reports include accuracy, precision, recall, F1 and a confusion matrix.

This is a research/portfolio workflow, not a validated production IDS. Do not treat model predictions as proof of compromise.
