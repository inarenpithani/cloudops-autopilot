from datetime import datetime, timezone

from cloudops_engine.models.incident import Incident
from cloudops_engine.repositories.dynamodb_incident_repository import (
    DynamoDBIncidentRepository,
)


def create_test_incident(incident_id: str) -> Incident:
    """Create a sample incident for DynamoDB testing."""

    return Incident(
        incident_id=incident_id,
        incident_type="HIGH_CPU",
        severity="HIGH",
        resource="i-test-instance",
        detected_at=datetime.now(timezone.utc),
        status="DETECTED",
        description="DynamoDB repository integration test.",
    )


def test_save_and_get_incident():
    """Verify that an incident can be saved and retrieved."""

    repository = DynamoDBIncidentRepository()

    incident = create_test_incident("TEST-DDB-001")

    repository.save(incident)

    retrieved_incident = repository.get(
        incident.incident_id
    )

    assert retrieved_incident is not None
    assert retrieved_incident.incident_id == incident.incident_id
    assert retrieved_incident.incident_type == incident.incident_type
    assert retrieved_incident.severity == incident.severity
    assert retrieved_incident.resource == incident.resource
    assert retrieved_incident.status == incident.status
    assert retrieved_incident.description == incident.description

    repository.table.delete_item(
        Key={"incident_id": incident.incident_id}
    )


def test_update_incident():
    """Verify that an existing incident can be updated."""

    repository = DynamoDBIncidentRepository()

    incident = create_test_incident("TEST-DDB-002")

    repository.save(incident)

    incident.status = "RESOLVED"
    incident.description = "Incident resolved successfully."

    repository.update(incident)

    retrieved_incident = repository.get(
        incident.incident_id
    )

    assert retrieved_incident is not None
    assert retrieved_incident.status == "RESOLVED"
    assert retrieved_incident.description == (
        "Incident resolved successfully."
    )

    repository.table.delete_item(
        Key={"incident_id": incident.incident_id}
    )
    
def test_duplicate_incident_is_rejected():
    """Verify that duplicate incident IDs are rejected."""

    repository = DynamoDBIncidentRepository()

    incident = create_test_incident("TEST-DDB-003")

    repository.save(incident)

    try:
        repository.save(incident)
        assert False, "Expected duplicate incident to be rejected."
    except ValueError as error:
        assert str(error) == (
            "Incident already exists: TEST-DDB-003"
        )

    repository.table.delete_item(
        Key={"incident_id": incident.incident_id}
    )
    
def test_update_missing_incident_is_rejected():
    """Verify that updating a missing incident is rejected."""

    repository = DynamoDBIncidentRepository()

    incident = create_test_incident("TEST-DDB-004")

    try:
        repository.update(incident)
        assert False, "Expected missing incident update to be rejected."
    except ValueError as error:
        assert str(error) == (
            "Incident not found: TEST-DDB-004"
        )