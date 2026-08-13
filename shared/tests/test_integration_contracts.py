from shared.connectors.contract_clients import ContractClient, ContractRequest
from shared.schemas.validation import SerializationAdapter, SimpleSchemaValidator
from shared.tenancy.multi_tenant import TenantContext, tenant_context
from shared.webhooks.dispatchers import WebhookDispatcher, WebhookEvent


def test_webhook_dispatcher_and_schema_validation(monkeypatch):
    class FakeResponse:
        status = 202

        def __init__(self, body):
            self._body = body.encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return self._body

    def fake_urlopen(request, timeout=5):
        assert request.full_url == "https://example.test/hooks"
        return FakeResponse("ok")

    monkeypatch.setattr("shared.webhooks.dispatchers.urllib.request.urlopen", fake_urlopen)
    dispatcher = WebhookDispatcher("https://example.test/hooks")
    result = dispatcher.dispatch(WebhookEvent("payment.created", {"id": "1"}, signature="abc"))
    assert result["status"] == 202

    validator = SimpleSchemaValidator({"id": {"required": True, "type": "string"}})
    assert validator.validate({"id": "abc"}) is True
    assert validator.validate({"amount": 1}) is False

    assert SerializationAdapter.to_dict({"user": {"name": "Ada"}}) == {"user": {"name": "Ada"}}


def test_multi_tenant_context_and_contract_client(monkeypatch):
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
        assert request.full_url == "https://api.test/payments"
        return FakeResponse('{"ok": true}')

    monkeypatch.setattr("shared.connectors.contract_clients.urllib.request.urlopen", fake_urlopen)
    with tenant_context("tenant-42", metadata={"region": "eu"}):
        ctx = TenantContext.current()
        assert ctx.tenant_id == "tenant-42"
        client = ContractClient("https://api.test")
        response = client.send(ContractRequest("GET", "/payments"))
        assert response["status"] == 200
        assert response["body"]["ok"] is True
