"""Record types and the transition kernel of the v4 state machine.

A *record* is the persisted truth about one root session. Everything the
adapters do — validating a Stop checkpoint, rewriting an Agent call, binding
a subagent — funnels through :func:`apply_v4_transition`, which enforces the
three invariants the whole design rests on:

1. **One owner per transition.** The caller names the phases it expects; a
   record found in any other phase is an error, never a guess.
2. **Event idempotency.** Every applied event id is recorded; a replayed id
   returns the current state untouched, so duplicated hook deliveries (the
   host sends them more often than one would think) cannot double-apply.
3. **Invariants re-checked on write.** After applying updates the record must
   satisfy :func:`validate_v4_state` again, or the whole write is abandoned.

Loading mirrors that caution: legacy 0.3 records are reset (never upgraded),
unknown future schemas fail closed, and structurally invalid v4 records are
reported for ``pw-off`` instead of being patched in place.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Iterable

from .protocol import (
    DEFAULT_MAX_TODOS,
    DEFAULT_PRESET,
    FRONTIER,
    HANDOFF_MODES,
    Todo,
    V4_CHECKPOINT_PHASES,
    V4_FORK_MODES,
    V4_PHASES,
    V4_ROUTE_PHASES,
    V4_SCHEMA_VERSION,
    count_remaining,
    missing_packet_headings,
    validate_todo_list,
)
from .store import (
    _read_all_with_status,
    _store_lock,
    _write_all,
    utc_timestamp,
    workspace_identity,
)


class V4StateError(ValueError):
    """A v4 record or transition violates the durable workflow contract."""


# --- Legacy 0.3 record --------------------------------------------------------


@dataclass
class PrewalkState:
    """Superseded 0.3 per-session record, readable but no longer written."""

    session_id: str
    phase: str = FRONTIER
    preset: str = DEFAULT_PRESET
    max_todos: int = DEFAULT_MAX_TODOS
    auto_swap: bool = False  # --no-pause: swap without waiting for /pw-go
    pause_seen: bool = False
    frontier_todos_ever_seen: bool = False
    todos_remaining: int = 0
    blocked_edits: int = 0
    first_edit_landed: bool = False  # frontier completed its one verified edit
    checkpoint_evidence: str = ""  # observed-edit | todo-only
    checkpoint_warning: str = ""
    handoff_done: bool = False  # a handoff was confirmed successful
    handoff_host: str = ""
    handoff_mode: str = "auto"
    require_model_routing: bool = True
    handoff_routed: bool = False
    handoff_token: str = ""
    handoff_tool_use_id: str = ""
    executor_agent_id: str = ""
    handoff_launch_acknowledged: bool = False
    handoff_attempts: int = 0
    last_handoff_error: str = ""
    original_model: str = ""  # planner model, to restore after executor finishes
    executor_model: str = ""  # model the /pw-go handoff should switch to
    planner_thinking: str = ""
    executor_thinking: str = ""
    created_turn: int = 0  # informational

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "PrewalkState":
        known = {name for name in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{key: value for key, value in raw.items() if key in known})


# --- V4 record ----------------------------------------------------------------


@dataclass
class V4State:
    """The durable per-session v4 record (see ADR 0001 for the field contract)."""

    root_session_id: str
    workspace_id: str
    host: str
    schema_version: int = V4_SCHEMA_VERSION
    phase: str = "planning"
    preset: str = DEFAULT_PRESET
    executor_model: str = ""
    executor_effort: str = ""
    max_todos: int = DEFAULT_MAX_TODOS
    handoff_mode: str = "auto"
    require_model_routing: bool = True
    fork_turns: str = "all"
    fast_mode: bool = False
    plan_seen: bool = False
    fast_gate_open: bool = False
    checkpoint_rejects: int = 0
    planner_mutations: int = 0
    model_routing_proven: bool = False
    effort_routing_proven: bool = False
    todos: list[Todo] = field(default_factory=list)
    packet: str = ""
    verification_evidence: list[str] = field(default_factory=list)
    verification_warning: str = ""
    route_token: str = ""
    route_task_name: str = ""
    route_tool_use_id: str = ""
    executor_agent_id: str = ""
    route_attempt: int = 0
    launch_acknowledged: bool = False
    created_at: str = ""
    updated_at: str = ""
    checkpoint_at: str = ""
    route_requested_at: str = ""
    executor_started_at: str = ""
    last_event_at: str = ""
    revision: int = 0
    processed_event_ids: list[str] = field(default_factory=list)
    last_error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "V4State":
        if not isinstance(raw, dict):
            raise V4StateError("v4 state record must be an object")
        known = {name for name in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        values = {key: value for key, value in raw.items() if key in known}
        todos = values.get("todos", [])
        if not isinstance(todos, list):
            raise V4StateError("v4 todo snapshot must be a list")
        values["todos"] = [
            todo if isinstance(todo, Todo) else Todo(**todo)
            for todo in todos
            if isinstance(todo, (Todo, dict))
        ]
        if len(values["todos"]) != len(todos):
            raise V4StateError("v4 todo snapshot contains an invalid item")
        try:
            return cls(**values)
        except TypeError as exc:
            raise V4StateError(f"v4 state record is partial: {exc}") from exc


@dataclass(frozen=True)
class V4LoadResult:
    """Outcome of a record load: the record (when readable) plus a status."""

    state: V4State | None
    status: str
    message: str = ""
    next_command: str = ""


@dataclass(frozen=True)
class V4CheckpointResult:
    """Outcome of checkpoint-family operations (capture, revise, retry...)."""

    status: str
    message: str
    state: V4State | None = None


@dataclass(frozen=True)
class V4RouteDecision:
    """Outcome of route-family operations (validate, bind, finish...)."""

    handled: bool
    allowed: bool
    message: str = ""
    state: V4State | None = None
    updated_input: dict[str, Any] | None = None


def _parse_v4_timestamp(value: Any, field_name: str) -> datetime:
    """Parse a persisted timestamp; reject naive or malformed values."""
    if not isinstance(value, str) or not value:
        raise V4StateError(f"{field_name} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise V4StateError(f"{field_name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise V4StateError(f"{field_name} must include a timezone")
    return parsed


def validate_v4_state(state: V4State) -> None:
    """Raise :class:`V4StateError` unless every phase invariant holds.

    The checks run top-down: schema and identity first, then scalar types,
    then timestamps, then per-phase requirements. The per-phase block is the
    one that encodes the workflow promise — a checkpoint phase always carries
    its packet, evidence, and a finished task 1; a route phase always carries
    its token and attempt counter.
    """
    if state.schema_version != V4_SCHEMA_VERSION:
        raise V4StateError(f"unsupported state schema {state.schema_version!r}")
    if not isinstance(state.root_session_id, str) or not state.root_session_id.strip():
        raise V4StateError("root_session_id is required")
    if not isinstance(state.workspace_id, str) or not state.workspace_id.strip():
        raise V4StateError("workspace_id is required")
    if state.host not in ("codex", "claude"):
        raise V4StateError("host must be codex or claude")
    if state.phase not in V4_PHASES:
        raise V4StateError(f"invalid v4 phase {state.phase!r}")
    string_fields = (
        "preset",
        "executor_model",
        "executor_effort",
        "handoff_mode",
        "packet",
        "verification_warning",
        "route_token",
        "route_task_name",
        "route_tool_use_id",
        "executor_agent_id",
        "last_error",
    )
    if any(not isinstance(getattr(state, name), str) for name in string_fields):
        raise V4StateError("v4 text fields must be strings")
    if not isinstance(state.max_todos, int) or isinstance(state.max_todos, bool) or state.max_todos < 1:
        raise V4StateError("max_todos must be positive")
    if state.handoff_mode not in HANDOFF_MODES:
        raise V4StateError(f"invalid handoff mode {state.handoff_mode!r}")
    if state.fork_turns not in V4_FORK_MODES:
        raise V4StateError(f"invalid fork_turns {state.fork_turns!r}")
    if not isinstance(state.checkpoint_rejects, int) or isinstance(state.checkpoint_rejects, bool) or state.checkpoint_rejects < 0:
        raise V4StateError("checkpoint_rejects cannot be negative")
    if not isinstance(state.planner_mutations, int) or isinstance(state.planner_mutations, bool) or state.planner_mutations < 0:
        raise V4StateError("planner_mutations cannot be negative")
    created = _parse_v4_timestamp(state.created_at, "created_at")
    updated = _parse_v4_timestamp(state.updated_at, "updated_at")
    if updated < created:
        raise V4StateError("updated_at cannot precede created_at")
    if not state.last_event_at:
        raise V4StateError("last_event_at is required")
    for field_name in (
        "checkpoint_at",
        "route_requested_at",
        "executor_started_at",
        "last_event_at",
    ):
        value = getattr(state, field_name)
        if value:
            parsed = _parse_v4_timestamp(value, field_name)
            if parsed < created or parsed > updated:
                raise V4StateError(f"{field_name} must fall between created_at and updated_at")
    if (
        not isinstance(state.revision, int)
        or isinstance(state.revision, bool)
        or not isinstance(state.route_attempt, int)
        or isinstance(state.route_attempt, bool)
        or state.revision < 0
        or state.route_attempt < 0
    ):
        raise V4StateError("revision and route_attempt cannot be negative")
    if (
        not isinstance(state.require_model_routing, bool)
        or not isinstance(state.fast_mode, bool)
        or not isinstance(state.plan_seen, bool)
        or not isinstance(state.fast_gate_open, bool)
        or not isinstance(state.model_routing_proven, bool)
        or not isinstance(state.effort_routing_proven, bool)
        or not isinstance(state.launch_acknowledged, bool)
    ):
        raise V4StateError("v4 capability flags must be booleans")
    if not isinstance(state.processed_event_ids, list) or not all(
        isinstance(event_id, str) and event_id for event_id in state.processed_event_ids
    ):
        raise V4StateError("processed event IDs must be non-empty strings")
    if len(set(state.processed_event_ids)) != len(state.processed_event_ids):
        raise V4StateError("processed event IDs must be unique")

    if not isinstance(state.todos, list) or not all(isinstance(todo, Todo) for todo in state.todos):
        raise V4StateError("v4 todo snapshot must contain normalized Todo records")
    if any(
        not isinstance(value, str)
        for todo in state.todos
        for value in (todo.id, todo.content, todo.status)
    ):
        raise V4StateError("v4 todo fields must be strings")
    if not isinstance(state.verification_evidence, list) or not all(
        isinstance(item, str) and item.strip() for item in state.verification_evidence
    ):
        raise V4StateError("verification evidence must contain non-empty strings")
    if state.todos:
        error = validate_todo_list(state.todos, state.max_todos)
        if error:
            raise V4StateError(error)
        if any(todo.is_pause for todo in state.todos):
            raise V4StateError("v4 todos contain real work only; PAUSE is not a work item")
        ids = [todo.id.strip() for todo in state.todos]
        if len(set(ids)) != len(ids):
            raise V4StateError("v4 todo IDs must be unique")

    if state.phase in V4_CHECKPOINT_PHASES:
        if not state.todos:
            raise V4StateError("checkpoint phases require a durable todo snapshot")
        if state.todos[0].status != "completed":
            raise V4StateError("checkpoint task 1 must be completed")
        if count_remaining(state.todos) < (1 if state.host == "codex" else 2):
            raise V4StateError("checkpoint requires remaining real tasks")
        missing = missing_packet_headings(state.packet)
        if missing:
            raise V4StateError("checkpoint packet is missing headings: " + ", ".join(missing))
        if not state.verification_evidence and not state.verification_warning.strip():
            raise V4StateError("checkpoint requires verification evidence or an explicit warning")
        if not state.checkpoint_at:
            raise V4StateError("checkpoint_at is required after checkpoint capture")

    if state.phase in V4_ROUTE_PHASES:
        if not state.route_token or not state.route_task_name:
            raise V4StateError("route phases require a token and task name")
        if state.route_attempt < 1 or not state.route_requested_at:
            raise V4StateError("route phases require an attempt and request timestamp")

    if state.phase == "executor_running":
        if not state.executor_agent_id:
            raise V4StateError("executor_running requires a bound agent ID")
        if not state.executor_started_at:
            raise V4StateError("executor_running requires executor_started_at")
    if state.phase in ("incomplete", "stale") and not state.last_error.strip():
        raise V4StateError(f"{state.phase} requires a recovery error")


def new_v4_state(
    root_session_id: str,
    workspace_id: str,
    host: str,
    *,
    now: str | None = None,
    **settings: Any,
) -> V4State:
    """Build a validated in-memory v4 record without touching the store."""
    timestamp = now or utc_timestamp()
    state = V4State(
        root_session_id=root_session_id.strip(),
        workspace_id=workspace_id.strip(),
        host=host,
        created_at=timestamp,
        updated_at=timestamp,
        last_event_at=timestamp,
        **settings,
    )
    validate_v4_state(state)
    return state


def create_v4_state(store_file: str | os.PathLike[str], state: V4State) -> None:
    """Atomically create one root record without replacing an existing run."""
    validate_v4_state(state)
    with _store_lock(store_file):
        data = _read_all_with_status(store_file)[0]
        if state.root_session_id in data:
            raise V4StateError("a state record already exists for this root session")
        data[state.root_session_id] = state.to_dict()
        _write_all(store_file, data)


def start_v4_run(
    store_file: str | os.PathLike[str],
    root_session_id: str,
    workspace_root: str | os.PathLike[str],
    host: str,
    preset,
    *,
    fast_mode: bool = False,
    now: str | None = None,
) -> V4State:
    """Arm a schema-4 run, replacing only this root session's prior record."""
    state = new_v4_state(
        root_session_id,
        workspace_identity(workspace_root),
        host,
        now=now,
        preset=preset.name,
        executor_model=preset.executor_model,
        executor_effort=preset.executor_effort,
        max_todos=preset.max_todos,
        handoff_mode=preset.handoff_mode,
        require_model_routing=preset.require_model_routing,
        fork_turns=preset.fork_turns,
        fast_mode=fast_mode,
    )
    with _store_lock(store_file):
        data, status = _read_all_with_status(store_file)
        if status == "corrupt_store":
            data = {}
        data[root_session_id] = state.to_dict()
        _write_all(store_file, data)
    return state


