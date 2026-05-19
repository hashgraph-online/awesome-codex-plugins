from __future__ import annotations

import argparse
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
from thoth.plan.compiler import compile_task_authority
from thoth.run.ledger import complete_run, heartbeat_run
from thoth.selftest_seed import seed_host_real_app

from .model import *
from .recorder import *
from .processes import *

def detect_capabilities() -> dict[str, Any]:
    def tool_path(name: str) -> str | None:
        return shutil.which(name)

    thoth_cli_path = tool_path("thoth")
    capabilities: dict[str, Any] = {
        "python": PYTHON,
        "codex_cli_present": bool(tool_path("codex")),
        "claude_cli_present": bool(tool_path("claude")),
        "thoth_cli_present": bool(thoth_cli_path),
        "thoth_cli_path": thoth_cli_path,
    }

    if capabilities["codex_cli_present"]:
        result = _run_command(["codex", "login", "status"], cwd=ROOT, timeout=20)
        status_text = result.stdout.strip() or result.stderr.strip()
        capabilities["codex_authenticated"] = "logged in" in status_text.lower()
        capabilities["codex_login_status"] = status_text
        features = _run_command(["codex", "features", "list"], cwd=ROOT, timeout=20)
        hooks_line = _codex_hooks_feature_line(features.stdout)
        capabilities["codex_hooks_enabled"] = hooks_line.split()[-1].lower() == "true"
        capabilities["codex_hooks_feature_line"] = hooks_line
        capabilities["codex_features_snapshot"] = features.stdout.strip()
    else:
        capabilities["codex_authenticated"] = False
        capabilities["codex_hooks_enabled"] = False

    if capabilities["claude_cli_present"]:
        result = _run_command(["claude", "auth", "status"], cwd=ROOT, timeout=20)
        status_text = result.stdout.strip() or result.stderr.strip()
        anthropic_env_auth = bool(os.environ.get("ANTHROPIC_AUTH_TOKEN") and os.environ.get("ANTHROPIC_BASE_URL"))
        capabilities["claude_authenticated"] = "\"loggedIn\": true" in status_text or anthropic_env_auth
        capabilities["claude_auth_status"] = status_text
        capabilities["claude_auth_via_env"] = anthropic_env_auth
    else:
        capabilities["claude_authenticated"] = False

    return capabilities


def _codex_hooks_feature_line(features_stdout: str) -> str:
    for line in features_stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("hooks "):
            return stripped
        if stripped.startswith("codex_hooks "):
            return stripped
    return "hooks false"


def _codex_config_path() -> Path:
    return Path.home() / ".codex" / "config.toml"


def _codex_hooks_path() -> Path:
    return Path.home() / ".codex" / "hooks.json"


def _codex_skills_root() -> Path:
    return Path.home() / ".codex" / "skills"


def _path_snapshot(path: Path) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists() or path.is_symlink(),
        "is_symlink": path.is_symlink(),
        "is_dir": path.is_dir(),
        "is_file": path.is_file(),
    }
    try:
        payload["resolved"] = str(path.resolve())
    except OSError:
        payload["resolved"] = None
    return payload


def _ensure_features_flag(content: str, *, key: str, value: str) -> str:
    lines = content.splitlines()
    if not lines:
        return f"[features]\n{key} = {value}\n"
    result: list[str] = []
    in_features = False
    inserted = False
    replaced = False
    for line in lines:
        stripped = line.strip()
        section_match = re.match(r"^\s*\[([^\]]+)\]", line)
        if section_match:
            if in_features and not inserted:
                result.append(f"{key} = {value}")
                inserted = True
            in_features = section_match.group(1).strip() == "features"
            result.append(line)
            continue
        if in_features and stripped.startswith(f"{key} "):
            result.append(f"{key} = {value}")
            inserted = True
            replaced = True
            continue
        result.append(line)
    if in_features and not inserted:
        result.append(f"{key} = {value}")
        inserted = True
    if not inserted and not replaced:
        if result and result[-1].strip():
            result.append("")
        result.extend(["[features]", f"{key} = {value}"])
    return "\n".join(result).rstrip() + "\n"


