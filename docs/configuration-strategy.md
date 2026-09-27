# CloudOps Autopilot — Configuration Strategy

## 1. Purpose

This document defines how CloudOps Autopilot manages application configuration across development, testing, and future production environments.

The configuration strategy is designed to provide:

* Clear separation between code and configuration
* Environment-specific configuration
* Secure handling of sensitive values
* Predictable application startup
* Configuration validation
* Easier testing
* Controlled deployment
* Future DEV/UAT/PROD separation

Configuration must remain separate from business logic wherever practical.

---

# 2. Configuration Principles

CloudOps Autopilot follows these principles:

1. Configuration should not be hardcoded unnecessarily.
2. Environment-specific values should be externalized.
3. Secrets must never be committed to Git.
4. Configuration should be validated at startup.
5. Defaults should be safe and explicit.
6. Production configuration should not depend on developer-machine settings.
7. Configuration names should remain consistent across environments.
8. Infrastructure configuration and application configuration should be clearly separated.
9. Configuration changes should be traceable.
10. Sensitive configuration should use appropriate secret-management mechanisms.

---

# 3. Current Configuration Model

The current application uses environment variables for runtime configuration.

The project uses:

```text
python-dotenv
```

to load environment variables during local development.

The current configuration module contains values such as:

```text
AWS_REGION
EC2_INSTANCE_ID
CPU_THRESHOLD
```

These values are used by the application without embedding environment-specific values directly into the core business logic.

---

# 4. Configuration Categories

Configuration is divided into several categories.

## 4.1 Application Configuration

Examples:

* Application environment
* Log level
* Feature flags
* Detection thresholds
* Detection windows
* Retry configuration

---

## 4.2 AWS Configuration

Examples:

* AWS region
* AWS account context
* Resource identifiers
* DynamoDB table name
* CloudWatch configuration

---

## 4.3 Security Configuration

Examples:

* Secret identifiers
* Authentication configuration
* Encryption configuration
* IAM-related settings

Sensitive security values must not be stored directly in source code.

---

## 4.4 Operational Configuration

Examples:

* Logging level
* Monitoring intervals
* Retry limits
* Timeout values
* Notification configuration

---

# 5. Environment Variables

Environment variables are the primary application-level configuration mechanism for the current project.

Conceptually:

```text
Operating Environment
        ↓
Environment Variables
        ↓
Configuration Module
        ↓
Application Components
```

This allows the same application code to operate with different environment-specific values.

---

# 6. Current Environment Variables

The current project uses configuration values such as:

```text
AWS_REGION
EC2_INSTANCE_ID
CPU_THRESHOLD
```

Example local configuration:

```text
AWS_REGION=ap-south-1
EC2_INSTANCE_ID=<target-instance-id>
CPU_THRESHOLD=90
```

The actual resource identifier should be supplied through the local environment rather than embedded directly into application logic.

---

# 7. `.env` for Local Development

For local development, a `.env` file may be used.

Example:

```text
AWS_REGION=ap-south-1
EC2_INSTANCE_ID=i-example
CPU_THRESHOLD=90
```

The `.env` file is intended for developer-local configuration.

It must not be committed to Git.

The project `.gitignore` already excludes:

```text
.env
```

This prevents local environment configuration from accidentally being pushed to GitHub.

---

# 8. Secrets vs Configuration

Not every environment variable is a secret.

The project distinguishes between:

### Non-sensitive configuration

Examples:

```text
AWS_REGION
CPU_THRESHOLD
LOG_LEVEL
```

and:

### Sensitive values

Examples:

```text
API credentials
Database passwords
Access tokens
Private keys
Application secrets
```

Sensitive values must not be stored in source code or committed `.env` files.

---

# 9. AWS Credentials

Application credentials should not be embedded in configuration files.

For local development, AWS authentication should use the AWS credential mechanisms supported by the AWS SDK and CLI.

The preferred model is:

```text
Local Development
      ↓
AWS CLI / Credential Provider Chain
      ↓
boto3
      ↓
AWS Services
```

The application should not contain:

```text
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

inside source-controlled configuration.

---

# 10. Runtime Identity

In deployed AWS environments, the application should use IAM roles instead of long-lived access keys.

For example:

```text
ECS Task
   ↓
IAM Task Role
   ↓
AWS API
```

or:

```text
Lambda
   ↓
