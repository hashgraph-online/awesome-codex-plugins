#!/usr/bin/env python3
"""Helpers for resolving local client context for yandex-performance-ops."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable, Optional


DEFAULT_CONTEXT_PATHS = (
    ".codex/yandex-performance-client.json",
    "claude/yandex-performance-client.json",
    ".claude/yandex-performance-client.json",
)


def _expand(path: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(path))).resolve()


def find_client_context(explicit_path: Optional[str] = None) -> Optional[Path]:
    candidates = []
    if explicit_path:
        candidates.append(explicit_path)
    env_path = os.environ.get("YANDEX_PERFORMANCE_CLIENT_CONTEXT")
    if env_path:
        candidates.append(env_path)
    candidates.extend(DEFAULT_CONTEXT_PATHS)

    cwd = Path.cwd()
    for candidate in candidates:
        p = Path(candidate)
        if not p.is_absolute():
            p = (cwd / p).resolve()
        if p.exists():
            return p
    return None


def load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_client_context(explicit_path: Optional[str] = None, required: bool = False) -> dict:
    found = find_client_context(explicit_path)
    if not found:
        if required:
            raise FileNotFoundError(
                "Client context not found. Create .codex/yandex-performance-client.json "
                "or set YANDEX_PERFORMANCE_CLIENT_CONTEXT."
            )
        return {}
    data = load_json(found)
    if not isinstance(data, dict):
        raise ValueError(f"Client context must be a JSON object: {found}")
    data["_context_source"] = "local-protected-file"
    return data


def nested_get(data: dict, dotted_path: str, default: Any = None) -> Any:
    current: Any = data
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def env_or_context(data: dict, env_name: str, dotted_path: Optional[str] = None, default: Any = None) -> Any:
    value = os.environ.get(env_name)
    if value not in (None, ""):
        return value
    if dotted_path:
        found = nested_get(data, dotted_path, default)
        if found not in (None, ""):
            return found
    return default


def ensure_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def read_text_lines(path: Optional[str]) -> list[str]:
    if not path:
        return []
    p = _expand(path)
    if not p.exists():
        return []
    return [line.strip() for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_csv_ints(value: Any) -> list[int]:
    if value is None:
        return []
    if isinstance(value, list):
        return [int(x) for x in value if str(x).strip()]
    return [int(x.strip()) for x in str(value).split(",") if x.strip()]


def parse_csv_strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return [x.strip() for x in str(value).split(",") if x.strip()]
