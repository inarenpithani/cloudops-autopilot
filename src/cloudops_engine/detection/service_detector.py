from datetime import datetime
from typing import Optional

from cloudops_engine.models.incident import Incident


def detect_unhealthy_service(
    health_statuses: list[bool],
    resource: str,
    required_breaches: int = 3,
) -> Optional[Incident]:
    """Detect a persistent unhealthy service condition."""

    if len(health_statuses) < required_breaches:
        return None

    recent_statuses = health_statuses[-required_breaches:]

    if any(recent_statuses):
        return None

    return Incident(
        incident_id="INC-003",
        incident_type="SERVICE_UNHEALTHY",
        severity="HIGH",
        resource=resource,
        detected_at=datetime.now(),
        status="DETECTED",
        description=(
            f"Service remained unhealthy for "
            f"{required_breaches} consecutive health checks."
        ),
    )