Lambda Execution Role
   ↓
AWS API
```

This follows the principle of using temporary AWS credentials wherever practical.

---

# 11. Configuration Module

The application should have a centralized configuration module.

Current location:

```text
src/cloudops_engine/config.py
```

The configuration module acts as the boundary between environment configuration and application code.

Conceptually:

```text
Environment
     ↓
config.py
     ↓
Application Services
```

Application components should consume configuration through the configuration layer rather than repeatedly reading environment variables throughout the codebase.

---

# 12. Configuration Validation

Configuration should be validated before the application performs operational work.

Examples:

### AWS Region

Must be a non-empty valid configuration value.

### EC2 Instance ID

Must be present when EC2 monitoring is enabled.

### CPU Threshold

Must be a valid numeric value.

Example conceptual validation:

```text
CPU_THRESHOLD
      ↓
Is value numeric?
      ↓
Is value within valid range?
      ↓
Valid → Application starts
Invalid → Application fails clearly
```

Failing early is preferable to allowing invalid configuration to cause unexpected behavior later.

---

# 13. Safe Defaults

Defaults should be used carefully.

A default is acceptable when it is:

* Safe
* Predictable
* Environment-independent
* Unlikely to cause destructive behavior

For example:

```text
AWS_REGION=ap-south-1
```

may be appropriate for the current development environment.

However, resource identifiers and production-specific values should not silently default to an arbitrary resource.

---

# 14. Required vs Optional Configuration

Configuration values should be classified as either required or optional.

### Required

Examples:

```text
AWS_REGION
EC2_INSTANCE_ID
```

when the relevant monitoring workflow is enabled.

### Optional

Examples:

```text
LOG_LEVEL
```

when a safe default exists.

The application should clearly report missing required configuration.

---

# 15. Configuration and Business Logic

Business logic should not contain environment-specific values.

Avoid:

```python
if instance_id == "i-05e3bbde2a13509f7":
    ...
```

Prefer:

```python
instance_id = configured_instance_id
```

This keeps the application reusable across environments.

---

# 16. Configuration and Infrastructure

Infrastructure configuration and application configuration serve different purposes.

### Infrastructure Configuration

Examples:

* Terraform variables
* AWS resource definitions
* IAM policies
* DynamoDB table definitions
* Networking

### Application Configuration

Examples:

* Thresholds
* Feature flags
* Runtime behavior
* Monitoring configuration
* Log levels

The two should be related but not unnecessarily coupled.

---

# 17. Development Environment

The current development environment uses:

```text
Windows 11
Git Bash
VS Code
Python virtual environment
AWS CLI
AWS account
ap-south-1
```

Local configuration is provided through the developer environment.

The development environment is not treated as a production-equivalent deployment.

---

# 18. Future Environment Strategy

The project is expected to evolve toward:

```text
DEV
 ↓
UAT
 ↓
PROD
```

Each environment should have its own configuration values.

For example:

```text
DEV
├── AWS account / resources
├── DynamoDB table
├── Monitoring thresholds
└── Logging configuration

UAT
├── AWS account / resources
├── DynamoDB table
├── Monitoring thresholds
└── Logging configuration

PROD
├── AWS account / resources
├── DynamoDB table
├── Monitoring thresholds
└── Logging configuration
```

The application code should remain the same wherever practical.

---

# 19. Configuration Precedence

A future deployment model should define configuration precedence explicitly.

A conceptual order is:

```text
Application Defaults
        ↓
Environment Configuration
        ↓
Deployment Configuration
        ↓
Runtime Environment Variables
```

More specific configuration should override less specific defaults only when explicitly defined.

The exact precedence should be standardized before production deployment.

---

# 20. Local `.env` vs Production Secrets

The `.env` approach is appropriate for local non-sensitive development configuration.

It should not automatically become the production secret-management mechanism.

A production AWS environment should use appropriate managed services such as:

* AWS Secrets Manager
* AWS Systems Manager Parameter Store
* IAM roles
* Deployment-time configuration

The selection should depend on the sensitivity and lifecycle of the value.

---

# 21. Secrets Manager Strategy

AWS Secrets Manager should be considered for sensitive runtime values that need secure storage and controlled retrieval.

Conceptually:

```text
Application
    ↓
IAM Role
    ↓
Secrets Manager
    ↓
