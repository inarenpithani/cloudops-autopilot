from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from cloudops_engine.models.remediation_result import RemediationResult
from cloudops_engine.repositories.remediation_execution_repository import (
    RemediationExecutionRepository,
)


def create_remediation_result() -> RemediationResult:
    started_at = datetime.now(timezone.utc)
    completed_at = datetime.now(timezone.utc)

    return RemediationResult(
        action="Reboot EC2 instance",
        action_id="EC2_REBOOT",
        resource_id="i-test-instance",
        status="SUCCESS",
        started_at=started_at,
        completed_at=completed_at,
        message="Remediation action executed successfully.",
        error=None,
    )


@patch(
    "cloudops_engine.repositories.remediation_execution_repository.boto3.resource"
)
def test_save_remediation_execution(mock_boto3_resource):
    mock_table = MagicMock()
    mock_boto3_resource.return_value.Table.return_value = mock_table

    repository = RemediationExecutionRepository(
        table_name="test-remediation-executions",
        region_name="ap-south-1",
    )

    result = create_remediation_result()

    repository.save(
        incident_id="INC-TEST-001",
        result=result,
    )

    mock_table.put_item.assert_called_once()

    item = mock_table.put_item.call_args.kwargs["Item"]

    assert item["execution_id"] == "INC-TEST-001:EC2_REBOOT"
    assert item["incident_id"] == "INC-TEST-001"
    assert item["action_id"] == "EC2_REBOOT"
    assert item["resource_id"] == "i-test-instance"
    assert item["status"] == "SUCCESS"
    assert item["message"] == (
        "Remediation action executed successfully."
    )
    assert "error" not in item


@patch(
    "cloudops_engine.repositories.remediation_execution_repository.boto3.resource"
)
def test_save_failed_remediation_execution_includes_error(
    mock_boto3_resource,
):
    mock_table = MagicMock()
    mock_boto3_resource.return_value.Table.return_value = mock_table

    repository = RemediationExecutionRepository(
        table_name="test-remediation-executions",
        region_name="ap-south-1",
    )

    result = RemediationResult(
        action="Reboot EC2 instance",
        action_id="EC2_REBOOT",
        resource_id="i-test-instance",
        status="FAILED",
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        message="Remediation action failed during AWS execution.",
        error="AWS reboot failed",
    )

    repository.save(
        incident_id="INC-TEST-002",
        result=result,
    )

    item = mock_table.put_item.call_args.kwargs["Item"]

    assert item["execution_id"] == "INC-TEST-002:EC2_REBOOT"
    assert item["status"] == "FAILED"
    assert item["error"] == "AWS reboot failed"


@patch(
    "cloudops_engine.repositories.remediation_execution_repository.boto3.resource"
)
def test_save_skipped_remediation_execution(
    mock_boto3_resource,
):
    mock_table = MagicMock()
    mock_boto3_resource.return_value.Table.return_value = mock_table

    repository = RemediationExecutionRepository(
        table_name="test-remediation-executions",
        region_name="ap-south-1",
    )

    result = RemediationResult(
        action="Reboot EC2 instance",
        action_id="EC2_REBOOT",
        resource_id="i-test-instance",
        status="SKIPPED",
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        message=(
            "Remediation action was skipped because "
            "the same action was already executed "
            "for this incident."
        ),
        error=None,
    )

    repository.save(
        incident_id="INC-TEST-003",
        result=result,
    )

    item = mock_table.put_item.call_args.kwargs["Item"]

    assert item["execution_id"] == "INC-TEST-003:EC2_REBOOT"
    assert item["status"] == "SKIPPED"
    assert "error" not in item