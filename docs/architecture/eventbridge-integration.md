# CloudOps Autopilot — EventBridge Integration

## 1. Integration Context

CloudOps Autopilot follows an event-driven architecture in which cloud incident events are routed into the incident processing workflow.

The application-level event boundary was established in the previous architecture phase.

Day 8 implements this boundary using Amazon EventBridge and AWS Lambda.

The integration provides a controlled path for receiving CloudOps incident events without directly coupling the core application logic to AWS event-routing infrastructure.

---

## 2. Integration Objective

The primary objective of the EventBridge integration is to establish a reliable AWS event-routing mechanism for CloudOps incident events.

The integration should:

* Receive CloudOps incident events
* Route matching events through a dedicated EventBridge event bus
* Identify incident events using an event pattern
* Invoke the CloudOps Autopilot Lambda event handler
* Convert AWS EventBridge events into the internal `CloudEvent` model
* Pass the event into the existing CloudOps event-processing boundary

The implementation is intentionally limited to the event ingestion and routing layer.

---

## 3. Event-Driven Architecture

The Day 8 event-driven architecture is:

```text
CloudOps Incident Event
        |
        v
Amazon EventBridge
        |
        v
Custom Event Bus
        |
        v
Incident Routing Rule
        |
        v
AWS Lambda
        |
        v
CloudEvent Adapter
        |
        v
CloudOps Event Handler
```

The architecture separates event routing from application-level incident processing.

EventBridge is responsible for routing.

Lambda provides the execution boundary.

The application remains responsible for processing the internal event.

---

## 4. EventBridge Resources

### 4.1 Custom Event Bus

A dedicated EventBridge custom event bus was created for CloudOps Autopilot.

```text
Name:
cloudops-autopilot-bus

Region:
ap-south-1

Account:
298785331841
```

The custom event bus provides a dedicated event-routing boundary for CloudOps incident events.

---

### 4.2 Incident Routing Rule

The EventBridge rule is:

```text
Name:
cloudops-autopilot-incident-rule

Event Bus:
cloudops-autopilot-bus

State:
ENABLED
```

The rule description is:

```text
Routes CloudOps incident events to the incident processing workflow.
```

The rule is responsible for identifying CloudOps incident events and routing them to the Lambda event handler.

---

### 4.3 Event Pattern

The rule uses the following event pattern:

```json
{
  "source": [
    "cloudops.autopilot"
  ],
  "detail-type": [
    "CloudOps Incident"
  ]
}
```

The rule therefore processes events that contain:

```text
source:
cloudops.autopilot
```

and:

```text
detail-type:
CloudOps Incident
```

This prevents unrelated EventBridge events from being routed into the CloudOps incident-processing workflow.

---

## 5. Event Contract

The CloudOps incident event follows the following structure:

```json
{
  "source": "cloudops.autopilot",
  "detail-type": "CloudOps Incident",
  "detail": {
    "incident_id": "e2e-test-001",
    "incident_type": "cloud_incident",
    "severity": "HIGH"
  }
}
```

The event contains the information required to identify and process a CloudOps incident.

EventBridge additionally provides event metadata such as:

* Event ID
* Event timestamp
* Event source
* Event detail type

---

## 6. Event Routing

The EventBridge routing flow is:

```text
CloudOps Incident Event
        |
        v
+-------------------------+
| Custom Event Bus        |
|                         |
| cloudops-autopilot-bus  |
+-----------+-------------+
            |
            v
+-------------------------+
| EventBridge Rule        |
|                         |
| cloudops-autopilot-     |
| incident-rule           |
+-----------+-------------+
            |
            v
+-------------------------+
| Event Pattern Match     |
|                         |
| source:                 |
| cloudops.autopilot      |
|                         |
| detail-type:            |
| CloudOps Incident       |
+-----------+-------------+
            |
            v
+-------------------------+
| Lambda Target           |
+-------------------------+
```

Only events matching the configured event pattern are routed to the Lambda function.

---

## 7. Lambda Integration

