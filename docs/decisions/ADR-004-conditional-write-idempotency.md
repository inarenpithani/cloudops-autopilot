# ADR-004: Conditional Write and Idempotency

## Status

Accepted

## Date

2026-09-27

## Context

CloudOps Autopilot is an incident automation platform that can detect incidents, diagnose probable causes, recommend remediation actions, execute approved actions, and verify recovery.

Automation systems can encounter duplicate events, retries, network failures, process restarts, and concurrent execution attempts.

Without appropriate protection, the same incident or remediation action could be processed multiple times.

For example:

```text
Incident Detected
      ↓
Remediation Approved
      ↓
Action Executed
      ↓
Network Timeout
      ↓
System Retries
      ↓
Same Action Executed Again
```

If the remediation action is not idempotent, the retry could produce an unintended second infrastructure change.

CloudOps Autopilot therefore requires protection against duplicate incident creation and duplicate remediation execution.

---

## Problem

The system must safely handle situations where:

* The same incident event is received more than once.
* An application retries an operation.
* A network timeout occurs after an action has been executed.
* Multiple processes attempt to create the same incident.
* A remediation request is submitted more than once.
* An event-processing component restarts.
* An asynchronous AWS event is delivered again.

The system must distinguish between:

```text
New operation
```

and:

```text
Repeated execution of an existing operation
```

---

## Decision

CloudOps Autopilot will use **two complementary mechanisms**:

1. **DynamoDB conditional writes** for duplicate incident creation protection.
2. **Application-level idempotency tracking** for remediation action execution.

These mechanisms operate at different layers.

```text
Incident Persistence
        ↓
DynamoDB Conditional Write
        ↓
Prevent Duplicate Incident

Remediation Execution
        ↓
Idempotency Registry
        ↓
Prevent Duplicate Action
```

---

## Decision Drivers

The decision is based on:

* Safety
* Duplicate-event protection
* Retry safety
* Concurrency control
* Data consistency
* Remediation safety
* Failure recovery
* Auditability
* Simplicity
* AWS-native capabilities

---

# Part 1 — Conditional Write for Incident Creation

## Duplicate Incident Problem

CloudOps Autopilot may receive the same incident more than once.

For example:

```text
CloudWatch Event
      ↓
Event Processing
      ↓
Incident INC-001
```

The same event could potentially be delivered again:

```text
CloudWatch Event
      ↓
Retry / Duplicate Delivery
      ↓
Incident INC-001
```

Without duplicate protection, the second request could overwrite or recreate the same incident.

---

## Decision

The DynamoDB repository uses a conditional write when creating a new incident.

The current implementation uses:

```python
ConditionExpression="attribute_not_exists(incident_id)"
```

This means the incident is created only when the specified `incident_id` does not already exist.

Conceptually:

```text
Create Incident
      ↓
Does incident_id exist?
      ↓
 ┌────┴────┐
 No        Yes
 ↓          ↓
Create     Reject
```

---

## Why Database-Level Protection

Application-only duplicate checking can introduce a race condition.

Unsafe pattern:

```text
Process A → Check → Not Found
Process B → Check → Not Found
Process A → Create
Process B → Create
```

Both processes may observe that the record does not exist.

The database should therefore enforce the condition atomically.

With DynamoDB:

```text
Process A ──┐
            ├── Conditional Write
Process B ──┘
                 ↓
        Only one valid creation
```

This makes the persistence layer responsible for enforcing the uniqueness condition.

---

## Duplicate Incident Behavior

If an incident with the same identifier already exists, the repository raises an error indicating that the incident already exists.

The system must not silently overwrite the existing incident during initial creation.

This protects incident history and prevents accidental duplicate records.

---

# Part 2 — Remediation Idempotency

## Why Remediation Needs Idempotency

Incident remediation can be more sensitive than ordinary data operations.

Consider an action such as:

```text
Restart service
```

If the same action is accidentally executed twice, the second execution may have additional operational impact.

For some actions, duplicate execution may be harmless.

For others, it may:

* Cause service interruption
* Modify capacity multiple times
* Trigger repeated configuration changes
* Produce additional costs
* Create inconsistent infrastructure state

Therefore, remediation execution requires explicit duplicate-action protection.

---

## Decision

The current remediation executor uses an `IdempotencyRegistry`.

