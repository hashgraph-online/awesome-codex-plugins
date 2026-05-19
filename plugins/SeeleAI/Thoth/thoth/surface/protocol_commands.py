"""Internal runtime protocol commands exposed through the public CLI parser."""

from __future__ import annotations

import json
from pathlib import Path

from thoth.run.ledger import append_protocol_event, complete_run, fail_run, heartbeat_run, record_artifact
from thoth.run.phases import next_phase_payload, submit_phase_output
from thoth.surface.envelope import decode_json_arg


def handle_append_event(args, parser, *, project_root: Path) -> int:
    payload = decode_json_arg(getattr(args, "payload_json", None), field="--payload-json")
    append_protocol_event(Path(args.project_root), args.run_id, message=args.message, kind=args.kind, level=args.level, phase=args.phase, progress_pct=args.progress, payload=payload if isinstance(payload, dict) else None)
    return 0


def handle_record_artifact(args, parser, *, project_root: Path) -> int:
    metadata = decode_json_arg(getattr(args, "metadata_json", None), field="--metadata-json")
    record_artifact(Path(args.project_root), args.run_id, path=args.path, label=args.label, artifact_kind=args.kind, metadata=metadata if isinstance(metadata, dict) else None)
    return 0


def handle_heartbeat(args, parser, *, project_root: Path) -> int:
    heartbeat_run(Path(args.project_root), args.run_id, phase=args.phase, progress_pct=args.progress, note=args.note)
    return 0


def handle_next_phase(args, parser, *, project_root: Path) -> int:
    payload = next_phase_payload(Path(args.project_root), args.run_id)
    print(payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def handle_submit_phase(args, parser, *, project_root: Path) -> int:
    payload = decode_json_arg(getattr(args, "output_json", None), field="--output-json")
    if not isinstance(payload, dict):
        parser.exit(2, "thoth: error: --output-json must decode to an object.\n")
    result = submit_phase_output(Path(args.project_root), args.run_id, phase=args.phase, payload=payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def handle_complete(args, parser, *, project_root: Path) -> int:
    result_payload = decode_json_arg(getattr(args, "result_json", None), field="--result-json")
    checks = decode_json_arg(getattr(args, "checks_json", None), field="--checks-json")
    complete_run(Path(args.project_root), args.run_id, summary=args.summary, result_payload=result_payload if isinstance(result_payload, dict) else None, checks=checks if isinstance(checks, list) else None)
    return 0


def handle_fail(args, parser, *, project_root: Path) -> int:
    result_payload = decode_json_arg(getattr(args, "result_json", None), field="--result-json")
    fail_run(Path(args.project_root), args.run_id, summary=args.summary, reason=args.reason, result_payload=result_payload if isinstance(result_payload, dict) else None)
    return 0
