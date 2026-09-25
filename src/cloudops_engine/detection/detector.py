from typing import Optional

from cloudops_engine.models.incident import Incident
from datetime import datetime


def detect_high_cpu(
    cpu_usage: float,
    threshold: float = 90.0,
) -> Optional[Incident]:
    if cpu_usage <= threshold:
        return None

    return Incident(
        incident_id="INC-001",
        incident_type="HIGH_CPU",
        severity="HIGH",
        resource="EC2-i-123456",
        detected_at=datetime.now(),
        status="DETECTED",
        description=f"CPU utilization reached {cpu_usage}%, exceeding the {threshold}% threshold.",
    )