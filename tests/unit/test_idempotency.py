from unittest.mock import MagicMock

from cloudops_engine.remediation.action import RemediationAction
from cloudops_engine.remediation.executor import execute_remediation


def create_reboot_action() -> RemediationAction:
    return RemediationAction(
        action_id="EC2_REBOOT",
        name="Reboot EC2 instance",
        description=(
            "Restart a running EC2 instance "
            "to recover from a controlled incident."
        ),
        risk_level="MEDIUM",
        resource_id="i-test-instance",
    )


def create_idempotency_repository():
    repository = MagicMock()

    repository.claim_action.side_effect = [
        True,
        False,
    ]

    return repository


def create_execution_repository():
    return MagicMock()


def test_same_action_for_same_incident_is_skipped():
    ec2_client = MagicMock()
    idempotency_repository = create_idempotency_repository()
    execution_repository = create_execution_repository()

    action = create_reboot_action()
    incident_id = "INC-TEST-001"

    first_result = execute_remediation(
        action=action,
        incident_id=incident_id,
        ec2_client=ec2_client,
        idempotency_repository=idempotency_repository,
        execution_repository=execution_repository,
    )

    second_result = execute_remediation(
        action=action,
        incident_id=incident_id,
        ec2_client=ec2_client,
        idempotency_repository=idempotency_repository,
        execution_repository=execution_repository,
    )

    assert first_result.status == "SUCCESS"
    assert second_result.status == "SKIPPED"

    ec2_client.reboot_instance.assert_called_once_with(
        instance_id="i-test-instance",
    )

    assert idempotency_repository.claim_action.call_count == 2
    assert execution_repository.save.call_count == 2


def test_same_action_for_different_incidents_is_allowed():
    ec2_client = MagicMock()
    idempotency_repository = MagicMock()
    execution_repository = create_execution_repository()

    idempotency_repository.claim_action.return_value = True

    action = create_reboot_action()

    first_result = execute_remediation(
        action=action,
        incident_id="INC-TEST-002",
        ec2_client=ec2_client,
        idempotency_repository=idempotency_repository,
        execution_repository=execution_repository,
    )

    second_result = execute_remediation(
        action=action,
        incident_id="INC-TEST-003",
        ec2_client=ec2_client,
        idempotency_repository=idempotency_repository,
        execution_repository=execution_repository,
    )

    assert first_result.status == "SUCCESS"
    assert second_result.status == "SUCCESS"

    assert ec2_client.reboot_instance.call_count == 2
    assert idempotency_repository.claim_action.call_count == 2
    assert execution_repository.save.call_count == 2


def test_empty_action_id_fails():
    ec2_client = MagicMock()
    idempotency_repository = MagicMock()
    execution_repository = create_execution_repository()

    action = RemediationAction(
        action_id="",
        name="Invalid action",
        description="Invalid remediation action.",
        risk_level="MEDIUM",
        resource_id="i-test-instance",
    )

    result = execute_remediation(
        action=action,
        incident_id="INC-TEST-004",
        ec2_client=ec2_client,
        idempotency_repository=idempotency_repository,
        execution_repository=execution_repository,
    )

    assert result.status == "FAILED"
    assert result.error == "Remediation action ID cannot be empty."

    ec2_client.reboot_instance.assert_not_called()
    idempotency_repository.claim_action.assert_not_called()
    execution_repository.save.assert_called_once_with(
        incident_id="INC-TEST-004",
        result=result,
    )