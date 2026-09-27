# CloudOps Autopilot — Logging and Observability Strategy

## 1. Purpose

This document defines the logging and observability strategy for CloudOps Autopilot.

The objective is to make the platform:

* Observable
* Diagnosable
* Auditable
* Measurable
* Debuggable
* Reliable
* Production-ready

CloudOps Autopilot is an incident automation platform. Therefore, the platform itself must also be observable.

The system should be able to answer:

* What happened?
* When did it happen?
* Which resource was affected?
* What evidence was collected?
* What diagnosis was produced?
* What risk was identified?
* What action was recommended?
* Was the action approved?
* What action was executed?
* Did execution succeed?
* Did verification succeed?
* What was the final incident state?

---

# 2. Observability Principles

CloudOps Autopilot follows these principles:

1. Logs should be structured.
2. Important operations should have correlation identifiers.
3. Logs should provide operational context.
4. Sensitive information must not be logged.
5. Metrics should measure system behavior.
6. Logs should support incident investigation.
7. Observability should cover both the monitored environment and CloudOps Autopilot itself.
8. Alerts should be actionable.
9. Monitoring should not create excessive noise.
10. Observability data should support research and operational analysis.

---

# 3. Observability Model

The platform follows the three major observability signals:

```text
Logs
Metrics
Traces
```

Conceptually:

```text
                  CloudOps Autopilot
                         |
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
        Logs           Metrics         Traces
          |              |              |
          └──────────────┼──────────────┘
                         ↓
                 Observability
                         ↓
              Detection / Diagnosis
                         ↓
                 Incident Response
```

The current implementation primarily uses logs and AWS monitoring metrics.

Tracing is a future enhancement as the platform becomes distributed.

---

# 4. Logging Strategy

Logging is used to record application events and operational decisions.

The logging strategy should favor structured, machine-readable logs over unstructured text.

Preferred conceptual format:

```text
timestamp
level
service
environment
incident_id
resource_id
event
message
```

Example:

```json
{
  "timestamp": "2026-09-27T10:00:00Z",
  "level": "INFO",
  "service": "cloudops-autopilot",
  "environment": "DEV",
  "incident_id": "INC-001",
  "event": "incident_detected",
  "message": "High CPU incident detected"
}
```

The exact schema may evolve as implementation matures.

---

# 5. Log Levels

The application should use standard log levels.

## DEBUG

Detailed information useful during development and troubleshooting.

Examples:

* Metric query parameters
* Internal decision details
* Repository operations

DEBUG logging should be controlled in production.

---

## INFO

Normal operational events.

Examples:

* Application startup
* Incident detected
* Diagnosis completed
* Recommendation generated
* Approval received
* Remediation started
* Verification completed

---

## WARNING

Unexpected conditions that do not necessarily stop the application.

Examples:

* Missing optional configuration
* Retry initiated
* Unexpected but recoverable AWS response
* Verification did not recover on the first attempt

---

## ERROR

An operation failed and requires attention.

Examples:

* DynamoDB persistence failure
* CloudWatch query failure
* Remediation execution failure
* Configuration validation failure

---

## CRITICAL

Severe failures that may prevent the system from operating correctly.

Examples:

* Required configuration unavailable
* Critical dependency unavailable
* Security control failure
* Persistent failure of core incident processing

CRITICAL should be used sparingly.

---

# 6. Structured Logging

CloudOps Autopilot should avoid relying primarily on free-form messages.

Instead of:

```text
CPU is high
```

prefer structured information such as:

```text
event=incident_detected
incident_type=HIGH_CPU
resource_id=i-example
cpu_threshold=90
```

Structured logs improve:

* Searchability
* Filtering
* Aggregation
* Alerting
* Dashboards
* Automated analysis

---

# 7. Correlation IDs

Distributed systems require a way to connect related operations.

CloudOps Autopilot should use identifiers such as:

```text
incident_id
execution_id
experiment_id
request_id
```

The primary operational correlation identifier is:

```text
incident_id
```

Example:

```text
incident_id=INC-001
```

