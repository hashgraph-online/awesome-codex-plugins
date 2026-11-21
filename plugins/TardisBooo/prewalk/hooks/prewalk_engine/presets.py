"""Preset files: how a run chooses its executor route.

Presets are deliberately *executor-only*. The planner is always the model the
human already runs in the root session — a config file on disk cannot (and in
a plugin sandbox should not) switch it. A preset therefore answers one
question: *"when the checkpoint is ready, what does the handoff look like?"*

Two file formats, both optional:

* **Claude** — ``~/.claude/prewalk-presets.json``;
* **Codex** — ``~/.codex/prewalk-presets.toml`` (a minimal TOML reader below
  covers flat ``[presets.<name>]`` tables so no third-party parser is needed).

Legacy ``planner`` / ``planner_thinking`` keys parse only into deprecation
warnings; ``executor_thinking`` remains readable as an alias of
``executor_effort``. Unknown model names are not validated here — the host's
own capability probe is the only authority worth trusting.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .protocol import DEFAULT_MAX_TODOS, DEFAULT_PRESET, HANDOFF_MODES, V4_FORK_MODES


@dataclass
class Preset:
    """One named executor route configuration."""

    name: str
    executor_model: str
    description: str = ""
    max_todos: int = DEFAULT_MAX_TODOS
    executor_effort: str = ""
    handoff_mode: str = "auto"
    require_model_routing: bool = True
    fork_turns: str = "all"
    deprecation_warnings: list[str] = field(default_factory=list)

    # Compatibility views kept for the 0.3 event machine during the rollout:
    # the planner is whatever the root session already runs.
    @property
    def planner_model(self) -> str:
        return "active-session"

    @property
    def planner_thinking(self) -> str:
        return ""

    @property
    def executor_thinking(self) -> str:
        return self.executor_effort


def _handoff_mode(value: Any) -> str:
    mode = str(value or "auto").strip()
    return mode if mode in HANDOFF_MODES else "auto"


def _fork_mode(value: Any) -> str:
    mode = str(value or "all").strip()
    return mode if mode in V4_FORK_MODES else "all"


def _preset_warnings(raw: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if "planner" in raw:
        warnings.append("planner is deprecated and ignored; the active root session is the planner")
    if "planner_thinking" in raw:
        warnings.append("planner_thinking is deprecated and ignored")
    if "executor_thinking" in raw and "executor_effort" not in raw:
        warnings.append("executor_thinking is deprecated; use executor_effort")
    return warnings


def load_presets_json(path: str | os.PathLike[str]) -> dict[str, Preset]:
    """Read Claude-style JSON presets.

    Expected shape::

        {"default": "code-value",
         "presets": {"<name>": {"executor": "...", "description": "...",
                                 "max_todos": 12, "executor_effort": "..."}}}

    An unreadable or malformed file yields an empty mapping — the caller
    falls back to built-in defaults rather than crashing a hook.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    presets: dict[str, Preset] = {}
    for name, raw in (data.get("presets") or {}).items():
        if not isinstance(raw, dict):
            continue
        executor = str(raw.get("executor") or "").strip()
        if not executor:
            continue
        presets[name] = Preset(
            name=name,
            executor_model=executor,
            description=str(raw.get("description") or ""),
            max_todos=int(raw.get("max_todos") or DEFAULT_MAX_TODOS),
            executor_effort=str(
                raw.get("executor_effort") or raw.get("executor_thinking") or ""
            ).strip(),
            handoff_mode=_handoff_mode(raw.get("handoff_mode")),
            require_model_routing=bool(raw.get("require_model_routing", True)),
            fork_turns=_fork_mode(raw.get("fork_turns")),
            deprecation_warnings=_preset_warnings(raw),
        )
    return presets


# Minimal TOML reader sufficient for flat ``[presets.NAME]`` tables with
# string / int / bool values. The full TOML spec is intentionally out of
# scope — a preset file that needs it is a preset file we reject loudly in
# review rather than silently half-parse in a hook.
_TOML_STRING_RE = re.compile(r'^"((?:[^"\\]|\\.)*)"$')
_TOML_TABLE_RE = re.compile(
    r'^\[presets\.(?:"((?:[^"\\]|\\.)*)"|([A-Za-z0-9_.-]+))\]\s*$'
)


def load_presets_toml(path: str | os.PathLike[str]) -> dict[str, Preset]:
    """Read Codex-style TOML presets.

    Expected shape::

        default_preset = "code-value"
        [presets.code-value]
        description = "..."
        executor = "gpt-5.6-terra"
        executor_effort = "medium"
        max_todos = 12
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    presets: dict[str, Preset] = {}
    current: str | None = None
    bucket: dict[str, Any] = {}
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        table = _TOML_TABLE_RE.match(line)
        if table:
            if current is not None:
                _flush_preset(presets, current, bucket)
            quoted_name, bare_name = table.groups()
            current = (
                quoted_name.encode().decode("unicode_escape")
                if quoted_name is not None
                else bare_name
            )
            bucket = {}
            continue
        if current is not None and "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            string_match = _TOML_STRING_RE.match(value)
            if string_match:
                bucket[key] = string_match.group(1).encode().decode("unicode_escape")
            elif value.isdigit():
                bucket[key] = int(value)
            elif value.lower() in ("true", "false"):
                bucket[key] = value.lower() == "true"
    if current is not None:
        _flush_preset(presets, current, bucket)
    return presets


def _flush_preset(out: dict[str, Preset], name: str, bucket: dict[str, Any]) -> None:
    """Materialize one accumulated ``[presets.<name>]`` table."""
    executor = str(bucket.get("executor") or "").strip()
    if not executor:
        return
    out[name] = Preset(
        name=name,
        executor_model=executor,
        description=str(bucket.get("description") or ""),
        max_todos=int(bucket.get("max_todos") or DEFAULT_MAX_TODOS),
        executor_effort=str(
            bucket.get("executor_effort") or bucket.get("executor_thinking") or ""
        ).strip(),
        handoff_mode=_handoff_mode(bucket.get("handoff_mode")),
        require_model_routing=bool(bucket.get("require_model_routing", True)),
        fork_turns=_fork_mode(bucket.get("fork_turns")),
        deprecation_warnings=_preset_warnings(bucket),
    )


def default_preset_json(path: str | os.PathLike[str]) -> str:
    """Read the ``default`` key of a Claude preset file."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return str(json.load(handle).get("default") or DEFAULT_PRESET)
    except (FileNotFoundError, json.JSONDecodeError):
        return DEFAULT_PRESET


def default_preset_toml(path: str | os.PathLike[str]) -> str:
    """Read the ``default_preset`` key of a Codex preset file."""
    try:
        for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
            line = raw_line.split("#", 1)[0].strip()
            if line.startswith("default_preset"):
                _, _, value = line.partition("=")
                value = value.strip()
                string_match = _TOML_STRING_RE.match(value)
                if string_match:
                    return string_match.group(1)
    except FileNotFoundError:
        pass
    return DEFAULT_PRESET
