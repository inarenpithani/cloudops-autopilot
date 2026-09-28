from unittest.mock import Mock

from cloudops_engine.verification.verification_service import (
    VerificationService,
)


def test_cpu_recovery_succeeds_when_recent_datapoints_are_healthy():
    cloudwatch_client = Mock()

    cloudwatch_client.get_cpu_utilization.return_value = [
        {"value": 95.0, "timestamp": "t1"},
        {"value": 60.0, "timestamp": "t2"},
        {"value": 70.0, "timestamp": "t3"},
        {"value": 65.0, "timestamp": "t4"},
    ]

    service = VerificationService(cloudwatch_client)

    result = service.verify_ec2_cpu_recovery(
        instance_id="i-test",
    )

    assert result is True


def test_cpu_recovery_fails_when_recent_datapoints_are_not_all_healthy():
    cloudwatch_client = Mock()

    cloudwatch_client.get_cpu_utilization.return_value = [
        {"value": 60.0, "timestamp": "t1"},
        {"value": 70.0, "timestamp": "t2"},
        {"value": 95.0, "timestamp": "t3"},
        {"value": 65.0, "timestamp": "t4"},
    ]

    service = VerificationService(cloudwatch_client)

    result = service.verify_ec2_cpu_recovery(
        instance_id="i-test",
    )

    assert result is False


def test_cpu_recovery_fails_when_not_enough_datapoints_exist():
    cloudwatch_client = Mock()

    cloudwatch_client.get_cpu_utilization.return_value = [
        {"value": 60.0, "timestamp": "t1"},
        {"value": 70.0, "timestamp": "t2"},
    ]

    service = VerificationService(cloudwatch_client)

    result = service.verify_ec2_cpu_recovery(
        instance_id="i-test",
    )

    assert result is False