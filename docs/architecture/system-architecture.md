# CloudOps Autopilot

## System Architecture

**Document Version:** 1.0
**Status:** Architecture Foundation
**Primary Cloud:** AWS
**Primary Region:** `ap-south-1`
**Related Document:** `docs/requirements/product-requirements.md`

---

# 1. Purpose

This document defines the logical and technical architecture of CloudOps Autopilot.

The architecture is designed to support:

* Incident detection
* Evidence collection
* Diagnosis
* Risk assessment
* Remediation recommendation
* Human approval
* Controlled remediation
* Verification
* Incident persistence
* Future event-driven automation
* Future AI-assisted RCA
* Future productization

The architecture follows separation of concerns so that individual components can evolve independently.

---

# 2. Architectural Principles

CloudOps Autopilot follows these principles:

1. **Separation of Concerns**
2. **Least Privilege**
3. **Human-in-the-Loop**
4. **Fail Closed**
5. **Evidence-Based Decisions**
6. **Idempotent Operations**
7. **Explicit State Management**
8. **Persistence of Important State**
9. **Verification After Remediation**
10. **Observable Operations**
11. **Testable Components**
12. **Incremental Evolution**
13. **Infrastructure as Code**
14. **Security by Design**

---

# 3. High-Level Architecture

The logical architecture is:

```text
┌──────────────────────────────────────────────────────────────┐
│                      AWS Environment                         │
│                                                              │
│   EC2 / Application / Services / Infrastructure              │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            │ Metrics / Events / Health
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                     Observability Layer                      │
│                                                              │
│                      Amazon CloudWatch                       │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                    CloudOps Engine                           │
│                                                              │
│  ┌──────────────┐                                           │
│  │  Detection   │                                           │
│  └──────┬───────┘                                           │
│         ▼                                                    │
│  ┌──────────────┐                                           │
│  │   Evidence   │                                           │
│  └──────┬───────┘                                           │
│         ▼                                                    │
│  ┌──────────────┐                                           │
│  │  Diagnosis   │                                           │
│  └──────┬───────┘                                           │
│         ▼                                                    │
│  ┌──────────────┐                                           │
│  │ Risk Engine  │                                           │
│  └──────┬───────┘                                           │
│         ▼                                                    │
│  ┌──────────────────────┐                                   │
│  │ Recommendation       │                                   │
│  │ + Safety Guardrails  │                                   │
│  └──────────┬───────────┘                                   │
│             ▼                                                │
│      ┌──────────────┐                                        │
│      │   Approval   │                                        │
│      └──────┬───────┘                                        │
│             ▼                                                │
│      ┌──────────────┐                                        │
│      │ Remediation  │                                        │
│      └──────┬───────┘                                        │
│             ▼                                                │
│      ┌──────────────┐                                        │
│      │ Verification │                                        │
│      └──────┬───────┘                                        │
└─────────────┼────────────────────────────────────────────────┘
              │
              ▼
┌──────────────────────────────────────────────────────────────┐
│                     Persistence Layer                        │
│                                                              │
│                    Amazon DynamoDB                           │
└──────────────────────────────────────────────────────────────┘
```

---

# 4. Core Incident Flow

The primary operational flow is:

```text
AWS Signal
    ↓
Collect Telemetry
    ↓
Detect Incident
    ↓
Collect Evidence
    ↓
Diagnose
    ↓
Assess Risk
    ↓
Generate Recommendation
    ↓
Apply Safety Guardrails
    ↓
Human Approval
    ↓
Execute Remediation
    ↓
Verify Recovery
    ↓
Persist Final Result
```

Each stage has a distinct responsibility.

---

# 5. Architectural Components

## 5.1 AWS Environment

The AWS environment contains the resources being monitored.

Initial resource:

```text
Amazon EC2
```

Future resources may include:

* Application Load Balancers
* ECS services
* EKS workloads
* Lambda functions
* RDS
* Other AWS services

The CloudOps platform should monitor resources without tightly coupling the core engine to one specific resource type.

---

# 6. Observability Layer

## 6.1 Amazon CloudWatch

CloudWatch is the initial telemetry source.

The platform uses CloudWatch to obtain operational signals such as:

* CPU utilization
* Application error metrics
* Service health information

The initial implementation uses:

```text
AWS/EC2
CPUUtilization
```

for EC2 CPU detection.

---

# 7. Detection Layer

The Detection component determines whether available telemetry represents an incident.

Detection is intentionally separate from remediation.

```text
Telemetry
    ↓
Detection Rules
    ↓
Incident?
   / \
 NO   YES
 |     |
End   Continue
```

Detection rules support:

* Thresholds
* Time windows
* Consecutive breaches

Example:

```text
CPU > 90%
for 3 consecutive datapoints
```

