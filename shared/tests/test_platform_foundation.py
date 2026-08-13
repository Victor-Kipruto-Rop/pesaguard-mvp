import hashlib
import json
import os
import threading
import time

import pytest

from shared.authentication.session_manager import SessionManager
from shared.authorization.permissions import Permission, PermissionRegistry, Role
from shared.cache.cache_manager import CacheManager
from shared.configuration.config_loader import ConfigLoader, ValidationError
from shared.context.correlation import CorrelationContext, correlation_id
from shared.database.connection_pool import ConnectionPool
from shared.database.unit_of_work import UnitOfWork
from shared.encryption.encryption import AESGCMCipher, secure_compare
from shared.filters.query_filters import FilterBuilder
from shared.hashing.hash_utils import PasswordHasher
from shared.idempotency.idempotency import IdempotencyStore
from shared.pagination.cursor_pagination import CursorPaginator
from shared.rate_limiting.rate_limiter import SlidingWindowRateLimiter
from shared.retry.retry_utils import RetryPolicy, retry_with_backoff
from shared.serialization.json_helper import to_jsonable, to_json_string
from shared.sorting.sorting import SortSpec, sort_items
from shared.telemetry.tracer import trace_span
from shared.validators.request_validators import validate_payload


def test_session_manager_lifecycle():
    manager = SessionManager(secret_key="session-secret", ttl_seconds=30)
    token = manager.create_session("user-1", metadata={"role": "admin"})
    session = manager.get_session(token)
    assert session is not None
    assert session.user_id == "user-1"
    assert session.metadata["role"] == "admin"

    manager.invalidate_session(token)
    assert manager.get_session(token) is None


def test_permissions_and_roles():
    registry = PermissionRegistry()
    admin = Role("admin", {"read", "write", "delete"})
    reader = Role("reader", {"read"})
    registry.register_role(admin)
    registry.register_role(reader)

    assert registry.has_permission("admin", "delete") is True
    assert registry.has_permission("reader", "delete") is False
    registry.grant_permission("reader", "write")
    assert registry.has_permission("reader", "write") is True


def test_config_loader_and_validation(tmp_path):
    config_file = tmp_path / "settings.json"
    config_file.write_text(json.dumps({"APP_ENV": "production", "APP_PORT": 9000, "FEATURE_X": True}), encoding="utf-8")

    loader = ConfigLoader(str(config_file))
    settings = loader.load()
    assert settings["APP_PORT"] == 9000

    with pytest.raises(ValidationError):
        ConfigLoader(str(config_file), required_keys=["MISSING_KEY"]).load()


def test_connection_pool_and_unit_of_work():
    pool = ConnectionPool(max_connections=2)
    with pool.acquire() as connection:
        connection.execute("SELECT 1")

    with UnitOfWork(pool) as uow:
        uow.execute("INSERT INTO demo VALUES (1)")
        uow.commit()


def test_cache_manager_round_trip_and_ttl():
    cache = CacheManager(default_ttl=1)
    cache.set("hello", "world")
    assert cache.get("hello") == "world"
    time.sleep(1.2)
    assert cache.get("hello") is None


def test_retry_policy_retries_until_success():
    attempts = {"count": 0}

    def flaky():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("boom")
        return "ok"

    policy = RetryPolicy(max_attempts=3, base_delay=0.0)
    result = retry_with_backoff(flaky, policy)
    assert result == "ok"
    assert attempts["count"] == 3


def test_filter_builder_and_sort_engine():
    items = [{"name": "Ada", "role": "admin", "score": 10}, {"name": "Bob", "role": "reader", "score": 8}]
    filtered = FilterBuilder().eq("role", "admin").build()(items)
    sorted_items = sort_items(items, [SortSpec("score", descending=True)])
    assert len(filtered) == 1
    assert sorted_items[0]["name"] == "Ada"


def test_encryption_and_password_hashing():
    cipher = AESGCMCipher(key=b"0123456789abcdef0123456789abcdef")
    ciphertext = cipher.encrypt(b"secret")
    assert cipher.decrypt(ciphertext) == b"secret"
    assert secure_compare(b"abc", b"abc") is True

    hasher = PasswordHasher()
    hashed = hasher.hash_password("super-secret")
    assert hasher.verify_password("super-secret", hashed) is True


def test_idempotency_and_rate_limit():
    store = IdempotencyStore()
    first = store.record("txn-1", {"amount": 100})
    second = store.record("txn-1", {"amount": 100})
    assert first is True
    assert second is False

    limiter = SlidingWindowRateLimiter(limit=2, window_seconds=1)
    assert limiter.allow("user-1") is True
    assert limiter.allow("user-1") is True
    assert limiter.allow("user-1") is False


def test_correlation_context_and_trace_span():
    with correlation_id("req-123"):
        ctx = CorrelationContext.current()
        assert ctx.correlation_id == "req-123"

    with trace_span("db.query") as span:
        assert span.name == "db.query"


def test_serialization_and_validation_helpers():
    payload = {"name": "Ada", "active": True}
    assert to_jsonable(payload)["active"] is True
    assert "name" in to_json_string(payload)
    assert validate_payload({"name": "Ada"}, {"name": {"required": True, "type": "string"}}) is True
