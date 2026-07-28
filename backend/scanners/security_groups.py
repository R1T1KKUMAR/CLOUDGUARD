"""Security Group scanner: world-open ingress on sensitive ports."""

from __future__ import annotations

from collections.abc import Iterable

from models import Finding, Service
from scanners.base import BaseScanner

# Ports that should never be open to the whole internet.
SENSITIVE_PORTS = {22: "SSH", 3389: "RDP", 3306: "MySQL", 5432: "PostgreSQL"}
WORLD = "0.0.0.0/0"


class SecurityGroupScanner(BaseScanner):
    name = "security_groups"

    def scan(self) -> Iterable[Finding]:
        ec2 = self.client("ec2")

        paginator = ec2.get_paginator("describe_security_groups")
        for page in paginator.paginate():
            for group in page.get("SecurityGroups", []):
                yield from self._check_group(group)

    def _check_group(self, group: dict) -> Iterable[Finding]:
        group_id = group["GroupId"]
        for rule in group.get("IpPermissions", []):
            open_to_world = any(
                rng.get("CidrIp") == WORLD for rng in rule.get("IpRanges", [])
            )
            if not open_to_world:
                continue

            from_port = rule.get("FromPort")
            to_port = rule.get("ToPort")
            for port, label in SENSITIVE_PORTS.items():
                if from_port is not None and from_port <= port <= (to_port or from_port):
                    yield Finding(
                        service=Service.SECURITY_GROUP,
                        resource_id=group_id,
                        check_id="sg-world-open-port",
                        title=f"Security group '{group_id}' exposes {label} ({port}) to the internet",
                        evidence={
                            "group_id": group_id,
                            "port": port,
                            "protocol": label,
                            "cidr": WORLD,
                        },
                    )
