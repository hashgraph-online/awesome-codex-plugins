#!/usr/bin/env python3
"""Shared data models and constants for docker-to-sealos consistency checks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Mapping, Sequence

if TYPE_CHECKING:
    from check_consistency_line_locator import LineLocator


LATEST_IMAGE_PATTERN = re.compile(r"\b(?:image|originImageName)\s*:\s*['\"]?[^#\s'\"]*:latest\b")
TEMPLATE_NAME_PATTERN = re.compile(r"^[a-z0-9](?:[-a-z0-9]*[a-z0-9])?$")
NEGATIVE_MARKERS = ("wrong example", "❌", "invalid example")
WORKLOAD_KINDS = {"Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob"}
APP_WORKLOAD_KINDS = {"Deployment", "StatefulSet", "DaemonSet"}
DB_SECRET_SUFFIXES = (
    "-pg-conn-credential",
    "-mysql-conn-credential",
    "-mongodb-account-root",
    "-mongo-mongodb-account-root",
    "-mongodb-mongodb-account-root",
    "-redis-redis-account-default",
    "-redis-account-default",
    "-broker-account-admin",
)
MAX_PVC_STORAGE_BYTES = 1024 ** 3  # 1Gi
SEALOS_CPU_REQUEST_BY_LIMIT = {
    "100m": "10m",
    "200m": "20m",
    "500m": "50m",
    "1": "100m",
    "2": "200m",
    "3": "300m",
    "4": "400m",
    "8": "800m",
}
SEALOS_MEMORY_REQUEST_BY_LIMIT = {
    "128Mi": "12Mi",
    "256Mi": "25Mi",
    "512Mi": "51Mi",
    "1024Mi": "102Mi",
    "2048Mi": "204Mi",
    "4096Mi": "409Mi",
    "8192Mi": "819Mi",
    "16384Mi": "1638Mi",
}
DB_COMPONENT_RESOURCE_LIMITS = {"cpu": "500m", "memory": "512Mi"}
DB_COMPONENT_RESOURCE_REQUESTS = {"cpu": "50m", "memory": "51Mi"}
STORAGE_UNIT_TO_BYTES = {
    "": 1,
    "k": 1000,
    "m": 1000 ** 2,
    "g": 1000 ** 3,
    "t": 1000 ** 4,
    "p": 1000 ** 5,
    "e": 1000 ** 6,
    "ki": 1024,
    "mi": 1024 ** 2,
    "gi": 1024 ** 3,
    "ti": 1024 ** 4,
    "pi": 1024 ** 5,
    "ei": 1024 ** 6,
}
DEFAULT_SEVERITY = "error"
ALLOWED_SEVERITIES = {"error", "warning"}


@dataclass(frozen=True)
class YamlBlock:
    path: Path
    start_line: int
    source: str
    skip_checks: bool


@dataclass(frozen=True)
class YamlDocument:
    path: Path
    start_line: int
    source: str
    data: Any
    skip_checks: bool
    line_locator: "LineLocator"


@dataclass(frozen=True)
class Violation:
    rule_id: str
    path: Path
    line: int
    message: str
    severity: str = DEFAULT_SEVERITY


CheckFunction = Callable[["ScanContext"], List[Violation]]


@dataclass(frozen=True)
class Rule:
    rule_id: str
    check: CheckFunction


@dataclass(frozen=True)
class RegistryRuleConfig:
    rule_id: str
    description: str
    severity: str
    include_paths: Sequence[str]


@dataclass(frozen=True)
class RegistryConfig:
    include_paths: List[str]
    rules: Dict[str, RegistryRuleConfig]
    ordered_rule_ids: List[str]


@dataclass(frozen=True)
class ScanContext:
    skill_path: Path
    references_dir: Path
    scanned_paths: List[Path]
    file_texts: Dict[Path, str]
    yaml_documents: List[YamlDocument]

    @property
    def markdown_paths(self) -> List[Path]:
        """Backward-compatible alias for pre-refactor callers."""
        return self.scanned_paths
