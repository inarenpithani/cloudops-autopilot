# CloudOps Autopilot — Notifications and Incident Records

## 1. Integration Context

CloudOps Autopilot requires persistent incident records and controlled notifications so that detected incidents can be tracked and communicated throughout the incident lifecycle.

Day 10 extends the existing incident-processing workflow with:

* Persistent incident records in Amazon DynamoDB
* Amazon SNS-based incident notifications
* Notification state policy
* Notification idempotency
* Duplicate notification protection
* Notification failure handling
* Integration testing against real AWS services

The implementation connects incident persistence and notification handling while maintaining separation between application logic and AWS infrastructure.

---

## 2. Integration Objective

The primary objective of Day 10 is to establish a reliable notification and incident-recording mechanism for CloudOps Autopilot incidents.

The implementation should:

* Persist detected incidents in DynamoDB
* Publish notifications for selected incident lifecycle states
* Deliver notifications through Amazon SNS
* Prevent duplicate notifications
* Allow failed notifications to be retried
* Keep notification infrastructure behind application-level services
* Validate the notification flow using real AWS resources

The implementation is intentionally limited to incident persistence and notification capabilities.

---

## 3. Notification and Incident Architecture

The Day 10 architecture is:

```text
CloudWatch Detection
        |
        v
Incident
        |
        +----------------------+
        |                      |
        v                      v
DynamoDB Incident Record   Notification Policy
                               |
                               v
                         Idempotency Claim
                               |
                               v
                           Amazon SNS
                               |
                               v
                       Email Subscription
```

The broader incident lifecycle is:

```text
Detect
   |
   v
Persist Incident
   |
   v
Notify DETECTED
   |
   v
Diagnose
   |
   v
Risk Assessment
   |
   v
Human Approval
   |
   v
Notify REMEDIATING
   |
   v
Remediation
   |
   v
Verification
   |
   v
Notify RESOLVED
```

Incident persistence and notification are separate responsibilities.

DynamoDB provides the persistent incident-record boundary.

SNS provides the notification delivery boundary.

---

## 4. Incident Record Persistence

CloudOps Autopilot uses DynamoDB to persist incident lifecycle information.

The existing incident repository is:

```text
src/cloudops_engine/repositories/dynamodb_incident_repository.py
```

The incident repository provides the persistence abstraction used by the application.

The Day 10 notification workflow uses the existing incident repository rather than introducing a separate incident-record implementation.

The incident persistence flow is:

```text
Incident Object
      |
      v
DynamoDBIncidentRepository
      |
      v
Amazon DynamoDB
      |
      v
cloudops-autopilot-incidents
```

The DynamoDB incident table is:

```text
Table:
cloudops-autopilot-incidents

Region:
ap-south-1

Partition Key:
incident_id

Billing Mode:
PAY_PER_REQUEST

Status:
ACTIVE
```

The application persists the incident after detection:

```text
Detection
   |
   v
Incident Created
   |
   v
incident_repository.save()
   |
   v
DynamoDB
```

Subsequent lifecycle state changes are persisted using the repository update operation.

---

## 5. Notification Policy

Not every lifecycle state requires an external notification.

The notification policy is implemented in:

```text
src/cloudops_engine/notifications/policy.py
```

The current notification states are:

```text
DETECTED
REMEDIATING
RESOLVED
```

These states trigger notifications.

The following states do not currently trigger notifications:

```text
ACKNOWLEDGED
INVESTIGATING
VERIFYING
```

The policy is implemented using:

```python
NOTIFIABLE_STATES = {
    "DETECTED",
    "REMEDIATING",
    "RESOLVED",
}
```

The application checks the policy through:

```python
should_notify(state)
```

This keeps notification decisions separate from the incident lifecycle model.

---

## 6. Amazon SNS Integration

Amazon SNS provides the notification delivery mechanism.

The AWS integration is implemented in:

```text
src/cloudops_engine/aws/sns.py
```

The application uses an `SNSClient` abstraction rather than directly calling the AWS SDK from the incident-processing workflow.

The client provides:

```python
publish(
    topic_arn,
    subject,
    message,
)
```

The SNS client:

* Creates the SNS client using the configured AWS region
* Publishes messages to the configured topic
* Returns the SNS `MessageId`

