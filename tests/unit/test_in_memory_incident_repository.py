from datetime import datetime, timezone

import pytest

from cloudops_engine.models.incident import Incident
from cloudops_engine.repositories.in_memory_incident_repository import (
    InMemoryIncidentRepository,
)


def create_incident(
    incident_id: str = "INC-TEST-001",
) -> Incident:
    return Incident(
        incident_id=incident_id,
        incident_type="HIGH_CPU",
        severity="HIGH",
        resource="i-test-instance",
        detected_at=datetime.now(timezone.utc),
        status="DETECTED",
        description="Test high CPU incident.",
    )


def test_save_and_get_incident():
    repository = InMemoryIncidentRepository()
    incident = create_incident()

    repository.save(incident)

    stored_incident = repository.get(
        incident_id="INC-TEST-001",
    )

    assert stored_incident is incident
    assert stored_incident.incident_id == "INC-TEST-001"


def test_update_incident():
    repository = InMemoryIncidentRepository()
    incident = create_incident()

    repository.save(incident)

    incident.transition_to("ACKNOWLEDGED")

    repository.update(incident)

    stored_incident = repository.get(
        incident_id="INC-TEST-001",
    )

    assert stored_incident is not None
    assert stored_incident.status == "ACKNOWLEDGED"


def test_duplicate_incident_is_rejected():
    repository = InMemoryIncidentRepository()

    first_incident = create_incident()
    second_incident = create_incident()

    repository.save(first_incident)

    with pytest.raises(ValueError):
        repository.save(second_incident)


def test_update_missing_incident_is_rejected():
    repository = InMemoryIncidentRepository()
    incident = create_incident()

    with pytest.raises(ValueError):
        repository.update(incident)


def test_missing_incident_returns_none():
    repository = InMemoryIncidentRepository()

    result = repository.get(
        incident_id="INC-NOT-FOUND",
    )

    assert result is None