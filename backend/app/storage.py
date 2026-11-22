"""SQLite persistence for CyberWatch events and alerts.

The database path can be overridden with CYBERWATCH_DB_PATH. SQLite is used
for a zero-service local setup; production deployments should use managed storage.
"""
from __future__ import annotations

import json
import os
import sqlite3
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
    with _connect() as connection:
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
        connection.execute("DELETE FROM sqlite_sequence WHERE name = 'events'")
        connection.commit()
