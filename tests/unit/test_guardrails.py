import pytest

from cloudops_engine.remediation.guardrails import validate_action


def test_allowed_low_risk_action():
    action = (
        "Monitor CPU utilization and collect "
        "additional diagnostic data."
    )

    result = validate_action(
        action=action,
        risk="LOW",
    )

    assert result.allowed is True
    assert result.reason == (
        "Remediation action passed safety guardrails."
    )


def test_allowed_medium_risk_action():
    action = (
        "Collect additional metrics and investigate "
        "the top CPU-consuming processes."
    )

    result = validate_action(
        action=action,
        risk="MEDIUM",
    )

    assert result.allowed is True


def test_unknown_action_is_blocked():
    result = validate_action(
        action="Terminate the EC2 instance.",
        risk="LOW",
    )

    assert result.allowed is False
    assert result.reason == (
        "Remediation action is not in the approved action allowlist."
    )


def test_high_risk_action_is_blocked():
    action = (
        "Collect additional metrics and investigate "
        "the top CPU-consuming processes."
    )

    result = validate_action(
        action=action,
        risk="HIGH",
    )

    assert result.allowed is False
    assert result.reason == (
        "Remediation risk level is not permitted."
    )


def test_empty_action_is_blocked():
    result = validate_action(
        action="",
        risk="LOW",
    )

    assert result.allowed is False
    assert result.reason == (
        "Remediation action cannot be empty."
    )