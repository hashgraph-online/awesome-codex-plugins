"""Shared scanner constants and truncation helpers."""

from __future__ import annotations

from typing import Any


MAX_IMPORTS_PER_FILE = 200
MAX_EXPORTS_PER_FILE = 200
JS_STRING_RE = r"['\"]([^'\"]+)['\"]"
IDENTIFIER_RE = r"[A-Za-z_$][\w$]*"


def truncate_items(items: list[dict[str, Any]], limit: int) -> tuple[list[dict[str, Any]], bool]:
    return items[:limit], len(items) > limit


def truncate_scanned(
    imports: list[dict[str, Any]], exports: list[dict[str, str]]
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    truncated_imports, imports_truncated = truncate_items(imports, MAX_IMPORTS_PER_FILE)
    truncated_exports, exports_truncated = truncate_items(exports, MAX_EXPORTS_PER_FILE)
    if imports_truncated:
        truncated_imports.append({"specifier": "__truncated__", "kind": "truncation-marker", "is_relative": False, "names": []})
    if exports_truncated:
        truncated_exports.append({"name": "__truncated__", "kind": "truncation-marker"})
    return truncated_imports, truncated_exports