The EventBridge rule uses the following Lambda function as its target:

```text
Function:
cloudops-autopilot-event-handler

Runtime:
Python 3.14

Handler:
lambda_function.lambda_handler

Region:
ap-south-1
```

The Lambda function provides the AWS execution boundary for incoming CloudOps events.

The event-processing flow is:

```text
EventBridge Event
        |
        v
lambda_handler()
        |
        v
adapt_eventbridge_event()
        |
        v
CloudEvent
        |
        v
handle_event()
        |
        v
Processing Result
```

The current processing result is:

```json
{
  "status": "processed",
  "event_type": "cloud_incident"
}
```

---

## 8. Application Event Adapter

The application uses an EventBridge adapter to convert the AWS-specific event structure into the internal `CloudEvent` model.

The adapter is implemented in:

```text
src/cloudops_engine/events/eventbridge_adapter.py
```

The mapping is:

| EventBridge Field | CloudEvent Field |
|---|---|
| `id` | `event_id` |
| `detail-type` | `event_type` |
| `source` | `source` |
| `time` | `timestamp` |
| `detail` | `payload` |

The adapter creates the following application boundary:

```text
AWS EventBridge Event
        |
        v
EventBridge Adapter
        |
        v
CloudEvent
        |
        v
CloudOps Event Handler
```

This keeps AWS-specific event handling at the integration boundary.

---

## 9. Lambda Resource-Based Permission

EventBridge requires permission to invoke the Lambda function.

A Lambda resource-based permission was configured for the CloudOps Autopilot EventBridge rule.

The permission allows:

```text
Principal:
events.amazonaws.com

Action:
lambda:InvokeFunction
```

The permission is restricted to the specific EventBridge rule using the following source ARN:

```text
arn:aws:events:ap-south-1:298785331841:rule/cloudops-autopilot-bus/cloudops-autopilot-incident-rule
```

The resulting security boundary is:

```text
Amazon EventBridge
        |
        | lambda:InvokeFunction
        |
        | SourceArn restricted
        v
cloudops-autopilot-event-handler
```

---

## 10. EventBridge Target Configuration

The Lambda function was configured as the target of:

```text
cloudops-autopilot-incident-rule
```

The configured target is:

```text
arn:aws:lambda:ap-south-1:298785331841:function:cloudops-autopilot-event-handler
```

The target relationship is:

```text
cloudops-autopilot-bus
        |
        v
cloudops-autopilot-incident-rule
        |
        v
cloudops-autopilot-event-handler
```

The target configuration was verified successfully.

---

## 11. End-to-End Validation

The EventBridge integration was validated using real AWS resources in the `ap-south-1` region.

A real CloudOps incident event was published to:

```text
cloudops-autopilot-bus
```

The test event contained:

```text
incident_id:
e2e-test-001

incident_type:
cloud_incident

severity:
HIGH
```

EventBridge returned:

```json
{
  "FailedEntryCount": 0,
  "Entries": [
    {
      "EventId": "3e8f2a5b-d48a-3510-b3e6-5c6e9420d85b"
    }
  ]
}
```

This confirmed that EventBridge successfully accepted the event.

### 11.1 Lambda Invocation Validation

CloudWatch Logs confirmed the Lambda invocation:

```text
START RequestId: 020f0bdd-0840-43c4-86e7-ba57f290b465
END RequestId: 020f0bdd-0840-43c4-86e7-ba57f290b465
REPORT RequestId: 020f0bdd-0840-43c4-86e7-ba57f290b465
```

The validated path was:

```text
CloudOps Incident
      |
      v
EventBridge
      |
      v
EventBridge Rule
      |
      v
Lambda
      |
      v
CloudEvent Adapter
      |
      v
CloudOps Event Handler
```

---

## 12. Observability

Lambda execution is integrated with Amazon CloudWatch Logs.

The Lambda log group is:

```text
/aws/lambda/cloudops-autopilot-event-handler
```

CloudWatch Logs were used to confirm the successful Lambda invocation during end-to-end testing.

