import os
import tempfile

from shared.communications.outbound import EmailClient, Message, SMSClient
from shared.context.request_context import RequestContext, request_context
from shared.locking.distributed_lock import DistributedLockManager
from shared.middleware.rate_limit_middleware import RateLimitMiddleware
from shared.secrets.secret_manager import SecretManager
from shared.storage.storage_utils import StorageClient


def test_distributed_locking_and_context_propagation():
    lock_manager = DistributedLockManager(ttl_seconds=1)
    assert lock_manager.acquire("payment", "worker-1") is True
    assert lock_manager.acquire("payment", "worker-2") is False
    assert lock_manager.is_locked("payment") is True
    assert lock_manager.release("payment", "worker-1") is True

    with request_context("corr-123", metadata={"tenant": "acme"}):
        ctx = RequestContext.current()
        assert ctx.correlation_id == "corr-123"
        assert ctx.metadata["tenant"] == "acme"


def test_rate_limit_middleware_and_secret_manager():
    middleware = RateLimitMiddleware(limit=2, window_seconds=1)
    handler = lambda request: {"ok": True}

    assert middleware({"client_id": "user-1"}, handler) == {"ok": True}
    assert middleware({"client_id": "user-1"}, handler) == {"ok": True}
    try:
        middleware({"client_id": "user-1"}, handler)
    except PermissionError:
        pass

    manager = SecretManager(provider=lambda name: "override" if name == "API_TOKEN" else None)
    assert manager.get("API_TOKEN") == "override"
    assert manager.get("MISSING") is None


def test_storage_and_outbound_helpers(tmp_path):
    storage = StorageClient(str(tmp_path))
    path = storage.put("invoices/001.txt", b"hello")
    assert storage.get("invoices/001.txt") == b"hello"
    assert path.exists() is True
    assert storage.delete("invoices/001.txt") is True

    email_client = EmailClient()
    sms_client = SMSClient()
    delivered = []
    email_client.add_handler(lambda message: delivered.append(("email", message.body)))
    sms_client.add_handler(lambda message: delivered.append(("sms", message.body)))
    email_client.send(Message("ops@example.com", "hello"))
    sms_client.send(Message("+254700000000", "world"))
    assert delivered[0][1] == "hello"
    assert delivered[1][1] == "world"