This identifier should appear in logs associated with the same incident whenever available.

---

# 8. Incident-Centric Observability

CloudOps Autopilot should organize operational observability around incidents.

Example:

```text
INC-001
   |
   ├── Detection
   ├── Evidence
   ├── Diagnosis
   ├── Risk Assessment
   ├── Recommendation
   ├── Approval
   ├── Remediation
   ├── Verification
   └── Final State
```

This makes it easier to reconstruct the complete incident lifecycle.

---

# 9. Detection Logging

When an incident is detected, the system should record:

* Incident ID
* Incident type
* Severity
* Resource
* Detection timestamp
* Detection rule
* Threshold
* Observed value
* Required breach count
* Evidence reference

Example:

```json
{
  "event": "incident_detected",
  "incident_id": "INC-001",
  "incident_type": "HIGH_CPU",
  "severity": "HIGH",
  "resource_id": "i-example",
  "threshold": 90,
  "required_breaches": 3
}
```

---

# 10. Evidence Logging

Evidence used for diagnosis should be traceable.

Examples:

* CloudWatch metric
* Metric value
* Timestamp
* Health status
* Error rate
* Resource metadata

The system should record which evidence contributed to the diagnosis.

This supports explainability.

---

# 11. Diagnosis Logging

Diagnosis events should include:

* Incident ID
* Probable cause
* Confidence
* Evidence count
* Diagnosis timestamp

Example:

```text
event=diagnosis_completed
incident_id=INC-001
confidence=0.90
```

The system should avoid logging unsupported conclusions as facts.

Diagnosis should remain distinguishable from raw evidence.

---

# 12. Risk Assessment Logging

Risk assessment should be observable.

Example fields:

```text
incident_id
risk_level
risk_reason
assessment_timestamp
```

Example:

```text
event=risk_assessed
incident_id=INC-001
risk=MEDIUM
```

This allows later analysis of why an action was considered safe or unsafe.

---

# 13. Recommendation Logging

The system should record:

* Incident ID
* Recommended action
* Risk level
* Recommendation timestamp
* Guardrail result

Example:

```text
event=recommendation_generated
incident_id=INC-001
action=collect_cpu_diagnostics
```

The recommendation should be distinguishable from actual execution.

---

# 14. Approval Logging

Approval events are important because human approval is a safety boundary.

The system should eventually record:

* Incident ID
* Recommended action
* Approval decision
* Approver identity
* Approval timestamp
* Approval source

Example:

```text
event=remediation_approval
incident_id=INC-001
decision=APPROVED
```

The current MVP has the approval control, while detailed approval audit implementation remains future work.

---

# 15. Remediation Logging

Remediation execution should produce structured events.

Important fields include:

* Incident ID
* Action ID
* Execution ID
* Start timestamp
* Completion timestamp
* Status
* Error
* Target resource

Example:

```text
event=remediation_completed
incident_id=INC-001
execution_id=EXEC-001
status=SUCCESS
```

---

# 16. Idempotency Logging

Because duplicate-action protection is part of the architecture, idempotency events should also be observable.

Examples:

```text
event=remediation_skipped
reason=duplicate_action
incident_id=INC-001
```

This allows operators to understand why an action was not executed.

---

# 17. Verification Logging

Verification should record:

* Incident ID
* Verification timestamp
* Observed condition
* Expected condition
* Verification result

Example:

```text
event=verification_completed
incident_id=INC-001
result=RECOVERED
```

Verification must not be inferred solely from remediation execution status.

---

# 18. Incident State Logging

Lifecycle transitions should be observable.

Example:

```text
DETECTED
→ ACKNOWLEDGED
→ INVESTIGATING
→ REMEDIATING
→ VERIFYING
→ RESOLVED
```

Each transition should ideally produce an event such as:

```text
event=incident_state_changed
from_state=INVESTIGATING
to_state=REMEDIATING
incident_id=INC-001
```

This makes lifecycle reconstruction easier.

---

# 19. Application Metrics

CloudOps Autopilot should expose metrics describing its own behavior.

