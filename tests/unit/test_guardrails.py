from cloudops_engine.remediation.action import RemediationAction
from cloudops_engine.remediation.guardrails import validate_action


def create_reboot_action(
    risk_level: str = "MEDIUM",
    resource_id: str = "i-test-instance",
) -> RemediationAction:
    return RemediationAction(
        action_id="EC2_REBOOT",
        name="Reboot EC2 instance",
        description=(
            "Restart a running EC2 instance "
            "to recover from a controlled incident."
        ),
        risk_level=risk_level,
        resource_id=resource_id,
    )


def test_allowed_medium_risk_reboot_action():
    action = create_reboot_action()

    result = validate_action(action)

    assert result.allowed is True
    assert result.reason == (
        "Remediation action passed safety guardrails."
    )


def test_unknown_action_is_blocked():
    action = RemediationAction(
        action_id="EC2_TERMINATE",
        name="Terminate EC2 instance",
        description="Terminate an EC2 instance.",
        risk_level="HIGH",
        resource_id="i-test-instance",
    )

    result = validate_action(action)

    assert result.allowed is False
    assert result.reason == (
        "Remediation action is not in the "
        "approved action allowlist."
    )


def test_high_risk_action_is_blocked():
    action = create_reboot_action(
        risk_level="HIGH",
    )

    result = validate_action(action)

    assert result.allowed is False
    assert result.reason == (
        "Remediation risk level is not permitted."
    )


def test_empty_action_id_is_blocked():
    action = RemediationAction(
        action_id="",
        name="Invalid action",
        description="Invalid remediation action.",
        risk_level="MEDIUM",
        resource_id="i-test-instance",
    )

    result = validate_action(action)

    assert result.allowed is False
    assert result.reason == (
        "Remediation action ID cannot be empty."
    )


def test_empty_resource_id_is_blocked():
    action = create_reboot_action(
        resource_id="",
    )

    result = validate_action(action)

    assert result.allowed is False
    assert result.reason == (
        "Remediation resource ID cannot be empty."
    )