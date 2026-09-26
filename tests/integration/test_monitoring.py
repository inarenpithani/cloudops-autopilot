from cloudops_engine.aws.cloudwatch import CloudWatchClient
from cloudops_engine.services.monitoring import MonitoringService


def test_check_ec2_cpu():
    cloudwatch_client = CloudWatchClient()
    monitoring_service = MonitoringService(cloudwatch_client)

    incident = monitoring_service.check_ec2_cpu(
        instance_id="i-05e3bbde2a13509f7",
    )

    if incident is not None:
        assert incident.incident_type == "HIGH_CPU"
        assert incident.severity == "HIGH"
        assert incident.resource == "EC2-i-123456"