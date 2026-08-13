import time

from shared.api_keys.api_key_utils import APIKeyManager
from shared.audit.audit_logger import AuditLogger
from shared.background.workers import BackgroundTask, BackgroundWorker
from shared.circuit_breaker.circuit_breaker import CircuitBreaker, CircuitState
from shared.feature_flags.feature_flags import FeatureFlag, FeatureFlagClient
from shared.notifications.notifier import Notification, NotificationService
from shared.redis.redis_manager import RedisManager
from shared.scheduler.scheduler import ScheduledJob, Scheduler


def test_redis_manager_ttl_and_publish():
    manager = RedisManager()
    manager.set("counter", 1, ttl_seconds=1)
    assert manager.get("counter") == 1
    time.sleep(1.2)
    assert manager.get("counter") is None

    manager.publish("events", {"kind": "payment"})
    assert "payment" in manager.subscribe("events")


def test_api_key_manager_round_trip():
    manager = APIKeyManager(secret_key="shared-secret")
    key, record = manager.create_key(key_id="key-1")
    assert manager.validate_key(key, record) is True
    assert manager.validate_key("wrong", record) is False


def test_circuit_breaker_opens_after_failures():
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout_seconds=0.01)

    def failing():
        raise RuntimeError("down")

    for _ in range(2):
        try:
            breaker.call(failing)
        except RuntimeError:
            pass

    assert breaker.state == CircuitState.OPEN


def test_feature_flags_client():
    client = FeatureFlagClient()
    client.register(FeatureFlag("payments", enabled=True))
    assert client.is_enabled("payments") is True
    client.set_enabled("payments", False)
    assert client.is_enabled("payments") is False


def test_background_worker_and_scheduler():
    calls = []

    task = BackgroundTask("demo", lambda: calls.append("tick"), interval_seconds=0.01)
    worker = BackgroundWorker(task)
    worker.start()
    time.sleep(0.03)
    worker.stop()
    assert len(calls) >= 1

    scheduler = Scheduler()
    scheduler.add_job(ScheduledJob("demo", lambda: calls.append("scheduled"), cron_expression="* * * * *"))
    scheduler.run_due_jobs()
    assert "scheduled" in calls


def test_audit_logger_and_notifications():
    logger = AuditLogger()
    logger.log("payment.created", "svc-payments", payload={"amount": 100})
    assert logger.entries()[0].event_type == "payment.created"

    service = NotificationService()
    delivered = []
    service.add_handler(lambda notification: delivered.append(notification.subject))
    service.send(Notification("ops@example.com", "Payment", "processed"))
    assert delivered == ["Payment"]
