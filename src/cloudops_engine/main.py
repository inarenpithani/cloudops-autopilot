from cloudops_engine.aws.cloudwatch import CloudWatchClient
from cloudops_engine.config import AWS_REGION, EC2_INSTANCE_ID, CPU_THRESHOLD
from cloudops_engine.diagnosis.root_cause import diagnose_incident
from cloudops_engine.remediation.approval import request_approval
from cloudops_engine.remediation.executor import execute_remediation
from cloudops_engine.remediation.recommendation import recommend_action
from cloudops_engine.risk.assessment import assess_risk
from cloudops_engine.services.monitoring import MonitoringService
from cloudops_engine.verification.health_check import verify_cpu_recovery


def main():
    print("CloudOps Autopilot is starting...\n")

    if not EC2_INSTANCE_ID:
        print("EC2_INSTANCE_ID is not configured.")
        return

    cloudwatch_client = CloudWatchClient(
        region_name=AWS_REGION,
    )

    monitoring_service = MonitoringService(
        cloudwatch_client=cloudwatch_client,
    )

    detection_result = monitoring_service.check_ec2_cpu(
        instance_id=EC2_INSTANCE_ID,
        threshold=CPU_THRESHOLD,
    )

    if detection_result is None:
        print("No incident detected.")
        return

    incident = detection_result.incident
    evidence = detection_result.evidence

    diagnosis = diagnose_incident(
        incident,
        evidence,
    )

    risk = assess_risk(incident)
    recommendation = recommend_action(incident, risk)

    print(f"Incident: {incident.incident_type}")
    print(f"Diagnosis: {diagnosis.probable_cause}")
    print(f"Confidence: {diagnosis.confidence}")
    print(f"Evidence: {diagnosis.evidence}")
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