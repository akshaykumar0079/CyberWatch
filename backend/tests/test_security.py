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
