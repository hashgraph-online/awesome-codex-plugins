"""Atomic selftest CLI orchestration for Thoth."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any

from .capabilities import (
    _ensure_codex_global_hooks,
    _ensure_codex_repo_hooks,
    _ensure_codex_skill_installed,
    _ensure_features_flag,
    _preflight_host_real,
    detect_capabilities,
)
from .fixtures import (
    _expected_host_review_result,
    _host_real_contract_payloads,
    _host_real_decision_payload,
    _host_real_source_fingerprint,
    _host_real_source_unchanged,
)
from .host_common import (
    _codex_completed_command_items,
    _codex_prompt_for_public_command,
    _effective_host_command_timeout,
    _looks_like_transient_host_outage,
    _normalize_codex_public_command_result,
)
from .hard_suite import _verify_host_run_completion
from .model import (
    FIXED_CLAUDE_DIR,
    FIXED_CODEX_DIR,
    FIXED_RUNTIME_DIR,
    HARD_SUITE_MAX_RUNTIME_SECONDS,
    HEAVY_SUITE_MAX_RUNTIME_SECONDS,
    ROOT,
)
from .processes import (
    _SelftestBudget,
    _cap_selftest_timeout,
    _cleanup_legacy_heavy_processes,
    _cleanup_legacy_heavy_tmp,
    _legacy_heavy_process_targets,
    _run_command,
    _terminate_processes,
)
from .recorder import Recorder, _write_json
from .registry import available_case_lines, recommended_usage, resolve_case_specs


INVOCATION_BUDGET_SECONDS = float(os.environ.get("THOTH_SELFTEST_INVOCATION_BUDGET_SECONDS", "180"))


def _case_status(checks: list[dict[str, Any]]) -> str:
    if any(item.get("status") == "failed" for item in checks):
        return "failed"
    if any(item.get("status") == "degraded" for item in checks):
        return "failed"
    return "passed"


def _aggregate_case_artifacts(checks: list[dict[str, Any]]) -> list[str]:
    artifacts: list[str] = []
    seen: set[str] = set()
    for check in checks:
        for artifact in check.get("artifacts", []):
            text = str(artifact)
            if not text or text in seen:
                continue
            seen.add(text)
            artifacts.append(text)
    return artifacts


def _host_requirements_for_cases(case_specs: list[Any]) -> set[str]:
    hosts: set[str] = set()
    for spec in case_specs:
        if spec.required_host in {"claude", "codex"}:
            hosts.add(spec.required_host)
    return hosts


def _render_case_help_message(prefix: str) -> str:
    lines = [prefix, "", "Available cases:"]
    lines.extend(available_case_lines())
    lines.extend(["", "Recommended usage:", f"  {recommended_usage()}"])
    return "\n".join(lines)


def run_selftest(
    *,
    cases: list[str],
    artifact_dir: Path | None,
    json_report: Path | None,
    keep_workdir: bool,
) -> int:
    case_specs = resolve_case_specs(cases)
    capabilities = detect_capabilities()
    base_dir = Path(tempfile.mkdtemp(prefix="thoth-selftest-"))
    work_root = base_dir / "workdirs"
    artifact_root = artifact_dir or (base_dir / "artifacts")
    if artifact_root.exists():
        shutil.rmtree(artifact_root, ignore_errors=True)
    artifact_root.mkdir(parents=True, exist_ok=True)
    if json_report is not None:
        json_report.unlink(missing_ok=True)

    prerequisites = Recorder(artifact_root / "_prerequisites")
    results: dict[str, dict[str, Any]] = {}
    exit_code = 0
    budget_exhausted = False
    selected_hosts = _host_requirements_for_cases(case_specs)

    try:
        with _SelftestBudget(INVOCATION_BUDGET_SECONDS, label="selftest invocation"):
            if selected_hosts:
                _cleanup_legacy_heavy_processes()
                _cleanup_legacy_heavy_tmp(preserve=[FIXED_CLAUDE_DIR, FIXED_CODEX_DIR, FIXED_RUNTIME_DIR])
                _preflight_host_real(capabilities, prerequisites, requested_hosts=selected_hosts)

            for index, spec in enumerate(case_specs):
                case_work_root = work_root / spec.case_id.replace("/", "_")
                case_artifact_dir = artifact_root / spec.case_id
                case_recorder = Recorder(case_artifact_dir)
                started = time.time()
                try:
                    with _SelftestBudget(spec.budget_seconds, label=f"case {spec.case_id}"):
                        spec.runner(case_work_root, case_recorder, capabilities)
                except Exception as exc:
                    error_artifact = case_recorder.write_json(
                        "case-error.json",
                        {
                            "case_id": spec.case_id,
                            "error": str(exc),
                        },
                    )
                    case_recorder.add(spec.case_id, "failed", f"Case aborted: {exc}", [error_artifact])
                    if "Self-test exceeded the active" in str(exc):
                        budget_exhausted = True
                checks = case_recorder.checks_payload()
                results[spec.case_id] = {
                    "status": _case_status(checks),
                    "duration_seconds": round(time.time() - started, 3),
                    "artifacts": _aggregate_case_artifacts(checks),
                    "checks": checks,
                }
                if results[spec.case_id]["status"] == "failed":
                    exit_code = 1
                if budget_exhausted:
                    for remaining in case_specs[index + 1 :]:
                        results[remaining.case_id] = {
                            "status": "failed",
                            "duration_seconds": 0.0,
                            "artifacts": [],
                            "checks": [
                                {
                                    "name": remaining.case_id,
                                    "status": "failed",
                                    "detail": "Case was not run because the 180s invocation budget was exhausted.",
                                    "artifacts": [],
                                }
                            ],
                        }
                    exit_code = 1
                    break
    finally:
        if not keep_workdir:
            shutil.rmtree(base_dir, ignore_errors=True)

    summary = {
        "schema_version": 1,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "overall_status": "failed" if exit_code else "passed",
        "selected_cases": [spec.case_id for spec in case_specs],
        "capabilities": capabilities,
        "prerequisites": prerequisites.checks_payload(),
        "results": results,
    }
    summary_path = json_report or (artifact_root / "summary.json")
    _write_json(summary_path, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if keep_workdir:
        print(f"Kept self-test workdir at {base_dir}")
    return exit_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run atomic Thoth selftest cases.")
    parser.add_argument("--case", action="append", dest="cases", default=[])
    parser.add_argument("--json-report", type=Path)
    parser.add_argument("--artifact-dir", type=Path)
    parser.add_argument("--keep-workdir", action="store_true")
    args = parser.parse_args(argv)
    if not args.cases:
        print(_render_case_help_message("thoth.selftest requires at least one explicit `--case`."), flush=True)
        return 2
    try:
        return run_selftest(
            cases=list(args.cases),
            artifact_dir=args.artifact_dir,
            json_report=args.json_report,
            keep_workdir=bool(args.keep_workdir),
        )
    except ValueError as exc:
        print(_render_case_help_message(str(exc)), flush=True)
        return 2


__all__ = [
    "HARD_SUITE_MAX_RUNTIME_SECONDS",
    "HEAVY_SUITE_MAX_RUNTIME_SECONDS",
    "INVOCATION_BUDGET_SECONDS",
    "ROOT",
    "Recorder",
    "_cap_selftest_timeout",
    "_cleanup_legacy_heavy_tmp",
    "_codex_completed_command_items",
    "_codex_prompt_for_public_command",
    "_effective_host_command_timeout",
    "_ensure_codex_global_hooks",
    "_ensure_codex_skill_installed",
    "_ensure_features_flag",
    "_expected_host_review_result",
    "_host_real_contract_payloads",
    "_host_real_decision_payload",
    "_host_real_source_fingerprint",
    "_host_real_source_unchanged",
    "_legacy_heavy_process_targets",
    "_looks_like_transient_host_outage",
    "_normalize_codex_public_command_result",
    "_preflight_host_real",
    "_run_command",
    "_terminate_processes",
    "_verify_host_run_completion",
    "main",
    "run_selftest",
]


if __name__ == "__main__":
    raise SystemExit(main())
