"""Shared public-surface response envelope helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def output_refs(*refs: str | Path | None) -> list[str]:
    rows: list[str] = []
    for ref in refs:
        if ref in (None, ""):
            continue
        rows.append(str(ref))
    return rows


def response_envelope(*, command: str, status: str, summary: str, body: dict[str, Any] | None = None, refs: list[str] | None = None, checks: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {"command": command, "status": status, "summary": summary, "refs": refs or [], "checks": checks or [], "body": body or {}}


def print_envelope(*, command: str, status: str, summary: str, body: dict[str, Any] | None = None, refs: list[str] | None = None, checks: list[dict[str, Any]] | None = None) -> None:
    print(json.dumps(response_envelope(command=command, status=status, summary=summary, body=body, refs=refs, checks=checks), ensure_ascii=False, indent=2))


def decode_json_arg(raw: str | None, *, field: str) -> dict | list | None:
    if raw is None:
        return None
    payload = json.loads(raw)
    if not isinstance(payload, (dict, list)):
        raise ValueError(f"{field} must decode to an object or list")
    return payload
