from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import yaml

from .model import CheckResult, utc_now

def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in value)


def _extract_json(stdout: str) -> dict[str, Any]:
    start = stdout.find("{")
    if start < 0:
        return {}
    try:
        payload = json.loads(stdout[start:])
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    body = payload.get("body")
    if isinstance(body, dict):
        packet = body.get("packet")
        if isinstance(packet, dict):
            return packet
        status_payload = body.get("status")
        if isinstance(status_payload, dict):
            return status_payload
        doctor_payload = body.get("doctor")
        if isinstance(doctor_payload, dict):
            return doctor_payload
        result_payload = body.get("result")
        if isinstance(result_payload, dict):
            return result_payload
    return payload


class Recorder:
    def __init__(self, artifact_dir: Path) -> None:
        self.artifact_dir = artifact_dir
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self.checks: list[CheckResult] = []

    def write_text(self, relpath: str, content: str) -> str:
        path = self.artifact_dir / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return str(path)

    def write_json(self, relpath: str, payload: dict[str, Any]) -> str:
        path = self.artifact_dir / relpath
        _write_json(path, payload)
        return str(path)

    def add(self, name: str, status: str, detail: str, artifacts: Iterable[str] | None = None) -> None:
        self.checks.append(CheckResult(name=name, status=status, detail=detail, artifacts=list(artifacts or [])))

    def checks_payload(self) -> list[dict[str, Any]]:
        return [
            {
                "name": item.name,
                "status": item.status,
                "detail": item.detail,
                "artifacts": item.artifacts,
            }
            for item in self.checks
        ]

    def summary_payload(self, *, tier: str, capabilities: dict[str, Any], work_root: str) -> dict[str, Any]:
        counts = {"passed": 0, "failed": 0, "degraded": 0}
        for item in self.checks:
            counts[item.status] = counts.get(item.status, 0) + 1
        overall = "failed" if counts.get("failed", 0) or counts.get("degraded", 0) else "passed"
        return {
            "schema_version": 1,
            "generated_at": utc_now(),
            "tier": tier,
            "overall_status": overall,
            "counts": counts,
            "capabilities": capabilities,
            "work_root": work_root,
            "checks": self.checks_payload(),
        }

__all__ = [
    "Recorder",
    "_dump_yaml",
    "_extract_json",
    "_load_yaml",
    "_read_json",
    "_safe_name",
    "_write_json",
]