The registry tracks:

```text
incident_id + action
```

as a unique execution key.

Example:

```text
INC-001:Collect additional metrics and investigate the top CPU-consuming processes.
```

If the same incident and action combination is submitted again, the executor detects that the action has already been executed.

---

## Idempotency Flow

```text
Remediation Request
        ↓
Build Idempotency Key
        ↓
Has this action executed?
       / \
     Yes  No
      ↓    ↓
   SKIP   Execute
           ↓
      Mark Executed
```

---

## Current Implementation

The current implementation builds the key using:

```python
f"{incident_id}:{action}"
```

The registry maintains executed action keys.

Conceptually:

```text
Executed Actions

INC-001:Action-A
INC-002:Action-B
INC-003:Action-C
```

When a duplicate request arrives:

```text
INC-001:Action-A
```

the executor returns:

```text
status = SKIPPED
```

instead of executing the action again.

---

## Idempotency Result States

The remediation executor currently supports:

### SUCCESS

The action has not previously been executed and is accepted for execution.

### SKIPPED

The same incident/action combination has already been executed.

### FAILED

The requested action is invalid, such as an empty action.

Conceptually:

```text
Action Request
      ↓
Validation
      ↓
Idempotency Check
      ↓
 ┌────┼─────┐
 ↓    ↓     ↓
FAIL SKIP SUCCESS
```

---

# Why Idempotency and Approval Are Different

Human approval and idempotency solve different problems.

### Human Approval

Answers:

> **Is this action authorized?**

### Idempotency

Answers:

> **Has this exact action already been executed?**

Therefore:

```text
Authorization ≠ Idempotency
```

Both controls are required.

Example:

```text
Recommendation
      ↓
Guardrails
      ↓
Human Approval
      ↓
Idempotency Check
      ↓
Execute
```

---

# Relationship With Guardrails

Guardrails determine whether an action is allowed.

Idempotency determines whether the allowed action has already been executed.

Therefore:

```text
Action
  ↓
Guardrail Validation
  ↓
Is action allowed?
  ↓
Yes
  ↓
Idempotency Check
  ↓
Has action already executed?
  ↓
No
  ↓
Execute
```

These controls should not be merged into a single responsibility.

---

# Failure Scenario: Network Timeout

A critical scenario is:

```text
Application
    ↓
Send remediation request
    ↓
AWS executes action
    ↓
Network response lost
    ↓
Application sees timeout
```

The application may not know whether the action actually executed.

A naive retry could execute the same action again.

Therefore, production remediation actions should use durable idempotency mechanisms where possible.

The current in-memory registry demonstrates the concept but is not sufficient for distributed production execution.

---

# Current MVP Limitation

The current `IdempotencyRegistry` is stored in application memory.

Therefore:

```text
Process Running
      ↓
Registry Exists
```

But:

```text
Process Restart
      ↓
Registry Lost
```

This means the current implementation protects duplicate actions only within the lifetime of the running process.

It is intentionally an MVP implementation.

A production implementation should use durable idempotency state.

---

# Future Durable Idempotency

A future implementation can store remediation execution records in DynamoDB.

Possible conceptual record:

```text
idempotency_key
incident_id
action
status
started_at
completed_at
execution_id
```

The key could be:

```text
INC-001:ACTION-001
```

A conditional write could then ensure that only one execution claim succeeds.

Conceptually:

```text
Remediation Request
        ↓
DynamoDB Conditional Write
        ↓
 ┌──────┴──────┐
 ↓             ↓
Claimed       Already Exists
 ↓             ↓
Execute       Skip / Return Existing Result
```

This would provide stronger protection across multiple application instances.

---

# Why Durable Idempotency Matters

CloudOps Autopilot may eventually run as:

```text
Lambda
ECS
Kubernetes
Multiple Workers
Multiple AWS Accounts
```

In such environments, application-memory state cannot reliably coordinate duplicate execution across instances.

Therefore, durable idempotency storage is part of the future production architecture.

---

# Concurrency Considerations

Multiple workers may process the same incident simultaneously.

Example:

```text
Worker A ──┐
           ├── Incident INC-001
Worker B ──┘
```

Both workers could attempt the same remediation.

A shared durable idempotency mechanism is required to guarantee that only one execution claim succeeds.

