"""CyberWatch REST API."""
from __future__ import annotations

import asyncio
import csv
import io
import os
import time
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import FastAPI, File, HTTPException, UploadFile, Query, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .detector import ThreatDetector
from . import storage
from .security import SlidingWindowRateLimiter

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

rate_limiter = SlidingWindowRateLimiter(
    limit=int(os.getenv("CYBERWATCH_RATE_LIMIT_PER_MINUTE", "120")),
    window_seconds=60,
)


@app.middleware("http")
async def enforce_api_rate_limit(request: Request, call_next):
    is_api = request.url.path.startswith("/api/") and request.method != "OPTIONS"
    is_write = is_api and request.method in {"POST", "PATCH", "PUT", "DELETE"}
    started = time.perf_counter()
    if is_api:
        client_key = request.client.host if request.client else "unknown"
        if not rate_limiter.allow(client_key):
            response = JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Retry in a minute."},
                headers={"Retry-After": "60"},
            )
        else:
            response = await call_next(request)
        if is_write:
            storage.record_api_audit(
                request.method,
                request.url.path,
                response.status_code,
                (time.perf_counter() - started) * 1000,
            )
        return response
    return await call_next(request)


detector = ThreatDetector()
storage.initialize_store()
EVENTS: list[dict[str, Any]] = storage.load_events()
ALERTS: list[dict[str, Any]] = storage.load_alerts()


class AlertStatusUpdate(BaseModel):
    status: Literal["open", "acknowledged", "resolved"]


class AlertNoteInput(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


class AlertAssigneeInput(BaseModel):
    assignee: str | None = Field(default=None, max_length=80)


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
            "reasons": result["reasons"],
            "status": "open",
            "notes": [],
        }
        storage.save_alert(alert)
        ALERTS.insert(0, alert)
    return record


@app.websocket("/ws/events")
async def stream_events(websocket: WebSocket, after_id: int | None = None) -> None:
    """Stream stored and newly ingested events to connected SOC dashboards."""
    await websocket.accept()
    last_seen_id = after_id if after_id is not None else (EVENTS[-1]["id"] if EVENTS else 0)
    try:
        while True:
            for event in EVENTS:
                if event["id"] > last_seen_id:
                    await websocket.send_json({"type": "security_event", "data": event})
                    last_seen_id = event["id"]
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        return


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

@app.patch("/api/alerts/{alert_id}/assignee")
def set_alert_assignee(alert_id: int, payload: AlertAssigneeInput) -> dict:
    """Assign an alert to an analyst or clear its assignment."""
    assignee = payload.assignee.strip() if payload.assignee else None
    if payload.assignee is not None and not assignee:
        raise HTTPException(status_code=422, detail="Assignee cannot be blank")
    updated = storage.assign_alert(alert_id, assignee)
    if updated is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    cached = next((item for item in ALERTS if item["id"] == alert_id), None)
    if cached is not None:
        cached["assignee"] = assignee
    return {"item": updated}


@app.get("/api/audit")
def list_api_audit(limit: int = Query(default=100, ge=1, le=500)) -> dict:
    """List metadata-only audit entries for API write operations."""
    items = storage.load_api_audit(limit)
    return {"items": items, "total": len(items)}


@app.get("/api/metrics")
def metrics() -> dict:
    total = len(EVENTS)
    suspicious = sum(1 for event in EVENTS if event["is_anomaly"])
    severities = {name: sum(1 for alert in ALERTS if alert["severity"] == name) for name in ("critical", "high", "medium", "low")}
    flagged_rate = round((suspicious / total) * 100, 1) if total else 0
    return {
        "total_events": total,
        "suspicious_events": suspicious,
        "open_alerts": sum(1 for alert in ALERTS if alert["status"] == "open"),
        "flagged_rate": flagged_rate,
        "detection_rate": flagged_rate,  # Backward-compatible alias; not model accuracy.
        "severity_breakdown": severities,
    }
