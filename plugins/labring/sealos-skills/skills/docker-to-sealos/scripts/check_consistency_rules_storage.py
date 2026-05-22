#!/usr/bin/env python3
"""Storage and workload-runtime consistency rules."""

from __future__ import annotations

import re
from typing import Dict, List

from check_consistency_models import (
    DB_COMPONENT_RESOURCE_LIMITS,
    DB_COMPONENT_RESOURCE_REQUESTS,
    MAX_PVC_STORAGE_BYTES,
    Rule,
    ScanContext,
    Violation,
)
from check_consistency_parser import find_line
from check_consistency_helpers_violations import add_doc_violation
from check_consistency_helpers_storage import (
    contains_key,
    has_variable_expression,
    iter_pvc_storage_values,
    parse_storage_bytes,
)
from check_consistency_helpers_workload import iter_containers


def check_no_emptydir(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    for doc in context.yaml_documents:
        if doc.skip_checks:
            continue
        if contains_key(doc.data, "emptyDir"):
            add_doc_violation(
                violations,
                rule_id="R005",
                doc=doc,
                pattern=r"^\s*emptyDir\s*:",
                message="emptyDir is not allowed; use persistent storage",
            )
    return violations


def check_image_pull_policy(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    for doc in context.yaml_documents:
        if doc.skip_checks:
            continue
        for container in iter_containers(doc.data):
            image = container.get("image")
            if not isinstance(image, str) or not image.strip():
                continue
            pull_policy = container.get("imagePullPolicy")
            if pull_policy != "IfNotPresent":
                line = find_line(doc, r"^\s*imagePullPolicy\s*:", default=find_line(doc, r"^\s*image\s*:"))
                message = (
                    "container imagePullPolicy must be IfNotPresent"
                    if pull_policy is not None
                    else "container must explicitly set imagePullPolicy: IfNotPresent"
                )
                violations.append(Violation(rule_id="R006", path=doc.path, line=line, message=message))
    return violations


def check_pvc_storage_limit(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    for doc in context.yaml_documents:
        if doc.skip_checks:
            continue

        for raw_storage in iter_pvc_storage_values(doc.data):
            storage_text = str(raw_storage).strip()
            line = find_line(
                doc,
                rf"^\s*storage\s*:\s*['\"]?{re.escape(storage_text)}['\"]?\s*$",
                default=find_line(doc, r"^\s*storage\s*:"),
            )

            if has_variable_expression(storage_text):
                violations.append(
                    Violation(
                        rule_id="R011",
                        path=doc.path,
                        line=line,
                        message="PVC storage must be a concrete quantity (variables are not allowed)",
                    )
                )
                continue

            storage_bytes = parse_storage_bytes(storage_text)
            if storage_bytes is None:
                violations.append(
                    Violation(
                        rule_id="R011",
                        path=doc.path,
                        line=line,
                        message=f"unable to parse PVC storage quantity: {storage_text!r}",
                    )
                )
                continue

            if storage_bytes > MAX_PVC_STORAGE_BYTES:
                violations.append(
                    Violation(
                        rule_id="R011",
                        path=doc.path,
                        line=line,
                        message="PVC storage request must be <= 1Gi",
                    )
                )

    return violations


def check_database_cluster_component_resources(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    for doc in context.yaml_documents:
        if doc.skip_checks or not isinstance(doc.data, dict):
            continue
        if doc.path.name != "index.yaml":
            continue
        if doc.data.get("kind") != "Cluster":
            continue

        metadata = doc.data.get("metadata")
        labels = metadata.get("labels") if isinstance(metadata, dict) else None
        db_label = labels.get("kb.io/database") if isinstance(labels, dict) else None
        if not isinstance(db_label, str) or not db_label.strip():
            continue

        spec = doc.data.get("spec")
        component_specs = spec.get("componentSpecs") if isinstance(spec, dict) else None
        if not isinstance(component_specs, list):
            continue

        for component in component_specs:
            if not isinstance(component, dict):
                continue
            component_name = str(component.get("name", "<unknown>"))
            resources = component.get("resources")
            if not isinstance(resources, dict):
                line = find_line(
                    doc,
                    rf"^\s*name\s*:\s*{re.escape(component_name)}\s*$",
                    default=find_line(doc, r"^\s*componentSpecs\s*:"),
                )
                violations.append(
                    Violation(
                        rule_id="R019",
                        path=doc.path,
                        line=line,
                        message=f"database component {component_name} must define resources limits/requests",
                    )
                )
                continue

            expected_sections = (
                ("limits", DB_COMPONENT_RESOURCE_LIMITS),
                ("requests", DB_COMPONENT_RESOURCE_REQUESTS),
            )
            for section_name, expected_values in expected_sections:
                section = resources.get(section_name)
                if not isinstance(section, dict):
                    line = find_line(
                        doc,
                        rf"^\s*name\s*:\s*{re.escape(component_name)}\s*$",
                        default=find_line(doc, r"^\s*resources\s*:"),
                    )
                    violations.append(
                        Violation(
                            rule_id="R019",
                            path=doc.path,
                            line=line,
                            message=f"database component {component_name} must define resources.{section_name}",
                        )
                    )
                    continue

                for key, expected in expected_values.items():
                    actual = section.get(key)
                    if actual == expected:
                        continue
                    line = find_line(
                        doc,
                        rf"^\s*{re.escape(key)}\s*:\s*['\"]?{re.escape(str(actual))}['\"]?\s*$",
                        default=find_line(
                            doc,
                            rf"^\s*name\s*:\s*{re.escape(component_name)}\s*$",
                            default=find_line(doc, r"^\s*resources\s*:"),
                        ),
                    )
                    violations.append(
                        Violation(
                            rule_id="R019",
                            path=doc.path,
                            line=line,
                            message=(
                                f"database component {component_name} resources.{section_name}.{key} "
                                f"must be {expected}"
                            ),
                        )
                    )

    return violations


STORAGE_RULES: Dict[str, Rule] = {
    "R005": Rule("R005", check_no_emptydir),
    "R006": Rule("R006", check_image_pull_policy),
    "R011": Rule("R011", check_pvc_storage_limit),
    "R019": Rule("R019", check_database_cluster_component_resources),
}