The current in-memory registry does not provide distributed concurrency protection.

This limitation is documented intentionally rather than hidden.

---

# Retry Strategy

Retries should not blindly repeat side effects.

The future remediation execution flow should be:

```text
Request
  ↓
Validate
  ↓
Authorize
  ↓
Check Idempotency
  ↓
Execute
  ↓
Record Result
```

When a retry occurs:

```text
Retry
  ↓
Check Idempotency
  ↓
Already Executed?
  ↓
Return Existing Result / Skip
```

This makes retries safer.

---

# Incident Identity

Idempotency depends on a stable incident identity.

The current incident model uses:

```text
incident_id
```

as the unique incident identifier.

Future versions should generate incident identifiers rather than relying on hardcoded prototype values.

Potential future approaches include:

* UUID
* ULID
* Event-derived deterministic identifier
* Composite incident identity

The selected approach should support distributed execution and traceability.

---

# Action Identity

The remediation action itself should also eventually have a stable identifier.

Instead of relying only on free-form action text:

```text
Collect additional metrics...
```

a future system could represent an action as:

```text
action_id = COLLECT_CPU_DIAGNOSTICS
```

Then the idempotency key could become:

```text
incident_id + action_id
```

This is more stable than using mutable human-readable action text.

---

# Idempotency and Incident Lifecycle

Idempotency integrates with the incident lifecycle.

Current conceptual lifecycle:

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

Before remediation execution:

```text
REMEDIATING
     ↓
Approval
     ↓
Guardrails
     ↓
Idempotency Check
     ↓
Execute
```

If the action was already executed, the system should not perform an unnecessary second side effect.

---

# Verification Relationship

Idempotency does not mean the system can assume success.

For example:

```text
Action already executed
        ↓
Does NOT mean
        ↓
Incident is resolved
```

The system must still perform verification.

Therefore:

```text
Idempotency
    ↓
Prevent Duplicate Execution
    ↓
Verification
    ↓
Determine Actual Recovery
```

This distinction is important for reliable incident automation.

---

# Auditability

A production idempotency implementation should record sufficient information to reconstruct execution behavior.

Potential fields include:

* Incident ID
* Action ID
* Idempotency key
* Execution ID
* Request timestamp
* Start timestamp
* Completion timestamp
* Execution status
* Error information
* Approver identity
* Verification result

This supports operational troubleshooting and research analysis.

---

# Security Considerations

Idempotency records may contain operational information about:

* Incidents
* Resources
* Remediation actions
* Execution results

Therefore, access to idempotency data should follow least privilege.

Production IAM policies should restrict:

* Who can create execution records
* Who can read them
* Who can update them
* Who can delete them

Application runtime roles should not receive unrestricted DynamoDB permissions.

---

# Reliability Considerations

Idempotency must remain reliable during:

* Application restarts
* Network failures
* AWS API retries
* Worker crashes
* Duplicate events
* Concurrent processing
* Partial failures

A durable implementation should distinguish between states such as:

```text
REQUESTED
RUNNING
SUCCEEDED
FAILED
UNKNOWN
```

The `UNKNOWN` state can be useful when the application cannot determine whether an external side effect completed.

The exact production state model will be defined when real AWS-mutating remediation is introduced.

---

# Alternatives Considered

## 1. No Duplicate Protection

Rejected.

Without duplicate protection, repeated events or retries could produce duplicate incidents and repeated remediation actions.

---

## 2. Application-Only Duplicate Check

Rejected as the long-term solution.

Application-only checks can suffer from race conditions:

```text
Check
  ↓
Execute
```

Multiple workers may perform the check simultaneously.

Persistence-layer conditional operations provide stronger concurrency protection.

---

## 3. In-Memory Idempotency Only

Accepted for the current MVP as a prototype mechanism.

Advantages:

* Simple
* Easy to test
* No additional infrastructure

Limitations:

* Lost on process restart
* Not shared between workers
* Not suitable for distributed production execution

Therefore, it is not considered sufficient for the final production architecture.

---

## 4. Durable DynamoDB Idempotency

Selected as the likely future production approach.

Advantages:

* Durable
* AWS-native
* Conditional writes
* Shared across application instances
* Supports distributed execution

It will be implemented when real AWS-mutating remediation is introduced.

---

# Consequences

