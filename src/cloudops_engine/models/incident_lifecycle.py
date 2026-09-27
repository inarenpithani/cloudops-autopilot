from dataclasses import dataclass


VALID_TRANSITIONS = {
    "DETECTED": {"ACKNOWLEDGED"},
    "ACKNOWLEDGED": {"INVESTIGATING"},
    "INVESTIGATING": {"REMEDIATING"},
    "REMEDIATING": {"VERIFYING"},
    "VERIFYING": {"RESOLVED", "INVESTIGATING"},
    "RESOLVED": set(),
}


@dataclass
class IncidentLifecycle:
    """Manage valid state transitions for an incident."""

    incident_id: str
    state: str = "DETECTED"

    def transition_to(self, new_state: str) -> None:
        """Move the incident to a valid next state."""

        allowed_states = VALID_TRANSITIONS.get(self.state, set())

        if new_state not in allowed_states:
            raise ValueError(
                f"Invalid incident transition: "
                f"{self.state} -> {new_state}"
            )

        self.state = new_state