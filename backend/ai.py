"""
AI analysis via Amazon Bedrock.

Given a Finding, we ask a Bedrock model to explain the risk, judge severity, and
recommend a fix. We use the Bedrock **Converse** API, which presents a single
uniform request/response shape across model families (Amazon Nova, Anthropic
Claude, etc.), so switching models is a config change (see BEDROCK_MODEL_ID) and
not a code change.

The AI is an enrichment step, never a hard dependency: if Bedrock is
unavailable, callers fall back to the deterministic severity scoring.
"""

from __future__ import annotations

import json
import logging

import boto3

import config
from models import Finding

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a senior AWS cloud security auditor. Given a single security "
    "finding, respond with strict JSON only, no prose, matching exactly: "
    '{"risk": string, "severity": integer 0-100, "recommendation": string}. '
    "Base severity on real-world exploitability and blast radius."
)


def analyze(finding: Finding, *, session: boto3.Session | None = None) -> Finding:
    """Enrich `finding` in place with AI risk, recommendation, and severity.

    Returns the same finding. On any failure the finding is returned unchanged
    (severity from `severity.py` remains authoritative) so the pipeline never
    breaks because of the model.
    """
    session = session or boto3.Session()
    client = session.client("bedrock-runtime", region_name=config.AWS_REGION)

    user_prompt = _build_prompt(finding)
    try:
        response = client.converse(
            modelId=config.BEDROCK_MODEL_ID,
            system=[{"text": _SYSTEM_PROMPT}],
            messages=[{"role": "user", "content": [{"text": user_prompt}]}],
            inferenceConfig={"maxTokens": 512, "temperature": 0.0},
        )
        text = response["output"]["message"]["content"][0]["text"]
        parsed = _parse(text)
    except Exception:  # noqa: BLE001 - AI must never crash the scan
        logger.exception("Bedrock analysis failed for %s", finding.finding_id)
        return finding

    finding.ai_risk = parsed.get("risk")
    finding.ai_recommendation = parsed.get("recommendation")
    if isinstance(parsed.get("severity"), int):
        finding.severity = max(0, min(100, parsed["severity"]))
    return finding


def _build_prompt(finding: Finding) -> str:
    return (
        f"Service: {finding.service.value}\n"
        f"Check: {finding.check_id}\n"
        f"Resource: {finding.resource_id}\n"
        f"Title: {finding.title}\n"
        f"Observed configuration: {json.dumps(finding.evidence)}\n\n"
        "Explain the risk, assign a severity score, and recommend a fix."
    )


def _parse(text: str) -> dict:
    """Extract the JSON object from the model response, tolerating stray text."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object in model response: {text!r}")
    return json.loads(text[start : end + 1])
