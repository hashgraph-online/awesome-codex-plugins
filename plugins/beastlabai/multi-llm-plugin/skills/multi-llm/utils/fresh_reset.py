"""The reset an apply phase's ``--fresh`` records, and the cutoff it moves.

``--fresh`` declares the earlier runs of the phase void and dispatches every
batch again. Clearing the processed records, the decisions and the
prior-changes log was not enough: every run resumes from the evidence on disk
(``write_resume.ResumeEvidence.result_counts_as_done``), and the result files
stayed valid for it. Whenever the ``--fresh`` run did not itself replace a
batch's result — a ``--fresh --dry-run`` or ``--dry-run-subagents``, a run
that failed before its first dispatch, or one that stopped part-way — the
next run kept the reverted batches as done (measured 2026-11-18).

Nothing on disk is moved or deleted. :func:`record_fresh_reset` stamps the
reset in ``state.json`` (:func:`reset_key`), in the same save as the clears
``--fresh`` makes, so the reset happens whole or not at all:

- ``ResumeEvidence.task_fingerprint`` hashes the stamp in, so every result
  bound before the reset reads as made from other inputs and is dispatched
  again (D2g). With no stamp the fingerprint is byte-identical to the one
  before this record existed.
- The cycle cutoff the evidence's dating rules use (report rows, pre-batch
  snapshot reuse, the backup's "recorded progress") is the later of the
  review's completion and the reset (:func:`cycle_cutoff`). ``--fresh``'s own
  refusal keeps the review completion: it must still see what the runs before
  a reset applied.
- The phase's task records (``apply-batch-N`` and its siblings) go back to
  ``pending`` with their reasons and verdicts dropped and their reset stamped,
  as ``implement``'s start-over does.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from .state_manager import (
    _parse_completion_time,
    clear_task_verdict,
    mark_tasks_reset_in_state,
)

#: Each apply kind's task-id prefix (``write_phase_bridge``'s adapters).
_TASK_PREFIXES: Dict[str, str] = {
    "apply_suggestions": "apply-batch-",
    "apply_task_suggestions": "apply-task-batch-",
    "apply_code_fixes": "apply-fix-batch-",
}


def reset_key(kind: str) -> str:
    """The top-level ``state.json`` key holding *kind*'s last ``--fresh`` reset
    (an ISO timestamp), merged as one value."""
    return f"fresh_reset_at_{kind}"


def reset_stamp(recorded: Any, kind: Any) -> Optional[str]:
    """*kind*'s recorded reset stamp in a ``state.json`` dict, or ``None``."""
    if not isinstance(recorded, dict) or kind not in _TASK_PREFIXES:
        return None
    value = recorded.get(reset_key(str(kind)))
    return value if isinstance(value, str) and value else None


def cycle_cutoff(
    reviewed_at: Optional[datetime], recorded: Any, kind: Any,
) -> Optional[datetime]:
    """The later of *reviewed_at* and *kind*'s last reset: what a record of
    this phase must not predate to be this run's evidence."""
    reset_at = _parse_completion_time(reset_stamp(recorded, kind))
    if reset_at is None:
        return reviewed_at
    if reviewed_at is None:
        return reset_at
    return max(reviewed_at, reset_at)


def record_fresh_reset(state: Any, kind: str) -> List[str]:
    """Stamp *kind*'s reset and put its task records back to ``pending``.

    Returns the task ids it reset. The caller saves *state*, in the same save
    as the clears ``--fresh`` makes. A kind that is not an apply kind records
    nothing.
    """
    if kind not in _TASK_PREFIXES:
        return []
    state.set(reset_key(kind), datetime.now().isoformat())
    own = re.compile(rf"^{re.escape(_TASK_PREFIXES[kind])}\d+$")
    ids = [task_id for task_id in state.get_all_task_statuses() if own.match(str(task_id))]
    for task_id in ids:
        if (state.get_task_status(task_id) != "pending"
                or state.get_task_status_reason(task_id)):
            state.update_task_status(task_id, "pending")
        clear_task_verdict(state.state, task_id)
    mark_tasks_reset_in_state(state.state, ids)
    return ids
