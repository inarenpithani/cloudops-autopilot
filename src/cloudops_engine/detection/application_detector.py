from datetime import datetime
from typing import Optional

from cloudops_engine.models.incident import Incident


def detect_application_5xx(
    error_rates: list[float],
    resource: str,
    threshold: float = 5.0,
    required_breaches: int = 3,
) -> Optional[Incident]:
    """Detect a persistent application 5xx error-rate condition."""

    if len(error_rates) < required_breaches:
        return None

    recent_rates = error_rates[-required_breaches:]

    if not all(rate > threshold for rate in recent_rates):
        return None

    return Incident(
        incident_id="INC-002",
        incident_type="APPLICATION_5XX",
        severity="HIGH",
        resource=resource,
        detected_at=datetime.now(),
        status="DETECTED",
        description=(
            f"Application 5xx error rate remained above "
            f"{threshold}% for {required_breaches} consecutive datapoints."
        ),
    )