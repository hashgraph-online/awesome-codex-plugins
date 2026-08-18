#!/usr/bin/env python3
"""Storage and workload-runtime consistency rules."""

from __future__ import annotations

import re
from typing import Dict, List, Set, Tuple

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
from path_converter import path_to_vn_name


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


def _is_mongodb_cluster(data: Dict[str, object]) -> bool:
    if data.get("kind") != "Cluster":
        return False

    metadata = data.get("metadata")
    labels = metadata.get("labels") if isinstance(metadata, dict) else None
    if isinstance(labels, dict):
        database_label = labels.get("kb.io/database")
        cluster_definition = labels.get("clusterdefinition.kubeblocks.io/name")
        if isinstance(database_label, str) and database_label.lower().startswith("mongodb"):
            return True
        if cluster_definition == "mongodb":
            return True

    spec = data.get("spec")
    component_specs = spec.get("componentSpecs") if isinstance(spec, dict) else None
    if not isinstance(component_specs, list):
        return False
    for component in component_specs:
        if not isinstance(component, dict):
            continue
        if component.get("name") == "mongodb" or component.get("componentDef") == "mongodb":
            return True
    return False


def check_mongodb_cluster_schema(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    for doc in context.yaml_documents:
        if doc.skip_checks or not isinstance(doc.data, dict):
            continue
        if doc.path.name != "index.yaml" or not _is_mongodb_cluster(doc.data):
            continue

        if doc.data.get("apiVersion") != "apps.kubeblocks.io/v1alpha1":
            add_doc_violation(
                violations,
                rule_id="R057",
                doc=doc,
                pattern=r"^\s*apiVersion\s*:",
                message="MongoDB Cluster apiVersion must be apps.kubeblocks.io/v1alpha1",
            )

        metadata = doc.data.get("metadata")
        name = metadata.get("name") if isinstance(metadata, dict) else None
        labels = metadata.get("labels") if isinstance(metadata, dict) else None
        expected_labels = {
            "kb.io/database": "mongodb-8.0.4",
            "clusterdefinition.kubeblocks.io/name": "mongodb",
            "app.kubernetes.io/instance": name,
        }
        for key, expected in expected_labels.items():
            actual = labels.get(key) if isinstance(labels, dict) else None
            if actual == expected:
                continue
            add_doc_violation(
                violations,
                rule_id="R057",
                doc=doc,
                pattern=rf"^\s*{re.escape(key)}\s*:",
                default_pattern=r"^\s*labels\s*:",
                message=f"MongoDB Cluster metadata.labels.{key} must be {expected}",
            )

        spec = doc.data.get("spec")
        component_specs = spec.get("componentSpecs") if isinstance(spec, dict) else None
        component = component_specs[0] if isinstance(component_specs, list) and component_specs else None
        if not isinstance(component, dict):
            add_doc_violation(
                violations,
                rule_id="R057",
                doc=doc,
                pattern=r"^\s*componentSpecs\s*:",
                default_pattern=r"^\s*spec\s*:",
                message="MongoDB Cluster must define a mongodb componentSpec",
            )
            continue

        expected_component_fields = {
            "name": "mongodb",
            "componentDef": "mongodb",
            "serviceVersion": "8.0.4",
        }
        for key, expected in expected_component_fields.items():
            if component.get(key) == expected:
                continue
            add_doc_violation(
                violations,
                rule_id="R057",
                doc=doc,
                pattern=rf"^\s*{re.escape(key)}\s*:",
                default_pattern=r"^\s*componentSpecs\s*:",
                message=f"MongoDB Cluster componentSpecs[0].{key} must be {expected}",
            )

    return violations


def check_statefulset_volume_claim_metadata(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    for doc in context.yaml_documents:
        if doc.skip_checks or not isinstance(doc.data, dict):
            continue
        if doc.path.name != "index.yaml" or doc.data.get("kind") != "StatefulSet":
            continue

        spec = doc.data.get("spec")
        claim_templates = spec.get("volumeClaimTemplates") if isinstance(spec, dict) else None
        if not isinstance(claim_templates, list) or not claim_templates:
            continue

        metadata = doc.data.get("metadata")
        workload_labels = metadata.get("labels") if isinstance(metadata, dict) else None
        if isinstance(workload_labels, dict) and TEMPLATE_DEPLOY_KEY in workload_labels:
            add_doc_violation(
                violations,
                rule_id="R056",
                doc=doc,
                pattern=rf"^\s*{re.escape(TEMPLATE_DEPLOY_KEY)}\s*:",
                default_pattern=r"^\s*labels\s*:",
                message=(
                    f"StatefulSet metadata.labels must omit {TEMPLATE_DEPLOY_KEY} "
                    "when spec.volumeClaimTemplates is present"
                ),
            )

        mounted_paths: Set[Tuple[str, str]] = set()
        for container in iter_containers(doc.data):
            mounts = container.get("volumeMounts")
            if not isinstance(mounts, list):
                continue
            for mount in mounts:
                if not isinstance(mount, dict):
                    continue
                mount_name = mount.get("name")
                mount_path = mount.get("mountPath")
                if isinstance(mount_name, str) and isinstance(mount_path, str):
                    mounted_paths.add((mount_name.strip(), mount_path.strip()))

        for claim_template in claim_templates:
            claim_metadata = claim_template.get("metadata") if isinstance(claim_template, dict) else None
            if not isinstance(claim_metadata, dict):
                add_doc_violation(
                    violations,
                    rule_id="R056",
                    doc=doc,
                    pattern=r"^\s*volumeClaimTemplates\s*:",
                    message="each volumeClaimTemplates item must define metadata",
                )
                continue

            claim_labels = claim_metadata.get("labels")
            if isinstance(claim_labels, dict) and TEMPLATE_DEPLOY_KEY in claim_labels:
                add_doc_violation(
                    violations,
                    rule_id="R056",
                    doc=doc,
                    pattern=rf"^\s*{re.escape(TEMPLATE_DEPLOY_KEY)}\s*:",
                    default_pattern=r"^\s*volumeClaimTemplates\s*:",
                    message=f"volumeClaimTemplates[].metadata.labels must omit {TEMPLATE_DEPLOY_KEY}",
                )

            annotations = claim_metadata.get("annotations")
            path = annotations.get("path") if isinstance(annotations, dict) else None
            value = annotations.get("value") if isinstance(annotations, dict) else None
            name = claim_metadata.get("name")
            if not isinstance(path, str) or not path.strip():
                add_doc_violation(
                    violations,
                    rule_id="R056",
                    doc=doc,
                    pattern=r"^\s*annotations\s*:",
                    default_pattern=r"^\s*volumeClaimTemplates\s*:",
                    message="volumeClaimTemplates[].metadata.annotations.path is required",
                )
                continue
            path = path.strip()

            if value != "1":
                add_doc_violation(
                    violations,
                    rule_id="R056",
                    doc=doc,
                    pattern=r"^\s*value\s*:",
                    default_pattern=r"^\s*annotations\s*:",
                    message="volumeClaimTemplates[].metadata.annotations.value must be the string '1'",
                )

            try:
                expected_name = path_to_vn_name(path)
            except ValueError:
                add_doc_violation(
                    violations,
                    rule_id="R056",
                    doc=doc,
                    pattern=r"^\s*path\s*:",
                    default_pattern=r"^\s*annotations\s*:",
                    message="volumeClaimTemplates[].metadata.annotations.path must produce a valid vn name",
                )
                continue
            if name != expected_name:
                add_doc_violation(
                    violations,
                    rule_id="R056",
                    doc=doc,
                    pattern=r"^\s*name\s*:",
                    default_pattern=r"^\s*volumeClaimTemplates\s*:",
                    message=(
                        "volumeClaimTemplates[].metadata.name must be derived from annotations.path "
                        f"with path_to_vn_name (expected {expected_name})"
                    ),
                )

            if (expected_name, path) not in mounted_paths:
                add_doc_violation(
                    violations,
                    rule_id="R056",
                    doc=doc,
                    pattern=r"^\s*volumeClaimTemplates\s*:",
                    message=(
                        "each volume claim template must have a matching container volumeMount "
                        "whose name is derived from annotations.path and whose mountPath equals that path"
                    ),
                )

    return violations


STORAGE_RULES: Dict[str, Rule] = {
    "R005": Rule("R005", check_no_emptydir),
    "R006": Rule("R006", check_image_pull_policy),
    "R011": Rule("R011", check_pvc_storage_limit),
    "R019": Rule("R019", check_database_cluster_component_resources),
    "R040": Rule("R040", check_database_cluster_visibility_labels),
    "R057": Rule("R057", check_mongodb_cluster_schema),
    "R038": Rule("R038", check_managed_workload_resource_ladder),
    "R056": Rule("R056", check_statefulset_volume_claim_metadata),
}
