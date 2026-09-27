# CloudOps Autopilot

## Incident Lifecycle

**Document Version:** 1.0
**Status:** Architecture Foundation
**Related Documents:**

* `docs/requirements/product-requirements.md`
* `docs/architecture/system-architecture.md`
* `docs/architecture/aws-architecture.md`

---

# 1. Purpose

This document defines the lifecycle of an incident in CloudOps Autopilot.

The incident lifecycle provides a controlled state model from initial detection through investigation, remediation, verification, and resolution.

The lifecycle prevents arbitrary state changes and provides a consistent operational model for incident handling.

---

# 2. Lifecycle Overview

The standard lifecycle is:

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

If verification fails:

```text
VERIFYING
    ↓
INVESTIGATING
```

---

# 3. Why a State Machine Is Required

An incident is not simply a boolean condition.

For example:

```text
Incident = True
```

does not tell us:

* Whether somebody acknowledged it
* Whether it is being investigated
* Whether remediation is running
* Whether recovery has been verified
* Whether the incident is actually resolved

A state machine makes these stages explicit.

It prevents invalid transitions such as:

```text
DETECTED → RESOLVED
```

without completing the required operational stages.

---

# 4. Incident States

## 4.1 DETECTED

### Meaning

The system has identified a condition that satisfies the configured incident-detection rule.

Example:

```text
CPU > 90%
for 3 consecutive datapoints
```

### Responsibilities

At this stage the system should:

* Create the incident
* Generate an incident identifier
* Capture initial evidence
* Persist the incident
* Record detection time

### Allowed Transition

```text
DETECTED → ACKNOWLEDGED
```

---

# 5. ACKNOWLEDGED

### Meaning

The incident has been recognized and accepted for investigation.

Acknowledgement creates a clear boundary between detection and active investigation.

### Responsibilities

The system should:

* Record acknowledgement
* Preserve incident context
* Move the incident toward investigation

### Allowed Transition

```text
ACKNOWLEDGED → INVESTIGATING
```

---

# 6. INVESTIGATING

### Meaning

The incident is being analyzed to determine its probable cause and appropriate response.

Typical activities include:

* Evidence collection
* Metric analysis
* Diagnosis
* Confidence calculation
* Risk assessment
* Recommendation generation

Example:

```text
Incident:
HIGH_CPU

Evidence:
CPU = 96%
CPU = 97%
CPU = 95%

Diagnosis:
Sustained high CPU utilization
```

### Allowed Transition

```text
INVESTIGATING → REMEDIATING
```

This transition must occur only after the required safety and approval controls have been satisfied.

---

# 7. REMEDIATING

### Meaning

An approved remediation action is being executed.

Expected sequence:

```text
Recommendation
      ↓
Safety Guardrail
      ↓
Human Approval
      ↓
REMEDIATING
```

A recommendation alone does not authorize remediation.

### Allowed Transition

```text
REMEDIATING → VERIFYING
```

---

# 8. VERIFYING

### Meaning

A remediation action has been executed and the platform is checking whether the incident condition has recovered.

Example:

```text
Before:
CPU = 96%

Remediation:
Approved corrective action

After:
CPU = 60%
```

The platform must verify the actual system condition.

A successful API call does not automatically mean the system recovered.

```text
Action succeeded
       ≠
System recovered
```

### Allowed Transitions

Successful recovery:

```text
VERIFYING → RESOLVED
```

Recovery failure:

```text
VERIFYING → INVESTIGATING
```

---

# 9. RESOLVED

### Meaning

The original incident condition has been successfully verified as recovered.

The incident should retain its historical information, including:

* Incident details
* Evidence
* Diagnosis
* Risk
* Recommendation
* Approval
* Remediation result
* Verification result
* Relevant timestamps

The current implementation treats `RESOLVED` as a terminal state.

```text
RESOLVED → No further lifecycle transition
```

---

# 10. State Transition Model

```text
                 ┌──────────────────┐
                 │     DETECTED     │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │   ACKNOWLEDGED   │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │  INVESTIGATING   │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │   REMEDIATING    │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │    VERIFYING     │
                 └───────┬───┬──────┘
                         │   │
                    success failure
                         │   │
                         ↓   └─────────────┐
                 ┌──────────────┐          │
                 │   RESOLVED   │          │
                 └──────────────┘          │
                                           ↓
                                   INVESTIGATING
```

---

# 11. Valid Transition Matrix

| Current State | Allowed Next State |
| ------------- | ------------------ |
| DETECTED      | ACKNOWLEDGED       |
| ACKNOWLEDGED  | INVESTIGATING      |
| INVESTIGATING | REMEDIATING        |
| REMEDIATING   | VERIFYING          |
| VERIFYING     | RESOLVED           |
| VERIFYING     | INVESTIGATING      |
| RESOLVED      | None               |

Invalid transitions must be rejected.

