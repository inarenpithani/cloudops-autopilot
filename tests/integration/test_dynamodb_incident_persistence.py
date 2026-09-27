from datetime import datetime, timezone

from cloudops_engine.models.incident import Incident
from cloudops_engine.repositories.dynamodb_incident_repository import (
    DynamoDBIncidentRepository,
)


def test_incident_lifecycle_is_persisted():
    """Verify that incident lifecycle state changes persist in DynamoDB."""

    repository = DynamoDBIncidentRepository()

    incident = Incident(
        incident_id="TEST-LIFECYCLE-001",
        incident_type="HIGH_CPU",
        severity="HIGH",
        resource="i-test-instance",
        detected_at=datetime.now(timezone.utc),
        status="DETECTED",
        description="DynamoDB lifecycle persistence integration test.",
    )

    try:
        # Persist initial incident.
        repository.save(incident)

        stored_incident = repository.get(
            incident.incident_id
        )

        assert stored_incident is not None
        assert stored_incident.status == "DETECTED"

        # Move to ACKNOWLEDGED.
        incident.transition_to("ACKNOWLEDGED")
        repository.update(incident)

        stored_incident = repository.get(
            incident.incident_id
        )

        assert stored_incident is not None
        assert stored_incident.status == "ACKNOWLEDGED"

        # Move to INVESTIGATING.
        incident.transition_to("INVESTIGATING")
        repository.update(incident)

        stored_incident = repository.get(
            incident.incident_id
        )

        assert stored_incident is not None
        assert stored_incident.status == "INVESTIGATING"

        # Move to REMEDIATING.
        incident.transition_to("REMEDIATING")
        repository.update(incident)

        stored_incident = repository.get(
            incident.incident_id
        )

        assert stored_incident is not None
        assert stored_incident.status == "REMEDIATING"

        # Move to VERIFYING.
        incident.transition_to("VERIFYING")
        repository.update(incident)

        stored_incident = repository.get(
            incident.incident_id
        )

        assert stored_incident is not None
        assert stored_incident.status == "VERIFYING"

        # Move to RESOLVED.
        incident.transition_to("RESOLVED")
        repository.update(incident)

        stored_incident = repository.get(
            incident.incident_id
        )

        assert stored_incident is not None
        assert stored_incident.status == "RESOLVED"

    finally:
        # Remove the test record from DynamoDB.
        repository.table.delete_item(
            Key={
                "incident_id": incident.incident_id,
            }
        )