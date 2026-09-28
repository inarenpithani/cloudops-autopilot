import boto3


class EC2Client:
    """Execute controlled EC2 operations for CloudOps Autopilot."""

    def __init__(self, region_name: str = "ap-south-1"):
        self.client = boto3.client(
            "ec2",
            region_name=region_name,
        )

    def reboot_instance(self, instance_id: str) -> None:
        """Reboot a specific EC2 instance."""

        self.client.reboot_instances(
            InstanceIds=[instance_id],
        )