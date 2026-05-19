from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import selectors
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import textwrap
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable
from urllib.error import URLError
from urllib.request import urlopen

import yaml

from thoth.init.render import render_codex_hooks_payload
from thoth.objects import Store
from thoth.plan.compiler import compile_task_authority
from thoth.plan.store import load_project_manifest, upsert_work_item, upsert_decision
from thoth.run.ledger import complete_run, heartbeat_run
from thoth.run.phases import default_validate_output_schema
from thoth.selftest_seed import seed_host_real_app

from .model import *
from .recorder import *
from .processes import *
from .capabilities import *

def _compact_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def _host_real_decision_payload() -> dict[str, Any]:
    now = utc_now()
    return {
        "schema_version": 1,
        "kind": "decision",
        "decision_id": "DEC-host-real-selftest",
        "scope_id": "command-probe-repo",
        "question": "Which minimal Thoth command-probe workflow should the disposable host repo follow?",
        "candidate_method_ids": ["runtime-probe", "review-probe"],
        "selected_values": {"workflow": ["runtime-probe", "review-probe"]},
        "status": "frozen",
        "unresolved_gaps": [],
        "created_at": now,
        "updated_at": now,
    }


def _expected_host_review_result() -> dict[str, Any]:
    return {
        "summary": "1 issue",
        "findings": [
            {
                "severity": "high",
                "title": "Empty title accepted",
                "path": "tracker/review_probe.py",
                "line": 4,
                "summary": "Blank titles are persisted as valid task state.",
            }
        ],
    }


def _host_real_contract_payloads() -> list[dict[str, Any]]:
    now = utc_now()
    return [
        {
            "schema_version": 1,
            "kind": "work_item",
            "work_id": "task-runtime-probe",
            "direction": "backend",
            "module": "selftest",
            "title": "Exercise durable sleep handoff without source edits",
            "status": "ready",
            "work_kind": "execution",
            "runnable": True,
            "goal": "Public `run --sleep` and `loop --sleep` must create durable ledgers, remain attachable, and stop cleanly without touching source files.",
            "context": "command-probe-repo",
            "constraints": ["selftest-command-probe-repo"],
            "execution_plan": [
                "Treat this task as a runtime protocol probe rather than a product-development task.",
                "Do not modify repo source files.",
                "Do not invent feature work, fallback validators, or review closure work.",
                "If an external worker is handed off successfully, stop there.",
            ],
            "eval_contract": {
                "entrypoint": {"command": "python scripts/runtime_probe.py"},
                "primary_metric": {"name": "runtime_contract_ok", "direction": "gte", "threshold": 1},
                "failure_classes": ["runtime_handoff_gap"],
                "validate_output_schema": default_validate_output_schema(),
            },
            "runtime_policy": {"loop": {"max_iterations": 10, "max_runtime_seconds": 28800}},
            "decisions": ["DEC-host-real-selftest"],
            "missing_questions": [],
            "created_at": now,
            "updated_at": now,
        },
        {
            "schema_version": 1,
            "kind": "work_item",
            "work_id": "task-review-probe",
            "direction": "backend",
            "module": "selftest",
            "title": "Return the fixed single finding for the known review defect",
            "status": "ready",
            "work_kind": "execution",
            "runnable": True,
            "goal": "Review `tracker/review_probe.py`, emit exactly one structured finding, and do not modify source files.",
            "context": "command-probe-repo",
            "constraints": ["selftest-command-probe-repo"],
            "execution_plan": [
                "Inspect only the review target and any imports needed to understand it.",
                "Return exactly the expected structured finding.",
                "Do not emit prose outside the structured review result.",
                "Do not modify code.",
            ],
            "eval_contract": {
                "entrypoint": {"command": "python scripts/runtime_probe.py"},
                "primary_metric": {"name": "review_exact_match", "direction": "gte", "threshold": 1},
                "failure_classes": ["review_output_drift"],
                "validate_output_schema": default_validate_output_schema(),
                "review_binding": {"target": "tracker/review_probe.py"},
                "review_expectation": _expected_host_review_result(),
            },
            "runtime_policy": {"loop": {"max_iterations": 10, "max_runtime_seconds": 28800}},
            "decisions": ["DEC-host-real-selftest"],
            "missing_questions": [],
            "created_at": now,
            "updated_at": now,
        },
    ]


