#!/usr/bin/env python3
"""Rule-engine execution layer for consistency checks."""

from __future__ import annotations

import fnmatch
from dataclasses import replace
from pathlib import Path
from typing import Dict, Mapping, Optional, Sequence

from check_consistency_models import RegistryConfig, Rule, ScanContext, Violation


class RuleEngine:
    def __init__(
        self,
        *,
        config: RegistryConfig,
        registered_rules: Mapping[str, Rule],
        skill_root: Path,
    ) -> None:
        self.config = config
        self.registered_rules: Dict[str, Rule] = dict(registered_rules)
        self.skill_root = skill_root

    def resolve_rules(self, only_rules: Optional[Sequence[str]]) -> list[str]:
        selected_rules = list(only_rules) if only_rules else list(self.config.ordered_rule_ids)
        unknown = sorted(set(selected_rules) - set(self.registered_rules.keys()))
        if unknown:
            raise ValueError(f"unknown rule id(s): {', '.join(unknown)}")
        return selected_rules

    def run(
        self,
        *,
        context: ScanContext,
        parse_violations: Sequence[Violation],
        selected_rules: Sequence[str],
    ) -> list[Violation]:
        violations: list[Violation] = list(parse_violations)
        for rule_id in selected_rules:
            rule = self.registered_rules[rule_id]
            default_meta = self.config.rules[rule_id]
            for item in rule.check(context):
                meta = self.config.rules.get(item.rule_id, default_meta)
                if not self._in_rule_scope(item, meta.include_paths):
                    continue
                violations.append(replace(item, severity=meta.severity))

        violations.sort(key=lambda x: (str(x.path), x.line, x.rule_id, x.message))
        return violations

    def _in_rule_scope(self, violation: Violation, include_paths: Sequence[str]) -> bool:
        if not include_paths:
            return True
        relative_path = self._as_relative_path(violation.path)
        return any(fnmatch.fnmatch(relative_path, pattern) for pattern in include_paths)

    def _as_relative_path(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.skill_root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()
