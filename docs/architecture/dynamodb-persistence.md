# CloudOps Autopilot — DynamoDB Persistence

## 1. Persistence Context

CloudOps Autopilot requires persistent incident records so that incidents detected by the monitoring and detection layers can be stored, retrieved, and updated throughout their lifecycle.

The persistence layer provides a controlled boundary between the application domain and Amazon DynamoDB.

This capability establishes:

* Persistent incident records
* Repository-based persistence abstraction
* Incident creation and retrieval
* Safe incident updates
* Duplicate incident protection
* Conditional DynamoDB writes
* Incident serialization and deserialization
* Real AWS DynamoDB integration testing

---

## 2. Persistence Objective

The persistence layer is responsible for maintaining the authoritative incident record used by the application.

The primary objectives are:

1. Persist newly detected incidents.
2. Prevent duplicate incident creation.
3. Retrieve incidents using their unique incident identifier.
4. Update existing incident records safely.
5. Reject updates for incidents that do not exist.
6. Convert domain objects into DynamoDB-compatible records.
7. Reconstruct domain objects from DynamoDB records.
8. Provide a repository abstraction independent of the storage implementation.

---

## 3. Persistence Architecture

The application uses a repository pattern to isolate domain logic from the database implementation.

```text
+----------------------+
|   CloudOps Engine    |
|                      |
| Incident Lifecycle   |
+----------+-----------+
           |
           v
+----------------------+
| IncidentRepository   |
|      Interface       |
+----------+-----------+
           |
           v
+------------------------------+
| DynamoDBIncidentRepository   |
+--------------+---------------+
               |
               v
+------------------------------+
|     Amazon DynamoDB          |
|                              |
| cloudops-autopilot-incidents|
+------------------------------+
```

The application interacts with the repository abstraction rather than directly accessing DynamoDB throughout the codebase.

---

## 4. Repository Abstraction

The persistence layer follows the repository pattern.

The repository abstraction defines persistence operations for incidents while allowing the underlying storage implementation to change independently.

The current repository supports:

* `save()`
* `get()`
* `update()`

The implementation is provided by:

```text
src/cloudops_engine/repositories/
    incident_repository.py
    dynamodb_incident_repository.py
```

This separation keeps application logic independent from AWS-specific persistence details.

---

## 5. Incident Persistence Lifecycle

Incident persistence follows the application lifecycle.

```text
Incident Detected
       |
       v
Create Incident Object
       |
       v
Repository.save()
       |
       v
DynamoDB Incident Record
       |
       v
Incident Lifecycle Updates
       |
       v
Repository.update()
       |
       v
Updated DynamoDB Record
```

Incident records can subsequently be retrieved using their unique `incident_id`.

---

## 6. DynamoDB Table

The primary incident persistence table is:

```text
Table Name:
cloudops-autopilot-incidents
```

AWS Region:

```text
ap-south-1
```

Partition key:

```text
incident_id
```

Key type:

```text
String
```

The incident identifier uniquely identifies each incident record.

---

## 7. Incident Record Schema

The current DynamoDB record contains the following attributes:

| Attribute | Description |
|---|---|
| `incident_id` | Unique incident identifier |
| `incident_type` | Type of detected incident |
| `severity` | Incident severity |
| `resource` | Affected AWS resource |
| `detected_at` | Incident detection timestamp |
| `status` | Current incident lifecycle state |
| `description` | Human-readable incident description |

Example logical record:

```json
{
  "incident_id": "INC-001",
  "incident_type": "HIGH_CPU",
  "severity": "HIGH",
  "resource": "i-example",
  "detected_at": "2026-09-28T10:30:00+00:00",
  "status": "DETECTED",
  "description": "EC2 CPU utilization exceeded the configured threshold."
}
```

---

## 8. Incident Creation

New incidents are persisted using the repository `save()` operation.

The implementation uses a DynamoDB conditional expression:

```text
attribute_not_exists(incident_id)
```

