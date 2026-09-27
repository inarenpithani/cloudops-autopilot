# CloudOps Autopilot — Dependency & Project Structure Cleanup Strategy

## 1. Purpose

This document defines the dependency-management and project-structure cleanup strategy for CloudOps Autopilot.

The project has evolved incrementally through:

* Detection
* Diagnosis
* Remediation controls
* Incident lifecycle
* DynamoDB persistence
* Configuration
* Observability
* Reliability
* Security
* Testing

As functionality grows, the repository structure and dependency management must remain clean and predictable.

The objectives are:

1. Maintain a clear project structure.
2. Establish a single dependency source of truth.
3. Remove unnecessary duplication.
4. Separate application code from tests and infrastructure.
5. Keep development tooling explicit.
6. Follow Python packaging conventions.
7. Make local development reproducible.
8. Prepare the repository for CI/CD and containerization.
9. Avoid unnecessary architectural complexity.
10. Keep future contributors able to understand the repository quickly.

---

# 2. Project Structure Principles

The repository follows these principles:

* Application code belongs under `src/`.
* Tests belong under `tests/`.
* Documentation belongs under `docs/`.
* Infrastructure code belongs under `infrastructure/`.
* Configuration belongs outside business logic.
* Temporary/generated files must not be committed.
* Dependencies must have one authoritative definition.
* Test dependencies should be separated from runtime dependencies.
* Infrastructure state must not be committed.
* Documentation should explain architectural decisions rather than duplicate implementation code.

---

# 3. Target Repository Structure

The intended structure is:

```text id="5v2j3m"
cloudops-autopilot/
│
├── README.md
├── pyproject.toml
├── .gitignore
├── .env.example
│
├── docs/
│   ├── requirements/
│   │   └── product-requirements.md
│   │
│   ├── architecture/
│   │   ├── system-architecture.md
│   │   ├── aws-architecture.md
│   │   └── incident-lifecycle.md
│   │
│   ├── decisions/
│   │   ├── ADR-001-repository-pattern.md
│   │   ├── ADR-002-dynamodb-persistence.md
│   │   ├── ADR-003-human-approval.md
│   │   └── ADR-004-conditional-write-idempotency.md
│   │
│   ├── research/
│   │   └── research-problem.md
│   │
│   ├── configuration-strategy.md
│   ├── logging-observability-strategy.md
│   ├── error-handling-reliability-strategy.md
│   ├── security-iam-strategy.md
│   └── testing-strategy.md
│
├── src/
│   └── cloudops_engine/
│       ├── __init__.py
│       ├── main.py
│       │
│       ├── aws/
│       │   ├── __init__.py
│       │   └── cloudwatch.py
│       │
│       ├── config.py
│       │
│       ├── detection/
│       │   ├── __init__.py
│       │   ├── detector.py
│       │   ├── application_detector.py
│       │   └── service_detector.py
│       │
│       ├── diagnosis/
│       │   ├── __init__.py
│       │   └── root_cause.py
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── incident.py
│       │   ├── incident_lifecycle.py
│       │   ├── evidence.py
│       │   ├── detection_result.py
│       │   ├── diagnosis.py
│       │   └── remediation_result.py
│       │
│       ├── remediation/
│       │   ├── __init__.py
│       │   ├── approval.py
│       │   ├── executor.py
│       │   ├── guardrails.py
│       │   ├── idempotency.py
│       │   └── recommendation.py
│       │
│       ├── repositories/
│       │   ├── __init__.py
│       │   ├── incident_repository.py
│       │   ├── in_memory_incident_repository.py
│       │   └── dynamodb_incident_repository.py
│       │
│       ├── risk/
│       │   ├── __init__.py
│       │   └── assessment.py
│       │
│       ├── services/
│       │   ├── __init__.py
│       │   └── monitoring.py
│       │
│       └── verification/
│           ├── __init__.py
│           └── health_check.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
└── infrastructure/
    └── terraform/
        └── .gitkeep
```

This structure keeps domain responsibilities separated.

---

# 4. Source Layout

The project uses the `src` layout:

```text id="v4t7r3"
src/
└── cloudops_engine/
```

