"""Lightweight anomaly detection and explainable security rules."""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import IsolationForest

FEATURES = ["bytes", "packets", "failed_logins", "dst_port", "src_port"]


class ThreatDetector:
    """Isolation Forest detector with a deterministic synthetic normal baseline."""

    def __init__(self) -> None:
        rng = np.random.default_rng(42)
        baseline = np.column_stack(
            [
                rng.lognormal(mean=7.0, sigma=0.65, size=600),  # bytes
                rng.poisson(lam=18, size=600),                 # packets
                rng.poisson(lam=0.15, size=600),               # failed logins
                rng.choice([80, 443, 53, 22, 8080], size=600), # destination port
                rng.integers(1024, 65535, size=600),           # source port
            ]
        )
        self.model = IsolationForest(
            n_estimators=150, contamination=0.06, random_state=42
        )
        self.model.fit(baseline)

    def analyze(self, event: dict) -> dict:
        values = np.array(
            [[max(0, float(event.get(key, 0) or 0)) for key in FEATURES]],
            dtype=float,
        )
        prediction = int(self.model.predict(values)[0])
        anomaly_score = float(-self.model.decision_function(values)[0])
        reasons: list[str] = []

        failed = int(event.get("failed_logins", 0) or 0)
        dst_port = int(event.get("dst_port", 0) or 0)
        packets = int(event.get("packets", 0) or 0)
        event_type = str(event.get("event_type", "")).lower()

        if failed >= 5:
            reasons.append("Repeated failed logins (possible brute force)")
        if packets >= 500 and dst_port not in (80, 443):
            reasons.append("High packet count to a non-web destination port (possible scan)")
        if event_type in {"privilege_escalation", "admin_login_from_unknown_host"}:
            reasons.append("Sensitive privilege or administrator activity")
        if prediction == -1:
            reasons.append("Traffic pattern differs from the learned normal baseline")

        # Rules are deliberately visible and independently explainable.
        risk = min(100, int(max(0.0, anomaly_score) * 120) + min(failed * 8, 40))
        if any("Sensitive privilege" in reason for reason in reasons):
            risk = max(risk, 85)
        if any("brute force" in reason for reason in reasons):
            risk = max(risk, 75)
        if any("possible scan" in reason for reason in reasons):
            risk = max(risk, 65)

        severity = "critical" if risk >= 85 else "high" if risk >= 65 else "medium" if risk >= 40 else "low"
        return {
            "is_anomaly": prediction == -1 or bool(reasons and risk >= 65),
            "anomaly_score": round(anomaly_score, 4),
            "risk_score": risk,
            "severity": severity,
            "reasons": reasons or ["No high-confidence rule triggered"],
        }
