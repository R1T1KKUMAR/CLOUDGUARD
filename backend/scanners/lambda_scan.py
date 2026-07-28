"""Lambda scanner: public function URLs and unencrypted environment secrets."""

from __future__ import annotations

from collections.abc import Iterable

from botocore.exceptions import ClientError

from models import Finding, Service
from scanners.base import BaseScanner


class LambdaScanner(BaseScanner):
    name = "lambda"

    def scan(self) -> Iterable[Finding]:
        lam = self.client("lambda")

        paginator = lam.get_paginator("list_functions")
        for page in paginator.paginate():
            for fn in page.get("Functions", []):
                yield from self._check_function(lam, fn)

    def _check_function(self, lam, fn: dict) -> Iterable[Finding]:
        name = fn["FunctionName"]

        # Public function URL with no auth (AuthType == NONE).
        try:
            url_cfg = lam.get_function_url_config(FunctionName=name)
            if url_cfg.get("AuthType") == "NONE":
                yield Finding(
                    service=Service.LAMBDA,
                    resource_id=name,
                    check_id="lambda-public-url",
                    title=f"Lambda '{name}' has an unauthenticated function URL",
                    evidence={"function": name, "auth_type": "NONE"},
                )
        except ClientError as exc:
            if exc.response["Error"]["Code"] != "ResourceNotFoundException":
                raise  # no URL configured is fine

        # TODO: flag plaintext-looking secrets in Environment.Variables and
        # functions without a KMS key on environment encryption.
