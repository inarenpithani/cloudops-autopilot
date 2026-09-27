from datetime import datetime, timezone

from cloudops_engine.models.remediation_result import RemediationResult
from cloudops_engine.remediation.idempotency import IdempotencyRegistry


idempotency_registry = IdempotencyRegistry()


def execute_remediation(
    action: str,
    incident_id: str,
) -> RemediationResult:
    """
    Execute a remediation action with idempotency protection.

    This prototype does not modify AWS resources yet.
    """

    started_at = datetime.now(timezone.utc)

    if not action or not action.strip():
        completed_at = datetime.now(timezone.utc)

        return RemediationResult(
            action=action,
            status="FAILED",
            started_at=started_at,
            completed_at=completed_at,
            message="Remediation action was not executed.",
            error="Remediation action cannot be empty.",
        )

    if idempotency_registry.has_executed(
        incident_id=incident_id,
        action=action,
    ):
        completed_at = datetime.now(timezone.utc)

        return RemediationResult(
            action=action,
            status="SKIPPED",
            started_at=started_at,
            completed_at=completed_at,
            message=(
                "Remediation action was skipped because "
                "the same action was already executed "
                "for this incident."
            ),
            error=None,
        )

    idempotency_registry.mark_executed(
        incident_id=incident_id,
        action=action,
    )

    completed_at = datetime.now(timezone.utc)

    return RemediationResult(
        action=action,
        status="SUCCESS",
        started_at=started_at,
        completed_at=completed_at,
        message=(
            "Remediation action accepted for execution "
            "(simulation mode)."
        ),
        error=None,
    )