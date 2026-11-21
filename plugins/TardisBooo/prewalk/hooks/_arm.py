#!/usr/bin/env python3
"""Skill-side helper for the Codex host: arm, status, disarm, doctor.

Invoked by the ``$prewalk`` skills through the wrapper scripts:

  _arm.py arm    <session_id> [--preset NAME] [--fast] [task ...]
  _arm.py status <session_id>
  _arm.py disarm <session_id>
  _arm.py doctor <session_id> [--schema-fields=a,b,...]

Presets are read from ``$CODEX_HOME/prewalk-presets.toml``; durable state is
written to ``$CODEX_HOME/prewalk-state.json`` (the same store the hook
scripts use). ``arm`` prints the frontier briefing plus the resolved model
pair so the skill can surface it verbatim.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

import _engine  # noqa: F401  (locates prewalk_engine)
import _common  # type: ignore[import-not-found]  # noqa: E402
import prewalk_engine as core  # noqa: E402


# ---------------------------------------------------------------- arm --------


def _parse_args(rest: list[str]) -> tuple[str | None, bool]:
    """Split leading options off the front of a freeform ``arm`` command line.

    Skills deliver ``$ARGUMENTS`` as one quoted blob; humans may pass separate
    argv tokens. Both forms are accepted here, and option parsing stops at the
    first bare token — everything after that is task text.
    """
    tokens = shlex.split(rest[0]) if len(rest) == 1 else rest
    auto_swap = False
    preset: str | None = None
    index = 0
    while index < len(tokens):
        tok = tokens[index]
        if tok == "--":
            break
        if tok in ("--no-pause", "--fast"):
            auto_swap = True
        elif tok == "--preset":
            if index + 1 >= len(tokens):
                raise ValueError("--preset requires a name")
            index += 1
            preset = tokens[index]
        elif tok.startswith("--preset="):
            preset = tok.partition("=")[2]
            if not preset:
                raise ValueError("--preset requires a name")
        else:
            break
        index += 1
    return preset, auto_swap


def cmd_arm(session_id: str, rest: list[str]) -> int:
    session_id = _common.resolve_session_id(session_id)
    if not session_id:
        print("prewalk: cannot arm — could not determine the session id. "
              "Pass it explicitly: _arm.py arm <session_id> ...",
              file=sys.stderr)
        return 1
    try:
        preset_name, auto_swap = _parse_args(rest)
    except (ValueError, shlex.Error) as exc:
        print(f"prewalk: invalid arm arguments: {exc}", file=sys.stderr)
        return 2

    # No user presets on disk? Warn and continue with a sane built-in pair
    # rather than refusing to arm — the run is still useful without routing.
    presets_path = _common.presets_file()
    presets = core.load_presets_toml(presets_path)
    if not presets:
        print(
            "prewalk: no presets found at " + presets_path + ". Copy "
            "hosts/codex/presets.example.toml there first. Falling back to built-in defaults.",
            file=sys.stderr,
        )
        preset = core.Preset(
            name="default",
            executor_model="gpt-5.6-terra",
            description="built-in fallback",
            max_todos=core.DEFAULT_MAX_TODOS,
        )
    else:
        name = preset_name or core.default_preset_toml(presets_path)
        preset = presets.get(name)
        if preset is None:
            available = ", ".join(sorted(presets))
            print(
                f"prewalk: unknown preset {name!r}; available presets: {available}.",
                file=sys.stderr,
            )
            return 2

    try:
        core.start_v4_run(
            _common.store_file(), session_id, _common.workspace_root(), "codex", preset, fast_mode=auto_swap
        )
    except OSError as exc:
        print(
            "prewalk: cannot arm because the durable state store is not writable: "
            f"{_common.store_file()} ({exc}).",
            file=sys.stderr,
        )
        print(
            "Grant this command write access outside the workspace sandbox, or set "
            "PREWALK_STATE_FILE to one absolute path inherited by Codex and all plugin hooks. "
            "No Prewalk checkpoint was created.",
            file=sys.stderr,
        )
        return 1
    print(f"prewalk ARMED  [{preset.name}]  auto_swap={auto_swap}")
    print("  planner : active root session (Prewalk does not change it)")
    print(f"  handoff : {preset.handoff_mode}  require_model_routing={preset.require_model_routing}")
    print(core.format_capability_report(core.evaluate_capabilities(preset, "codex")))
    print()
    print("Continue in this active session and follow $prewalk:prewalk.")
    return 0


# ------------------------------------------------------------- doctor -------


MIN_CODEX_VERSION = (0, 146, 0)


def _cli_executable(name: str) -> str:
    """Resolve npm command shims on Windows without requiring a shell."""
    candidates = (f"{name}.cmd", f"{name}.exe", name) if os.name == "nt" else (name,)
    return next((path for item in candidates if (path := shutil.which(item))), name)


def _codex_version() -> tuple[tuple[int, int, int] | None, str]:
    """Ask the ``codex`` binary for its version, tolerating any output shape."""
    try:
        result = subprocess.run(
            [_cli_executable("codex"), "--version"],
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None, "not found"
    lines = (result.stdout or result.stderr or "").strip().splitlines()
    detail = lines[-1] if lines else f"exit {result.returncode} with no output"
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", detail)
    return (tuple(map(int, match.groups())) if match else None), detail


def _codex_catalog_ids(payload: object) -> set[str]:
    """Pull model slugs out of the native ``codex debug models`` response."""
    if not isinstance(payload, dict) or not isinstance(payload.get("models"), list):
        raise ValueError("expected an object containing a models array")
    model_ids = {
        model["slug"].strip()
        for model in payload["models"]
        if isinstance(model, dict)
        and isinstance(model.get("slug"), str)
        and model["slug"].strip()
    }
    if not model_ids:
        raise ValueError("models array contains no model slugs")
    return model_ids


def _codex_model_catalog() -> tuple[set[str] | None, str]:
    """Return the live model-id set, or None plus a human reason on failure."""
    try:
        result = subprocess.run(
            [_cli_executable("codex"), "debug", "models"],
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return None, f"unavailable ({exc})"
    if result.returncode:
        detail = (result.stderr or result.stdout).strip().splitlines()
        return None, detail[-1] if detail else f"exit {result.returncode}"
    try:
        model_ids = _codex_catalog_ids(json.loads(result.stdout or ""))
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        return None, f"invalid response ({exc})"
    return model_ids, f"{len(model_ids)} model(s) from codex debug models"


def cmd_doctor(given_session_id: str, rest: list[str]) -> int:
    failures = 0

    def check(ok: bool, label: str, detail: str = "") -> None:
        nonlocal failures
        print(f"{'PASS' if ok else 'FAIL'}  {label}" + (f": {detail}" if detail else ""))
        failures += 0 if ok else 1

    check(sys.version_info >= (3, 10), "Python", sys.version.split()[0])
    check(core.VERSION == "1.0.9", "shared core", core.VERSION)
    version, version_text = _codex_version()
    check(
        version is not None and version >= MIN_CODEX_VERSION,
        "Codex CLI >= 0.146.0",
        version_text,
    )
    thread_id = os.environ.get("CODEX_THREAD_ID", "").strip()
    resolved = _common.resolve_session_id(given_session_id)
    check(
        bool(resolved),
        "thread identity",
        "CODEX_THREAD_ID is active" if thread_id and resolved else (
            "explicit legacy id accepted" if resolved else
            "missing or mismatched; upgrade Codex and restart the thread"
        ),
    )
    presets_path = Path(_common.presets_file())
    presets = core.load_presets_toml(presets_path)
    if presets_path.is_file():
        check(bool(presets), "preset parse", f"{len(presets)} preset(s) in {presets_path}")
    else:
        print(f"WARN  preset file: {presets_path} is absent; built-in defaults will be used")
    for preset_name, configured in presets.items():
        check(
            bool(configured.executor_model.strip()),
            f"model catalog/config [{preset_name}]",
            configured.executor_model or "missing executor model",
        )
        for warning in configured.deprecation_warnings:
            print(f"WARN  config deprecation [{preset_name}]: {warning}")
    manifest = Path(__file__).resolve().parent / "hooks.json"
    try:
        hooks = json.loads(manifest.read_text(encoding="utf-8"))["hooks"]
        required_events = {"PreToolUse", "PostToolUse", "SubagentStop", "Stop"}
        spawn_matcher = r"^(((functions|collaboration)\.)?spawn_agent|multi_agent_v[0-9]+__spawn_agent)$"
        manifest_ok = (
            required_events.issubset(hooks)
            and [group.get("matcher") for group in hooks["PreToolUse"]] == [spawn_matcher]
            and len(hooks["SubagentStop"]) == 1
        )
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        manifest_ok = False
    check(manifest_ok, "plugin hooks", str(manifest))
    store_ok, store_detail = _common.state_store_access()
    check(store_ok, "state store", store_detail)
    preset = (
        presets.get(core.default_preset_toml(presets_path)) or next(iter(presets.values()))
        if presets else core.Preset("default", "gpt-5.6-terra")
    )
    # Routing needs proof from the *live* spawn_agent schema; the skill passes
    # the current field list through --schema-fields.
    schema_fields = set()
    for argument in rest:
        if argument.startswith("--schema-fields="):
            schema_fields.update(
                item.strip() for item in argument.partition("=")[2].split(",") if item.strip()
            )
    report = core.evaluate_capabilities(preset, "codex", schema_fields=schema_fields)
    print(core.format_capability_report(report))
    if schema_fields:
        check(report.routing_allowed, "live executor routing", report.model_proven)
    else:
        print("WARN  live executor routing: pass the current spawn_agent schema fields to validate it")
    catalog, catalog_detail = _codex_model_catalog()
    if catalog is None:
        print(f"WARN  native model catalog: {catalog_detail}; availability will be validated at launch")
    elif preset.executor_model in catalog:
        print(f"PASS  native model catalog: {preset.executor_model} ({catalog_detail})")
    else:
        print(
            f"WARN  native model catalog: {preset.executor_model} is not listed "
            f"({catalog_detail}); it may require a custom provider"
        )
    return 1 if failures else 0


# --------------------------------------------------------------- main --------


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    sub, session_id = sys.argv[1], sys.argv[2]
    rest = sys.argv[3:]
    if sub == "doctor":
        return cmd_doctor(session_id, rest)
    session_id = _common.resolve_session_id(session_id)
    if not session_id:
        print(
            "prewalk: cannot continue — CODEX_THREAD_ID is missing or conflicts with the supplied id. "
            "Use Codex CLI 0.146.0 or newer, or pass an explicit id on a legacy CLI.",
            file=sys.stderr,
        )
        return 1
    store = _common.store_file()
    if sub == "arm":
        return cmd_arm(session_id, rest)
    if sub == "status":
        workspace_id = core.workspace_identity(_common.workspace_root())
        core.detect_v4_stale(store, session_id, workspace_id=workspace_id)
        loaded = core.load_v4_state(
            store, session_id, workspace_id=workspace_id
        )
        print(core.format_v4_status(loaded, host="codex"))
        return 0
    if sub == "disarm":
        print(core.disarm(store, session_id))
        return 0
    print("unknown subcommand: " + sub, file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"prewalk: operation failed; state not acknowledged: {exc}", file=sys.stderr)
        raise SystemExit(1)
