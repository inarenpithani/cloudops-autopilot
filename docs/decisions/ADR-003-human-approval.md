# ADR-003: Human Approval Before Remediation

## Status

Accepted

## Date

2026-09-27

## Context

CloudOps Autopilot is designed to detect cloud incidents, diagnose probable causes, assess risk, recommend remediation actions, execute approved actions, and verify recovery.

Automating remediation can reduce recovery time and human effort. However, directly allowing an automated system to modify cloud infrastructure can also introduce significant operational and security risks.

A remediation action may:

* Affect production workloads
* Cause service interruption
* Change infrastructure state
* Increase or decrease capacity
* Modify application or network configuration
* Create financial impact
* Produce unintended side effects
* Increase the blast radius of an incorrect diagnosis

The system therefore needs a clearly defined boundary between **analysis/recommendation** and **actual infrastructure modification**.

For the current MVP, remediation actions must not be executed solely because the automation engine recommends them.

---

## Problem

A cloud incident automation platform needs to balance two competing objectives:

1. Reduce manual operational effort.
2. Prevent unsafe or unintended infrastructure changes.

If every recommended action is automatically executed, a false detection, incorrect diagnosis, stale evidence, or faulty automation logic could cause an unwanted infrastructure change.

CloudOps Autopilot therefore needs an explicit control mechanism before a remediation action can proceed.

---

## Decision

CloudOps Autopilot will use **human approval as a mandatory control before remediation actions are executed** in the current MVP.

The system will separate:

```text
Detection
    ↓
Diagnosis
    ↓
Risk Assessment
    ↓
Recommendation
    ↓
Safety Guardrails
    ↓
Human Approval
    ↓
Remediation
    ↓
Verification
```

The automation engine may detect, analyze, assess, and recommend an action without human intervention.

However, an infrastructure-changing remediation action requires explicit approval before execution.

---

## Decision Drivers

The decision is based on:

* Safety
* Operational control
* Blast-radius reduction
* Explainability
* Auditability
* Risk management
* Human oversight
* Controlled automation
* Production-readiness
* Research validity

---

## Human-in-the-Loop Principle

The current system follows a **Human-in-the-Loop** operating model.

The automation system is responsible for:

* Detecting the incident
* Collecting evidence
* Diagnosing the probable cause
* Calculating confidence
* Assessing risk
* Recommending an action
* Validating the action against safety guardrails

The human operator is responsible for:

* Reviewing the recommendation
* Evaluating the operational context
* Approving or rejecting the action

The remediation executor is responsible for:

* Executing only an approved action
* Returning an execution result

The verification component is responsible for:

* Checking whether the incident condition improved
* Determining whether the remediation succeeded

---

## Recommendation Is Not Execution

A key architectural boundary is:

```text
Recommendation ≠ Execution
```

The system may determine:

```text
Recommended Action:
Collect additional metrics and investigate the top
CPU-consuming processes.
```

That recommendation does not automatically authorize an infrastructure change.

The system must pass through the approval boundary before executing an approved remediation action.

---

## Approval Flow

The current flow is:

```text
Incident Detected
        ↓
Evidence Collected
        ↓
Diagnosis
        ↓
Risk Assessment
        ↓
Recommendation
        ↓
Safety Guardrails
        ↓
Human Approval
        ↓
Approved?
     /       \
   No         Yes
   ↓           ↓
Stop       Remediation
               ↓
          Verification
```

If approval is denied, the remediation action must not execute.

---

## Safety Boundary

The approval boundary acts as a safety barrier between analysis and infrastructure modification.

```text
┌───────────────────────────────────────┐
│        Analysis / Decision Layer      │
│                                       │
│ Detection                             │
│ Diagnosis                             │
│ Risk Assessment                       │
│ Recommendation                        │
│ Guardrails                            │
└───────────────────┬───────────────────┘
                    │
                    │ Human Approval
                    ▼
┌───────────────────────────────────────┐
│        Infrastructure Action Layer     │
│                                       │
│ Remediation                           │
│ Verification                          │
└───────────────────────────────────────┘
```

This boundary reduces the probability that an incorrect automated decision immediately becomes an infrastructure change.

---

## Risk-Based Reasoning

Human approval is especially important when the potential impact of a remediation action is significant.

Examples of potentially higher-impact actions include:

* Restarting production workloads
* Changing instance capacity
* Modifying security-group rules
* Changing network configuration
* Updating infrastructure configuration
* Deleting resources
* Modifying application deployment state

The current MVP does not attempt to automatically classify all infrastructure actions as safe.

Instead, the system uses restrictive guardrails and human approval.

---

## Current Guardrail Model

The current remediation guardrail implementation uses an allowlist.

