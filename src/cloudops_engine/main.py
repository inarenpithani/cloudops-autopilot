from cloudops_engine.aws.cloudwatch import CloudWatchClient
from cloudops_engine.config import AWS_REGION, EC2_INSTANCE_ID, CPU_THRESHOLD
from cloudops_engine.diagnosis.root_cause import diagnose_incident
from cloudops_engine.remediation.approval import request_approval
from cloudops_engine.remediation.executor import execute_remediation
from cloudops_engine.remediation.guardrails import validate_action
from cloudops_engine.remediation.recommendation import recommend_action
from cloudops_engine.repositories.dynamodb_incident_repository import (
    DynamoDBIncidentRepository,
)
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

    incident_repository = DynamoDBIncidentRepository(
        table_name="cloudops-autopilot-incidents",
        region_name=AWS_REGION,
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

    print(f"Incident detected: {incident.incident_type}")

    incident_repository.save(incident)
    print("Incident persisted: DynamoDB")

    incident.transition_to("ACKNOWLEDGED")
    incident_repository.update(incident)
    print(f"Incident state: {incident.status}")

    incident.transition_to("INVESTIGATING")
    incident_repository.update(incident)
    print(f"Incident state: {incident.status}")

    diagnosis = diagnose_incident(
        incident,
        evidence,
    )

    risk = assess_risk(incident)
    recommendation = recommend_action(incident, risk)

    print(f"Diagnosis: {diagnosis.probable_cause}")
    print(f"Confidence: {diagnosis.confidence}")
    print(f"Evidence: {diagnosis.evidence}")
    print(f"Risk: {risk}")
    print(f"Recommendation: {recommendation}")

    guardrail_result = validate_action(
        action=recommendation,
        risk=risk,
    )

    print(f"Guardrail allowed: {guardrail_result.allowed}")
    print(f"Guardrail reason: {guardrail_result.reason}")

    if not guardrail_result.allowed:
        print("Remediation blocked by safety guardrails.")
        return

    approved = request_approval(recommendation)

    if not approved:
        print("Action rejected.")
        return

    print("Action approved.")

    incident.transition_to("REMEDIATING")
    incident_repository.update(incident)
    print(f"Incident state: {incident.status}")

    remediation_result = execute_remediation(
        action=recommendation,
        incident_id=incident.incident_id,
    )

    print(f"Remediation status: {remediation_result.status}")
    print(f"Remediation message: {remediation_result.message}")

    if remediation_result.error:
        print(f"Remediation error: {remediation_result.error}")

    if remediation_result.status != "SUCCESS":
        print("Remediation did not execute successfully.")
        return

    incident.transition_to("VERIFYING")
    incident_repository.update(incident)
    print(f"Incident state: {incident.status}")

    simulated_cpu_after_remediation = 60.0

    recovered = verify_cpu_recovery(
        simulated_cpu_after_remediation,
    )

    if recovered:
        incident.transition_to("RESOLVED")
        incident_repository.update(incident)
        print(f"Incident state: {incident.status}")
        print("Verification: System recovered successfully.")
    else:
        incident.transition_to("INVESTIGATING")
        incident_repository.update(incident)
        print(f"Incident state: {incident.status}")
        print("Verification: System has not recovered.")


if __name__ == "__main__":
    main()