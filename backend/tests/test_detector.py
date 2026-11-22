from app.detector import ThreatDetector


def test_repeated_failed_logins_raise_high_risk():
    result = ThreatDetector().analyze({
        "bytes": 500, "packets": 5, "failed_logins": 8,
        "dst_port": 22, "src_port": 52000, "event_type": "authentication",
    })
    assert result["risk_score"] >= 75
    assert result["severity"] in {"high", "critical"}
    assert any("brute force" in reason for reason in result["reasons"])


def test_privilege_event_is_flagged():
    result = ThreatDetector().analyze({
        "bytes": 1200, "packets": 8, "failed_logins": 0,
        "dst_port": 443, "src_port": 53000, "event_type": "privilege_escalation",
    })
    assert result["risk_score"] >= 85
    assert result["is_anomaly"]