def _seed_host_real_tasks(project_dir: Path) -> None:
    upsert_decision(project_dir, _host_real_decision_payload())
    for item in _host_real_contract_payloads():
        upsert_work_item(project_dir, item)
    compile_task_authority(project_dir)


def _write_host_real_discuss_payload_files(project_dir: Path) -> tuple[Path, list[Path]]:
    payload_dir = project_dir / ".thoth-selftest-inputs"
    payload_dir.mkdir(parents=True, exist_ok=True)
    decision_path = payload_dir / "decision.json"
    _write_json(decision_path, _host_real_decision_payload())
    contract_paths: list[Path] = []
    for index, contract in enumerate(_host_real_contract_payloads(), start=1):
        contract_path = payload_dir / f"contract-{index}.json"
        _write_json(contract_path, contract)
        contract_paths.append(contract_path)
    return decision_path, contract_paths


def _seed_host_real_repo(project_dir: Path, recorder: Recorder | None = None) -> None:
    shutil.rmtree(project_dir, ignore_errors=True)
    project_dir.mkdir(parents=True, exist_ok=True)
    seed_host_real_app(project_dir)
    _init_git_repo(project_dir)


def _host_real_source_fingerprint(project_dir: Path) -> dict[str, str]:
    tracked_root = project_dir / "tracker"
    fingerprints: dict[str, str] = {}
    if not tracked_root.is_dir():
        return fingerprints
    for path in sorted(tracked_root.rglob("*")):
        if not path.is_file():
            continue
        relpath = path.relative_to(project_dir).as_posix()
        fingerprints[relpath] = hashlib.sha256(path.read_bytes()).hexdigest()
    return fingerprints


def _host_real_source_unchanged(project_dir: Path, baseline: dict[str, str]) -> tuple[bool, dict[str, Any]]:
    current = _host_real_source_fingerprint(project_dir)
    return current == baseline, {
        "baseline": baseline,
        "current": current,
    }

def _run_deterministic_validators(
    project_dir: Path,
    recorder: Recorder,
    *,
    label: str,
    validators: tuple[str, ...],
) -> list[str]:
    artifacts: list[str] = []
    for script in validators:
        result = _run_command([PYTHON, script], cwd=project_dir, timeout=120)
        script_label = _safe_name(f"{label}-{Path(script).stem}")
        artifacts.extend(_save_command(recorder, script_label, result))
        if result.returncode != 0:
            raise RuntimeError(f"{script} failed for {label}")
    recorder.add(
        f"{label}.validators",
        "passed",
        f"Deterministic validators passed for {label}.",
        artifacts,
    )
    return artifacts


def _latest_run_id(
    project_dir: Path,
    *,
    kind: str,
    work_id: str | None = None,
    exclude_run_ids: set[str] | None = None,
) -> str:
    exclude = exclude_run_ids or set()
    runs_dir = project_dir / ".thoth" / "runs"
    candidates: list[tuple[str, str]] = []
    if not runs_dir.is_dir():
        return ""
    for run_dir in runs_dir.iterdir():
        if not run_dir.is_dir():
            continue
        run = _read_json(run_dir / "run.json")
        run_id = str(run.get("run_id") or run_dir.name)
        if run_id in exclude:
            continue
        if run.get("kind") != kind:
            continue
        if work_id is not None and run.get("work_id") != work_id:
            continue
        candidates.append((str(run.get("created_at") or ""), run_id))
    candidates.sort()
    return candidates[-1][1] if candidates else ""


def _wait_for_http_json(url: str, *, timeout: float, description: str) -> dict[str, Any]:
    payload: dict[str, Any] = {}

    def _probe() -> bool:
        nonlocal payload
        try:
            payload = _http_get_json(url)
            return True
        except Exception:
            return False

    _wait_until(_probe, timeout=timeout, interval=0.5, description=description)
    return payload


