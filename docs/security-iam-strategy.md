# CloudOps Autopilot — Security & IAM Strategy

## 1. Purpose

This document defines the security and Identity and Access Management (IAM) strategy for CloudOps Autopilot.

CloudOps Autopilot is designed to monitor cloud infrastructure, analyze incidents, recommend remediation actions, obtain appropriate approval, execute controlled remediation, and verify recovery.

Because the platform can eventually interact with infrastructure, security must be treated as a core architectural concern rather than an additional feature.

The primary security objectives are:

1. Least privilege
2. Strong identity separation
3. Explicit authorization
4. Controlled remediation permissions
5. Human approval for infrastructure-changing actions
6. Protection of credentials and secrets
7. Auditability
8. Isolation of environments
9. Limited blast radius
10. Secure failure behavior

---

# 2. Security Principles

CloudOps Autopilot follows these principles:

* Least privilege by default
* Deny by default where practical
* No root credentials for application operations
* Separate read and write permissions
* Separate detection and remediation authority
* Human approval before infrastructure-changing remediation
* Credentials must not be hardcoded
* Secrets must not be stored in Git
* Resource-level IAM permissions where supported
* Short-lived credentials preferred for production workloads
* Security failures must fail closed
* All privileged actions must be auditable
* Development and production access must be separated

The central principle is:

> **The component that detects a problem should not automatically have unrestricted authority to modify infrastructure.**

---

# 3. Threat Model

CloudOps Autopilot must consider threats against both the platform and the cloud resources it manages.

Potential threats include:

* Compromised developer credentials
* Excessive IAM permissions
* Credential leakage
* Malicious or compromised application code
* Unauthorized remediation
* Accidental destructive actions
* Incorrect AI-generated recommendations in future versions
* Configuration tampering
* Event injection
* Log manipulation
* Unauthorized incident modification
* Cross-environment access
* Compromised CI/CD credentials

The architecture should reduce the probability and impact of these threats.

---

# 4. Security Boundary

The platform should be separated into security boundaries.

```text
+-----------------------------+
| Developer / Operator        |
+-------------+---------------+
              |
              | Authenticated Access
              v
+-----------------------------+
| CloudOps Autopilot          |
| Application Layer           |
+-------------+---------------+
              |
              | Controlled IAM
              v
+-----------------------------+
| AWS Services                |
| CloudWatch / DynamoDB / etc |
+-----------------------------+
              |
              | Controlled Remediation
              v
+-----------------------------+
| Target Cloud Resources      |
| EC2 / Services / Workloads  |
+-----------------------------+
```

Each boundary should have only the permissions required for its responsibility.

---

# 5. AWS Account Strategy

The current project uses a dedicated AWS account for CloudOps Autopilot development.

Current account:

```text
Environment: Development
Region: ap-south-1
Purpose: CloudOps Autopilot development and experimentation
```

This provides isolation from unrelated workloads.

For a production product, separate AWS accounts should be considered for:

```text
Development
     ↓
UAT / Staging
     ↓
Production
```

Production workloads should not depend on unrestricted developer access.

---

# 6. AWS Region

The current development region is:

```text
ap-south-1
```

Mumbai.

Region selection should be configuration-driven rather than hardcoded throughout application logic.

Security controls should be reviewed for every additional region introduced later.

---

# 7. IAM Identity Model

CloudOps Autopilot uses different identities for different responsibilities.

Conceptually:

```text
Developer
   ↓
Development IAM Identity

Application
   ↓
Runtime IAM Role

EC2
   ↓
Instance Profile

Lambda
   ↓
Lambda Execution Role

ECS
   ↓
Task Role

CI/CD
   ↓
Dedicated Deployment Role
```

These identities should not share credentials.

---

# 8. Current Development IAM User

The current development environment uses:

```text
cloudops-autopilot-dev
```

This identity is used for local development and AWS CLI/API access.

The current access is intentionally limited compared with an administrator identity.

Current development permissions include read access for:

* CloudWatch
* EC2

Additional DynamoDB bootstrap permissions were later introduced for incident persistence.

---

