from fastapi.testclient import TestClient

from app.main import app, EVENTS, ALERTS

client = TestClient(app)


def setup_function():
    EVENTS.clear()
    ALERTS.clear()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ingest_and_metrics():
    event = {
        "src_ip": "192.0.2.10",
        "dst_ip": "192.0.2.20",
        "dst_port": 22,
        "bytes": 900,
        "packets": 8,
        "failed_logins": 9,
        "event_type": "authentication",
    }
    response = client.post("/api/events", json=event)
    assert response.status_code == 200
    assert response.json()["accepted"] == 1
    assert len(client.get("/api/alerts").json()["items"]) >= 1
    assert client.get("/api/metrics").json()["total_events"] == 1


def test_demo_endpoint():
    response = client.post("/api/events/demo")
    assert response.status_code == 200
    assert response.json()["accepted"] == 4
