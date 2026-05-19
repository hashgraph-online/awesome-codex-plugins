"""Registry dispatch for the public Thoth surface."""

from __future__ import annotations

from pathlib import Path

from thoth.observe.status import status_snapshot
from thoth.surface.envelope import print_envelope
from thoth.surface.observe_commands import handle_dashboard, handle_doctor, handle_report, handle_status
from thoth.surface.plan_commands import handle_discuss, handle_record_discussion_authority
from thoth.surface.project_commands import handle_extend, handle_hook, handle_init, handle_sync
from thoth.surface.protocol_commands import (
    handle_append_event,
    handle_complete,
    handle_fail,
    handle_heartbeat,
    handle_next_phase,
    handle_record_artifact,
    handle_submit_phase,
)
from thoth.surface.run_commands import handle_auto, handle_auto_worker, handle_orchestration, handle_prepare, handle_review, handle_run_or_loop, handle_supervise, handle_worker

COMMAND_HANDLERS = {
    "init": handle_init,
    "sync": handle_sync,
    "hook": handle_hook,
    "extend": handle_extend,
    "status": handle_status,
    "doctor": handle_doctor,
    "dashboard": handle_dashboard,
    "report": handle_report,
    "discuss": handle_discuss,
    "record-discussion-authority": handle_record_discussion_authority,
    "review": handle_review,
    "orchestration": handle_orchestration,
    "auto": handle_auto,
    "auto-worker": handle_auto_worker,
    "prepare": handle_prepare,
    "supervise": handle_supervise,
    "worker": handle_worker,
    "append-event": handle_append_event,
    "record-artifact": handle_record_artifact,
    "heartbeat": handle_heartbeat,
    "next-phase": handle_next_phase,
    "submit-phase": handle_submit_phase,
    "complete": handle_complete,
    "fail": handle_fail,
}


def handle_command(args, parser, *, project_root: Path) -> int:
    if args.command in {"run", "loop"}:
        return handle_run_or_loop(args, parser, project_root=project_root)
    handler = COMMAND_HANDLERS.get(args.command)
    if handler is not None:
        return handler(args, parser, project_root=project_root)
    snapshot = status_snapshot(project_root)
    print_envelope(command=args.command, status="ok", summary=f"Loaded {args.command}", body=snapshot)
    return 0