A single temporary threshold breach should not automatically become a confirmed incident.

---

# 8. Evidence Layer

Once an incident is detected, relevant evidence is associated with the incident.

Evidence contains:

```text
source
signal
value
observed_at
description
```

Example:

```text
Source: CloudWatch
Signal: CPUUtilization
Value: 96.4%
Observed At: <timestamp>
Description: CPU exceeded configured threshold
```

Evidence provides the basis for downstream diagnosis.

---

# 9. Diagnosis Layer

The Diagnosis component determines the probable cause based on available evidence.

Current implementation supports high CPU diagnosis.

The diagnosis output contains:

```text
probable_cause
confidence
evidence
explanation
```

The diagnosis layer must not directly execute infrastructure changes.

Its responsibility is analysis.

```text
Evidence
   ↓
Diagnosis
   ↓
Probable Cause
   +
Confidence
   +
Explanation
```

---

# 10. Risk Assessment Layer

The Risk Assessment component evaluates the operational risk associated with the incident and potential response.

Current risk categories:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

Risk classification is an internal CloudOps Autopilot model.

It should not be interpreted as an AWS-wide severity standard.

Risk and incident severity are separate concepts.

```text
Incident Severity ≠ Remediation Risk
```

---

# 11. Recommendation Layer

The Recommendation component determines a proposed response.

The recommendation should consider:

* Incident type
* Diagnosis
* Evidence
* Risk
* Allowed actions
* Safety policy

Example:

```text
Incident:
HIGH_CPU

Diagnosis:
Sustained high CPU utilization

Risk:
LOW

Recommendation:
Collect additional diagnostic information
```

The recommendation is not automatically equivalent to permission to execute.

---

# 12. Safety Guardrail Layer

The Guardrail component determines whether the proposed action is permitted.

The current design uses an explicit allowlist.

```text
Recommendation
      ↓
Safety Validation
      ↓
 ┌────┴────┐
 ▼         ▼
ALLOW     BLOCK
```

An action may be blocked because:

* It is empty.
* It is not allowlisted.
* Its risk level is not permitted.
* Required approval is missing.
* The action violates policy.

The safety layer should fail closed.

---

# 13. Human Approval Layer

Human approval separates automated analysis from operational authority.

The intended flow is:

```text
Automated Analysis
       ↓
Recommendation
       ↓
Safety Validation
       ↓
Human Decision
    ↙       ↘
 APPROVE   REJECT
    ↓         ↓
Remediate    Stop
```

A recommendation does not grant execution authority.

This boundary is especially important when the platform begins performing real AWS-mutating actions.

---

# 14. Remediation Layer

The Remediation component executes approved actions.

The current implementation contains a structured executor operating in controlled/simulation mode.

The executor records:

```text
action
status
started_at
completed_at
message
error
```

Real AWS-mutating actions will be introduced only after:

* IAM permissions are designed
* Safety controls are established
* Approval controls are validated
* Idempotency is implemented
* Verification is available
* Failure handling is defined

---

# 15. Idempotency

Remediation operations must prevent accidental duplicate execution.

The current model identifies an execution using:

```text
incident_id + action
```

Example:

```text
INC-001:Collect additional diagnostic information
```

If the same action is attempted again for the same incident, the executor can return:

```text
SKIPPED
```

instead of executing the action again.

---

# 16. Verification Layer

Verification determines whether the incident condition actually recovered.

Important distinction:

```text
API call succeeded
        ≠
System recovered
```

For example:

```text
Remediation executed
        ↓
CPU checked again
        ↓
CPU below recovery threshold?
       / \
     YES  NO
      ↓    ↓
 RESOLVED INVESTIGATING
```

Verification therefore closes the operational loop.

---

# 17. Persistence Layer

Amazon DynamoDB is the initial persistence layer.

Table:

```text
cloudops-autopilot-incidents
```

Region:

```text
ap-south-1
```

Partition key:

```text
incident_id
```

Initial persisted attributes include:

```text
incident_id
incident_type
severity
resource
detected_at
status
description
```

Future versions will persist additional operational context.

---

# 18. Repository Layer

The application uses a Repository abstraction between business logic and persistence.

```text
Application Logic
       ↓
IncidentRepository
       ↓
 ┌─────┴─────────┐
 ▼               ▼
In-Memory      DynamoDB
Repository     Repository
```

This provides:

* Separation of concerns
* Testability
* Replaceable persistence implementation
* Reduced coupling between domain logic and AWS SDK

The repository interface defines:

```text
save()
get()
update()
```

---

# 19. Incident State Management

Incident state is controlled through an explicit lifecycle model.

Current states:

```text
DETECTED
ACKNOWLEDGED
INVESTIGATING
REMEDIATING
VERIFYING
RESOLVED
```

