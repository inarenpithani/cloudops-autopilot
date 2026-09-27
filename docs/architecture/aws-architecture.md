# CloudOps Autopilot

## AWS Architecture

**Document Version:** 1.0
**Status:** Architecture Foundation
**Cloud Provider:** Amazon Web Services (AWS)
**Primary Region:** `ap-south-1`
**Related Documents:**

* `docs/requirements/product-requirements.md`
* `docs/architecture/system-architecture.md`

---

# 1. Purpose

This document defines the AWS-specific architecture for CloudOps Autopilot.

It describes:

* AWS services
* AWS resource responsibilities
* IAM boundaries
* Telemetry flow
* Incident processing flow
* Persistence
* Remediation boundaries
* Networking considerations
* Security boundaries
* Current architecture
* Target architecture
* Future scalability

The architecture is intentionally designed to start small while providing a controlled path toward an event-driven production platform.

---

# 2. AWS Architecture Principles

CloudOps Autopilot follows these AWS architecture principles:

1. Least privilege
2. Separation of duties
3. Resource-level IAM permissions where practical
4. Secure credential handling
5. Region-aware architecture
6. Infrastructure as Code
7. Event-driven design
8. Failure isolation
9. Observability
10. Auditability
11. Cost awareness
12. Human approval for protected actions
13. Verification after remediation
14. Minimal permissions for automation
15. Controlled blast radius

---

# 3. AWS Account Strategy

The current project uses a dedicated AWS account for development.

Current model:

```text
CloudOps Autopilot AWS Account
            │
            ├── Development IAM
            │
            ├── EC2 Development Resource
            │
            ├── CloudWatch
            │
            └── DynamoDB
```

The initial implementation intentionally avoids mixing the project with unrelated workloads.

---

# 4. AWS Region

Primary region:

```text
ap-south-1
```

This corresponds to the AWS Mumbai region.

The application configuration should keep the region configurable rather than hardcoding it throughout the codebase.

Future environments may use additional regions for:

* Disaster recovery
* Business continuity
* Regional deployment
* Latency requirements

---

# 5. Current AWS Components

The current architecture uses:

```text
Amazon EC2
Amazon CloudWatch
Amazon DynamoDB
AWS IAM
AWS CLI
```

Future architecture will introduce additional services progressively.

---

# 6. Current AWS Architecture

```text
┌──────────────────────────────────────────────────────┐
│              CloudOps Autopilot AWS Account          │
│                                                      │
│  ┌────────────────┐                                  │
│  │      EC2       │                                  │
│  │ Development    │                                  │
│  │   Instance     │                                  │
│  └───────┬────────┘                                  │
│          │                                           │
│          │ CPU Metrics                               │
│          ▼                                           │
│  ┌────────────────┐                                  │
│  │  CloudWatch    │                                  │
│  │    Metrics     │                                  │
│  └───────┬────────┘                                  │
│          │                                           │
│          │ Read                                      │
│          ▼                                           │
│  ┌────────────────────────────┐                      │
│  │   CloudOps Engine          │                      │
│  │                            │                      │
│  │ Detection                  │                      │
│  │ Diagnosis                  │                      │
│  │ Risk                       │                      │
│  │ Recommendation             │                      │
│  │ Guardrails                 │                      │
│  │ Approval                   │                      │
│  │ Remediation                │                      │
│  │ Verification               │                      │
│  └──────────────┬─────────────┘                      │
│                 │                                    │
│                 │ Incident State                     │
│                 ▼                                    │
│        ┌──────────────────┐                          │
│        │    DynamoDB      │                          │
│        │                  │                          │
│        │ cloudops-        │                          │
│        │ autopilot-       │                          │
│        │ incidents        │                          │
│        └──────────────────┘                          │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

# 7. Amazon EC2

EC2 is currently used as the monitored development workload.

Current instance characteristics:

```text
Service: Amazon EC2
Purpose: Development monitoring target
Operating System: Amazon Linux
Instance Type: t3.micro
```

The instance provides a real AWS resource against which CloudWatch monitoring and incident detection can be tested.

---

# 8. EC2 Monitoring

The current monitoring signal is:

```text
Namespace:
AWS/EC2

Metric:
CPUUtilization
```

The CloudOps engine retrieves CloudWatch datapoints and evaluates them against configured detection rules.

Example:

```text
CPU > 90%
+
3 consecutive datapoints
        ↓
