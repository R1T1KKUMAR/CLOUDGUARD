"""EC2 scanner: public instances, unencrypted volumes, and IMDSv1."""

from __future__ import annotations

from collections.abc import Iterable

from models import Finding, Service
from scanners.base import BaseScanner


class EC2Scanner(BaseScanner):
    name = "ec2"

    def scan(self) -> Iterable[Finding]:
        ec2 = self.client("ec2")

        paginator = ec2.get_paginator("describe_instances")
        for page in paginator.paginate():
            for reservation in page.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    yield from self._check_instance(instance)

    def _check_instance(self, instance: dict) -> Iterable[Finding]:
        instance_id = instance["InstanceId"]

        # Public IP exposure.
        if instance.get("PublicIpAddress"):
            yield Finding(
                service=Service.EC2,
                resource_id=instance_id,
                check_id="ec2-public-ip",
                title=f"EC2 instance '{instance_id}' has a public IP",
                evidence={
                    "instance_id": instance_id,
                    "public_ip": instance["PublicIpAddress"],
                },
            )

        # IMDSv1 still allowed (token not required) => SSRF credential theft risk.
        metadata = instance.get("MetadataOptions", {})
        if metadata.get("HttpTokens") == "optional":
            yield Finding(
                service=Service.EC2,
                resource_id=instance_id,
                check_id="ec2-imdsv1-enabled",
                title=f"EC2 instance '{instance_id}' allows IMDSv1",
                evidence={"instance_id": instance_id, "http_tokens": "optional"},
            )

        # TODO: cross-reference BlockDeviceMappings -> describe_volumes to flag
        # unencrypted EBS volumes.
