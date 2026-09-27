# CloudOps Autopilot — Testing Strategy

## 1. Purpose

This document defines the testing strategy for CloudOps Autopilot.

CloudOps Autopilot is an automation platform that can eventually interact with cloud infrastructure. Therefore, testing must validate not only whether the code works, but also whether the system behaves safely under normal, abnormal, and failure conditions.

The testing strategy covers:

* Unit testing
* Integration testing
* AWS integration testing
* End-to-end testing
* Failure testing
* Security testing
* Reliability testing
* Performance testing
* Regression testing
* Research experimentation
* CI/CD quality gates

The central principle is:

> **Every automation capability must be tested for correctness, safety, failure behavior, and recovery before it is trusted with infrastructure-changing actions.**

---

# 2. Testing Principles

CloudOps Autopilot follows these testing principles:

1. Test behavior, not implementation details.
2. Keep unit tests deterministic.
3. Separate unit tests from AWS-dependent tests.
4. Use integration tests for real AWS interactions.
5. Test failure paths explicitly.
6. Test security boundaries negatively.
7. Test lifecycle transitions.
8. Test idempotency.
9. Test verification independently from remediation.
10. Keep production infrastructure isolated from tests.
11. Clean up integration-test resources.
12. Run regression tests before milestones.
13. Automate quality checks in CI/CD.
14. Make research experiments reproducible.

---

# 3. Testing Pyramid

The project follows a testing pyramid.

```text
                 /\
                /  \
               / E2E\
              /------\
             /Integr. \
            /----------\
           /   Unit     \
          /--------------\
```

The majority of tests should be fast unit tests.

Integration tests should be fewer and focused on actual AWS behavior.

End-to-end tests should validate complete workflows.

---

# 4. Test Levels

The project uses the following levels:

```text
Level 1 → Unit Tests
Level 2 → Component Tests
Level 3 → Integration Tests
Level 4 → End-to-End Tests
Level 5 → Security / Reliability / Performance Tests
Level 6 → Research Experiments
```

Each level answers a different question.

---

# 5. Unit Testing

Unit tests validate isolated application behavior.

Examples:

* Detection rules
* Diagnosis logic
* Risk assessment
* Recommendation logic
* Guardrails
* Incident lifecycle
* Idempotency
* Serialization
* Configuration validation

Unit tests should normally not require:

* AWS credentials
* Internet access
* Running EC2 instances
* DynamoDB tables
* CloudWatch APIs

---

# 6. Current Unit Testing Framework

The project uses:

```text id="yq2z7q"
pytest
```

The test configuration is defined in `pyproject.toml`.

Current configuration includes:

```toml
[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

This allows the test suite to import the application package consistently.

---

# 7. Unit Test Structure

The project follows a structure similar to:

```text
tests/
├── unit/
├── integration/
└── e2e/
```

Unit tests should focus on deterministic application behavior.

Example:

```text id="9d0w9s"
tests/unit/
├── test_detector.py
├── test_diagnosis.py
├── test_incident_lifecycle.py
├── test_guardrails.py
├── test_idempotency.py
└── test_repositories.py
```

---

# 8. Detection Testing

Detection is one of the most important components.

Tests should cover:

### High CPU

* CPU below threshold
* CPU equal to threshold
* CPU above threshold
* Fewer than required datapoints
* Exactly required datapoints
* Three consecutive breaches
* Non-consecutive breaches
* Mixed datapoints

Example:

```text id="l7q4t1"
[91, 92, 95]
```

should detect persistent high CPU when the configured threshold is `90`.

But:

```text id="uv9i0z"
[91, 80, 95]
```

should not trigger the three-consecutive-breach rule.

---

# 9. Application 5xx Testing

The application 5xx detector should be tested for:

* Below threshold
* Above threshold
* Consecutive breaches
* Non-consecutive breaches
* Insufficient datapoints
* Exact threshold behavior
* Multiple independent incidents

The tests should confirm that detection does not trigger from a single noisy datapoint when persistence is required.

---

# 10. Unhealthy Service Testing

The service-health detector should test:

```text id="fl6v1f"
[True, True, True]
```

No incident.

```text id="33vps7"
[False, False, False]
```

Incident detected.

```text id="c4jq9e"
[False, True, False]
```

No incident under the consecutive unhealthy rule.

The expected behavior must remain explicit and deterministic.

---

# 11. Evidence Testing

Evidence generation should be tested independently.

Tests should verify:

* Correct source
* Correct signal
* Correct value
* Correct timestamp
* Correct description
* Correct number of evidence records

The system should not report evidence that was not actually observed.

---

# 12. Diagnosis Testing

Diagnosis should be tested against different evidence strengths.

Examples:

```text id="y9w43a"
No evidence
```

should produce:

```text id="w9u4uw"
Probable cause = Unknown
Confidence = 0
```

Strong evidence should produce higher confidence according to the defined diagnosis logic.

The test should also verify that confidence remains within the valid range:

```text id="2f9hlh"
0.0 <= confidence <= 1.0
```

---

# 13. Diagnosis Uncertainty

Tests must ensure that the system does not manufacture a root cause when evidence is insufficient.

Example:

```text id="7h4l6u"
Insufficient Evidence
       ↓
