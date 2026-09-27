# ADR-001: Repository Pattern for Incident Persistence

## Status

Accepted

## Date

2026-09-27

## Decision

CloudOps Autopilot uses the **Repository Pattern** to separate incident persistence logic from the core application and domain logic.

The application interacts with incidents through the `IncidentRepository` abstraction rather than directly interacting with DynamoDB or another persistence technology.

The current implementations are:

* `InMemoryIncidentRepository` — used for development and unit testing.
* `DynamoDBIncidentRepository` — used for AWS-backed incident persistence.

The architecture is:

```text
CloudOps Application
        |
        v
IncidentRepository
   (abstraction)
        |
   +----+----+
   |         |
   v         v
In-Memory  DynamoDB
Repository Repository
```

## Context

CloudOps Autopilot needs to persist incident information across the incident lifecycle.

An incident may move through states such as:

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

The platform needs to store information such as:

* Incident ID
* Incident type
* Severity
* Affected resource
* Detection timestamp
* Current lifecycle state
* Incident description

The application should not be tightly coupled to a specific database implementation.

If application code directly used DynamoDB everywhere, persistence logic would become mixed with detection, diagnosis, remediation, and lifecycle logic.

That would make the system harder to test, maintain, and evolve.

## Problem

Without a persistence abstraction, application code could become dependent on AWS-specific DynamoDB APIs.

For example:

```text
Detection Logic
      ↓
DynamoDB API
      ↓
DynamoDB Table
```

This creates several problems:

1. Unit tests become dependent on AWS resources.
2. Local development becomes harder.
3. Database-specific code spreads across the application.
4. Changing the persistence technology becomes more difficult.
5. Business logic becomes tightly coupled to infrastructure.
6. Testing failure scenarios becomes more complicated.

## Decision Drivers

The following requirements influenced this decision:

* Separation of concerns
* Testability
* Maintainability
* Infrastructure independence
* Local development support
* AWS integration
* Future scalability
* Clear architecture boundaries
* Ability to replace the persistence implementation

## Repository Abstraction

The repository interface defines the persistence operations required by the application.

Current interface:

```python
from abc import ABC, abstractmethod

from cloudops_engine.models.incident import Incident


class IncidentRepository(ABC):
    """Define persistence operations for incidents."""

    @abstractmethod
    def save(self, incident: Incident) -> None:
        """Persist an incident."""
        raise NotImplementedError

    @abstractmethod
    def get(self, incident_id: str) -> Incident | None:
        """Retrieve an incident by ID."""
        raise NotImplementedError

    @abstractmethod
    def update(self, incident: Incident) -> None:
        """Update an existing incident."""
        raise NotImplementedError
```

The interface defines **what the application needs**, while individual repository implementations define **how the data is stored**.

## In-Memory Repository

The `InMemoryIncidentRepository` stores incidents in a Python dictionary.

It is primarily used for:

* Unit testing
* Local development
* Fast execution
* Testing business logic without AWS dependencies

Conceptually:

```text
Application
     ↓
IncidentRepository
     ↓
InMemoryIncidentRepository
     ↓
Python Dictionary
```

This allows tests to execute without requiring a live DynamoDB table.

## DynamoDB Repository

The `DynamoDBIncidentRepository` provides the AWS-backed implementation.

Conceptually:

```text
Application
     ↓
IncidentRepository
     ↓
DynamoDBIncidentRepository
     ↓
Amazon DynamoDB
     ↓
cloudops-autopilot-incidents
```

The repository is responsible for:

* Creating DynamoDB requests
* Serializing `Incident` objects
* Reading DynamoDB items
* Deserializing DynamoDB items
* Updating incident records
* Preventing duplicate incident creation

The application does not need to know the DynamoDB API details.

## Separation of Responsibilities

The repository is responsible for **persistence**.

It should not be responsible for:

* Detecting incidents
* Diagnosing root causes
* Assessing remediation risk
* Selecting remediation actions
* Approving remediation
* Executing remediation
* Verifying recovery

Those responsibilities belong to other components.

The intended separation is:

```text
Detection
    ↓
Diagnosis
    ↓
Risk Assessment
    ↓
Recommendation
    ↓
Approval
    ↓
Remediation
    ↓
Verification
    ↓
Repository
    ↓
Persistence
```

The repository stores the state produced by these processes.

## Duplicate Incident Protection

The DynamoDB repository uses a conditional write when creating an incident:

```python
ConditionExpression="attribute_not_exists(incident_id)"
```

This prevents an existing incident with the same `incident_id` from being silently overwritten during creation.

The behavior is:

