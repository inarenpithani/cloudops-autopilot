from cloudops_engine.aws.cloudwatch import CloudWatchClient
from cloudops_engine.detection.detector import detect_high_cpu
from cloudops_engine.models.incident import Incident


class MonitoringService:
    """Coordinate AWS monitoring data with incident detection."""

    def __init__(self, cloudwatch_client: CloudWatchClient):
        self.cloudwatch_client = cloudwatch_client

    def check_ec2_cpu(
        self,
        instance_id: str,
        threshold: float = 90.0,
    ) -> Incident | None:
        """Read EC2 CPU utilization and detect a high CPU incident."""

        cpu_usage = self.cloudwatch_client.get_cpu_utilization(
            instance_id=instance_id,
        )

        if cpu_usage is None:
            return None

        return detect_high_cpu(
            cpu_usage=cpu_usage,
            resource=instance_id,
            threshold=threshold,
        )