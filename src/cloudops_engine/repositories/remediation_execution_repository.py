import boto3

from cloudops_engine.models.remediation_result import RemediationResult


class RemediationExecutionRepository:
    """Persist remediation execution results in Amazon DynamoDB."""

    def __init__(
        self,
        table_name: str,
        region_name: str = "ap-south-1",
    ):
        self.table = boto3.resource(
            "dynamodb",
            region_name=region_name,
        ).Table(table_name)

    def save(
        self,
        incident_id: str,
        result: RemediationResult,
    ) -> None:
        """Persist a remediation execution result."""

        execution_id = f"{incident_id}:{result.action_id}"

        item = {
            "execution_id": execution_id,
            "incident_id": incident_id,
            "action": result.action,
            "action_id": result.action_id,
            "resource_id": result.resource_id,
            "status": result.status,
            "started_at": result.started_at.isoformat(),
            "completed_at": result.completed_at.isoformat(),
            "message": result.message,
        }

        if result.error is not None:
            item["error"] = result.error

        self.table.put_item(
            Item=item,
        )