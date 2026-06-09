#!/usr/bin/env python3
"""Rules registry loading and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import yaml

from check_consistency_models import ALLOWED_SEVERITIES, DEFAULT_SEVERITY, RegistryConfig, RegistryRuleConfig


def _parse_global_include_paths(data: Mapping[str, Any]) -> List[str]:
    include_paths: List[str] = []
    scope = data.get("scope")
    if isinstance(scope, dict):
        include = scope.get("include")
        if include is not None:
            if not isinstance(include, list) or not all(isinstance(x, str) for x in include):
                raise ValueError("scope.include must be a list of strings")
            include_paths = list(include)
    return include_paths


def _parse_rule_scope(rule_entry: Mapping[str, Any]) -> List[str]:
    scope = rule_entry.get("scope")
    if scope is None:
        return []
    if not isinstance(scope, dict):
        raise ValueError(f"rule scope must be an object: {rule_entry!r}")
    include_paths = scope.get("include_paths")
    if include_paths is None:
        return []
    if not isinstance(include_paths, list) or not all(isinstance(x, str) for x in include_paths):
        raise ValueError(f"rule scope.include_paths must be a list of strings: {rule_entry!r}")
    return include_paths


def _parse_rule_config(item: Mapping[str, Any]) -> RegistryRuleConfig:
    rule_id = item.get("id")
    description = item.get("description")
    if not isinstance(rule_id, str) or not isinstance(description, str):
        raise ValueError(f"invalid rule entry in registry: {item!r}")

    severity = item.get("severity", DEFAULT_SEVERITY)
    if not isinstance(severity, str) or severity not in ALLOWED_SEVERITIES:
        allowed = ", ".join(sorted(ALLOWED_SEVERITIES))
        raise ValueError(f"invalid severity for {rule_id}: {severity!r} (allowed: {allowed})")

    return RegistryRuleConfig(
        rule_id=rule_id,
        description=description,
        severity=severity,
        include_paths=_parse_rule_scope(item),
    )


def load_registry_config(registry_path: Path) -> RegistryConfig:
    data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"invalid rules registry format: {registry_path}")

    rules = data.get("rules")
    if not isinstance(rules, list):
        raise ValueError(f"invalid rules list in registry: {registry_path}")

    ordered_rule_ids: List[str] = []
    parsed_rules: Dict[str, RegistryRuleConfig] = {}
    for item in rules:
        if not isinstance(item, dict):
            raise ValueError(f"invalid rule entry in registry: {item!r}")
        parsed_rule = _parse_rule_config(item)
        if parsed_rule.rule_id in parsed_rules:
            raise ValueError(f"duplicate rule id in registry: {parsed_rule.rule_id}")
        ordered_rule_ids.append(parsed_rule.rule_id)
        parsed_rules[parsed_rule.rule_id] = parsed_rule

    return RegistryConfig(
        include_paths=_parse_global_include_paths(data),
        rules=parsed_rules,
        ordered_rule_ids=ordered_rule_ids,
    )


def validate_registry(registry_path: Path, implemented_rule_ids: Iterable[str]) -> RegistryConfig:
    config = load_registry_config(registry_path)
    registry_ids = set(config.ordered_rule_ids)
    implemented_ids = set(implemented_rule_ids)

    missing_impl = sorted(registry_ids - implemented_ids)
    missing_registry = sorted(implemented_ids - registry_ids)

    if missing_impl or missing_registry:
        parts: List[str] = []
        if missing_impl:
            parts.append(f"rules declared but not implemented: {', '.join(missing_impl)}")
        if missing_registry:
            parts.append(f"rules implemented but not declared: {', '.join(missing_registry)}")
        raise ValueError("; ".join(parts))

    return config
