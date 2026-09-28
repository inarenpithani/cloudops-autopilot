from unittest.mock import Mock

from cloudops_engine.notifications.service import NotificationService


def test_notify_incident_publishes_notification():
    sns_client = Mock()
    sns_client.publish.return_value = "test-message-id"

    idempotency_repository = Mock()
    idempotency_repository.claim_notification.return_value = True

    service = NotificationService(
        sns_client=sns_client,
        topic_arn=(
            "arn:aws:sns:ap-south-1:123456789012:"
            "cloudops-autopilot-incidents"
        ),
        idempotency_repository=idempotency_repository,
    )

    message_id = service.notify_incident(
        incident_id="INC-001",
        incident_type="high_cpu",
        severity="high",
        resource="i-test",
        status="DETECTED",
        description="EC2 CPU utilization exceeded the configured threshold.",
    )

    assert message_id == "test-message-id"

    idempotency_repository.claim_notification.assert_called_once_with(
        "INC-001#DETECTED"
    )

    sns_client.publish.assert_called_once_with(
        topic_arn=(
            "arn:aws:sns:ap-south-1:123456789012:"
            "cloudops-autopilot-incidents"
        ),
        subject="CloudOps Incident | HIGH | INC-001",
        message=(
            "CloudOps Autopilot Incident\n\n"
            "Incident ID: INC-001\n"
            "Incident Type: high_cpu\n"
            "Severity: high\n"
            "Resource: i-test\n"
            "Status: DETECTED\n"
            "Description: EC2 CPU utilization exceeded the configured threshold.\n"
        ),
    )


def test_notify_incident_skips_duplicate_notification():
    sns_client = Mock()

    idempotency_repository = Mock()
    idempotency_repository.claim_notification.return_value = False

    service = NotificationService(
        sns_client=sns_client,
        topic_arn="test-topic-arn",
        idempotency_repository=idempotency_repository,
    )

    message_id = service.notify_incident(
        incident_id="INC-001",
        incident_type="high_cpu",
        severity="high",
        resource="i-test",
        status="DETECTED",
        description="Duplicate notification test.",
    )

    assert message_id is None

    idempotency_repository.claim_notification.assert_called_once_with(
        "INC-001#DETECTED"
    )

    sns_client.publish.assert_not_called()


def test_notify_incident_handles_notification_failure():
    sns_client = Mock()
    sns_client.publish.side_effect = Exception("SNS unavailable")

    idempotency_repository = Mock()
    idempotency_repository.claim_notification.return_value = True

    service = NotificationService(
        sns_client=sns_client,
        topic_arn="test-topic-arn",
        idempotency_repository=idempotency_repository,
    )

    message_id = service.notify_incident(
        incident_id="INC-002",
        incident_type="high_cpu",
        severity="high",
        resource="i-test",
        status="DETECTED",
        description="Notification failure test.",
    )

    assert message_id is None

    sns_client.publish.assert_called_once()

    idempotency_repository.release_notification.assert_called_once_with(
        "INC-002#DETECTED"
    )