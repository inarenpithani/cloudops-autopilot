from cloudops_engine.models.incident import Incident
from cloudops_engine.repositories.incident_repository import IncidentRepository


class InMemoryIncidentRepository(IncidentRepository):
    """Store incidents in memory for development and testing."""

    def __init__(self):
        self._incidents: dict[str, Incident] = {}

    def save(self, incident: Incident) -> None:
        """Save a new incident."""

        if incident.incident_id in self._incidents:
            raise ValueError(
                f"Incident already exists: {incident.incident_id}"
            )

        self._incidents[incident.incident_id] = incident

    def get(self, incident_id: str) -> Incident | None:
        """Retrieve an incident by ID."""

        return self._incidents.get(incident_id)

    def update(self, incident: Incident) -> None:
        """Update an existing incident."""

        if incident.incident_id not in self._incidents:
            raise ValueError(
                f"Incident not found: {incident.incident_id}"
            )

        self._incidents[incident.incident_id] = incident