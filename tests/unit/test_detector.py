from cloudops_engine.detection.detector import detect_high_cpu


def test_high_cpu_creates_incident():
    incident = detect_high_cpu(95)

    assert incident is not None
    assert incident.incident_type == "HIGH_CPU"
    assert incident.severity == "HIGH"


def test_normal_cpu_does_not_create_incident():
    incident = detect_high_cpu(70)

    assert incident is None