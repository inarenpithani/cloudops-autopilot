from datetime import datetime, timedelta, timezone

import boto3


class CloudWatchClient:
    """Read CloudWatch metrics for CloudOps Autopilot."""

    def __init__(self, region_name: str = "ap-south-1"):
        self.client = boto3.client(
            "cloudwatch",
            region_name=region_name,
        )

    def get_cpu_utilization(
        self,
        instance_id: str,
        minutes: int = 15,
    ) -> list[dict]:
        """Return CPU utilization datapoints with timestamps."""

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(minutes=minutes)

        response = self.client.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[
                {
                    "Name": "InstanceId",
                    "Value": instance_id,
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=["Average"],
        )

        datapoints = response.get("Datapoints", [])

        sorted_datapoints = sorted(
            datapoints,
            key=lambda datapoint: datapoint["Timestamp"],
        )

        return [
            {
                "value": float(datapoint["Average"]),
                "timestamp": datapoint["Timestamp"],
            }
            for datapoint in sorted_datapoints
        ]