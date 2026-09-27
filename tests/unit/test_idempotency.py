from cloudops_engine.remediation.executor import execute_remediation


def test_same_action_for_same_incident_is_skipped():
    action = "Collect additional metrics"
    incident_id = "INC-TEST-001"

    first_result = execute_remediation(
        action=action,
        incident_id=incident_id,
    )

    second_result = execute_remediation(
        action=action,
        incident_id=incident_id,
    )

    assert first_result.status == "SUCCESS"
    assert second_result.status == "SKIPPED"


def test_same_action_for_different_incidents_is_allowed():
    action = "Collect additional metrics"

    first_result = execute_remediation(
        action=action,
        incident_id="INC-TEST-002",
    )

    second_result = execute_remediation(
        action=action,
        incident_id="INC-TEST-003",
    )

    assert first_result.status == "SUCCESS"
    assert second_result.status == "SUCCESS"


def test_empty_action_fails():
    result = execute_remediation(
        action="",
        incident_id="INC-TEST-004",
    )

    assert result.status == "FAILED"
    assert result.error == "Remediation action cannot be empty."