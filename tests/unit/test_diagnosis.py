from datetime import datetime, timezone

from cloudops_engine.detection.detector import detect_high_cpu
from cloudops_engine.diagnosis.root_cause import diagnose_incident


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


def test_high_cpu_diagnosis():
    detection_result = detect_high_cpu(
        cpu_datapoints=create_datapoints([92, 94, 96]),
        resource="i-05e3bbde2a13509f7",
    )

    diagnosis = diagnose_incident(
        detection_result.incident,
        detection_result.evidence,
    )

    assert diagnosis.probable_cause == (
        "Sustained high CPU utilization on the affected compute instance."
    )
    assert diagnosis.confidence == 0.85
    assert diagnosis.evidence == ["92%", "94%", "96%"]
    assert "persistent CPU utilization" in diagnosis.explanation


def test_unknown_incident_diagnosis():
    detection_result = detect_high_cpu(
        cpu_datapoints=create_datapoints([92, 94, 96]),
        resource="i-05e3bbde2a13509f7",
    )

    detection_result.incident.incident_type = "UNKNOWN"

    diagnosis = diagnose_incident(
        detection_result.incident,
        detection_result.evidence,
    )

    assert diagnosis.probable_cause == "Unknown"
    assert diagnosis.confidence == 0.0
    assert diagnosis.evidence == []


def test_high_cpu_diagnosis_uses_actual_evidence():
    detection_result = detect_high_cpu(
        cpu_datapoints=create_datapoints([91, 93, 97]),
        resource="i-05e3bbde2a13509f7",
    )

    diagnosis = diagnose_incident(
        detection_result.incident,
        detection_result.evidence,
    )

    assert diagnosis.evidence == ["91%", "93%", "97%"]

def test_high_cpu_diagnosis_with_two_evidence_points():
    detection_result = detect_high_cpu(
        cpu_datapoints=create_datapoints([92, 94]),
        resource="i-05e3bbde2a13509f7",
        required_breaches=2,
    )

    diagnosis = diagnose_incident(
        detection_result.incident,
        detection_result.evidence,
    )

    assert diagnosis.confidence == 0.70
    assert diagnosis.evidence == ["92%", "94%"]


def test_high_cpu_diagnosis_with_one_evidence_point():
    detection_result = detect_high_cpu(
        cpu_datapoints=create_datapoints([92]),
        resource="i-05e3bbde2a13509f7",
        required_breaches=1,
    )

    diagnosis = diagnose_incident(
        detection_result.incident,
        detection_result.evidence,
    )

    assert diagnosis.confidence == 0.50
    assert diagnosis.evidence == ["92%"]

def test_high_cpu_diagnosis_increases_confidence_for_very_strong_signal():
    detection_result = detect_high_cpu(
        cpu_datapoints=create_datapoints([97, 98, 99]),
        resource="i-05e3bbde2a13509f7",
    )

    diagnosis = diagnose_incident(
        detection_result.incident,
        detection_result.evidence,
    )

    assert diagnosis.confidence == 0.90
    assert "Very strong" in diagnosis.explanation


def test_high_cpu_diagnosis_keeps_base_confidence_for_strong_signal():
    detection_result = detect_high_cpu(
        cpu_datapoints=create_datapoints([92, 94, 96]),
        resource="i-05e3bbde2a13509f7",
    )

    diagnosis = diagnose_incident(
        detection_result.incident,
        detection_result.evidence,
    )

    assert diagnosis.confidence == 0.85
    assert "Strong" in diagnosis.explanation

def test_unknown_incident_returns_zero_confidence():
    detection_result = detect_high_cpu(
        cpu_datapoints=create_datapoints([92, 94, 96]),
        resource="i-05e3bbde2a13509f7",
    )

    detection_result.incident.incident_type = "UNKNOWN"

    diagnosis = diagnose_incident(
        detection_result.incident,
        detection_result.evidence,
    )

    assert diagnosis.probable_cause == "Unknown"
    assert diagnosis.confidence == 0.0
    assert diagnosis.evidence == []


def test_high_cpu_without_evidence_returns_zero_confidence():
    detection_result = detect_high_cpu(
        cpu_datapoints=create_datapoints([92, 94, 96]),
        resource="i-05e3bbde2a13509f7",
    )

    diagnosis = diagnose_incident(
        detection_result.incident,
        [],
    )

    assert diagnosis.confidence == 0.0
    assert diagnosis.evidence == []
    assert "Insufficient evidence" in diagnosis.explanation


def test_high_cpu_diagnosis_with_non_cpu_evidence_returns_zero_confidence():
    from datetime import datetime, timezone

    from cloudops_engine.models.evidence import Evidence

    non_cpu_evidence = [
        Evidence(
            source="CloudWatch",
            signal="NetworkIn",
            value="1000",
            observed_at=datetime(
                2026,
                9,
                26,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            description="Network traffic observation.",
        )
    ]

    detection_result = detect_high_cpu(
        cpu_datapoints=create_datapoints([92, 94, 96]),
        resource="i-05e3bbde2a13509f7",
    )

    diagnosis = diagnose_incident(
        detection_result.incident,
        non_cpu_evidence,
    )

    assert diagnosis.probable_cause == "Unknown"
    assert diagnosis.confidence == 0.0
    assert diagnosis.evidence == []
    assert "Insufficient evidence" in diagnosis.explanation