## Positive Consequences

The decision provides:

* Duplicate incident protection
* Safer retry behavior
* Protection against repeated remediation
* Clear execution semantics
* Better concurrency control
* Stronger reliability architecture
* Better auditability
* Clear separation of responsibilities

---

## Negative Consequences

The decision introduces:

* Additional state management
* Idempotency-key design requirements
* More complex failure handling
* Need for durable state in production
* Additional database operations
* Need to reason about unknown execution outcomes

These trade-offs are accepted because duplicate side effects can be significantly more harmful than additional control logic.

---

# Current Implementation Status

### Incident Persistence

Implemented:

```text
DynamoDB conditional write
```

Using:

```python
ConditionExpression="attribute_not_exists(incident_id)"
```

Status:

**Implemented and integration-tested.**

---

### Remediation Idempotency

Implemented:

```text
In-memory IdempotencyRegistry
```

Status:

**Implemented for MVP simulation and unit testing.**

---

### Durable Remediation Idempotency

Status:

**Planned.**

Target:

```text
DynamoDB-backed idempotency state
```

This will be introduced before production-grade AWS-mutating remediation.

---

# Testing Requirements

The system should test at least:

### Incident Creation

* New incident is created.
* Duplicate incident is rejected.
* Existing incident is not overwritten during creation.

### Remediation

* First action executes successfully.
* Duplicate action is skipped.
* Empty action is rejected.
* Different action for the same incident can be evaluated independently.
* Same action for a different incident can be evaluated independently.

### Failure Scenarios

* Application restart
* Network timeout
* Duplicate event
* Concurrent execution
* Partial execution
* Unknown execution result

The current test suite covers the implemented MVP behavior.

---

# Research Relevance

Idempotency is an important part of evaluating safe automation.

A remediation framework should not only measure whether an action succeeds.

It should also measure whether the system avoids unsafe repeated execution.

Potential research metrics include:

* Duplicate incident rate
* Duplicate remediation rate
* Idempotency protection rate
* Retry success rate
* Unsafe repeated-action rate
* Unknown execution rate
* Remediation success rate

This allows the project to evaluate reliability in addition to automation effectiveness.

---

# Product Relevance

For a future CloudOps Autopilot product, reliable idempotency is important because customers may operate the platform across:

* Multiple AWS accounts
* Multiple regions
* Multiple applications
* Multiple workers
* Event-driven architectures
* Large incident volumes

A production product cannot assume that an event will be delivered exactly once.

The platform should therefore be designed around **at-least-once event delivery with idempotent processing** where applicable.

---

# Future Architecture

The future remediation architecture is expected to evolve toward:

```text
Incident Event
      ↓
Incident Identity
      ↓
DynamoDB Conditional Write
      ↓
Diagnosis
      ↓
Risk Assessment
      ↓
Recommendation
      ↓
Human Approval
      ↓
Durable Idempotency Check
      ↓
AWS Remediation
      ↓
Execution Result
      ↓
Verification
      ↓
Incident State Update
```

This architecture provides multiple independent safety controls.

---

# Decision Summary

CloudOps Autopilot will use **DynamoDB conditional writes** to protect incident creation from duplicate records and **idempotency controls** to prevent repeated remediation execution.

The current MVP uses:

```text
Incident Creation
        ↓
DynamoDB Conditional Write
```

and:

```text
Remediation Execution
        ↓
In-Memory Idempotency Registry
```

The in-memory implementation is intentionally limited to the MVP.

Before real production AWS-mutating remediation is introduced, the idempotency mechanism should evolve to a durable, distributed implementation, preferably using DynamoDB conditional operations.

The overall principle is:

> **Every automated side effect must be designed to tolerate retries and duplicate requests safely.**

---

## Related Architecture Decisions

* [ADR-001: Repository Pattern](./ADR-001-repository-pattern.md)
* [ADR-002: DynamoDB Persistence](./ADR-002-dynamodb-persistence.md)
* [ADR-003: Human Approval Before Remediation](./ADR-003-human-approval.md)

## Related Documentation

* [System Architecture](../architecture/system-architecture.md)
* [AWS Architecture](../architecture/aws-architecture.md)
* [Incident Lifecycle](../architecture/incident-lifecycle.md)
* [Product Requirements](../requirements/product-requirements.md)
