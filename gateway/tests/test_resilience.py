from app.core.resilience import CircuitBreaker


def test_circuit_breaker_tracks_open_and_closed_states():
    breaker = CircuitBreaker(threshold=2, reset_seconds=60)

    assert breaker.allow("payments") is True
    breaker.failure("payments")
    breaker.failure("payments")

    assert breaker.allow("payments") is False
    breaker.success("payments")

    assert breaker.allow("payments") is True
