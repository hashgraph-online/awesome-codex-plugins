"""Explicit checkpoint transaction: independent of Stop event delivery."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import _common
import prewalk_engine as core
from prewalk_engine.checkpoint import packet_todos


def submit(store: str, sid: str, packet_path: str) -> int:
    path = Path(packet_path).resolve()
    workspace = Path(_common.workspace_root()).resolve()
    if not path.is_relative_to(workspace):
        raise ValueError("checkpoint packet must be inside the active workspace")
    if path.stat().st_size > 1024 * 1024:
        raise ValueError("checkpoint packet exceeds 1 MiB")
    packet = path.read_text(encoding="utf-8-sig")
    loaded = core.load_v4_state(store, sid, workspace_id=core.workspace_identity(workspace))
    if loaded.state is None:
        raise ValueError(loaded.message or "no active run; arm before checkpoint submission")
    before = loaded.state
    snapshot = packet_todos(packet)
    if not snapshot:
        raise ValueError("checkpoint requires a complete Markdown todo snapshot; stored todos are not a substitute")
    if before.phase == "checkpoint_ready" and before.packet != packet:
        raise ValueError("checkpoint already committed with different content; use pw-revise first")
    result = core.capture_v4_checkpoint(store, sid, packet=packet, todos=snapshot)
    if result.status != "checkpoint_ready":
        core.note_v4_checkpoint_reject(store, sid, reason=f"explicit checkpoint: {result.status}: {result.message}")
        print(json.dumps({"status": result.status, "error": result.message}, ensure_ascii=False))
        return 1
    # Do not acknowledge a write that cannot be read back, or a racing revision.
    state = core.load_v4_state(store, sid).state
    if state is None or state.phase != "checkpoint_ready" or state.packet != packet:
        raise ValueError("checkpoint read-back mismatch; no handoff authorized")
    _common.audit("explicit_checkpoint", "checkpoint_ready", revision=state.revision,
                  packet_sha256=hashlib.sha256(packet.encode("utf-8")).hexdigest())
    print(json.dumps({"status": "checkpoint_ready", "session_id": sid,
                      "workspace": str(workspace), "store": store,
                      "revision": state.revision,
                      "packet_sha256": hashlib.sha256(packet.encode("utf-8")).hexdigest(),
                      "next": "pw-go" if state.fast_mode else "await_user_review"}, ensure_ascii=False))
    return 0
