from cloudops_engine.models.incident import Incident


def assess_risk(incident: Incident) -> str:
    if incident.incident_type == "HIGH_CPU" and incident.severity == "HIGH":
        return "MEDIUM"

    return "LOW"