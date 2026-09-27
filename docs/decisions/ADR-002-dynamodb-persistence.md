# ADR-002: DynamoDB Persistence

## Status

Accepted

## Date

2026-09-27

## Context

CloudOps Autopilot detects cloud incidents and manages them through a defined incident lifecycle.

The initial prototype could keep incident information in application memory. However, in-memory state is not sufficient for a reliable incident automation platform because application restarts would remove incident information.

The platform needs persistent storage for:

* Incident identity
* Incident type
* Severity
* Affected resource
* Detection timestamp
* Current lifecycle state
* Incident description
* Future diagnosis and remediation information
* Historical incident records

Persistence is particularly important because CloudOps Autopilot is designed to detect, diagnose, remediate, and verify incidents over a lifecycle that may involve multiple application operations.

The persistence layer must therefore provide durable storage while remaining simple, scalable, secure, and compatible with the project's repository abstraction.

---

## Problem

CloudOps Autopilot needs a persistence mechanism that can:

1. Store incident records durably.
2. Retrieve incidents using a unique incident identifier.
3. Update incident lifecycle state.
4. Prevent accidental duplicate incident creation.
5. Support automated application access.
6. Scale without requiring database server management.
7. Support the AWS-native architecture of the platform.
8. Work cleanly behind the Repository Pattern.
9. Keep operational complexity appropriate for the MVP.
10. Support future expansion of the incident record.

The persistence solution should not tightly couple the domain model to a specific database implementation.

---

## Decision

CloudOps Autopilot will use **Amazon DynamoDB** as the primary persistent storage system for incident records.

The application will access DynamoDB through the repository abstraction defined by **ADR-001 — Repository Pattern**.

The current implementation uses:

```text
Incident
   ↓
IncidentRepository
   ↓
DynamoDBIncidentRepository
   ↓
Amazon DynamoDB
```

This keeps the domain model and business logic independent from DynamoDB-specific implementation details.

---

## Decision Drivers

The decision is based on the following factors:

* Durability
* AWS-native integration
* Operational simplicity
* Scalability
* Low infrastructure management overhead
* Serverless-friendly architecture
* Pay-per-request pricing
* Fine-grained IAM control
* Conditional writes
* Fast key-based access
* Compatibility with the repository abstraction
* Suitability for incident-oriented workloads

---

## Why DynamoDB

### 1. AWS-Native Integration

CloudOps Autopilot is designed primarily around AWS services.

DynamoDB integrates naturally with:

* IAM
* Lambda
* ECS
* CloudWatch
* EventBridge
* AWS SDK
* CloudTrail
* AWS monitoring and security services

This reduces the operational complexity of introducing a separate database platform.

---

### 2. Managed Service

DynamoDB is a fully managed NoSQL database.

The application does not need to manage:

* Database servers
* Operating systems
* Database patching
* Database installation
* Traditional database clustering
* Manual capacity provisioning for the current workload

This allows the project to focus on incident automation rather than database administration.

---

### 3. Scalability

CloudOps Autopilot may eventually monitor incidents across multiple:

* AWS accounts
* Regions
* Applications
* EC2 instances
* Containers
* Kubernetes clusters
* Cloud services

The number of incident records can therefore grow significantly.

DynamoDB provides a scalable persistence model suitable for this type of workload.

---

### 4. Key-Based Incident Retrieval

Each incident has a unique `incident_id`.

The current table uses:

```text
Partition Key:
incident_id
```

Example:

```text
INC-001
INC-002
INC-003
```

This supports direct retrieval of an incident using its unique identifier.

---

## Current DynamoDB Table

Table name:

```text
cloudops-autopilot-incidents
```

Region:

```text
ap-south-1
```

Billing mode:

```text
PAY_PER_REQUEST
```

Partition key:

```text
incident_id
```

Data type:

```text
String
```

---

## Current Incident Data Model

The current persistence model stores:

| Attribute       | Purpose                             |
| --------------- | ----------------------------------- |
| `incident_id`   | Unique incident identifier          |
| `incident_type` | Type of detected incident           |
| `severity`      | Incident severity                   |
| `resource`      | Affected AWS resource               |
| `detected_at`   | Incident detection timestamp        |
| `status`        | Current lifecycle state             |
| `description`   | Human-readable incident description |

Example conceptual record:

```text
incident_id   = INC-001
incident_type = HIGH_CPU
severity      = HIGH
resource      = i-05e3bbde2a13509f7
detected_at   = 2026-09-27T10:00:00+00:00
status        = INVESTIGATING
description   = CPU remained above threshold
```

---

## Why PAY_PER_REQUEST

The current DynamoDB table uses:

```text
PAY_PER_REQUEST
```

This is appropriate for the current MVP because incident traffic is:

* Variable
* Event-driven
* Potentially bursty
* Not yet predictable

The project should not provision fixed database capacity before actual workload characteristics are known.

Pay-per-request also reduces infrastructure configuration for the development and early product stages.

Capacity strategy can be reconsidered when production traffic patterns become measurable.

---

## Repository Abstraction

DynamoDB access is isolated behind:

```text
IncidentRepository
```

The repository defines operations such as:

```python
save()
get()
update()
```

The current implementation is:

```text
IncidentRepository
        │
        ├── InMemoryIncidentRepository
        │
        └── DynamoDBIncidentRepository
```

This allows the application to use the same persistence contract regardless of the underlying storage implementation.

---

## Separation of Responsibilities

The architecture separates responsibilities as follows:

```text
Incident Model
    ↓
Business Logic
    ↓
IncidentRepository
    ↓
DynamoDBIncidentRepository
    ↓
DynamoDB
```

### Incident Model

Represents the domain object.

### Business Logic

Controls incident detection, diagnosis, risk, remediation, and lifecycle behavior.

### Repository Interface

Defines persistence operations without exposing database implementation details.

### DynamoDB Repository

Handles DynamoDB-specific operations.

### DynamoDB

Provides durable persistent storage.

This separation prevents DynamoDB-specific logic from spreading throughout the application.

---

## Duplicate Incident Protection

Duplicate incident creation is a significant concern in automation systems.

The current DynamoDB repository uses a conditional write:

```python
ConditionExpression="attribute_not_exists(incident_id)"
```

This ensures that a new incident cannot overwrite an existing incident with the same identifier during the initial save operation.

Conceptually:

```text
Save Incident
      ↓
Does incident_id already exist?
      ↓
   ┌──Yes──→ Reject duplicate
   │
   No
   ↓
Create incident
```

This protection is implemented at the persistence layer rather than relying only on application-side checks.

---

## Why Conditional Writes

A simple application-side sequence such as:

```text
Check if exists
        ↓
If not exists
        ↓
Create
```

can suffer from race conditions when multiple processes execute at the same time.

The database should therefore enforce the uniqueness condition.

DynamoDB conditional writes provide that protection for the current incident creation path.

---

## Serialization and Deserialization

The application uses Python dataclasses for domain models.

DynamoDB stores data as DynamoDB attributes.

Therefore, the repository performs conversion between the two representations.

```text
Incident Object
      ↓
Serialization
      ↓
DynamoDB Item
```

and:

```text
DynamoDB Item
      ↓
Deserialization
      ↓
Incident Object
```

The conversion logic remains inside the DynamoDB repository.

This prevents persistence-specific serialization logic from leaking into the domain model.

---

## Timestamp Handling

Incident timestamps are persisted using ISO 8601 representation.

Example:

```text
2026-09-27T10:00:00+00:00
```

The repository normalizes timestamps to UTC when a naive timestamp is encountered.

This provides a consistent representation for incident records.

---

## Incident Lifecycle Persistence

The incident lifecycle is persisted as the incident changes state.

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

The persistence layer therefore allows the system to recover the current state of an incident rather than relying entirely on in-memory application state.

---

## Update Strategy

The current implementation retrieves the incident before updating it.

Conceptually:

```text
Get incident
     ↓
Does incident exist?
     ↓
   Yes
     ↓
Update incident
```