The `src` layout reduces accidental imports from the repository root and more closely represents how the installed package is consumed.

The project is already configured for this layout through `pyproject.toml`.

---

# 5. Application Package

The primary package is:

```text id="2s9f2m"
cloudops_engine
```

Its responsibility is to contain the CloudOps Autopilot application.

Application code should not be placed directly in:

```text id="z8v7c1"
tests/
docs/
infrastructure/
```

---

# 6. Package Initialization

Python packages should use appropriate `__init__.py` files where package initialization is required.

Example:

```text id="t7q4e8"
src/cloudops_engine/__init__.py
src/cloudops_engine/models/__init__.py
src/cloudops_engine/detection/__init__.py
```

These files should remain intentionally lightweight.

They should not contain large application initialization logic.

---

# 7. Domain Separation

The application is divided by responsibility.

### AWS

External AWS service clients.

### Detection

Determines whether an incident condition exists.

### Diagnosis

Analyzes evidence and determines probable causes.

### Models

Defines domain data structures.

### Remediation

Controls recommendations, approvals, guardrails, idempotency, and execution.

### Repositories

Provides persistence abstractions and implementations.

### Risk

Determines incident risk.

### Services

Coordinates application workflows.

### Verification

Determines whether the system recovered.

This separation supports maintainability and testing.

---

# 8. Separation of Business Logic and Infrastructure

Business logic should not be tightly coupled to AWS SDK calls.

For example:

```text id="6m2r7v"
Detection Logic
      ↓
CloudWatch Client
```

rather than:

```text id="z5f1cx"
Detection Logic
      ↓
Direct boto3 calls everywhere
```

This makes the business logic easier to test.

---

# 9. Repository Pattern

Persistence is abstracted through:

```text id="6g9k2d"
IncidentRepository
```

Implementations include:

```text id="x4k8q2"
InMemoryIncidentRepository
DynamoDBIncidentRepository
```

This allows the domain/application layer to depend on an abstraction rather than a specific database.

The repository decision is documented in ADR-001.

---

# 10. AWS Client Separation

AWS SDK interactions should be isolated in appropriate modules.

Current example:

```text id="0g4t7v"
cloudops_engine/aws/cloudwatch.py
```

This prevents direct AWS API calls from spreading throughout the application.

Future AWS clients should follow the same pattern.

Potential future modules include:

```text id="7f3p8m"
eventbridge.py
ec2.py
logs.py
sns.py
```

Only when those integrations are actually required.

---

# 11. Avoid Premature Abstraction

The project should not create an abstraction merely because a future service might exist.

For example, do not create:

```text id="v3b7z9"
GenericCloudProviderInterface
```

before there is a real requirement for multiple cloud providers.

Abstraction should be introduced when it solves a current architectural problem.

---

# 12. Configuration Separation

Configuration belongs in:

```text id="e6q8w2"
cloudops_engine/config.py
```

Configuration should not be scattered throughout the application.

Examples:

```text id="0l9gq1"
AWS_REGION
EC2_INSTANCE_ID
CPU_THRESHOLD
```

Business logic should receive configuration through appropriate interfaces rather than reading environment variables throughout the codebase.

---

# 13. Dependency Source of Truth

The project uses:

```text id="b7s4x3"
pyproject.toml
```

as the authoritative dependency definition.

Runtime dependencies are defined under:

```toml id="6t2f8a"
[project]
dependencies = [
    "boto3",
    "python-dotenv",
]
```

Development dependencies are defined under:

```toml id="1c9q7e"
[project.optional-dependencies]
dev = [
    "pytest",
]
```

This provides a clear separation between runtime and development requirements.

---

# 14. Requirements.txt Cleanup

The project previously contained:

```text id="2q7h5c"
requirements.txt
```

with development/test dependency information.

Because `pyproject.toml` is now the dependency source of truth, maintaining duplicate dependency definitions creates unnecessary drift risk.

The cleanup strategy is:

```text id="q1w7p3"
pyproject.toml
      ↓
Single dependency definition
```

The old duplicate `requirements.txt` should be removed if it is no longer required by deployment tooling.

If a deployment target later requires a generated requirements file, it should be generated from the authoritative dependency definition rather than manually maintained.

