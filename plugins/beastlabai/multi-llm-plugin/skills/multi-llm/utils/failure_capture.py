"""What the executor writes about a run, and the redaction every one of
those writes goes through first.

``redact.redact_text`` (the one redactor, imported here and applied
before any tail or cut) and :func:`_redact_json` (the same over a JSON
payload), :func:`_redact_probe_tail` (the boundary a probe's
stream crosses before it reaches a message), :func:`_atomic_write_json`
(owner-only, same-directory temp file, ``os.replace``) and the
per-attempt diagnostic captures under ``failed/``
(:func:`_write_failure_capture`, D3k). It imports none of the executor's
other modules.

``utils.subagent_executor`` re-exports every name defined here for reading
only: patch one here, never through the executor
(docs/development/delegation.md#where-the-executors-helpers-live).
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from .held_folder import plan_dir_of, write_in_plan_dir
from .retry_ladder import (  # noqa: F401 - re-exported, see below
    RUNG_BY_STATUS,
)
from .redact import redact_text
from .write_safety import (
    WriteSafetyError,
    contain_local_path,
    rename_below_root,
    write_below_root,
)


#: Per-attempt diagnostic captures (D3k). A directory, so the reaggregation glob
#: (``{phase_dir}/*.json``) never sees them.
FAILED_CAPTURE_DIRNAME = "failed"

#: Per-stream diagnostic capture cap (D3k): last 64 KiB each of stdout/stderr.
MAX_CAPTURE_BYTES = 64 * 1024


def _atomic_write_json(path: str, data: Any) -> bytes:
    """Write ``data`` as JSON, owner-only (0600), by ``atomic_io``'s atomic write;
    the bytes written.

    An executor killed mid-batch (expected on the D4 detached path) therefore
    never leaves a half-written result for the reaggregation glob to pick up.
    The file is published through its folder held below the plan's directory,
    made there if missing (``held_folder.write_in_plan_dir``): a link swapped
    in for the phase folder during the run is refused, never written through
    (docs/development/write-safety.md#plan-output-containment).
    """
    encoded = json.dumps(data, indent=2).encode("utf-8")
    write_in_plan_dir(path, encoded, make=True, mode=0o600)
    return encoded


def _tail(text: str, limit: int = MAX_CAPTURE_BYTES) -> str:
    """The last ``limit`` bytes of ``text``, decoded leniently for diagnostics.

    **Every caller redacts first (``redact_text``), then tails, never the
    reverse.** This keeps the *last* bytes, so a cut landing inside
    ``aws_secret_access_key=`` leaves ``_access_key=<value>`` — a shape
    ``SECRET_KEY`` does not match, so no later pass could recover it.
    """
    encoded = (text or "").encode("utf-8", errors="replace")
    if len(encoded) <= limit:
        return text or ""
    return encoded[-limit:].decode("utf-8", errors="replace")


def _redact_probe_tail(text: str, limit: int = MAX_CAPTURE_BYTES) -> str:
    """A captured stream, redacted then tailed, for quoting into a refusal.

    Also the wrapper for a tail that leaves this module with no redacting sink
    behind it to name — ``dispatch_task``'s ``after_result`` payload, whose
    consumer is a caller's callback.

    The refusal-message counterpart to
    ``providers.cursor_agent.redact_probe_output``, and the same §4.5 boundary as
    ``redact_text`` — not a second mechanism, a wrapper that fixes the two things
    a refusal needs on top of it.

    **Diagnostic value is the point.** A refusal quotes a probe so the reader can
    see *why* the runner was refused, so this redacts identity- and
    credential-shaped **values** and nothing else: cursor-agent's ``status
    --format json`` is a nine-key object, three of whose keys are §4.5.1 P13
    identity fields, and the other six — plus every key name — survive, so two
    runs stay diffable. Dropping the whole tail would trade one regression for
    another.

    Redaction runs **before** ``_tail`` for the reason :func:`_tail` states: the
    tail keeps the *last* bytes, so a cut landing inside a keyword leaves a value
    no later pass can match.

    **Fail safe.** A redactor that raises must never
    fall back to the raw stream — the fallback drops the text exactly the way
    M13's probe boundary does.
    """
    try:
        redacted = redact_text(text or "")
    except Exception:  # noqa: BLE001 - a diagnostic never leaks on failure
        return "<redacted:probe-output>"
    return _tail(redacted, limit).strip()


def _redact_json(value: Any) -> Any:
    """``value`` with every string in it redacted, structure preserved.

    Used at the two JSON write boundaries. A per-field list would have to be
    kept in step with every new diagnostic field a failure record grows; walking
    the payload cannot fall behind one.
    """
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, dict):
        return {key: _redact_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_json(item) for item in value]
    return value


def _safe_task_filename(task_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", task_id or "task") or "task"


def _retire_capture(target: Path, root: str, *, resolve_root: bool = True) -> None:
    """Move an earlier invocation's capture aside rather than overwrite it.

    Attempt numbering restarts at 1 on every invocation, and a re-invoked phase
    re-dispatches the failed task under the same id — so without this the retry
    destroyed the evidence of the attempt it was retrying (measured
    2026-09-14: two ``generate-tasks`` runs an hour apart left one
    ``task_generation.attempt1.json``, the second's). The stamp is the retired
    file's own mtime in UTC, so the name says when that attempt ran; the batch
    report that named the old path is rewritten by the same invocation.
    Best-effort: a rename that fails leaves the overwrite as it was. *target*
    is checked below the phase folder, and renamed in its folder held below
    *root*, the plan's directory as the run recorded it, not resolved again
    (*resolve_root* off; ``write_safety.rename_below_root``), never through a
    link.
    """
    try:
        if not target.exists():
            return
        stamp = datetime.fromtimestamp(
            target.stat().st_mtime, tz=timezone.utc
        ).strftime("%Y%m%dT%H%M%SZ")
        retired = target.with_name(f"{target.stem}.{stamp}{target.suffix}")
        serial = 1
        while retired.exists():
            retired = target.with_name(
                f"{target.stem}.{stamp}-{serial}{target.suffix}"
            )
            serial += 1
        rename_below_root(root, target, retired.name, resolve_root=resolve_root)
    except OSError:  # pragma: no cover - diagnostics must never fail a run
        return


def _write_failure_capture(
    *,
    phase_dir: str,
    task: Dict[str, Any],
    attempt_index: int,
    argv: Sequence[str],
    prompt: str,
    stdout: str,
    stderr: str,
    exit_code: Optional[int],
    duration: float,
    status: str,
    error: str,
    repair: Optional[str] = None,
) -> Optional[str]:
    """Persist one failed attempt's bounded capture (D3k). Best-effort.

    A detached or CI failure has no chat context and no stdout to scroll back
    through, so the diagnosis has to survive on disk. The rendered argv carries
    the prompt **elided to its sha256 and byte length** — never the prompt bytes,
    which embed the plan/diff under review.

    Six of the nine planted secret shapes landed here, three times each: the
    existing 64 KiB ``_tail`` preserved every one, which is why §4.4 does not
    subsume §4.5. Redaction runs on the **full** stream before the tail is taken,
    and the assembled payload is walked once more on the way out.
    """
    try:
        capture_dir = Path(phase_dir) / FAILED_CAPTURE_DIRNAME
        name = f"{_safe_task_filename(str(task.get('task_id', '')))}.attempt{attempt_index}.json"
        digest = hashlib.sha256((prompt or "").encode("utf-8")).hexdigest()
        rendered = [
            f"<prompt sha256:{digest} bytes:{len((prompt or '').encode('utf-8'))}>"
            if arg == prompt
            else arg
            for arg in argv
        ]
        # Checked below the phase folder and below the plan's directory as
        # the run recorded it, then retired and written through the capture
        # folder held from that recorded directory, never resolved again, the
        # phase folder and `failed/` walked: never through a link swapped in
        # for any of them (docs/development/write-safety.md#plan-output-containment).
        target = contain_local_path(capture_dir / name, phase_dir,
                                    what="failure capture")
        recorded = plan_dir_of(capture_dir / name)
        if recorded is not None and not target.is_relative_to(recorded):
            return None
        root = recorded or phase_dir
        _retire_capture(target, root, resolve_root=recorded is None)
        payload = _redact_json({
            "task_id": task.get("task_id"),
            "kind": task.get("kind"),
            "attempt": attempt_index,
            "status": status,
            "rung": RUNG_BY_STATUS.get(status),
            "error": error,
            "exit_code": exit_code,
            "duration_seconds": round(duration, 3),
            "argv": rendered,
            "prompt_sha256": digest,
            "prompt_bytes": len((prompt or "").encode("utf-8")),
            # §4.5 before §4.4: redact the whole stream, then tail it. Tailing
            # first would keep a value whose key name the cut had just removed.
            "stdout_tail": _tail(redact_text(stdout)),
            "stderr_tail": _tail(redact_text(stderr)),
            # Only on the schema-repair re-ask, so every other capture keeps
            # exactly the keys it always had.
            **({"repair": repair} if repair else {}),
        })
        write_below_root(root, target,
                         json.dumps(payload, indent=2).encode("utf-8"), mode=0o600,
                         resolve_root=recorded is None)
        return str(capture_dir / name)
    except (OSError, WriteSafetyError):  # pragma: no cover - diagnostics must never fail a run
        return None
