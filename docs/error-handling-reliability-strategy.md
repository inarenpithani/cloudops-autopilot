# CloudOps Autopilot — Error Handling and Reliability Strategy

## 1. Purpose

This document defines how CloudOps Autopilot handles failures and maintains reliable incident processing.

CloudOps Autopilot is itself an automation system. Therefore, failures inside the automation platform must be handled carefully.

The system should distinguish between:

* Expected conditions
* Transient failures
* Permanent failures
* Configuration failures
* Dependency failures
* Safety failures
* Remediation failures
* Verification failures

The objective is not to hide failures.

The objective is to:

1. Detect failures clearly.
2. Classify them correctly.
3. Retry only when appropriate.
4. Prevent unsafe repeated operations.
5. Preserve incident state.
6. Recover where possible.
7. Fail safely when recovery is not possible.
8. Provide enough information for diagnosis and audit.

---

# 2. Reliability Principles

CloudOps Autopilot follows these principles:

1. Failures must be explicit.
2. Retry only operations that are safe to retry.
3. Retries must use bounded attempts.
4. Retries should use exponential backoff where appropriate.
5. Timeouts must prevent indefinite waiting.
6. Idempotency must protect retryable side effects.
7. Permanent failures should not be retried indefinitely.
8. Safety failures should fail closed.
9. Incident state must remain recoverable.
10. Errors must be observable.
11. Recovery actions must be verifiable.
12. The system should degrade gracefully where practical.

---

# 3. Failure Categories

Failures are classified into major categories.

```text
Failure
   │
   ├── Configuration Failure
   ├── Validation Failure
   ├── Dependency Failure
   ├── Transient Failure
   ├── Permanent Failure
   ├── Authorization Failure
   ├── Safety Failure
   ├── Remediation Failure
   └── Verification Failure
```

Correct classification is important because each category requires different handling.

---

# 4. Configuration Failures

Configuration failures occur when required application configuration is missing or invalid.

Examples:

* Missing AWS region
* Missing EC2 instance ID
* Invalid CPU threshold
* Invalid environment configuration
* Invalid remediation configuration

Example:

```text
Missing EC2_INSTANCE_ID
        ↓
Configuration Validation
        ↓
Startup Failure
```

The system should fail clearly rather than silently selecting an arbitrary value.

---

# 5. Validation Failures

Validation failures occur when an input does not satisfy the expected rules.

Examples:

* Empty remediation action
* Invalid incident state
* Invalid risk level
* Unsupported action
* Invalid configuration value

Validation failures should normally not be retried because retrying the same invalid input will produce the same failure.

Example:

```text
Invalid Action
      ↓
Validation
      ↓
Reject
      ↓
Do Not Retry
```

---

# 6. Transient Failures

Transient failures are temporary conditions that may succeed when retried.

Examples include:

* Temporary AWS service errors
* Network interruptions
* Temporary throttling
* Temporary connection failures
* Short-lived dependency unavailability

A retry may be appropriate when the operation is safe to retry.

---

# 7. Permanent Failures

Permanent failures are conditions that are unlikely to succeed by simply retrying.

Examples:

* Resource does not exist
* Invalid request
* Unsupported operation
* Invalid configuration
* IAM permission denied
* Invalid resource identifier

These failures should normally be surfaced immediately.

Example:

```text
Invalid Request
      ↓
Failure Classification
      ↓
Permanent Failure
      ↓
Do Not Retry Indefinitely
```

---

# 8. Authorization Failures

Authorization failures occur when the application does not have permission to perform an operation.

Examples:

* `AccessDeniedException`
* Missing IAM permission
* Incorrect resource policy
* Incorrect role configuration

Authorization failures should generally not be retried automatically.

The correct response is to:

1. Record the failure.
2. Log the affected operation.
3. Preserve incident state.
4. Alert or surface the issue.
5. Correct the authorization configuration.

---

# 9. Safety Failures

Safety failures are different from ordinary infrastructure failures.

Examples:

* Action not in allowlist
* Required approval missing
* Invalid risk classification
* Idempotency conflict
* Unsafe resource scope

Safety failures should fail closed.

That means:

```text
Safety Check Failed
        ↓
Block Action
        ↓
Do Not Execute
```

The system must never interpret a safety failure as permission to proceed.

---

# 10. Remediation Failures

A remediation action may fail even after:

* Diagnosis succeeded
* Risk assessment succeeded
* Guardrails passed
* Human approval succeeded

Therefore:

```text
Approved
   ↓
Remediation
   ↓
Execution Failure
```

