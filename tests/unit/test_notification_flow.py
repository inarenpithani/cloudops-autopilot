from unittest.mock import Mock

from cloudops_engine.notifications.policy import should_notify
from cloudops_engine.notifications.service import NotificationService


def test_notifiable_incident_state_triggers_notification():
    sns_client = Mock()
    sns_client.publish.return_value = "test-message-id"

    idempotency_repository = Mock()
    idempotency_repository.claim_notification.return_value = True

    service = NotificationService(
        sns_client=sns_client,
        topic_arn="test-topic-arn",
        idempotency_repository=idempotency_repository,
    )

    state = "DETECTED"

    if should_notify(state):
        message_id = service.notify_incident(
            incident_id="INC-001",
            incident_type="high_cpu",
            severity="high",
            resource="i-test",
            status=state,
            description="Test incident notification.",
        )
    else:
        message_id = None

    assert message_id == "test-message-id"

    idempotency_repository.claim_notification.assert_called_once_with(
        "INC-001#DETECTED"
    )

    sns_client.publish.assert_called_once()