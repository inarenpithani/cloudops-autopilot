# Remediation Framework

---

## 1. Purpose

The remediation framework provides a controlled mechanism for executing approved cloud remediation actions.

The framework separates:

- remediation recommendation
- executable remediation action
- safety validation
- human approval
- idempotency control
- AWS execution
- execution result
- audit persistence
- post-remediation verification

The design follows the principle:

> Automation must be controlled, explainable, auditable, and verifiable.

---

## 2. Remediation Flow

```text
Incident
   |
   v
Diagnosis
   |
   v
Risk Assessment
   |
   v
Recommendation
   |
   v
RemediationAction
   |
   v
Safety Guardrails
   |
   v
Human Approval
   |
   v
Idempotency Claim
   |
   v
AWS Remediation
   |
   v
RemediationResult
   |
   v
Execution Audit
   |
   v
Post-Remediation Verification
   |
   +---- Recovered ----> RESOLVED
   |
   +---- Not Recovered -> INVESTIGATING
```

---

## 3. Design Principles

### 3.1 Explicit Actions

Recommendations and executable actions are separate concepts.

A recommendation describes what the system believes should be done.

A `RemediationAction` represents an explicit executable operation.

This prevents free-form recommendation text from directly becoming an AWS mutation.

---

### 3.2 Safety Before Execution

Every remediation action passes through safety guardrails before execution.

The guardrail layer validates:

- action identifier
- action allowlist
- risk level
- target resource

An action that fails validation is blocked before AWS execution.

---

### 3.3 Human Approval

The remediation framework supports explicit human approval.

For actions requiring approval, execution does not begin until the action is approved.

```text
RemediationAction
       |
       v
Guardrails
       |
       +---- no ---> Stop
       |
       +---- yes --> Executor
```

This provides a human control boundary around potentially disruptive operations.

---

## 4. Remediation Action Model

The `RemediationAction` model represents an executable remediation operation.

```python
@dataclass(frozen=True)
class RemediationAction:
    action_id: str
    name: str
    description: str
    risk_level: str
    resource_id: str
    requires_approval: bool = True
```

The important fields are:

| Field | Purpose |
|---|---|
| `action_id` | Stable identifier for the remediation operation |
| `name` | Human-readable action name |
| `description` | Explanation of the operation |
| `risk_level` | Risk classification |
| `resource_id` | Target AWS resource |
| `requires_approval` | Controls human approval requirement |

---

## 5. Supported Remediation Action

The current controlled remediation action is:

```text
EC2_REBOOT
```

It represents a controlled EC2 instance reboot.

The AWS operation is isolated behind the EC2 client:

```python
ec2_client.reboot_instance(
    instance_id=action.resource_id,
)
```

The remediation executor does not directly construct boto3 clients. AWS interaction remains inside the AWS integration layer.

---

## 6. Safety Guardrails

The guardrail layer defines which remediation actions are permitted.

Current allowed action:

```text
EC2_REBOOT
```

Current permitted risk levels:

```text
LOW
MEDIUM
```

The guardrail validation also requires:

```text
action_id != empty
resource_id != empty
```

A rejected action returns a structured `GuardrailResult`.

```python
@dataclass
class GuardrailResult:
    allowed: bool
    reason: str
```

Example:

```text
Guardrail allowed: False
Guardrail reason: Remediation action is not in the approved action allowlist.
```

No AWS mutation occurs when guardrails reject an action.

---

## 7. Human Approval Boundary

Human approval is handled independently from AWS execution.

The approval component receives a `RemediationAction` and requests explicit confirmation.

```text
Action
  |
  v
Approval Request
  |
  +---- no ---> Stop
  |
  +---- yes --> Executor
```

The executor does not make the approval decision.

This separation keeps authorization logic outside the AWS execution mechanism.

---

## 8. Persistent Idempotency

Remediation execution uses persistent idempotency keys.

The key is generated from:

```text
incident_id:action_id
```

Example:

```text
INC-001:EC2_REBOOT
```

The repository uses a conditional DynamoDB write to atomically claim the action.

```text
New action
    |
    v
Conditional PutItem
    |
    +---- Success ---> Execute
    |
    +---- Duplicate -> SKIPPED
```

This prevents the same remediation action from being executed repeatedly for the same incident.

---

## 9. Idempotency Failure Handling

If AWS execution fails, the idempotency claim is released.

```text
Claim
  |
  v
AWS Execution
  |
  +---- Success ---> Keep claim
  |
  +---- Failure ---> Release claim
```

This allows a failed action to be retried.

Unsupported actions also release their claim before returning a failed result.

---

## 10. Remediation Executor

The remediation executor coordinates the execution lifecycle.

Its responsibilities are:

1. Validate the action identifier.
2. Claim the remediation action.
3. Skip duplicate executions.
4. Dispatch the supported AWS operation.
5. Release the claim when execution fails.
6. Construct a `RemediationResult`.
7. Persist the execution result for auditability.

The executor does not:

- request human approval
- perform diagnosis
- calculate incident risk
- decide whether an action should be recommended

Those responsibilities remain in their respective layers.