The integration flow is:

```text
NotificationService
       |
       v
SNSClient
       |
       v
Amazon SNS
       |
       v
SNS Topic
       |
       v
Email Subscription
```

---

## 7. SNS Topic

A dedicated SNS topic was created for CloudOps Autopilot incident notifications.

```text
Name:
cloudops-autopilot-incidents

Region:
ap-south-1

Account:
298785331841

ARN:
arn:aws:sns:ap-south-1:298785331841:cloudops-autopilot-incidents
```

The topic provides a dedicated notification boundary for CloudOps incident events.

An email subscription was configured and confirmed for the notification recipient.

The subscription provides the following delivery path:

```text
CloudOps Autopilot
        |
        v
Amazon SNS
        |
        v
cloudops-autopilot-incidents
        |
        v
Confirmed Email Subscription
```

---

## 8. Notification Service

The application-level notification service is implemented in:

```text
src/cloudops_engine/notifications/service.py
```

The service coordinates:

* Notification key generation
* Idempotency checking
* Message construction
* SNS publishing
* Notification failure handling

The service receives:

```text
SNSClient
Topic ARN
NotificationIdempotencyRepository
```

This keeps the notification workflow independent from the underlying AWS SDK implementation.

The application flow is:

```text
Incident
   |
   v
NotificationService
   |
   +--> Generate Notification Key
   |
   +--> Claim Idempotency Key
   |
   +--> Build Notification
   |
   +--> Publish Through SNSClient
   |
   v
SNS
```

---

## 9. Notification Message Structure

The notification subject contains:

```text
CloudOps Incident | <SEVERITY> | <INCIDENT_ID>
```

The notification body contains:

```text
CloudOps Autopilot Incident

Incident ID: <incident_id>
Incident Type: <incident_type>
Severity: <severity>
Resource: <resource>
Status: <status>
Description: <description>
```

The notification provides the operational information required to identify the incident and its current lifecycle state.

---

## 10. Notification Idempotency

Repeated processing of the same incident state must not result in uncontrolled duplicate notifications.

Day 10 therefore introduces a dedicated notification idempotency repository:

```text
src/cloudops_engine/repositories/
notification_idempotency_repository.py
```

The repository stores notification keys in DynamoDB.

The notification key format is:

```text
<incident_id>#<status>
```

Example:

```text
INC-12345#DETECTED
```

The idempotency flow is:

```text
Notification Request
        |
        v
Generate Key
        |
        v
DynamoDB Conditional Write
        |
        +--------------------+
        |                    |
        | New Key            | Existing Key
        v                    v
    Claim = True          Claim = False
        |                    |
        v                    v
    Publish SNS          Skip Publish
```

The repository uses a DynamoDB conditional expression:

```text
attribute_not_exists(notification_key)
```

This provides an atomic claim operation.

---

## 11. Idempotency DynamoDB Table

A dedicated DynamoDB table is used for notification idempotency.

```text
Table:
cloudops-autopilot-notification-idempotency

Partition Key:
notification_key

Region:
ap-south-1
```

The table stores notification claims independently from the main incident table.

This separation allows incident records and notification delivery state to evolve independently.

---

## 12. Notification Failure Handling

SNS publishing can fail.

The notification service therefore handles publishing failures explicitly.

The flow is:

```text
Claim Notification Key
        |
        v
Attempt SNS Publish
        |
        +----------------------+
        |                      |
      Success                Failure
        |                      |
        v                      v
Return MessageId       Release Idempotency Key
                               |
                               v
                         Allow Retry
```

When the SNS publish operation raises an exception:

* The notification key is released
* The failure is logged
* The service returns `None`
* A later attempt can claim the notification key again

Unexpected DynamoDB errors during idempotency operations are not silently swallowed.

---

## 13. Delivery Semantics

The notification design provides:

```text
At-least-once delivery semantics
+
Duplicate protection
```

It does not provide strict exactly-once delivery.

There is a small distributed failure window between SNS accepting a message and the application receiving the successful response.

For example:

```text
Application
    |
    | Publish
    v
   SNS
    |
    | Message accepted
    |
    X Response lost
    |
Application interprets publish as failed
    |
    v
Idempotency key released
    |
    v
Retry
    |
    v
Possible duplicate notification
```

