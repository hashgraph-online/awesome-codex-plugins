"""Capability probing: prove, never assume, that a route can honor the preset.

Both hosts advertise model routing in ways that look promising and break in
practice:

* **Codex** publishes the ``spawn_agent`` tool schema at runtime. Whether the
  ``model`` (and ``reasoning_effort``) parameters exist is a property of the
  *running CLI*, not of any documentation — so callers must pass the live
  field names and this check trusts nothing else.
* **Claude Code** hooks can rewrite a subagent call's model via
  ``updatedInput``, but the ``CLAUDE_CODE_SUBAGENT_MODEL`` environment
  override silently wins over the rewrite. A conflicting override is a hard
  error when the preset requires pinned routing, a loud warning otherwise.

The resulting :class:`CapabilityReport` separates three columns that are easy
to conflate: what was *configured*, what was *requested*, and what the host
actually *proved*. ``routing_allowed`` is the single verdict the routers obey.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable

from .presets import Preset


@dataclass(frozen=True)
class CapabilityReport:
    """Three-column capability verdict for one (preset, host) pair."""

    host: str
    configured_model: str
    configured_effort: str
    model_requested: str
    model_proven: str
    effort_requested: str
    effort_proven: str
    routing_allowed: bool
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


def evaluate_capabilities(
    preset: Preset,
    host: str,
    *,
    schema_fields: Iterable[str] | None = None,
    environment: dict[str, str] | None = None,
) -> CapabilityReport:
    """Separate configured controls from requested and runtime-proven controls."""
    fields = None if schema_fields is None else set(schema_fields)
    warnings = list(preset.deprecation_warnings)
    errors: list[str] = []
    configured_effort = preset.executor_effort or "host-default"

    if host == "codex":
        if fields is None:
            # No live schema was inspected: everything stays pending, and the
            # caller (doctor, or pw-go) is expected to re-run with evidence.
            model_requested = "pending-live-schema"
            model_proven = "unproven"
            effort_requested = "pending-live-schema" if preset.executor_effort else "no"
            effort_proven = "unproven" if preset.executor_effort else "not-configured"
        else:
            model_requested = "yes" if "model" in fields else "no"
            model_proven = "supported" if "model" in fields else "unsupported"
            effort_requested = (
                "yes" if preset.executor_effort and "reasoning_effort" in fields else "no"
            )
            effort_proven = (
                "supported" if preset.executor_effort and "reasoning_effort" in fields
                else "unsupported" if preset.executor_effort
                else "not-configured"
            )
            if preset.require_model_routing and "model" not in fields:
                errors.append("live spawn_agent schema cannot prove configured model routing")
        return CapabilityReport(
            host=host,
            configured_model=preset.executor_model,
            configured_effort=configured_effort,
            model_requested=model_requested,
            model_proven=model_proven,
            effort_requested=effort_requested,
            effort_proven=effort_proven,
            routing_allowed=not errors,
            warnings=tuple(warnings),
            errors=tuple(errors),
        )

    if host != "claude":
        raise ValueError(f"unsupported host {host!r}")
    env = environment if environment is not None else os.environ
    override = env.get("CLAUDE_CODE_SUBAGENT_MODEL", "").strip()
    model_proven = "hook-rewrite"
    if override and override != preset.executor_model:
        detail = (
            f"CLAUDE_CODE_SUBAGENT_MODEL={override!r} conflicts with configured executor "
            f"{preset.executor_model!r}"
        )
        if preset.require_model_routing:
            errors.append(detail)
            model_proven = "override-conflict"
        else:
            warnings.append(detail)
            model_proven = "overridden"
    if preset.executor_effort:
        warnings.append("Claude does not expose a dynamic per-subagent effort control")
    return CapabilityReport(
        host=host,
        configured_model=preset.executor_model,
        configured_effort=configured_effort,
        model_requested="yes",
        model_proven=model_proven,
        effort_requested="no",
        effort_proven="unsupported" if preset.executor_effort else "not-configured",
        routing_allowed=not errors,
        warnings=tuple(warnings),
        errors=tuple(errors),
    )


def format_capability_report(report: CapabilityReport) -> str:
    """Render the three columns plus warnings/errors, aligned for terminals."""
    lines = [
        f"  configured: executor={report.configured_model}; effort={report.configured_effort}",
        f"  requested : model={report.model_requested}; effort={report.effort_requested}",
        f"  proven    : model={report.model_proven}; effort={report.effort_proven}",
    ]
    lines.extend(f"  warning   : {warning}" for warning in report.warnings)
    lines.extend(f"  error     : {error}" for error in report.errors)
    return "\n".join(lines)