Examples:

```text
DETECTED → RESOLVED
DETECTED → REMEDIATING
RESOLVED → INVESTIGATING
RESOLVED → REMEDIATING
```

---

# 12. Lifecycle and Detection

Detection creates the initial incident state:

```text
AWS Telemetry
      ↓
Detection Rule
      ↓
Incident Created
      ↓
DETECTED
```

Detection must not directly initiate infrastructure remediation.

This maintains separation between:

```text
Detection
```

and:

```text
Action
```

---

# 13. Lifecycle and Evidence

Evidence is collected during detection and investigation.

Example:

```text
CloudWatch
    ↓
CPU = 96%
    ↓
Evidence
    ↓
Incident
```

Evidence should include:

* Source
* Signal
* Value
* Timestamp
* Description

Evidence provides the foundation for diagnosis.

---

# 14. Lifecycle and Diagnosis

Diagnosis primarily occurs while the incident is in:

```text
INVESTIGATING
```

Diagnosis should produce:

* Probable cause
* Confidence
* Supporting evidence
* Explanation

Diagnosis should not directly modify AWS resources.

---

# 15. Lifecycle and Risk

Risk assessment occurs before remediation.

```text
INVESTIGATING
      ↓
Diagnosis
      ↓
Risk Assessment
      ↓
Recommendation
```

Risk classification determines whether the proposed action can proceed through the safety controls.

Risk is distinct from incident severity.

```text
Incident Severity ≠ Remediation Risk
```

---

# 16. Lifecycle and Recommendation

The recommendation engine proposes an action based on:

* Incident type
* Evidence
* Diagnosis
* Risk
* Approved actions
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

The recommendation is not execution authority.

---

# 17. Lifecycle and Guardrails

Before remediation:

```text
Recommendation
      ↓
Guardrail Validation
```

Possible outcomes:

```text
ALLOW
```

or:

```text
BLOCK
```

An action can be blocked when:

* The action is empty
* The action is not allowlisted
* Risk is not permitted
* Required approval is missing
* A policy constraint is violated

The safety model follows a fail-closed approach.

---

# 18. Lifecycle and Human Approval

Protected remediation actions require explicit human approval.

```text
INVESTIGATING
      ↓
Recommendation
      ↓
Safety Validation
      ↓
Human Approval
    ↙       ↘
APPROVE    REJECT
   ↓          ↓
REMEDIATING  Stop
```

The system must not execute the protected action when approval is rejected.

---

# 19. Lifecycle and Idempotency

Remediation actions must be protected against duplicate execution.

The current execution identity is based on:

```text
incident_id + action
```

Example:

```text
INC-001 + Collect additional diagnostic information
```

If the same action is requested again for the same incident, the executor can return:

```text
SKIPPED
```

instead of executing the same action again.

---

# 20. Lifecycle and Persistence

Important lifecycle changes should be persisted.

Example:

```text
DETECTED
   ↓
DynamoDB
   ↓
ACKNOWLEDGED
   ↓
DynamoDB
   ↓
INVESTIGATING
   ↓
DynamoDB
   ↓
REMEDIATING
   ↓
DynamoDB
   ↓
VERIFYING
   ↓
DynamoDB
   ↓
RESOLVED
   ↓
DynamoDB
```

This prevents important state from existing only in application memory.

---

# 21. Failure Scenarios

## 21.1 Insufficient Detection Data

If reliable telemetry is unavailable, the system should not create an unsupported incident solely because data is missing.

---

## 21.2 Insufficient Diagnosis Evidence

If evidence is insufficient:

```text
Confidence = 0
```

or another explicitly defined low-confidence outcome should be produced.

The system should not invent a probable cause.

---

## 21.3 Guardrail Rejection

```text
Recommendation
      ↓
Guardrail
      ↓
BLOCKED
```

The action must not execute.

---

## 21.4 Approval Rejection

```text
Recommendation
      ↓
Human
      ↓
REJECTED
      ↓
No Remediation
```

The incident remains unresolved.

---

## 21.5 Remediation Failure

If remediation fails:

```text
REMEDIATING
      ↓
Execution Failed
```

The system must not mark the incident as resolved.

Future implementation should define retry and escalation behavior.

---

## 21.6 Verification Failure

If remediation executes but the original condition remains:

```text
VERIFYING
      ↓
Recovery Failed
      ↓
INVESTIGATING
```

The incident remains active.

---

# 22. Safety Rules

The lifecycle follows these core rules:

### Rule 1

```text
DETECTED ≠ REMEDIATING
```

### Rule 2

Diagnosis must be evidence-based.

### Rule 3

Risk must be evaluated before protected remediation.

### Rule 4

Protected actions require approval.

### Rule 5

Duplicate remediation must be prevented.

### Rule 6

Successful execution does not equal successful recovery.

### Rule 7