This prevents an existing incident from being silently overwritten during creation.

The persistence flow is:

```text
save(incident)
     |
     v
Serialize Incident
     |
     v
DynamoDB PutItem
     |
     +---- incident_id does not exist
     |           |
     |           v
     |       Record created
     |
     +---- incident_id already exists
                 |
                 v
        Conditional write fails
                 |
                 v
        ValueError is raised
```

This provides duplicate incident protection at the database boundary.

---

## 9. Incident Retrieval

Existing incidents can be retrieved using:

```python
repository.get(incident_id)
```

The repository performs a DynamoDB `GetItem` operation using the incident identifier as the partition key.

If the incident exists:

```text
DynamoDB Item
     |
     v
Deserialize
     |
     v
Incident object
```

If no matching record exists, the repository returns:

```python
None
```

---

## 10. Incident Updates

Incident lifecycle transitions require existing records to be updated.

The repository provides:

```python
repository.update(incident)
```

The update operation uses a conditional DynamoDB write.

The current condition is:

```text
attribute_exists(incident_id)
```

This ensures that an update is only accepted when the incident record already exists.

---

## 11. Conditional Update Semantics

The previous update approach required two separate operations:

```text
GET
 ↓
Check existence
 ↓
PUT
```

This creates an unnecessary race window between the existence check and the write.

The current implementation delegates the existence check to DynamoDB itself:

```text
PUT + ConditionExpression
          |
          v
DynamoDB checks incident_id
          |
      +---+---+
      |       |
   Exists   Missing
      |       |
      v       v
   Update   Reject
```

The repository therefore uses:

```python
ConditionExpression="attribute_exists(incident_id)"
```

This makes the existence requirement part of the database write operation.

---

## 12. Missing Incident Handling

If an update is attempted for an incident that does not exist, DynamoDB raises a conditional check failure.

The repository converts this storage-level failure into an application-level error:

```text
ConditionalCheckFailedException
            |
            v
ValueError
            |
            v
Incident not found
```

The resulting error format is:

```text
Incident not found: <incident_id>
```

This keeps AWS-specific exception handling inside the repository layer.

---

## 13. Serialization

The repository converts an `Incident` domain object into a DynamoDB-compatible dictionary.

The serialization process includes:

```text
Incident object
     |
     v
_serialize()
     |
     v
DynamoDB item
```

The detection timestamp is normalized to UTC when it does not already contain timezone information.

The timestamp is stored using ISO 8601 representation.

Example:

```text
2026-09-28T10:30:00+00:00
```

---

## 14. Deserialization

DynamoDB records are converted back into application domain objects using `_deserialize()`.

The process is:

```text
DynamoDB item
     |
     v
Read attributes
     |
     v
Parse detected_at
     |
     v
Incident object
```

This allows the rest of the application to work with the domain model instead of raw DynamoDB dictionaries.

---

## 15. Persistence Boundary

The repository acts as the persistence boundary for incident data.

```text
+----------------------------+
| Application / Domain Logic |
+-------------+--------------+
              |
              | Incident object
              v
+----------------------------+
| Incident Repository        |
+-------------+--------------+
              |
              | AWS-specific operations
              v
+----------------------------+
| Amazon DynamoDB            |
+----------------------------+
```

AWS-specific persistence behavior remains isolated inside the repository implementation.

---

## 16. Duplicate Protection

Incident creation is protected against duplicate identifiers.

The protection is enforced by DynamoDB rather than only by application-side validation.

```text
New Incident
     |
     v
incident_id
     |
     v
attribute_not_exists()
     |
 +---+---+
 |       |
New    Existing
 |       |
 v       v
Save    Reject
```

This prevents accidental replacement of an existing incident during creation.

---

## 17. Update Safety

Incident updates are similarly protected.

The repository does not first perform a separate existence lookup.

Instead, DynamoDB evaluates:

```text
attribute_exists(incident_id)
```

as part of the write operation.

This reduces the number of database operations required for an update and removes the explicit application-level GET-before-PUT existence check.

