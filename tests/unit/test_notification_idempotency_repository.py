from unittest.mock import Mock, patch

from botocore.exceptions import ClientError

from cloudops_engine.repositories.notification_idempotency_repository import (
    NotificationIdempotencyRepository,
)


def test_claim_notification_succeeds_for_new_key():
    dynamodb_table = Mock()

    with patch("boto3.resource") as boto3_resource:
        boto3_resource.return_value.Table.return_value = dynamodb_table

        repository = NotificationIdempotencyRepository(
            table_name="test-table",
            region_name="ap-south-1",
        )

    result = repository.claim_notification("INC-001#DETECTED")

    assert result is True

    dynamodb_table.put_item.assert_called_once_with(
        Item={
            "notification_key": "INC-001#DETECTED",
        },
        ConditionExpression=(
            "attribute_not_exists(notification_key)"
        ),
    )


def test_claim_notification_returns_false_for_duplicate_key():
    dynamodb_table = Mock()

    duplicate_error = ClientError(
        {
            "Error": {
                "Code": "ConditionalCheckFailedException",
                "Message": "The conditional request failed",
            }
        },
        "PutItem",
    )

    dynamodb_table.put_item.side_effect = duplicate_error

    with patch("boto3.resource") as boto3_resource:
        boto3_resource.return_value.Table.return_value = dynamodb_table

        repository = NotificationIdempotencyRepository(
            table_name="test-table",
            region_name="ap-south-1",
        )

    result = repository.claim_notification("INC-001#DETECTED")

    assert result is False
    
def test_release_notification_deletes_notification_key():
    dynamodb_table = Mock()

    with patch("boto3.resource") as boto3_resource:
        boto3_resource.return_value.Table.return_value = dynamodb_table

        repository = NotificationIdempotencyRepository(
            table_name="test-table",
            region_name="ap-south-1",
        )

    repository.release_notification("INC-001#DETECTED")

    dynamodb_table.delete_item.assert_called_once_with(
        Key={
            "notification_key": "INC-001#DETECTED",
        },
    )