Valid transitions are controlled by the lifecycle model.

Example:

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

Invalid transitions are rejected.

---

# 20. Failure Path

The architecture must account for failures at every stage.

Example:

```text
Detection
   ↓
Diagnosis
   ↓
Risk
   ↓
Recommendation
   ↓
Approval
   ↓
Remediation
   ↓
Verification
```

Potential failures include:

* Missing CloudWatch data
* AWS API failure
* Diagnosis failure
* Persistence failure
* Approval rejection
* Guardrail rejection
* Remediation failure
* Verification failure

The platform should avoid assuming success.

---

# 21. Verification Failure

If remediation executes but verification fails:

```text
REMEDIATING
     ↓
VERIFYING
     ↓
Recovery Failed
     ↓
INVESTIGATING
```

The incident should remain active rather than being incorrectly marked as resolved.

---

# 22. Security Boundaries

Security boundaries exist between:

```text
AWS Resources
     ↓
Telemetry Access
     ↓
CloudOps Engine
     ↓
Decision / Policy Layer
     ↓
Remediation Permissions
```

The remediation layer should receive only the permissions required for approved actions.

Read-only monitoring permissions should not automatically imply write permissions.

---

# 23. IAM Architecture

The initial development environment separates monitoring access from future remediation authority.

Current monitoring access includes:

* CloudWatch read access
* EC2 read access

DynamoDB persistence uses explicit permissions for the incident table.

Future remediation should use a separate IAM role or execution identity with narrowly scoped permissions.

Conceptually:

```text
Monitoring Identity
       │
       ├── CloudWatch Read
       └── EC2 Read

Remediation Identity
       │
       └── Only explicitly approved AWS actions
```

This separation reduces blast radius.

---

# 24. Current vs Target Architecture

## Current

The current application primarily executes through the Python application engine.

```text
Python Application
      ↓
CloudWatch
      ↓
Detection
      ↓
Diagnosis
      ↓
Risk
      ↓
Approval
      ↓
Remediation Framework
      ↓
Verification
      ↓
DynamoDB
```

---

## Target

The future event-driven architecture is:

```text
AWS Resources
      ↓
CloudWatch
      ↓
CloudWatch Alarm
      ↓
EventBridge
      ↓
CloudOps Event Handler
      ↓
Incident Engine
      ↓
Diagnosis
      ↓
Risk / Policy
      ↓
Approval
      ↓
Remediation
      ↓
Verification
      ↓
DynamoDB
      ↓
Notification / Dashboard
```

This separation allows the current deterministic engine to evolve into an event-driven platform without replacing the core domain logic.

---

# 25. Future AWS Components

The architecture may progressively introduce:

## EventBridge

For event-driven incident ingestion.

## Lambda

For lightweight event processing and orchestration where appropriate.

## SNS

For notifications and approval-related communication.

## ECS

For long-running CloudOps engine workloads when required.

## ECR

For container image storage.

## Terraform

For reproducible infrastructure provisioning.

## CloudWatch Logs

For application and operational logs.

---

# 26. Future AI Architecture

AI will be introduced after the deterministic foundation is established.

Future flow:

```text
Metrics
Logs
Events
Deployments
Configuration
Historical Incidents
        ↓
AI-Assisted Analysis
        ↓
Possible Causes
        ↓
Confidence
        ↓
Risk / Policy Engine
        ↓
Approval
        ↓
Controlled Action
        ↓
Verification
```

The AI component should not have unrestricted infrastructure authority.

The architecture intentionally separates:

```text
AI = Analysis / Recommendation

Policy Engine = Authority

Human = Approval for protected actions

Executor = Controlled Operational Action
```

---

# 27. Scalability Model

The architecture should evolve from a single-resource prototype to a multi-resource platform.

Current:

```text
One AWS Account
      ↓
One EC2 Instance
```

Future:

```text
AWS Organization
      ↓
Multiple Accounts
      ↓
Multiple Environments
      ↓
Multiple Resources
      ↓
Multiple Incident Types
```

The core incident model should remain independent of individual AWS resource implementations.

---

# 28. Multi-Account Future Architecture

A future enterprise architecture may look like:

```text
                 CloudOps Control Plane
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
      AWS Account A  AWS Account B  AWS Account C
          │              │              │
        DEV            UAT            PROD
```

Each account should have controlled telemetry and remediation access.

Cross-account access should be based on explicitly defined IAM roles and trust relationships.

---

# 29. Observability Architecture

Future observability should provide:

```text
Application Logs
      +
Cloud Metrics
      +
Incident Metrics
      +
Remediation Metrics
      +
Audit Events
      ↓
Operational Visibility
```

Important operational metrics include:

