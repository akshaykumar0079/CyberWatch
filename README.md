# CyberWatch 🛡️

AI-assisted security event monitoring and anomaly detection.

CyberWatch is a runnable portfolio MVP that accepts security events, scores suspicious activity with an Isolation Forest model, applies transparent detection rules, and displays alerts in a React SOC dashboard.

## Features

- FastAPI backend with health, event ingestion, CSV upload, alert and metric endpoints
- Isolation Forest anomaly detection trained on a bundled synthetic baseline
- Explainable rule detections for brute-force attempts, port scans and suspicious privilege events
- Risk scoring and alert severity
- React dashboard with event/alert summaries and live refresh
- Sample CSV, automated backend tests and Docker Compose setup

> **Important:** This is a learning and demonstration project, not a production SIEM or a replacement for endpoint/network security controls. Do not upload confidential logs. The included baseline is synthetic; validate and retrain with an appropriately licensed real dataset before making operational claims.

## Architecture

```text
CSV / JSON events
       |
       v
FastAPI ingestion -----> validation + normalization
       |                           |
       v                           v
Detection service <---- Isolation Forest + rule engine
       |
       v
Risk score + alert records
       |
       +---- REST API ----> React SOC dashboard
```

## Quick start (local)

Requirements: Python 3.10+ and Node.js 18+.

### 1. Start the API

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API: http://127.0.0.1:8000  
Swagger docs: http://127.0.0.1:8000/docs

### 2. Start the dashboard

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Dashboard: http://localhost:5173

The frontend uses the API at `http://127.0.0.1:8000`. Set `VITE_API_URL` to override it.

### 3. Try sample events

Upload `sample-data/security-events.csv` from the dashboard, or use:

```bash
curl -X POST http://127.0.0.1:8000/api/events/demo
```

Then open the dashboard and inspect the alerts.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Service health |
| GET | `/api/events` | List ingested events |
| POST | `/api/events` | Ingest JSON events |
| POST | `/api/events/demo` | Load safe demo events |
| POST | `/api/events/upload` | Upload CSV events |
| GET | `/api/alerts` | List alerts; supports `status`, `severity` and `limit` filters |\n| PATCH | `/api/alerts/{id}` | Change alert status to `open`, `acknowledged` or `resolved` |
| GET | `/api/metrics` | Dashboard metrics |

## Event CSV format

Required: `timestamp,src_ip,dst_ip,src_port,dst_port,protocol,bytes,packets,failed_logins`

Optional: `username,event_type`

## Machine learning notes

The detector uses scikit-learn's Isolation Forest over numeric traffic/authentication features. It is fitted on a deterministic synthetic normal-traffic baseline at startup. A separate rule engine adds explainable detections. The demo dataset is synthetic and deliberately includes a few suspicious patterns.

For a research-grade extension, evaluate on CIC-IDS2017 or UNSW-NB15, prevent train/test leakage, report precision/recall/F1 and false-positive rate, and document dataset licensing and preprocessing.

## Tests

```bash
cd backend
pytest
```

## Roadmap

- [ ] CIC-IDS2017 preprocessing and reproducible evaluation
- [ ] Persist events and alerts in MongoDB
- [ ] Authentication and role-based access
- [ ] WebSocket streaming
- [ ] Model versioning and drift monitoring
- [ ] Deployment hardening and security review

## License

MIT — see [LICENSE](LICENSE).
