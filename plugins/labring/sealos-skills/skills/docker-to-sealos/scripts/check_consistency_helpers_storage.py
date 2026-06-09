#!/usr/bin/env python3
"""Storage-oriented helper utilities for consistency rules."""

from __future__ import annotations

import re
from typing import Any, Iterator, Optional

from check_consistency_models import STORAGE_UNIT_TO_BYTES


def contains_key(node: Any, key: str) -> bool:
    if isinstance(node, dict):
        if key in node:
            return True
        return any(contains_key(value, key) for value in node.values())
    if isinstance(node, list):
        return any(contains_key(item, key) for item in node)
    return False


def parse_storage_bytes(raw_value: str) -> Optional[int]:
    text = raw_value.strip()
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*([A-Za-z]*)", text)
    if not match:
        return None

    number = float(match.group(1))
    unit = match.group(2).lower()
    factor = STORAGE_UNIT_TO_BYTES.get(unit)
    if factor is None:
        return None

    return int(number * factor)


def has_variable_expression(raw_value: str) -> bool:
    text = raw_value.strip()
    return "${{" in text or re.search(r"\$\([^)]+\)", text) is not None


def iter_pvc_storage_values(data: Any) -> Iterator[str]:
    if isinstance(data, dict):
        kind = data.get("kind")
        if kind == "PersistentVolumeClaim":
            spec = data.get("spec")
            if isinstance(spec, dict):
                resources = spec.get("resources")
                if isinstance(resources, dict):
                    requests = resources.get("requests")
                    if isinstance(requests, dict):
                        storage = requests.get("storage")
                        if storage is not None:
                            yield str(storage)

        for key, value in data.items():
            if key == "volumeClaimTemplates" and isinstance(value, list):
                for item in value:
                    if not isinstance(item, dict):
                        continue
                    spec = item.get("spec")
                    if not isinstance(spec, dict):
                        continue
                    resources = spec.get("resources")
                    if not isinstance(resources, dict):
                        continue
                    requests = resources.get("requests")
                    if not isinstance(requests, dict):
                        continue
                    storage = requests.get("storage")
                    if storage is not None:
                        yield str(storage)
            else:
                yield from iter_pvc_storage_values(value)
    elif isinstance(data, list):
        for item in data:
            yield from iter_pvc_storage_values(item)