* Incident count
* Detection latency
* Diagnosis latency
* Remediation duration
* Verification duration
* MTTR
* Remediation success rate
* Failed remediation rate
* Human intervention rate

---

# 30. Audit Architecture

Operationally significant actions should eventually generate audit records.

An audit event should answer:

```text
Who?
What?
When?
Why?
Which incident?
Which resource?
Which action?
What approval?
What result?
```

Future audit records should be designed for traceability and investigation.

---

# 31. Deployment Architecture

The project will progressively move from local development to automated deployment.

Target flow:

```text
Developer
    ↓
GitHub
    ↓
Pull Request
    ↓
Automated Tests
    ↓
Lint / Type / Security Checks
    ↓
Build
    ↓
Deploy
    ↓
AWS Environment
```

The exact deployment target will depend on the maturity of the CloudOps engine.

---

# 32. Environment Strategy

The future project should separate:

```text
DEV
 ↓
UAT
 ↓
PROD
```

Development resources should not automatically share production permissions.

Each environment should have appropriate:

* AWS resources
* IAM permissions
* Configuration
* Secrets
* Monitoring
* Deployment controls

---

# 33. Data Flow

The end-to-end logical data flow is:

```text
1. AWS resource generates telemetry
             ↓
2. CloudWatch receives/maintains telemetry
             ↓
3. Detection component evaluates signals
             ↓
4. Incident is created
             ↓
5. Evidence is attached
             ↓
6. Diagnosis analyzes evidence
             ↓
7. Risk engine evaluates response risk
             ↓
8. Recommendation engine proposes action
             ↓
9. Safety guardrails validate action
             ↓
10. Human approval is requested
             ↓
11. Approved action is executed
             ↓
12. System state is verified
             ↓
13. Incident state is updated
             ↓
14. Incident record is persisted
```

---

# 34. Component Responsibility Matrix

| Component            | Responsibility                                 |
| -------------------- | ---------------------------------------------- |
| CloudWatch Client    | Retrieve AWS telemetry                         |
| Detection            | Determine whether an incident condition exists |
| Evidence Model       | Represent supporting operational evidence      |
| Diagnosis            | Determine probable cause                       |
| Risk Engine          | Evaluate operational risk                      |
| Recommendation       | Propose remediation                            |
| Guardrails           | Determine whether an action is permitted       |
| Approval             | Capture human decision                         |
| Executor             | Execute permitted remediation                  |
| Idempotency Registry | Prevent duplicate execution                    |
| Verification         | Determine recovery                             |
| Incident Lifecycle   | Control valid state transitions                |
| Repository           | Abstract persistence                           |
| DynamoDB Repository  | Persist incidents                              |
| Main Orchestrator    | Coordinate the workflow                        |

---

# 35. Separation of Concerns

The architecture intentionally avoids placing all logic in a single application component.

Instead:

```text
AWS Access
    ≠
Detection
    ≠
Diagnosis
    ≠
Risk
    ≠
Recommendation
    ≠
Approval
    ≠
Remediation
    ≠
Verification
    ≠
Persistence
```

This makes individual components easier to:

* Test
* Replace
* Scale
* Secure
* Review
* Maintain

---

# 36. Architecture Evolution Strategy

The system will evolve incrementally.

### Stage 1

Local Python application.

### Stage 2

AWS-integrated incident engine.

### Stage 3

Persistent incident management.

### Stage 4

Event-driven architecture.

### Stage 5

Infrastructure as Code.

### Stage 6

CI/CD.

### Stage 7

Real controlled remediation.

### Stage 8

Advanced incident correlation.

### Stage 9

AI-assisted RCA.

### Stage 10

Multi-account/product architecture.

The architecture should avoid premature complexity while preserving clear boundaries for future growth.

---

# 37. Architectural Quality Criteria

Every major architectural change should be evaluated against:

```text
Does it work?
Does it remain safe?
Is it testable?
Is it maintainable?
Is it observable?
Is it auditable?
Can it scale?
Can we explain it?
Can it become a product capability?
```

---

# 38. Architecture Summary

CloudOps Autopilot follows a layered incident automation architecture:

```text
┌──────────────────────────────┐
│ AWS Resources                │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Telemetry / CloudWatch       │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Detection                    │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Evidence + Diagnosis         │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Risk + Recommendation        │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Safety + Human Approval      │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Controlled Remediation       │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Verification                 │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Incident Persistence         │
└──────────────────────────────┘
```

The architecture is intentionally designed so that automation does not bypass safety, policy, approval, or verification boundaries.

# 39. Event-Driven Architecture Boundary

Day 7 introduces the first application-level event boundary.

The event layer separates incoming operational events from the CloudOps incident processing logic.

Current implementation:

```text
Incoming Cloud Event
        ↓
CloudEvent
        ↓
Event Handler
        ↓
Supported Event Type