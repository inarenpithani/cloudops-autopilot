from datetime import datetime, timezone

from cloudops_engine.aws.ec2 import EC2Client
from cloudops_engine.models.remediation_result import RemediationResult
from cloudops_engine.remediation.action import RemediationAction
from cloudops_engine.repositories.remediation_execution_repository import (
    RemediationExecutionRepository,
)
from cloudops_engine.repositories.remediation_idempotency_repository import (
    RemediationIdempotencyRepository,
)


def _persist_result(
    incident_id: str,
    result: RemediationResult,
    execution_repository: RemediationExecutionRepository,
) -> RemediationResult:
    """Persist a remediation execution result."""

    execution_repository.save(
        incident_id=incident_id,
        result=result,
    )

    return result


def execute_remediation(
    action: RemediationAction,
    incident_id: str,
    ec2_client: EC2Client,
    idempotency_repository: RemediationIdempotencyRepository,
    execution_repository: RemediationExecutionRepository,
) -> RemediationResult:
    """Execute an approved remediation action."""

    started_at = datetime.now(timezone.utc)

    if not action.action_id:
        completed_at = datetime.now(timezone.utc)

        result = RemediationResult(
            action=action.name,
            action_id=action.action_id,
            resource_id=action.resource_id,
            status="FAILED",
            started_at=started_at,
            completed_at=completed_at,
            message="Remediation action was not executed.",
            error="Remediation action ID cannot be empty.",
        )

        return _persist_result(
            incident_id=incident_id,
            result=result,
            execution_repository=execution_repository,
        )

    claimed = idempotency_repository.claim_action(
        incident_id=incident_id,
        action_id=action.action_id,
    )

    if not claimed:
        completed_at = datetime.now(timezone.utc)

        result = RemediationResult(
            action=action.name,
            action_id=action.action_id,
            resource_id=action.resource_id,
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

        return _persist_result(
            incident_id=incident_id,
            result=result,
            execution_repository=execution_repository,
        )

    try:
        if action.action_id == "EC2_REBOOT":
            ec2_client.reboot_instance(
                instance_id=action.resource_id,
            )
        else:
            idempotency_repository.release_action(
                incident_id=incident_id,
                action_id=action.action_id,
            )

            completed_at = datetime.now(timezone.utc)

            result = RemediationResult(
                action=action.name,
                action_id=action.action_id,
                resource_id=action.resource_id,
                status="FAILED",
                started_at=started_at,
                completed_at=completed_at,
                message="Remediation action was not executed.",
                error=(
                    f"Unsupported remediation action: "
                    f"{action.action_id}"
                ),
            )

            return _persist_result(
                incident_id=incident_id,
                result=result,
                execution_repository=execution_repository,
            )

    except Exception as exc:
        idempotency_repository.release_action(
            incident_id=incident_id,
            action_id=action.action_id,
        )

        completed_at = datetime.now(timezone.utc)

        result = RemediationResult(
            action=action.name,
            action_id=action.action_id,
            resource_id=action.resource_id,
            status="FAILED",
            started_at=started_at,
            completed_at=completed_at,
            message="Remediation action failed during AWS execution.",
            error=str(exc),
        )

        return _persist_result(
            incident_id=incident_id,
            result=result,
            execution_repository=execution_repository,
        )

    completed_at = datetime.now(timezone.utc)

    result = RemediationResult(
        action=action.name,
        action_id=action.action_id,
        resource_id=action.resource_id,
        status="SUCCESS",
        started_at=started_at,
        completed_at=completed_at,
        message="Remediation action executed successfully.",
        error=None,
    )

    return _persist_result(
        incident_id=incident_id,
        result=result,
        execution_repository=execution_repository,
    )