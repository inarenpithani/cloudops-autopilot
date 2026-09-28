from botocore.exceptions import ClientError


class NotificationIdempotencyRepository:
    """Persist notification idempotency keys in DynamoDB."""

    def __init__(
        self,
        table_name: str,
        region_name: str = "ap-south-1",
    ):
        import boto3

        self.table = boto3.resource(
            "dynamodb",
            region_name=region_name,
        ).Table(table_name)

    def claim_notification(self, notification_key: str) -> bool:
        """
        Atomically claim a notification key.

        Returns True when the key is newly claimed.
        Returns False when the notification was already claimed.
        """

        try:
            self.table.put_item(
                Item={
                    "notification_key": notification_key,
                },
                ConditionExpression=(
                    "attribute_not_exists(notification_key)"
                ),
            )

            return True

        except ClientError as error:
            error_code = error.response.get("Error", {}).get("Code")

            if error_code == "ConditionalCheckFailedException":
                return False

            raise

    def release_notification(self, notification_key: str) -> None:
        """Release a notification key so a failed notification can be retried."""

        self.table.delete_item(
            Key={
                "notification_key": notification_key,
            },
        )