---

# 15. Editable Installation

The project is installed locally using:

```bash id="d2q7n4"
python -m pip install -e ".[dev]"
```

This provides:

* Editable application installation
* Runtime dependencies
* Development dependencies

Using:

```text id="4g8c2f"
python -m pip
```

is preferred over relying on a potentially ambiguous global `pip` executable.

---

# 16. Virtual Environment

Local development uses:

```text id="v5p3m1"
.venv/
```

The virtual environment must not be committed to Git.

The repository `.gitignore` already excludes:

```text id="e9x1r6"
.venv/
venv/
```

This keeps environment-specific binaries and packages outside version control.

---

# 17. Python Version

The project currently declares:

```toml id="h6s4x2"
requires-python = ">=3.14"
```

This establishes the minimum Python version expected by the project.

The development environment currently uses Python 3.14.

Future production deployment should standardize the exact supported Python version across:

* Local development
* CI/CD
* Docker
* Runtime environment

---

# 18. Dependency Pinning Strategy

Application dependency management should balance:

* Reproducibility
* Security updates
* Maintainability

The project should distinguish between:

```text id="z4m6n8"
Direct Dependencies
```

and:

```text id="q7w1s5"
Transitive Dependencies
```

Direct dependencies should be declared explicitly.

Transitive dependencies should generally be resolved by the package manager.

For production deployments, dependency resolution should be reproducible through the selected packaging/deployment mechanism.

---

# 19. Dependency Updates

Dependency updates should be intentional.

Recommended process:

```text id="7x5q9k"
Dependency Update
      ↓
Review Release Notes
      ↓
Run Tests
      ↓
Run Security Scan
      ↓
Validate Integration
      ↓
Commit
```

Blindly upgrading every package without testing should be avoided.

---

# 20. Dependency Security

Dependencies are part of the application's attack surface.

The project should eventually use automated vulnerability scanning.

Potential tooling includes:

* `pip-audit`
* GitHub Dependabot
* GitHub security scanning

Security tooling should be integrated into CI/CD when the pipeline is introduced.

---

# 21. Test Dependency Separation

Runtime dependencies:

```text id="p4y2n8"
boto3
python-dotenv
```

Development dependencies:

```text id="k7s5c3"
pytest
```

Future development tools may include:

```text id="a1v6z9"
ruff
mypy
pip-audit
```

These should not be required by the production runtime unless there is a specific reason.

---

# 22. Formatting and Linting

The project should eventually standardize code quality tooling.

A likely future setup is:

```text id="f5r8w2"
Ruff
```

for:

* Formatting
* Linting
* Import organization
* Common Python quality checks

The exact tooling should be introduced as part of the CI/CD quality-gate work.

---

# 23. Type Checking

Static type checking can improve reliability as the codebase grows.

A future tool such as:

```text id="x8c2m4"
mypy
```

may be introduced.

Type checking should initially focus on important boundaries:

* AWS clients
* Repositories
* Models
* Services
* Remediation interfaces

It should not become a blocker before the project has an agreed typing standard.

---

# 24. Naming Conventions

Python modules should use lowercase snake_case.

Examples:

```text id="w4n8q2"
cloudwatch.py
root_cause.py
incident_repository.py
health_check.py
```

Classes should use PascalCase:

```text id="s7f2m9"
CloudWatchClient
IncidentRepository
DynamoDBIncidentRepository
MonitoringService
```

Functions and variables should use snake_case:

```text id="c3v8x1"
detect_high_cpu()
incident_id
cpu_threshold
```

Constants should use uppercase when appropriate:

```text id="m9q4z6"
AWS_REGION
CPU_THRESHOLD
```

---

# 25. Import Organization

Imports should be organized consistently.

Typical structure:

```python id="u7g3p5"
from datetime import datetime

import boto3

from cloudops_engine.models.incident import Incident
```

The expected grouping is:

1. Standard library
2. Third-party packages
3. Internal application packages

Consistent imports improve readability and automated linting.

---

# 26. Circular Dependency Prevention

The project should avoid circular dependencies.

For example:

