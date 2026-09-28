from unittest.mock import MagicMock, patch

from cloudops_engine.aws.ec2 import EC2Client


@patch("cloudops_engine.aws.ec2.boto3.client")
def test_reboot_instance(mock_boto3_client):
    mock_ec2_client = MagicMock()

    mock_boto3_client.return_value = mock_ec2_client

    ec2_client = EC2Client(
        region_name="ap-south-1",
    )

    ec2_client.reboot_instance(
        instance_id="i-test-instance",
    )

    mock_ec2_client.reboot_instances.assert_called_once_with(
        InstanceIds=["i-test-instance"],
    )