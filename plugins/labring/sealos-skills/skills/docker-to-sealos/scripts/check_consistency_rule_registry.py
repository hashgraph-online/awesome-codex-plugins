#!/usr/bin/env python3
"""Rule registry composition for consistency checks."""

from __future__ import annotations

from typing import Dict, Mapping

from check_consistency_models import Rule
from check_consistency_rules_app import APP_RULES
from check_consistency_rules_security import SECURITY_RULES
from check_consistency_rules_storage import STORAGE_RULES


def _merge_rule_sets(*rule_sets: Mapping[str, Rule]) -> Dict[str, Rule]:
    merged: Dict[str, Rule] = {}
    for rule_set in rule_sets:
        for rule_id, rule in rule_set.items():
            if rule_id in merged:
                raise ValueError(f"duplicate rule id: {rule_id}")
            merged[rule_id] = rule
    return merged


REGISTERED_RULES: Dict[str, Rule] = _merge_rule_sets(
    APP_RULES,
    STORAGE_RULES,
    SECURITY_RULES,
)
