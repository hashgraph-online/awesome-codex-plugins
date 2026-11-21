"""prewalk-engine: the host-agnostic half of the prewalk plugin.

The package is organized as a set of layers, each importable only from the
layers above it::

    protocol       frozen names, limits, todo rules (imports nothing local)
      ↑
    store          locked, atomic JSON persistence
      ↑
    records        record types + the transition kernel
      ↑        ↑             ↑
    checkpoint  routing     operations      (the three v4 workflows)
      ↑        ↑             ↑
    presets → capabilities                  (configuration + probing)
      ↑
    prompts        model-facing prose (leaf; imported by everything)
    legacy         the frozen 0.3 event machine (imports store/protocol)

Host adapters (``hosts/codex``, ``hosts/claude``) may import this package;
this package never imports a host. Each host vendors a byte-identical copy
under its ``hooks/`` directory (see ``scripts/sync_engine.py``) because both
plugin marketplaces install only the host subtree.

Importing ``prewalk_engine`` re-exports the complete public API under one
namespace, so adapters and tests can treat the package exactly like the
single-module core this project was refactored from.
"""

from __future__ import annotations

from .protocol import (
    DEFAULT_MAX_TODOS,
    DEFAULT_PRESET,
    EXECUTOR,
    FRONTIER,
    HANDOFF_MODES,
    HANDOFF_REQUESTED,
    IDLE,
    PAUSED,
    READY,
    RESTORING,
    VERSION,
    V4_CHECKPOINT_PHASES,
    V4_CHECKPOINT_READY,
    V4_CHECKPOINT_RETRY_LIMIT,
    V4_DEFAULT_STALE_SECONDS,
    V4_EXECUTOR_RUNNING,
    V4_FORK_MODES,
    V4_HANDOFF_REQUESTED,
    V4_INCOMPLETE,
    V4_PACKET_HEADINGS,
    V4_PHASES,
    V4_PLANNING,
    V4_PLANNER_MUTATION_LIMIT,
    V4_PLANNER_NUDGE_AT,
    V4_ROUTE_PHASES,
    V4_SCHEMA_VERSION,
    V4_STALE,
    Todo,
    count_remaining,
    is_pause_todo,
    missing_packet_headings,
    validate_checkpoint,
    validate_todo_list,
)
from .store import (
    clear_state,
    has_record,
    load_state,
    save_state,
    state_path,
    utc_timestamp,
    workspace_identity,
)
from .records import (
    PrewalkState,
    V4CheckpointResult,
    V4LoadResult,
    V4RouteDecision,
    V4State,
    V4StateError,
    apply_v4_transition,
    create_v4_state,
    load_v4_state,
    new_v4_state,
    start_v4_run,
    validate_v4_state,
)
from .checkpoint import (
    capture_v4_checkpoint,
    note_v4_checkpoint_reject,
    note_v4_planner_mutation,
    packet_verification,
    record_v4_todos,
    revise_v4_checkpoint,
    v4_handoff_context,
)
from .routing import (
    CLAUDE_EXECUTOR_AGENT,
    CLAUDE_EXECUTOR_LIFECYCLE_TYPES,
    CLAUDE_EXECUTOR_INSTRUCTIONS,
    CODEX_EXECUTOR_INSTRUCTIONS,
    acknowledge_claude_agent_call,
    bind_claude_executor,
    bind_codex_executor,
    claude_route_instruction,
    claude_route_message,
    codex_route_message,
    fail_claude_agent_call,
    finish_codex_manual,
    finish_v4_executor,
    interrupt_v4_executor,
    request_claude_handoff,
    request_codex_handoff,
    resume_codex_manual,
    validate_claude_agent_call,
    validate_codex_spawn,
)
from .operations import (
    describe,
    detect_v4_stale,
    disarm,
    format_v4_status,
    prepare_v4_retry,
    reconcile_v4_route,
)
from .presets import (
    Preset,
    default_preset_json,
    default_preset_toml,
    load_presets_json,
    load_presets_toml,
)
from .capabilities import (
    CapabilityReport,
    evaluate_capabilities,
    format_capability_report,
)
from .prompts import (
    FAST_HANDOFF_HINT,
    FORK_HANDOFF_NOTE,
    HANDOFF_NOTE,
    HANDOFF_PACKET_TEMPLATE,
    HookAction,
    NO_HANDOFF_NEEDED,
    ONE_LEFT_HINT,
    PAUSED_HINT,
    frontier_prompt,
)
from .legacy import (
    on_edit_attempt,
    on_executor_result,
    on_executor_started,
    on_fast_handoff,
    on_handoff_confirm,
    on_handoff_failed,
    on_handoff_launch_ack,
    on_pw_go,
    on_pw_revise,
    on_todos_changed,
    on_turn_end,
    start_run,
)

