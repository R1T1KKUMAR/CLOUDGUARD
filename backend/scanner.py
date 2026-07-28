"""
Scan orchestrator.

Ties the pipeline together: run every registered scanner, score each finding,
enrich it with AI analysis, persist it, and fire alerts for high-severity
findings. This is the entry point the Scan Lambda calls.
"""

from __future__ import annotations

import logging

import boto3

import ai
import config
import severity
from database import FindingsRepository
from models import Finding
from notifications import send_alert
from scanners import ALL_SCANNERS

logger = logging.getLogger(__name__)


def run_scan(
    *,
    session: boto3.Session | None = None,
    use_ai: bool = True,
    persist: bool = True,
) -> list[Finding]:
    """Run all scanners and return the enriched findings.

    Parameters are keyword-only so call sites stay readable. `use_ai` and
    `persist` can be turned off for fast local/dry-run testing.
    """
    session = session or boto3.Session()
    repo = FindingsRepository(session) if persist else None

    findings: list[Finding] = []
    for scanner_cls in ALL_SCANNERS:
        scanner = scanner_cls(session, config.AWS_REGION)
        try:
            produced = list(scanner.scan())
        except Exception:  # noqa: BLE001 - one failing scanner must not abort the rest
            logger.exception("Scanner %s failed", scanner.name)
            continue
        logger.info("Scanner %s produced %d findings", scanner.name, len(produced))
        findings.extend(produced)

    for finding in findings:
        severity.score_finding(finding)
        if use_ai:
            ai.analyze(finding, session=session)

    if repo:
        repo.save_many(findings)

    _alert_high_severity(findings, session)
    return findings


def _alert_high_severity(findings: list[Finding], session: boto3.Session) -> None:
    for finding in findings:
        if (finding.severity or 0) >= config.ALERT_SEVERITY_THRESHOLD:
            send_alert(finding, session=session)