```text
New Incident
     ↓
Save Request
     ↓
Does incident_id already exist?
     |
   +---+---+
   |       |
  No      Yes
   |       |
   v       v
 Save    Reject
```

This provides an important persistence-level safety control.

## Testing Strategy

The Repository Pattern enables different levels of testing.

### Unit Tests

Business logic can use:

```text
InMemoryIncidentRepository
```

This avoids AWS dependencies and keeps tests fast.

### Repository Tests

The DynamoDB repository has tests for:

* Save and retrieve
* Update
* Duplicate incident rejection
* Missing incident update rejection

### Integration Tests

A live DynamoDB integration test verifies that incident lifecycle changes are actually persisted.

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
```

This verifies the application-to-AWS persistence boundary.

## Alternatives Considered

### Direct DynamoDB Access

The application could directly call DynamoDB wherever persistence is required.

Rejected because it would increase coupling between application logic and AWS infrastructure.

### Global Database Utility

A shared database utility could expose DynamoDB operations throughout the application.

Rejected because it would still expose infrastructure details to multiple application components.

### ORM

An ORM could provide a higher-level persistence abstraction.

Not selected for the current implementation because the incident model is relatively small and DynamoDB is already the selected persistence technology.

An ORM can be reconsidered if the persistence requirements become significantly more complex.

## Consequences

### Positive Consequences

The decision provides:

* Clear separation of concerns
* Better unit-testability
* Easier local development
* Reduced infrastructure coupling
* Easier AWS integration
* Clear persistence boundaries
* Ability to introduce another repository implementation later

For example, a future implementation could be:

```text
IncidentRepository
       |
   +---+-------+---------+
   |           |         |
   v           v         v
In-Memory   DynamoDB   Other DB
```

The core application would not need to change its persistence contract.

### Negative Consequences

The Repository Pattern introduces additional abstraction.

Instead of directly calling DynamoDB, the application has:

```text
Application
    ↓
Repository Interface
    ↓
Repository Implementation
    ↓
Database
```

This means there are additional files and interfaces to maintain.

For a very small application, this could be considered unnecessary complexity.

For CloudOps Autopilot, the abstraction is justified because the project is intended to evolve into a larger cloud operations platform with stronger testing, multiple environments, and potentially additional persistence requirements.

## Security Considerations

The repository does not receive unrestricted AWS permissions.

The current DynamoDB access follows the project's least-privilege approach.

The application is allowed to interact with the intended incident table rather than being granted unrestricted DynamoDB access.

The repository therefore acts as a persistence boundary, while IAM remains the AWS authorization boundary.

## Reliability Considerations

Persistence failures must not be silently ignored.

Future production improvements should include:

* Explicit AWS API error handling
* Retry policies where appropriate
* Exponential backoff
* Timeout handling
* Structured logging
* Persistence failure metrics
* Dead-letter or recovery mechanisms for asynchronous workflows
* Stronger conditional updates where concurrent state changes are possible

These are future reliability improvements and are not all implemented in the current prototype.

## Future Evolution

The repository abstraction can support future requirements such as:

* Incident history
* Audit events
* Remediation records
* Verification results
* Multi-account incident storage
* Additional database implementations
* Event-driven persistence
* Historical analytics
* Research evaluation datasets

The persistence model can therefore evolve without forcing persistence-specific logic into the detection, diagnosis, or remediation components.

## Implementation Reference

Current implementation:

```text
src/cloudops_engine/repositories/
├── incident_repository.py
├── in_memory_incident_repository.py
└── dynamodb_incident_repository.py
```

Tests:

```text
tests/
├── unit/
│   ├── test_in_memory_incident_repository.py
│   └── test_dynamodb_incident_repository.py
└── integration/
    └── test_dynamodb_incident_persistence.py
```

## Decision Summary

CloudOps Autopilot uses the Repository Pattern because persistence should remain separated from the incident-management domain logic.

The application depends on the `IncidentRepository` abstraction, while concrete implementations handle storage details.

This design improves:

* Maintainability
* Testability
* Separation of concerns
* Infrastructure independence
* Future extensibility

The decision is therefore **Accepted** for the current architecture.

## Related Architecture Decisions

- [ADR-002: DynamoDB Persistence](./ADR-002-dynamodb-persistence.md)
- [ADR-003: Human Approval Before Remediation](./ADR-003-human-approval.md)
- [ADR-004: Conditional Write and Idempotency](./ADR-004-conditional-write-idempotency.md)

## Related Documentation

- [System Architecture](../architecture/system-architecture.md)
- [AWS Architecture](../architecture/aws-architecture.md)
- [Incident Lifecycle](../architecture/incident-lifecycle.md)
- [Product Requirements](../requirements/product-requirements.md)