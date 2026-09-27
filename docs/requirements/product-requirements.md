# CloudOps Autopilot

## Product Requirements & Product Definition

**Document Version:** 1.0
**Project Status:** Foundation / MVP Development
**Repository:** `cloudops-autopilot`
**Primary Region:** `ap-south-1`
**Document Purpose:** Define the product, engineering, research, safety, and business requirements for CloudOps Autopilot.

---

# 1. Product Overview

CloudOps Autopilot is a risk-aware cloud operations platform designed to detect, diagnose, assess, recommend, safely remediate, and verify cloud incidents.

The platform is intended to reduce the amount of repetitive manual work involved in cloud incident response while maintaining human control over potentially risky operational actions.

The core operational flow is:

**Detect → Diagnose → Assess Risk → Recommend → Approve → Remediate → Verify → Record**

The initial implementation targets AWS environments and focuses on controlled incident scenarios such as:

* High CPU utilization
* Unhealthy services
* Application 5xx error spikes

The system will initially operate with deterministic rules and controlled remediation. AI-assisted Root Cause Analysis (RCA) is planned as a future capability.

---

# 2. Problem Statement

Modern cloud environments generate large volumes of operational signals including:

* Metrics
* Logs
* Events
* Health checks
* Deployment information
* Infrastructure state
* Application errors

When an incident occurs, engineers often need to manually:

1. Detect the issue.
2. Collect relevant evidence.
3. Identify the probable cause.
4. Determine severity and risk.
5. Decide what action should be taken.
6. Execute the remediation.
7. Verify whether the system recovered.
8. Record what happened.

This process can be slow, inconsistent, and difficult to audit.

CloudOps Autopilot aims to provide a controlled automation framework that assists with these activities while preventing unsafe or unauthorized remediation.

---

# 3. Product Vision

The long-term vision is to build an intelligent and risk-aware CloudOps platform capable of assisting engineering teams with incident response across cloud environments.

The platform should eventually be able to:

* Detect incidents automatically.
* Correlate multiple operational signals.
* Diagnose probable causes.
* Explain the evidence supporting a diagnosis.
* Assess remediation risk.
* Recommend appropriate actions.
* Request human approval for risky actions.
* Execute approved remediation.
* Verify recovery.
* Maintain an auditable incident history.
* Learn from historical incident data.
* Support AI-assisted RCA.
* Support controlled low-risk autonomous remediation.

The core principle is:

> **Automation should be explainable, controlled, and verifiable.**

---

# 4. Product Goals

## 4.1 Primary Goals

### Goal 1 — Automated Incident Detection

Detect predefined cloud incidents using measurable operational signals.

Examples:

* High CPU utilization
* Application 5xx errors
* Unhealthy service state

---

### Goal 2 — Evidence-Based Diagnosis

Use collected evidence to determine the probable cause of an incident.

The system should not simply report:

> "CPU is high."

It should provide:

* Observed signal
* Signal value
* Time of observation
* Evidence count
* Probable cause
* Confidence
* Explanation

---

### Goal 3 — Risk-Aware Remediation

Before executing an operational action, the system must determine whether the action is permitted.

The remediation flow must consider:

* Action type
* Risk level
* Allowlisted actions
* Approval requirements
* Idempotency
* Safety constraints

---

### Goal 4 — Human-Controlled Automation

Human approval must be required for remediation actions that can potentially affect production resources.

The system must not provide unrestricted AWS access to an automated decision component.

---

### Goal 5 — Verification

Every remediation action must be followed by verification.

The platform must determine whether the original incident condition has actually recovered.

Example:

```text
High CPU detected
       ↓
Remediation executed
       ↓
CPU checked again
       ↓
Recovered?
   ↙       ↘
 YES        NO
 ↓           ↓
RESOLVED   INVESTIGATING
```

---

### Goal 6 — Persistent Incident History

Incident information must be persisted so that the platform can maintain historical operational records.

The system should record:

* Incident identity
* Incident type
* Severity
* Resource
* Detection time
* Current state
* Description
* Diagnosis
* Remediation
* Verification result
* Future audit information

---

### Goal 7 — Research Measurement

The platform must support measurable evaluation.

Important metrics include:

* Detection time
* Diagnosis accuracy
* Mean Time To Recovery (MTTR)
* Remediation success rate
* False-positive rate
* Unsafe-action prevention rate
* Human intervention rate
* Verification accuracy

---

# 5. Product Scope

## 5.1 MVP Scope

The initial MVP includes:

1. AWS monitoring integration
2. CloudWatch metric collection
3. Incident detection
4. Evidence collection
5. Incident diagnosis
6. Risk assessment
7. Remediation recommendation
8. Safety guardrails
9. Human approval
10. Remediation execution framework
11. Verification
12. Incident lifecycle management
13. DynamoDB persistence
14. Automated testing
15. Git-based version control