def _ensure_codex_hooks_enabled(recorder: Recorder) -> dict[str, Any]:
    config_path = _codex_config_path()
    before = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    before_artifact = recorder.write_text("codex-hooks/config.before.toml", before or "__MISSING__\n")
    updated = _ensure_features_flag(before, key="codex_hooks", value="true")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(updated, encoding="utf-8")
    after = config_path.read_text(encoding="utf-8")
    after_artifact = recorder.write_text("codex-hooks/config.after.toml", after)
    features = _run_command(["codex", "features", "list"], cwd=ROOT, timeout=20)
    features_artifact = _save_command(recorder, "codex-features-list", features)
    hooks_line = _codex_hooks_feature_line(features.stdout)
    enabled = hooks_line.split()[-1].lower() == "true"
    payload = {
        "path": str(config_path),
        "before_artifact": before_artifact,
        "after_artifact": after_artifact,
        "effective_enabled": enabled,
        "effective_line": hooks_line,
    }
    recorder.add(
        "preflight.codex_hooks_config",
        "passed" if enabled else "failed",
        "Codex global config was checked and codex_hooks was forced on under [features].",
        [before_artifact, after_artifact, *features_artifact],
    )
    if not enabled:
        raise RuntimeError("codex hooks feature flag is still disabled after config.toml update")
    return payload


def _codex_thoth_plugin_roots() -> list[Path]:
    roots: list[Path] = []
    cache_root = Path.home() / ".codex" / "plugins" / "cache" / "thoth" / "thoth"
    if cache_root.exists():
        roots.extend(sorted((path for path in cache_root.iterdir() if path.is_dir()), key=lambda path: path.stat().st_mtime, reverse=True))
    marketplace_root = Path.home() / ".codex" / ".tmp" / "marketplaces" / "thoth"
    if marketplace_root.exists():
        roots.append(marketplace_root)
    return roots


def _codex_plugin_install_payload(plugin_root: Path | None) -> dict[str, Any]:
    manifest = plugin_root / ".codex-plugin" / "plugin.json" if plugin_root else None
    skill = plugin_root / "plugins" / "thoth" / "skills" / CODEX_SKILL_NAME / "SKILL.md" if plugin_root else None
    legacy_skill = plugin_root / "skills" / CODEX_SKILL_NAME / "SKILL.md" if plugin_root else None
    runtime_entry = plugin_root / "scripts" / "thoth-cli-entry.py" if plugin_root else None
    wrapper = plugin_root / "bin" / "thoth" if plugin_root else None
    payload = {
        "plugin_root": str(plugin_root) if plugin_root else None,
        "manifest": _path_snapshot(manifest) if manifest else None,
        "skill": _path_snapshot(skill) if skill else None,
        "legacy_skill": _path_snapshot(legacy_skill) if legacy_skill else None,
        "runtime_entry": _path_snapshot(runtime_entry) if runtime_entry else None,
        "wrapper": _path_snapshot(wrapper) if wrapper else None,
    }
    return payload


def _codex_plugin_payload_effective(payload: dict[str, Any]) -> bool:
    manifest = payload.get("manifest") if isinstance(payload.get("manifest"), dict) else {}
    skill = payload.get("skill") if isinstance(payload.get("skill"), dict) else {}
    legacy_skill = payload.get("legacy_skill") if isinstance(payload.get("legacy_skill"), dict) else {}
    runtime_entry = payload.get("runtime_entry") if isinstance(payload.get("runtime_entry"), dict) else {}
    return bool(
        payload.get("plugin_root")
        and manifest.get("exists")
        and (skill.get("exists") or legacy_skill.get("exists"))
        and runtime_entry.get("exists")
    )


def _ensure_codex_skill_installed(recorder: Recorder) -> dict[str, Any]:
    payloads = [_codex_plugin_install_payload(root) for root in _codex_thoth_plugin_roots()]
    payload = next((item for item in payloads if _codex_plugin_payload_effective(item)), payloads[0] if payloads else _codex_plugin_install_payload(None))
    artifact = recorder.write_json("codex-plugin/installed-thoth.json", {"selected": payload, "candidates": payloads})
    effective = _codex_plugin_payload_effective(payload)
    recorder.add(
        "preflight.codex_plugin_install",
        "passed" if effective else "failed",
        "Codex installed Thoth plugin was checked without writing global skills or hooks.",
        [artifact],
    )
    if not effective:
        raise RuntimeError("codex installed Thoth plugin does not contain the generated skill and runtime entrypoint")
    return payload


