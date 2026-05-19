"""Targeted pytest manifests and changed-path recommendations for Thoth."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class TargetSpec:
    target_id: str
    selectors: tuple[str, ...]
    recommended_selftest_cases: tuple[str, ...] = ()
    description: str = ""


TARGET_SPECS: dict[str, TargetSpec] = {
    "selftest-core": TargetSpec(
        target_id="selftest-core",
        selectors=("tests/unit/test_selftest_helpers.py", "tests/unit/test_selftest_registry.py"),
        recommended_selftest_cases=(
            "plan.discuss.compile",
            "runtime.run.live",
            "runtime.run.sleep",
            "runtime.run.validate_fail",
            "runtime.loop.live",
            "runtime.loop.sleep",
            "runtime.loop.lease_conflict",
            "review.exact_match",
            "observe.dashboard",
            "hooks.codex",
        ),
        description="Atomic selftest registry, repo-local runtime probes, and host-surface helpers.",
    ),
    "runtime-core": TargetSpec(
        target_id="runtime-core",
        selectors=(
            "tests/unit/test_runtime_protocol.py",
            "tests/unit/test_run_state_machine.py",
            "tests/integration/test_runtime_lifecycle_e2e.py",
        ),
        recommended_selftest_cases=(
            "runtime.run.live",
            "runtime.run.sleep",
            "runtime.run.validate_fail",
            "runtime.loop.live",
            "runtime.loop.sleep",
            "runtime.loop.lease_conflict",
        ),
        description="Durable run/loop controller, ledger, and runtime protocol behavior.",
    ),
    "surface-cli": TargetSpec(
        target_id="surface-cli",
        selectors=(
            "tests/unit/test_cli_surface.py",
            "tests/unit/test_command_spec_generation.py",
        ),
        recommended_selftest_cases=(
            "surface.codex.init",
            "surface.codex.status",
            "surface.codex.doctor",
            "surface.codex.discuss.compile",
            "surface.codex.run.live_prepare",
            "surface.codex.run.sleep_prepare",
            "surface.codex.run.watch",
            "surface.codex.run.stop",
            "surface.codex.review.exact_match",
            "surface.codex.loop.live_prepare",
            "surface.codex.loop.sleep_prepare",
            "surface.codex.loop.stop",
            "surface.codex.auto.sleep_prepare",
            "surface.codex.auto.stop",
            "surface.codex.dashboard.start",
            "surface.codex.dashboard.stop",
            "surface.codex.init_sync",
        ),
        description="Public CLI and generated command surface behavior.",
    ),
    "claude-bridge": TargetSpec(
        target_id="claude-bridge",
        selectors=("tests/unit/test_claude_bridge.py",),
        recommended_selftest_cases=(
            "surface.claude.init",
            "surface.claude.status",
            "surface.claude.doctor",
            "surface.claude.discuss.compile",
            "surface.claude.run.live_prepare",
            "surface.claude.run.sleep_prepare",
            "surface.claude.run.watch",
            "surface.claude.run.stop",
            "surface.claude.review.exact_match",
            "surface.claude.loop.live_prepare",
            "surface.claude.loop.sleep_prepare",
            "surface.claude.loop.stop",
            "surface.claude.auto.sleep_prepare",
            "surface.claude.auto.stop",
            "surface.claude.dashboard.start",
            "surface.claude.dashboard.stop",
            "surface.claude.init_sync",
        ),
        description="Claude bridge surface and slash-command projection behavior.",
    ),
    "dashboard-runtime": TargetSpec(
        target_id="dashboard-runtime",
        selectors=(
            "tests/unit/test_dashboard_runtime_api.py",
            "tests/integration/test_dashboard_api.py",
        ),
        recommended_selftest_cases=("observe.dashboard",),
        description="Dashboard backend read model and runtime status views.",
    ),
    "init-workflow": TargetSpec(
        target_id="init-workflow",
        selectors=(
            "tests/unit/test_init.py",
            "tests/integration/test_init_workflow.py",
        ),
        recommended_selftest_cases=(
            "surface.codex.init",
            "surface.claude.init",
        ),
        description="Audit-first init/adopt workflow and generated repo scaffolding.",
    ),
    "plugin-surface": TargetSpec(
        target_id="plugin-surface",
        selectors=("tests/unit/test_plugin_surface.py",),
        recommended_selftest_cases=(
            "surface.codex.init_sync",
            "surface.claude.init_sync",
        ),
        description="Plugin install surface and generated host entrypoint artifacts.",
    ),
    "observe-read-model": TargetSpec(
        target_id="observe-read-model",
        selectors=(
            "tests/unit/test_status.py",
            "tests/unit/test_report.py",
            "tests/unit/test_data_loader.py",
            "tests/unit/test_runtime_loader.py",
        ),
        recommended_selftest_cases=("observe.dashboard",),
        description="Status/report/read-model derivation logic.",
    ),
}


PATH_TARGET_HINTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("thoth/observe/selftest/", ("selftest-core", "runtime-core", "surface-cli", "claude-bridge")),
    ("thoth/run/", ("runtime-core", "selftest-core")),
    ("thoth/surface/", ("surface-cli", "claude-bridge")),
    ("thoth/projections.py", ("surface-cli", "claude-bridge", "selftest-core")),
    ("thoth/prompt_specs.py", ("surface-cli", "claude-bridge", "selftest-core")),
    ("thoth/prompt_validators.py", ("runtime-core", "selftest-core")),
    ("thoth/init/", ("init-workflow", "plugin-surface")),
    ("thoth/observe/dashboard.py", ("dashboard-runtime", "observe-read-model")),
    ("thoth/observe/read_model.py", ("dashboard-runtime", "observe-read-model")),
    ("templates/dashboard/", ("dashboard-runtime", "observe-read-model")),
    ("tests/conftest.py", ("selftest-core",)),
    ("thoth/test_targets.py", ("selftest-core",)),
    ("scripts/recommend_tests.py", ("selftest-core",)),
)


def _normalize_repo_path(path: str | Path) -> str:
    raw = str(path).replace("\\", "/").strip()
    if not raw:
        return ""
    candidate = Path(raw)
    if candidate.is_absolute():
        try:
            raw = candidate.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
        except ValueError:
            raw = candidate.name
    while raw.startswith("./"):
        raw = raw[2:]
    return raw


def known_target_ids() -> tuple[str, ...]:
    return tuple(TARGET_SPECS.keys())


def resolve_target_specs(target_ids: Iterable[str]) -> list[TargetSpec]:
    resolved: list[TargetSpec] = []
    missing: list[str] = []
    seen: set[str] = set()
    for target_id in target_ids:
        normalized = str(target_id).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        spec = TARGET_SPECS.get(normalized)
        if spec is None:
            missing.append(normalized)
            continue
        resolved.append(spec)
    if missing:
        raise ValueError(f"Unknown Thoth test target(s): {', '.join(missing)}")
    return resolved


def selectors_for_targets(target_ids: Iterable[str]) -> tuple[str, ...]:
    selectors: list[str] = []
    seen: set[str] = set()
    for spec in resolve_target_specs(target_ids):
        for selector in spec.selectors:
            if selector in seen:
                continue
            seen.add(selector)
            selectors.append(selector)
    return tuple(selectors)


def recommended_targets_for_paths(paths: Iterable[str | Path]) -> list[str]:
    matches: list[str] = []
    seen: set[str] = set()
    normalized_paths = [_normalize_repo_path(path) for path in paths]
    for path in normalized_paths:
        if not path:
            continue
        for prefix, target_ids in PATH_TARGET_HINTS:
            if path == prefix or path.startswith(prefix):
                for target_id in target_ids:
                    if target_id in seen:
                        continue
                    seen.add(target_id)
                    matches.append(target_id)
    return matches


def recommended_selftest_cases_for_paths(paths: Iterable[str | Path]) -> list[str]:
    cases: list[str] = []
    seen: set[str] = set()
    for target_id in recommended_targets_for_paths(paths):
        for case_id in TARGET_SPECS[target_id].recommended_selftest_cases:
            if case_id in seen:
                continue
            seen.add(case_id)
            cases.append(case_id)
    return cases


def build_pytest_command(target_ids: Iterable[str]) -> str:
    specs = resolve_target_specs(target_ids)
    if not specs:
        return ""
    argv = ["python", "-m", "pytest", "-q"]
    for spec in specs:
        argv.extend(["--thoth-target", spec.target_id])
    return " ".join(argv)


def build_selftest_command(case_ids: Iterable[str]) -> str:
    normalized = [str(case_id).strip() for case_id in case_ids if str(case_id).strip()]
    if not normalized:
        return ""
    argv = ["python", "-m", "thoth.selftest"]
    for case_id in normalized:
        argv.extend(["--case", case_id])
    return " ".join(argv)


__all__ = [
    "PATH_TARGET_HINTS",
    "REPO_ROOT",
    "TARGET_SPECS",
    "TargetSpec",
    "build_pytest_command",
    "build_selftest_command",
    "known_target_ids",
    "recommended_selftest_cases_for_paths",
    "recommended_targets_for_paths",
    "resolve_target_specs",
    "selectors_for_targets",
]
