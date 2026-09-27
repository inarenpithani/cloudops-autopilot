from cloudops_engine.remediation.executor import execute_remediation


def test_failed_remediation_does_not_report_success():
    result = execute_remediation(
        action="",
        incident_id="INC-FAIL-001",
    )

    assert result.status == "FAILED"
    assert result.error == "Remediation action cannot be empty."