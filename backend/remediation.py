"""
Remediation.

Remediation is strictly opt-in and only runs after a user has approved a
specific finding in the dashboard. Each remediation is keyed by the finding's
`check_id` so we only ever apply a fix we have explicitly written and reviewed.
Unknown check ids are refused rather than guessed at.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

import boto3

import config
from models import Finding, RemediationStatus

logger = logging.getLogger(__name__)


class RemediationError(RuntimeError):
    pass


def remediate(finding: Finding, *, session: boto3.Session | None = None) -> RemediationStatus:
    """Apply the fix registered for this finding's check_id.

    Returns the resulting RemediationStatus. Raises if remediation is disabled
    globally or no handler exists for the check.
    """
    if not config.REMEDIATION_ENABLED:
        raise RemediationError("Remediation is disabled (set CLOUDGUARD_REMEDIATION_ENABLED=true)")

    handler = _HANDLERS.get(finding.check_id)
    if handler is None:
        raise RemediationError(f"No remediation handler for check '{finding.check_id}'")

    session = session or boto3.Session()
    try:
        handler(finding, session)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Remediation failed for %s", finding.finding_id)
        raise RemediationError(str(exc)) from exc

    return RemediationStatus.REMEDIATED


# --- Handlers ---------------------------------------------------------------
# Each handler performs exactly one narrowly-scoped fix via boto3.

def _fix_s3_public_access(finding: Finding, session: boto3.Session) -> None:
    s3 = session.client("s3", region_name=config.AWS_REGION)
    s3.put_public_access_block(
        Bucket=finding.resource_id,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        },
    )


def _fix_s3_encryption(finding: Finding, session: boto3.Session) -> None:
    s3 = session.client("s3", region_name=config.AWS_REGION)
    s3.put_bucket_encryption(
        Bucket=finding.resource_id,
        ServerSideEncryptionConfiguration={
            "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
        },
    )


Handler = Callable[[Finding, boto3.Session], None]

_HANDLERS: dict[str, Handler] = {
    "s3-public-access": _fix_s3_public_access,
    "s3-no-encryption": _fix_s3_encryption,
    # TODO: sg-world-open-port -> revoke_security_group_ingress
    # TODO: ec2-imdsv1-enabled -> modify_instance_metadata_options (HttpTokens=required)
}
