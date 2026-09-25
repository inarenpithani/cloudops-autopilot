from cloudops_engine.models.incident import Incident


def recommend_action(incident: Incident, risk_level: str) -> str:
    if incident.incident_type == "HIGH_CPU":
        if risk_level == "MEDIUM":
            return "Collect additional metrics and investigate the top CPU-consuming processes."

        return "Monitor CPU utilization and collect additional diagnostic data."

    return "No remediation action available."