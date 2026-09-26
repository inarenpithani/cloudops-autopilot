from datetime import datetime, timezone

from cloudops_engine.detection.detector import detect_high_cpu
from cloudops_engine.risk.assessment import assess_risk


def create_datapoints(values: list[float]) -> list[dict]:
    """Create deterministic CloudWatch-style datapoints for testing."""

    return [
        {
            "value": value,
            "timestamp": datetime(
                2026,
                9,
                26,
                10,
                index,
                tzinfo=timezone.utc,
            ),
        }
        for index, value in enumerate(values)
    ]


def test_high_cpu_high_severity_has_medium_risk():
    detection_result = detect_high_cpu(
        cpu_datapoints=create_datapoints([92, 94, 96]),
        resource="i-05e3bbde2a13509f7",
    )

    risk = assess_risk(detection_result.incident)

    assert risk == "MEDIUM"


def test_low_risk_for_other_incident():
    detection_result = detect_high_cpu(
        cpu_datapoints=create_datapoints([92, 94, 96]),
        resource="i-05e3bbde2a13509f7",
    )

    detection_result.incident.incident_type = "OTHER"

    risk = assess_risk(detection_result.incident)

    assert risk == "LOW"