If the incident does not exist, the repository raises an error instead of silently creating a new record.

This protects the distinction between:

* Creating a new incident
* Updating an existing incident

Future versions may strengthen this behavior using fully conditional DynamoDB update expressions.

---

## Alternatives Considered

### 1. In-Memory Storage

Rejected as the primary persistence mechanism.

Advantages:

* Very simple
* Fast
* Useful for unit testing

Limitations:

* Data is lost when the process stops.
* Cannot provide durable incident history.
* Not suitable for distributed execution.

The project therefore retains an in-memory repository for testing but does not use it as the production persistence mechanism.

---

### 2. Amazon RDS

RDS was considered.

Advantages:

* Relational data model
* SQL support
* Strong relational capabilities
* Useful for complex relational queries

However, the current incident workload primarily requires:

* Key-based incident retrieval
* Simple record updates
* Durable event/incident storage
* High scalability
* Low operational overhead

Introducing a relational database would add unnecessary infrastructure complexity for the current MVP.

RDS may be reconsidered if future requirements introduce substantial relational reporting or transactional data relationships.

---

### 3. Amazon Aurora

Aurora provides managed relational database capabilities and could support more complex transactional workloads.

However, the current MVP does not require a relational database architecture.

Aurora would introduce additional database infrastructure considerations that are not necessary for the current incident persistence requirements.

---

### 4. Amazon S3

S3 is already part of the broader CloudOps ecosystem and is excellent for:

* Objects
* Logs
* Large datasets
* Historical archives
* Data lake workloads

However, the incident service requires frequent key-based retrieval and state updates.

DynamoDB is therefore used for the operational incident state, while S3 can be considered for future archival or large historical datasets.

---

## Security Considerations

DynamoDB access is controlled through IAM.

The development IAM user was granted a restricted custom policy for the specific incident table.

The policy allows required operations such as:

* `dynamodb:GetItem`
* `dynamodb:PutItem`
* `dynamodb:UpdateItem`
* `dynamodb:DeleteItem`
* `dynamodb:DescribeTable`

Table creation and table listing permissions were used during the bootstrap phase.

The project deliberately avoids broad unrestricted DynamoDB access.

---

## Least-Privilege Principle

The application should only receive the DynamoDB permissions required for its operational responsibilities.

The architecture should avoid policies such as:

```text
dynamodb:*
```

across all resources unless explicitly justified.

The target production architecture should further separate:

```text
Infrastructure provisioning permissions
```

from:

```text
Runtime application permissions
```

This reduces the blast radius of credential compromise or application failure.

---

## Reliability Considerations

DynamoDB provides managed persistent storage, but persistence failures must still be handled by the application.

Future reliability improvements include:

* Retry with exponential backoff
* Timeout handling
* AWS SDK retry configuration
* Structured error classification
* Circuit-breaking where appropriate
* Dead-letter handling for asynchronous workflows
* Monitoring of DynamoDB errors
* Persistence failure alerts

These are part of the later Error Handling & Reliability Strategy.

---

## Testing Strategy

The DynamoDB persistence implementation is tested at multiple levels.

### Unit Tests

Repository behavior is tested using isolated test cases.

Examples include:

* Save and retrieve incident
* Update incident
* Reject duplicate incident
* Reject update for missing incident

### Integration Test

The project also uses an integration test against the actual DynamoDB table.

The lifecycle is tested through:

```text
DETECTED
→ ACKNOWLEDGED
→ INVESTIGATING
→ REMEDIATING
→ VERIFYING
→ RESOLVED
```

The integration test removes its test record after execution.

This prevents test data from accumulating in the development table.

---

## Current Implementation

The current repository implementation is:

```text
src/cloudops_engine/repositories/
├── incident_repository.py
├── in_memory_incident_repository.py
└── dynamodb_incident_repository.py
```

### Interface

```text
IncidentRepository
```

### Development/Test Implementation

```text
InMemoryIncidentRepository
```

### AWS Implementation

```text
DynamoDBIncidentRepository
```