# 9. Long-Term Production Identity Strategy

Long-term production architecture should reduce dependence on long-lived IAM user access keys.

Preferred model:

```text
Application
    ↓
AWS IAM Role
    ↓
Temporary Credentials
    ↓
AWS API
```

Examples:

* Lambda execution role
* ECS task role
* EC2 instance profile
* GitHub Actions OIDC role

Long-lived access keys should not be embedded into applications or container images.

---

# 10. Least Privilege

Every identity should receive only the permissions required for its responsibility.

For example:

```text
Detection Identity
    ↓
CloudWatch Read
EC2 Read
```

should not automatically receive:

```text
EC2 Stop
EC2 Terminate
IAM Administrator
```

Similarly:

```text
Incident Persistence Identity
    ↓
DynamoDB incident table access
```

should not automatically receive unrestricted access to every DynamoDB table.

---

# 11. Current DynamoDB IAM Model

The current project uses a custom DynamoDB bootstrap policy.

The policy allows:

```text
dynamodb:ListTables
dynamodb:CreateTable
```

and table-specific management permissions for:

```text
cloudops-autopilot-incidents
```

The incident table ARN is:

```text
arn:aws:dynamodb:ap-south-1:298785331841:table/cloudops-autopilot-incidents
```

The table-specific permissions include:

* DescribeTable
* GetItem
* PutItem
* UpdateItem
* DeleteItem

This demonstrates resource-level least privilege for incident persistence.

---

# 12. Bootstrap vs Runtime Permissions

A production-grade system should distinguish between bootstrap permissions and runtime permissions.

### Bootstrap

Used to create or configure infrastructure.

Examples:

```text
CreateTable
CreateInfrastructure
ConfigureResources
```

### Runtime

Used by the running application.

Examples:

```text
GetMetricData
GetItem
PutItem
UpdateItem
```

Runtime identities should not retain infrastructure bootstrap privileges unless explicitly required.

---

# 13. IAM Role for EC2 Monitoring

The project created:

```text
CloudOpsAutopilotEC2ReadOnlyRole
```

This role is attached to the development EC2 instance through an instance profile.

Its purpose is read-only monitoring.

Current policies include:

* CloudWatchReadOnlyAccess
* AmazonEC2ReadOnlyAccess

The purpose is to allow monitoring without granting infrastructure modification permissions.

---

# 14. Detection Permissions

Detection should normally require read-only access.

Typical permissions may include:

```text
CloudWatch metric read
EC2 describe operations
Load Balancer health read
Application monitoring read
```

Detection does not require:

```text
ec2:TerminateInstances
ec2:StopInstances
ec2:ModifyInstanceAttribute
```

unless a future remediation component explicitly requires them.

---

# 15. Diagnosis Permissions

Diagnosis should normally remain read-only.

It may require access to:

* CloudWatch metrics
* CloudWatch logs
* EC2 metadata
* Load Balancer health information
* Deployment information
* Configuration metadata

Diagnosis should not receive write permissions merely because it analyzes infrastructure.

---

# 16. Risk Assessment Permissions

Risk assessment should ideally operate on already collected evidence and metadata.

Therefore it should require minimal direct AWS access.

Conceptually:

```text
AWS Evidence
     ↓
Diagnosis
     ↓
Risk Assessment
```

This reduces unnecessary AWS permissions.

---

# 17. Recommendation Permissions

Recommendation generation should not require infrastructure modification permissions.

A recommendation component should produce something like:

```text
Action:
Collect additional metrics and investigate the top CPU-consuming processes.
```

It should not directly execute the action.

This creates a security boundary between:

```text
Recommendation
```

and:

```text
Execution
```

---

# 18. Remediation IAM Boundary

Remediation is the most sensitive component.

A future remediation role should have only the permissions required for approved remediation actions.

Example:

```text
Remediation Role
    ↓
Specific EC2 Action
    ↓
Specific Resource Scope
```

Avoid:

```text
Remediation Role
    ↓
AdministratorAccess
```

The latter creates an unnecessarily large blast radius.

---

# 19. Blast Radius

