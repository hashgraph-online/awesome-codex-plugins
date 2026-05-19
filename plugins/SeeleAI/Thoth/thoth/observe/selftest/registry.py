"""Atomic selftest case registry."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from . import atomic_cases
from .recorder import Recorder


CaseRunner = Callable[[Path, Recorder, dict[str, Any]], None]


@dataclass(frozen=True)
class SelftestCaseSpec:
    case_id: str
    scope: str
    budget_seconds: float
    requires_host_auth: bool
    required_host: str
    fixture_kind: str
    runner: CaseRunner
    tags: tuple[str, ...]


_REPO_CASES: tuple[SelftestCaseSpec, ...] = (
    SelftestCaseSpec("discuss.subtree.close", "repo_local", 20.0, False, "none", "probe_repo", atomic_cases.case_plan_discuss_compile, ("discuss", "subtree")),
    SelftestCaseSpec("run.phase_contract", "repo_local", 20.0, False, "none", "runtime_repo", atomic_cases.case_runtime_run_live, ("run", "phase")),
    SelftestCaseSpec("run.locked_work", "repo_local", 20.0, False, "none", "runtime_repo", atomic_cases.case_runtime_loop_lease_conflict, ("run", "lock")),
    SelftestCaseSpec("loop.controller", "repo_local", 20.0, False, "none", "runtime_repo", atomic_cases.case_runtime_loop_live, ("loop", "controller")),
    SelftestCaseSpec("orchestration.controller", "repo_local", 20.0, False, "none", "runtime_repo", atomic_cases.case_runtime_loop_live, ("orchestration", "controller")),
    SelftestCaseSpec("auto.queue", "repo_local", 20.0, False, "none", "runtime_repo", atomic_cases.case_runtime_loop_sleep, ("auto", "queue")),
    SelftestCaseSpec("observe.object_graph", "repo_local", 75.0, False, "none", "runtime_repo", atomic_cases.case_observe_dashboard, ("observe", "object_graph")),
    SelftestCaseSpec("plan.discuss.compile", "repo_local", 20.0, False, "none", "probe_repo", atomic_cases.case_plan_discuss_compile, ("plan", "compile")),
    SelftestCaseSpec("runtime.run.live", "repo_local", 20.0, False, "none", "runtime_repo", atomic_cases.case_runtime_run_live, ("runtime", "run", "live")),
    SelftestCaseSpec("runtime.run.sleep", "repo_local", 20.0, False, "none", "runtime_repo", atomic_cases.case_runtime_run_sleep, ("runtime", "run", "sleep")),
    SelftestCaseSpec("runtime.run.validate_fail", "repo_local", 20.0, False, "none", "runtime_repo", atomic_cases.case_runtime_run_validate_fail, ("runtime", "run", "reflect")),
    SelftestCaseSpec("runtime.loop.live", "repo_local", 20.0, False, "none", "runtime_repo", atomic_cases.case_runtime_loop_live, ("runtime", "loop", "live")),
    SelftestCaseSpec("runtime.loop.sleep", "repo_local", 20.0, False, "none", "runtime_repo", atomic_cases.case_runtime_loop_sleep, ("runtime", "loop", "sleep")),
    SelftestCaseSpec("runtime.loop.lease_conflict", "repo_local", 20.0, False, "none", "runtime_repo", atomic_cases.case_runtime_loop_lease_conflict, ("runtime", "loop", "lease")),
    SelftestCaseSpec("review.exact_match", "repo_local", 20.0, False, "none", "probe_repo", atomic_cases.case_review_exact_match, ("review", "exact_match")),
    SelftestCaseSpec("observe.dashboard", "repo_local", 75.0, False, "none", "runtime_repo", atomic_cases.case_observe_dashboard, ("observe", "dashboard")),
    SelftestCaseSpec("hooks.codex", "repo_local", 20.0, False, "none", "runtime_repo", atomic_cases.case_hooks_codex, ("hooks", "codex")),
)


_HOST_CASES: tuple[SelftestCaseSpec, ...] = (
    SelftestCaseSpec("surface.codex.init", "host_surface", 90.0, True, "codex", "host_probe", atomic_cases.case_surface_codex_init, ("surface", "codex", "init")),
    SelftestCaseSpec("surface.codex.status", "host_surface", 60.0, True, "codex", "host_probe", atomic_cases.case_surface_codex_status, ("surface", "codex", "status")),
    SelftestCaseSpec("surface.codex.doctor", "host_surface", 60.0, True, "codex", "host_probe", atomic_cases.case_surface_codex_doctor, ("surface", "codex", "doctor")),
    SelftestCaseSpec("surface.codex.discuss.compile", "host_surface", 150.0, True, "codex", "host_probe", atomic_cases.case_surface_codex_discuss_compile, ("surface", "codex", "discuss")),
    SelftestCaseSpec("surface.codex.run.live_prepare", "host_surface", 120.0, True, "codex", "host_probe", atomic_cases.case_surface_codex_run_live_prepare, ("surface", "codex", "run", "live")),
    SelftestCaseSpec("surface.codex.run.sleep_prepare", "host_surface", 90.0, True, "codex", "host_probe", atomic_cases.case_surface_codex_run_sleep_prepare, ("surface", "codex", "run", "sleep")),
    SelftestCaseSpec("surface.codex.run.watch", "host_surface", 120.0, True, "codex", "host_probe", atomic_cases.case_surface_codex_run_watch, ("surface", "codex", "watch")),
    SelftestCaseSpec("surface.codex.run.stop", "host_surface", 120.0, True, "codex", "host_probe", atomic_cases.case_surface_codex_run_stop, ("surface", "codex", "stop")),
    SelftestCaseSpec("surface.codex.review.exact_match", "host_surface", 150.0, True, "codex", "host_probe", atomic_cases.case_surface_codex_review_exact_match, ("surface", "codex", "review")),
    SelftestCaseSpec("surface.codex.loop.live_prepare", "host_surface", 120.0, True, "codex", "host_probe", atomic_cases.case_surface_codex_loop_live_prepare, ("surface", "codex", "loop", "live")),
    SelftestCaseSpec("surface.codex.loop.sleep_prepare", "host_surface", 90.0, True, "codex", "host_probe", atomic_cases.case_surface_codex_loop_sleep_prepare, ("surface", "codex", "loop", "sleep")),
    SelftestCaseSpec("surface.codex.loop.stop", "host_surface", 120.0, True, "codex", "host_probe", atomic_cases.case_surface_codex_loop_stop, ("surface", "codex", "loop", "stop")),
    SelftestCaseSpec("surface.codex.auto.sleep_prepare", "host_surface", 90.0, True, "codex", "host_probe", atomic_cases.case_surface_codex_auto_sleep_prepare, ("surface", "codex", "auto", "sleep")),
    SelftestCaseSpec("surface.codex.auto.stop", "host_surface", 150.0, True, "codex", "host_probe", atomic_cases.case_surface_codex_auto_stop, ("surface", "codex", "auto", "stop")),
    SelftestCaseSpec("surface.codex.dashboard.start", "host_surface", 90.0, True, "codex", "host_probe", atomic_cases.case_surface_codex_dashboard_start, ("surface", "codex", "dashboard")),
    SelftestCaseSpec("surface.codex.dashboard.stop", "host_surface", 120.0, True, "codex", "host_probe", atomic_cases.case_surface_codex_dashboard_stop, ("surface", "codex", "dashboard")),
    SelftestCaseSpec("surface.codex.init_sync", "host_surface", 60.0, True, "codex", "host_probe", atomic_cases.case_surface_codex_init_sync, ("surface", "codex", "init", "sync")),
    SelftestCaseSpec("surface.claude.init", "host_surface", 25.0, True, "claude", "host_probe", atomic_cases.case_surface_claude_init, ("surface", "claude", "init")),
    SelftestCaseSpec("surface.claude.status", "host_surface", 25.0, True, "claude", "host_probe", atomic_cases.case_surface_claude_status, ("surface", "claude", "status")),
    SelftestCaseSpec("surface.claude.doctor", "host_surface", 25.0, True, "claude", "host_probe", atomic_cases.case_surface_claude_doctor, ("surface", "claude", "doctor")),
    SelftestCaseSpec("surface.claude.discuss.compile", "host_surface", 45.0, True, "claude", "host_probe", atomic_cases.case_surface_claude_discuss_compile, ("surface", "claude", "discuss")),
    SelftestCaseSpec("surface.claude.run.live_prepare", "host_surface", 45.0, True, "claude", "host_probe", atomic_cases.case_surface_claude_run_live_prepare, ("surface", "claude", "run", "live")),
    SelftestCaseSpec("surface.claude.run.sleep_prepare", "host_surface", 45.0, True, "claude", "host_probe", atomic_cases.case_surface_claude_run_sleep_prepare, ("surface", "claude", "run", "sleep")),
    SelftestCaseSpec("surface.claude.run.watch", "host_surface", 45.0, True, "claude", "host_probe", atomic_cases.case_surface_claude_run_watch, ("surface", "claude", "watch")),
    SelftestCaseSpec("surface.claude.run.stop", "host_surface", 45.0, True, "claude", "host_probe", atomic_cases.case_surface_claude_run_stop, ("surface", "claude", "stop")),
    SelftestCaseSpec("surface.claude.review.exact_match", "host_surface", 45.0, True, "claude", "host_probe", atomic_cases.case_surface_claude_review_exact_match, ("surface", "claude", "review")),
    SelftestCaseSpec("surface.claude.loop.live_prepare", "host_surface", 45.0, True, "claude", "host_probe", atomic_cases.case_surface_claude_loop_live_prepare, ("surface", "claude", "loop", "live")),
    SelftestCaseSpec("surface.claude.loop.sleep_prepare", "host_surface", 45.0, True, "claude", "host_probe", atomic_cases.case_surface_claude_loop_sleep_prepare, ("surface", "claude", "loop", "sleep")),
    SelftestCaseSpec("surface.claude.loop.stop", "host_surface", 45.0, True, "claude", "host_probe", atomic_cases.case_surface_claude_loop_stop, ("surface", "claude", "loop", "stop")),
    SelftestCaseSpec("surface.claude.auto.sleep_prepare", "host_surface", 45.0, True, "claude", "host_probe", atomic_cases.case_surface_claude_auto_sleep_prepare, ("surface", "claude", "auto", "sleep")),
    SelftestCaseSpec("surface.claude.auto.stop", "host_surface", 90.0, True, "claude", "host_probe", atomic_cases.case_surface_claude_auto_stop, ("surface", "claude", "auto", "stop")),
    SelftestCaseSpec("surface.claude.dashboard.start", "host_surface", 45.0, True, "claude", "host_probe", atomic_cases.case_surface_claude_dashboard_start, ("surface", "claude", "dashboard")),
    SelftestCaseSpec("surface.claude.dashboard.stop", "host_surface", 45.0, True, "claude", "host_probe", atomic_cases.case_surface_claude_dashboard_stop, ("surface", "claude", "dashboard")),
    SelftestCaseSpec("surface.claude.init_sync", "host_surface", 25.0, True, "claude", "host_probe", atomic_cases.case_surface_claude_init_sync, ("surface", "claude", "init", "sync")),
)


CASE_REGISTRY: tuple[SelftestCaseSpec, ...] = _REPO_CASES + _HOST_CASES


def all_case_specs() -> tuple[SelftestCaseSpec, ...]:
    return CASE_REGISTRY


def case_registry_map() -> dict[str, SelftestCaseSpec]:
    mapping = {spec.case_id: spec for spec in CASE_REGISTRY}
    if len(mapping) != len(CASE_REGISTRY):
        raise ValueError("Duplicate selftest case ids detected in registry.")
    return mapping


def resolve_case_specs(case_ids: list[str]) -> list[SelftestCaseSpec]:
    registry = case_registry_map()
    resolved: list[SelftestCaseSpec] = []
    seen: set[str] = set()
    missing: list[str] = []
    for case_id in case_ids:
        normalized = str(case_id).strip()
        if not normalized:
            continue
        if normalized in seen:
            raise ValueError(f"Duplicate selftest case requested: {normalized}")
        seen.add(normalized)
        spec = registry.get(normalized)
        if spec is None:
            missing.append(normalized)
            continue
        resolved.append(spec)
    if missing:
        raise ValueError(f"Unknown selftest case(s): {', '.join(missing)}")
    return resolved


def recommended_usage() -> str:
    return "python -m thoth.selftest --case discuss.subtree.close --case run.phase_contract --case observe.object_graph"


def available_case_lines() -> list[str]:
    return [f"- {spec.case_id} [{spec.scope}; host={spec.required_host}; budget={int(spec.budget_seconds)}s]" for spec in CASE_REGISTRY]


__all__ = [
    "CASE_REGISTRY",
    "SelftestCaseSpec",
    "all_case_specs",
    "available_case_lines",
    "case_registry_map",
    "recommended_usage",
    "resolve_case_specs",
]
