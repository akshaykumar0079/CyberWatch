# CyberWatch machine-learning approach

## Current MVP

The API creates a deterministic synthetic baseline at startup and fits a scikit-learn Isolation Forest. Each ingested event is transformed into five numeric features:

- bytes transferred
- packet count
- failed login count
- destination port
- source port

The model returns an anomaly prediction and decision score. A separate rule layer adds human-readable reasons for repeated failed logins, high packet counts to non-web ports, and sensitive privilege events. The API combines these signals into a 0–100 risk score and a severity label.

## Why Isolation Forest?

Isolation Forest is an unsupervised outlier-detection method. It can be used when a labelled attack dataset is not yet available. It does not identify a specific malware family or prove that an event is malicious. Its output is a triage signal that needs investigation.

## Important limitations

- The bundled baseline is synthetic and is intended only to make the demo run without downloading a dataset.
- Port numbers are categorical in meaning; this MVP treats them as numeric for a compact demonstration. A serious experiment should use suitable categorical encoding or domain-specific features.
- The detector is fitted on startup and is not persisted.
- Events and alerts are held in process memory and are cleared when the API restarts.
- The demo risk score is heuristic, not a calibrated probability.
- No authentication, tenant isolation, durable storage, or production-grade rate limiting is implemented.

## Suggested research evaluation

1. Download CIC-IDS2017 or UNSW-NB15 from its official source and review its license/terms.
2. Document feature selection, missing-value handling, categorical encoding, and label mapping.
3. Split data by time or capture/session where possible to reduce leakage.
4. Compare a rule-only baseline, Isolation Forest, and a supervised classifier.
5. Report precision, recall, F1, confusion matrix, and false-positive rate.
6. Tune thresholds on validation data only and report results on a held-out test set.
7. Record dataset version, preprocessing configuration, random seeds, and model parameters.

Official dataset pages:
- https://www.unb.ca/cic/datasets/ids-2017.html
- https://research.unsw.edu.au/projects/unsw-nb15-dataset
