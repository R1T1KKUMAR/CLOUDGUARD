"""
Shared data model for CloudGuard findings.

A Finding is the single unit of information that flows through the whole system:
scanners produce them, the AI layer enriches them, the database persists them,
the dashboard renders them, and remediation acts on them. Keeping one shape here
means every module speaks the same language.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum


class Service(str, Enum):
    IAM = "IAM"
    S3 = "S3"
    EC2 = "EC2"
    LAMBDA = "Lambda"
    SECURITY_GROUP = "SecurityGroup"
    CONFIG = "Config"


class RemediationStatus(str, Enum):
    OPEN = "OPEN"                 # detected, awaiting review
    APPROVED = "APPROVED"         # user approved a fix, not yet applied
    REJECTED = "REJECTED"         # user declined the fix
    REMEDIATED = "REMEDIATED"     # fix applied successfully
    FAILED = "FAILED"             # remediation attempted but failed


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Finding:
    """One security or compliance issue about one AWS resource."""

    service: Service
    resource_id: str
    # Stable machine name for the rule that fired, e.g. "s3-public-access".
    check_id: str
    title: str
    # Raw configuration facts the scanner observed. Fed to the AI layer verbatim.
    evidence: dict = field(default_factory=dict)

    # --- populated later in the pipeline -----------------------------------
    severity: int | None = None          # 0-100, set by severity scoring / AI
    ai_risk: str | None = None           # AI explanation of the risk
    ai_recommendation: str | None = None  # AI recommended fix
    remediation_status: RemediationStatus = RemediationStatus.OPEN
    scanned_at: str = field(default_factory=_utc_now_iso)

    # Deterministic id so re-scanning the same issue updates rather than
    # duplicates the record.
    finding_id: str = field(default="")

    def __post_init__(self) -> None:
        if not self.finding_id:
            self.finding_id = self._build_id()

    def _build_id(self) -> str:
        raw = f"{self.service.value}:{self.check_id}:{self.resource_id}"
        digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return f"{self.service.value.lower()}-{digest}"

    def to_item(self) -> dict:
        """Serialise to a plain dict suitable for DynamoDB / JSON."""
        item = asdict(self)
        item["service"] = self.service.value
        item["remediation_status"] = self.remediation_status.value
        item["FindingId"] = self.finding_id  # DynamoDB partition key
        return item
