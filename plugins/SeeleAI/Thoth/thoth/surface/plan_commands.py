"""Planning public commands."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from thoth.plan.discuss import checkpoint_discussion_authority, close_discussion_authority, load_authority_json
from thoth.plan.compiler import compile_task_authority
from thoth.plan.store import create_discussion_placeholder, upsert_work_item, upsert_decision
from thoth.objects import ActiveExecutionLock, active_work_ids
from thoth.surface.envelope import output_refs, print_envelope


def append_project_note(project_root: Path, note_type: str, content: str) -> Path:
    path = project_root / ".thoth" / "docs" / "conversations.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"ts": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"), "type": note_type, "host": "codex", "content": content}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return path


def _protocol_command(project_root: Path, command: str, *extra: str) -> str:
    argv = [sys.executable, "-m", "thoth.cli", command, "--project-root", str(project_root), *extra]
    return " ".join(json.dumps(part) for part in argv)


def _discussion_protocol_commands(project_root: Path, discussion_id: str) -> dict[str, str]:
    return {
        "checkpoint_authority": _protocol_command(
            project_root,
            "record-discussion-authority",
            "--discussion-id",
            discussion_id,
            "--mode",
            "draft",
            "--authority-json-file",
            "path/to/authority.json",
        ),
        "close_authority": _protocol_command(
            project_root,
            "record-discussion-authority",
            "--discussion-id",
            discussion_id,
            "--mode",
            "close",
            "--authority-json-file",
            "path/to/authority.json",
        ),
    }


def handle_discuss(args, parser, *, project_root: Path) -> int:
    content = (getattr(args, "goal", None) or " ".join(getattr(args, "rest", []) or [])).strip()
    work_payload = json.loads(args.work_json) if getattr(args, "work_json", None) else None
    if isinstance(work_payload, dict):
        work_id = work_payload.get("work_id") or work_payload.get("object_id")
        if isinstance(work_id, str) and work_id in active_work_ids(project_root):
            print_envelope(
                command="discuss",
                status="blocked_by_active_execution",
                summary=f"Work item {work_id} is locked by active execution; stop or wait for terminal state first.",
                body={"work_id": work_id, "active_work_ids": sorted(active_work_ids(project_root))},
                checks=[{"name": "active_work_lock", "ok": False, "detail": "no discussion or work mutation recorded"}],
            )
            return 3
    note_path = append_project_note(project_root, "discuss", content)
    if getattr(args, "decision_json", None):
        decision = upsert_decision(project_root, json.loads(args.decision_json))
        body: dict[str, Any] = {"decision": decision, "note_path": str(note_path)}
    elif isinstance(work_payload, dict):
        try:
            work = upsert_work_item(project_root, work_payload)
        except ActiveExecutionLock as exc:
            print_envelope(
                command="discuss",
                status="blocked_by_active_execution",
                summary=str(exc),
                body={"work_payload": work_payload},
                checks=[{"name": "active_work_lock", "ok": False, "detail": "work mutation rejected"}],
            )
            return 3
        body = {"work_item": work, "note_path": str(note_path)}
    else:
        decision = create_discussion_placeholder(project_root, content, host="codex")
        body = {
            "discussion": decision,
            "note_path": str(note_path),
            "packet": {
                "packet_kind": "discussion_authority",
                "discussion_id": decision["discussion_id"],
                "protocol_commands": _discussion_protocol_commands(project_root, decision["discussion_id"]),
                "required_authority_categories": [
                    "goal",
                    "non_goals",
                    "constraints",
                    "accepted_decisions",
                    "rejected_options",
                    "acceptance",
                    "context_evidence",
                    "risks",
                    "run_instructions",
                    "open_questions",
                ],
            },
        }
    compiler = compile_task_authority(project_root)
    summary = compiler.get("summary", {})
    work_counts = summary.get("work_item_counts", {}) if isinstance(summary.get("work_item_counts"), dict) else {}
    decision_counts = summary.get("decision_counts", {}) if isinstance(summary.get("decision_counts"), dict) else {}
    print_envelope(
        command="discuss",
        status="ok",
        summary="Object graph summary: ready={ready} blocked={blocked} active={active} accepted_decisions={accepted} legacy={legacy}".format(
            ready=int(work_counts.get("ready", 0)),
            blocked=int(work_counts.get("blocked", 0)),
            active=int(summary.get("active_work_count", 0)),
            accepted=int(decision_counts.get("accepted", 0)),
            legacy=int(summary.get("legacy_authority_count", 0)),
        ),
        body={**body, "compiler": compiler},
        refs=output_refs(note_path, project_root / ".thoth" / "docs" / "object-graph-summary.json"),
        checks=[{"name": "object_graph_ready", "ok": True, "detail": str(work_counts.get("ready", 0))}],
    )
    return 0


def handle_record_discussion_authority(args, parser, *, project_root: Path) -> int:
    root = Path(args.project_root).resolve() if getattr(args, "project_root", None) else project_root
    capsule = load_authority_json(Path(args.authority_json_file))
    try:
        if args.mode == "draft":
            result = checkpoint_discussion_authority(root, discussion_id=args.discussion_id, capsule=capsule)
            status = "ok"
            summary = f"Checkpointed discussion authority for {args.discussion_id}"
        else:
            result = close_discussion_authority(root, discussion_id=args.discussion_id, capsule=capsule)
            status = str(result.get("status") or "ok")
            if status == "needs_input":
                summary = f"Discussion {args.discussion_id} still has authority gaps."
            else:
                summary = f"Closed discussion authority for {args.discussion_id}"
    except ActiveExecutionLock as exc:
        print_envelope(
            command="record-discussion-authority",
            status="blocked_by_active_execution",
            summary=str(exc),
            checks=[{"name": "active_work_lock", "ok": False, "detail": "authority close rejected"}],
        )
        return 3
    print_envelope(
        command="record-discussion-authority",
        status=status,
        summary=summary,
        body={"result": result},
        refs=output_refs(root / ".thoth" / "objects" / "discussion" / f"{args.discussion_id}.json"),
        checks=[{"name": "authority_recorded", "ok": status == "ok", "detail": args.mode}],
    )
    return 0 if status == "ok" else 2
