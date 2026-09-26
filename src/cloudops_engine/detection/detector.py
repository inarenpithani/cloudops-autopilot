from datetime import datetime
from typing import Optional

from cloudops_engine.models.detection_result import DetectionResult
from cloudops_engine.models.evidence import Evidence
from cloudops_engine.models.incident import Incident


def detect_high_cpu(
    cpu_datapoints: list[dict],
    resource: str,
    threshold: float = 90.0,
    required_breaches: int = 3,
) -> Optional[DetectionResult]:
    """Detect a persistent high CPU condition."""

    if len(cpu_datapoints) < required_breaches:
        return None

    recent_datapoints = cpu_datapoints[-required_breaches:]

    if not all(
        datapoint["value"] > threshold
        for datapoint in recent_datapoints
    ):
        return None

    incident = Incident(
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

    evidence = [
        Evidence(
            source="CloudWatch",
            signal="CPUUtilization",
            value=f"{datapoint['value']}%",
            observed_at=datapoint["timestamp"],
            description=(
                f"CPU utilization exceeded the configured "
                f"threshold of {threshold}%."
            ),
        )
        for datapoint in recent_datapoints
    ]

    return DetectionResult(
        incident=incident,
        evidence=evidence,
    )