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
    SEALOS_CPU_REQUEST_BY_LIMIT,
    SEALOS_MEMORY_REQUEST_BY_LIMIT,
    TEMPLATE_DEPLOY_KEY,
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


def check_statefulset_template_deploy_labels(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    expected_value = "${{ defaults.app_name }}"

    for doc in context.yaml_documents:
        if doc.skip_checks or not isinstance(doc.data, dict):
            continue
        if doc.data.get("kind") != "StatefulSet":
            continue

        metadata = doc.data.get("metadata")
        labels = metadata.get("labels") if isinstance(metadata, dict) else None
        if not isinstance(labels, dict) or labels.get(TEMPLATE_DEPLOY_KEY) != expected_value:
            add_doc_violation(
                violations,
                rule_id="R041",
                doc=doc,
                pattern=rf"^\s*{re.escape(TEMPLATE_DEPLOY_KEY)}\s*:",
                default_pattern=r"^\s*labels\s*:",
                message=(
                    f"StatefulSet metadata.labels.{TEMPLATE_DEPLOY_KEY} "
                    f"must be {expected_value} for Template instance tracking"
                ),
            )

        spec = doc.data.get("spec")
        volume_claim_templates = spec.get("volumeClaimTemplates") if isinstance(spec, dict) else None
        if not isinstance(volume_claim_templates, list):
            continue

        for volume_claim_template in volume_claim_templates:
            if not isinstance(volume_claim_template, dict):
                continue
            vct_metadata = volume_claim_template.get("metadata")
            vct_labels = vct_metadata.get("labels") if isinstance(vct_metadata, dict) else None
            if isinstance(vct_labels, dict) and vct_labels.get(TEMPLATE_DEPLOY_KEY) == expected_value:
                continue

            name = "<unknown>"
            if isinstance(vct_metadata, dict) and isinstance(vct_metadata.get("name"), str):
                name = vct_metadata["name"]
            add_doc_violation(
                violations,
                rule_id="R041",
                doc=doc,
                pattern=rf"^\s*{re.escape(TEMPLATE_DEPLOY_KEY)}\s*:",
                default_pattern=rf"^\s*name\s*:\s*{re.escape(name)}\s*$",
                message=(
                    f"StatefulSet volumeClaimTemplates[{name}] metadata.labels.{TEMPLATE_DEPLOY_KEY} "
                    f"must be {expected_value} so Template can track and clean PVCs"
                ),
            )

    return violations


def _display_allowed(values: Dict[str, str]) -> str:
    return "/".join(values.keys())


def _resource_line(doc, key: str, value) -> int:
    if value is None:
        return find_line(doc, rf"^\s*{re.escape(key)}\s*:", default=find_line(doc, r"^\s*resources\s*:"))
    return find_line(
        doc,
        rf"^\s*{re.escape(key)}\s*:\s*['\"]?{re.escape(str(value))}['\"]?\s*$",
        default=find_line(doc, r"^\s*resources\s*:"),
    )


def check_managed_workload_resource_ladder(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    for doc in context.yaml_documents:
        if doc.skip_checks or not isinstance(doc.data, dict):
            continue
        if doc.path.name != "index.yaml":
            continue
        if doc.data.get("kind") not in {"Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob"}:
            continue

        for container in iter_containers(doc.data):
            image = container.get("image")
            if not isinstance(image, str) or not image.strip():
                continue

            name = str(container.get("name", "<unknown>"))
            resources = container.get("resources")
            if not isinstance(resources, dict):
                violations.append(
                    Violation(
                        rule_id="R038",
                        path=doc.path,
                        line=find_line(doc, rf"^\s*name\s*:\s*{re.escape(name)}\s*$"),
                        message=f"container {name} must define resources limits/requests from the Sealos ladder",
                    )
                )
                continue

            limits = resources.get("limits")
            requests = resources.get("requests")
            if not isinstance(limits, dict):
                violations.append(
                    Violation(
                        rule_id="R038",
                        path=doc.path,
                        line=find_line(doc, r"^\s*resources\s*:"),
                        message=f"container {name} must define resources.limits from the Sealos ladder",
                    )
                )
                continue
            if not isinstance(requests, dict):
                violations.append(
                    Violation(
                        rule_id="R038",
                        path=doc.path,
                        line=find_line(doc, r"^\s*resources\s*:"),
                        message=f"container {name} must define resources.requests derived from limits",
                    )
                )
                continue

            cpu_limit = str(limits.get("cpu", "")).strip()
            memory_limit = str(limits.get("memory", "")).strip()
            if cpu_limit not in SEALOS_CPU_REQUEST_BY_LIMIT:
                violations.append(
                    Violation(
                        rule_id="R038",
                        path=doc.path,
                        line=_resource_line(doc, "cpu", limits.get("cpu")),
                        message=(
                            f"container {name} limits.cpu must use Sealos ladder "
                            f"({_display_allowed(SEALOS_CPU_REQUEST_BY_LIMIT)})"
                        ),
                    )
                )
            if memory_limit not in SEALOS_MEMORY_REQUEST_BY_LIMIT:
                violations.append(
                    Violation(
                        rule_id="R038",
                        path=doc.path,
                        line=_resource_line(doc, "memory", limits.get("memory")),
                        message=(
                            f"container {name} limits.memory must use Sealos ladder "
                            f"({_display_allowed(SEALOS_MEMORY_REQUEST_BY_LIMIT)})"
                        ),
                    )
                )

            expected_cpu_request = SEALOS_CPU_REQUEST_BY_LIMIT.get(cpu_limit)
            expected_memory_request = SEALOS_MEMORY_REQUEST_BY_LIMIT.get(memory_limit)
            actual_cpu_request = str(requests.get("cpu", "")).strip()
            actual_memory_request = str(requests.get("memory", "")).strip()
            if expected_cpu_request is not None and actual_cpu_request != expected_cpu_request:
                violations.append(
                    Violation(
                        rule_id="R038",
                        path=doc.path,
                        line=_resource_line(doc, "cpu", requests.get("cpu")),
                        message=(
                            f"container {name} requests.cpu must be {expected_cpu_request} "
                            f"when limits.cpu is {cpu_limit}"
                        ),
                    )
                )
            if expected_memory_request is not None and actual_memory_request != expected_memory_request:
                violations.append(
                    Violation(
                        rule_id="R038",
                        path=doc.path,
                        line=_resource_line(doc, "memory", requests.get("memory")),
                        message=(
                            f"container {name} requests.memory must be {expected_memory_request} "
                            f"when limits.memory is {memory_limit}"
                        ),
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


def check_database_cluster_visibility_labels(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    required_label_keys = (
        "kb.io/database",
        "sealos-db-provider-cr",
        "clusterdefinition.kubeblocks.io/name",
    )

    for doc in context.yaml_documents:
        if doc.skip_checks or not isinstance(doc.data, dict):
            continue
        if doc.path.name != "index.yaml":
            continue
        if doc.data.get("kind") != "Cluster":
            continue
        api_version = doc.data.get("apiVersion")
        if not isinstance(api_version, str) or not api_version.startswith("apps.kubeblocks.io/"):
            continue

        metadata = doc.data.get("metadata")
        if not isinstance(metadata, dict):
            continue
        labels = metadata.get("labels")
        if not isinstance(labels, dict):
            add_doc_violation(
                violations,
                rule_id="R040",
                doc=doc,
                pattern=r"^\s*labels\s*:",
                default_pattern=r"^\s*metadata\s*:",
                message=(
                    "database Cluster metadata.labels must include "
                    "kb.io/database, sealos-db-provider-cr, and "
                    "clusterdefinition.kubeblocks.io/name for dbprovider visibility"
                ),
            )
            continue

        name = metadata.get("name")
        if not isinstance(name, str) or not name.strip():
            continue

        for label_key in required_label_keys:
            label_value = labels.get(label_key)
            if isinstance(label_value, str) and label_value.strip():
                continue
            add_doc_violation(
                violations,
                rule_id="R040",
                doc=doc,
                pattern=rf"^\s*{re.escape(label_key)}\s*:",
                default_pattern=r"^\s*labels\s*:",
                message=(
                    "database Cluster metadata.labels must include "
                    "kb.io/database, sealos-db-provider-cr, and "
                    "clusterdefinition.kubeblocks.io/name for dbprovider visibility"
                ),
            )

        label_value = labels.get("sealos-db-provider-cr")
        if label_value is not None and label_value != name:
            add_doc_violation(
                violations,
                rule_id="R040",
                doc=doc,
                pattern=r"^\s*sealos-db-provider-cr\s*:",
                default_pattern=r"^\s*labels\s*:",
                message="database Cluster metadata.labels.sealos-db-provider-cr must exactly match metadata.name",
            )

    return violations


STORAGE_RULES: Dict[str, Rule] = {
    "R005": Rule("R005", check_no_emptydir),
    "R006": Rule("R006", check_image_pull_policy),
    "R011": Rule("R011", check_pvc_storage_limit),
    "R041": Rule("R041", check_statefulset_template_deploy_labels),
    "R019": Rule("R019", check_database_cluster_component_resources),
    "R040": Rule("R040", check_database_cluster_visibility_labels),
    "R038": Rule("R038", check_managed_workload_resource_ladder),
}
