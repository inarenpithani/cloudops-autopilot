from datetime import datetime, timezone

from cloudops_engine.detection.detector import detect_high_cpu


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


def test_high_cpu_creates_incident():
    detection_result = detect_high_cpu(
        cpu_datapoints=create_datapoints([92, 94, 96]),
        resource="i-05e3bbde2a13509f7",
    )

    assert detection_result is not None
    assert detection_result.incident.incident_type == "HIGH_CPU"
    assert detection_result.incident.severity == "HIGH"
    assert detection_result.incident.resource == "i-05e3bbde2a13509f7"
    assert len(detection_result.evidence) == 3


def test_high_cpu_preserves_cloudwatch_timestamps():
    detection_result = detect_high_cpu(
        cpu_datapoints=create_datapoints([92, 94, 96]),
        resource="i-05e3bbde2a13509f7",
    )

    assert detection_result is not None

    assert detection_result.evidence[0].observed_at == datetime(
        2026,
        9,
        26,
        10,
        0,
        tzinfo=timezone.utc,
    )


def test_high_cpu_evidence_contains_actual_values():
    detection_result = detect_high_cpu(
        cpu_datapoints=create_datapoints([92, 94, 96]),
        resource="i-05e3bbde2a13509f7",
    )

    assert detection_result is not None

    assert [
        evidence.value
        for evidence in detection_result.evidence
    ] == ["92%", "94%", "96%"]


def test_normal_cpu_does_not_create_incident():
    detection_result = detect_high_cpu(
        cpu_datapoints=create_datapoints([70, 75, 80]),
        resource="i-05e3bbde2a13509f7",
    )

    assert detection_result is None


def test_non_consecutive_breaches_do_not_create_incident():
    detection_result = detect_high_cpu(
        cpu_datapoints=create_datapoints([92, 70, 95]),
        resource="i-05e3bbde2a13509f7",
    )

    assert detection_result is None


def test_insufficient_datapoints_do_not_create_incident():
    detection_result = detect_high_cpu(
        cpu_datapoints=create_datapoints([92, 94]),
        resource="i-05e3bbde2a13509f7",
    )

    assert detection_result is None


def test_cpu_at_threshold_does_not_create_incident():
    detection_result = detect_high_cpu(
        cpu_datapoints=create_datapoints([90.0, 90.0, 90.0]),
        resource="i-05e3bbde2a13509f7",
    )

    assert detection_result is None


def test_cpu_custom_threshold_creates_incident():
    detection_result = detect_high_cpu(
        cpu_datapoints=create_datapoints([81.0, 83.0, 85.0]),
        resource="i-05e3bbde2a13509f7",
        threshold=80.0,
    )

    assert detection_result is not None


def test_cpu_custom_breach_count():
    detection_result = detect_high_cpu(
        cpu_datapoints=create_datapoints([92.0, 94.0]),
        resource="i-05e3bbde2a13509f7",
        required_breaches=2,
    )

    assert detection_result is not None