Only explicitly approved actions can pass the guardrail.

Example approved actions currently include:

```text
Monitor CPU utilization and collect additional diagnostic data.
```

and:

```text
Collect additional metrics and investigate the top
CPU-consuming processes.
```

Actions outside the allowlist are rejected.

This is intentionally restrictive because the current project is establishing the safety architecture before introducing real AWS-mutating remediation.

---

## Why Allowlisting Is Used

An allowlist provides a default-deny model.

Conceptually:

```text
Action requested
      ↓
Is action explicitly approved?
      ↓
   ┌──No──→ BLOCK
   │
  Yes
   ↓
Continue safety evaluation
```

This is safer than allowing arbitrary remediation commands.

The model can later evolve as individual remediation actions are tested, classified, and approved.

---

## Approval Rejection

If the operator rejects the recommendation:

```text
Recommendation
      ↓
Human Review
      ↓
Rejected
      ↓
No Remediation
```

The system must not attempt to bypass the decision.

The incident can remain available for investigation or future action.

---

## Approval Failure

If the approval mechanism itself fails or does not produce a valid approval result, the system must fail closed.

That means:

```text
Approval unavailable
       ↓
Do not execute remediation
```

The absence of approval must never be interpreted as approval.

---

## Remediation Failure

Approval does not guarantee successful execution.

The lifecycle therefore remains:

```text
APPROVED
   ↓
REMEDIATING
   ↓
Execution Result
   ├── SUCCESS → VERIFYING
   └── FAILURE → Investigation / Failure Handling
```

The system must record the remediation result and avoid assuming that an approved action automatically resolved the incident.

---

## Verification

Every remediation action should be followed by verification.

The system should not conclude:

```text
Action executed = Incident resolved
```

Instead:

```text
Action executed
      ↓
Verification
      ↓
Did the incident condition recover?
```

If verification succeeds:

```text
VERIFYING → RESOLVED
```

If verification fails:

```text
VERIFYING → INVESTIGATING
```

This preserves the distinction between **action execution** and **actual recovery**.

---

## Idempotency Relationship

Human approval does not replace idempotency.

Both controls are required:

```text
Human Approval
      +
Idempotency
      +
Guardrails
      +
Verification
```

Human approval controls whether an action is authorized.

Idempotency controls whether the same action is executed repeatedly.

Guardrails control which actions are permitted.

Verification determines whether the system actually recovered.

These controls address different failure modes.

---

## Auditability

The approval process should eventually provide an audit trail containing information such as:

* Incident ID
* Recommended action
* Risk level
* Evidence used
* Approval decision
* Approver identity
* Approval timestamp
* Remediation action
* Execution result
* Verification result

This is important for operational troubleshooting, security investigations, compliance requirements, and research evaluation.

The current MVP provides the architectural foundation for this audit trail, while a more complete audit implementation remains future work.

---

## Security Considerations

The approval mechanism should not be treated as the only security control.

Production remediation must also use:

* Least-privilege IAM
* Dedicated remediation roles
* Restricted resource scope
* Explicit action permissions
* Strong authentication
* Secure secrets management
* CloudTrail auditing
* Logging and monitoring
* Environment separation

The remediation execution identity should have only the permissions required for the specific approved actions.

---

## Blast-Radius Control

A core principle is:

> **The more powerful the remediation action, the stronger the control required around its execution.**

Potential controls include:

* Resource allowlists
* Action allowlists
* Environment restrictions
* Human approval
* Time-limited authorization
* IAM permission boundaries
* Maximum affected-resource limits
* Verification requirements
* Automatic rollback where technically possible

These controls reduce the potential impact of an incorrect remediation.

---

## Environment Considerations

The approval model should differ according to environment requirements.

A possible future model is:

```text
Development
    ↓
More automation / lower operational impact

UAT
    ↓
Controlled approval

Production
    ↓
Strong approval + restrictive guardrails
```

The exact production policy should be defined after the project's security and environment strategy is finalized.

---

## Current MVP Behavior

The current implementation follows this sequence:

```text
Incident detected
        ↓
Incident persisted
        ↓
ACKNOWLEDGED
        ↓
INVESTIGATING
        ↓
Diagnosis
        ↓
Risk assessment
        ↓
Recommendation
        ↓
Guardrail validation
        ↓
Human approval
        ↓
REMEDIATING
        ↓
Remediation executor
        ↓
VERIFYING
        ↓
RESOLVED / INVESTIGATING
```

The current remediation executor operates in **simulation mode** and does not yet modify AWS infrastructure.

This is intentional.

The project establishes the control architecture before introducing real AWS-mutating remediation.

---

## Alternatives Considered

