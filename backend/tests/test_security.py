from fastapi.testclient import TestClient

from app.main import app, rate_limiter
from app.security import SlidingWindowRateLimiter


def test_sliding_window_rate_limit_and_expiry():
    limiter = SlidingWindowRateLimiter(limit=2, window_seconds=10)
    assert limiter.allow("client-a", now=1.0)
    assert limiter.allow("client-a", now=2.0)
    assert not limiter.allow("client-a", now=3.0)
    assert limiter.allow("client-a", now=11.0)


def test_rate_limits_are_isolated_per_client():
    limiter = SlidingWindowRateLimiter(limit=1, window_seconds=60)
    assert limiter.allow("client-a", now=1.0)
    assert not limiter.allow("client-a", now=2.0)
    assert limiter.allow("client-b", now=2.0)


def test_api_middleware_returns_429_when_limit_is_exceeded():
    client = TestClient(app)
    original_limit = rate_limiter.limit
    rate_limiter._hits.clear()
    rate_limiter.limit = 1
    try:
        first = client.get("/api/events")
        second = client.get("/api/events")
        assert first.status_code == 200
        assert second.status_code == 429
        assert second.headers["retry-after"] == "60"
    finally:
        rate_limiter.limit = original_limit
        rate_limiter._hits.clear()
