#!/usr/bin/env python3
"""Workload-centric helper utilities for consistency rules."""

from __future__ import annotations

from typing import Any, Iterator, Mapping, Optional, Tuple

from check_consistency_models import APP_WORKLOAD_KINDS, ScanContext, YamlDocument


def iter_documents_by_kind(context: ScanContext, kind: str) -> Iterator[YamlDocument]:
    for doc in context.yaml_documents:
        if doc.skip_checks:
            continue
        if isinstance(doc.data, dict) and doc.data.get("kind") == kind:
            yield doc


def iter_containers(node: Any) -> Iterator[dict]:
    if isinstance(node, dict):
        for child_key, child_value in node.items():
            if child_key in {"containers", "initContainers"} and isinstance(child_value, list):
                for item in child_value:
                    if isinstance(item, dict):
                        yield item
            yield from iter_containers(child_value)
    elif isinstance(node, list):
        for item in node:
            yield from iter_containers(item)


def iter_workload_env_secret_refs(data: Mapping[str, Any]) -> Iterator[Tuple[str, str]]:
    for env_name, secret_name, _ in iter_workload_env_secret_key_refs(data):
        yield env_name, secret_name


def iter_workload_env_secret_key_refs(data: Mapping[str, Any]) -> Iterator[Tuple[str, str, Optional[str]]]:
    for source, secret_name, env_name, secret_key in iter_workload_secret_refs(data):
        if source == "env" and env_name is not None:
            yield env_name, secret_name, secret_key


def iter_workload_secret_refs(data: Mapping[str, Any]) -> Iterator[Tuple[str, str, Optional[str], Optional[str]]]:
    for container in iter_containers(data):
        env_list = container.get("env")
        if not isinstance(env_list, list):
            env_list = []

        for env_item in env_list:
            if not isinstance(env_item, dict):
                continue
            env_name = env_item.get("name")
            value_from = env_item.get("valueFrom")
            if not isinstance(env_name, str) or not isinstance(value_from, dict):
                continue
            secret_ref = value_from.get("secretKeyRef")
            if not isinstance(secret_ref, dict):
                continue
            secret_name = secret_ref.get("name")
            secret_key = secret_ref.get("key")
            if isinstance(secret_name, str):
                yield "env", secret_name, env_name, secret_key if isinstance(secret_key, str) else None

        env_from_list = container.get("envFrom")
        if isinstance(env_from_list, list):
            for env_from_item in env_from_list:
                if not isinstance(env_from_item, dict):
                    continue
                secret_ref = env_from_item.get("secretRef")
                if not isinstance(secret_ref, dict):
                    continue
                secret_name = secret_ref.get("name")
                if isinstance(secret_name, str):
                    yield "envFrom", secret_name, None, None

    template_spec = get_template_spec(data)
    if not isinstance(template_spec, dict):
        return

    volumes = template_spec.get("volumes")
    if not isinstance(volumes, list):
        return

    for volume in volumes:
        if not isinstance(volume, dict):
            continue
        secret_spec = volume.get("secret")
        if isinstance(secret_spec, dict):
            secret_name = secret_spec.get("secretName")
            if isinstance(secret_name, str):
                yield "volume", secret_name, None, None

        projected = volume.get("projected")
        if not isinstance(projected, dict):
            continue
        sources = projected.get("sources")
        if not isinstance(sources, list):
            continue
        for source in sources:
            if not isinstance(source, dict):
                continue
            source_secret = source.get("secret")
            if not isinstance(source_secret, dict):
                continue
            secret_name = source_secret.get("name")
            if isinstance(secret_name, str):
                yield "projected", secret_name, None, None


def get_template_spec(data: Mapping[str, Any]) -> Optional[Mapping[str, Any]]:
    spec = data.get("spec")
    if not isinstance(spec, dict):
        return None
    template = spec.get("template")
    if not isinstance(template, dict):
        return None
    template_spec = template.get("spec")
    if not isinstance(template_spec, dict):
        return None
    return template_spec


def is_app_workload_document(doc: YamlDocument) -> bool:
    if not isinstance(doc.data, dict):
        return False
    if doc.data.get("kind") not in APP_WORKLOAD_KINDS:
        return False
    template_spec = get_template_spec(doc.data)
    if not isinstance(template_spec, dict):
        return False
    containers = template_spec.get("containers")
    return isinstance(containers, list) and len(containers) > 0


def has_managed_workload_marker(data: Mapping[str, Any]) -> bool:
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        return False

    labels = metadata.get("labels")
    if isinstance(labels, dict) and "cloud.sealos.io/app-deploy-manager" in labels:
        return True

    annotations = metadata.get("annotations")
    if isinstance(annotations, dict) and "originImageName" in annotations:
        return True

    return False


def is_managed_app_workload_document(doc: YamlDocument) -> bool:
    if not is_app_workload_document(doc):
        return False
    if not has_managed_workload_marker(doc.data):
        return False
    return True
