from datetime import datetime, timezone

from cloudops_engine.detection.detector import detect_high_cpu
from cloudops_engine.remediation.recommendation import recommend_action


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


def test_medium_risk_high_cpu_recommendation():
    detection_result = detect_high_cpu(
        cpu_datapoints=create_datapoints([92, 94, 96]),
        resource="i-05e3bbde2a13509f7",
    )

    recommendation = recommend_action(
        detection_result.incident,
        "MEDIUM",
    )

    assert recommendation == (
        "Collect additional metrics and investigate "
        "the top CPU-consuming processes."
    )


def test_low_risk_high_cpu_recommendation():
    detection_result = detect_high_cpu(
        cpu_datapoints=create_datapoints([92, 94, 96]),
        resource="i-05e3bbde2a13509f7",
    )

    recommendation = recommend_action(
        detection_result.incident,
        "LOW",
    )

    assert recommendation == (
        "Monitor CPU utilization and collect "
        "additional diagnostic data."
    )