---

# 6. Initial Incident Types

## 6.1 High CPU

Condition:

```text
CPU > configured threshold
for configured consecutive datapoints
```

Initial example:

```text
CPU > 90%
for 3 consecutive datapoints
```

The actual threshold must remain configurable.

---

## 6.2 Application 5xx Spike

Condition:

```text
5xx error rate > configured threshold
for configured consecutive datapoints
```

The system should avoid treating a single short-lived spike as a confirmed incident.

---

## 6.3 Unhealthy Service

Condition:

```text
Service health check = unhealthy
for configured consecutive checks
```

The detection mechanism should support persistence requirements to reduce false positives.

---

# 7. Incident Lifecycle

The standard internal lifecycle is:

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
   ↓
CLOSED
```

Verification failure may return an incident to:

```text
VERIFYING → INVESTIGATING
```

The lifecycle must prevent invalid state transitions.

---

# 8. Functional Requirements

## FR-001 — Metric Collection

The platform shall collect required AWS operational metrics.

Initial source:

```text
Amazon CloudWatch
```

---

## FR-002 — Incident Detection

The platform shall detect configured incident conditions.

Detection rules must support configurable:

* Threshold
* Time window
* Required consecutive breaches

---

## FR-003 — Evidence Collection

The platform shall associate relevant evidence with a detected incident.

Evidence should contain:

* Source
* Signal
* Value
* Timestamp
* Description

---

## FR-004 — Diagnosis

The platform shall generate a probable cause based on available evidence.

The diagnosis shall include:

* Probable cause
* Confidence
* Supporting evidence
* Explanation

---

## FR-005 — Risk Assessment

The platform shall evaluate the operational risk associated with a recommended action.

Initial risk categories:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

These categories are internal product classifications and are not intended to represent a universal AWS severity standard.

---

## FR-006 — Recommendation

The platform shall generate a remediation recommendation based on:

* Incident type
* Diagnosis
* Risk
* Available evidence
* Approved remediation policies

---

## FR-007 — Safety Guardrails

The platform shall prevent actions that violate configured safety policies.

Examples:

* Empty action
* Unknown action
* Unapproved action
* Excessive risk
* Missing approval

---

## FR-008 — Human Approval

The platform shall support explicit human approval before executing protected remediation actions.

The approval decision must be distinguishable from the automated recommendation.

---

## FR-009 — Remediation

The platform shall execute only approved and permitted remediation actions.

The initial implementation may operate in simulation mode before real AWS-mutating actions are enabled.

---

## FR-010 — Idempotency

The platform shall prevent accidental duplicate execution of the same remediation action for the same incident.

The system must be able to identify:

```text
incident + action
```

as a unique execution context.

---

## FR-011 — Verification

The platform shall verify whether the incident condition recovered after remediation.

Verification must produce an explicit result.

---

## FR-012 — Incident Persistence

The platform shall persist incident information in durable storage.

Initial persistence layer:

```text
Amazon DynamoDB
```

---

## FR-013 — Incident State Updates

The platform shall persist lifecycle state changes.

Example:

```text
DETECTED
→ ACKNOWLEDGED
→ INVESTIGATING
→ REMEDIATING
→ VERIFYING
→ RESOLVED
```

---

## FR-014 — Historical Records

The platform shall maintain historical incident information for future:

* Analysis
* Reporting
* Research
* Auditing
* Product analytics
* AI-assisted RCA

---

# 9. Non-Functional Requirements

## NFR-001 — Security

The platform shall follow least-privilege access principles.

AWS permissions shall be limited to the resources and actions required by each component.

---

## NFR-002 — Safety

Automated remediation shall be constrained by:

* Allowlisted actions
* Risk policies
* Approval controls
* Idempotency
* Verification

---

## NFR-003 — Explainability

The platform shall be able to explain:

* What happened?
* What evidence was observed?
* What was the probable cause?
* Why was the action recommended?
* What risk was identified?
* Who approved the action?
* What action was executed?
* Did the system recover?

---

## NFR-004 — Reliability

The system shall handle expected operational failures such as:

* AWS API failures
* Missing metrics
* Invalid configuration
* Duplicate actions
* Persistence failures
* Verification failures

Future implementations shall introduce appropriate:

* Timeouts
* Retries
* Backoff
* Failure handling
* Recovery mechanisms

---

## NFR-005 — Observability

The platform shall provide sufficient operational visibility through:

* Structured logs
* Incident identifiers
* Action identifiers
* Metrics
* Audit records
* CloudWatch integration

---

## NFR-006 — Testability

Core components shall be independently testable.

The project shall maintain:

* Unit tests
* Integration tests
* Regression tests
* End-to-end tests in later stages
* Failure scenario tests

---

## NFR-007 — Maintainability

The system shall use modular architecture with clear separation of responsibilities.

Examples:

```text
Detection
Diagnosis
Risk
Recommendation
Approval
Remediation
Verification
Persistence
```

Each component should have a clear responsibility.

---

## NFR-008 — Scalability

The architecture should support expansion from:

```text
1 incident type
```

to:

```text
multiple incident types
multiple AWS resources
multiple AWS accounts
multiple environments
```

without requiring a complete redesign.

---

## NFR-009 — Auditability

Operationally significant decisions and actions should eventually be traceable.

The audit model should answer:

```text
What happened?
When did it happen?
Why did it happen?
What decision was made?
Who approved it?
What changed?
What was the result?
```

---

## NFR-010 — Configuration

Operational configuration should not be hardcoded into application logic.

Examples:

* AWS region
* Thresholds
* Detection windows
* Resource identifiers
* Environment
* Feature flags

---

# 10. Safety Requirements

Safety is a core product requirement.

The platform must follow these principles:

## Safety Principle 1 — Detect Before Acting

Detection must be logically separated from remediation.

```text
Detection ≠ Remediation
```

---

## Safety Principle 2 — Diagnose Before Recommending

The platform should collect sufficient evidence before generating a remediation recommendation.

---

## Safety Principle 3 — Risk Before Action

A remediation action must pass risk and policy checks.

---

## Safety Principle 4 — Human Control

Risky operational actions require human approval.

---

## Safety Principle 5 — Idempotency

Repeated events must not unintentionally execute the same remediation multiple times.

---

## Safety Principle 6 — Verify After Action

A remediation action is not considered successful merely because the API call succeeded.

The system must verify the actual system state.

---

## Safety Principle 7 — Fail Closed

When the system cannot confidently determine whether an action is safe, it should avoid executing the action.

---

# 11. Security Requirements

The system shall follow:

* Least privilege
* Separation of duties
* Explicit IAM permissions
* No unnecessary root access
* Secure secret handling
* Encryption where applicable
* Auditability
* Controlled remediation permissions

Automated components must not receive unrestricted administrative AWS permissions.

---

# 12. Data Requirements

The platform shall maintain structured incident data.

Initial incident attributes:

```text
incident_id
incident_type
severity
resource
detected_at
status
description
```

Future incident data may include:

```text
evidence
diagnosis
confidence
risk
recommendation
approval
remediation
verification
audit events
```

The data model must evolve without breaking existing incident records.

---

# 13. Research Requirements

CloudOps Autopilot is also intended to serve as a research project.

## Research Question

> Can a risk-aware cloud incident remediation framework safely automate selected remediation tasks while reducing recovery time and unnecessary human intervention?

The research must evaluate both:

### Automation effectiveness

and

### Automation safety

The project must not evaluate automation only by speed.

---

# 14. Research Hypothesis

A risk-aware incident automation framework that combines evidence-based diagnosis, safety guardrails, human approval, controlled remediation, and post-action verification can reduce incident recovery effort while limiting unsafe remediation actions.

This hypothesis will be evaluated experimentally rather than assumed to be true.

---

# 15. Research Metrics

The platform should support measurement of:

| Metric                   | Purpose                                        |
| ------------------------ | ---------------------------------------------- |
| Detection Time           | Measure how quickly an incident is identified  |
| Diagnosis Accuracy       | Measure correctness of probable-cause analysis |
| MTTR                     | Measure recovery time                          |
| Remediation Success Rate | Measure successful actions                     |
| False-Positive Rate      | Measure incorrect incident detection           |
| Unsafe-Action Rate       | Measure prevented/incorrect risky actions      |
| Human Intervention Rate  | Measure required manual involvement            |
| Verification Accuracy    | Measure correctness of recovery determination  |

---

# 16. Business/Product Requirements

CloudOps Autopilot should be designed so that it can eventually evolve from a portfolio/research system into a real cloud operations product.

Potential target users include:

* DevOps teams
* SRE teams
* Cloud operations teams
* Platform engineering teams
* Startups operating AWS infrastructure
* Organizations with small cloud operations teams

Potential product value:

```text
Lower operational effort
        +
