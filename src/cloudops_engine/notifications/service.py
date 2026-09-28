from cloudops_engine.aws.sns import SNSClient
from cloudops_engine.repositories.notification_idempotency_repository import (
    NotificationIdempotencyRepository,
)


class NotificationService:
    """Coordinate CloudOps Autopilot incident notifications."""

    def __init__(
        self,
        sns_client: SNSClient,
        topic_arn: str,
        idempotency_repository: NotificationIdempotencyRepository,
    ):
        self.sns_client = sns_client
        self.topic_arn = topic_arn
        self.idempotency_repository = idempotency_repository

    def notify_incident(
        self,
        incident_id: str,
        incident_type: str,
        severity: str,
        resource: str,
        status: str,
        description: str,
    ) -> str | None:
        """Publish an incident notification with duplicate protection."""

        notification_key = f"{incident_id}#{status}"

        claimed = self.idempotency_repository.claim_notification(
            notification_key
        )

        if not claimed:
            return None

        subject = (
            f"CloudOps Incident | "
            f"{severity.upper()} | "
            f"{incident_id}"
        )

        message = (
            "CloudOps Autopilot Incident\n\n"
            f"Incident ID: {incident_id}\n"
            f"Incident Type: {incident_type}\n"
            f"Severity: {severity}\n"
            f"Resource: {resource}\n"
            f"Status: {status}\n"
            f"Description: {description}\n"
        )

        try:
            return self.sns_client.publish(
                topic_arn=self.topic_arn,
                subject=subject,
                message=message,
            )

        except Exception as error:
            self.idempotency_repository.release_notification(
                notification_key
            )

            print(
                f"Notification failed for incident "
                f"{incident_id}: {error}"
            )

            return None