Blast radius represents the potential impact if a credential, role, or application component is compromised.

Example:

```text
Broad IAM Permissions
       ↓
Compromise
       ↓
Large Blast Radius
```

versus:

```text
Least Privilege Role
       ↓
Compromise
       ↓
Limited Available Actions
```

CloudOps Autopilot should minimize blast radius through:

* Resource-level policies
* Separate roles
* Separate accounts
* Separate environments
* Approval controls
* Action allowlists

---

# 20. Human Approval as a Security Control

Human approval is currently a major security boundary.

Current flow:

```text
Detection
   ↓
Diagnosis
   ↓
Risk Assessment
   ↓
Recommendation
   ↓
Guardrails
   ↓
Human Approval
   ↓
Remediation
```

The system should not skip approval because an automated recommendation appears highly confident.

Approval provides an additional authorization boundary.

---

# 21. Guardrails

Guardrails provide another security layer.

Current remediation guardrails are intentionally restrictive.

Only approved actions are allowed.

Conceptually:

```text
Requested Action
       ↓
Allowlist Check
       ↓
Risk Check
       ↓
Allowed?
   ├── No → Block
   └── Yes → Approval
```

This is a default-deny approach.

---

# 22. Default Deny

When the system cannot confidently determine that an action is safe, it should not execute the action.

Examples:

```text
Unknown action
    ↓
DENY
```

```text
Unknown risk
    ↓
DENY
```

```text
Missing approval
    ↓
DENY
```

```text
Safety validation failure
    ↓
DENY
```

This principle is especially important for infrastructure-changing operations.

---

# 23. Credential Management

Credentials must never be hardcoded into source code.

Do not commit:

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
passwords
tokens
API keys
private keys
```

to Git.

The repository `.gitignore` already excludes:

```text
.env
```

and other local credential-related files.

---

# 24. Local Development Credentials

For local development, AWS credential mechanisms should be used rather than embedding secrets in Python code.

Preferred approaches include:

```text
AWS CLI credential configuration
AWS profiles
Environment-based temporary credentials
SSO where applicable
```

The application should obtain credentials through the AWS SDK credential provider chain.

---

# 25. Production Secrets

Production secrets should be stored using managed secret/configuration services where appropriate.

Potential services include:

* AWS Secrets Manager
* AWS Systems Manager Parameter Store

Secrets should not be stored in:

* Git repositories
* Docker images
* Terraform source files
* Application source code
* Plain-text configuration committed to Git

---

# 26. Encryption

Sensitive data should be protected both in transit and at rest.

### In Transit

Use TLS/HTTPS for external communication.

### At Rest

AWS managed encryption should be used for supported services.

Potential controls include:

* S3 encryption
* DynamoDB encryption
* CloudWatch log encryption where required
* Secrets Manager encryption
* KMS customer-managed keys where justified

Encryption key management should follow least privilege as well.

---

# 27. DynamoDB Security

The incident table contains operational information and should be protected.

Controls include:

* IAM authorization
* Encryption at rest
* Resource-level permissions
* Restricted application roles
* CloudTrail auditing where applicable
* No public access model

The application should only access the required table.

---

# 28. CloudWatch Security

Monitoring data may contain operational information.

Access should be restricted according to role.

Detection identities should have only the read permissions required.

Write access to logs or metrics should be separated from read access where practical.

---

# 29. Logging Security

Logs must not expose sensitive information.

Never log:

```text
Access keys
Secret keys
Passwords
Authentication tokens
Session credentials
Private keys
Sensitive application secrets
```

Operational identifiers may be logged where necessary, but the amount of sensitive infrastructure information should be minimized.

---

# 30. Auditability

Security-sensitive actions should be auditable.

The system should be able to answer:

* Who initiated the action?
* Which incident triggered it?
* What action was requested?
* What risk was assigned?
* Who approved it?
* Which identity executed it?
* What resource was affected?
* When did execution occur?
* What was the result?
* Was recovery verified?

AWS CloudTrail should be used for AWS API-level auditing where applicable.

Application-level audit information should complement CloudTrail.

---

# 31. Incident Audit Trail

An incident should eventually have an audit trail similar to:

```text
Incident Detected
       ↓
