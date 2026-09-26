from datetime import datetime

from cloudops_engine.aws.cloudwatch import CloudWatchClient


def test_get_cpu_utilization():
    client = CloudWatchClient()

    cpu_datapoints = client.get_cpu_utilization(
        instance_id="i-05e3bbde2a13509f7",
        minutes=15,
    )

    assert isinstance(cpu_datapoints, list)

    for datapoint in cpu_datapoints:
        assert isinstance(datapoint, dict)

        assert "value" in datapoint
        assert "timestamp" in datapoint

        assert isinstance(datapoint["value"], float)
        assert isinstance(datapoint["timestamp"], datetime)