Potential metrics include:

### Incident Metrics

* Incidents detected
* Incidents by type
* Incidents by severity
* Incidents resolved
* Incidents unresolved

### Diagnosis Metrics

* Diagnosis count
* Diagnosis confidence
* Diagnosis failures

### Remediation Metrics

* Recommendations generated
* Approvals
* Rejections
* Remediation attempts
* Remediation successes
* Remediation failures
* Duplicate actions skipped

### Verification Metrics

* Verification attempts
* Verification successes
* Verification failures

---

# 20. Research Metrics

The same observability data should support the research evaluation.

Potential metrics include:

* Detection time
* Diagnosis time
* Remediation time
* MTTR
* Human intervention
* Approval latency
* Remediation success rate
* False-positive rate
* Unsafe-action rate
* Verification accuracy
* Duplicate-action rate

This reduces the need for separate manual data collection.

---

# 21. AWS CloudWatch

CloudWatch is the primary AWS-native monitoring platform for the current project.

It is already used to retrieve EC2 CPU utilization.

Future observability architecture can use CloudWatch for:

* Application logs
* Metrics
* Alarms
* Dashboards
* Operational monitoring

Conceptually:

```text
CloudOps Autopilot
       ↓
CloudWatch
   ┌───┼────┐
   ↓   ↓    ↓
 Logs Metrics Alarms
```

---

# 22. CloudWatch Logs

When the application is deployed to AWS services such as Lambda or ECS, application logs should be centralized in CloudWatch Logs.

The logging architecture should preserve:

* Timestamp
* Log level
* Service
* Environment
* Incident ID
* Event
* Message

Logs should be searchable using incident identifiers.

---

# 23. CloudWatch Metrics

Custom application metrics may eventually be published to CloudWatch.

Examples:

```text
CloudOpsAutopilot/IncidentsDetected
CloudOpsAutopilot/RemediationSuccess
CloudOpsAutopilot/RemediationFailure
CloudOpsAutopilot/VerificationFailure
```

Metric naming should remain consistent across environments.

---

# 24. CloudWatch Alarms

CloudWatch alarms can monitor the CloudOps Autopilot platform itself.

Examples:

* Excessive remediation failures
* High application error rate
* DynamoDB errors
* CloudWatch API failures
* Processing latency
* Queue backlog in future event-driven architecture

This creates **monitoring of the monitoring/automation platform**.

---

# 25. Event-Driven Observability

The target architecture may use EventBridge for event-driven processing.

Conceptually:

```text
AWS Event
   ↓
EventBridge
   ↓
CloudOps Autopilot
   ↓
Incident
   ↓
Logs / Metrics / Audit
```

Event metadata should be correlated with the resulting incident.

---

# 26. Distributed Tracing

Tracing is not required for the current local MVP.

As the platform becomes distributed, tracing becomes increasingly useful.

Potential future flow:

```text
EventBridge
    ↓
Lambda / ECS
    ↓
Detection
    ↓
Diagnosis
    ↓
Remediation
    ↓
Verification
```

A trace ID could connect these operations.

Potential tracing technologies include AWS X-Ray or OpenTelemetry-compatible tooling.

The exact implementation will be decided when the distributed architecture is introduced.

---

# 27. Dashboards

A production deployment should provide dashboards for operational visibility.

Potential dashboard sections:

### Incident Overview

* Active incidents
* Incidents by severity
* Incidents by type

### Remediation

* Success rate
* Failure rate
* Approval rate
* Duplicate actions

### Performance

* Detection latency
* Diagnosis latency
* Remediation latency
* Verification latency

### Platform Health

* API errors
* Persistence errors
* Processing failures
* Dependency failures

---

# 28. Alerting Strategy

Alerts should be actionable.

Avoid alerting for every informational event.

Good alerts should represent conditions that require investigation or action.

Examples:

```text
High remediation failure rate
```

```text
CloudOps Autopilot persistence failures
```

```text
Incident processing backlog
```

```text
Verification failures above expected baseline
```

---

# 29. Alert Severity

