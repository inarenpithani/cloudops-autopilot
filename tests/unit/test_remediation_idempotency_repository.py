from unittest.mock import MagicMock, patch

from cloudops_engine.repositories.remediation_idempotency_repository import (
    RemediationIdempotencyRepository,
)


@patch(
    "cloudops_engine.repositories.remediation_idempotency_repository.boto3.resource"
)
def test_claim_action_succeeds_for_new_key(mock_boto3_resource):
    mock_table = MagicMock()
    mock_boto3_resource.return_value.Table.return_value = mock_table

    repository = RemediationIdempotencyRepository(
        table_name="test-remediation-idempotency",
        region_name="ap-south-1",
    )

    result = repository.claim_action(
        incident_id="INC-TEST-001",
        action_id="EC2_REBOOT",
    )

    assert result is True

    mock_table.put_item.assert_called_once_with(
        Item={
            "remediation_key": "INC-TEST-001:EC2_REBOOT",
            "incident_id": "INC-TEST-001",
            "action_id": "EC2_REBOOT",
        },
        ConditionExpression=(
            "attribute_not_exists(remediation_key)"
        ),
    )


@patch(
    "cloudops_engine.repositories.remediation_idempotency_repository.boto3.resource"
)
def test_claim_action_returns_false_for_duplicate(
    mock_boto3_resource,
):
    mock_table = MagicMock()
    mock_boto3_resource.return_value.Table.return_value = mock_table

    repository = RemediationIdempotencyRepository(
        table_name="test-remediation-idempotency",
        region_name="ap-south-1",
    )

    from botocore.exceptions import ClientError

    mock_table.put_item.side_effect = ClientError(
        {
            "Error": {
                "Code": "ConditionalCheckFailedException",
                "Message": "The conditional request failed",
            }
        },
        "PutItem",
    )

    result = repository.claim_action(
        incident_id="INC-TEST-001",
        action_id="EC2_REBOOT",
    )

    assert result is False


@patch(
    "cloudops_engine.repositories.remediation_idempotency_repository.boto3.resource"
)
def test_release_action_deletes_key(mock_boto3_resource):
    mock_table = MagicMock()
    mock_boto3_resource.return_value.Table.return_value = mock_table

    repository = RemediationIdempotencyRepository(
        table_name="test-remediation-idempotency",
        region_name="ap-south-1",
    )

    repository.release_action(
        incident_id="INC-TEST-001",
        action_id="EC2_REBOOT",
    )

    mock_table.delete_item.assert_called_once_with(
        Key={
            "remediation_key": "INC-TEST-001:EC2_REBOOT",
        },
    )