An incident must be verified before entering `RESOLVED`.

### Rule 8

When safety cannot be established, the system should fail closed.

---

# 23. Incident Record

Current incident information:

```text
incident_id
incident_type
severity
resource
detected_at
status
description
```

Future lifecycle information may include:

```text
evidence
diagnosis
confidence
risk
recommendation
approval
remediation_result
verification_result
audit_events
```

---

# 24. Audit Requirements

Each important lifecycle transition should eventually be traceable.

An audit event should contain information such as:

```text
incident_id
previous_state
new_state
timestamp
actor
reason
```

Possible actors:

```text
SYSTEM
HUMAN
AUTOMATION
```

Human approval events should identify the authorized approval actor according to the future identity and audit design.

---

# 25. Current Implementation

The lifecycle is implemented in:

```text
src/cloudops_engine/models/incident.py
src/cloudops_engine/models/incident_lifecycle.py
```

The lifecycle uses an explicit transition map.

Current transition model:

```python
VALID_TRANSITIONS = {
    "DETECTED": {"ACKNOWLEDGED"},
    "ACKNOWLEDGED": {"INVESTIGATING"},
    "INVESTIGATING": {"REMEDIATING"},
    "REMEDIATING": {"VERIFYING"},
    "VERIFYING": {"RESOLVED", "INVESTIGATING"},
    "RESOLVED": set(),
}
```

The `Incident` model delegates transition validation to the lifecycle component.

---

# 26. Testing Requirements

The lifecycle must be tested for valid transitions.

### Valid

```text
DETECTED → ACKNOWLEDGED
ACKNOWLEDGED → INVESTIGATING
INVESTIGATING → REMEDIATING
REMEDIATING → VERIFYING
VERIFYING → RESOLVED
VERIFYING → INVESTIGATING
```

### Invalid

```text
DETECTED → RESOLVED
DETECTED → REMEDIATING
ACKNOWLEDGED → RESOLVED
RESOLVED → INVESTIGATING
RESOLVED → REMEDIATING
```

Persistence tests should verify that lifecycle state changes remain correct after writing to and reading from DynamoDB.

---

# 27. Future Lifecycle Enhancements

Future versions may introduce states such as:

```text
SUPPRESSED
CANCELLED
ESCALATED
REOPENED
```

These should only be introduced when their operational semantics are clearly defined.

The lifecycle should remain as simple as possible while supporting required operational behavior.

---

# 28. End-to-End Lifecycle Example

Consider a high CPU incident.

### Step 1 — Detection

```text
CPU = 96%
CPU = 97%
CPU = 95%
```

Detection rule is satisfied.

State:

```text
DETECTED
```

### Step 2 — Acknowledgement

State:

```text
ACKNOWLEDGED
```

### Step 3 — Investigation

Evidence is analyzed.

State:

```text
INVESTIGATING
```

Diagnosis:

```text
Sustained high CPU utilization
```

### Step 4 — Risk

Risk is assessed.

```text
LOW
```

### Step 5 — Recommendation

A permitted action is recommended.

### Step 6 — Approval

Human approval is obtained.

### Step 7 — Remediation

State:

```text
REMEDIATING
```

### Step 8 — Verification

State:

```text
VERIFYING
```

CPU after remediation:

```text
60%
```

### Step 9 — Resolution

State:

```text
RESOLVED
```

Final incident information is persisted.

---

# 29. Lifecycle Design Principle

The incident lifecycle is designed around one important operational rule:

> **An incident is resolved only when recovery has been verified.**

Therefore:

```text
Detection
    ↓
Decision
    ↓
Action
    ↓
Verification
    ↓
Resolution
```

The verification step is mandatory for a successful remediation workflow.

---

# 30. Summary

CloudOps Autopilot uses an explicit state machine to control incident progression.

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

Verification failure returns the incident to investigation.

The lifecycle provides:

* Controlled state transitions
* Clear operational responsibility
* Safety boundaries
* Persistence
* Auditability
* Testability
* Consistent incident handling

This lifecycle becomes the foundation for future event-driven automation, real remediation, AI-assisted RCA, and product-level incident management.

````

Save chesi:

```bash
git status
````

Then:

```bash
git add docs/architecture/incident-lifecycle.md
git commit -m "docs: define incident lifecycle"
git push
```

### Current documentation progress

```text
✅ Product Requirements
✅ Professional README
✅ System Architecture
✅ AWS Architecture
✅ Incident Lifecycle
⬜ ADR-001 Repository Pattern
⬜ ADR-002 DynamoDB Persistence
⬜ ADR-003 Human Approval
⬜ ADR-004 Idempotency
⬜ Research Documentation
⬜ Configuration Strategy
⬜ Logging & Observability
⬜ Error Handling & Reliability
⬜ Security
⬜ Testing Strategy
...
```

**Next item: ADR-001 — Repository Pattern.**
