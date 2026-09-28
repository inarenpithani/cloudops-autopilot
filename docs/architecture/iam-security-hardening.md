# IAM & Security Hardening

---

## 1. Purpose

The IAM and security hardening strategy defines how CloudOps Autopilot accesses AWS resources using least-privilege permissions.

The application must have only the permissions required to perform its runtime responsibilities.

IAM administration and application runtime permissions are intentionally separated.

---

## 2. Security Objectives

The security model is based on the following principles:

- Least privilege
- Explicit resource scoping
- Separation of bootstrap and runtime permissions
- Human approval for controlled remediation
- Restricted remediation actions
- Persistent auditability
- No unrestricted AWS administrative access

---

## 3. IAM Permission Layers

CloudOps Autopilot separates AWS permissions into two logical layers.

```text
IAM / Infrastructure Administration
              |
              | creates infrastructure
              | creates or updates IAM policies
              v
        AWS Resources
              ^
              |
        Runtime Identity
              |
              +--> CloudWatch
              +--> DynamoDB
              +--> SNS
              +--> EC2
```

The runtime identity must not receive IAM administration permissions merely to execute application operations.

---

## 4. Runtime AWS Operations

The application currently performs the following AWS operations:

| Service | API | IAM Action |
|---|---|---|
| CloudWatch | `get_metric_statistics()` | `cloudwatch:GetMetricStatistics` |
| EC2 | `reboot_instances()` | `ec2:RebootInstances` |
| SNS | `publish()` | `sns:Publish` |
| DynamoDB | `put_item()` | `dynamodb:PutItem` |
| DynamoDB | `get_item()` | `dynamodb:GetItem` |
| DynamoDB | `delete_item()` | `dynamodb:DeleteItem` |

No broader service-level permissions are required by the current application runtime.

---

## 5. CloudWatch Permissions

CloudOps Autopilot reads EC2 CPU metrics from Amazon CloudWatch.

Required permission:

```text
cloudwatch:GetMetricStatistics
```

The application does not require CloudWatch write permissions.

Current monitoring boundary:

```text
CloudWatch
    |
    +-- AWS/EC2
          |
          +-- CPUUtilization
```

---

## 6. EC2 Remediation Permissions

The current controlled remediation action is:

```text
EC2_REBOOT
```

Required permission:

```text
ec2:RebootInstances
```

The permission is scoped to the approved EC2 instance rather than all EC2 resources.

Current instance:

```text
i-05e3bbde2a13509f7
```

Resource ARN:

```text
arn:aws:ec2:ap-south-1:298785331841:instance/i-05e3bbde2a13509f7
```

The runtime identity does not require:

```text
ec2:StopInstances
ec2:TerminateInstances
ec2:StartInstances
ec2:*
```

---

## 7. SNS Permissions

CloudOps Autopilot publishes incident notifications to the configured SNS topic.

Required permission:

```text
sns:Publish
```

SNS topic:

```text
arn:aws:sns:ap-south-1:298785331841:cloudops-autopilot-incidents
```

The runtime identity does not require topic administration permissions such as:

```text
sns:CreateTopic
sns:Subscribe
sns:Unsubscribe
```

---

## 8. DynamoDB Permissions

CloudOps Autopilot uses four DynamoDB tables.

### Incident Table

```text
cloudops-autopilot-incidents
```

Required operations:

```text
dynamodb:PutItem
dynamodb:GetItem
```

---

### Notification Idempotency Table

```text
cloudops-autopilot-notification-idempotency
```

Required operations:

```text
dynamodb:PutItem
dynamodb:DeleteItem
```

---

### Remediation Idempotency Table

```text
cloudops-autopilot-remediation-idempotency
```

Required operations:

```text
dynamodb:PutItem
dynamodb:DeleteItem
```

---

### Remediation Execution Audit Table

```text
cloudops-autopilot-remediation-executions
```

Required operation:

```text
dynamodb:PutItem
```

---

## 9. Runtime Permission Policy

The runtime policy is maintained in:

```text
iam-runtime-policy.json
```

The policy is intentionally restricted to:

- Required API actions
- Required AWS resources
- Required application runtime responsibilities

The policy does not grant IAM administration privileges.

---

## 10. Bootstrap vs Runtime Permissions

Bootstrap and runtime permissions serve different purposes.

### Bootstrap / Infrastructure Operations

Bootstrap operations may require permissions such as:

```text
dynamodb:CreateTable
dynamodb:ListTables
```

These permissions are intended for infrastructure provisioning and should not automatically be granted to the runtime application identity.

### Runtime Operations

Runtime permissions are limited to operations required while the application is executing.

```text
Runtime
  |
  +-- CloudWatch read
  +-- DynamoDB data operations
  +-- SNS publish
  +-- Approved EC2 reboot
```

This separation reduces the blast radius of a compromised application credential.

---

## 11. IAM Administration Boundary

The current development IAM identity:

```text
cloudops-autopilot-dev
```

does not have permissions to create or inspect IAM policies.

For example:

```text
iam:CreatePolicy  -> AccessDenied
iam:GetPolicy     -> AccessDenied
```

This is treated as an administrative boundary rather than a reason to grant broad IAM permissions to the application identity.

The runtime policy must therefore be created and attached by an appropriately authorized IAM administrator.

---

## 12. Security Validation

After the runtime policy is attached to the correct application identity, the following validation must be performed.

### Allowed Operations

The application should be able to:

```text
CloudWatch
    GetMetricStatistics

SNS
    Publish

DynamoDB
    PutItem
    GetItem
    DeleteItem

EC2
    RebootInstances
    on the approved instance only
```

### Denied Operations

The runtime identity should not be able to:

```text
EC2 StopInstances
EC2 TerminateInstances
EC2 operations on unrelated resources

DynamoDB CreateTable
DynamoDB ListTables
DynamoDB DescribeTable

SNS CreateTopic
SNS Subscribe
SNS Unsubscribe

IAM policy administration
```

The denied-operation tests are important because least privilege must be demonstrated through both successful and unsuccessful authorization attempts.

---

## 13. Remediation Security Boundary

EC2 remediation is protected by multiple controls.

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
Action Allowlist
   |
   v
Guardrails
   |
   v
Human Approval
   |
   v
Idempotency
   |
   v
EC2 Reboot
   |
   v
Verification
```

IAM permissions are therefore one layer of the security model rather than the only safety mechanism.

---

## 14. Current Security State

Completed:

- Runtime AWS API mapping
- DynamoDB resource identification
- Required remediation tables provisioned
- Least-privilege runtime policy designed
- Runtime policy JSON validated
- Bootstrap/runtime permission separation defined
- IAM administration boundary identified

Pending:

- Administrative creation of runtime IAM policy
- Policy attachment to the intended runtime identity
- Allowed-access validation
- Denied-access validation
- Real controlled EC2 remediation test
- Final security regression

---

## 15. Related Documentation

- `docs/architecture/system-architecture.md`
- `docs/architecture/aws-architecture.md`
- `docs/architecture/remediation-framework.md`
- `docs/architecture/eventbridge-integration.md`
- `docs/architecture/incident-lifecycle.md`
- `docs/research/research-problem.md`
- `iam-runtime-policy.json`

---

## 16. Related Architecture Decisions

- `docs/decisions/ADR-001-aws-native-event-driven-architecture.md`
- `docs/decisions/ADR-002-dynamodb-persistence.md`
- `docs/decisions/ADR-003-human-approval-for-remediation.md`
- `docs/decisions/ADR-004-remediation-idempotency.md`
