"""CyberWatch REST API."""
from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import FastAPI, File, HTTPException, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .detector import ThreatDetector
from . import storage

app = FastAPI(
    title="CyberWatch API",
    description="AI-assisted security event monitoring demo",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

detector = ThreatDetector()
storage.initialize_store()
EVENTS: list[dict[str, Any]] = storage.load_events()
ALERTS: list[dict[str, Any]] = storage.load_alerts()


class AlertStatusUpdate(BaseModel):
    status: Literal["open", "acknowledged", "resolved"]


class AlertNoteInput(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


class SecurityEvent(BaseModel):
    timestamp: str | None = None
    src_ip: str = "0.0.0.0"
    dst_ip: str = "0.0.0.0"
    src_port: int = Field(default=0, ge=0, le=65535)
    dst_port: int = Field(default=0, ge=0, le=65535)
    protocol: str = "TCP"
    bytes: int = Field(default=0, ge=0)
    packets: int = Field(default=0, ge=0)
    failed_logins: int = Field(default=0, ge=0)
    username: str = "unknown"
    event_type: str = "network"


def process_event(raw: dict[str, Any]) -> dict[str, Any]:
    event = SecurityEvent(**raw).model_dump()
    event["timestamp"] = event["timestamp"] or datetime.now(timezone.utc).isoformat()
    result = detector.analyze(event)
    record = storage.save_event({**event, **result})
    EVENTS.append(record)
    if result["is_anomaly"]:
        alert = {
            "id": record["id"],
            "timestamp": event["timestamp"],
            "src_ip": event["src_ip"],
            "severity": result["severity"],
            "risk_score": result["risk_score"],
            "title": result["reasons"][0],
            "status": "open",
            "notes": [],
        }
        storage.save_alert(alert)
        ALERTS.insert(0, alert)
    return record


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "CyberWatch API", "version": "0.1.0"}


@app.get("/api/events")
def list_events(limit: int = 100) -> dict:
    return {"items": EVENTS[-max(1, min(limit, 500)):][::-1], "total": len(EVENTS)}


@app.post("/api/events")
def ingest_events(payload: list[SecurityEvent] | SecurityEvent) -> dict:
    batch = payload if isinstance(payload, list) else [payload]
    if len(batch) > 1000:
        raise HTTPException(status_code=413, detail="Maximum batch size is 1000 events")
    created = [process_event(item.model_dump()) for item in batch]
    return {"accepted": len(created), "items": created}


@app.post("/api/events/upload")
async def upload_csv(file: UploadFile = File(...)) -> dict:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")
    raw = await file.read()
    if len(raw) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="CSV must be 5 MB or smaller")
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
        required = {"src_ip", "dst_ip", "dst_port", "bytes", "packets"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise HTTPException(status_code=400, detail=f"CSV must include columns: {', '.join(sorted(required))}")
        rows = list(reader)
        if len(rows) > 1000:
            raise HTTPException(status_code=413, detail="Maximum CSV size is 1000 rows")
        created = [process_event(row) for row in rows]
        return {"accepted": len(created), "items": created}
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded") from exc


@app.post("/api/events/demo")
def load_demo() -> dict:
    samples = [
        {"src_ip": "10.0.0.12", "dst_ip": "10.0.0.2", "src_port": 51022, "dst_port": 443, "bytes": 2400, "packets": 12, "failed_logins": 0, "protocol": "TCP"},
        {"src_ip": "185.22.10.4", "dst_ip": "10.0.0.5", "src_port": 42000, "dst_port": 22, "bytes": 900, "packets": 8, "failed_logins": 12, "username": "root", "event_type": "authentication"},
        {"src_ip": "91.198.4.20", "dst_ip": "10.0.0.8", "src_port": 53000, "dst_port": 3389, "bytes": 120000, "packets": 900, "failed_logins": 0, "event_type": "network"},
        {"src_ip": "10.0.0.44", "dst_ip": "10.0.0.3", "src_port": 50111, "dst_port": 443, "bytes": 4500, "packets": 20, "failed_logins": 0, "event_type": "privilege_escalation"},
    ]
    created = [process_event(item) for item in samples]
    return {"accepted": len(created), "items": created}


@app.get("/api/alerts")
def list_alerts(
    status: str | None = Query(default=None, pattern="^(open|acknowledged|resolved)$"),
    severity: str | None = Query(default=None, pattern="^(critical|high|medium|low)$"),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict:
    """List alerts with optional status/severity filters."""
    filtered = ALERTS
    if status:
        filtered = [alert for alert in filtered if alert["status"] == status]
    if severity:
        filtered = [alert for alert in filtered if alert["severity"] == severity]
    return {"items": filtered[:limit], "total": len(filtered)}


@app.patch("/api/alerts/{alert_id}")
def update_alert_status(
    alert_id: int,
    payload: AlertStatusUpdate,
) -> dict:
    """Acknowledge or resolve an alert."""
    alert = next((item for item in ALERTS if item["id"] == alert_id), None)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    if not storage.set_alert_status(alert_id, payload.status):
        raise HTTPException(status_code=404, detail="Alert not found")
    alert["status"] = payload.status
    return {"item": alert}



@app.post("/api/alerts/{alert_id}/notes")
def add_alert_note(alert_id: int, payload: AlertNoteInput) -> dict:
    """Add a short investigation note to an alert."""
    note = payload.text.strip()
    if not note:
        raise HTTPException(status_code=422, detail="Note cannot be empty")
    updated = storage.append_alert_note(alert_id, note)
    if updated is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    cached = next((item for item in ALERTS if item["id"] == alert_id), None)
    if cached is not None:
        cached["notes"] = updated["notes"]
    return {"item": updated}

@app.get("/api/metrics")
def metrics() -> dict:
    total = len(EVENTS)
    suspicious = sum(1 for event in EVENTS if event["is_anomaly"])
    severities = {name: sum(1 for alert in ALERTS if alert["severity"] == name) for name in ("critical", "high", "medium", "low")}
    return {
        "total_events": total,
        "suspicious_events": suspicious,
        "open_alerts": sum(1 for alert in ALERTS if alert["status"] == "open"),
        "detection_rate": round((suspicious / total) * 100, 1) if total else 0,
        "severity_breakdown": severities,
    }
