from dataclasses import dataclass
from datetime import datetime


@dataclass
class RemediationResult:
    """Represent the outcome of a remediation action."""

    action: str
    action_id: str
    resource_id: str
    status: str
    started_at: datetime
    completed_at: datetime
    message: str
    error: str | None = None