Evidence Collected
       ↓
Diagnosis Generated
       ↓
Risk Assessed
       ↓
Recommendation Generated
       ↓
Guardrails Passed
       ↓
Approval Granted
       ↓
Remediation Executed
       ↓
Verification Completed
```

Each important event should have appropriate timestamps and identifiers.

---

# 32. Correlation and Traceability

Security investigations require correlation.

The system should use identifiers such as:

* `incident_id`
* `execution_id`
* `request_id`
* `experiment_id`

This allows an investigator to trace activity across:

```text
Application Logs
CloudWatch
DynamoDB
AWS API activity
Future EventBridge events
```

---

# 33. Network Security

The current development EC2 instance uses restricted SSH access.

SSH access is limited to the configured development source IP rather than open Internet access.

HTTP/HTTPS access was removed when not required.

This reduces unnecessary exposure.

For production workloads, additional controls should be considered:

* Private subnets
* VPC endpoints
* Security groups
* Network ACLs where justified
* AWS Systems Manager instead of direct SSH where appropriate
* No unnecessary public IP addresses

---

# 34. Security Group Principle

Security groups should follow least privilege.

Example:

```text
Required Port
     ↓
Required Source
     ↓
Required Protocol
```

Avoid:

```text
0.0.0.0/0
```

unless public exposure is explicitly required and justified.

---

# 35. SSH Security

Development currently uses SSH access to the EC2 instance.

The project key pair is:

```text
cloudops-autopilot-key
```

The private key must remain outside Git.

The `.pem` file must never be committed to the repository.

For production, Systems Manager Session Manager may be preferred over directly exposing SSH.

---

# 36. CI/CD Security

Future GitHub Actions workflows should use short-lived AWS credentials.

Preferred architecture:

```text
GitHub Actions
      ↓
OIDC
      ↓
AWS IAM Role
      ↓
Temporary Credentials
      ↓
AWS
```

Long-lived AWS access keys should not be stored as permanent CI/CD credentials.

The deployment role should have only the permissions required for deployment.

---

# 37. Terraform Security

Terraform will eventually manage AWS infrastructure.

Terraform state may contain sensitive infrastructure information.

Therefore:

* State must not be committed to Git.
* Remote state should be protected.
* State access must be restricted.
* Encryption should be enabled.
* State locking should be used where supported.
* CI/CD should use controlled IAM roles.

The current `.gitignore` already excludes:

```text
.terraform/
*.tfstate
*.tfstate.*
```

Terraform lock files should normally remain version controlled.

---

# 38. Environment Isolation

The project should maintain clear boundaries between:

```text
DEV
UAT
PROD
```

Permissions should not automatically cross environments.

Example:

```text
DEV Role
   ↓
DEV Resources
```

rather than:

```text
DEV Role
   ↓
DEV + UAT + PROD
```

Production access should require stronger controls.

---

# 39. Multi-Account Security

As the platform evolves, a multi-account AWS architecture may be used.

Example:

```text
Management / Security
        |
        +---- Development
        |
        +---- UAT
        |
        +---- Production
        |
        +---- Logging / Audit
```

Cross-account access should be explicitly configured and limited.

The platform should not assume that one identity should control every account.

---

# 40. Cross-Account Remediation

Future cross-account remediation is highly sensitive.

A possible model is:

```text
CloudOps Control Plane
          ↓
AssumeRole
          ↓
Target Account Remediation Role
          ↓
Specific Resource
```

The target role should:

* Trust only the required principal
* Permit only approved actions
* Restrict resources where possible
* Be separately auditable
* Have a limited session duration
* Not provide administrator privileges unnecessarily

---

# 41. AI Security Boundary

AI-assisted RCA is planned for a future stage.

AI should not receive unrestricted AWS credentials.

Preferred architecture:

```text
AWS Evidence
      ↓
AI Analysis
      ↓
Possible Cause
      ↓
Recommendation
      ↓
Risk / Policy Engine
      ↓
Human Approval
      ↓
