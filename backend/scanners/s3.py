"""S3 scanner: public access and encryption at rest."""

from __future__ import annotations

from collections.abc import Iterable

from botocore.exceptions import ClientError

from models import Finding, Service
from scanners.base import BaseScanner


class S3Scanner(BaseScanner):
    name = "s3"

    def scan(self) -> Iterable[Finding]:
        s3 = self.client("s3")

        buckets = s3.list_buckets().get("Buckets", [])
        for bucket in buckets:
            name = bucket["Name"]

            if self._is_public(s3, name):
                yield Finding(
                    service=Service.S3,
                    resource_id=name,
                    check_id="s3-public-access",
                    title=f"S3 bucket '{name}' allows public access",
                    evidence={"bucket": name, "public": True},
                )

            if not self._has_encryption(s3, name):
                yield Finding(
                    service=Service.S3,
                    resource_id=name,
                    check_id="s3-no-encryption",
                    title=f"S3 bucket '{name}' has no default encryption",
                    evidence={"bucket": name, "encryption": False},
                )

    def _is_public(self, s3, bucket: str) -> bool:
        """True if Block Public Access is not fully enabled."""
        try:
            cfg = s3.get_public_access_block(Bucket=bucket)["PublicAccessBlockConfiguration"]
        except ClientError as exc:
            # No config at all means nothing is blocking public access.
            if exc.response["Error"]["Code"] == "NoSuchPublicAccessBlockConfiguration":
                return True
            raise
        return not all(cfg.get(flag, False) for flag in (
            "BlockPublicAcls",
            "IgnorePublicAcls",
            "BlockPublicPolicy",
            "RestrictPublicBuckets",
        ))

    def _has_encryption(self, s3, bucket: str) -> bool:
        try:
            s3.get_bucket_encryption(Bucket=bucket)
            return True
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ServerSideEncryptionConfigurationNotFoundError":
                return False
            raise
