from datetime import datetime, timezone

import boto3

from cloudops_engine.models.incident import Incident
from cloudops_engine.repositories.incident_repository import IncidentRepository


class DynamoDBIncidentRepository(IncidentRepository):
    """Persist incidents in Amazon DynamoDB."""

    def __init__(
        self,
        table_name: str = "cloudops-autopilot-incidents",
        region_name: str = "ap-south-1",
    ):
        self.dynamodb = boto3.resource(
            "dynamodb",
            region_name=region_name,
        )

        self.table = self.dynamodb.Table(table_name)

    def save(self, incident: Incident) -> None:
        """Save a new incident to DynamoDB without allowing duplicates."""

        try:
            self.table.put_item(
                Item=self._serialize(incident),
                ConditionExpression="attribute_not_exists(incident_id)",
            )
        except self.table.meta.client.exceptions.ConditionalCheckFailedException:
            raise ValueError(
                f"Incident already exists: {incident.incident_id}"
            )

    def get(self, incident_id: str) -> Incident | None:
        """Retrieve an incident from DynamoDB."""

        response = self.table.get_item(
            Key={
                "incident_id": incident_id,
            }
        )

        item = response.get("Item")

        if item is None:
            return None

        return self._deserialize(item)

    def update(self, incident: Incident) -> None:
        """Update an existing incident in DynamoDB."""

        try:
            self.table.put_item(
                Item=self._serialize(incident),
                ConditionExpression="attribute_exists(incident_id)",
            )

        except self.table.meta.client.exceptions.ConditionalCheckFailedException:
            raise ValueError(
                f"Incident not found: {incident.incident_id}"
            )

    @staticmethod
    def _serialize(incident: Incident) -> dict:
        """Convert an Incident object into a DynamoDB item."""

        detected_at = incident.detected_at

        if detected_at.tzinfo is None:
            detected_at = detected_at.replace(
                tzinfo=timezone.utc
            )

        return {
            "incident_id": incident.incident_id,
            "incident_type": incident.incident_type,
            "severity": incident.severity,
            "resource": incident.resource,
            "detected_at": detected_at.isoformat(),
            "status": incident.status,
            "description": incident.description,
        }

    @staticmethod
    def _deserialize(item: dict) -> Incident:
        """Convert a DynamoDB item back into an Incident object."""

        detected_at = datetime.fromisoformat(
            item["detected_at"]
        )

        return Incident(
            incident_id=item["incident_id"],
            incident_type=item["incident_type"],
            severity=item["severity"],
            resource=item["resource"],
            detected_at=detected_at,
            status=item["status"],
            description=item["description"],
        )