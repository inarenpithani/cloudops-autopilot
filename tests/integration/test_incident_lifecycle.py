from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from cloudops_engine.diagnosis.root_cause import diagnose_incident
from cloudops_engine.detection.detector import detect_high_cpu
from cloudops_engine.remediation.action import RemediationAction
from cloudops_engine.remediation.approval import request_approval
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

    assert recommendation

    remediation_action = RemediationAction(
        action_id="EC2_REBOOT",
        name="Reboot EC2 instance",
        description=(
            "Restart a running EC2 instance "
            "to recover from a controlled incident."
        ),
        risk_level="MEDIUM",
        resource_id="i-test-instance",
    )

    guardrail_result = validate_action(
        remediation_action,
    )

    assert guardrail_result.allowed is True

    with patch(
        "cloudops_engine.remediation.approval.input",
        return_value="yes",
    ) as mock_input:
        approved = request_approval(
            remediation_action,
        )

    assert approved is True

    mock_input.assert_called_once_with(
        "Approve this remediation action? (yes/no): "
    )

    incident.transition_to("REMEDIATING")
    assert incident.status == "REMEDIATING"

    ec2_client = MagicMock()
    idempotency_repository = MagicMock()
    execution_repository = MagicMock()

    idempotency_repository.claim_action.return_value = True

    remediation_result = execute_remediation(
        action=remediation_action,
        incident_id=incident.incident_id,
        ec2_client=ec2_client,
        idempotency_repository=idempotency_repository,
        execution_repository=execution_repository,
    )

    assert remediation_result.status == "SUCCESS"

    ec2_client.reboot_instance.assert_called_once_with(
        instance_id="i-test-instance",
    )

    idempotency_repository.claim_action.assert_called_once_with(
        incident_id=incident.incident_id,
        action_id="EC2_REBOOT",
    )

    idempotency_repository.release_action.assert_not_called()

    execution_repository.save.assert_called_once_with(
        incident_id=incident.incident_id,
        result=remediation_result,
    )

    incident.transition_to("VERIFYING")
    assert incident.status == "VERIFYING"

    recovered = verify_cpu_recovery(60.0)

    assert recovered is True

    incident.transition_to("RESOLVED")

    assert incident.status == "RESOLVED"


def test_remediation_is_not_executed_when_human_rejects():
    remediation_action = RemediationAction(
        action_id="EC2_REBOOT",
        name="Reboot EC2 instance",
        description=(
            "Restart a running EC2 instance "
            "to recover from a controlled incident."
        ),
        risk_level="MEDIUM",
        resource_id="i-test-instance",
    )

    ec2_client = MagicMock()

    with patch(
        "cloudops_engine.remediation.approval.input",
        return_value="no",
    ):
        approved = request_approval(
            remediation_action,
        )

    assert approved is False

    ec2_client.reboot_instance.assert_not_called()


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