A future alerting model may classify alerts as:

```text
INFO
WARNING
ERROR
CRITICAL
```

Alert severity should reflect operational impact rather than merely the existence of an event.

---

# 30. Noise Reduction

Observability systems can themselves become a source of operational noise.

The platform should therefore use:

* Appropriate log levels
* Aggregated metrics
* Thresholds
* Alert deduplication
* Alert grouping
* Rate limiting where appropriate

The objective is actionable observability rather than maximum event volume.

---

# 31. Sensitive Data Protection

Logs must never expose sensitive information.

Do not log:

* AWS secret access keys
* Passwords
* Authentication tokens
* Private keys
* Secret values
* Sensitive credentials

Care must also be taken with application payloads that may contain confidential information.

---

# 32. Resource Identifier Handling

Resource identifiers such as EC2 instance IDs may be useful for troubleshooting.

However, logs should avoid unnecessarily exposing sensitive or excessive infrastructure metadata.

The final logging policy should define what identifiers can be logged and at which log levels.

---

# 33. Log Retention

Log retention should be explicitly configured in production.

Retention should consider:

* Operational troubleshooting
* Security investigations
* Research requirements
* Cost
* Compliance requirements

Different log categories may require different retention periods.

The exact retention periods will be defined as part of the production deployment strategy.

---

# 34. Audit Trail

Operational logs and audit records have different purposes.

### Operational Logs

Answer:

> What is the application doing?

### Audit Records

Answer:

> What important action occurred, who authorized it, and what was the result?

For remediation, an audit record should eventually capture:

```text
Incident
→ Recommendation
→ Approval
→ Execution
→ Verification
```

This distinction should be preserved as the system evolves.

---

# 35. Incident Correlation

All major operations should be connected to an incident identifier where applicable.

Example:

```text
INC-001
├── detection
├── evidence
├── diagnosis
├── risk
├── recommendation
├── approval
├── remediation
├── verification
└── resolution
```

This creates an incident-centric operational view.

---

# 36. Observability of Dependencies

CloudOps Autopilot depends on AWS services.

Important dependencies include:

* CloudWatch
* EC2
* DynamoDB
* IAM
* Future EventBridge
* Future Lambda/ECS
* Future SNS

Dependency failures should be distinguishable from application logic failures.

For example:

```text
CloudWatch API failure
```

should not be recorded as:

```text
No incident detected
```

These are different operational states.

---

# 37. Observability Failure Handling

If observability itself fails, the system should avoid silently continuing without visibility.

Examples:

```text
Logging failure
Metric publishing failure
Tracing failure
```

The exact behavior depends on the criticality of the observability component.

Security and audit records may require stronger guarantees than debug logs.

---

# 38. Health Checks

The future deployed application should expose health information.

Possible checks:

### Liveness

Is the application process running?

### Readiness

Can the application process requests and access required dependencies?

### Dependency Health

Are required AWS services reachable and usable?

Health checks should not unnecessarily perform expensive operations.

---

# 39. Platform Self-Monitoring

CloudOps Autopilot must monitor its own health.

The platform should detect conditions such as:

```text
High error rate
High processing latency
DynamoDB failures
CloudWatch failures
Remediation failures
Verification failures
```

This creates a second layer of observability:

```text
Cloud Environment
      ↓
CloudOps Autopilot
      ↓
CloudOps Autopilot Observability
```

---

# 40. Observability and Incident Lifecycle

Observability should cover the complete lifecycle:

```text
DETECTED
   ↓
ACKNOWLEDGED
   ↓
INVESTIGATING
   ↓
REMEDIATING
   ↓
VERIFYING
   ↓
RESOLVED
```

Every important transition should be reconstructable from logs and persistent incident data.

---

# 41. Testing Observability

Observability should itself be tested.

Tests should verify:

* Important events are logged
* Incident IDs are included
* Sensitive values are not logged
* Errors are logged at appropriate levels
* Metrics are emitted correctly
* State transitions are observable
* Duplicate remediation is observable
* Verification results are observable

---

