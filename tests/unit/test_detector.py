from cloudops_engine.detection.detector import detect_high_cpu


def test_high_cpu_creates_incident():
    incident = detect_high_cpu(
        cpu_datapoints=[92, 94, 96],
        resource="i-05e3bbde2a13509f7",
    )

    assert incident is not None
    assert incident.incident_type == "HIGH_CPU"
    assert incident.severity == "HIGH"
    assert incident.resource == "i-05e3bbde2a13509f7"


def test_normal_cpu_does_not_create_incident():
    incident = detect_high_cpu(
        cpu_datapoints=[70, 75, 80],
        resource="i-05e3bbde2a13509f7",
    )

    assert incident is None


def test_non_consecutive_breaches_do_not_create_incident():
    incident = detect_high_cpu(
        cpu_datapoints=[92, 70, 95],
        resource="i-05e3bbde2a13509f7",
    )

    assert incident is None


def test_insufficient_datapoints_do_not_create_incident():
    incident = detect_high_cpu(
        cpu_datapoints=[92, 94],
        resource="i-05e3bbde2a13509f7",
    )

    assert incident is None


def test_cpu_at_threshold_does_not_create_incident():
    incident = detect_high_cpu(
        cpu_datapoints=[90.0, 90.0, 90.0],
        resource="i-05e3bbde2a13509f7",
    )

    assert incident is None


def test_cpu_custom_threshold_creates_incident():
    incident = detect_high_cpu(
        cpu_datapoints=[81.0, 83.0, 85.0],
        resource="i-05e3bbde2a13509f7",
        threshold=80.0,
    )

    assert incident is not None


def test_cpu_custom_breach_count():
    incident = detect_high_cpu(
        cpu_datapoints=[92.0, 94.0],
        resource="i-05e3bbde2a13509f7",
        required_breaches=2,
    )

    assert incident is not None