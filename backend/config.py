"""
Central configuration for CloudGuard.

All runtime settings are read from environment variables so the same code runs
locally (via a .env file) and inside Lambda (via configured environment
variables). Nothing here performs AWS calls at import time.
"""

import os

from dotenv import load_dotenv

# Load a local .env when present. In Lambda there is no .env file and this is a
# harmless no-op, so real environment variables always win.
load_dotenv()


def _get(name: str, default: str | None = None, *, required: bool = False) -> str | None:
    value = os.environ.get(name, default)
    if required and not value:
        raise RuntimeError(f"Required environment variable {name!r} is not set")
    return value


# --- AWS / region -----------------------------------------------------------
# Bedrock model access was requested in ap-south-1 (see README / Step 1).
AWS_REGION = _get("AWS_REGION", "ap-south-1")

# --- DynamoDB ---------------------------------------------------------------
FINDINGS_TABLE = _get("CLOUDGUARD_FINDINGS_TABLE", "CloudGuardFindings")

# --- SNS --------------------------------------------------------------------
# ARN of the CloudGuardAlerts topic. Optional locally; required to send alerts.
ALERTS_TOPIC_ARN = _get("CLOUDGUARD_ALERTS_TOPIC_ARN")

# --- Bedrock ----------------------------------------------------------------
# Model id to invoke for AI analysis. Override per-account depending on which
# model access was granted (e.g. an Amazon Nova or Anthropic Claude model id).
BEDROCK_MODEL_ID = _get("CLOUDGUARD_BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")

# --- Behaviour flags --------------------------------------------------------
# Only send SNS alerts for findings at or above this severity score.
ALERT_SEVERITY_THRESHOLD = int(_get("CLOUDGUARD_ALERT_THRESHOLD", "80"))

# Remediation is opt-in and only ever runs after explicit approval.
REMEDIATION_ENABLED = _get("CLOUDGUARD_REMEDIATION_ENABLED", "false").lower() == "true"
