from dataclasses import dataclass

from cloudops_engine.remediation.action import RemediationAction


@dataclass
class GuardrailResult:
    """Represent the result of a remediation safety check."""

    allowed: bool
    reason: str


ALLOWED_ACTIONS = {
    "EC2_REBOOT",
}


ALLOWED_RISK_LEVELS = {
    "LOW",
    "MEDIUM",
}


def validate_action(
    action: RemediationAction,
) -> GuardrailResult:
    """Validate whether a remediation action is allowed to proceed."""

    if not action.action_id:
        return GuardrailResult(
            allowed=False,
            reason="Remediation action ID cannot be empty.",
        )

    if action.action_id not in ALLOWED_ACTIONS:
        return GuardrailResult(
            allowed=False,
            reason=(
                "Remediation action is not in the "
                "approved action allowlist."
            ),
        )

    if action.risk_level not in ALLOWED_RISK_LEVELS:
        return GuardrailResult(
            allowed=False,
            reason="Remediation risk level is not permitted.",
        )

    if not action.resource_id:
        return GuardrailResult(
            allowed=False,
            reason="Remediation resource ID cannot be empty.",
        )

    return GuardrailResult(
        allowed=True,
        reason="Remediation action passed safety guardrails.",
    )