import boto3
from botocore.exceptions import ClientError


class RemediationIdempotencyRepository:
    """Persist remediation idempotency keys in DynamoDB."""

    def __init__(
        self,
        table_name: str,
        region_name: str = "ap-south-1",
    ):
        self.table = boto3.resource(
            "dynamodb",
            region_name=region_name,
        ).Table(table_name)

    def claim_action(
        self,
        incident_id: str,
        action_id: str,
    ) -> bool:
        """
        Atomically claim a remediation action.

        Returns True when the action is newly claimed.
        Returns False when the action was already claimed.
        """

        remediation_key = f"{incident_id}:{action_id}"

        try:
            self.table.put_item(
                Item={
                    "remediation_key": remediation_key,
                    "incident_id": incident_id,
                    "action_id": action_id,
                },
                ConditionExpression=(
                    "attribute_not_exists(remediation_key)"
                ),
            )

            return True

        except ClientError as error:
            error_code = error.response.get("Error", {}).get("Code")

            if error_code == "ConditionalCheckFailedException":
                return False

            raise

    def release_action(
        self,
        incident_id: str,
        action_id: str,
    ) -> None:
        """Release a remediation action so it can be retried."""

        remediation_key = f"{incident_id}:{action_id}"

        self.table.delete_item(
            Key={
                "remediation_key": remediation_key,
            },
        )