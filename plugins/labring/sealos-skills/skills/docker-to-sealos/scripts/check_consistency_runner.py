#!/usr/bin/env python3
"""Orchestrates registry-aware consistency checks."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Sequence

from check_consistency_context import ContextBuilder
from check_consistency_engine import RuleEngine
from check_consistency_models import Violation
from check_consistency_registry import validate_registry
from check_consistency_rule_registry import REGISTERED_RULES


def run_checks(
    skill_path: Path,
    references_dir: Path,
    registry_path: Path,
    only_rules: Optional[Sequence[str]] = None,
    additional_include_paths: Optional[Sequence[str]] = None,
) -> List[Violation]:
    config = validate_registry(registry_path, REGISTERED_RULES.keys())
    include_paths = list(config.include_paths)
    if additional_include_paths:
        include_paths.extend(additional_include_paths)
    builder = ContextBuilder(
        skill_path=skill_path,
        references_dir=references_dir,
        include_paths=include_paths,
    )
    context, parse_violations = builder.build()

    engine = RuleEngine(
        config=config,
        registered_rules=REGISTERED_RULES,
        skill_root=skill_path.parent,
    )
    selected_rules = engine.resolve_rules(only_rules)
    return engine.run(
        context=context,
        parse_violations=parse_violations,
        selected_rules=selected_rules,
    )
