from cloudops_engine.aws.sns import SNSClient
from cloudops_engine.notifications.service import NotificationService
from cloudops_engine.repositories.notification_idempotency_repository import (
    NotificationIdempotencyRepository,
)


SNS_TOPIC_ARN = (
    "arn:aws:sns:ap-south-1:298785331841:"
    "cloudops-autopilot-incidents"
)

IDEMPOTENCY_TABLE_NAME = (
    "cloudops-autopilot-notification-idempotency"
)


def test_incident_notification_flow():
    sns_client = SNSClient(
        region_name="ap-south-1",
    )

    idempotency_repository = NotificationIdempotencyRepository(
        table_name=IDEMPOTENCY_TABLE_NAME,
        region_name="ap-south-1",
    )

    notification_service = NotificationService(
        sns_client=sns_client,
        topic_arn=SNS_TOPIC_ARN,
        idempotency_repository=idempotency_repository,
    )

    incident_id = "INC-INTEGRATION-NOTIFICATION-001"

    first_message_id = notification_service.notify_incident(
        incident_id=incident_id,
        incident_type="high_cpu",
        severity="high",
        resource="i-test",
        status="DETECTED",
        description="Full Day 10 notification integration test.",
    )

    assert first_message_id

    duplicate_message_id = notification_service.notify_incident(
        incident_id=incident_id,
        incident_type="high_cpu",
        severity="high",
        resource="i-test",
        status="DETECTED",
        description="Duplicate notification attempt.",
    )

    assert duplicate_message_id is None

    idempotency_repository.release_notification(
        f"{incident_id}#DETECTED"
    )