# CloudOps Autopilot

> **Risk-aware cloud incident detection, diagnosis, remediation and verification platform.**

CloudOps Autopilot is an AWS-focused cloud operations platform designed to help engineering teams detect incidents, analyze evidence, assess remediation risk, obtain human approval, execute controlled remediation, and verify recovery.

The project is being developed as a combination of:

* Cloud engineering project
* DevOps/SRE portfolio project
* Research project
* Future cloud operations product

---

## 1. Vision

Cloud incidents often require engineers to manually detect problems, investigate evidence, decide what action to take, execute remediation, and verify recovery.

CloudOps Autopilot aims to make this workflow more systematic and controlled:

```text
Detect
  ↓
Diagnose
  ↓
Assess Risk
  ↓
Recommend
  ↓
Approve
  ↓
Remediate
  ↓
Verify
  ↓
Record
```

The platform is designed around a simple principle:

> **Automation should be explainable, controlled, and verifiable.**

---

## 2. Problem

Modern cloud environments continuously generate operational signals such as:

* Metrics
* Logs
* Events
* Health checks
* Deployment information
* Infrastructure state
* Application errors

During an incident, engineers may need to manually correlate these signals and determine the correct response.

This creates several challenges:

* Slow incident detection
* Manual diagnosis
* Repetitive operational work
* Inconsistent remediation decisions
* Risk of incorrect actions
* Limited auditability
* Difficulty measuring incident-response effectiveness

CloudOps Autopilot is designed to address these challenges through controlled automation.

---

## 3. Solution

CloudOps Autopilot provides a structured incident-response pipeline.

```text
AWS Environment
      ↓
Operational Signals
      ↓
CloudWatch
      ↓
Incident Detection
      ↓
Evidence Collection
      ↓
Diagnosis
      ↓
Risk Assessment
      ↓
Remediation Recommendation
      ↓
Safety Guardrails
      ↓
Human Approval
      ↓
Controlled Remediation
      ↓
Verification
      ↓
DynamoDB Incident Record
```

The system separates detection, diagnosis, decision-making, remediation, and verification instead of allowing an incident detector to directly modify infrastructure.

---

## 4. Core Design Principles

CloudOps Autopilot follows these engineering principles:

* Security by design
* Least privilege
* Fail closed
* Human-in-the-loop
* Evidence-based decisions
* Idempotent operations
* Separation of concerns
* Testability
* Observability
* Auditability
* Infrastructure as Code
* Automation with verification
* Explicit architecture decisions
* Incremental delivery
* Measurable outcomes

---

## 5. Current Capabilities

The current implementation includes:

### Incident Detection

* AWS CloudWatch integration
* EC2 CPU monitoring
* Persistent threshold detection
* Consecutive-breach detection
* Configurable detection thresholds

### Evidence

* Structured evidence model
* Signal values
* Observation timestamps
* Evidence descriptions
* Evidence-aware incident detection

### Diagnosis

* Probable-cause analysis
* Confidence scoring
* Supporting evidence
* Human-readable diagnosis explanation

### Risk & Safety

* Risk assessment
* Remediation recommendations
* Action allowlisting
* Safety guardrails
* Fail-closed behavior

### Human Approval

Remediation actions are subject to an explicit approval step before execution.

### Remediation Controls

* Structured remediation executor
* Idempotency protection
* Duplicate-action prevention
* Remediation result tracking

The current remediation implementation is intentionally controlled and does not provide unrestricted AWS mutation.

### Verification

The system verifies whether the incident condition has recovered after remediation.

### Incident Lifecycle

The platform currently supports:

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

Verification failure can return the incident to investigation.

### Persistence

Incident state is persisted using Amazon DynamoDB.

The repository layer supports:

* Create incident
* Retrieve incident
* Update incident
* Duplicate protection
* Lifecycle state persistence

---

## 6. Architecture

### Current Logical Architecture

```text
┌───────────────────────┐
│     AWS Resources     │
│       / Services      │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│     CloudWatch        │
│ Metrics / Signals     │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ Incident Detection    │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ Evidence Collection   │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ Diagnosis Engine      │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ Risk Assessment       │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ Recommendation        │
│ + Safety Guardrails   │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ Human Approval        │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ Remediation Executor  │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ Verification Engine   │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ DynamoDB Incident DB  │
└───────────────────────┘
```

The detailed architecture is maintained under:

```text
docs/architecture/
```

---

## 7. Incident Lifecycle

CloudOps Autopilot treats incident handling as a controlled state machine.

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

If verification fails:

```text
VERIFYING
    ↓
INVESTIGATING
```

Invalid state transitions are rejected by the lifecycle model.

---

## 8. Safety Model

Safety is a first-class product requirement.

The platform follows:

```text
Detect
  ↓
Collect Evidence
  ↓
Diagnose
  ↓
Assess Risk
  ↓
Validate Action
  ↓
Request Approval
  ↓
Execute
  ↓
Verify
```