Remediation
```

The AI should primarily provide:

* Analysis
* Explanation
* Candidate causes
* Recommendations

The policy and safety layer should determine whether an action is permitted.

---

# 42. AI Prompt and Data Security

Future AI integrations must consider:

* Sensitive log data
* Credentials accidentally appearing in logs
* Personally identifiable information
* Internal infrastructure information
* Prompt injection
* Malicious log content
* Untrusted external data

External or untrusted data should never automatically become an authorization instruction.

---

# 43. Prompt Injection Boundary

Future AI systems may encounter malicious text inside:

* Application logs
* Error messages
* User-provided input
* Configuration
* Incident descriptions

The system must treat such content as data, not as trusted instructions.

For example:

```text
Log Content
    ↓
AI Analysis
    ↓
Untrusted Evidence
```

must never directly become:

```text
AWS Command
```

without policy validation and authorization.

---

# 44. Remediation Safety Boundary

The strongest security boundary should exist immediately before infrastructure modification.

```text
AI / Diagnosis
      ↓
Recommendation
      ↓
Risk
      ↓
Policy
      ↓
Guardrails
      ↓
Approval
      ↓
IAM Authorization
      ↓
AWS Resource
```

Multiple independent controls therefore exist before a potentially destructive action.

---

# 45. IAM Permission Separation

The architecture should progressively separate:

```text
Detection Role
```

from:

```text
Persistence Role
```

from:

```text
Remediation Role
```

from:

```text
Deployment Role
```

This prevents one compromised component from automatically obtaining all platform privileges.

---

# 46. Permission Review

IAM permissions should be reviewed periodically.

Review questions:

1. Is every permission still required?
2. Can a wildcard resource be narrowed?
3. Can an action be removed?
4. Can read and write access be separated?
5. Can a role replace an IAM user?
6. Can temporary credentials replace long-lived credentials?
7. Can a resource ARN replace `*`?

---

# 47. IAM Policy Design

Avoid unnecessary wildcard permissions.

Prefer:

```text
Specific Action
+
Specific Resource
```

where supported.

For example:

```text
dynamodb:GetItem
```

on:

```text
cloudops-autopilot-incidents
```

is preferable to unrestricted access to all DynamoDB tables.

Some AWS APIs require `Resource: "*"`.

In those cases, the permission should be documented and kept limited to the minimum required API actions.

---

# 48. Security Testing

Security must be tested continuously.

Testing areas include:

### IAM

* Permission denied scenarios
* Least-privilege validation
* Role assumption
* Cross-account boundaries

### Application

* Invalid input
* Unauthorized action
* Missing approval
* Invalid risk

### Secrets

* Secret scanning
* Credential leakage detection
* Repository scanning

### Infrastructure

* Security group validation
* Public exposure checks
* Encryption checks

---

# 49. Negative Security Tests

The system should explicitly test actions that must fail.

Examples:

```text
Unauthorized DynamoDB table
        ↓
DENY
```

```text
Unauthorized remediation action
        ↓
DENY
```

```text
Missing approval
        ↓
DENY
```

```text
High-risk action
        ↓
DENY
```

These tests demonstrate that security controls are actually enforced.

---

# 50. Current Security Controls

The current MVP already includes:

* Dedicated AWS development account
* IAM user rather than root for development
* EC2 IAM role
* CloudWatch read permissions
* EC2 read permissions
* DynamoDB resource-specific permissions
* Human approval
* Remediation allowlist
* Risk validation
* Idempotency
* Conditional DynamoDB writes
* Restricted SSH access
* `.env` exclusion from Git
* Terraform state exclusion from Git
* No credentials in source code

---

# 51. Current Security Gaps

The current project is not yet production-grade.

Important remaining work includes:

* Replace long-lived local IAM access keys with stronger identity mechanisms where possible
* Separate bootstrap and runtime roles
* Create dedicated remediation IAM role
* Narrow AWS managed policies where practical
* Add formal security testing
* Add secret scanning
* Add dependency vulnerability scanning
* Add CloudTrail review
* Add production account isolation
* Add centralized security logging
* Add infrastructure security validation
* Add Terraform-managed IAM
* Add CI/CD OIDC
* Add formal threat model testing
* Add durable audit trail

---

# 52. Security Maturity Model

The project security maturity can evolve as follows:

```text
Level 1
Basic IAM
   ↓