def load_v4_state(
    store_file: str | os.PathLike[str],
    root_session_id: str,
    *,
    workspace_id: str = "",
) -> V4LoadResult:
    """Load one v4 record and report deterministic reset/recovery information.

    Every failure mode maps to a status plus the single safest next command:
    corrupt store -> re-arm, legacy record -> re-arm, future schema -> doctor,
    invalid record -> disarm, wrong workspace -> doctor. Callers render these
    verbatim; they are part of the operator contract.
    """
    root_session_id = (root_session_id or "").strip()
    if not root_session_id:
        return V4LoadResult(
            None,
            "missing_identity",
            "Prewalk cannot resolve the active root session identity.",
            "pw-doctor",
        )
    with _store_lock(store_file):
        data, store_status = _read_all_with_status(store_file)
        if store_status == "corrupt_store":
            return V4LoadResult(
                None,
                "corrupt_store",
                "Prewalk quarantined an unreadable state store. Re-arm this run.",
                "prewalk",
            )
        raw = data.get(root_session_id)
        if raw is None:
            return V4LoadResult(None, "missing")
        record_version = raw.get("schema_version")
        if record_version in (None, 3):
            data.pop(root_session_id, None)
            _write_all(store_file, data)
            return V4LoadResult(
                None,
                "legacy_reset",
                "Prewalk reset an incompatible 0.3.x run; worktree files and host todos were unchanged.",
                "prewalk",
            )
        if record_version != V4_SCHEMA_VERSION:
            return V4LoadResult(
                None,
                "unsupported_version",
                f"Prewalk state schema {record_version!r} is not supported by this plugin and was not changed.",
                "pw-doctor",
            )
        try:
            state = V4State.from_dict(raw)
            validate_v4_state(state)
        except (AttributeError, TypeError, V4StateError, ValueError) as exc:
            return V4LoadResult(
                None,
                "invalid",
                f"Prewalk found an invalid v4 state record: {exc}",
                "pw-off",
            )
        if state.root_session_id != root_session_id:
            return V4LoadResult(
                None,
                "invalid",
                "Prewalk state key conflicts with its root session identity.",
                "pw-off",
            )
        if workspace_id and state.workspace_id != workspace_id:
            return V4LoadResult(
                None,
                "workspace_mismatch",
                "Prewalk state belongs to a different workspace and was not changed.",
                "pw-doctor",
            )
        if state.phase == "stale":
            return V4LoadResult(
                state,
                "stale",
                "Prewalk cannot prove whether the bound executor is still running.",
                "pw-reconcile",
            )
        if state.phase == "incomplete":
            return V4LoadResult(
                state,
                "incomplete",
                "Prewalk retained the durable checkpoint after an incomplete executor attempt.",
                "pw-retry",
            )
        return V4LoadResult(state, "ok")


