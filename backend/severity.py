"""
Severity scoring.

Every finding gets a 0-100 score and a categorical label. The AI layer may
override the numeric score with its own judgement, but this module guarantees a
deterministic baseline so the system still works (and stays testable) without
Bedrock.
"""

from __future__ import annotations

from models import Finding

# Baseline score per check id. Tuned so the bands line up with the brief:
#   Critical >= 90, High 70-89, Medium 40-69, Low < 40.
BASELINE_SCORES: dict[str, int] = {
    "s3-public-access": 95,
    "sg-world-open-port": 90,
    "lambda-public-url": 85,
    "iam-user-no-mfa": 80,
    "ec2-imdsv1-enabled": 70,
    "s3-no-encryption": 65,
    "ec2-public-ip": 55,
}

DEFAULT_SCORE = 50


def label_for(score: int) -> str:
    if score >= 90:
        return "Critical"
    if score >= 70:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def score_finding(finding: Finding) -> Finding:
    """Set `finding.severity` in place from the baseline table and return it.

    Config-sourced findings inherit a medium-high default because AWS Config
    already decided they are non-compliant.
    """
    if finding.check_id.startswith("config-"):
        finding.severity = 75
    else:
        finding.severity = BASELINE_SCORES.get(finding.check_id, DEFAULT_SCORE)
    return finding