Faster incident response
        +
Controlled automation
        +
Explainable decisions
        +
Auditability
```

The product must prioritize trust and safety rather than unrestricted automation.

---

# 17. Future Product Capabilities

Potential future capabilities include:

### Multi-Account AWS Support

```text
AWS Organization
   ├── Account A
   ├── Account B
   ├── Account C
   └── Account D
```

---

### Multi-Environment Support

```text
DEV
UAT
PROD
```

---

### AI-Assisted RCA

AI may later analyze:

* Metrics
* Logs
* Events
* Deployments
* Configuration
* Historical incidents

AI output should be treated as analysis/recommendation, not unrestricted authority.

---

### Controlled Autonomous Remediation

Low-risk actions may eventually be automated without manual approval when:

* Policy permits it
* Risk is low
* Action is allowlisted
* Idempotency is guaranteed
* Verification is available
* Rollback is possible where applicable

---

# 18. Explicit Non-Goals

The following are not initial MVP goals:

## NG-001 — Fully Autonomous Production Operations

The first version will not attempt unrestricted autonomous cloud administration.

---

## NG-002 — Unrestricted AI Access

AI components will not receive unrestricted AWS permissions.

---

## NG-003 — Immediate Multi-Cloud Support

AWS is the initial cloud platform.

Other clouds may be considered later.

---

## NG-004 — Automatic Remediation of Every Incident

Only explicitly supported and controlled remediation actions will be eligible.

---

## NG-005 — Replacing Engineers

The platform is intended to assist engineers and reduce repetitive operational work.

It is not initially intended to eliminate human operational responsibility.

---

# 19. MVP Success Criteria

The MVP will be considered technically successful when it can demonstrate:

```text
AWS Signal
   ↓