```text id="p8m2r4"
module A → module B
module B → module A
```

should be avoided.

A clean dependency direction is preferred:

```text id="v6x9k1"
Models
  ↑
Domain Logic
  ↑
Services
  ↑
Infrastructure
```

The exact dependency direction may evolve, but lower-level domain concepts should not unnecessarily depend on high-level orchestration.

---

# 27. Model Simplicity

Domain models should remain simple.

Current examples include:

* `Incident`
* `Evidence`
* `DiagnosisResult`
* `DetectionResult`
* `RemediationResult`

These models should represent domain information rather than contain large infrastructure integrations.

---

# 28. Main Application Entry Point

The current application entry point is:

```text id="j4c7m2"
src/cloudops_engine/main.py
```

`main.py` should remain an orchestration entry point rather than becoming a large business-logic module.

Its responsibilities should primarily include:

* Initialize dependencies
* Coordinate services
* Execute the workflow
* Handle top-level application errors
* Provide application entry behavior

Complex logic should live in dedicated modules.

---

# 29. Test Structure Cleanup

The test structure should remain aligned with application responsibilities.

Target:

```text id="q8v4k2"
tests/
├── unit/
│   ├── detection/
│   ├── diagnosis/
│   ├── remediation/
│   ├── repositories/
│   └── services/
│
├── integration/
│   ├── aws/
│   └── repositories/
│
└── e2e/
```

The current repository may contain flatter test files.

The structure should be expanded only when the number of tests justifies additional organization.

---

# 30. Unit vs Integration Naming

Test names should make the test level obvious through directory placement.

Example:

```text id="f7w2q9"
tests/unit/test_guardrails.py
```

versus:

```text id="x3n8m5"
tests/integration/test_dynamodb_incident_persistence.py
```

This makes it easier to determine whether AWS access is required.

---

# 31. Integration Test Isolation

AWS integration tests should never assume that another test has created the required resource.

Each test should:

1. Create or identify its required test resource.
2. Execute the test.
3. Validate the result.
4. Clean up test state.

This keeps tests reproducible.

---

# 32. Infrastructure Structure

Infrastructure code belongs under:

```text id="v9s2k4"
infrastructure/
└── terraform/
```

The Terraform directory should eventually contain environment-aware infrastructure definitions.

A possible future structure is:

```text id="z6m3q8"
infrastructure/
└── terraform/
    ├── modules/
    ├── environments/
    │   ├── dev/
    │   ├── uat/
    │   └── prod/
    └── README.md
```

This should be introduced when Terraform implementation begins.

---

# 33. Terraform State

Terraform state must never be committed to Git.

The `.gitignore` already excludes:

```text id="s8x4n1"
.terraform/
*.tfstate
*.tfstate.*
```

The state should eventually be stored in a protected remote backend.

Production state access must be restricted.

---

# 34. Generated Files

Generated files should not normally be committed.

Examples:

```text id="e7r3v5"
__pycache__/
*.pyc
*.egg-info/
.terraform/
*.tfstate
```

The `.gitignore` already covers these categories.

Generated build artifacts should be managed by the appropriate build or CI/CD system.

---

# 35. Environment Files

Local environment configuration should use:

```text id="k4y7m2"
.env
```

but `.env` must not be committed.

A safe template should eventually be maintained:

```text id="b8q3x6"
.env.example
```

containing variable names but no secrets.

Example:

```text id="9m4v7k"
AWS_REGION=ap-south-1
EC2_INSTANCE_ID=
CPU_THRESHOLD=90
```

---

# 36. Documentation Organization

Documentation should remain grouped by purpose.

```text id="n5x8c2"
requirements/
architecture/
decisions/
research/
```

Operational strategy documents may remain directly under `docs/` when they describe cross-cutting engineering practices.

The goal is discoverability rather than excessive folder nesting.

---

# 37. ADR Organization

Architecture Decision Records should remain under:

```text id="c7m2p9"
docs/decisions/
```

Current ADRs:

```text id="r8x4w1"
ADR-001-repository-pattern.md
ADR-002-dynamodb-persistence.md
ADR-003-human-approval.md
ADR-004-conditional-write-idempotency.md
```