Unknown Cause
       ↓
Low / Zero Confidence
```

This is an important safety property.

---

# 14. Risk Assessment Testing

Risk assessment tests should verify:

* Valid incident types
* Valid severity values
* Allowed risk levels
* Unknown incident behavior
* High-risk conditions
* Low-risk conditions

The system should never silently default an unknown situation to a permissive risk classification.

---

# 15. Recommendation Testing

Recommendation tests should verify:

* Correct action for the incident
* Correct risk relationship
* Unknown incident handling
* Unsupported action handling
* Recommendation consistency

Recommendation generation must remain separate from execution.

---

# 16. Guardrail Testing

Guardrails require extensive negative testing.

Tests should verify:

### Allowed

```text id="l4l5gi"
Approved action
+
Permitted risk
=
Allowed
```

### Blocked

```text id="h4u3h1"
Unknown action
=
Blocked
```

```text id="4gr0xy"
High-risk action
=
Blocked
```

```text id="5drxst"
Empty action
=
Blocked
```

The default behavior should remain restrictive.

---

# 17. Human Approval Testing

Approval logic should test:

* Approved action
* Rejected action
* Missing approval
* Invalid approval state
* Approval failure

Important safety rule:

```text id="z5y1qj"
No approval
    ↓
No remediation
```

Approval should never default to `True`.

---

# 18. Incident Lifecycle Testing

Every valid lifecycle transition should have a test.

Current lifecycle:

```text id="t5uf0o"
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

Invalid transitions must also be tested.

Examples:

```text id="y6w3jq"
DETECTED → RESOLVED
```

must fail.

```text id="x8ot6k"
RESOLVED → REMEDIATING
```

must fail.

This protects state-machine integrity.

---

# 19. Remediation Result Testing

`RemediationResult` should be tested for:

* SUCCESS
* FAILED
* SKIPPED
* Error message
* Timestamps
* Action identity

The result must accurately represent what happened.

---

# 20. Idempotency Testing

Idempotency is a critical safety property.

Tests should verify:

### First execution

```text id="2m9qzv"
Action → SUCCESS
```

### Same action again

```text id="b6x7ip"
Same Incident + Same Action
       ↓
SKIPPED
```

The system must not execute the same action repeatedly for the same incident.

---

# 21. Idempotency Key Testing

The following combinations should be tested:

```text id="4k8g5q"
INC-001 + ACTION-A
INC-001 + ACTION-A
```

should identify the same execution key.

But:

```text id="8i2g2a"
INC-001 + ACTION-A
INC-002 + ACTION-A
```

should be different.

Similarly:

```text id="j4b7y9"
INC-001 + ACTION-A
INC-001 + ACTION-B
```

should be different.

---

# 22. Repository Testing

Repository tests should verify the repository contract.

### Save

```text id="9x1j2u"
save()
```

should persist an incident.

### Get

```text id="8pr2wz"
get()
```

should retrieve the correct incident.

### Update

```text id="n4j7xe"
update()
```

should persist state changes.

### Missing

Retrieving a nonexistent incident should return the expected empty result.

### Duplicate

Creating the same incident twice should be rejected according to the repository contract.

---

# 23. In-Memory Repository Testing

The in-memory repository is useful for fast unit testing.

Tests should verify:

* Save
* Get
* Update
* Duplicate rejection
* Missing incident rejection

Because it does not require AWS, these tests should execute quickly.

---

# 24. DynamoDB Repository Testing

DynamoDB repository tests validate actual persistence behavior.

Tests should cover:

* Save
* Get
* Update
* Duplicate incident
* Missing incident
* Serialization
* Deserialization
* Timestamp handling

The project already includes dedicated DynamoDB repository tests.

---

# 25. Conditional Write Testing

The DynamoDB duplicate protection must be tested.

The repository uses:

```python
ConditionExpression="attribute_not_exists(incident_id)"
```