Incident Detection
   ↓
Evidence Collection
   ↓
Diagnosis
   ↓
Risk Assessment
   ↓
Recommendation
   ↓
Safety Validation
   ↓
Human Approval
   ↓
Controlled Remediation
   ↓
Verification
   ↓
Persistent Incident Record
```

The implementation must be:

* Tested
* Explainable
* Auditable
* Safe by default
* Version controlled
* Documented

---

# 20. Engineering Principles

CloudOps Autopilot shall follow these core engineering principles:

1. **Security by Design**
2. **Least Privilege**
3. **Fail Closed**
4. **Human-in-the-Loop**
5. **Evidence-Based Decisions**
6. **Idempotent Operations**
7. **Separation of Concerns**
8. **Testability**
9. **Observability**
10. **Auditability**
11. **Infrastructure as Code**
12. **Automation with Verification**
13. **Explicit Architecture Decisions**
14. **Incremental Delivery**
15. **Measurable Outcomes**

---

# 21. Product Evolution

The project will evolve through the following stages:

```text
Stage 1
Core Detection
        ↓
Stage 2
Diagnosis
        ↓
Stage 3
Risk & Safety
        ↓
Stage 4
Controlled Remediation
        ↓
Stage 5
Event-Driven Automation
        ↓
Stage 6
Infrastructure as Code
        ↓
Stage 7
CI/CD & Production Engineering
        ↓
Stage 8
Advanced Incident Correlation
        ↓
Stage 9
AI-Assisted RCA
        ↓
Stage 10
Controlled Autonomous Operations
        ↓
Stage 11
Multi-Account / SaaS Product
```

---

# 22. Current Implementation Status

As of Version 1.0 of this requirements document:

### Implemented

* AWS CloudWatch monitoring
* EC2 CPU detection
* Evidence model
* Diagnosis model
* Risk assessment
* Recommendation
* Safety guardrails
* Human approval flow
* Remediation framework
* Idempotency protection
* Verification
* Incident lifecycle
* DynamoDB persistence
* Unit testing
* Integration testing
* Git/GitHub version control
* Least-privilege AWS access for implemented read/persistence functionality

### Planned

* EventBridge integration
* Real remediation actions
* Terraform
* CI/CD
* Structured logging
* Advanced observability
* Security hardening
* Advanced testing
* Application 5xx detection integration
* Unhealthy service detection integration
* AI-assisted RCA
* Dashboard
* Research evaluation
* Multi-account architecture
* SaaS/business architecture

---

# 23. Requirement Traceability Principle

Every major implementation feature should be traceable to one or more requirements.

Example:

```text
Requirement
    ↓
Architecture Decision
    ↓
Implementation
    ↓
Test
    ↓
Operational Evidence
```

This ensures that the project remains aligned with its original product, engineering, and research objectives.

---

# 24. Definition of Done

A major feature should not be considered complete merely because its code works.

A feature should progressively satisfy:

```text
Works
  ↓
Safe
  ↓
Testable
  ↓
Maintainable
  ↓
Observable
  ↓
Auditable
  ↓
Scalable
  ↓
Explainable
  ↓
Productizable
```

The exact level required depends on the project's current maturity and environment.

---

# 25. Document Ownership

This document is the primary product-definition reference for CloudOps Autopilot.

When future implementation decisions conflict with these requirements, the requirements should be reviewed before changing the architecture or implementation.

Major changes to product scope, safety model, research objectives, or business direction should be documented as explicit project decisions.
