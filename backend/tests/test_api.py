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


def test_alert_can_be_acknowledged_and_resolved():
    client.post("/api/events", json={
        "src_ip": "198.51.100.9", "dst_ip": "10.0.0.5",
        "dst_port": 22, "bytes": 500, "packets": 10,
        "failed_logins": 8, "event_type": "authentication",
    })
    alert = client.get("/api/alerts").json()["items"][0]
    response = client.patch(f"/api/alerts/{alert['id']}", json={"status": "acknowledged"})
    assert response.status_code == 200
    assert response.json()["item"]["status"] == "acknowledged"
    assert client.get("/api/alerts", params={"status": "acknowledged"}).json()["total"] == 1
    resolved = client.patch(f"/api/alerts/{alert['id']}", json={"status": "resolved"})
    assert resolved.json()["item"]["status"] == "resolved"


def test_alert_update_rejects_unknown_alert_and_status():
    missing = client.patch("/api/alerts/9999", json={"status": "resolved"})
    assert missing.status_code == 404
    client.post("/api/events", json={
        "src_ip": "198.51.100.10", "dst_ip": "10.0.0.5",
        "dst_port": 22, "bytes": 500, "packets": 10,
        "failed_logins": 8, "event_type": "authentication",
    })
    alert_id = client.get("/api/alerts").json()["items"][0]["id"]
    invalid = client.patch(f"/api/alerts/{alert_id}", json={"status": "closed"})
    assert invalid.status_code == 422
