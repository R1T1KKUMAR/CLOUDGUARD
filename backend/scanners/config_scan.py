"""AWS Config scanner: surfaces non-compliant resources from Config rules.

Rather than re-implementing every compliance check, this scanner reads the
evaluation results AWS Config already produces and turns each NON_COMPLIANT
result into a CloudGuard finding.
"""

from __future__ import annotations

from collections.abc import Iterable

from models import Finding, Service
from scanners.base import BaseScanner


class ConfigScanner(BaseScanner):
    name = "config"

    def scan(self) -> Iterable[Finding]:
        config = self.client("config")

        rules_paginator = config.get_paginator("describe_config_rules")
        for rules_page in rules_paginator.paginate():
            for rule in rules_page.get("ConfigRules", []):
                rule_name = rule["ConfigRuleName"]
                yield from self._non_compliant(config, rule_name)

    def _non_compliant(self, config, rule_name: str) -> Iterable[Finding]:
        results_paginator = config.get_paginator(
            "get_compliance_details_by_config_rule"
        )
        for page in results_paginator.paginate(
            ConfigRuleName=rule_name, ComplianceTypes=["NON_COMPLIANT"]
        ):
            for result in page.get("EvaluationResults", []):
                qualifier = result["EvaluationResultIdentifier"][
                    "EvaluationResultQualifier"
                ]
                resource_id = qualifier.get("ResourceId", "unknown")
                yield Finding(
                    service=Service.CONFIG,
                    resource_id=resource_id,
                    check_id=f"config-{rule_name}",
                    title=f"Resource '{resource_id}' is non-compliant with Config rule '{rule_name}'",
                    evidence={
                        "rule": rule_name,
                        "resource_type": qualifier.get("ResourceType"),
                        "resource_id": resource_id,
                    },
                )