New ADRs should be created only for meaningful architectural decisions.

---

# 38. Avoid Documentation Duplication

Documentation should not become a second copy of the source code.

For example, a strategy document should explain:

```text id="q2v8m5"
Why the system uses DynamoDB
```

rather than copying the entire repository implementation.

The source code remains the implementation source of truth.

Documentation explains:

* Intent
* Architecture
* Constraints
* Decisions
* Trade-offs
* Operational expectations

---

# 39. Dependency Graph

The intended application dependency direction is approximately:

```text id="h6r2p8"
Models
  ↑
Detection / Diagnosis / Risk
  ↑
Remediation / Verification
  ↑
Services
  ↑
Main / Application Entry Point
```

Infrastructure implementations such as:

```text id="z4c7m1"
AWS Clients
DynamoDB Repository
```

should be injected into application services rather than embedded throughout the domain.

---

# 40. Dependency Injection

The current project already demonstrates basic dependency injection.

Example:

```python id="p9x3k6"
monitoring_service = MonitoringService(
    cloudwatch_client=cloudwatch_client,
)
```

This is preferable to constructing the AWS client internally inside every service method.

Benefits include:

* Testability
* Replaceability
* Clear dependencies
* Better separation of concerns

---

# 41. Avoid Global Mutable State

Global mutable state should be minimized.

The current remediation idempotency registry is an MVP implementation:

```text id="s4n8q2"
idempotency_registry = IdempotencyRegistry()
```

This is acceptable for the current single-process prototype but is not sufficient for distributed production workers.

The future implementation should use durable shared state.

---

# 42. Package Dependency Boundaries

The project should prevent infrastructure concerns from leaking into every module.

For example:

```text id="x7m2v9"
Detection
  ↓
Pure decision logic
```

should be separated from:

```text id="c8q4n1"
CloudWatch
  ↓
AWS API interaction
```

This allows detection rules to be tested using plain Python data.

---

# 43. Cleanup of Duplicate Code

As the project evolves, duplicated logic should be identified.

Examples of duplication to avoid:

* Repeated AWS client creation
* Repeated configuration loading
* Repeated incident serialization
* Repeated validation logic
* Repeated error formatting

However, duplication should not be removed prematurely if abstraction would make the design harder to understand.

---

# 44. Dependency Upgrade Policy

Before upgrading a major dependency:

```text id="n7x3c5"
Review compatibility
      ↓
Run unit tests
      ↓
Run integration tests
      ↓
Run security checks
      ↓
Review behavior
```

Breaking changes should be documented when they affect architecture or runtime behavior.

---

# 45. Build Reproducibility

A developer or CI system should be able to recreate the project environment from repository configuration.

The intended workflow is:

```bash id="v2k7m4"
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -e ".[dev]"
pytest
```

This should produce a consistent development environment.

---

# 46. Local Development Standard

Windows Git Bash development currently uses:

```bash id="w4p8n2"
source .venv/Scripts/activate
```

Python commands should use:

```bash id="j6m3x9"
python
python -m pip
pytest
```

The project should document equivalent commands for other supported environments when required.

---

# 47. CI/CD Readiness

The repository structure is intended to support future CI/CD.

A CI pipeline should be able to discover:

```text id="q8x4m2"
pyproject.toml
src/
tests/
docs/
infrastructure/
```

without requiring custom path assumptions.

This is one advantage of maintaining a conventional repository structure.

---

# 48. Container Readiness

The project will eventually be containerized.

A future Docker build should be able to install the package using the project metadata.

Conceptually:

```text id="c5n9v1"
Docker Build
    ↓
Install pyproject dependencies
    ↓
Run cloudops_engine
```

The container should not require the developer's local `.venv`.

---

# 49. ECR / ECS Readiness

Future deployment to AWS ECS/ECR should use:

```text id="m7x2q8"
Source
  ↓
Docker Build
  ↓
Image
  ↓
ECR
  ↓
ECS
```

The application package structure should remain independent of the deployment platform.

---

# 50. Security Cleanup

Project structure should support security.

Ensure that the repository excludes:

```text id="z4v8m2"
.env
*.pem
credentials
Terraform state
local virtual environments
build artifacts
```

