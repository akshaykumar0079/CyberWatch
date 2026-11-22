# CyberWatch project status

## Status

**Portfolio MVP complete.** The project has a runnable React SOC dashboard, FastAPI backend, anomaly detection, offline supervised ML tooling, persistent alert workflows, and Docker-based local deployment.

## Delivered

- JSON and CSV security-event ingestion with validation and bounded upload sizes.
- Online Isolation Forest anomaly scoring plus explainable brute-force, scan and privilege rules.
- Risk scoring, severity labels and full detection-reason lists.
- SQLite persistence for events, alerts, alert status, analyst notes, assignments and metadata-only write audit records.
- Alert filtering, acknowledgement, resolution, assignment and investigation notes in the dashboard.
- WebSocket event stream with a polling fallback.
- Per-client sliding-window API rate limiting for single-process deployments.
- Offline Random Forest training, preprocessing, evaluation, feature-importance export, group/time-aware splits and false-positive-constrained score-threshold calibration.
- Model card, dataset preparation guide, security notes, API documentation and Docker Compose setup.

## Verified checks

The latest GitHub Actions run completed successfully:

- Backend API/security/storage tests: 20 passed.
- ML pipeline tests: 10 passed.
- Frontend production build: passed.
- Docker image build: passed.
- Docker Compose configuration validation: passed.
- Running API container health smoke test: passed.

Run: https://github.com/akshaykumar0079/CyberWatch/actions/runs/45057814038

## Explicit limitations

This is a portfolio/demo MVP, not a production SIEM. No real CIC-IDS2017 or UNSW-NB15 benchmark result is claimed. The online Isolation Forest baseline is synthetic; the offline Random Forest workflow is not wired into live inference. Authentication/RBAC, TLS, distributed rate limiting and a production security review remain future work.

Use sanitized data only. Review SECURITY.md and docs/MODEL_CARD.md before deployment or interpreting model scores.