This structure follows the Repository Pattern documented in ADR-001.

---

## Consequences

### Positive Consequences

Using DynamoDB provides:

* Durable incident persistence
* AWS-native integration
* Low infrastructure management overhead
* Scalable storage
* Fast key-based access
* Conditional write support
* IAM-based security
* Compatibility with serverless architectures
* Clear separation through the repository pattern

---

### Negative Consequences

The decision also introduces:

* DynamoDB-specific implementation code
* NoSQL data-model constraints
* Need to design access patterns carefully
* Additional AWS dependency
* Potential complexity for advanced relational reporting
* Need for additional operational monitoring
* Need to carefully design future indexes and query patterns

These trade-offs are accepted for the current incident persistence workload.

---

## Future Evolution

As CloudOps Autopilot grows, the persistence architecture may evolve.

Potential future capabilities include:

### Global Secondary Indexes

Possible access patterns could include querying incidents by:

```text
resource
incident_type
severity
status
detected_at
```

Indexes should only be introduced when justified by actual access patterns.

---

### Incident History

Future records may include:

* Diagnosis evidence
* Risk assessment
* Recommendation
* Approval information
* Remediation action
* Remediation result
* Verification result
* Audit information

---

### Event History

The platform may eventually separate:

```text
Current Incident State
```

from:

```text
Incident Event History
```

This could support a more complete audit trail.

---

### Archival

Older incident records could eventually be archived to S3 for:

* Long-term retention
* Research analysis
* Historical reporting
* Machine learning datasets
* Cost optimization

---

### Multi-Account Architecture

As the platform evolves toward multi-account AWS monitoring, the incident identity model may need to incorporate:

```text
AWS Account
Region
Resource
Incident
```

The DynamoDB key design would then be reviewed according to actual access patterns.

---

## Production Considerations

The current DynamoDB implementation is suitable for the project's development and MVP stage.

Before production deployment, the following areas require additional design:

* Production IAM roles
* Encryption requirements
* Backup and recovery strategy
* Retention policy
* Monitoring and alerting
* Capacity/access-pattern review
* Multi-account strategy
* Disaster recovery requirements
* Audit requirements
* Data lifecycle management

These will be addressed in the relevant security, reliability, observability, and production-readiness documentation.

---

## Relationship to the Overall Architecture

DynamoDB is responsible for **persistent incident state**.

It is not responsible for:

* Incident detection
* Diagnosis
* Risk assessment
* Remediation decisions
* Human approval
* Verification

Those responsibilities remain within their respective application components.

The architecture therefore remains:

```text
AWS Monitoring
      ↓
Detection
      ↓
Evidence
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
      ↓
DynamoDB
```

DynamoDB records the operational state and history required by the incident management system.

---

## Decision Summary

CloudOps Autopilot uses **Amazon DynamoDB as the persistent incident store** because it provides a managed, scalable, AWS-native persistence layer that fits the application's key-based incident access patterns.

The database is accessed through the Repository Pattern, keeping persistence concerns separated from the domain and application logic.

The current design uses:

```text
DynamoDB
├── Table: cloudops-autopilot-incidents
├── Region: ap-south-1
├── Billing: PAY_PER_REQUEST
└── Partition Key: incident_id
```

Conditional writes provide duplicate incident protection, while the repository abstraction preserves maintainability and testability.

The decision is accepted for the current MVP and will be revisited if future access patterns, scale, relational requirements, or multi-account requirements justify changes.

---

## Related Architecture Decisions

* [ADR-001: Repository Pattern](./ADR-001-repository-pattern.md)
* [ADR-003: Human Approval Before Remediation](./ADR-003-human-approval.md)
* [ADR-004: Conditional Write and Idempotency](./ADR-004-conditional-write-idempotency.md)

## Related Documentation

* [System Architecture](../architecture/system-architecture.md)
* [AWS Architecture](../architecture/aws-architecture.md)
* [Incident Lifecycle](../architecture/incident-lifecycle.md)
* [Product Requirements](../requirements/product-requirements.md)