---

## 18. AWS Integration

The repository creates a DynamoDB resource using boto3.

Current AWS configuration:

```text
Service:
Amazon DynamoDB

Region:
ap-south-1

Table:
cloudops-autopilot-incidents
```

The repository receives the table name and AWS region through constructor parameters, with development defaults defined in the implementation.

---

## 19. Testing Strategy

Persistence testing is divided into unit-level and AWS integration-level validation.

### Unit / repository validation

The existing repository tests cover:

* Save and retrieve
* Existing incident update
* Duplicate incident rejection
* Missing incident update rejection

### Integration validation

A dedicated integration test validates the real DynamoDB persistence flow.

The integration test verifies:

```text
Save
 ↓
Get
 ↓
Update
 ↓
Get updated record
 ↓
Cleanup
```

The test uses the actual:

```text
cloudops-autopilot-incidents
```

DynamoDB table.

---

## 20. Validation Results

Repository-specific validation completed successfully.

```text
Repository unit tests:
4 passed

DynamoDB integration test:
1 passed

Combined repository validation:
5 passed
```

The complete project regression suite also passed:

```text
83 passed
```

This confirms that the persistence change did not break the existing application functionality.

---

## 21. Implementation References

Primary implementation:

```text
src/cloudops_engine/repositories/dynamodb_incident_repository.py
```

Repository abstraction:

```text
src/cloudops_engine/repositories/incident_repository.py
```

Unit tests:

```text
tests/unit/test_dynamodb_incident_repository.py
```

Integration tests:

```text
tests/integration/test_dynamodb_incident_repository.py
```

Incident domain model:

```text
src/cloudops_engine/models/incident.py
```

---

## 22. Current Limitations

The current persistence implementation is intentionally focused on the core incident record.

Current limitations include:

* No DynamoDB TTL configuration for historical incident retention.
* No secondary indexes are currently required by the application.
* No pagination API is currently implemented for listing incidents.
* Persistence retries are not yet implemented as a dedicated repository policy.
* Optimistic versioning is not currently implemented for concurrent lifecycle updates.
* The development implementation uses boto3 directly rather than a more advanced persistence abstraction.

These concerns can be addressed during later production-hardening work if required.

---

## 23. Future Enhancements

Potential future persistence improvements include:

* Incident retention and TTL policies
* Query and listing capabilities
* Secondary indexes for operational investigations
* Optimistic concurrency control
* Persistence retry strategies
* Dead-letter handling for persistent failures
* Audit-oriented historical records
* Production IAM role-based access
* Infrastructure provisioning through Terraform

These enhancements should be introduced based on actual operational requirements rather than adding unnecessary infrastructure prematurely.

---

## 24. Architectural Outcome

The persistence layer now provides a reliable storage boundary for CloudOps Autopilot incidents.

The architecture supports:

```text
Detection
   ↓
Incident Object
   ↓
Repository
   ↓
DynamoDB
   ↓
Persistent Incident Record
```

The persistence boundary provides:

* Durable incident storage
* Duplicate protection
* Safe conditional updates
* Incident retrieval
* Domain-object serialization
* Domain-object reconstruction
* Real AWS integration validation

The use of DynamoDB conditional expressions moves important persistence invariants into the database operation itself.

This strengthens the reliability of incident lifecycle persistence while keeping AWS-specific behavior isolated from the application domain.

---

## Related Documentation

* `docs/architecture/system-architecture.md`
* `docs/architecture/aws-architecture.md`
* `docs/architecture/incident-lifecycle.md`
* `docs/architecture/notification-and-incident-records.md`
* `docs/research/research-problem.md`

## Related Architecture Decisions

* `docs/decisions/ADR-001-persistence-strategy.md`
* `docs/decisions/ADR-002-event-driven-architecture.md`
* `docs/decisions/ADR-003-incident-lifecycle.md`
* `docs/decisions/ADR-004-safety-and-human-approval.md`
