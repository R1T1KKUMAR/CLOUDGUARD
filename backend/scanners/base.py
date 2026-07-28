"""
Base class shared by every service scanner.

A scanner takes a boto3 session, inspects one AWS service, and yields Finding
objects. Keeping a common base means the orchestrator can treat all scanners
uniformly and each concrete scanner only implements `scan()`.
"""

from __future__ import annotations

import abc
from collections.abc import Iterable

import boto3

from models import Finding


class BaseScanner(abc.ABC):
    """Abstract base for all CloudGuard scanners."""

    #: Human-friendly name, used in logs and progress output.
    name: str = "base"

    def __init__(self, session: boto3.Session, region: str) -> None:
        self.session = session
        self.region = region

    def client(self, service_name: str):
        """Convenience boto3 client factory bound to this scanner's region."""
        return self.session.client(service_name, region_name=self.region)

    @abc.abstractmethod
    def scan(self) -> Iterable[Finding]:
        """Inspect the service and yield findings. Must be side-effect free."""
        raise NotImplementedError
