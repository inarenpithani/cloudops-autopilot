from unittest.mock import MagicMock

from cloudops_engine.remediation.action import RemediationAction
from cloudops_engine.remediation.executor import execute_remediation


def test_failed_remediation_does_not_report_success():
    ec2_client = MagicMock()
    idempotency_repository = MagicMock()
    execution_repository = MagicMock()

    action = RemediationAction(
        action_id="",
        name="Invalid remediation action",
        description="Invalid remediation action.",
        risk_level="MEDIUM",
        resource_id="i-test-instance",
    )

    result = execute_remediation(
        action=action,
        incident_id="INC-FAIL-001",
        ec2_client=ec2_client,
        idempotency_repository=idempotency_repository,
        execution_repository=execution_repository,
    )

    assert result.status == "FAILED"
    assert result.error == "Remediation action ID cannot be empty."

    ec2_client.reboot_instance.assert_not_called()

    idempotency_repository.claim_action.assert_not_called()

    execution_repository.save.assert_called_once_with(
        incident_id="INC-FAIL-001",
        result=result,
    )