---

## 11. Remediation Result

Every execution produces a `RemediationResult`.

```python
@dataclass
class RemediationResult:
    action: str
    action_id: str
    resource_id: str
    status: str
    started_at: datetime
    completed_at: datetime
    message: str
    error: str | None = None
```

Supported execution outcomes include:

```text
SUCCESS
FAILED
SKIPPED
```

Example successful result:

```text
status  : SUCCESS
message : Remediation action executed successfully.
error   : None
```

Example failed result:

```text
status : FAILED
error  : AWS reboot failed
```

Example duplicate result:

```text
status  : SKIPPED
message : Same action was already executed for this incident.
```

---

## 12. Remediation Execution Audit

Remediation execution results are persisted separately from the incident record.

The repository is:

```text
RemediationExecutionRepository
```

The current logical execution identifier is:

```text
incident_id:action_id
```

Example:

```text
INC-001:EC2_REBOOT
```

An audit record contains:

```text
execution_id
incident_id
action
action_id
resource_id
status
started_at
completed_at
message
error
```

This provides an execution-level audit trail.

---

## 13. Audit Persistence Flow

```text
Remediation Executor
        |
        v
RemediationResult
        |
        v
RemediationExecutionRepository
        |
        v
DynamoDB
```

The application creates the repository using the configured DynamoDB table:

```text
cloudops-autopilot-remediation-executions
```

The repository is responsible only for persistence.

---

## 14. Incident Lifecycle Integration

Remediation is integrated with the incident lifecycle.

The relevant lifecycle sequence is:

```text
DETECTED
   |
   v
ACKNOWLEDGED
   |
   v
INVESTIGATING
   |
   v
REMEDIATING
   |
   v
VERIFYING
   |
   +---- recovered ----> RESOLVED
   |
   +---- not recovered -> INVESTIGATING
```

The remediation action is executed only after the incident reaches the controlled remediation stage.

---

## 15. Verification Boundary

Successful remediation execution does not automatically mean that the incident is resolved.

The framework separates:

```text
Action execution
```

from:

```text
Recovery verification
```

Therefore:

```text
AWS reboot SUCCESS
        |
        v
Verification
        |
        +---- Healthy ---> RESOLVED
        |
        +---- Unhealthy -> INVESTIGATING
```

This prevents the system from treating an accepted AWS API operation as proof of recovery.

---

## 16. Failure Handling

The framework distinguishes between execution and recovery failures.

### Remediation execution failure

```text
Remediation
    |
    v
FAILED
    |
    v
No successful remediation claim retained
```

### Verification failure

```text
Remediation SUCCESS
    |
    v
Verification
    |
    v
Not recovered
    |
    v
INVESTIGATING
```

This distinction allows the system to determine whether the remediation itself failed or whether the remediation completed but did not restore service health.

---

## 17. Current AWS Integration Boundary

The framework contains a real AWS EC2 remediation implementation.

The EC2 client performs:

```text
ec2:RebootInstances
```

The application currently requires appropriate IAM authorization for the execution identity.

The remediation framework does not grant permissions itself.

IAM permissions remain an infrastructure and security concern and must be explicitly scoped to the required AWS operation and target resource.

---

## 18. Controlled Execution Model

The current architecture follows:

```text
Recommendation
      |
      v
Policy / Guardrails
      |
      v
Human Approval
      |
      v
Execution
      |
      v
Verification
```

The recommendation layer does not have authority to execute AWS actions.

The executor cannot bypass the guardrail and approval boundaries established before it.

---

## 19. Test Coverage

The remediation framework is covered by unit and integration tests.

The test suite validates:

- successful EC2 remediation
- unsupported remediation actions
- invalid action identifiers
- AWS execution failures
- idempotent duplicate handling
- different incidents using the same action
- execution audit persistence
- human approval rejection
- incident lifecycle integration
- verification success
- verification failure

The full project regression suite currently passes:

```text
100 passed
```

---

## 20. Current Limitations

The current implementation intentionally keeps the remediation framework controlled and limited.

Current limitations include:

- only `EC2_REBOOT` is implemented as an executable remediation action
- real AWS execution requires explicit IAM authorization
- human approval is interactive
- remediation execution records currently use `incident_id:action_id` as the logical execution identifier
- the framework does not yet provide autonomous remediation
- advanced remediation policy management is not yet implemented

These limitations are intentional boundaries for controlled expansion.

---

## 21. Future Extensions

Potential future capabilities include:

- additional remediation action types
- centralized remediation policies
- richer execution audit history
- approval workflows
- remediation timeouts
- execution leases
- rollback mechanisms
- automated low-risk remediation
- Kubernetes remediation
- multi-resource remediation
- policy-driven remediation authorization

Future autonomous capabilities must preserve the existing safety boundaries.

---

## 22. Related Documentation

- `docs/architecture/system-architecture.md`
- `docs/architecture/aws-architecture.md`
- `docs/architecture/incident-lifecycle.md`
- `docs/architecture/dynamodb-persistence.md`
- `docs/architecture/eventbridge-integration.md`
- `docs/research/research-problem.md`

---

