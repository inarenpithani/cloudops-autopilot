from dataclasses import dataclass


@dataclass
class GuardrailResult:
    """Represent the result of a remediation safety check."""

    allowed: bool
    reason: str


ALLOWED_ACTIONS = {
    "Monitor CPU utilization and collect additional diagnostic data.",
    "Collect additional metrics and investigate the top CPU-consuming processes.",
}


def validate_action(action: str, risk: str) -> GuardrailResult:
    """
    Validate whether a remediation action is allowed to proceed.

    The current implementation is intentionally restrictive.
    Real AWS-mutating actions will be introduced later.
    """

    if not action or not action.strip():
        return GuardrailResult(
            allowed=False,
            reason="Remediation action cannot be empty.",
        )

    if action not in ALLOWED_ACTIONS:
        return GuardrailResult(
            allowed=False,
            reason="Remediation action is not in the approved action allowlist.",
        )

    if risk not in {"LOW", "MEDIUM"}:
        return GuardrailResult(
            allowed=False,
            reason="Remediation risk level is not permitted.",
        )

    return GuardrailResult(
        allowed=True,
        reason="Remediation action passed safety guardrails.",
    )