must be treated as a valid operational state.

The system must record the remediation result and transition the incident into an appropriate failure-handling path.

---

# 11. Verification Failures

A remediation can execute successfully while the incident remains unresolved.

Therefore:

```text
Remediation SUCCESS
        ≠
Incident RESOLVED
```

The system must perform verification.

If verification fails:

```text
VERIFYING
    ↓
Recovery Not Confirmed
    ↓
INVESTIGATING
```

The system may then collect additional evidence or evaluate another approved action.

---

# 12. Retry Strategy

Retries should be used only when they have a reasonable probability of succeeding.

The general retry model is:

```text
Operation
   ↓
Failure
   ↓
Is failure retryable?
   ├── No → Return failure
   │
   └── Yes
        ↓
    Retry Count
        ↓
    Backoff
        ↓
    Retry
```

Retries must be bounded.

---

# 13. Exponential Backoff

For retryable failures, exponential backoff should be considered.

Conceptually:

```text
Attempt 1 → immediate
Attempt 2 → short delay
Attempt 3 → longer delay
Attempt 4 → longer delay
```

A common conceptual formula is:

```text
delay = base_delay × 2^attempt
```

Production implementations should also consider jitter to reduce synchronized retries across multiple workers.

---

# 14. Retry Limits

Retries must have a maximum attempt count.

Example:

```text
MAX_RETRIES = 3
```

Conceptually:

```text
Attempt 1
   ↓
Failure
   ↓
Attempt 2
   ↓
Failure
   ↓
Attempt 3
   ↓
Failure
   ↓
Stop
```

The exact value should be configuration-driven and selected according to the operation.

---

# 15. Retry Safety

Not every operation is safe to retry.

### Usually safer to retry

* Read-only metric queries
* Read-only resource lookups
* Some idempotent persistence operations
* Temporary network operations

### Requires additional protection

* Resource modifications
* Scaling operations
* Restart operations
* Deployment changes
* Configuration changes
* Other infrastructure side effects

Before retrying a side-effecting operation, the system must consider idempotency.

---

# 16. Idempotency and Reliability

Idempotency is a key reliability mechanism.

The system must prevent:

```text
Retry
  ↓
Same side effect
  ↓
Unexpected duplicate execution
```

The current architecture uses:

* DynamoDB conditional writes for incident creation
* Idempotency registry for remediation actions

The remediation idempotency implementation is currently in memory.

A durable distributed implementation is planned before production-grade AWS-mutating remediation.

---

# 17. Timeout Strategy

Operations that depend on external systems should have appropriate timeouts.

Examples:

* CloudWatch API calls
* DynamoDB operations
* Event processing
* Remediation API calls
* Verification operations

The objective is to prevent the application from waiting indefinitely.

Conceptually:

```text
External Operation
      ↓
Timeout
      ↓
Operation stops waiting
      ↓
Failure classified
```

Timeout values should be configuration-driven where practical.

---

# 18. AWS SDK Error Handling

AWS SDK operations can produce different classes of failures.

The application should distinguish between:

* Throttling
* Service unavailable
* Access denied
* Resource not found
* Validation errors
* Network errors
* Unexpected service errors

The system should avoid converting all AWS exceptions into one generic error.

Specific error classification improves retry and recovery behavior.

---

# 19. CloudWatch Failure Handling

CloudWatch is a critical dependency for incident detection.

Possible failures include:

* API errors
* Throttling
* Network failure
* Invalid metric configuration
* Missing datapoints
* Unexpected response

The system should distinguish:

```text
No Incident Detected
```

from:

```text
Could Not Determine Incident State
```

A monitoring failure must not be silently interpreted as a healthy environment.

---

# 20. DynamoDB Failure Handling

DynamoDB is responsible for incident persistence.

Possible failures include:

* Throttling
* Service errors
* Network failures
* Permission errors
* Conditional check failures
* Missing records

The system should classify these separately.

For example:

```text
ConditionalCheckFailed
```

during duplicate incident creation is not equivalent to:

```text
DynamoDB service unavailable
```

The first may represent expected duplicate protection.

The second represents a persistence dependency failure.

---

# 21. Conditional Write Failures

The current DynamoDB repository uses conditional writes to prevent duplicate incidents.

A conditional check failure may indicate:

```text
Incident already exists
```

This should not automatically be treated as infrastructure failure.

The system should distinguish expected business conditions from unexpected infrastructure failures.

---

# 22. Persistence Failure and Incident State

