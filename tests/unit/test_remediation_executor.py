from unittest.mock import MagicMock

from cloudops_engine.models.remediation_result import RemediationResult
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


def create_execution_repository():
    repository = MagicMock()
    return repository


def test_ec2_reboot_remediation_executes():
    ec2_client = MagicMock()
    idempotency_repository = MagicMock()
    execution_repository = create_execution_repository()

    idempotency_repository.claim_action.return_value = True

    action = create_reboot_action()

    result = execute_remediation(
        action=action,
        incident_id="INC-TEST-001",
        ec2_client=ec2_client,
        idempotency_repository=idempotency_repository,
        execution_repository=execution_repository,
    )

    assert result.status == "SUCCESS"
    assert result.error is None

    ec2_client.reboot_instance.assert_called_once_with(
        instance_id="i-test-instance",
    )

    idempotency_repository.claim_action.assert_called_once_with(
        incident_id="INC-TEST-001",
        action_id="EC2_REBOOT",
    )

    idempotency_repository.release_action.assert_not_called()

    execution_repository.save.assert_called_once_with(
        incident_id="INC-TEST-001",
        result=result,
    )


def test_unsupported_remediation_action_does_not_call_aws():
    ec2_client = MagicMock()
    idempotency_repository = MagicMock()
    execution_repository = create_execution_repository()

    idempotency_repository.claim_action.return_value = True

    action = RemediationAction(
        action_id="EC2_TERMINATE",
        name="Terminate EC2 instance",
        description="Terminate an EC2 instance.",
        risk_level="HIGH",
        resource_id="i-test-instance",
    )

    result = execute_remediation(
        action=action,
        incident_id="INC-TEST-002",
        ec2_client=ec2_client,
        idempotency_repository=idempotency_repository,
        execution_repository=execution_repository,
    )

    assert result.status == "FAILED"
    assert result.error == (
        "Unsupported remediation action: EC2_TERMINATE"
    )

    ec2_client.reboot_instance.assert_not_called()

    idempotency_repository.release_action.assert_called_once_with(
        incident_id="INC-TEST-002",
        action_id="EC2_TERMINATE",
    )

    execution_repository.save.assert_called_once_with(
        incident_id="INC-TEST-002",
        result=result,
    )


def test_executor_does_not_handle_human_approval():
    ec2_client = MagicMock()
    idempotency_repository = MagicMock()
    execution_repository = create_execution_repository()

    idempotency_repository.claim_action.return_value = True

    action = create_reboot_action()

    result = execute_remediation(
        action=action,
        incident_id="INC-TEST-APPROVAL-001",
        ec2_client=ec2_client,
        idempotency_repository=idempotency_repository,
        execution_repository=execution_repository,
    )

    assert result.status == "SUCCESS"

    ec2_client.reboot_instance.assert_called_once_with(
        instance_id="i-test-instance",
    )


def test_failed_aws_execution_releases_idempotency_claim():
    ec2_client = MagicMock()
    idempotency_repository = MagicMock()
    execution_repository = create_execution_repository()

    idempotency_repository.claim_action.return_value = True

    ec2_client.reboot_instance.side_effect = RuntimeError(
        "AWS reboot failed"
    )

    action = create_reboot_action()

    result = execute_remediation(
        action=action,
        incident_id="INC-TEST-003",
        ec2_client=ec2_client,
        idempotency_repository=idempotency_repository,
        execution_repository=execution_repository,
    )

    assert result.status == "FAILED"
    assert result.error == "AWS reboot failed"

    idempotency_repository.release_action.assert_called_once_with(
        incident_id="INC-TEST-003",
        action_id="EC2_REBOOT",
    )

    execution_repository.save.assert_called_once_with(
        incident_id="INC-TEST-003",
        result=result,
    )


def test_duplicate_remediation_is_skipped_and_audited():
    ec2_client = MagicMock()
    idempotency_repository = MagicMock()
    execution_repository = create_execution_repository()

    idempotency_repository.claim_action.return_value = False

    action = create_reboot_action()

    result = execute_remediation(
        action=action,
        incident_id="INC-TEST-004",
        ec2_client=ec2_client,
        idempotency_repository=idempotency_repository,
        execution_repository=execution_repository,
    )

    assert result.status == "SKIPPED"

    ec2_client.reboot_instance.assert_not_called()

    execution_repository.save.assert_called_once_with(
        incident_id="INC-TEST-004",
        result=result,
    )


def test_empty_action_id_fails_and_is_audited():
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
        incident_id="INC-TEST-005",
        ec2_client=ec2_client,
        idempotency_repository=idempotency_repository,
        execution_repository=execution_repository,
    )

    assert result.status == "FAILED"
    assert result.error == "Remediation action ID cannot be empty."

    ec2_client.reboot_instance.assert_not_called()
    idempotency_repository.claim_action.assert_not_called()

    execution_repository.save.assert_called_once_with(
        incident_id="INC-TEST-005",
        result=result,
    )