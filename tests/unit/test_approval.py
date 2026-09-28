from unittest.mock import patch

from cloudops_engine.remediation.action import RemediationAction
from cloudops_engine.remediation.approval import request_approval


def create_reboot_action(
    requires_approval: bool = True,
) -> RemediationAction:
    return RemediationAction(
        action_id="EC2_REBOOT",
        name="Reboot EC2 instance",
        description=(
            "Restart a running EC2 instance "
            "to recover from a controlled incident."
        ),
        risk_level="MEDIUM",
        resource_id="i-test-instance",
        requires_approval=requires_approval,
    )


@patch("builtins.input", return_value="yes")
def test_approval_is_granted_when_human_confirms(mock_input):
    action = create_reboot_action()

    result = request_approval(action)

    assert result is True

    mock_input.assert_called_once_with(
        "Approve this remediation action? (yes/no): "
    )


@patch("builtins.input", return_value="no")
def test_approval_is_denied_when_human_rejects(mock_input):
    action = create_reboot_action()

    result = request_approval(action)

    assert result is False

    mock_input.assert_called_once_with(
        "Approve this remediation action? (yes/no): "
    )


def test_approval_is_not_required_when_action_is_preapproved():
    action = create_reboot_action(
        requires_approval=False,
    )

    with patch("builtins.input") as mock_input:
        result = request_approval(action)

    assert result is True
    mock_input.assert_not_called()