An automated detection event must not directly trigger unrestricted infrastructure modification.

The current system uses an allowlist for remediation actions and blocks unsupported actions.

---

## 9. Technology Stack

### Cloud

* Amazon Web Services (AWS)
* Amazon CloudWatch
* Amazon DynamoDB
* Amazon EC2

### Application

* Python
* boto3
* python-dotenv

### Development

* Git
* GitHub
* VS Code
* Python virtual environment

### Testing

* pytest
* Unit testing
* Integration testing

### Planned Infrastructure

* Terraform
* AWS EventBridge
* AWS Lambda
* Amazon SNS
* Additional AWS services as the architecture evolves

### Planned Platform

* Docker
* Amazon ECR
* Amazon ECS
* Kubernetes / Amazon EKS
* Prometheus
* Grafana

---

## 10. Repository Structure

```text
cloudops-autopilot/
│
├── README.md
├── pyproject.toml
├── .gitignore
│
├── docs/
│   ├── requirements/
│   │   └── product-requirements.md
│   │
│   ├── architecture/
│   │
│   ├── decisions/
│   │
│   └── research/
│
├── src/
│   └── cloudops_engine/
│       ├── aws/
│       ├── detection/
│       ├── diagnosis/
│       ├── models/
│       ├── remediation/
│       ├── repositories/
│       ├── risk/
│       ├── services/
│       ├── verification/
│       └── main.py
│
├── tests/
│   ├── unit/
│   └── integration/
│
└── infrastructure/
    └── terraform/
```

The structure follows separation of responsibilities so that individual components can be developed and tested independently.

---

## 11. Local Development

### Prerequisites

The current development environment uses:

* Windows 11
* Git Bash
* VS Code
* Python 3.14+
* AWS CLI
* An AWS development account

AWS credentials must be configured securely outside the source repository.

---

### Clone Repository

```bash
git clone git@github.com:inarenpithani/cloudops-autopilot.git
cd cloudops-autopilot
```

---

### Create Virtual Environment

```bash
python -m venv .venv
```

Activate:

```bash
source .venv/Scripts/activate
```

Verify:

```bash
which python
python --version
```

---

### Install Project Dependencies

```bash
python -m pip install -e ".[dev]"
```

---

### Verify AWS Identity

```bash
aws sts get-caller-identity
```

The development environment should use a dedicated IAM identity with only the permissions required for the current implementation.

---

## 12. Running the Application

Activate the virtual environment:

```bash
source .venv/Scripts/activate
```

Run:

```bash
python -m cloudops_engine.main
```

The current application checks the configured EC2 instance and performs the implemented incident-detection workflow.

If no incident condition is detected, the application exits without attempting remediation.

---

## 13. Testing

Run the complete test suite:

```bash
pytest
```

The project currently includes:

* Unit tests
* Repository tests
* DynamoDB integration tests
* Detection tests
* Diagnosis tests
* Remediation tests
* Lifecycle tests
* Verification tests

Tests should remain deterministic where possible, while integration tests explicitly validate AWS behavior.

---

## 14. AWS Resources

The current development environment includes:

### EC2

A dedicated development EC2 instance is used for CloudWatch monitoring experiments.

### CloudWatch

Used as the initial operational telemetry source.

### DynamoDB

Incident persistence table:

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

### IAM

The project uses dedicated IAM identities and follows least-privilege principles for implemented functionality.

AWS credentials, private keys, and secrets must never be committed to Git.

---

## 15. Security

CloudOps Autopilot is designed with security and operational safety as core requirements.

Current principles include:

* Dedicated AWS development identity
* Least-privilege IAM
* No root credentials for application development
* Read-only AWS access where mutation is not required
* Restricted DynamoDB access
* Remediation action allowlisting
* Human approval
* Idempotency protection
* Fail-closed safety behavior

Future security work includes:

* Formal threat modeling
* Expanded IAM separation
* Encryption strategy
* Audit trail
* Security testing
* Secret-management strategy
* Production environment isolation

---

## 16. Research

CloudOps Autopilot is also being developed as a research project.

### Research Question

> Can a risk-aware cloud incident remediation framework safely automate selected remediation tasks while reducing recovery time and unnecessary human intervention?

### Research Areas

The project will evaluate:

* Incident detection
* Evidence-based diagnosis
* Risk-aware remediation
* Human intervention
* Verification
* Automation safety

### Evaluation Metrics

Planned metrics include:

* Detection time
* Diagnosis accuracy
* Mean Time To Recovery (MTTR)
* Remediation success rate
* False-positive rate
* Unsafe-action rate
* Human intervention rate
* Verification accuracy

Detailed research documentation will be maintained under:

```text
docs/research/
```

---

## 17. AI Roadmap

