# CloudGuard - Agentic Security & Compliance Auditor

AI-powered security auditor that continuously scans an AWS account, detects security and compliance issues, reasons about them with Amazon Bedrock, assigns severity scores, and optionally remediates them after user approval.

## Architecture

```text
User Dashboard  ──HTTPS──▶  API Gateway  ──▶  Lambda (API)  ──┬──▶  Scan Lambda ──▶ boto3 Scanner ──▶ IAM / S3 / EC2 / Lambda / SG / Config
                                                              └──▶  Bedrock AI
                                                                     │
Findings (DynamoDB) ──▶ Severity Scoring ──▶ Suggested Remediation ──▶ SSM Automation (optional)
        │
        └──▶ SNS Alerts
```

## Layout

```text
backend/                 Python scan engine + FastAPI API
  app.py                 API endpoints (scan, findings, approve/reject)
  scanner.py             Orchestrator: scan -> score -> AI -> persist -> alert
  models.py              Shared Finding data model
  severity.py            Deterministic severity scoring baseline
  ai.py                  Bedrock (Converse API) enrichment
  remediation.py         Approved, per-check remediation handlers
  database.py            DynamoDB access layer
  notifications.py       SNS alerts
  config.py              Env-driven configuration
  scanners/              One module per AWS service
frontend/                React dashboard (to be built)
infrastructure/
  cloudformation/        Deployable IaC (core resources)
  lambda/                Lambda entrypoints
  policies/              Least-privilege IAM policy documents
docs/  screenshots/      Documentation & demo assets
```

## Setup

### 1. Deploy AWS resources (no CLI required)

Deploy `infrastructure/cloudformation/cloudguard-core.yaml` from the
**CloudFormation console** (Create stack → upload template). It provisions:

- `CloudGuardFindings` DynamoDB table (on-demand, encrypted, PITR)
- `CloudGuardAlerts` SNS topic + your email subscription (confirm via email)
- `CloudGuardLambdaRole` execution role (ReadOnlyAccess for scanning + scoped writes)

Enable **AWS Config** and request **Bedrock model access** (ap-south-1) from
their respective consoles as described in the project brief.

### 2. Backend (local dev)

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env      # fill in the CloudFormation outputs
uvicorn app:app --reload
```

Trigger a scan: `curl -X POST localhost:8000/scan`

## Status

Phase 1 scaffold in place: scanners for IAM, S3, EC2, Security Groups, Lambda,
and Config with a full scan→score→AI→persist→alert→remediate pipeline. Scanner
checks and remediation handlers are being fleshed out; the React dashboard is
next.
# CLOUDGUARD
# CLOUDGUARD
