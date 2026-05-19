"""Claude custom-command bridge for executing the repo-local Thoth CLI.

This bridge is used by generated Claude `/thoth:*` command surfaces. The
plugin executes it via skill shell preprocessing so the real repo-local CLI
runs before Claude sees the command body. Claude then summarizes the structured
result instead of improvising a parallel implementation.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _trim(text: str, *, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 15] + "\n...[truncated]\n"


def _event_log_path(project_root: Path) -> Path:
    return project_root / ".thoth" / "derived" / "host-bridges" / "claude-command-events.jsonl"


def _append_event(project_root: Path, payload: dict[str, Any]) -> None:
    if not (project_root / ".thoth").exists():
        return
    path = _event_log_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _canonical_checks(project_root: Path, command_id: str, command_args: list[str], stdout: str) -> dict[str, Any]:
    project_object = project_root / ".thoth" / "objects" / "project" / "project.json"
    project_manifest = project_root / ".thoth" / "docs" / "project.json"
    instructions = project_root / ".thoth" / "docs" / "agent-entry.md"
    source_map = project_root / ".thoth" / "docs" / "source-map.json"

    checks: dict[str, Any] = {
        "project_object_exists": project_object.exists(),
        "project_manifest_exists": project_manifest.exists(),
        "instructions_exists": instructions.exists(),
        "source_map_exists": source_map.exists(),
    }

    if command_id in {"run", "loop", "review"} and not any(flag in command_args for flag in ("--attach", "--watch", "--stop")):
        packet = _parse_packet(stdout)
        candidate = str(packet.get("run_id") or "").strip()
        if not candidate:
            candidate = _parse_runtime_run_id(stdout)
        checks["run_id"] = candidate
        checks["packet_kind"] = packet.get("packet_kind")
        checks["dispatch_mode"] = packet.get("dispatch_mode")
        checks["run_ledger_exists"] = bool(candidate) and (project_root / ".thoth" / "runs" / candidate / "run.json").exists()
        checks["packet_exists"] = bool(candidate) and (project_root / ".thoth" / "runs" / candidate / "packet.json").exists()
        checks["runtime_event_stream"] = _has_runtime_events(stdout)

    return checks


def _parse_packet(stdout: str) -> dict[str, Any]:
    text = stdout.strip()
    if not text.startswith("{"):
        return {}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    body = payload.get("body")
    if isinstance(body, dict):
        packet = body.get("packet")
        if isinstance(packet, dict):
            return packet
    return payload


def _has_runtime_events(stdout: str) -> bool:
    return any('"type":"thoth.' in line or '"type": "thoth.' in line for line in stdout.splitlines())


def _parse_runtime_run_id(stdout: str) -> str:
    for raw in stdout.splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and str(payload.get("type") or "").startswith("thoth."):
            run_id = payload.get("run_id")
            if isinstance(run_id, str) and run_id.strip():
                return run_id.strip()
    return ""


def _bridge_success(command_id: str, returncode: int, checks: dict[str, Any]) -> bool:
    if returncode != 0:
        return False
    if command_id in {"init", "sync"}:
        return bool(
            checks.get("project_object_exists")
            and checks.get("project_manifest_exists")
            and checks.get("instructions_exists")
            and checks.get("source_map_exists")
        )
    if command_id == "status":
        return bool(checks.get("project_object_exists") or checks.get("project_manifest_exists"))
    if command_id in {"run", "loop", "review"} and "run_ledger_exists" in checks:
        return bool(checks.get("run_ledger_exists") and (checks.get("packet_exists") or checks.get("runtime_event_stream")))
    return True


def _rewrite_review_prepare_args(command_args: list[str]) -> list[str]:
    rewritten: list[str] = []
    target_parts: list[str] = []
    expects_value = {"--goal", "--target", "--work-id", "--host", "--executor"}
    idx = 0
    while idx < len(command_args):
        token = command_args[idx]
        if token in expects_value:
            rewritten.append(token)
            if idx + 1 < len(command_args):
                rewritten.append(command_args[idx + 1])
            idx += 2
            continue
        if token.startswith("--"):
            rewritten.append(token)
            idx += 1
            continue
        target_parts.append(token)
        idx += 1
    has_explicit_target = any(flag in rewritten for flag in ("--target", "--goal"))
    if target_parts and not has_explicit_target:
        rewritten.extend(["--target", " ".join(target_parts)])
    return rewritten


def _rewrite_run_loop_prepare_args(command_args: list[str]) -> list[str]:
    rewritten: list[str] = []
    prompt_parts: list[str] = []
    expects_value = {"--goal", "--work-id", "--host", "--executor"}
    idx = 0
    while idx < len(command_args):
        token = command_args[idx]
        if token in expects_value:
            rewritten.append(token)
            if idx + 1 < len(command_args):
                rewritten.append(command_args[idx + 1])
            idx += 2
            continue
        if token.startswith("--"):
            rewritten.append(token)
            idx += 1
            continue
        prompt_parts.append(token)
        idx += 1
    has_goal = "--goal" in rewritten
    has_work_id = "--work-id" in rewritten
    if prompt_parts and not has_goal and not has_work_id:
        rewritten.extend(["--goal", " ".join(prompt_parts)])
    return rewritten


def _expand_bridge_args(command_id: str, command_args: list[str]) -> list[str]:
    if command_id != "discuss":
        return command_args
    if len(command_args) >= 2 and command_args[0] == "--thoth-arguments-file":
        path = Path(command_args[1])
        content = path.read_text(encoding="utf-8")
        return [content.rstrip("\n")]
    return command_args


def run_bridge(command_id: str, command_args: list[str], *, project_root: Path | None = None) -> dict[str, Any]:
    project_root = (project_root or Path.cwd()).resolve()
    plugin_root = Path(os.environ.get("THOTH_CLAUDE_PLUGIN_ROOT") or Path(__file__).resolve().parents[3]).resolve()
    cli_entry = plugin_root / "scripts" / "thoth-cli-entry.py"

    env = dict(os.environ)
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(plugin_root) if not existing_pythonpath else f"{plugin_root}:{existing_pythonpath}"
    env["THOTH_CLAUDE_BRIDGE"] = "1"

    actual_command = command_id
    command_args = _expand_bridge_args(command_id, list(command_args))
    actual_args = list(command_args)
    if command_id == "review" and not any(flag in command_args for flag in ("--attach", "--watch", "--stop")):
        actual_command = "prepare"
        prepare_args = _rewrite_review_prepare_args(command_args)
        actual_args = ["--command-id", command_id, *prepare_args]
    elif command_id == "auto" and not any(flag in command_args for flag in ("--watch", "--stop", "--sleep", "--monitor-packet")):
        actual_args = [*command_args, "--monitor-packet"]
    argv = [sys.executable, str(cli_entry), actual_command, *actual_args]
    started = time.time()
    result = subprocess.run(
        argv,
        cwd=str(project_root),
        env=env,
        text=True,
        capture_output=True,
    )
    duration = round(time.time() - started, 3)

    checks = _canonical_checks(project_root, command_id, command_args, result.stdout)
    packet = {}
    if command_id in {"run", "loop", "review"} and actual_command == "prepare":
        packet = _parse_packet(result.stdout)
    payload = {
        "schema_version": 1,
        "bridge": "claude-command",
        "executed_at": utc_now(),
        "project_root": str(project_root),
        "plugin_root": str(plugin_root),
        "command_id": command_id,
        "bridged_command_id": actual_command,
        "arguments": command_args,
        "argv": argv,
        "returncode": result.returncode,
        "duration_seconds": duration,
        "bridge_success": _bridge_success(command_id, result.returncode, checks),
        "checks": checks,
        "stdout": _trim(result.stdout.strip()),
        "stderr": _trim(result.stderr.strip()),
    }
    if packet:
        payload["packet"] = packet
    _append_event(project_root, payload)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute the repo-local Thoth CLI for Claude command surfaces.")
    parser.add_argument("command_id")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    ns = parser.parse_args(argv)
    payload = run_bridge(ns.command_id, list(ns.args))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    # Always exit 0 so Claude can read the structured failure payload instead of
    # losing the skill body on preprocessing failure.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