If persistence fails during incident processing, the system must avoid falsely reporting a successfully persisted state.

For example:

```text
Incident Detected
      ↓
DynamoDB Save
      ↓
Failure
```

The application should record the persistence failure through available observability mechanisms and avoid claiming that the incident has been durably stored.

Future versions may introduce recovery queues or durable event processing for this scenario.

---

# 23. Partial Failure

Distributed systems can fail after completing part of an operation.

Example:

```text
Diagnosis completed
        ↓
Risk assessment completed
        ↓
Approval completed
        ↓
Remediation request sent
        ↓
Response lost
```

The system may not know whether remediation completed.

This creates an **unknown execution state**.

The system should not blindly retry an unknown side effect.

Instead, it should use idempotency, status inspection, or another safe recovery mechanism.

---

# 24. Unknown State

An unknown state is different from failure.

Example:

```text
Request sent
    ↓
Response lost
    ↓
Execution state unknown
```

The system should avoid assuming either:

```text
SUCCESS
```

or:

```text
FAILURE
```

without evidence.

Future production remediation should support explicit execution states such as:

```text
REQUESTED
RUNNING
SUCCEEDED
FAILED
UNKNOWN
```

---

# 25. Graceful Degradation

When a non-critical capability fails, the system should degrade gracefully where safe.

For example:

```text
Optional Dashboard Failure
        ↓
Core Incident Processing Continues
```

However, safety-critical capabilities should not be bypassed.

For example:

```text
Approval Service Failure
        ↓
Remediation Blocked
```

The system should prioritize safety over availability when infrastructure-changing actions are involved.

---

# 26. Fail-Closed Principle

Safety-sensitive components should fail closed.

Examples:

```text
Approval unavailable
        ↓
No remediation
```

```text
Guardrail validation unavailable
        ↓
No remediation
```

```text
Required safety policy unavailable
        ↓
No remediation
```

The absence of a safety decision must never be interpreted as permission.

---

# 27. Incident Lifecycle During Failures

The incident lifecycle must remain explicit during failures.

Normal flow:

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

Possible failure path:

```text
REMEDIATING
   ↓
Execution Failure
   ↓
INVESTIGATING
```

Verification failure:

```text
VERIFYING
   ↓
Recovery Not Confirmed
   ↓
INVESTIGATING
```

The exact failure transitions should remain controlled by the incident lifecycle model.

---

# 28. Error Propagation

Errors should be handled at the appropriate layer.

Conceptually:

```text
AWS Client
    ↓
AWS-specific exception
    ↓
Service Layer
    ↓
Domain/application decision
    ↓
Incident handling
```

Low-level infrastructure exceptions should not unnecessarily leak into every business component.

The application should preserve enough context for diagnosis while maintaining separation of concerns.

---

# 29. Error Messages

Error messages should be:

* Clear
* Actionable
* Contextual
* Safe
* Non-sensitive

Example:

```text
Failed to persist incident INC-001 to DynamoDB.
```

rather than exposing:

```text
Credentials:
AKIA...
Secret:
...
```

Sensitive information must never appear in errors or logs.

---

# 30. Error Context

Operational errors should include useful context such as:

* Incident ID
* Operation
* Resource
* Service
* Error category
* Timestamp
* Retry attempt

Example:

```text
incident_id=INC-001
operation=dynamodb_update
resource=cloudops-autopilot-incidents
error_type=Throttling
retry_attempt=2
```

This improves diagnosis.

---

# 31. Dependency Isolation

CloudOps Autopilot should isolate external dependencies behind appropriate components.

Examples:

```text
CloudWatchClient
DynamoDBIncidentRepository
Future EventBridge Client
Future Notification Client
```

This improves:

* Testing
* Error handling
* Retry logic
* Dependency replacement
* Maintainability

---

# 32. Circuit Breaker Concept

A future distributed implementation may use circuit-breaker behavior for repeatedly failing dependencies.

Conceptually:

```text
Healthy
   ↓
Repeated Failures
   ↓
Open Circuit
   ↓
Stop Requests Temporarily
   ↓
Recovery Check
   ↓
Half Open
   ↓
Healthy
```

Circuit breakers should only be introduced where the failure pattern and dependency behavior justify them.

They are not required for the current local MVP.

---

# 33. Dead-Letter Handling

The future event-driven architecture may require dead-letter handling.

Example:

```text
Event
 ↓
Processing
 ↓
Repeated Failure
 ↓
Retry Limit Reached
 ↓
Dead-Letter Queue
```

This prevents permanently failing events from blocking the main processing flow.