Therefore, the current implementation should be described as **duplicate-protected at-least-once notification delivery**, rather than exactly-once delivery.

---

## 14. AWS Integration and Security

The SNS integration uses a dedicated customer-managed IAM policy.

The policy grants the required SNS operations for the CloudOps Autopilot notification topic.

The configured permissions include:

```text
sns:CreateTopic
sns:GetTopicAttributes
sns:Publish
sns:Subscribe
sns:Unsubscribe
sns:ListSubscriptionsByTopic
```

Topic-specific management and publishing permissions are restricted to:

```text
arn:aws:sns:ap-south-1:298785331841:cloudops-autopilot-incidents
```

The notification application does not require unrestricted SNS permissions.

The current development setup uses the existing CloudOps Autopilot development IAM identity.

Production hardening will replace long-lived development credentials with appropriate AWS role-based temporary credentials.

---

## 15. Application Notification Flow

The main application integrates notification handling into the incident lifecycle.

The current flow is:

```text
Incident Detected
      |
      v
Persist Incident
      |
      v
Notify DETECTED
      |
      v
ACKNOWLEDGED
      |
      v
INVESTIGATING
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
Guardrail Validation
      |
      v
Human Approval
      |
      v
REMEDIATING
      |
      v
Notify REMEDIATING
      |
      v
Execute Remediation
      |
      v
VERIFYING
      |
      v
Verification
      |
      +----------------------+
      |                      |
   Recovered              Not Recovered
      |                      |
      v                      v
  RESOLVED              INVESTIGATING
      |
      v
Notify RESOLVED
```

This connects notification delivery with the existing incident lifecycle without embedding SNS-specific logic into the lifecycle model.

---

## 16. Configuration

The SNS topic ARN is configured through:

```text
src/cloudops_engine/config.py
```

The configuration variable is:

```text
SNS_TOPIC_ARN
```

The default development configuration points to:

```text
arn:aws:sns:ap-south-1:298785331841:cloudops-autopilot-incidents
```

The application therefore obtains the topic configuration through the configuration layer rather than embedding the topic ARN throughout the application code.

Production configuration should provide the value through an appropriate environment or deployment configuration mechanism.

---

## 17. Testing Strategy

Day 10 includes unit and integration testing for notification functionality.

### 17.1 Notification Service Unit Tests

The notification service tests cover:

* Successful notification publishing
* Duplicate notification prevention
* Notification publishing failure
* Idempotency key release after failure

Test file:

```text
tests/unit/test_notification_service.py
```

---

### 17.2 Idempotency Repository Unit Tests

The repository tests cover:

* Successful new notification claim
* Duplicate notification claim
* Notification key release

Test file:

```text
tests/unit/test_notification_idempotency_repository.py
```

---

### 17.3 Notification Policy Tests

The policy tests verify:

```text
DETECTED      → notify
REMEDIATING   → notify
RESOLVED      → notify
```

and confirm that non-notifiable lifecycle states do not trigger notifications.

Test file:

```text
tests/unit/test_notification_policy.py
```

---

### 17.4 AWS Integration Tests

Real AWS integration tests were executed against:

```text
Amazon SNS
Amazon DynamoDB
```

The integration tests validated:

* Real SNS publishing
* Real notification service execution
* Real DynamoDB idempotency claims
* Duplicate notification prevention
* Idempotency key release and re-claim
* End-to-end notification flow

Integration test files include:

```text
tests/integration/test_notification_flow.py

tests/integration/test_notification_idempotency_flow.py

tests/integration/test_incident_notification_flow.py
```

---

## 18. Validation Results

Notification-specific unit tests:

```text
10 passed in 1.18s
```

Notification integration tests:

```text
3 passed in 9.37s
```

The complete project regression suite was also executed:

```text
82 passed in 19.00s
```

The real AWS notification integration successfully validated the SNS and DynamoDB components.

The notification integration therefore passed both application-level and AWS integration-level validation.

---

## 19. Current Limitations

The current Day 10 implementation has several known limitations.

### 19.1 Idempotency Retention

The notification idempotency table currently does not implement TTL-based expiration.

Notification keys can therefore remain in DynamoDB until explicitly removed.

A production retention strategy can be introduced during production hardening.

### 19.2 Exactly-Once Delivery