# 42. Development vs Production Observability

## Development

Focus on:

* Debugging
* Detailed logs
* Local troubleshooting
* Test evidence

## UAT

Focus on:

* Integration visibility
* Error detection
* Workflow validation
* Test metrics

## Production

Focus on:

* Actionable alerts
* SLO/SLA monitoring
* Security
* Auditability
* Incident response
* Cost-aware retention
* Platform health

---

# 43. Future SLOs

As the platform becomes production-ready, service-level objectives may be defined.

Possible SLO categories:

* Incident processing latency
* Detection processing success
* Remediation processing success
* Verification completion
* Persistence availability

SLO values should be defined only after actual workload and architecture characteristics are known.

---

# 44. Observability Architecture

## Current

```text
EC2
 ↓
CloudWatch
 ↓
CloudOps Engine
 ↓
Application Output
```

## Target

```text
AWS Environment
      ↓
CloudWatch / EventBridge
      ↓
CloudOps Autopilot
      ↓
┌──────────┬──────────┬──────────┐
│   Logs   │ Metrics  │  Traces  │
└──────────┴──────────┴──────────┘
      ↓
CloudWatch / OpenTelemetry
      ↓
Dashboards / Alerts / Audit
```

---

# 45. Industry Standards Alignment

The strategy aligns with common observability engineering principles:

* Structured logging
* Correlation IDs
* Metrics
* Centralized logs
* Actionable alerts
* Distributed tracing
* Health checks
* Incident correlation
* Sensitive-data protection
* Auditability
* Service self-monitoring
* Environment-specific observability

The implementation will evolve incrementally as the platform moves from a local prototype to a distributed AWS deployment.

---

# 46. Current Implementation Status

### Implemented

* CloudWatch metric monitoring
* Incident evidence collection
* Incident persistence
* Incident lifecycle
* Remediation result model
* Verification result
* Basic application output
* Incident correlation through `incident_id`

### Planned

* Structured logging framework
* JSON logs
* CloudWatch Logs integration
* Custom CloudWatch metrics
* CloudWatch dashboards
* Actionable alarms
* Audit trail
* Distributed tracing
* OpenTelemetry
* Platform health monitoring
* Production SLOs

---

# 47. Observability Roadmap

The observability roadmap is:

```text
Basic Application Logs
        ↓
Structured Logging
        ↓
Centralized CloudWatch Logs
        ↓
Custom Metrics
        ↓
Dashboards
        ↓
Actionable Alerts
        ↓
Audit Trail
        ↓
Distributed Tracing
        ↓
SLO / SLI Monitoring
```

This allows observability maturity to grow with system complexity.

---

# 48. Summary

CloudOps Autopilot treats observability as a core engineering capability rather than an optional operational feature.

The system should make the complete incident lifecycle visible:

```text
Detect
  ↓
Evidence
  ↓
Diagnose
  ↓
Risk
  ↓
Recommend
  ↓
Approve
  ↓
Remediate
  ↓
Verify
  ↓
Resolve
```

The logging and observability strategy is designed to support:

* Operational troubleshooting
* Incident investigation
* Safety verification
* Security auditing
* Performance measurement
* Research evaluation
* Production monitoring

The key principle is:

> **If the system cannot explain what happened, it is not sufficiently observable for reliable automation.**

---

## Related Documentation

* [Product Requirements](requirements/product-requirements.md)
* [System Architecture](architecture/system-architecture.md)
* [AWS Architecture](architecture/aws-architecture.md)
* [Incident Lifecycle](architecture/incident-lifecycle.md)
* [Configuration Strategy](configuration-strategy.md)

## Related Architecture Decisions

* [ADR-001: Repository Pattern](decisions/ADR-001-repository-pattern.md)
* [ADR-002: DynamoDB Persistence](decisions/ADR-002-dynamodb-persistence.md)
* [ADR-003: Human Approval Before Remediation](decisions/ADR-003-human-approval.md)
* [ADR-004: Conditional Write and Idempotency](decisions/ADR-004-conditional-write-idempotency.md)