Potential HIGH_CPU incident
```

---

# 9. IAM Architecture

IAM is a critical security boundary.

The project uses a dedicated IAM development identity instead of relying on the AWS root user for normal development operations.

The current development identity has permissions required for:

* CloudWatch read operations
* EC2 read operations
* DynamoDB incident persistence

---

# 10. IAM Separation

The architecture distinguishes between:

### Monitoring Permissions

Used for reading telemetry and resource information.

Examples:

```text
CloudWatch Read
EC2 Read
```

### Persistence Permissions

Used for incident storage.

Examples:

```text
DynamoDB ListTables
DynamoDB CreateTable
DynamoDB DescribeTable
DynamoDB GetItem
DynamoDB PutItem
DynamoDB UpdateItem
DynamoDB DeleteItem
```

These permissions are restricted to the intended incident table where resource-level permissions are applicable.

---

# 11. Remediation IAM Boundary

Real remediation introduces a significantly higher security risk than monitoring.

Therefore, remediation permissions should not automatically be added to the monitoring identity.

Future architecture:

```text
                 CloudOps System
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
 Monitoring Role              Remediation Role
          │                         │
          ├── CloudWatch Read       └── Only approved
          └── EC2 Read                  AWS actions
```

The remediation identity should receive only the minimum permissions required for explicitly supported actions.

---

# 12. Blast Radius

A compromised or incorrectly behaving component should have the smallest practical blast radius.

For example:

```text
Monitoring Role
      ↓
Read-only access
```

should not automatically provide:

```text
IAM Administrator
EC2 Administrator
S3 Administrator
Account Administrator
```

The architecture therefore separates observation from modification.

---

# 13. DynamoDB Architecture

The current incident persistence service is Amazon DynamoDB.

Table:

```text
cloudops-autopilot-incidents
```

Region:

```text
ap-south-1
```

Billing:

```text
PAY_PER_REQUEST
```

Partition key:

```text
incident_id
```

---

# 14. DynamoDB Data Model

Current incident record:

```text
{
    incident_id,
    incident_type,
    severity,
    resource,
    detected_at,
    status,
    description
}
```

Future attributes may include:

```text
evidence
diagnosis
confidence
risk
recommendation
approval
remediation_result
verification_result
audit_events
```

The schema should evolve carefully to preserve compatibility with historical records.

---

# 15. DynamoDB Access Pattern

The application uses a repository abstraction:

```text
CloudOps Engine
      ↓
IncidentRepository
      ↓
DynamoDBIncidentRepository
      ↓
DynamoDB
```

This keeps AWS-specific persistence logic outside the core domain logic.

---

# 16. Duplicate Protection

Incident creation uses conditional writes.

The application uses:

```text
attribute_not_exists(incident_id)
```

when creating an incident.

Therefore, an existing incident cannot be accidentally overwritten through the normal `save()` operation.

Conceptually:

```text
Save Incident
     ↓
Does incident_id exist?
   /          \
 NO            YES
 ↓              ↓
Create         Reject
```

This is an important consistency and safety control.

---

# 17. CloudWatch Architecture

CloudWatch acts as the initial operational telemetry layer.

Current usage:

```text
EC2
 ↓
CloudWatch
 ↓
CPUUtilization
 ↓
CloudOps Engine
```

Future CloudWatch usage may include:

* CPU
* Memory
* Network
* Request count
* Error rate
* Latency
* Application 5xx
* Service health
* Custom metrics

---

# 18. Current Telemetry Flow

The current flow is application-driven:

```text
CloudOps Engine
      ↓
CloudWatch API
      ↓
Metric Datapoints
      ↓
Detection
```

This is appropriate for the current development and learning stage.

It allows the core incident engine to be developed independently of an event-driven production trigger.

---

# 19. Target Event-Driven Architecture

The target architecture introduces CloudWatch alarms and EventBridge.

```text
┌─────────────────┐
│ AWS Workloads   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   CloudWatch    │
│     Metrics     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ CloudWatch      │
│ Alarm           │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ EventBridge     │
│ Event Bus       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ CloudOps Event  │
│ Handler         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Incident Engine │
└─────────────────┘
```

This allows the platform to respond to operational events without continuously polling every resource.

---

# 20. EventBridge

EventBridge will eventually provide event-driven integration between AWS operational events and CloudOps Autopilot.

Potential events include:

* CloudWatch alarm state changes
* Deployment events
* EC2 events
* ECS events
* EKS-related events
* Infrastructure events
* Custom application events

Future flow:

```text
AWS Event
    ↓
EventBridge
    ↓
CloudOps Event Handler
    ↓
Incident Processing
```

---

# 21. Lambda

AWS Lambda may be used for lightweight event processing.

Potential responsibility:

```text
EventBridge
     ↓
Lambda
     ↓
Normalize Event
     ↓
CloudOps Engine
```

Lambda should not automatically become the location for all business logic.

Core domain logic should remain modular and independently testable.

---

# 22. ECS

Amazon ECS is a potential future deployment target for the CloudOps engine when the application requires:

* Long-running processes
* Continuous workers
* More control over runtime
* Containerized deployment
* Higher operational flexibility

Potential architecture:

```text
GitHub
   ↓
