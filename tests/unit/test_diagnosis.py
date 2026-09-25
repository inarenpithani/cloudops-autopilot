from cloudops_engine.detection.detector import detect_high_cpu
from cloudops_engine.diagnosis.root_cause import diagnose_incident


def test_high_cpu_diagnosis():
    incident = detect_high_cpu(95)

    diagnosis = diagnose_incident(incident)

    assert diagnosis == "High resource utilization on the affected compute instance."


def test_unknown_incident_diagnosis():
    incident = detect_high_cpu(95)
    incident.incident_type = "UNKNOWN"

    diagnosis = diagnose_incident(incident)

    assert diagnosis == "Root cause could not be determined."