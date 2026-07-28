"""
SNS notifications.

Publishes a short alert to the CloudGuardAlerts topic for high-severity
findings. No-op (with a warning) when no topic ARN is configured, so local runs
don't fail.
"""

from __future__ import annotations

import logging

import boto3

import config
from models import Finding
from severity import label_for

logger = logging.getLogger(__name__)


def send_alert(finding: Finding, *, session: boto3.Session | None = None) -> None:
    if not config.ALERTS_TOPIC_ARN:
        logger.warning("No SNS topic configured; skipping alert for %s", finding.finding_id)
        return

    session = session or boto3.Session()
    sns = session.client("sns", region_name=config.AWS_REGION)

    severity_label = label_for(finding.severity or 0)
    sns.publish(
        TopicArn=config.ALERTS_TOPIC_ARN,
        Subject=f"CloudGuard Alert: {severity_label} finding",
        Message=(
            f"{finding.title}\n\n"
            f"Service: {finding.service.value}\n"
            f"Resource: {finding.resource_id}\n"
            f"Severity: {finding.severity} ({severity_label})\n"
            f"Risk: {finding.ai_risk or 'n/a'}\n"
            f"Recommendation: {finding.ai_recommendation or 'n/a'}\n"
        ),
    )
