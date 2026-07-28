"""
DynamoDB persistence for findings.

Thin data-access layer over the CloudGuardFindings table. The rest of the code
deals in Finding objects and dicts; only this module knows about DynamoDB.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

import config
from models import Finding, RemediationStatus


class FindingsRepository:
    def __init__(self, session: boto3.Session | None = None) -> None:
        session = session or boto3.Session()
        dynamodb = session.resource("dynamodb", region_name=config.AWS_REGION)
        self.table = dynamodb.Table(config.FINDINGS_TABLE)

    def save(self, finding: Finding) -> None:
        """Upsert a finding. The deterministic FindingId makes re-scans idempotent."""
        self.table.put_item(Item=_to_dynamo(finding.to_item()))

    def save_many(self, findings: list[Finding]) -> None:
        with self.table.batch_writer(overwrite_by_pkeys=["FindingId"]) as batch:
            for finding in findings:
                batch.put_item(Item=_to_dynamo(finding.to_item()))

    def get(self, finding_id: str) -> dict | None:
        result = self.table.get_item(Key={"FindingId": finding_id})
        item = result.get("Item")
        return _from_dynamo(item) if item else None

    def list_all(self) -> list[dict]:
        # NOTE: full-table scan is fine at hackathon/demo scale. For production,
        # add a GSI (e.g. by severity or status) and query instead.
        items: list[dict] = []
        kwargs: dict[str, Any] = {}
        while True:
            page = self.table.scan(**kwargs)
            items.extend(page.get("Items", []))
            if "LastEvaluatedKey" not in page:
                break
            kwargs["ExclusiveStartKey"] = page["LastEvaluatedKey"]
        return [_from_dynamo(item) for item in items]

    def update_status(self, finding_id: str, status: RemediationStatus) -> None:
        self.table.update_item(
            Key={"FindingId": finding_id},
            UpdateExpression="SET remediation_status = :s",
            ExpressionAttributeValues={":s": status.value},
        )


def _to_dynamo(item: dict) -> dict:
    """DynamoDB rejects floats; convert them to Decimal."""
    return {k: (Decimal(str(v)) if isinstance(v, float) else v) for k, v in item.items()}


def _from_dynamo(item: dict) -> dict:
    """Convert Decimals back to int/float for JSON serialisation."""
    out: dict = {}
    for key, value in item.items():
        if isinstance(value, Decimal):
            out[key] = int(value) if value % 1 == 0 else float(value)
        else:
            out[key] = value
    return out