The current observability implementation confirms:

* Lambda initialization
* Lambda invocation
* Lambda completion
* Lambda execution duration

Future observability stages will introduce additional metrics, dashboards, alerts, and operational visibility.

---

## 13. Security and IAM

The EventBridge integration follows the security model established for CloudOps Autopilot.

The Lambda resource-based policy grants EventBridge the required invocation permission:

```text
events.amazonaws.com
        |
        +-- lambda:InvokeFunction
```

The permission is restricted to the specific EventBridge rule.

The Lambda deployment policy contains controlled permissions for:

* Lambda function management
* Lambda invocation
* Lambda resource-policy management
* Lambda execution-role access

The Lambda execution role is:

```text
CloudOpsAutopilotLambdaExecutionRole
```

The deployment identity does not receive unrestricted `lambda:*` permissions.

---

## 14. Current Limitations

The current EventBridge integration establishes the event ingestion and routing boundary.

It does not yet connect the incoming EventBridge event to the complete incident lifecycle.

The complete CloudOps Autopilot lifecycle remains:

```text
Detect
   |
   v
Collect Evidence
   |
   v
Diagnose
   |
   v
Assess Risk
   |
   v
Recommend
   |
   v
Human Approval
   |
   v
Remediate
   |
   v
Verify
   |
   v
Record Result
```

The EventBridge integration currently provides the entry point into this lifecycle.

Further integration with persistent incident management, remediation, and verification will be implemented in subsequent roadmap stages.

---

## 15. Future Integration

Future stages will extend the EventBridge integration to support additional event sources and incident scenarios.

Potential event sources include:

* CloudWatch-based incident detection
* Application 5xx detection
* Unhealthy service detection
* Infrastructure events
* Application events
* Kubernetes events

The long-term event-driven architecture is:

```text
Cloud / Application Signals
          |
          v
Event Detection
          |
          v
Amazon EventBridge
          |
          v
Incident Processing
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
Human Approval
          |
          v
Remediation
          |
          v
Verification
```

The EventBridge integration therefore provides the foundation for future event-driven incident automation.

---

## 16. Day 8 Completion Status

The following Day 8 objectives have been completed:

* Custom EventBridge event bus created
* Incident routing rule created
* Event pattern configured
* Lambda event handler deployed
* Lambda resource-based permission configured
* Lambda registered as EventBridge target
* Real incident event published
* EventBridge successfully accepted the event
* EventBridge successfully routed the event
* Lambda invocation confirmed
* CloudWatch execution logs confirmed
* EventBridge event adapter implemented
* Internal `CloudEvent` processing boundary established
* Automated test suite passed with 64 tests
* Real AWS end-to-end integration validated

The Day 8 AWS EventBridge integration is therefore complete.

---

## 17. Architectural Outcome

Day 8 establishes the real AWS event-driven execution boundary for CloudOps Autopilot.

The resulting architecture is:

```text
                    AWS
                     |
                     v
          +---------------------+
          | Amazon EventBridge  |
          |                     |
          | cloudops-autopilot- |
          | bus                 |
          +----------+----------+
                     |
                     v
          +---------------------+
          | Incident Rule       |
          |                     |
          | CloudOps Incident   |
          +----------+----------+
                     |
                     v
          +---------------------+
          | AWS Lambda          |
          |                     |
          | event-handler       |
          +----------+----------+
                     |
                     v
          +---------------------+
          | CloudEvent Adapter  |
          +----------+----------+
                     |
                     v
          +---------------------+
          | CloudOps Event      |
          | Handler             |
          +---------------------+
```

The implementation establishes a controlled and event-driven foundation for the subsequent CloudOps Autopilot incident-processing stages.

---

## Related Documentation

* [Product Requirements](../requirements/product-requirements.md)

* [System Architecture](./system-architecture.md)

* [AWS Architecture](./aws-architecture.md)

* [Incident Lifecycle](./incident-lifecycle.md)

* [Research Problem and Methodology](../research/research-problem.md)

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
