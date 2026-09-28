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


def test_notification_flow_publishes_to_real_sns():
    sns_client = SNSClient()

    idempotency_repository = NotificationIdempotencyRepository(
        table_name=IDEMPOTENCY_TABLE_NAME,
        region_name="ap-south-1",
    )

    notification_service = NotificationService(
        sns_client=sns_client,
        topic_arn=SNS_TOPIC_ARN,
        idempotency_repository=idempotency_repository,
    )

    incident_id = "INC-DAY10-001-REAL-SNS"

    message_id = notification_service.notify_incident(
        incident_id=incident_id,
        incident_type="high_cpu",
        severity="high",
        resource="i-test",
        status="DETECTED",
        description="Day 10 real SNS integration test.",
    )

    assert message_id

    idempotency_repository.release_notification(
        f"{incident_id}#DETECTED"
    )