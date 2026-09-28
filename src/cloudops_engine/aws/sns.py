import boto3


class SNSClient:
    """Publish CloudOps Autopilot notifications through Amazon SNS."""

    def __init__(self, region_name: str = "ap-south-1"):
        self.client = boto3.client(
            "sns",
            region_name=region_name,
        )

    def publish(
        self,
        topic_arn: str,
        subject: str,
        message: str,
    ) -> str:
        """Publish a notification message to an SNS topic."""

        response = self.client.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message,
        )

        return response["MessageId"]