"""
CloudGuard API.

FastAPI application exposing the scan/finding/approval endpoints consumed by the
React dashboard. Runs locally with `uvicorn app:app --reload` and deploys to
Lambda behind API Gateway via the Mangum adapter (see `handler` at the bottom).
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import remediation
import scanner
from database import FindingsRepository
from models import Finding, RemediationStatus

app = FastAPI(title="CloudGuard API", version="0.1.0")

# The dashboard is a separate origin; tighten this to the real domain in prod.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScanResponse(BaseModel):
    count: int
    findings: list[dict]


class ActionResponse(BaseModel):
    finding_id: str
    status: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/scan", response_model=ScanResponse)
def trigger_scan() -> ScanResponse:
    findings = scanner.run_scan()
    return ScanResponse(count=len(findings), findings=[f.to_item() for f in findings])


@app.get("/findings")
def list_findings() -> list[dict]:
    return FindingsRepository().list_all()


@app.get("/findings/{finding_id}")
def get_finding(finding_id: str) -> dict:
    item = FindingsRepository().get(finding_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    return item


@app.post("/findings/{finding_id}/approve", response_model=ActionResponse)
def approve_finding(finding_id: str) -> ActionResponse:
    """Approve and apply the remediation for a finding."""
    repo = FindingsRepository()
    item = repo.get(finding_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Finding not found")

    repo.update_status(finding_id, RemediationStatus.APPROVED)
    try:
        status = remediation.remediate(_finding_from_item(item))
    except remediation.RemediationError as exc:
        repo.update_status(finding_id, RemediationStatus.FAILED)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    repo.update_status(finding_id, status)
    return ActionResponse(finding_id=finding_id, status=status.value)


@app.post("/findings/{finding_id}/reject", response_model=ActionResponse)
def reject_finding(finding_id: str) -> ActionResponse:
    repo = FindingsRepository()
    if repo.get(finding_id) is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    repo.update_status(finding_id, RemediationStatus.REJECTED)
    return ActionResponse(finding_id=finding_id, status=RemediationStatus.REJECTED.value)


def _finding_from_item(item: dict) -> Finding:
    """Rebuild the minimal Finding remediation needs from a stored item."""
    from models import Service

    return Finding(
        service=Service(item["service"]),
        resource_id=item["resource_id"],
        check_id=item["check_id"],
        title=item.get("title", ""),
        evidence=item.get("evidence", {}),
    )


# --- Lambda entrypoint ------------------------------------------------------
# Mangum wraps the ASGI app so the same code serves API Gateway events.
try:
    from mangum import Mangum

    handler = Mangum(app)
except ImportError:  # mangum not installed in local dev is fine
    handler = None