Level 2
Least Privilege
   ↓
Level 3
Role Separation
   ↓
Level 4
Automated Security Validation
   ↓
Level 5
Multi-Account Isolation
   ↓
Level 6
Short-Lived Identity
   ↓
Level 7
Policy-Based Remediation
   ↓
Level 8
Production Security Governance
```

The current MVP is progressing through the early levels.

---

# 53. Security and Reliability Relationship

Security and reliability must work together.

For example:

```text
IAM Denied
   ↓
Remediation Cannot Execute
```

is both:

* A security control
* An operational failure

Therefore the failure should be observable and recoverable without weakening security.

Security controls should never be bypassed simply to improve availability.

---

# 54. Security and Research Relationship

Security is also part of the research evaluation.

Potential research metrics include:

* Unsafe action rate
* Unauthorized action rate
* Guardrail bypass rate
* Approval bypass rate
* Duplicate execution rate
* Security control failure rate
* False authorization rate

A successful automation system should not only reduce operational effort.

It must do so without creating unacceptable security risk.

---

# 55. Security and Product Relationship

For a future commercial CloudOps Autopilot product, customers will require confidence that the platform cannot freely modify their infrastructure.

Therefore product trust depends on:

```text
Least Privilege
+
Policy Controls
+
Human Approval
+
Auditability
+
Isolation
+
Verification
```

Security is therefore part of the product architecture, not only an infrastructure concern.

---

# 56. Production Security Checklist

Before production deployment:

```text
[ ] Separate AWS production account
[ ] Separate production IAM roles
[ ] No root credentials for application access
[ ] No long-lived application access keys
[ ] Least-privilege IAM policies
[ ] Dedicated remediation role
[ ] Resource-level restrictions
[ ] Human approval for risky actions
[ ] Default-deny guardrails
[ ] Secrets Manager / Parameter Store where required
[ ] Encryption at rest
[ ] TLS in transit
[ ] CloudTrail auditing
[ ] Centralized security logging
[ ] Secret scanning
[ ] Dependency vulnerability scanning
[ ] Infrastructure security scanning
[ ] Security-group review
[ ] Private networking where appropriate
[ ] CI/CD OIDC
[ ] Terraform state protection
[ ] Cross-account access controls
[ ] Security tests
[ ] Failure tests
[ ] Audit trail
[ ] Incident response procedure
```

---

# 57. Final Security Principle

CloudOps Autopilot is designed around a fundamental security rule:

> **Automation should have only the authority it needs, and infrastructure-changing authority should be separated, controlled, approved, auditable, and verifiable.**

The system should never rely on trust alone.

Instead, trust should be established through:

```text
Identity
   ↓
Authorization
   ↓
Policy
   ↓
Guardrails
   ↓
Approval
   ↓
Execution
   ↓
Audit
   ↓
Verification
```

This security model supports the project's engineering, research, portfolio, and future product objectives.

---

## Related Documentation

* [Product Requirements](requirements/product-requirements.md)
* [System Architecture](architecture/system-architecture.md)
* [AWS Architecture](architecture/aws-architecture.md)
* [Incident Lifecycle](architecture/incident-lifecycle.md)
* [Configuration Strategy](configuration-strategy.md)
* [Logging & Observability Strategy](logging-observability-strategy.md)
* [Error Handling & Reliability Strategy](error-handling-reliability-strategy.md)

## Related Architecture Decisions

* [ADR-001: Repository Pattern](decisions/ADR-001-repository-pattern.md)
* [ADR-002: DynamoDB Persistence](decisions/ADR-002-dynamodb-persistence.md)
* [ADR-003: Human Approval Before Remediation](decisions/ADR-003-human-approval.md)
* [ADR-004: Conditional Write and Idempotency](decisions/ADR-004-conditional-write-idempotency.md)
