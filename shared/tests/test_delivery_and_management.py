import os

from dataclasses import dataclass
from datetime import datetime, timedelta

from shared.migrations.migration_helper import MigrationManager, MigrationStep
from shared.security.secret_rotation import SecretRotationManager, SecretRotationPolicy
from shared.service_mesh.sidecar import SidecarContract, SidecarRegistry
from shared.webhooks.delivery import DeliveryResult, WebhookDeliveryGuarantee


def test_webhook_delivery_guarantee(monkeypatch):
    class FakeResponse:
        status = 200

        def __init__(self, body):
            self._body = body.encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return self._body

    def fake_urlopen(request, timeout=5):
        return FakeResponse("ok")

    monkeypatch.setattr("shared.webhooks.delivery.urllib.request.urlopen", fake_urlopen)
    delivery = WebhookDeliveryGuarantee("https://hooks.test", max_attempts=2, backoff_seconds=0.0)
    result = delivery.send({"id": "1"})
    assert result.success is True
    assert result.attempts == 1


def test_migration_manager():
    applied = []

    def up():
        applied.append("up")

    def down():
        applied.append("down")

    manager = MigrationManager()
    manager.register(MigrationStep("m1", up=up, down=down))
    manager.apply_all()
    assert manager.status()["m1"] is True
    manager.rollback_all()
    assert manager.status()["m1"] is False
    assert applied == ["up", "down"]


def test_secret_rotation_manager():
    values = {"API_KEY": "initial"}

    def provider(name):
        return values.get(name)

    def setter(name, value):
        values[name] = value

    rotated = []

    def callback(name):
        rotated.append(name)

    manager = SecretRotationManager(provider=provider, setter=setter)
    manager.add_policy(SecretRotationPolicy(
        "API_KEY",
        rotate_every=timedelta(seconds=0),
        last_rotated=datetime.utcnow() - timedelta(days=1),
        callback=callback,
    ))
    manager.rotate_if_needed()
    assert values["API_KEY"] != "initial"
    assert rotated == ["API_KEY"]


def test_sidecar_registry():
    registry = SidecarRegistry()
    registry.register(SidecarContract("payments", {"health": "http://payments/health"}))
    service = registry.resolve("payments")
    assert service is not None
    assert service.endpoints["health"] == "http://payments/health"
