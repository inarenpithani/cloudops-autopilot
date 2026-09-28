from cloudops_engine.repositories.notification_idempotency_repository import (
    NotificationIdempotencyRepository,
)


TABLE_NAME = "cloudops-autopilot-notification-idempotency"


def test_notification_idempotency_flow():
    repository = NotificationIdempotencyRepository(
        table_name=TABLE_NAME,
        region_name="ap-south-1",
    )

    notification_key = "INC-INTEGRATION-IDEMPOTENCY-001#DETECTED"

    first_claim = repository.claim_notification(notification_key)

    assert first_claim is True

    second_claim = repository.claim_notification(notification_key)

    assert second_claim is False

    repository.release_notification(notification_key)

    third_claim = repository.claim_notification(notification_key)

    assert third_claim is True

    repository.release_notification(notification_key)