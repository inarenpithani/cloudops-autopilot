from cloudops_engine.detection.detector import detect_high_cpu
from cloudops_engine.diagnosis.root_cause import diagnose_incident
from cloudops_engine.risk.assessment import assess_risk
from cloudops_engine.remediation.recommendation import recommend_action
from cloudops_engine.remediation.approval import request_approval
from cloudops_engine.remediation.executor import execute_remediation
from cloudops_engine.verification.health_check import verify_cpu_recovery


def main():
    print("CloudOps Autopilot is starting...\n")

    incident = detect_high_cpu(95)

    if incident is None:
        print("No incident detected.")
        return

    diagnosis = diagnose_incident(incident)
    risk = assess_risk(incident)
    recommendation = recommend_action(incident, risk)

    print(f"Incident: {incident.incident_type}")
    print(f"Diagnosis: {diagnosis}")
    print(f"Risk: {risk}")

    approved = request_approval(recommendation)

    if approved:
        print("Action approved.")

        result = execute_remediation(recommendation)
        print(result)

        simulated_cpu_after_remediation = 60.0
        recovered = verify_cpu_recovery(simulated_cpu_after_remediation)

        if recovered:
            print("Verification: System recovered successfully.")
        else:
            print("Verification: System has not recovered.")

    else:
        print("Action rejected.")


if __name__ == "__main__":
    main()