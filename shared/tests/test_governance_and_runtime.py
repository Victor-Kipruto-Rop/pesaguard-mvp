from shared.compliance.policy import ComplianceRule, PolicyEnforcer
from shared.exporters.data_exchange import DataExporter, DataImporter
from shared.runtime.contracts import RuntimeContract, RuntimeContractRegistry
from shared.workflows.saga import SagaOrchestrator, SagaStep


def test_saga_orchestrator_and_policy_enforcer():
    orchestrator = SagaOrchestrator()
    executed = []

    orchestrator.add_step(SagaStep("charge", lambda: executed.append("charge") or True, compensation=lambda: executed.append("refund")))
    orchestrator.add_step(SagaStep("notify", lambda: executed.append("notify") or True))
    assert orchestrator.execute() is True

    enforcer = PolicyEnforcer()
    enforcer.add_rule(ComplianceRule("store_approved", lambda ctx: ctx.get("approved") is True))
    assert enforcer.evaluate({"approved": True}) is True
    assert enforcer.evaluate({"approved": False}) is False


def test_data_exchange_and_runtime_contracts():
    records = [{"id": 1, "name": "Ada"}]
    assert DataExporter.export_json(records) == '[{"id": 1, "name": "Ada"}]'
    assert "id,name" in DataExporter.export_csv(records)
    assert DataImporter.import_json('[{"id": 2, "name": "Grace"}]')[0]["name"] == "Grace"
    assert DataImporter.import_csv("id,name\n3,Linus\n")[0]["name"] == "Linus"

    registry = RuntimeContractRegistry()
    registry.register(RuntimeContract("payments", "v1", metadata={"owner": "platform"}))
    contract = registry.get("payments")
    assert contract is not None and contract.version == "v1"
