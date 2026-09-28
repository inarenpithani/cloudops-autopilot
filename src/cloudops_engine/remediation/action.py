from dataclasses import dataclass


@dataclass(frozen=True)
class RemediationAction:
    """Represent an approved remediation action."""

    action_id: str
    name: str
    description: str
    risk_level: str
    resource_id: str
    requires_approval: bool = True