#: Fields no transition may ever overwrite — they pin the record's identity
#: and its idempotency ledger.
_V4_IMMUTABLE_FIELDS = {
    "schema_version",
    "root_session_id",
    "workspace_id",
    "host",
    "created_at",
    "revision",
    "processed_event_ids",
}


def apply_v4_transition(
    store_file: str | os.PathLike[str],
    root_session_id: str,
    *,
    expected_phases: Iterable[str],
    target_phase: str,
    event_id: str,
    updates: dict[str, Any] | None = None,
    now: str | None = None,
) -> V4State:
    """Apply one locked, invariant-checked, event-idempotent v4 transition.

    Callers describe *what changed* (``updates``) and *which phases legitimize
    it* (``expected_phases``); this function owns ordering, timestamps, the
    revision counter, and durability. A repeated ``event_id`` short-circuits
    to the stored state — replays are always safe.
    """
    expected = set(expected_phases)
    if not event_id.strip():
        raise V4StateError("transition event_id is required")
    if target_phase not in V4_PHASES:
        raise V4StateError(f"invalid target phase {target_phase!r}")
    changes = dict(updates or {})
    forbidden = _V4_IMMUTABLE_FIELDS.intersection(changes)
    if forbidden:
        raise V4StateError("transition cannot replace immutable fields: " + ", ".join(sorted(forbidden)))
    unknown = set(changes) - set(V4State.__dataclass_fields__)  # type: ignore[attr-defined]
    if unknown:
        raise V4StateError("transition contains unknown fields: " + ", ".join(sorted(unknown)))

    with _store_lock(store_file):
        data, status = _read_all_with_status(store_file)
        if status == "corrupt_store":
            raise V4StateError("state store was corrupt and has been quarantined")
        raw = data.get(root_session_id)
        if raw is None or raw.get("schema_version") != V4_SCHEMA_VERSION:
            raise V4StateError("no v4 state exists for this root session")
        state = V4State.from_dict(raw)
        validate_v4_state(state)
        if event_id in state.processed_event_ids:
            return state
        if state.phase not in expected:
            raise V4StateError(
                f"event {event_id!r} cannot transition {state.phase!r}; expected {sorted(expected)!r}"
            )
        for key, value in changes.items():
            if key == "todos":
                value = [todo if isinstance(todo, Todo) else Todo(**todo) for todo in value]
            setattr(state, key, value)
        timestamp = now or utc_timestamp()
        if _parse_v4_timestamp(timestamp, "updated_at") < _parse_v4_timestamp(
            state.updated_at, "previous updated_at"
        ):
            raise V4StateError("transition timestamp cannot precede the current state")
        state.phase = target_phase
        state.updated_at = timestamp
        state.last_event_at = timestamp
        state.revision += 1
        state.processed_event_ids = state.processed_event_ids + [event_id]
        validate_v4_state(state)
        data[root_session_id] = state.to_dict()
        _write_all(store_file, data)
        return state


def _v4_content_event_id(kind: str, root_session_id: str, *values: Any) -> str:
    """Derive a stable event id from event content.

    Content-derived ids make retries of the *same* observation idempotent
    (e.g. persisting an unchanged todo snapshot twice) while still recording
    genuinely new content as new events.
    """
    encoded = json.dumps(values, ensure_ascii=False, sort_keys=True, default=str)
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:24]
    return f"{kind}:{root_session_id}:{digest}"
