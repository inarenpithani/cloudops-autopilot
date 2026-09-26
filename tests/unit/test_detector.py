from cloudops_engine.detection.detector import detect_high_cpu


def test_high_cpu_creates_incident():
    incident = detect_high_cpu(
        cpu_usage=95,
        resource="i-05e3bbde2a13509f7",
    )

    assert incident is not None
    assert incident.incident_type == "HIGH_CPU"
    assert incident.severity == "HIGH"
    assert incident.resource == "i-05e3bbde2a13509f7"


def test_normal_cpu_does_not_create_incident():
    incident = detect_high_cpu(
        cpu_usage=70,
        resource="i-05e3bbde2a13509f7",
    )

    assert incident is None