GitHub Actions
   ↓
Docker Build
   ↓
Amazon ECR
   ↓
Amazon ECS
   ↓
CloudOps Engine
```

---

# 23. ECR

Amazon ECR will provide container image storage when the CloudOps engine is containerized.

Expected flow:

```text
Source Code
    ↓
Docker Build
    ↓
Container Image
    ↓
Amazon ECR
    ↓
ECS / Future Runtime
```

---

# 24. SNS

Amazon SNS may be introduced for operational notifications.

Potential notifications:

* New incident
* High-severity incident
* Approval required
* Remediation completed
* Remediation failed
* Verification failed

Example:

```text
Incident
   ↓
SNS
   ├── Email
   ├── Notification
   └── Future integrations
```

---

# 25. Networking Architecture

The current EC2 instance uses a VPC and subnet provided by the AWS environment.

The current project does not require a complex multi-VPC architecture.

Future production architecture may introduce:

* Private subnets
* Public/private subnet separation
* NAT Gateway where required
* VPC endpoints
* Security groups
* Network ACLs
* Restricted ingress/egress
* Private application workloads

---

# 26. Security Group Strategy

The monitored EC2 instance should expose only required network access.

Current development principle:

```text
SSH
 ↓
Restricted source IP
```

Unnecessary public application ports should not remain open.

Future production workloads should prefer private networking where appropriate.

---

# 27. Secrets Management

Secrets must not be stored in:

* Source code
* Git history
* README
* Terraform files
* Plain-text configuration committed to Git

Future production architecture should use an appropriate AWS-managed secret mechanism such as:

```text
AWS Secrets Manager
```

or another approved secret-management solution.

---

# 28. Encryption

Future production architecture should define encryption requirements for:

* DynamoDB
* CloudWatch Logs
* Secrets
* Data in transit
* Backup data

AWS-managed encryption should be enabled where appropriate.

Customer-specific encryption requirements may require AWS KMS.

---

# 29. Logging Architecture

Application logs should eventually flow through:

```text
CloudOps Engine
      ↓
Structured Logs
      ↓
CloudWatch Logs
      ↓
Operational Monitoring
```

Logs should include useful context such as:

```text
incident_id
event_id
component
action
status
timestamp
```

Sensitive information must not be written to logs.

---

# 30. Audit Architecture

Operationally significant events should eventually produce audit records.

Example:

```text
Incident Detected
      ↓
Diagnosis Generated
      ↓
Recommendation Created
      ↓
Approval Requested
      ↓
Approval Granted
      ↓
Remediation Executed
      ↓
Verification Completed
```

Each important event should be traceable to the incident.

---

# 31. AWS Security Model

The architecture follows:

```text
Identity
   ↓
Authentication
   ↓
Authorization
   ↓
Least Privilege
   ↓
Controlled Action
   ↓
Audit
```

The platform should avoid broad administrative permissions.

---

# 32. Environment Strategy

Future deployment environments:

```text
DEV
 ↓
UAT
 ↓
PROD
```

Each environment should have independent:

* AWS resources
* Configuration
* IAM permissions
* Secrets
* Monitoring
* Deployment controls

Production credentials should never be reused for local development.

---

# 33. Multi-Account Architecture

Future enterprise deployment may use AWS Organizations.

Example:

```text
                    AWS Organization
                           │
             ┌─────────────┼─────────────┐
             │             │             │
             ▼             ▼             ▼
        Management       Security      CloudOps
          Account        Account        Account
                                         │
                           ┌─────────────┼─────────────┐
                           ▼             ▼             ▼
                         DEV           UAT           PROD
```

The exact organizational model will be defined before enterprise deployment.

---

# 34. Cross-Account Access

For multi-account monitoring, CloudOps Autopilot should use controlled cross-account IAM roles.

Conceptually:

```text
CloudOps Control Plane
        │
        │ AssumeRole
        ▼
Target AWS Account
        │
        └── CloudOps Monitoring Role
```

The role should provide only the permissions necessary for the requested monitoring or remediation operation.

---

# 35. Remediation Architecture

Real remediation is intentionally separated from monitoring.

Future model:

```text
CloudOps Engine
      │
      ▼
Policy / Risk Engine
      │
      ▼
Human Approval
      │
      ▼
Remediation Role
      │
      ▼
AWS API
      │
      ▼
Target Resource
```

The remediation role must not be granted broad administrator permissions simply to simplify implementation.

---

# 36. Remediation Safety Boundary

A remediation action must pass:

```text
Incident
   ↓
Diagnosis
   ↓
Risk Assessment
   ↓
Policy Check
   ↓
Allowlist
   ↓
Approval
   ↓
IAM Authorization
   ↓
Execution
   ↓
Verification
```

There are therefore multipl
