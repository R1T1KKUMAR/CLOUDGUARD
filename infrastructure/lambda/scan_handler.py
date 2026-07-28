"""
Lambda entrypoint for the scheduled/triggered security scan.

Deploy this as the `Scan Lambda` in the architecture. It simply invokes the
orchestrator in `backend/scanner.py`. Package the `backend/` directory alongside
this file (or as a Lambda layer) so the imports resolve.
"""

from __future__ import annotations

import json
import logging

import scanner  # from backend/

logging.getLogger().setLevel(logging.INFO)


def handler(event, context):  # noqa: ANN001 - Lambda signature
    findings = scanner.run_scan()
    summary = {
        "scanned": len(findings),
        "high_severity": sum(1 for f in findings if (f.severity or 0) >= 80),
    }
    logging.info("Scan complete: %s", summary)
    return {"statusCode": 200, "body": json.dumps(summary)}
