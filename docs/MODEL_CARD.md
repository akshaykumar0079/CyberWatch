# CyberWatch model card

## Model inventory

CyberWatch currently contains two separate ML workflows. They are intentionally not presented as one validated production model.

| Component | Purpose | Current status |
|---|---|---|
| Isolation Forest | Online anomaly scoring in the FastAPI event path | Enabled; fitted on a deterministic synthetic normal-traffic baseline |
| Explainable rules | Flag repeated failed logins, high packet counts to non-web ports, and sensitive privilege events | Enabled; transparent heuristic layer |
| Random Forest pipeline | Offline supervised experiments on labelled IDS CSV files | Training/evaluation utilities available; not connected to live API inference |

## Online anomaly detector

- Algorithm: scikit-learn IsolationForest
- Features: bytes, packets, failed logins, destination port, source port
- Baseline: 600 synthetic rows generated with NumPy random seed 42
- Estimator configuration: 150 trees, contamination 0.06, random seed 42
- Rule thresholds: failed logins >= 5; packet count >= 500 for non-web destination ports; explicit privilege-escalation event types
- Risk scores and severity labels combine the anomaly score with the visible rule thresholds

The synthetic baseline makes the demo reproducible. It does not represent a measured enterprise network distribution.

## Offline supervised pipeline

The separate research pipeline uses a preprocessing ColumnTransformer and a RandomForestClassifier with 250 trees and balanced-subsample class weighting. It creates a stratified holdout report and can evaluate a separately supplied holdout CSV.

The offline model is not automatically loaded by the API. Dataset schemas and feature names differ, so a validated feature-mapping layer and real-data evaluation are required before online deployment.

## Intended use

- Demonstrate event ingestion, anomaly scoring, explainable alerts, and analyst workflows.
- Explore IDS dataset preprocessing and supervised model evaluation.
- Support learning and portfolio review in a controlled demo environment.

## Out-of-scope use

- Production incident response or autonomous blocking.
- Proof that a host or user is compromised.
- Compliance certification or security assurance.
- Decisions based solely on a risk score.

## Evaluation and known limitations

No real CIC-IDS2017 or UNSW-NB15 benchmark result is claimed at this stage. The included sample events and synthetic baseline are development fixtures, not an independent test set. The online detector may produce false positives and false negatives, and its thresholds require calibration on representative, permissioned traffic.

Before making performance claims:
1. Record the exact real dataset version, files, license and label mapping.
2. Remove duplicate and leakage-prone identifiers where appropriate.
3. Use time/session/group-aware holdouts when the data structure requires them.
4. Report per-class precision, recall, F1, confusion matrix and false-positive rate.
5. Document class imbalance, threshold selection and limitations.

## Privacy and operations

The local API stores ingested events and alerts in SQLite by default. Database files are not encrypted by this application. Use sanitized demo data unless the deployment has an approved security and retention design. Do not expose the demo API publicly without authentication, access control, TLS, distributed rate limiting, monitoring and a security review. The included per-client limiter is in-memory and intended only for a single-process demo.