def _init_git_repo(project_dir: Path) -> None:
    _run_command(["git", "init"], cwd=project_dir, timeout=20)
    _run_command(["git", "config", "user.email", "selftest@example.com"], cwd=project_dir, timeout=20)
    _run_command(["git", "config", "user.name", "Thoth Selftest"], cwd=project_dir, timeout=20)


def _seed_task(project_dir: Path, *, work_id: str = "task-1") -> None:
    upsert_decision(
        project_dir,
        {
            "schema_version": 1,
            "kind": "decision",
            "decision_id": "DEC-selftest-runtime",
            "scope_id": "frontend-runtime",
            "question": "Which runtime validation method should be executed for selftest?",
            "candidate_method_ids": ["real-cli-runtime-check"],
            "selected_values": {"candidate_method_id": "real-cli-runtime-check"},
            "status": "frozen",
            "unresolved_gaps": [],
            "created_at": utc_now(),
            "updated_at": utc_now(),
        },
    )
    upsert_work_item(
        project_dir,
        {
            "schema_version": 1,
            "kind": "work_item",
            "work_id": work_id,
            "direction": "frontend",
            "module": "f1",
            "title": "Dashboard lifecycle validation",
            "status": "ready",
            "work_kind": "execution",
            "runnable": True,
            "goal": "Verify that runtime state remains inspectable under real process execution.",
            "context": "frontend-runtime",
            "constraints": ["selftest-temp-project"],
            "execution_plan": [
                "Initialize a temp Thoth project.",
                "Start detached run and loop lifecycles.",
                "Observe dashboard runtime freshness and hook behavior.",
            ],
            "eval_contract": {
                "entrypoint": {"command": "python -m thoth.selftest --case run.phase_contract"},
                "primary_metric": {"name": "selftest_checks_passed", "direction": "gte", "threshold": 1},
                "failure_classes": ["runtime_unstable", "dashboard_drift", "hook_failure"],
                "validate_output_schema": default_validate_output_schema(),
            },
            "runtime_policy": {"loop": {"max_iterations": 10, "max_runtime_seconds": 28800}},
            "decisions": ["DEC-selftest-runtime"],
            "missing_questions": [],
            "created_at": utc_now(),
            "updated_at": utc_now(),
        },
    )
    compile_task_authority(project_dir)


def _set_dashboard_port(project_dir: Path, port: int) -> None:
    manifest_path = project_dir / ".thoth" / "docs" / "project.json"
    manifest = load_project_manifest(project_dir)
    manifest.setdefault("dashboard", {})
    manifest["dashboard"]["port"] = port
    _write_json(manifest_path, manifest)
    store = Store(project_dir)
    project = store.read("project", "project")
    if project:
        payload = dict(project.get("payload") if isinstance(project.get("payload"), dict) else {})
        payload.setdefault("dashboard", {})
        payload["dashboard"]["port"] = port
        store.update(
            "project",
            "project",
            expected_revision=int(project.get("revision", 0)),
            updates={"payload": payload},
            history_summary=f"dashboard port -> {port}",
            source="selftest",
        )