Possible AWS implementation:

```text
EventBridge / SQS
       ↓
Processing
       ↓
DLQ
```

The exact event architecture will be defined when asynchronous processing is introduced.

---

# 34. Recovery Strategy

Recovery should depend on failure type.

### Transient Failure

Retry with bounded backoff.

### Permanent Failure

Stop retrying and surface the failure.

### Safety Failure

Block action.

### Remediation Failure

Preserve incident state and investigate.

### Verification Failure

Return to investigation.

### Persistence Failure

Record the failure and use future durable recovery mechanisms where available.

---

# 35. Data Consistency

Incident state should remain consistent with actual processing outcomes.

The system should avoid situations such as:

```text
DynamoDB says RESOLVED
```

while:

```text
Verification actually failed
```

State transitions should therefore occur only after the relevant operation has produced the required result.

---

# 36. Retry and State Transitions

Retries must not accidentally advance an incident multiple times.

Example:

```text
INVESTIGATING
     ↓
Remediation
     ↓
Retry
```

The retry should not create:

```text
REMEDIATING
REMEDIATING
```

or duplicate lifecycle events.

State transitions should remain validated through the lifecycle model.

---

# 37. Reliability of Detection

Detection itself must be reliable.

The system should distinguish:

```text
No evidence of incident
```

from:

```text
Unable to retrieve evidence
```

For example:

```text
CloudWatch query fails
        ↓
Do not automatically conclude
"No incident"
```

The monitoring failure should be surfaced as an operational issue.

---

# 38. Reliability of Diagnosis

Diagnosis should preserve uncertainty.

If insufficient evidence exists:

```text
Probable Cause = Unknown
Confidence = 0
```

The system should not invent a diagnosis simply because the detection occurred.

This improves safety and explainability.

---

# 39. Reliability of Risk Assessment

Risk assessment should also fail safely.

If risk cannot be determined reliably:

```text
Risk Assessment Failure
        ↓
Do Not Execute Remediation
```

A missing risk decision should not default to a permissive action.

---

# 40. Reliability of Recommendation

Recommendations should be validated against available guardrails.

If no approved action exists:

```text
No Safe Recommendation
        ↓
Do Not Remediate
```

The system should prefer no action over an unsafe action.

---

# 41. Reliability of Approval

Approval should be explicit.

Valid approval:

```text
APPROVED
```

Invalid or missing approval:

```text
NOT APPROVED
```

The system must never interpret:

```text
timeout
unknown
missing
```

as approval.

---

# 42. Reliability of Remediation

The remediation executor should return a structured result.

The current model contains:

```text
action
status
started_at
completed_at
message
error
```

This allows the system to distinguish execution outcomes.

Future implementations should additionally record:

* Execution ID
* Target resource
* Attempt number
* Idempotency key
* Provider response
* Rollback information

---

# 43. Reliability of Verification

Verification must be based on observable system state.

The system should not rely only on:

```text
Remediation status = SUCCESS
```

Instead:

```text
Remediation SUCCESS
        ↓
Observe System
        ↓
Condition Recovered?
```

Only successful verification should allow the incident to transition to `RESOLVED`.

---

# 44. Observability Relationship

Error handling and observability are closely connected.

Every important failure should produce enough telemetry to answer:

* What failed?
* Why did it fail?
* Which incident was affected?
* Was it retried?
* How many times?
* Was the action executed?
* What was the final state?

The Logging & Observability Strategy defines the telemetry model.

This document defines how failures should behave.

---

# 45. Testing Reliability

Reliability behavior must be tested deliberately.

Tests should cover:

### Configuration

* Missing configuration
* Invalid configuration

### AWS Dependencies

* CloudWatch failure
* DynamoDB failure
* Throttling
* Permission denied
* Resource not found

### Retry

* Retryable failure
* Maximum retry reached
* Backoff behavior

### Safety

* Guardrail failure
* Approval failure
* Idempotency conflict

### Remediation

* Execution failure
* Timeout
* Unknown execution result

### Verification

* Recovery success
* Recovery failure

---

# 46. Failure Injection

Future testing should intentionally introduce controlled failures.

Examples:

```text
CloudWatch unavailable
DynamoDB unavailable
Network timeout
Permission denied
Remediation failure
Verification failure
```

This allows the team to evaluate whether the system behaves as designed.

Failure injection should be performed only in controlled environments.

---

# 47. Recovery Time

Reliability evaluation should measure how quickly the system recovers from failures.

Potential metrics include:

* Retry recovery time
* Dependency recovery time
* Incident recovery time
* Remediation recovery time

These measurements can contribute to the broader research evaluation.

---

# 48. Reliability Metrics

Potential platform reliability metrics include:

### Error Rate

```text
Failed Operations
----------------- × 100
Total Operations
```

### Retry Rate

```text
Retried Operations
------------------ × 100
Total Operations
```

### Remediation Failure Rate

```text
Failed Remediations
------------------- × 100
Total Remediations
```

### Verification Failure Rate

```text
Failed Verifications
-------------------- × 100
Total Verifications
```

### Persistence Failure Rate

```text
Failed Persistence Operations
----------------------------- × 100
Total Persistence Operations
```

---

# 49. Production Reliability Considerations

Before production deployment, the following should be addressed:

* Retry policies
* Timeout configuration
* Durable idempotency
* Structured error handling
* Centralized logs
* Metrics
* Alerts
* Health checks
* Dead-letter handling
* Backup and recovery
* Disaster recovery
* Dependency monitoring
* Failure injection
* Security controls
* Auditability

---

# 50. Current vs Target Reliability

## Current MVP

```text
Application
    ↓
Basic Exception Handling
    ↓
In-Memory Idempotency
    ↓
DynamoDB Persistence
    ↓
Verification
```

## Target

```text
Event
  ↓
Validation
  ↓
Detection
  ↓
Diagnosis
  ↓
Risk
  ↓
Guardrails
  ↓
Approval
  ↓
Durable Idempotency
  ↓
Retry / Timeout Controls
  ↓
Remediation
  ↓
Verification
  ↓
Audit
  ↓
Observability
  ↓
Recovery / Escalation
```

---

# 51. Industry Standards Alignment

The strategy follows common reliability engineering principles including:

* Explicit failure classification
* Bounded retries
* Exponential backoff
* Timeout protection
* Idempotent operations
* Fail-closed safety controls
* Graceful degradation
* Dependency isolation
* Health checks
* Observability
* Failure injection
* Structured incident states
* Recovery verification

The project will progressively implement these principles as it moves from MVP to production architecture.

---

# 52. Current Implementation Status

## Implemented

* Incident lifecycle validation
* DynamoDB persistence
* Conditional incident creation
* In-memory remediation idempotency
* Guardrails
* Human approval
* Structured remediation result
* Verification
* Basic failure handling
* Unit tests
* Integration tests

## Planned

* Centralized exception hierarchy
* Retry framework
* Exponential backoff
* Jitter
* Timeout configuration
* Durable remediation idempotency
* Structured error logging
* Failure injection
* Dead-letter handling
* Health checks
* Circuit-breaker patterns where justified
* Disaster recovery strategy

---

# 53. Reliability Roadmap

The reliability maturity path is:

```text
Basic Exception Handling
        ↓
Failure Classification
        ↓
Bounded Retries
        ↓
Timeouts
        ↓
Idempotency
        ↓
Structured Observability
        ↓
Failure Injection
        ↓
Durable Recovery
        ↓
Distributed Reliability
        ↓
Production Resilience
```

---

# 54. Summary

CloudOps Autopilot treats failure handling as a core part of the automation architecture.

The system must not assume that:

```text
API success = Incident resolved
```

or:

```text
API failure = Action not executed
```

Instead, it must reason about:

* Failure type
* Retryability
* Idempotency
* Current incident state
* Execution uncertainty
* Verification
* Recovery

The central reliability principle is:

> **Retry safe operations, block unsafe operations, preserve state, verify outcomes, and never hide uncertainty.**

This approach supports the project's broader goal of building cloud automation that is reliable, explainable, controlled, and suitable for progressive evolution toward production use.

---

## Related Documentation

* [Product Requirements](requirements/product-requirements.md)
* [System Architecture](architecture/system-architecture.md)
* [AWS Architecture](architecture/aws-architecture.md)
* [Incident Lifecycle](architecture/incident-lifecycle.md)
* [Configuration Strategy](configuration-strategy.md)
* [Logging & Observability Strategy](logging-observability-strategy.md)

## Related Architecture Decisions

* [ADR-001: Repository Pattern](decisions/ADR-001-repository-pattern.md)
* [ADR-002: DynamoDB Persistence](decisions/ADR-002-dynamodb-persistence.md)
* [ADR-003: Human Approval Before Remediation](decisions/ADR-003-human-approval.md)
* [ADR-004: Conditional Write and Idempotency](decisions/ADR-004-conditional-write-idempotency.md)
