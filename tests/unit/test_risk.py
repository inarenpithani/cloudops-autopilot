from cloudops_engine.detection.detector import detect_high_cpu
from cloudops_engine.risk.assessment import assess_risk


def test_high_cpu_high_severity_has_medium_risk():
    incident = detect_high_cpu(95)

    risk = assess_risk(incident)

    assert risk == "MEDIUM"


def test_low_risk_for_other_incident():
    incident = detect_high_cpu(95)
    incident.incident_type = "UNKNOWN"

    risk = assess_risk(incident)

    assert risk == "LOW"