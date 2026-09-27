import pytest

from cloudops_engine.models.incident_lifecycle import IncidentLifecycle


def test_incident_starts_in_detected_state():
    lifecycle = IncidentLifecycle(
        incident_id="INC-TEST-001",
    )

    assert lifecycle.state == "DETECTED"


def test_valid_incident_lifecycle():
    lifecycle = IncidentLifecycle(
        incident_id="INC-TEST-002",
    )

    lifecycle.transition_to("ACKNOWLEDGED")
    assert lifecycle.state == "ACKNOWLEDGED"

    lifecycle.transition_to("INVESTIGATING")
    assert lifecycle.state == "INVESTIGATING"

    lifecycle.transition_to("REMEDIATING")
    assert lifecycle.state == "REMEDIATING"

    lifecycle.transition_to("VERIFYING")
    assert lifecycle.state == "VERIFYING"

    lifecycle.transition_to("RESOLVED")
    assert lifecycle.state == "RESOLVED"


def test_verification_failure_can_return_to_investigating():
    lifecycle = IncidentLifecycle(
        incident_id="INC-TEST-003",
    )

    lifecycle.transition_to("ACKNOWLEDGED")
    lifecycle.transition_to("INVESTIGATING")
    lifecycle.transition_to("REMEDIATING")
    lifecycle.transition_to("VERIFYING")

    lifecycle.transition_to("INVESTIGATING")

    assert lifecycle.state == "INVESTIGATING"


def test_invalid_transition_is_rejected():
    lifecycle = IncidentLifecycle(
        incident_id="INC-TEST-004",
    )

    with pytest.raises(ValueError):
        lifecycle.transition_to("RESOLVED")


def test_resolved_incident_cannot_transition():
    lifecycle = IncidentLifecycle(
        incident_id="INC-TEST-005",
    )

    lifecycle.transition_to("ACKNOWLEDGED")
    lifecycle.transition_to("INVESTIGATING")
    lifecycle.transition_to("REMEDIATING")
    lifecycle.transition_to("VERIFYING")
    lifecycle.transition_to("RESOLVED")

    with pytest.raises(ValueError):
        lifecycle.transition_to("REMEDIATING")