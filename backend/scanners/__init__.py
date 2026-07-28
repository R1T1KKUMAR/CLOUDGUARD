"""Scanner registry.

`ALL_SCANNERS` is the single source of truth for which scanners the engine runs.
Add a new scanner class here and the orchestrator picks it up automatically.
"""

from scanners.base import BaseScanner
from scanners.config_scan import ConfigScanner
from scanners.ec2 import EC2Scanner
from scanners.iam import IAMScanner
from scanners.lambda_scan import LambdaScanner
from scanners.s3 import S3Scanner
from scanners.security_groups import SecurityGroupScanner

ALL_SCANNERS: list[type[BaseScanner]] = [
    IAMScanner,
    S3Scanner,
    EC2Scanner,
    SecurityGroupScanner,
    LambdaScanner,
    ConfigScanner,
]

__all__ = ["ALL_SCANNERS", "BaseScanner"]
