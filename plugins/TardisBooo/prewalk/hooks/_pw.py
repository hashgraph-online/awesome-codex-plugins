#!/usr/bin/env python3
"""Skill-side helper for the Codex host: handoff and revision commands.

Invoked by the ``$pw-go`` / ``$pw-revise`` / ``$pw-retry`` /
``$pw-reconcile`` / ``$pw-resume`` / ``$pw-off`` skills:

  _pw.py go        <session_id> [--schema-fields=...]
  _pw.py observe   <session_id> (read runtime evidence; never accepts a result)
  _pw.py revise    <session_id> [revision text...]
  _pw.py retry     <session_id> --schema-fields=...
  _pw.py reconcile <session_id> [--confirmed-not-running] [detail...]
  _pw.py resume    <session_id>
  _pw.py complete|incomplete <session_id> [detail...]

On success ``go``/``retry`` print the route in the machine-readable envelope
(``PREWALK_*`` markers) that skills relay verbatim to the model.
"""

from __future__ import annotations

import sys

import _engine  # noqa: F401  (locates prewalk_engine)
import _common  # type: ignore[import-not-found]  # noqa: E402
import prewalk_engine as core  # noqa: E402


def _schema_fields(arguments: list[str]) -> set[str]:
    """Collect ``--schema-fields=a,b`` values so routing proof is per-run live."""
    fields: set[str] = set()
    for argument in arguments:
        if argument.startswith("--schema-fields="):
            fields.update(
                item.strip() for item in argument.partition("=")[2].split(",") if item.strip()
            )
    return fields


def _print_route(result: core.V4CheckpointResult, schema_fields: set[str]) -> None:
    """Emit the route envelope, or the plain message when nothing is live."""
    if result.state is not None and result.status == "handoff_requested":
        state = result.state
        if "fork_context" in schema_fields:
            print("PREWALK_SPAWN_PROFILE: fork_context")
            fork_context = False if state.model_routing_proven else state.fork_turns == "all"
            print(f"PREWALK_FORK_CONTEXT: {str(fork_context).lower()}")
        else:
            print("PREWALK_SPAWN_PROFILE: task_name")
            print(f"PREWALK_TASK_NAME: {state.route_task_name}")
            fork_turns = "none" if state.model_routing_proven else state.fork_turns
            print(f"PREWALK_FORK_TURNS: {fork_turns}")
        print(f"PREWALK_EXECUTOR_MODEL: {state.executor_model}")
        if state.effort_routing_proven:
            print(f"PREWALK_EXECUTOR_EFFORT: {state.executor_effort}")
        print("PREWALK_MESSAGE_BEGIN")
        print(result.message)
        print("PREWALK_MESSAGE_END")
    else:
        print(result.message or "There is no active prewalk checkpoint in this session.")


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    sub = sys.argv[1]
    session_id = _common.resolve_session_id(sys.argv[2])
    if not session_id:
        print(
            "prewalk: cannot continue — CODEX_THREAD_ID is missing or conflicts with the supplied id. "
            "Use Codex CLI 0.146.0 or newer, or pass an explicit id on a legacy CLI.",
            file=sys.stderr,
        )
        return 1
    store = _common.store_file()

    if sub == "recover":
        from _recover import recover
        ordinal = next((arg.partition("=")[2] for arg in sys.argv[3:] if arg.startswith("--ordinal=")), None)
        return recover(session_id, ordinal)

    if sub == "checkpoint":
        if len(sys.argv) != 4:
            raise ValueError("usage: _pw.py checkpoint <session_id> <workspace-packet-file>")
        from _checkpoint import submit
        return submit(store, session_id, sys.argv[3])

    if sub == "observe":
        from _observe import observe
        print(observe(store, session_id))
        return 0

    if sub == "go":
        loaded = core.load_v4_state(store, session_id,
                                    workspace_id=core.workspace_identity(_common.workspace_root()))
        if loaded.status == "workspace_mismatch":
            raise ValueError(loaded.message)
        pending = loaded.state
        if pending and pending.phase in ("handoff_requested", "executor_running"):
            from _observe import observe
            print(observe(store, session_id))
            return 0
        fields = _schema_fields(sys.argv[3:])
        result = core.request_codex_handoff(
            store, session_id, schema_fields=fields
        )
        _print_route(result, fields)
        return 0

    if sub == "retry":
        previous = core.load_v4_state(store, session_id).state
        if previous and any(word in previous.last_error.lower() for word in
                            ("permission denied", "read-only", "not writable", "credentials", "sandbox")):
            if "--prerequisite-resolved" not in sys.argv[3:]:
                raise ValueError("retry blocked: resolve the recorded permission/configuration prerequisite first; "
                                 "then explicitly pass --prerequisite-resolved")
        fields = _schema_fields(sys.argv[3:])
        prepared = core.prepare_v4_retry(store, session_id)
        if prepared.status in ("checkpoint_ready", "handoff_requested"):
            prepared = core.request_codex_handoff(
                store, session_id, schema_fields=fields
            )
        _print_route(prepared, fields)
        return 0

    if sub == "reconcile":
        confirmed = "--confirmed-not-running" in sys.argv[3:]
        detail = " ".join(
            argument for argument in sys.argv[3:]
            if argument != "--confirmed-not-running"
        )
        result = core.reconcile_v4_route(
            store,
            session_id,
            confirmed_not_running=confirmed,
            detail=detail,
        )
        print(result.message)
        return 0

    if sub == "revise":
        revision = " ".join(sys.argv[3:]).strip()
        result = core.revise_v4_checkpoint(store, session_id, revision)
        print(result.message or "There is no active prewalk checkpoint to revise.")
        return 0

    if sub == "resume":
        result = core.resume_codex_manual(store, session_id)
        print(result.message)
        return 0

    if sub in ("complete", "incomplete"):
        result = core.finish_codex_manual(
            store,
            session_id,
            complete=sub == "complete",
            detail=" ".join(sys.argv[3:]),
        )
        print(result.message)
        return 0

    print("unknown subcommand: " + sub, file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"prewalk: operation failed; no new launch authorized: {exc}", file=sys.stderr)
        raise SystemExit(1)
