from abc import ABC, abstractmethod

from cloudops_engine.models.incident import Incident


class IncidentRepository(ABC):
    """Define persistence operations for incidents."""

    @abstractmethod
    def save(self, incident: Incident) -> None:
        """Persist an incident."""
        raise NotImplementedError

    @abstractmethod
    def get(self, incident_id: str) -> Incident | None:
        """Retrieve an incident by ID."""
        raise NotImplementedError

    @abstractmethod
    def update(self, incident: Incident) -> None:
        """Update an existing incident."""
        raise NotImplementedError