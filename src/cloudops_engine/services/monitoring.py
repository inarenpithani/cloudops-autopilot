from cloudops_engine.aws.cloudwatch import CloudWatchClient
from cloudops_engine.detection.detector import detect_high_cpu
from cloudops_engine.models.detection_result import DetectionResult


class MonitoringService:
    """Coordinate AWS monitoring data with incident detection."""

    def __init__(self, cloudwatch_client: CloudWatchClient):
        self.cloudwatch_client = cloudwatch_client

    def check_ec2_cpu(
        self,
        instance_id: str,
        threshold: float = 90.0,
        required_breaches: int = 3,
    ) -> DetectionResult | None:
        """Read EC2 CPU datapoints and detect persistent high CPU."""

        cpu_datapoints = self.cloudwatch_client.get_cpu_utilization(
            instance_id=instance_id,
        )

        return detect_high_cpu(
            cpu_datapoints=cpu_datapoints,
            resource=instance_id,
            threshold=threshold,
            required_breaches=required_breaches,
        )