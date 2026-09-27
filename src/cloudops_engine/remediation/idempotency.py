from dataclasses import dataclass


@dataclass
class ActionExecution:
    """Track whether a remediation action has already been executed."""

    incident_id: str
    action: str


class IdempotencyRegistry:
    """Track remediation actions that have already been executed."""

    def __init__(self):
        self._executed_actions: set[str] = set()

    def build_key(self, incident_id: str, action: str) -> str:
        """Build a unique key for an incident and remediation action."""

        return f"{incident_id}:{action}"

    def has_executed(self, incident_id: str, action: str) -> bool:
        """Return True when the action was already executed."""

        key = self.build_key(
            incident_id=incident_id,
            action=action,
        )

        return key in self._executed_actions

    def mark_executed(self, incident_id: str, action: str) -> None:
        """Mark a remediation action as executed."""

        key = self.build_key(
            incident_id=incident_id,
            action=action,
        )

        self._executed_actions.add(key)