Secret scanning should eventually be added to CI/CD.

---

# 51. Git Hygiene

Commits should remain focused.

Good example:

```text id="p6m3x8"
docs: define testing strategy
```

Another:

```text id="v7q2n5"
feat: add DynamoDB incident persistence
```

Avoid mixing unrelated changes in one commit.

---

# 52. Branching Strategy

For the current learning/MVP phase, a simple `main` branch workflow is acceptable.

As the project grows:

```text id="x3k8m4"
feature branch
      ↓
Pull Request
      ↓
CI checks
      ↓
Review
      ↓
main
```

can be adopted.

Production deployments should not rely on direct unreviewed pushes.

---

# 53. Cleanup Checklist

The repository cleanup should verify:

```text id="a5v8m2"
[ ] pyproject.toml is dependency source of truth
[ ] Duplicate requirements file removed if unnecessary
[ ] src layout maintained
[ ] Package structure is clear
[ ] Tests separated by level
[ ] AWS clients isolated
[ ] Repository abstraction maintained
[ ] Configuration centralized
[ ] Generated files ignored
[ ] .env ignored
[ ] .env.example available
[ ] Terraform state ignored
[ ] Documentation organized
[ ] ADRs organized
[ ] No unnecessary abstractions
[ ] No obvious duplicate code
[ ] No circular dependencies
[ ] Imports consistently organized
[ ] Naming conventions consistent
[ ] CI/CD ready
[ ] Containerization ready
```

---

# 54. Current Repository Assessment

The project already has a strong foundation:

* `src` layout
* `pyproject.toml`
* Editable installation
* Virtual environment isolation
* Modular application structure
* Repository pattern
* Unit tests
* Integration tests
* Terraform directory
* Documentation structure
* `.gitignore`
* Git/GitHub version control

The primary cleanup item identified is dependency-definition duplication involving the older `requirements.txt`.

---

# 55. Cleanup Priority

The cleanup should be performed in this order:

```text id="r7x2m4"
1. Dependency source of truth
        ↓
2. Remove obsolete files
        ↓
3. Verify package structure
        ↓
4. Verify tests
        ↓
5. Verify imports
        ↓
6. Add development tooling
        ↓
7. Verify security exclusions
        ↓
8. Run full regression suite
        ↓
9. Commit cleanup milestone
```

---

# 56. Regression Requirement

Structural cleanup must not change application behavior.

After cleanup:

```bash id="x5m8q2"
pytest
```

must pass.

The cleanup should be treated as a refactoring milestone rather than a feature milestone.

---

# 57. Industry Alignment

The structure follows common Python engineering practices:

* `pyproject.toml`
* `src` layout
* Separate test directories
* Dependency separation
* Modular packages
* Repository abstraction
* Configuration separation
* Infrastructure separation
* Version-controlled documentation
* Environment isolation

The exact tooling can evolve as the project matures.

---

# 58. Final Principle

Project structure should make the system easier to understand, test, secure, and deploy.

The goal is not to create the largest folder structure possible.

The goal is:

> **Keep every component in the smallest clear boundary that accurately represents its responsibility.**

A clean repository reduces cognitive load and makes future engineering work safer.

---

## Related Documentation

* [Product Requirements](requirements/product-requirements.md)
* [System Architecture](architecture/system-architecture.md)
* [AWS Architecture](architecture/aws-architecture.md)
* [Configuration Strategy](configuration-strategy.md)
* [Logging & Observability Strategy](logging-observability-strategy.md)
* [Error Handling & Reliability Strategy](error-handling-reliability-strategy.md)
* [Security & IAM Strategy](security-iam-strategy.md)
* [Testing Strategy](testing-strategy.md)

## Related Architecture Decisions

* [ADR-001: Repository Pattern](decisions/ADR-001-repository-pattern.md)
* [ADR-002: DynamoDB Persistence](decisions/ADR-002-dynamodb-persistence.md)
* [ADR-003: Human Approval Before Remediation](decisions/ADR-003-human-approval.md)
* [ADR-004: Conditional Write and Idempotency](decisions/ADR-004-conditional-write-idempotency.md)
