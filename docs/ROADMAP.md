# CyberWatch development roadmap

## MVP foundation
- [x] FastAPI event ingestion and CSV upload
- [x] Isolation Forest anomaly scoring
- [x] Explainable brute-force, scan and privilege rules
- [x] React security operations dashboard
- [x] API tests and GitHub Actions workflow

## ML research track
- [x] Dataset validation and cleaning utility
- [x] Mixed numeric/categorical preprocessing pipeline
- [x] Random Forest supervised classifier training
- [x] Held-out evaluation report
- [x] Feature-importance export
- [ ] CIC-IDS2017 benchmark with documented label mapping
- [ ] UNSW-NB15 external validation
- [x] Group-aware and chronological holdout split options with tests
- [ ] Threshold calibration and false-positive analysis
- [x] Model card with limitations and dataset provenance

## Platform engineering
- [x] Durable event and alert persistence (SQLite, single-instance/local deployment)
- [ ] Authentication and role-based access
- [x] WebSocket event streaming with cursor support and polling fallback
- [x] Alert acknowledgement and resolution API + dashboard actions
- [x] Persist analyst investigation notes on alerts
- [ ] Incident assignment and ownership
- [x] In-memory per-client API rate limiting for single-process deployments
- [x] Metadata-only API write audit log persisted in SQLite
- [ ] Distributed rate limiting for multi-instance deployments
- [ ] Deployment configuration and security review

## Research integrity

Never report benchmark accuracy until the model has been trained and evaluated on a documented, held-out real dataset. Synthetic demo data is for exercising application flows only.
