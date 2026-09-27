from datetime import datetime, timezone

from cloudops_engine.diagnosis.root_cause import diagnose_incident
from cloudops_engine.detection.detector import detect_high_cpu
from cloudops_engine.remediation.executor import execute_remediation
from cloudops_engine.remediation.guardrails import validate_action
from cloudops_engine.remediation.recommendation import recommend_action
from cloudops_engine.risk.assessment import assess_risk
from cloudops_engine.verification.health_check import verify_cpu_recovery


def create_datapoints(values: list[float]) -> list[dict]:
    return [
        {
            "value": value,
            "timestamp": datetime(
                2026,
                9,
                27,
                10,
                index,
                tzinfo=timezone.utc,
            ),
        }
        for index, value in enumerate(values)
    ]


def test_full_incident_lifecycle_to_resolution():
    detection_result = detect_high_cpu(
        cpu_datapoints=create_datapoints([92.0, 94.0, 96.0]),
        resource="i-test-instance",
    )

    assert detection_result is not None

    incident = detection_result.incident
    evidence = detection_result.evidence

    assert incident.status == "DETECTED"

    incident.transition_to("ACKNOWLEDGED")
    assert incident.status == "ACKNOWLEDGED"

    incident.transition_to("INVESTIGATING")
    assert incident.status == "INVESTIGATING"

    diagnosis = diagnose_incident(
        incident,
        evidence,
    )

    assert diagnosis.confidence > 0.0

    risk = assess_risk(incident)

    recommendation = recommend_action(
        incident,
        risk,
    )

    guardrail_result = validate_action(
        action=recommendation,
        risk=risk,
    )

    assert guardrail_result.allowed is True

    incident.transition_to("REMEDIATING")
    assert incident.status == "REMEDIATING"

    remediation_result = execute_remediation(
        action=recommendation,
        incident_id=incident.incident_id,
    )

    assert remediation_result.status == "SUCCESS"

    incident.transition_to("VERIFYING")
    assert incident.status == "VERIFYING"

    recovered = verify_cpu_recovery(60.0)

    assert recovered is True

    incident.transition_to("RESOLVED")

    assert incident.status == "RESOLVED"


def test_failed_verification_returns_to_investigation():
    detection_result = detect_high_cpu(
        cpu_datapoints=create_datapoints([92.0, 94.0, 96.0]),
        resource="i-test-instance-2",
    )

    assert detection_result is not None

    incident = detection_result.incident

    incident.transition_to("ACKNOWLEDGED")
    incident.transition_to("INVESTIGATING")
    incident.transition_to("REMEDIATING")
    incident.transition_to("VERIFYING")

    recovered = verify_cpu_recovery(95.0)

    assert recovered is False

    incident.transition_to("INVESTIGATING")

    assert incident.status == "INVESTIGATING"