Secret Value
```

The secret value should not be committed to:

* Git
* Source code
* README
* Terraform variables stored in plain text
* Docker images
* Application logs

---

# 22. Parameter Store Strategy

AWS Systems Manager Parameter Store may be used for non-secret or appropriately protected runtime configuration.

Examples:

```text
/cloudops-autopilot/prod/cpu-threshold
/cloudops-autopilot/prod/log-level
```

Sensitive parameters can use appropriate encryption.

The final production design should select Secrets Manager or Parameter Store based on the actual configuration requirement.

---

# 23. Configuration Versioning

Configuration changes that affect application behavior should be traceable.

Examples:

* Threshold changes
* Detection-window changes
* Feature changes
* Retry changes
* Verification changes

Configuration should therefore be managed through version-controlled infrastructure or deployment configuration wherever practical.

---

# 24. Configuration Changes and Safety

Configuration changes can alter automation behavior.

For example:

```text
CPU_THRESHOLD=90
```

versus:

```text
CPU_THRESHOLD=70
```

can significantly change incident detection frequency.

Similarly, changing remediation-related configuration can affect operational risk.

Therefore, important configuration changes should be:

* Reviewed
* Tested
* Documented
* Versioned
* Auditable

---

# 25. Configuration Validation by Environment

Different environments may use different validation requirements.

Example:

```text
DEV
    ↓
Flexible experimentation

UAT
    ↓
Controlled testing

PROD
    ↓
Strict validation
```

Production should reject configurations that violate mandatory safety constraints.

---

# 26. Configuration Security

Configuration security requires protection at multiple levels.

### Source Control

Do not commit secrets.

### Runtime

Use IAM roles and managed secret mechanisms.

### Logs

Do not log secret values.

### Infrastructure

Restrict who can modify configuration.

### Deployment

Require appropriate review and authorization for sensitive changes.

---

# 27. Configuration and IAM

Configuration strategy must not become a mechanism for bypassing IAM.

For example:

```text
CONFIGURATION
    ↓
Resource ID
```

does not grant access to that resource.

IAM determines whether the application can access the resource.

Therefore:

```text
Configuration = What resource to target
IAM = What the application is allowed to do
```

Both controls are required.

---

# 28. Configuration and Multi-Account AWS

The future architecture may use separate AWS accounts for:

```text
DEV
UAT
PROD
LOGGING
AUDIT
```

Configuration should identify the appropriate environment and AWS context without embedding credentials.

The runtime identity should be provided through IAM roles and AWS account boundaries.

---

# 29. Configuration for Detection

Detection configuration should eventually include values such as:

```text
CPU_THRESHOLD
REQUIRED_BREACHES
DETECTION_WINDOW_MINUTES
METRIC_PERIOD_SECONDS
```

Example:

```text
CPU_THRESHOLD=90
REQUIRED_BREACHES=3
DETECTION_WINDOW_MINUTES=15
METRIC_PERIOD_SECONDS=300
```

These values should be configuration rather than hardcoded business logic.

---

# 30. Configuration for Remediation

Future remediation configuration may include:

```text
ALLOWED_ACTIONS
REQUIRED_APPROVAL
MAX_RESOURCE_COUNT
ENVIRONMENT_RESTRICTIONS
```

Remediation configuration must follow a restrictive default.

The absence of an explicit permission should not automatically allow an action.

---

# 31. Configuration for Verification

Verification may eventually include:

```text
VERIFICATION_WINDOW
RECOVERY_THRESHOLD
MAX_VERIFICATION_ATTEMPTS
VERIFICATION_INTERVAL
```

These values should be configurable but must also have safe validation boundaries.

---

# 32. Configuration Failure Behavior

If required configuration is invalid, the application should fail clearly rather than operating with an unsafe assumption.

Example:

```text
Missing EC2_INSTANCE_ID
        ↓
Configuration Validation
        ↓
Startup Failure
        ↓
Clear Error Message
```

The system should not silently select an arbitrary AWS resource.

---

# 33. Configuration Observability

The application may log non-sensitive configuration metadata at startup.

For example:

```text
Environment: DEV
AWS Region: ap-south-1
Monitoring: Enabled
CPU Threshold: 90
```

Sensitive values must never be logged.

Resource identifiers should be logged only when operationally necessary and according to the security policy.

---

# 34. Configuration Testing

Configuration should be tested independently.

Tests should cover:

* Required configuration present
* Required configuration missing
* Invalid threshold
* Invalid numeric values
* Safe defaults
* Environment-specific configuration
* Invalid remediation configuration
* Secret values not exposed in logs

Configuration tests should prevent deployment of unsafe configuration.

---

# 35. Docker Configuration

When the application is containerized in the future, configuration should be injected at runtime.

Preferred model:

```text
Docker Image
     ↓
