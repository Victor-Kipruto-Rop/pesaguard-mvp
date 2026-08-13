from shared.discovery.service_discovery import ServiceRegistry, ServiceRegistration
from shared.events.message_bus import EventEnvelope, MessageBus
from shared.events.outbox import OutboxEvent, OutboxStore
from shared.repositories.base_repository import InMemoryRepository


class SampleEntity:
    def __init__(self, entity_id: str, name: str) -> None:
        self.id = entity_id
        self.name = name


def test_message_bus_and_outbox():
    bus = MessageBus()
    received = []
    bus.subscribe("payment.created", lambda envelope: received.append(envelope.payload["id"]))
    bus.publish(EventEnvelope("payment.created", {"id": "p-1"}))
    assert received == ["p-1"]

    outbox = OutboxStore()
    outbox.add(OutboxEvent("payment.created", {"id": "p-1"}))
    events = outbox.drain()
    assert len(events) == 1
    assert events[0].event_type == "payment.created"


def test_repository_and_service_discovery():
    repo = InMemoryRepository[SampleEntity]()
    entity = SampleEntity("e-1", "Ada")
    repo.save(entity)
    assert repo.get_by_id("e-1").name == "Ada"
    assert len(repo.list_all()) == 1

    registry = ServiceRegistry()
    registry.register(ServiceRegistration("payments", "http://payments.internal"))
    found = registry.get("payments")
    assert found is not None and found.address == "http://payments.internal"
