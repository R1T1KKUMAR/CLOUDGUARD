"""IAM scanner: users, credentials, and overly permissive policies."""

from __future__ import annotations

from collections.abc import Iterable

from models import Finding, Service
from scanners.base import BaseScanner


class IAMScanner(BaseScanner):
    name = "iam"

    def scan(self) -> Iterable[Finding]:
        iam = self.client("iam")

        # --- Users without MFA / with stale access keys --------------------
        # TODO: paginate list_users, then for each user check:
        #   - MFA devices (list_mfa_devices) -> flag console users without MFA
        #   - access key age (list_access_keys) -> flag keys older than N days
        #   - attached admin policies (list_attached_user_policies)
        paginator = iam.get_paginator("list_users")
        for page in paginator.paginate():
            for user in page.get("Users", []):
                username = user["UserName"]

                mfa = iam.list_mfa_devices(UserName=username).get("MFADevices", [])
                if not mfa:
                    yield Finding(
                        service=Service.IAM,
                        resource_id=username,
                        check_id="iam-user-no-mfa",
                        title=f"IAM user '{username}' has no MFA device",
                        evidence={"user": username, "mfa_devices": 0},
                    )

        # --- Policies allowing "*:*" ---------------------------------------
        # TODO: iterate customer-managed policies, fetch default version,
        # detect statements with Action "*" and Resource "*".
        yield from ()
