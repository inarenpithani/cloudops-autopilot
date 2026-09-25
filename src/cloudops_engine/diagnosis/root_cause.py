from cloudops_engine.models.incident import Incident


def diagnose_incident(incident: Incident) -> str:
    if incident.incident_type == "HIGH_CPU":
        return "High resource utilization on the affected compute instance."

    return "Root cause could not be determined."