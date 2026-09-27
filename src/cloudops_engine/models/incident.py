from dataclasses import dataclass
from datetime import datetime


@dataclass
class Incident:
    incident_id: str
    incident_type: str
    severity: str
    resource: str
    detected_at: datetime
    status: str
    description: str

    def transition_to(self, new_state: str) -> None:
        """Transition the incident to a valid lifecycle state."""

        from cloudops_engine.models.incident_lifecycle import (
            IncidentLifecycle,
        )

        lifecycle = IncidentLifecycle(
            incident_id=self.incident_id,
            state=self.status,
        )

        lifecycle.transition_to(new_state)

        self.status = lifecycle.state