The implementation does not guarantee exactly-once notification delivery.

It provides duplicate protection while maintaining at-least-once semantics.

### 19.3 Notification Failure Visibility

Notification failures are currently logged and do not stop the incident-processing workflow.

A future observability phase can introduce dedicated metrics and alerts for notification failures.

### 19.4 Configuration Hardening

The current development configuration contains a fallback SNS topic ARN.

Production deployment should provide infrastructure-specific configuration through controlled deployment configuration.

---

## 20. Future Enhancements

Future stages can extend the notification architecture with:

* CloudWatch notification metrics
* Notification failure alarms
* Additional SNS subscribers
* Operational dashboards
* Notification delivery metrics
* Incident escalation policies
* Additional incident channels
* Production-grade credential management
* Idempotency record retention and TTL
* More detailed incident event payloads

The notification layer can therefore evolve without changing the core incident lifecycle model.

---

## 21. Day 10 Completion Status

The following Day 10 objectives have been completed:

* Existing Incident model reviewed
* Existing CloudEvent model reviewed
* Existing event handler reviewed
* Existing AWS client pattern reviewed
* AWS integration structure inspected
* SNS topic created
* Least-privilege SNS permissions configured
* Email subscription configured and confirmed
* Direct SNS publishing validated
* Notification policy implemented
* SNS client implemented
* Notification service implemented
* Notification idempotency repository implemented
* DynamoDB conditional-write duplicate protection implemented
* Notification failure handling implemented
* Incident notification flow integrated
* Real SNS integration validated
* Real DynamoDB idempotency integration validated
* Notification unit tests passed
* Notification integration tests passed
* Full regression suite passed with 82 tests

The remaining Day 10 activities are:

* Documentation review
* Final Git commit
* Push to GitHub
* Final clean-working-tree verification

The Day 10 implementation is therefore complete and ready for the documentation and Git milestone.

---

## 22. Architectural Outcome

Day 10 establishes the persistent incident-record and notification boundary for CloudOps Autopilot.

The resulting architecture is:

```text
                    CloudOps Autopilot
                            |
                            v
                    Incident Detection
                            |
                            v
                    +---------------+
                    | Incident      |
                    | Model         |
                    +-------+-------+
                            |
             +--------------+--------------+
             |                             |
             v                             v
     +---------------+             +---------------+
     | DynamoDB      |             | Notification  |
     | Incident     |             | Policy        |
     | Records       |             +-------+-------+
     +---------------+                     |
                                           v
                                   +---------------+
                                   | Idempotency   |
                                   | Repository    |
                                   +-------+-------+
                                           |
                                           v
                                   +---------------+
                                   | Amazon SNS    |
                                   | Topic         |
                                   +-------+-------+
                                           |
                                           v
                                   Email Subscriber
```

The implementation establishes a controlled notification path while preserving the existing separation between:

```text
Incident Lifecycle
       |
       +--> Persistence
       |
       +--> Notification
       |
       +--> Remediation
       |
       +--> Verification
```

This provides the foundation for subsequent observability, infrastructure, deployment, and advanced incident-automation stages.

---

## Related Documentation

* [Product Requirements](../requirements/product-requirements.md)

* [System Architecture](./system-architecture.md)

* [AWS Architecture](./aws-architecture.md)

* [EventBridge Integration](./eventbridge-integration.md)

* [Incident Lifecycle](./incident-lifecycle.md)

* [Configuration Strategy](../configuration-strategy.md)

* [Logging and Observability Strategy](../logging-observability-strategy.md)

* [Error Handling and Reliability Strategy](../error-handling-reliability-strategy.md)

* [Security and IAM Strategy](../security-iam-strategy.md)

* [Testing Strategy](../testing-strategy.md)

* [Production Readiness Gap Review](../production-readiness-gap-review.md)

## Related Architecture Decisions

* [ADR-001: Repository Pattern](../decisions/ADR-001-repository-pattern.md)

* [ADR-002: DynamoDB Persistence](../decisions/ADR-002-dynamodb-persistence.md)

* [ADR-003: Human Approval Before Remediation](../decisions/ADR-003-human-approval.md)

* [ADR-004: Conditional Write and Idempotency](../decisions/ADR-004-conditional-write-idempotency.md)
