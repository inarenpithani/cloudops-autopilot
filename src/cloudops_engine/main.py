from cloudops_engine.aws.cloudwatch import CloudWatchClient
from cloudops_engine.aws.ec2 import EC2Client
from cloudops_engine.aws.sns import SNSClient
from cloudops_engine.config import (
    AWS_REGION,
    EC2_INSTANCE_ID,
    CPU_THRESHOLD,
    SNS_TOPIC_ARN,
)
from cloudops_engine.diagnosis.root_cause import diagnose_incident
from cloudops_engine.notifications.policy import should_notify
from cloudops_engine.notifications.service import NotificationService
from cloudops_engine.remediation.action import RemediationAction
from cloudops_engine.remediation.approval import request_approval
from cloudops_engine.remediation.executor import execute_remediation
from cloudops_engine.remediation.guardrails import validate_action
from cloudops_engine.remediation.recommendation import recommend_action
from cloudops_engine.repositories.dynamodb_incident_repository import (
    DynamoDBIncidentRepository,
)
from cloudops_engine.repositories.notification_idempotency_repository import (
    NotificationIdempotencyRepository,
)
from cloudops_engine.repositories.remediation_execution_repository import (
    RemediationExecutionRepository,
)
from cloudops_engine.repositories.remediation_idempotency_repository import (
    RemediationIdempotencyRepository,
)
from cloudops_engine.risk.assessment import assess_risk
from cloudops_engine.services.monitoring import MonitoringService
from cloudops_engine.verification.verification_service import (
    VerificationService,
)


def main():
    print("CloudOps Autopilot is starting...\n")

    if not EC2_INSTANCE_ID:
        print("EC2_INSTANCE_ID is not configured.")
        return

    cloudwatch_client = CloudWatchClient(
        region_name=AWS_REGION,
    )

    ec2_client = EC2Client(
        region_name=AWS_REGION,
    )

    remediation_idempotency_repository = (
        RemediationIdempotencyRepository(
            table_name="cloudops-autopilot-remediation-idempotency",
            region_name=AWS_REGION,
        )
    )

    remediation_execution_repository = (
        RemediationExecutionRepository(
            table_name="cloudops-autopilot-remediation-executions",
            region_name=AWS_REGION,
        )
    )

    sns_client = SNSClient(
        region_name=AWS_REGION,
    )

    notification_idempotency_repository = NotificationIdempotencyRepository(
        table_name="cloudops-autopilot-notification-idempotency",
        region_name=AWS_REGION,
    )

    notification_service = NotificationService(
        sns_client=sns_client,
        topic_arn=SNS_TOPIC_ARN,
        idempotency_repository=notification_idempotency_repository,
    )

    monitoring_service = MonitoringService(
        cloudwatch_client=cloudwatch_client,
    )

    verification_service = VerificationService(
        cloudwatch_client=cloudwatch_client,
    )

    incident_repository = DynamoDBIncidentRepository(
        table_name="cloudops-autopilot-incidents",
        region_name=AWS_REGION,
    )

    detection_result = monitoring_service.check_ec2_cpu(
        instance_id=EC2_INSTANCE_ID,
        threshold=CPU_THRESHOLD,
    )

    if detection_result is None:
        print("No incident detected.")
        return

    incident = detection_result.incident
    evidence = detection_result.evidence

    print(f"Incident detected: {incident.incident_type}")

    incident_repository.save(incident)
    print("Incident persisted: DynamoDB")

    if should_notify(incident.status):
        notification_result = notification_service.notify_incident(
            incident_id=incident.incident_id,
            incident_type=incident.incident_type,
            severity=incident.severity,
            resource=incident.resource,
            status=incident.status,
            description=incident.description,
        )

        if notification_result:
            print(f"Notification sent: {incident.status}")
        else:
            print(
                f"Notification skipped or failed: "
                f"{incident.status}"
            )

    incident.transition_to("ACKNOWLEDGED")
    incident_repository.update(incident)
    print(f"Incident state: {incident.status}")

    incident.transition_to("INVESTIGATING")
    incident_repository.update(incident)
    print(f"Incident state: {incident.status}")

    diagnosis = diagnose_incident(
        incident,
        evidence,
    )

    risk = assess_risk(incident)
    recommendation = recommend_action(
        incident,
        risk,
    )

    print(f"Diagnosis: {diagnosis.probable_cause}")
    print(f"Confidence: {diagnosis.confidence}")
    print(f"Evidence: {diagnosis.evidence}")
    print(f"Risk: {risk}")
    print(f"Recommendation: {recommendation}")

    remediation_action = RemediationAction(
        action_id="EC2_REBOOT",
        name="Reboot EC2 instance",
        description=(
            "Restart a running EC2 instance "
            "to recover from a controlled incident."
        ),
        risk_level="MEDIUM",
        resource_id=EC2_INSTANCE_ID,
    )

    guardrail_result = validate_action(
        remediation_action,
    )

    print(f"Guardrail allowed: {guardrail_result.allowed}")
    print(f"Guardrail reason: {guardrail_result.reason}")

    if not guardrail_result.allowed:
        print("Remediation blocked by safety guardrails.")
        return

    approved = request_approval(
        remediation_action,
    )

    if not approved:
        print("Action rejected.")
        return

    print("Action approved.")

    incident.transition_to("REMEDIATING")
    incident_repository.update(incident)
    print(f"Incident state: {incident.status}")

    if should_notify(incident.status):
        notification_result = notification_service.notify_incident(
            incident_id=incident.incident_id,
            incident_type=incident.incident_type,
            severity=incident.severity,
            resource=incident.resource,
            status=incident.status,
            description=incident.description,
        )

        if notification_result:
            print(f"Notification sent: {incident.status}")
        else:
            print(
                f"Notification skipped or failed: "
                f"{incident.status}"
            )

    remediation_result = execute_remediation(
        action=remediation_action,
        incident_id=incident.incident_id,
        ec2_client=ec2_client,
        idempotency_repository=remediation_idempotency_repository,
        execution_repository=remediation_execution_repository,
    )

    print(f"Remediation status: {remediation_result.status}")
    print(f"Remediation message: {remediation_result.message}")

    if remediation_result.error:
        print(f"Remediation error: {remediation_result.error}")

    if remediation_result.status != "SUCCESS":
        print("Remediation did not execute successfully.")
        return

    incident.transition_to("VERIFYING")
    incident_repository.update(incident)
    print(f"Incident state: {incident.status}")

    recovered = verification_service.verify_ec2_cpu_recovery(
        instance_id=EC2_INSTANCE_ID,
        threshold=CPU_THRESHOLD,
    )

    if recovered:
        incident.transition_to("RESOLVED")
        incident_repository.update(incident)
        print(f"Incident state: {incident.status}")

        if should_notify(incident.status):
            notification_result = notification_service.notify_incident(
                incident_id=incident.incident_id,
                incident_type=incident.incident_type,
                severity=incident.severity,
                resource=incident.resource,
                status=incident.status,
                description=incident.description,
            )

            if notification_result:
                print(f"Notification sent: {incident.status}")
            else:
                print(
                    f"Notification skipped or failed: "
                    f"{incident.status}"
                )

        print("Verification: System recovered successfully.")

    else:
        incident.transition_to("INVESTIGATING")
        incident_repository.update(incident)
        print(f"Incident state: {incident.status}")
        print("Verification: System has not recovered.")


if __name__ == "__main__":
    main()