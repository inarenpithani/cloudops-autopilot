from cloudops_engine.aws.cloudwatch import CloudWatchClient


def test_get_cpu_utilization():
    client = CloudWatchClient()

    cpu = client.get_cpu_utilization(
        instance_id="i-05e3bbde2a13509f7",
        minutes=15,
    )

    assert cpu is None or isinstance(cpu, float)

    if cpu is not None:
        assert 0.0 <= cpu <= 100.0