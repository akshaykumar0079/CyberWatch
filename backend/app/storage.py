"""SQLite persistence for CyberWatch events and alerts.

The database path can be overridden with CYBERWATCH_DB_PATH. SQLite is used
for a zero-service local setup; production deployments should use managed storage.
"""
from __future__ import annotations

import json
from contextlib import closing
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "cyberwatch.db"


def _connect() -> sqlite3.Connection:
    path = Path(os.getenv("CYBERWATCH_DB_PATH", str(DEFAULT_DB_PATH))).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_store() -> None:
    with closing(_connect()) as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payload TEXT NOT NULL
            )"""
        )
        connection.execute(
            """CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY,
                payload TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('open', 'acknowledged', 'resolved'))
            )"""
        )
        connection.execute(
            """CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                method TEXT NOT NULL,
                path TEXT NOT NULL,
                status_code INTEGER NOT NULL,
                duration_ms REAL NOT NULL
            )"""
        )
        connection.commit()


def load_events() -> list[dict[str, Any]]:
    initialize_store()
    with _connect() as connection:
        rows = connection.execute("SELECT id, payload FROM events ORDER BY id").fetchall()
    return [{**json.loads(row["payload"]), "id": row["id"]} for row in rows]


def load_alerts() -> list[dict[str, Any]]:
    initialize_store()
    with _connect() as connection:
        rows = connection.execute("SELECT id, payload, status FROM alerts ORDER BY id DESC").fetchall()
    return [
        {**json.loads(row["payload"]), "id": row["id"], "status": row["status"]}
        for row in rows
    ]


def save_event(record: dict[str, Any]) -> dict[str, Any]:
    initialize_store()
    payload = {key: value for key, value in record.items() if key != "id"}
    with _connect() as connection:
        cursor = connection.execute(
            "INSERT INTO events(payload) VALUES (?)",
            (json.dumps(payload, separators=(",", ":")),),
        )
        record_id = int(cursor.lastrowid)
        connection.commit()
    return {**payload, "id": record_id}


def save_alert(alert: dict[str, Any]) -> None:
    initialize_store()
    payload = {key: value for key, value in alert.items() if key not in {"id", "status"}}
    with _connect() as connection:
        connection.execute(
            "INSERT OR REPLACE INTO alerts(id, payload, status) VALUES (?, ?, ?)",
            (alert["id"], json.dumps(payload, separators=(",", ":")), alert["status"]),
        )
        connection.commit()


def set_alert_status(alert_id: int, status: str) -> bool:
    initialize_store()
    with _connect() as connection:
        cursor = connection.execute(
            "UPDATE alerts SET status = ? WHERE id = ?", (status, alert_id)
        )
        connection.commit()
        return cursor.rowcount > 0


def reset_store() -> None:
    """Clear persisted records. Intended for isolated tests and local demos."""
    initialize_store()
    with _connect() as connection:
        connection.execute("DELETE FROM alerts")
        connection.execute("DELETE FROM events")
        connection.execute("DELETE FROM audit_logs")
        connection.execute("DELETE FROM sqlite_sequence WHERE name = 'events'")
        connection.commit()


def append_alert_note(alert_id: int, note: str) -> dict[str, Any] | None:
    """Append an analyst note to an alert and return its updated record."""
    with closing(_connect()) as connection:
        row = connection.execute(
            "SELECT payload, status FROM alerts WHERE id = ?", (alert_id,)
        ).fetchone()
        if row is None:
            return None
        payload = json.loads(row["payload"])
        notes = payload.setdefault("notes", [])
        notes.append({
            "text": note.strip(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        connection.execute(
            "UPDATE alerts SET payload = ? WHERE id = ?",
            (json.dumps(payload, separators=(",", ":")), alert_id),
        )
        connection.commit()
    return {**payload, "id": alert_id, "status": row["status"]}


def record_api_audit(method: str, path: str, status_code: int, duration_ms: float) -> None:
    """Store metadata for an API write request; never store bodies or credentials."""
    with closing(_connect()) as connection:
        connection.execute(
            """INSERT INTO audit_logs(timestamp, method, path, status_code, duration_ms)
               VALUES (?, ?, ?, ?, ?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                method,
                path,
                status_code,
                round(duration_ms, 2),
            ),
        )
        connection.commit()


def load_api_audit(limit: int = 100) -> list[dict[str, Any]]:
    initialize_store()
    with closing(_connect()) as connection:
        rows = connection.execute(
            """SELECT id, timestamp, method, path, status_code, duration_ms
               FROM audit_logs ORDER BY id DESC LIMIT ?""",
            (max(1, min(limit, 500)),),
        ).fetchall()
    return [dict(row) for row in rows]
