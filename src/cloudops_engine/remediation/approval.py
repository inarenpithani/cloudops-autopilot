from cloudops_engine.remediation.action import RemediationAction


def request_approval(action: RemediationAction) -> bool:
    """Request explicit human approval for a remediation action."""

    print(f"Remediation action: {action.name}")
    print(f"Action ID: {action.action_id}")
    print(f"Risk level: {action.risk_level}")
    print(f"Target resource: {action.resource_id}")
    print(f"Description: {action.description}")

    if not action.requires_approval:
        return True

    response = input(
        "Approve this remediation action? (yes/no): "
    ).strip().lower()

    return response == "yes"