### 1. Fully Autonomous Remediation

Under this model:

```text
Detection
   ↓
Diagnosis
   ↓
Remediation
```

The system would automatically execute remediation without human approval.

Advantages:

* Lower human intervention
* Potentially faster response
* Higher automation

Risks:

* Incorrect diagnosis could cause infrastructure changes
* Higher blast radius
* Greater impact from software defects
* Harder operational control
* Greater security risk
* More difficult failure recovery

This approach is not selected for the current MVP.

---

### 2. Recommendation Only

Under this model, the system would:

```text
Detect
  ↓
Diagnose
  ↓
Recommend
```

and stop.

Advantages:

* Very low automation risk
* No infrastructure modification

Limitations:

* Human must execute every remediation
* Does not demonstrate the full remediation lifecycle
* Does not allow evaluation of controlled remediation automation

This is safer but does not satisfy the project's broader automation objective.

---

### 3. Human Approval Before Remediation

The selected model is:

```text
Detect
  ↓
Diagnose
  ↓
Assess Risk
  ↓
Recommend
  ↓
Guardrails
  ↓
Human Approval
  ↓
Remediate
  ↓
Verify
```

This provides a controlled transition from analysis to action and allows the project to evolve toward more automation while retaining safety controls.

---

## Consequences

### Positive Consequences

The decision provides:

* Human oversight
* Reduced remediation risk
* Controlled automation
* Clear safety boundary
* Better explainability
* Better auditability
* Lower blast radius
* Easier incremental evolution
* Stronger research evaluation

It also allows the project to demonstrate meaningful automation without immediately giving the system unrestricted infrastructure control.

---

### Negative Consequences

Human approval introduces:

* Additional latency
* Human dependency
* Potential approval bottlenecks
* Operational overhead
* Reduced automation compared with fully autonomous systems

These trade-offs are accepted for the current MVP because safety and control are prioritized while the remediation architecture is being established.

---

## Future Evolution

The long-term architecture may introduce **risk-based automation**.

A possible evolution is:

```text
                Risk Assessment
                      ↓
              ┌───────┴────────┐
              ↓                ↓
          Low Risk          High Risk
              ↓                ↓
     Controlled Auto       Human Approval
       Remediation              ↓
              ↓             Remediation
              └───────┬────────┘
                      ↓
                  Verification
```

However, automatic remediation should only be introduced after:

* Action-specific testing
* Strong guardrails
* Reliable verification
* Sufficient observability
* Auditability
* Failure handling
* Security review
* Blast-radius analysis

The project should not treat autonomous remediation as the default.

---

## Research Relevance

Human approval is also important to the project's research objective.

The project evaluates whether cloud incident remediation can be automated safely while reducing human intervention.

Human approval provides a measurable control point.

Potential research metrics include:

* Human intervention rate
* Approval rate
* Approval latency
* Remediation success rate
* Unsafe-action rate
* False-positive rate
* Mean Time To Recovery
* Verification accuracy

This allows future experiments to compare different levels of automation while retaining measurable safety boundaries.

---

## Product Relevance

For a future CloudOps Autopilot product, customers may require different automation policies.

Possible product modes include:

```text
Mode 1:
Recommendation Only

Mode 2:
Human Approval Required

Mode 3:
Controlled Autonomous Remediation
```

The current MVP establishes **Mode 2** as the default operational model.

This provides a foundation for future policy-based automation without requiring unrestricted autonomy.

---

## Decision Summary

CloudOps Autopilot will require **human approval before infrastructure-changing remediation actions** in the current MVP.

The system can automatically:

* Detect incidents
* Collect evidence
* Diagnose probable causes
* Assess risk
* Recommend actions
* Apply safety guardrails

But it must receive explicit approval before executing an infrastructure-changing remediation action.

The architecture therefore maintains:

```text
Analysis
   ↓
Recommendation
   ↓
Safety Boundary
   ↓
Human Approval
   ↓
Remediation
   ↓
Verification
```

This decision establishes a controlled, explainable, and auditable foundation for gradually increasing automation while maintaining operational safety.

---

## Related Architecture Decisions

* [ADR-001: Repository Pattern](./ADR-001-repository-pattern.md)
* [ADR-002: DynamoDB Persistence](./ADR-002-dynamodb-persistence.md)
* [ADR-004: Conditional Write and Idempotency](./ADR-004-conditional-write-idempotency.md)

## Related Documentation

* [System Architecture](../architecture/system-architecture.md)
* [AWS Architecture](../architecture/aws-architecture.md)
* [Incident Lifecycle](../architecture/incident-lifecycle.md)
* [Product Requirements](../requirements/product-requirements.md)
