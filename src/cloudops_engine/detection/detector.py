from datetime import datetime
from typing import Optional

from cloudops_engine.models.incident import Incident


def detect_high_cpu(
    cpu_datapoints: list[float],
    resource: str,
    threshold: float = 90.0,
    required_breaches: int = 3,
) -> Optional[Incident]:
    """Detect a persistent high CPU condition."""

    if len(cpu_datapoints) < required_breaches:
        return None

    recent_datapoints = cpu_datapoints[-required_breaches:]

    if not all(cpu > threshold for cpu in recent_datapoints):
        return None

    return Incident(
        incident_id="INC-001",
        incident_type="HIGH_CPU",
        severity="HIGH",
        resource=resource,
        detected_at=datetime.now(),
        status="DETECTED",
        description=(
            f"CPU remained above {threshold}% for "
            f"{required_breaches} consecutive datapoints."
        ),
    )