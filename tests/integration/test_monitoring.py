from cloudops_engine.aws.cloudwatch import CloudWatchClient
from cloudops_engine.services.monitoring import MonitoringService


def test_check_ec2_cpu():
    cloudwatch_client = CloudWatchClient()
    monitoring_service = MonitoringService(cloudwatch_client)

    detection_result = monitoring_service.check_ec2_cpu(
        instance_id="i-05e3bbde2a13509f7",
    )

    if detection_result is not None:
        assert detection_result.incident.incident_type == "HIGH_CPU"
        assert detection_result.incident.severity == "HIGH"
        assert (
            detection_result.incident.resource
            == "i-05e3bbde2a13509f7"
        )

        assert len(detection_result.evidence) == 3

        for evidence in detection_result.evidence:
            assert evidence.source == "CloudWatch"
            assert evidence.signal == "CPUUtilization"
            assert evidence.observed_at is not None