Generic Application
     ↓
Runtime Environment Variables / Secret Provider
```

The Docker image should not contain environment-specific secrets.

This allows the same image to move through:

```text
DEV → UAT → PROD
```

without rebuilding the application solely to change configuration.

---

# 36. CI/CD Configuration

Future GitHub Actions workflows should separate:

* Build configuration
* Test configuration
* Deployment configuration
* Environment-specific configuration
* Secrets

CI/CD secrets should be stored using the appropriate secure secret mechanism.

Production deployment should not depend on a developer's local `.env` file.

---

# 37. Configuration Governance

Configuration that affects operational behavior should have clear ownership.

Potential governance controls include:

* Pull request review
* Version control
* Environment separation
* Change history
* Approval for production changes
* Automated validation
* Rollback capability

This becomes particularly important for remediation-related configuration.

---

# 38. Current vs Target Configuration Architecture

## Current

```text
Local Environment
      ↓
.env / Environment Variables
      ↓
config.py
      ↓
CloudOps Engine
```

## Target

```text
Environment
      ↓
Managed Configuration / Secrets
      ↓
Runtime Identity
      ↓
Configuration Loader
      ↓
Validated Configuration
      ↓
CloudOps Engine
```

The target architecture separates configuration management from application code while maintaining strong security controls.

---

# 39. Configuration Lifecycle

The configuration lifecycle is:

```text
Define
  ↓
Store
  ↓
Validate
  ↓
Deploy
  ↓
Load
  ↓
Use
  ↓
Monitor
  ↓
Review
  ↓
Update
```

Every important configuration change should be traceable through this lifecycle.

---

# 40. Industry Standards Alignment

The configuration strategy aligns with common engineering principles including:

* Configuration externalization
* Environment separation
* Secret management
* Least privilege
* Immutable application artifacts
* Runtime configuration
* Configuration validation
* Version-controlled infrastructure
* Secure CI/CD practices
* Separation of configuration and code

The strategy is designed to evolve toward production-grade configuration management rather than treating the current local `.env` model as the final architecture.

---

# 41. Current Implementation Status

### Implemented

* Environment-variable based configuration
* `.env` support
* `python-dotenv`
* Central configuration module
* `.env` excluded from Git
* AWS region configuration
* EC2 instance configuration
* CPU threshold configuration

### Planned

* Strong configuration validation
* Environment-specific configuration
* DEV/UAT/PROD separation
* Managed configuration
* Secrets Manager / Parameter Store integration
* Configuration testing
* CI/CD configuration management
* Production configuration governance

---

# 42. Configuration Strategy Summary

CloudOps Autopilot separates configuration from application logic and uses environment-based configuration for the current development implementation.

The current approach provides a practical foundation:

```text
Environment Variables
        ↓
Configuration Module
        ↓
Application
```

The target architecture evolves toward:

```text
Managed Configuration
        +
Secrets Management
        +
IAM
        +
Environment Separation
        +
Validation
        +
Version Control
        ↓
CloudOps Autopilot
```

The key principle is:

> **Configuration determines how the application operates; IAM determines what the application is allowed to do.**

Configuration must remain secure, validated, environment-aware, and independently manageable throughout the project's evolution.

---

## Related Documentation

* [Product Requirements](requirements/product-requirements.md)
* [System Architecture](architecture/system-architecture.md)
* [AWS Architecture](architecture/aws-architecture.md)
* [Incident Lifecycle](architecture/incident-lifecycle.md)

## Related Architecture Decisions

* [ADR-001: Repository Pattern](decisions/ADR-001-repository-pattern.md)
* [ADR-002: DynamoDB Persistence](decisions/ADR-002-dynamodb-persistence.md)
* [ADR-003: Human Approval Before Remediation](decisions/ADR-003-human-approval.md)
* [ADR-004: Conditional Write and Idempotency](decisions/ADR-004-conditional-write-idempotency.md)