__all__ = [
    # protocol
    "DEFAULT_MAX_TODOS", "DEFAULT_PRESET", "EXECUTOR", "FRONTIER", "HANDOFF_MODES",
    "HANDOFF_REQUESTED", "IDLE", "PAUSED", "READY", "RESTORING", "VERSION",
    "V4_CHECKPOINT_PHASES", "V4_CHECKPOINT_READY", "V4_CHECKPOINT_RETRY_LIMIT",
    "V4_DEFAULT_STALE_SECONDS", "V4_EXECUTOR_RUNNING", "V4_FORK_MODES",
    "V4_HANDOFF_REQUESTED", "V4_INCOMPLETE", "V4_PACKET_HEADINGS", "V4_PHASES",
    "V4_PLANNING", "V4_PLANNER_MUTATION_LIMIT", "V4_PLANNER_NUDGE_AT",
    "V4_ROUTE_PHASES", "V4_SCHEMA_VERSION", "V4_STALE",
    "Todo", "count_remaining", "is_pause_todo", "missing_packet_headings",
    "validate_checkpoint", "validate_todo_list",
    # store
    "clear_state", "has_record", "load_state", "save_state", "state_path",
    "utc_timestamp", "workspace_identity",
    # records
    "PrewalkState", "V4CheckpointResult", "V4LoadResult", "V4RouteDecision",
    "V4State", "V4StateError", "apply_v4_transition", "create_v4_state",
    "load_v4_state", "new_v4_state", "start_v4_run", "validate_v4_state",
    # checkpoint
    "capture_v4_checkpoint", "note_v4_checkpoint_reject", "note_v4_planner_mutation",
    "packet_verification", "record_v4_todos", "revise_v4_checkpoint",
    "v4_handoff_context",
    # routing
    "CLAUDE_EXECUTOR_AGENT", "CLAUDE_EXECUTOR_LIFECYCLE_TYPES",
    "CLAUDE_EXECUTOR_INSTRUCTIONS", "CODEX_EXECUTOR_INSTRUCTIONS",
    "acknowledge_claude_agent_call", "bind_claude_executor", "bind_codex_executor",
    "claude_route_instruction", "claude_route_message", "codex_route_message",
    "fail_claude_agent_call", "finish_codex_manual", "finish_v4_executor",
    "interrupt_v4_executor", "request_claude_handoff", "request_codex_handoff",
    "resume_codex_manual", "validate_claude_agent_call", "validate_codex_spawn",
    # operations
    "describe", "detect_v4_stale", "disarm", "format_v4_status",
    "prepare_v4_retry", "reconcile_v4_route",
    # presets
    "Preset", "default_preset_json", "default_preset_toml",
    "load_presets_json", "load_presets_toml",
    # capabilities
    "CapabilityReport", "evaluate_capabilities", "format_capability_report",
    # prompts
    "FAST_HANDOFF_HINT", "FORK_HANDOFF_NOTE", "HANDOFF_NOTE",
    "HANDOFF_PACKET_TEMPLATE", "HookAction", "NO_HANDOFF_NEEDED",
    "ONE_LEFT_HINT", "PAUSED_HINT", "frontier_prompt",
    # legacy 0.3 machine
    "on_edit_attempt", "on_executor_result", "on_executor_started",
    "on_fast_handoff", "on_handoff_confirm", "on_handoff_failed",
    "on_handoff_launch_ack", "on_pw_go", "on_pw_revise", "on_todos_changed",
    "on_turn_end", "start_run",
]
