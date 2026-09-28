from unittest.mock import Mock

from cloudops_engine.verification.verification_service import (
    VerificationService,
)


def test_verification_flow_confirms_recovery_after_remediation():
    cloudwatch_client = Mock()

    cloudwatch_client.get_cpu_utilization.return_value = [
        {"value": 60.0, "timestamp": "t1"},
        {"value": 65.0, "timestamp": "t2"},
        {"value": 70.0, "timestamp": "t3"},
    ]

    verification_service = VerificationService(
        cloudwatch_client=cloudwatch_client,
    )

    recovered = verification_service.verify_ec2_cpu_recovery(
        instance_id="i-test",
        threshold=90.0,
        required_healthy_datapoints=3,
    )

    assert recovered is True

    cloudwatch_client.get_cpu_utilization.assert_called_once_with(
        instance_id="i-test",
    )