The test should confirm:

```text id="gk9v8h"
First save
   ↓
SUCCESS

Second save
   ↓
ConditionalCheckFailedException
   ↓
Application-level duplicate error
```

This validates database-level duplicate protection.

---

# 26. Integration Testing

Integration tests validate interactions between real components.

Examples:

```text id="t4ny2k"
Application
    ↓
CloudWatch
```

```text id="z9q6hr"
Application
    ↓
DynamoDB
```

Integration tests may require:

* AWS credentials
* AWS resources
* Network connectivity
* Correct IAM permissions

They should therefore be separated from normal unit tests.

---

# 27. Current DynamoDB Integration Test

The project includes a lifecycle persistence integration test.

It validates:

```text id="0z6p8h"
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
```

The test cleans up its test record afterward.

---

# 28. Integration Test Cleanup

Integration tests must clean up resources they create.

For example:

```python
finally:
    repository.table.delete_item(
        Key={
            "incident_id": incident.incident_id,
        }
    )
```

Cleanup prevents:

* Test pollution
* Unexpected AWS costs
* Duplicate test failures
* Persistent test data

---

# 29. AWS Integration Testing

AWS integration tests should use dedicated development/test resources.

They must not run against production resources.

Resources should have clear naming conventions.

Example:

```text id="2c8v2u"
TEST-DDB-001
TEST-LIFECYCLE-001
```

Test resource cleanup should be mandatory.

---

# 30. End-to-End Testing

End-to-end testing validates the complete incident lifecycle.

Target flow:

```text id="xj4c9z"
AWS Signal
   ↓
Detection
   ↓
Evidence
   ↓
Diagnosis
   ↓
Risk
   ↓
Recommendation
   ↓
Guardrails
   ↓
Approval
   ↓
Remediation
   ↓
Verification
   ↓
Persistence
   ↓
Resolved
```

The purpose is to verify that all major components work together.

---

# 31. Current E2E Limitation

The current remediation executor operates in simulation mode.

Therefore the current full workflow does not yet perform real infrastructure-changing remediation.

The project must not claim production-grade autonomous remediation testing until real remediation is implemented and separately tested.

---

# 32. Failure Testing

Failure paths are first-class test scenarios.

Tests should intentionally simulate:

* CloudWatch failure
* DynamoDB failure
* Permission denied
* Invalid configuration
* Invalid remediation action
* Approval rejection
* Remediation failure
* Verification failure
* Duplicate action
* Timeout
* Retry exhaustion

The objective is to verify safe behavior.

---

# 33. Failure Injection

Future failure-injection testing should simulate dependency failures.

Example:

```text id="qxxq7k"
CloudWatch
   ↓
Unavailable
```

Expected behavior:

```text id="j3kg2h"
No false "healthy" conclusion
```

Similarly:

```text id="7o7h8r"
DynamoDB
   ↓
Unavailable
```

should not produce a false statement that the incident was durably persisted.

---

# 34. Security Testing

Security tests should validate authorization boundaries.

Examples:

### Unauthorized DynamoDB resource

```text id="9w6j0y"
Access unauthorized table
        ↓
DENY
```

### Unauthorized remediation

```text id="g2b9v1"
Unsupported action
        ↓
Guardrail DENY
```

### Missing approval

```text id="4b5q6x"
No approval
        ↓
No execution
```

### High-risk action

```text id="v7x1pa"
High risk
   ↓
Blocked
```

These negative tests are as important as success tests.

---

# 35. IAM Testing

IAM behavior should be validated using least-privilege tests.

Tests should confirm that:

* Required actions succeed.
* Unnecessary actions fail.
* Restricted resources remain inaccessible.
* Remediation roles cannot perform unrelated operations.
* Production resources cannot be modified from development identities.

IAM testing should be performed in controlled environments.

---

# 36. Secrets Testing

The repository should be checked for accidental secret exposure.

Potential controls include:

* Git secret scanning
* Pre-commit scanning
* CI secret scanning
* Dependency/security scanning

The test objective is:

```text id="p8n4i1"
Credential accidentally committed
        ↓
Pipeline detects it
        ↓
Build blocked
```

---

# 37. Dependency Security Testing

Dependencies should be checked for known vulnerabilities.

Potential tools include:

* pip audit
* Dependabot
* GitHub security scanning
* Other approved vulnerability scanners

Dependency updates should be reviewed rather than blindly applied.

---

# 38. Performance Testing

Performance testing becomes important as the platform scales.

Potential measurements include:

* Detection latency
* Diagnosis latency
* Persistence latency
* Remediation execution latency
* Verification latency
* End-to-end incident processing time

The project should avoid optimizing prematurely.

Performance tests should be introduced when realistic workload requirements exist.

---

# 39. Load Testing

Future load testing should simulate multiple incidents.

Example:

```text id="4b0f6q"
Incident 1 ─┐
Incident 2 ─┤
Incident 3 ─┤
Incident 4 ─┤──→ CloudOps Engine
Incident 5 ─┘
```

The system should be evaluated for:

* Throughput
* Latency
* Concurrent processing
* DynamoDB behavior
* AWS API throttling
* Duplicate events
* Queue/event behavior

---

# 40. Concurrency Testing

Concurrency is especially important for remediation.

Example:

```text id="7k8l0e"
Worker A ─┐
          ├──→ Same Incident
Worker B ─┘
```

Both workers may attempt the same action.

The system must prevent unsafe duplicate execution.

This is one reason database-level conditional writes are important for incident identity.

Future durable remediation idempotency should provide similar protection for distributed workers.

---

# 41. Regression Testing

Every new feature should preserve existing behavior.

The full test suite should be run after significant changes.

Current project history demonstrates this approach.

Examples of major milestones include:

* Detection
* Diagnosis
* Remediation controls
* DynamoDB persistence

Each milestone was validated using the test suite before being committed.

---

# 42. Full Test Suite

The standard local command is:

```bash
pytest
```

The expected behavior is that all configured tests are executed.

The project should maintain a clean test result before a milestone is committed.

---

# 43. Test Naming

Tests should use descriptive names.

Prefer:

```python
def test_duplicate_incident_is_rejected():
    ...
```

over:

```python
def test_1():
    ...
```

Descriptive names make failures easier to understand.

---

# 44. Test Data

Test data should be:

* Deterministic
* Minimal
* Clearly identified
* Non-production
* Easy to clean up

Avoid depending on unpredictable live production data.

---

# 45. Mocking Strategy

Mocks should be used when testing isolated business logic.

For example:

```text id="1kz9b4"
Detector
   ↓
Mock CloudWatch data
```

This allows detection behavior to be tested without calling AWS.

However, excessive mocking can hide real integration problems.

Therefore:

```text id="rrd4k3"
Mock for unit tests
+
Real AWS for integration tests
```

is the preferred approach.

---

# 46. Test Isolation

Tests should not depend on execution order.

Bad pattern:

```text id="02a8hv"
Test A creates state
        ↓
Test B expects Test A state
```

Preferred:

```text id="8h8gzz"
Test A
Independent

Test B
Independent
```

Each test should create and clean up its own state where required.

---

# 47. Deterministic Testing

Tests should avoid unnecessary dependence on:

* Current time
* Random IDs
* Live network conditions
* Uncontrolled AWS state

Where time or randomness is part of behavior, testable abstractions should be introduced.

---

# 48. Test Environment Strategy

Testing should be separated by environment.

```text id="9un5fm"
Local
 ↓
Unit Tests

AWS Development
 ↓
Integration Tests

Dedicated Test Environment
 ↓
E2E / Failure Tests

Production
 ↓
Controlled Validation Only
```

Production should not be used as a general testing environment.

---

# 49. CI/CD Testing Strategy

Future GitHub Actions should execute automated quality checks.

A conceptual pipeline:

```text id="5h2tqf"
Pull Request
     ↓
Lint
     ↓
Type Check
     ↓
Unit Tests
     ↓
Security Scan
     ↓
Build
     ↓
Integration Tests
     ↓
Quality Gate
```

Only after required checks pass should deployment proceed.

---

# 50. Quality Gates

Recommended CI quality gates include:

* Formatting check
* Linting
* Unit tests
* Coverage threshold
* Type checking
* Dependency/security scanning
* Secret scanning
* Build validation

AWS integration tests may run in a controlled CI environment using short-lived credentials.

---

# 51. Code Coverage

Coverage should be treated as a signal rather than the only definition of quality.

Important areas should have strong coverage:

* Incident lifecycle
* Detection
* Guardrails
* Risk assessment
* Idempotency
* Persistence
* Failure handling

100% coverage does not guarantee correct behavior.

Behavioral and negative tests remain important.

---

# 52. Research Testing

Testing is also part of the research methodology.

Experiments should compare:

```text id="y7k8p5"
Manual Response
      VS
Controlled Automation
```

Potential metrics include:

* Detection time
* Diagnosis time
* Remediation time
* MTTR
* Remediation success rate
* False-positive rate
* Unsafe-action rate
* Human intervention
* Verification accuracy
* Duplicate action rate

---

# 53. Experimental Reproducibility

Research experiments should record:

* Experiment ID
* Environment
* Incident scenario
* Configuration
* Thresholds
* Test data
* Software version
* AWS resources
* Start time
* End time
* Results
* Failures
* Observations

This allows experiments to be repeated.

---

# 54. Research Scenario Testing

Initial research scenarios include:

### Scenario 1 — High CPU

```text id="4l0szh"
CPU > Threshold
```

### Scenario 2 — Application 5xx

```text id="b3f8x9"
5xx Error Rate > Threshold
```

### Scenario 3 — Unhealthy Service

```text id="8n6r8a"
Health Checks Failed
```

Each scenario should be tested under both normal and failure conditions.

---

# 55. Safety Testing for Research

Research experiments must never sacrifice safety for data collection.

For example:

```text id="i8c1hs"
Unsafe remediation
        ↓
Must remain blocked
```

The research environment should not intentionally bypass safety controls merely to demonstrate autonomous behavior.

---

# 56. Acceptance Testing

Before a capability is considered complete, it should satisfy:

```text id="b2p5gd"
Functional correctness
        +
Safety
        +
Failure handling
        +
Observability
        +
Test coverage
```

A feature is not complete merely because its happy path works.

---

# 57. Feature Completion Checklist

For every major feature:

```text id="m0m5t8"
[ ] Happy path works
[ ] Invalid input tested
[ ] Failure path tested
[ ] Negative security test added
[ ] Idempotency considered
[ ] Observability added
[ ] Integration behavior verified
[ ] Documentation updated
[ ] Regression suite passes
[ ] Git milestone created
```

---

# 58. Current Testing Status

The current project already has:

* Pytest configuration
* Unit tests
* Detection tests
* Lifecycle tests
* Guardrail tests
* Remediation tests
* Idempotency tests
* Repository tests
* DynamoDB integration tests
* Full regression execution
* Integration-test cleanup

The project previously reached:

```text id="4bdq8j"
61 passed
```

during the DynamoDB persistence milestone.

The exact count may change as additional tests are added.

---

# 59. Current Testing Gaps

Important remaining areas include:

* Full CloudWatch integration tests
* Full end-to-end workflow tests
* Failure injection framework
* IAM negative testing
* Security scanning
* Dependency vulnerability scanning
* Secret scanning
* Performance testing
* Concurrency testing
* Durable idempotency testing
* CI/CD automated quality gates
* Coverage reporting
* Production-like staging environment
* Disaster-recovery testing

---

# 60. Testing Maturity Roadmap

```text id="d3t2gr"
Unit Testing
     ↓
Integration Testing
     ↓
Regression Testing
     ↓
Failure Testing
     ↓
Security Testing
     ↓
E2E Testing
     ↓
CI/CD Quality Gates
     ↓
Performance / Load Testing
     ↓
Chaos / Failure Injection
     ↓
Production Reliability Testing
```

Testing maturity should increase alongside automation maturity.

---

# 61. Final Testing Principle

CloudOps Autopilot should never become more autonomous faster than it becomes testable.

The maturity relationship should be:

```text id="y9e6ju"
More Automation
      ↓
More Permissions
      ↓
More Risk
      ↓
More Testing Required
```

Therefore:

> **Automation capability, security controls, observability, and testing maturity must evolve together.**

A reliable CloudOps Autopilot system is one that can demonstrate not only that it works when everything is normal, but also that it behaves safely when things go wrong.

---

## Related Documentation

* [Product Requirements](requirements/product-requirements.md)
* [System Architecture](architecture/system-architecture.md)
* [AWS Architecture](architecture/aws-architecture.md)
* [Incident Lifecycle](architecture/incident-lifecycle.md)
* [Configuration Strategy](configuration-strategy.md)
* [Logging & Observability Strategy](logging-observability-strategy.md)
* [Error Handling & Reliability Strategy](error-handling-reliability-strategy.md)
* [Security & IAM Strategy](security-iam-strategy.md)

## Related Architecture Decisions

* [ADR-001: Repository Pattern](decisions/ADR-001-repository-pattern.md)
* [ADR-002: DynamoDB Persistence](decisions/ADR-002-dynamodb-persistence.md)
* [ADR-003: Human Approval Before Remediation](decisions/ADR-003-human-approval.md)
* [ADR-004: Conditional Write and Idempotency](decisions/ADR-004-conditional-write-idempotency.md)
