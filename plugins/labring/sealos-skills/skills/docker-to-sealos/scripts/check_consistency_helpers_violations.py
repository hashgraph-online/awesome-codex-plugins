#!/usr/bin/env python3
"""Violation construction helpers for consistency rules."""

from __future__ import annotations

from typing import Any, Callable, List, Mapping, Optional

from check_consistency_models import ScanContext, Violation, YamlDocument
from check_consistency_parser import find_line

from check_consistency_helpers_workload import is_managed_app_workload_document


def add_doc_violation(
    violations: List[Violation],
    *,
    rule_id: str,
    doc: YamlDocument,
    pattern: str,
    message: str,
    default_pattern: Optional[str] = None,
) -> None:
    default_line = find_line(doc, default_pattern) if default_pattern else None
    line = find_line(doc, pattern, default=default_line)
    violations.append(
        Violation(
            rule_id=rule_id,
            path=doc.path,
            line=line,
            message=message,
        )
    )


def check_managed_workload_setting(
    context: ScanContext,
    *,
    rule_id: str,
    value_extractor: Callable[[Mapping[str, Any]], Any],
    expected: Any,
    value_pattern: str,
    fallback_pattern: str,
    missing_message: str,
    mismatch_message: str,
) -> List[Violation]:
    violations: List[Violation] = []
    for doc in context.yaml_documents:
        if doc.skip_checks or not is_managed_app_workload_document(doc):
            continue
        if not isinstance(doc.data, dict):
            continue

        value = value_extractor(doc.data)
        if value == expected:
            continue

        add_doc_violation(
            violations,
            rule_id=rule_id,
            doc=doc,
            pattern=value_pattern,
            default_pattern=fallback_pattern,
            message=mismatch_message if value is not None else missing_message,
        )

    return violations