def _snapshot_runtime(recorder: Recorder, project_dir: Path, label: str) -> list[str]:
    artifacts: list[str] = []
    for rel in (".thoth", ".agent-os", ".codex"):
        path = project_dir / rel
        if not path.exists():
            continue
        target = recorder.artifact_dir / "snapshots" / _safe_name(label) / rel.replace("/", "_")
        if path.is_dir():
            shutil.copytree(path, target, dirs_exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        artifacts.append(str(target))
    return artifacts


def _run_thoth(project_dir: Path, *args: str, timeout: float = 120, env: dict[str, str] | None = None) -> CommandResult:
    merged_env = dict(env or {})
    existing_pythonpath = os.environ.get("PYTHONPATH", "")
    merged_env["PYTHONPATH"] = str(ROOT) if not existing_pythonpath else f"{ROOT}:{existing_pythonpath}"
    return _run_command([PYTHON, "-m", "thoth.cli", *args], cwd=project_dir, env=merged_env, timeout=timeout)


def _state_payload(project_dir: Path, run_id: str) -> dict[str, Any]:
    return _read_json(project_dir / ".thoth" / "runs" / run_id / "state.json")


def _heartbeat_payload(project_dir: Path, run_id: str) -> dict[str, Any]:
    state = _read_json(project_dir / ".thoth" / "runs" / run_id / "state.json")
    if state.get("last_heartbeat_at"):
        return {
            "last_heartbeat_at": state.get("last_heartbeat_at"),
            "updated_at": state.get("updated_at"),
        }
    return _read_json(project_dir / ".thoth" / "runs" / run_id / "heartbeat.json")


def _run_payload(project_dir: Path, run_id: str) -> dict[str, Any]:
    return _read_json(project_dir / ".thoth" / "runs" / run_id / "run.json")


def _result_payload(project_dir: Path, run_id: str) -> dict[str, Any]:
    return _read_json(project_dir / ".thoth" / "runs" / run_id / "result.json")


def _artifacts_payload(project_dir: Path, run_id: str) -> dict[str, Any]:
    return _read_json(project_dir / ".thoth" / "runs" / run_id / "artifacts.json")


def _events_payload(project_dir: Path, run_id: str) -> list[dict[str, Any]]:
    path = project_dir / ".thoth" / "runs" / run_id / "events.jsonl"
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            events.append(payload)
    return events


_FORBIDDEN_HOST_REAL_PHRASES = (
    "fallback",
    "degraded",
    "official validator",
    "validator skipped",
    "substitute implementation",
)


def _host_run_uses_forbidden_fallback(acceptance: dict[str, Any], events: list[dict[str, Any]]) -> bool:
    texts: list[str] = []
    summary = acceptance.get("summary")
    if isinstance(summary, str) and summary.strip():
        texts.append(summary)
    for check in acceptance.get("checks", []):
        if not isinstance(check, dict):
            continue
        for key in ("name", "detail", "summary"):
            value = check.get(key)
            if isinstance(value, str) and value.strip():
                texts.append(value)
    for event in events:
        message = event.get("message")
        if isinstance(message, str) and message.strip():
            texts.append(message)
    lowered = "\n".join(texts).lower()
    return any(phrase in lowered for phrase in _FORBIDDEN_HOST_REAL_PHRASES)


def _review_findings_payload(project_dir: Path, run_id: str, acceptance: dict[str, Any]) -> list[dict[str, Any]]:
    findings = acceptance.get("result", {}).get("findings")
    if isinstance(findings, list) and findings:
        return [item for item in findings if isinstance(item, dict)]
    artifacts = _artifacts_payload(project_dir, run_id).get("artifacts", [])
    if isinstance(artifacts, list):
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                continue
            label = str(artifact.get("label") or "")
            relpath = str(artifact.get("path") or "")
            if label != "review-findings" or not relpath:
                continue
            payload = _read_json(project_dir / relpath)
            extracted = payload.get("findings") if isinstance(payload, dict) else None
            if isinstance(extracted, list) and extracted:
                return [item for item in extracted if isinstance(item, dict)]
    for event in _events_payload(project_dir, run_id):
        message = event.get("message")
        if not isinstance(message, str) or not message.strip():
            continue
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            continue
        extracted = payload.get("findings") if isinstance(payload, dict) else None
        if isinstance(extracted, list) and extracted:
            return [item for item in extracted if isinstance(item, dict)]
    return []


def _canonical_review_result_payload(project_dir: Path, run_id: str, acceptance: dict[str, Any]) -> dict[str, Any]:
    result_payload = acceptance.get("result")
    summary = result_payload.get("summary") if isinstance(result_payload, dict) else None
    findings = _review_findings_payload(project_dir, run_id, acceptance)
    payload: dict[str, Any] = {}
    if isinstance(summary, str) and summary.strip():
        payload["summary"] = summary.strip()
    if findings:
        payload["findings"] = findings
    return payload

__all__ = [name for name in globals() if not name.startswith("__")]