def _ensure_codex_repo_hooks(project_dir: Path, recorder: Recorder) -> dict[str, Any]:
    config_path = project_dir / ".codex" / "config.toml"
    hooks_path = project_dir / ".codex" / "hooks.json"
    before_config = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    before_hooks = hooks_path.read_text(encoding="utf-8") if hooks_path.exists() else ""
    before_config_artifact = recorder.write_text("codex-hooks/project-config.before.toml", before_config or "__MISSING__\n")
    before_hooks_artifact = recorder.write_text("codex-hooks/project-hooks.before.json", before_hooks or "__MISSING__\n")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    updated_config = _ensure_features_flag(before_config, key="hooks", value="true")
    config_path.write_text(updated_config, encoding="utf-8")
    hooks_path.write_text(json.dumps(render_codex_hooks_payload(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    after_config_artifact = recorder.write_text("codex-hooks/project-config.after.toml", config_path.read_text(encoding="utf-8"))
    after_hooks = hooks_path.read_text(encoding="utf-8")
    after_hooks_artifact = recorder.write_text("codex-hooks/project-hooks.after.json", after_hooks)
    effective = "thoth-codex-hook.sh" in after_hooks
    recorder.add(
        "preflight.codex_project_hooks",
        "passed" if effective else "failed",
        "Codex project-local hooks were written under the disposable test repo only.",
        [before_config_artifact, before_hooks_artifact, after_config_artifact, after_hooks_artifact],
    )
    if not effective:
        raise RuntimeError("codex project-local hooks.json does not contain the Thoth hook bridge commands")
    return {
        "config_path": str(config_path),
        "hooks_path": str(hooks_path),
        "effective": effective,
    }


def _ensure_codex_global_skill_installed(recorder: Recorder) -> dict[str, Any]:
    source = ROOT / "plugins" / "thoth" / "skills" / CODEX_SKILL_NAME
    if not source.exists():
        raise RuntimeError(f"missing generated Codex skill at {source}")
    target = _codex_skills_root() / CODEX_SKILL_NAME
    before_snapshot = _path_snapshot(target)
    before_artifact = recorder.write_json("codex-skill/skill.before.json", before_snapshot)

    same_target = bool(target.exists() or target.is_symlink())
    if same_target:
        try:
            same_target = target.resolve() == source.resolve()
        except OSError:
            same_target = False
    if not same_target:
        if target.is_symlink() or target.is_file():
            target.unlink()
        elif target.is_dir():
            shutil.rmtree(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(source, target_is_directory=True)

    after_snapshot = _path_snapshot(target)
    after_artifact = recorder.write_json("codex-skill/skill.after.json", after_snapshot)
    effective = bool(target.exists() or target.is_symlink())
    try:
        effective = effective and target.resolve() == source.resolve()
    except OSError:
        effective = False
    recorder.add(
        "preflight.codex_global_skill_install",
        "passed" if effective else "failed",
        "Codex global skill entry for Thoth was checked and aligned to the repo-generated public skill surface.",
        [before_artifact, after_artifact],
    )
    if not effective:
        raise RuntimeError("codex skill installation did not resolve to the repo-generated Thoth skill")
    return {
        "source": str(source),
        "target": str(target),
        "before": before_snapshot,
        "after": after_snapshot,
        "effective": effective,
    }


def _ensure_codex_global_hooks(recorder: Recorder) -> dict[str, Any]:
    hooks_path = _codex_hooks_path()
    before = hooks_path.read_text(encoding="utf-8") if hooks_path.exists() else ""
    before_artifact = recorder.write_text("codex-hooks/global.before.json", before or "__MISSING__\n")
    payload = render_codex_hooks_payload()
    hooks_path.parent.mkdir(parents=True, exist_ok=True)
    hooks_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    after = hooks_path.read_text(encoding="utf-8")
    after_artifact = recorder.write_text("codex-hooks/global.after.json", after)
    effective = "thoth-codex-hook.sh" in after
    recorder.add(
        "preflight.codex_global_hooks",
        "passed" if effective else "failed",
        "Codex global hooks.json was aligned to the repo-local Thoth hook bridge commands.",
        [before_artifact, after_artifact],
    )
    if not effective:
        raise RuntimeError("codex global hooks.json does not contain the Thoth hook bridge commands")
    return {
        "path": str(hooks_path),
        "before_artifact": before_artifact,
        "after_artifact": after_artifact,
        "effective": effective,
    }


def _preflight_host_real(
    capabilities: dict[str, Any],
    recorder: Recorder,
    *,
    requested_hosts: set[str],
) -> None:
    required = {
        "codex_cli_present": bool(capabilities.get("codex_cli_present")) if "codex" in requested_hosts else True,
        "codex_authenticated": bool(capabilities.get("codex_authenticated")) if "codex" in requested_hosts else True,
        "claude_cli_present": bool(capabilities.get("claude_cli_present")) if "claude" in requested_hosts else True,
        "claude_authenticated": bool(capabilities.get("claude_authenticated")) if "claude" in requested_hosts else True,
    }
    missing = [name for name, ok in required.items() if not ok]
    if missing:
        detail = f"Missing heavy host-real prerequisites: {', '.join(missing)}"
        recorder.add("preflight.host_tools", "failed", detail)
        raise RuntimeError(detail)
    if "codex" in requested_hosts:
        _ensure_codex_skill_installed(recorder)
    recorder.add(
        "preflight.deterministic_seed",
        "passed",
        "Verified heavy prerequisites for the deterministic Python host workflow.",
    )

__all__ = [name for name in globals() if not name.startswith("__")]
