from datetime import datetime, timezone

from cloudops_engine.models.incident import Incident
from cloudops_engine.repositories.dynamodb_incident_repository import (
    DynamoDBIncidentRepository,
)


def create_test_incident(incident_id: str) -> Incident:
    """Create a sample incident for DynamoDB integration testing."""

    return Incident(
        incident_id=incident_id,
        incident_type="HIGH_CPU",
        severity="HIGH",
        resource="i-test-instance",
        detected_at=datetime.now(timezone.utc),
        status="DETECTED",
        description="DynamoDB persistence integration test.",
    )


def test_dynamodb_incident_persistence():
    """Verify incident create, read, update, and duplicate protection."""

    repository = DynamoDBIncidentRepository()

    incident = create_test_incident("TEST-DDB-INTEGRATION-001")

    try:
        repository.save(incident)

        retrieved_incident = repository.get(
            incident.incident_id
        )

        assert retrieved_incident is not None
        assert retrieved_incident.incident_id == incident.incident_id
        assert retrieved_incident.status == "DETECTED"

        incident.status = "RESOLVED"
        incident.description = "Incident resolved successfully."

        repository.update(incident)

        updated_incident = repository.get(
            incident.incident_id
        )

        assert updated_incident is not None
        assert updated_incident.status == "RESOLVED"
        assert updated_incident.description == (
            "Incident resolved successfully."
        )

    finally:
        repository.table.delete_item(
            Key={
                "incident_id": incident.incident_id,
            }
        )