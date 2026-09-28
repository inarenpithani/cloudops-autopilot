from cloudops_engine.aws.cloudwatch import CloudWatchClient
from cloudops_engine.verification.health_check import verify_cpu_recovery


class VerificationService:
    """Coordinate post-remediation verification."""

    def __init__(self, cloudwatch_client: CloudWatchClient):
        self.cloudwatch_client = cloudwatch_client

    def verify_ec2_cpu_recovery(
        self,
        instance_id: str,
        threshold: float = 90.0,
        required_healthy_datapoints: int = 3,
    ) -> bool:
        """Verify that EC2 CPU utilization has recovered."""

        cpu_datapoints = self.cloudwatch_client.get_cpu_utilization(
            instance_id=instance_id,
        )

        if len(cpu_datapoints) < required_healthy_datapoints:
            return False

        recent_datapoints = cpu_datapoints[
            -required_healthy_datapoints:
        ]

        return all(
            verify_cpu_recovery(
                datapoint["value"],
                threshold=threshold,
            )
            for datapoint in recent_datapoints
        )