AI is intentionally **not part of the current core incident engine**.

The initial system establishes deterministic foundations for:

* Detection
* Evidence
* Diagnosis
* Risk
* Policy
* Approval
* Remediation
* Verification

AI-assisted Root Cause Analysis is planned for a later stage.

Future architecture:

```text
Metrics
Logs
Events
Deployments
Configuration
     │
     ▼
AI-Assisted Analysis
     │
     ▼
Probable Causes
     │
     ▼
Risk / Policy Engine
     │
     ▼
Approval
     │
     ▼
Remediation
     │
     ▼
Verification
```

The AI component will not be treated as an unrestricted operational authority.

---

## 18. Roadmap

### Phase 1 — Foundation

* [x] Product requirements
* [x] Core project structure
* [x] Git/GitHub
* [x] Python environment
* [x] AWS development environment

### Phase 2 — Core Incident Engine

* [x] CloudWatch monitoring
* [x] High CPU detection
* [x] Evidence model
* [x] Diagnosis
* [x] Risk assessment
* [x] Recommendation
* [x] Safety guardrails
* [x] Human approval
* [x] Remediation framework
* [x] Verification
* [x] Incident lifecycle
* [x] DynamoDB persistence

### Phase 3 — Production Engineering

* [ ] Professional architecture documentation
* [ ] Architecture Decision Records
* [ ] Structured logging
* [ ] Configuration management
* [ ] Error handling and retries
* [ ] Advanced observability
* [ ] Security hardening
* [ ] Expanded testing strategy
* [ ] Code quality tooling

### Phase 4 — Infrastructure Automation

* [ ] Terraform
* [ ] EventBridge
* [ ] Lambda
* [ ] SNS
* [ ] Infrastructure deployment automation
* [ ] Environment separation

### Phase 5 — CI/CD

* [ ] GitHub Actions
* [ ] Automated tests
* [ ] Linting
* [ ] Type checking
* [ ] Security checks
* [ ] Deployment pipeline

### Phase 6 — Advanced Incident Automation

* [ ] Application 5xx detection
* [ ] Unhealthy service detection
* [ ] Multi-signal correlation
* [ ] Deployment correlation
* [ ] Advanced diagnosis
* [ ] Real controlled remediation

### Phase 7 — AI-Assisted Operations

* [ ] AI-assisted RCA
* [ ] Explainable AI recommendations
* [ ] Confidence scoring
* [ ] Historical incident context
* [ ] Policy-controlled AI actions

### Phase 8 — Productization

* [ ] Multi-account AWS support
* [ ] Tenant isolation
* [ ] SaaS architecture
* [ ] Operational dashboard
* [ ] Product analytics
* [ ] Cost model
* [ ] Pricing model
* [ ] Production security architecture

---

## 19. Project Maturity Model

The project is intentionally evolving through multiple maturity levels:

```text
Prototype
   ↓
Engineering MVP
   ↓
Research Platform
   ↓
Production-Ready System
   ↓
Cloud Operations Product
```

Each stage introduces additional requirements for:

* Security
* Reliability
* Scalability
* Observability
* Testing
* Governance
* Cost management

The project should not claim production readiness until the corresponding engineering controls have been implemented and validated.

---

## 20. Documentation

Detailed project documentation is maintained under:

```text
docs/
```

Planned documentation includes:

```text
docs/
├── requirements/
│   └── product-requirements.md
│
├── architecture/
│   ├── system-architecture.md
│   ├── aws-architecture.md
│   └── incident-lifecycle.md
│
├── decisions/
│   ├── ADR-001-repository-pattern.md
│   ├── ADR-002-dynamodb-persistence.md
│   ├── ADR-003-human-approval.md
│   └── ADR-004-idempotency.md
│
└── research/
    ├── research-problem.md
    ├── methodology.md
    └── evaluation-metrics.md
```

These documents will evolve as the system architecture matures.

---

## 21. Engineering Quality Standard

A feature is not considered complete only because the code executes successfully.

CloudOps Autopilot evaluates major features across:

```text
Works
  ↓
Safe
  ↓
Testable
  ↓
Maintainable
  ↓
Observable
  ↓
Auditable
  ↓
Scalable
  ↓
Explainable
  ↓
Productizable
```

This standard is used to guide future implementation decisions.

---

## 22. Current Project Status

**Status:** Active development

**Current milestone:** Core incident automation foundation

The current system has established the foundational incident lifecycle from detection through persistence and verification.

The next development work focuses on strengthening engineering documentation and production-quality foundations before expanding into event-driven automation and real remediation.

---

## 23. License

License strategy will be defined before public product distribution.

---

## 24. Disclaimer

CloudOps Autopilot is an engineering and research project.

Cloud infrastructure automation can affect availability, security, and cost. Production deployment should only be performed after appropriate security, reliability, testing, approval, and operational controls have been established.
