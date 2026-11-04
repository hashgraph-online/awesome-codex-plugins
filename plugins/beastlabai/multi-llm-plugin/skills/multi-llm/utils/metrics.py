"""Metrics utility for recording and reporting Task tool resource usage.

Records per-subagent metrics (tokens, tool uses, duration) into state JSON
and generates markdown reports for individual phases or cross-phase summaries.
"""

import argparse
import contextlib
import json
import os
import re
import sys
import tempfile
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import (
    Any, Callable, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence,
    Tuple,
)

try:
    from . import process_control
    from .stream_bootstrap import bootstrap_streams
    from .text_clip import clip
except ImportError:
    # Direct script invocation (`python utils/metrics.py`): sys.path[0]
    # is the utils/ directory, so import the sibling module directly.
    import process_control  # type: ignore[no-redef]
    from stream_bootstrap import bootstrap_streams
    from text_clip import clip  # type: ignore[no-redef]


#: The interprocess lock every raw read-modify-write of ``state.json`` holds
#: (:func:`state_file_lock`): a sibling of the state file, dot-prefixed,
#: created on demand and never unlinked (an unlinked lock file would put two
#: writers on two inodes of "the" lock; see ``process_control.FileMutex``).
STATE_LOCK_FILENAME = ".state.lock"

#: How long a raw state write waits for its turn. A holder runs one JSON read
#: and write plus, for ``util batch-done`` and ``util finalize-tracking``, the
#: dirty-tree census (seconds on a large repository); a host that records
#: several parallel tasks at once queues that many. Generous, because the only
#: thing the bound is for is a holder that is stopped rather than dead.
STATE_LOCK_TIMEOUT_S = 120.0


class StateLockTimeout(OSError):
    """The state-file lock was not free in time; nothing was written."""


#: Serializes this process's own raw state writes across threads; the file
#: lock serializes processes. Reentrant, because a holder may call a helper
#: that takes the lock again (see :func:`state_file_lock`).
_STATE_THREAD_LOCK = threading.RLock()

#: The state-file locks this process holds, by lock path. Only touched under
#: :data:`_STATE_THREAD_LOCK`, so a present key is this thread's outer frame.
_HELD_STATE_LOCKS: Dict[str, Any] = {}


@contextlib.contextmanager
def state_file_lock(state_path) -> Iterator[None]:
    """Hold ``<state dir>/.state.lock`` for one read-modify-write of *state_path*.

    The native write leg's per-batch records are separate processes the host
    may start in parallel — implement.md lets same-batch tasks run together,
    and ``util batch-done`` reads ``state.json``, runs the dirty-tree census
    (seconds since fix round 7) and writes the whole file back — so two
    unlocked records read the same file and the later write dropped the
    earlier one's ``task_status`` (fix round 8: two records started together
    left one). ``util batch-done``, ``util metrics record|start|finish`` and
    ``util finalize-tracking`` take this lock from their read to their write.

    Reentrant within a process (an inner frame does not take the file lock a
    second time: an OS lock is per open file, so it would wait on itself). A
    state file whose directory does not exist yet has nothing to lock. A lock
    not free within :data:`STATE_LOCK_TIMEOUT_S` raises
    :class:`StateLockTimeout` and the caller writes nothing: an unserialized
    write is exactly the lost record this lock exists to prevent.
    """
    with _STATE_THREAD_LOCK:
        folder = os.path.dirname(os.path.abspath(str(state_path)))
        key = os.path.realpath(os.path.join(folder, STATE_LOCK_FILENAME))
        if key in _HELD_STATE_LOCKS or not os.path.isdir(folder):
            yield
            return
        mutex = process_control.FileMutex(key)
        timeout_s = STATE_LOCK_TIMEOUT_S
        if not mutex.acquire(timeout_s=timeout_s, poll_interval_s=0.02):
            raise StateLockTimeout(
                f"{key} was not free within {timeout_s:g}s: another multi-llm "
                f"command is still writing {state_path} (or the lock file "
                f"cannot be opened), so nothing was written. Run this command "
                f"again once that one has finished."
            )
        _HELD_STATE_LOCKS[key] = mutex
        try:
            yield
        finally:
            del _HELD_STATE_LOCKS[key]
            mutex.release()


def _read_state(state_path: Path) -> dict:
    """Read and parse the state JSON file."""
    with open(state_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_state(state_path: Path, state: dict) -> None:
    """Write state JSON atomically (temp file + os.replace)."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    temp_fd, temp_path = tempfile.mkstemp(
        dir=str(state_path.parent),
        suffix=".tmp",
        prefix=".metrics_",
    )
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        temp_fd = None  # fdopen closes the fd
        os.replace(temp_path, str(state_path))
        temp_path = None  # file has been moved
    finally:
        if temp_fd is not None:
            try:
                os.close(temp_fd)
            except OSError:
                pass
        if temp_path is not None and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                pass


def format_duration(ms: Optional[int]) -> str:
    """Format milliseconds as human-readable duration.

    Examples:
        83000  -> "1m 23s"
        52000  -> "0m 52s"
        500    -> "<1s"
        0      -> "0s"
        None   -> "-"
    """
    if ms is None:
        return "-"
    if ms == 0:
        return "0s"
    if ms < 1000:
        return "<1s"
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}m {seconds}s"


def format_number(n: Optional[int]) -> str:
    """Format an integer with comma separators.

    Examples:
        12450 -> "12,450"
        0     -> "0"
        None  -> "-"
    """
    if n is None:
        return "-"
    return f"{n:,}"


def describe_usage(usage: Optional[Dict[str, Any]]) -> str:
    """One clause naming what a run cost, or ``""``.

    ``$25.05 est., 137,348 output tokens`` — the dollar figure first because
    it is the number a human acts on, the output count second because it is
    the one that says how far the run got. Input and cache counts are not
    rendered: they are on ``details["usage"]`` for anything that wants them,
    and a seven-figure cache-read count beside a failure reads as noise. Cost
    is rendered to the cent and dropped when it rounds to nothing, so a
    duration-only or free run says nothing rather than "$0.00".

    **Why "est." and not a bare figure.** ``cost_usd`` is whatever the CLI
    computed from its own price catalog: an estimate the runner relays, never
    a vendor invoice and never a billed amount, and a report that printed it
    unqualified would be read as one. One renderer serves every surface that
    names the number (the failed-slot error line, the ``**Models:**`` line,
    the HTML model badge and the report header), so the qualifier is attached
    once, here, rather than trusted to four call sites to remember.

    **Why this module.** It formats a usage metric, beside
    :func:`format_number` and :func:`format_duration`, and — unlike
    ``llm_client``, where it was first written for the failed-slot error line
    — it imports nothing but the standard library. That is what lets
    ``html_report_generator`` (which must keep working as
    ``python utils/html_report_generator.py``, where a relative-importing
    module cannot be loaded at all) render the same clause the fan-out logs,
    instead of a second copy of these rules drifting in a template.
    ``llm_client.describe_usage`` re-exports it for the callers that have
    always reached it there.
    """
    if not isinstance(usage, dict) or not usage:
        return ""
    parts = []
    cost = usage.get("cost_usd")
    if isinstance(cost, (int, float)) and not isinstance(cost, bool) and cost >= 0.005:
        parts.append(f"${cost:.2f} est.")
    output = usage.get("output_tokens")
    if isinstance(output, (int, float)) and not isinstance(output, bool) and output > 0:
        parts.append(f"{int(output):,} output tokens")
    return ", ".join(parts)


def _escape_pipe(text: str) -> str:
    """Escape pipe characters for markdown table cells."""
    return text.replace("|", "\\|")


def _should_colorize_stderr() -> bool:
    """True when ANSI color codes should be emitted on stderr.

    Suppressed when ``NO_COLOR`` is set (https://no-color.org/) or when stderr
    is not a TTY (e.g. piped to a file or captured by pytest).
    """
    if os.environ.get("NO_COLOR"):
        return False
    try:
        return bool(sys.stderr.isatty())
    except (AttributeError, ValueError):
        return False


def _colorize(text: str, code: str, enabled: bool) -> str:
    """Wrap ``text`` in an ANSI color escape when ``enabled``."""
    if not enabled:
        return text
    return f"\033[{code}m{text}\033[0m"


def start_phase_in_state(state: dict, phase: str, total_batches: int) -> None:
    """``start_phase``'s mutation, applied to an in-memory state dict.

    Split out so a holder of a live ``StateManager`` dict can record progress
    without becoming a *second* writer of ``state.json``: the two race, and the
    ``StateManager``'s own ``save()`` — which dumps its dict wholesale and never
    merges — always wins. Measured 2026-09-16: three independent runs finished
    with `metrics: null` after every batch had recorded one (F4).

    Each start also stamps a fresh ``run_id``, which every entry recorded under
    it carries. It is what tells a second record of the *same* event (collapsed
    by ``record_metric_in_state``) from a rerun's or a ``--resume``'s real
    measurement of the same label: ``metrics`` outlives runs in ``state.json``,
    and a rerun or resume starts the phase again, so it gets a new id.
    """
    progress = state.get("metrics_progress")
    if not isinstance(progress, dict):
        progress = {}
        state["metrics_progress"] = progress
    progress[phase] = {
        "started_at": datetime.now().isoformat(),
        "total_batches": int(total_batches),
        "run_id": uuid.uuid4().hex,
    }


#: ``metrics_progress.{phase}.withdrawn``: ``{task id: the task whose record
#: took it out}`` — the tasks this run's started total counted that it will
#: not dispatch after all (fix round 18).
WITHDRAWN_KEY = "withdrawn"


def withdraw_from_progress_in_state(
    state: dict, phase: str, task_ids: Iterable[str], cause: str,
) -> List[str]:
    """Take *task_ids* out of this run's started total; the ones taken out.

    Fix round 18 (live run 7, Claude Code stop 01): the native implement emit
    hands out a task that waits on a check's verdict (T007 behind check
    T002), so ``tasks_to_dispatch`` — what the host passes as
    ``--total-batches`` — counts it. When T002 reported problems, T007 was
    held and never dispatched, and the ``[ETA]`` line stopped at "batch 4/5"
    for good. ``util batch-done`` calls this for each handed-out task its
    record keeps from running (held by a check's findings, after a failed
    task, refused before dispatch): the stored ``total_batches`` drops by
    one per task, once, and :func:`record_metric_in_state` then counts
    against it. No-op when the phase was not started (no ``metrics start``)
    or the task is already out.
    """
    progress = (state.get("metrics_progress") or {}).get(phase)
    if not isinstance(progress, dict) or not _is_index(progress.get("total_batches")):
        return []
    withdrawn = progress.get(WITHDRAWN_KEY)
    if not isinstance(withdrawn, dict):
        withdrawn = {}
    taken: List[str] = []
    for task_id in task_ids:
        task_id = str(task_id)
        if not task_id or task_id in withdrawn:
            continue
        withdrawn[task_id] = str(cause)
        taken.append(task_id)
    if taken:
        progress[WITHDRAWN_KEY] = withdrawn
        progress["total_batches"] = max(int(progress["total_batches"]) - len(taken), 0)
    return taken


def restore_to_progress_in_state(state: dict, phase: str, cause: str) -> List[str]:
    """Put back the tasks *cause*'s earlier record took out of the total
    (:func:`withdraw_from_progress_in_state`): that task is recorded again,
    and its new record decides afresh. The ones put back."""
    progress = (state.get("metrics_progress") or {}).get(phase)
    if not isinstance(progress, dict) or not _is_index(progress.get("total_batches")):
        return []
    withdrawn = progress.get(WITHDRAWN_KEY)
    if not isinstance(withdrawn, dict):
        return []
    back = sorted(t for t, by in withdrawn.items() if by == str(cause))
    for task_id in back:
        del withdrawn[task_id]
    if back:
        progress["total_batches"] = int(progress["total_batches"]) + len(back)
    if not withdrawn:
        progress.pop(WITHDRAWN_KEY, None)
    return back


#: ``metrics_progress.{phase}.failed``: the tasks this run recorded
#: ``failed`` after a runner ran them (fix round 22). A task refused before
#: dispatch is withdrawn instead. Their run stops short, so the line of the
#: last task does not say "complete" and ``util metrics finish`` closes on
#: "run stopped" rather than "phase complete", as the executor does.
FAILED_KEY = "failed"


def mark_failed_in_progress(
    state: dict, phase: str, task_id: str, *, failed: bool,
) -> None:
    """Record whether *task_id*'s latest record in this run is a failure.
    No-op when the phase was not started."""
    progress = (state.get("metrics_progress") or {}).get(phase)
    if not isinstance(progress, dict):
        return
    current = {
        str(t) for t in (progress.get(FAILED_KEY) or []) if str(t) != str(task_id)
    }
    if failed:
        current.add(str(task_id))
    if current:
        progress[FAILED_KEY] = sorted(current, key=_id_key)
    else:
        progress.pop(FAILED_KEY, None)


#: A metric entry whose task failed carries ``"failed": true`` (fix round
#: 24, live run 10 #5: OpenCode's T002 timed out at its 1200 s slot budget
#: and its line read "task 2/11 done in 20m 5s · ~109m 30s remaining"). Its
#: ``[ETA]`` line says it failed, and no remaining-time estimate averages its
#: duration in or counts it as progress (:func:`_compute_eta`).
FAILED_ENTRY_KEY = "failed"
#: How a half-applied task's reason starts on record (``util batch-done
#: --partial``; ``write_batch_scheduler.HALF_APPLIED_PREFIX``, spelled here so
#: this module imports nothing heavy: a test holds the two together).
HALF_APPLIED_PREFIX = "half-applied: "
#: What a failed task's line adds when it changed files before it failed.
HALF_APPLIED_WORDS = "half-applied: its edits are kept"
#: How much of a native failed task's recorded reason its line quotes.
FAILURE_WORDS_CHARS = 80


def label_task_id(label: str) -> Optional[str]:
    """The task id an implement record's label starts with (``T002: Build
    the track``, ``instructions/implement.md``'s ``--label``), or ``None``
    (an apply batch's ``Batch 2 (index.html)``)."""
    match = re.match(r"\s*([A-Za-z][\w.-]*):\s", str(label or ""))
    return match.group(1) if match else None


#: Fix round 25 (review of round 24, stops #2): a native record that names
#: no task (no ``--task-id``, a label not starting with ``<id>: ``) while
#: two or more failed tasks of this run have no record yet is marked
#: ``"no_task_id": true``: which task it measured is never guessed, so it is
#: no progress — no estimate averages it in or counts it (:func:`_compute_eta`)
#: — and ``[METRICS_NO_TASK_ID]`` asks for ``--task-id``.
NO_TASK_ID_ENTRY_KEY = "no_task_id"
NO_TASK_ID_MARKER = "[METRICS_NO_TASK_ID]"


def unrecorded_failures(
    state: dict, phase: str, entries: Sequence[Any],
) -> List[str]:
    """The tasks this run's ``util batch-done`` recorded ``failed``
    (:data:`FAILED_KEY`) that no metric entry of this run measures yet, by
    its ``task_id`` or the id its label starts with (fix round 25)."""
    progress = (state.get("metrics_progress") or {}).get(phase)
    if not isinstance(progress, dict):
        return []
    run_id = progress.get("run_id")
    measured = {
        str(e.get("task_id") or label_task_id(str(e.get("label") or "")) or "")
        for e in entries
        if isinstance(e, dict) and run_id and e.get("run_id") == run_id
    }
    return [
        str(t) for t in (progress.get(FAILED_KEY) or []) if str(t) not in measured
    ]


def _named_ids(ids: Sequence[str]) -> str:
    """``T002``, ``T002 and T003``, ``T002, T003 and T004``; past
    :data:`LEFT_OUT_IDS_SHOWN` ids the rest counted."""
    ids = sorted((str(i) for i in ids), key=_id_key)
    shown = ids[:LEFT_OUT_IDS_SHOWN]
    if len(ids) > len(shown):
        return ", ".join(shown) + f" and {len(ids) - len(shown)} more"
    return shown[0] if len(shown) == 1 else ", ".join(shown[:-1]) + f" and {shown[-1]}"


def native_failure(
    state: dict, phase: str, task_id: Optional[str],
) -> Optional[Tuple[str, bool]]:
    """``(what failed, half-applied)`` for a task this run's ``util
    batch-done`` recorded ``failed`` (:data:`FAILED_KEY`), read off the reason
    it recorded (the host's ``--reason``, cut at a word; ``--partial``
    prefixes :data:`HALF_APPLIED_PREFIX`); ``None`` for any other task, a
    task refused before dispatch included (fix round 24)."""
    if not task_id:
        return None
    progress = (state.get("metrics_progress") or {}).get(phase)
    if not isinstance(progress, dict) or str(task_id) not in {
        str(t) for t in (progress.get(FAILED_KEY) or [])
    }:
        return None
    reasons = state.get("task_status_reasons")
    reason = " ".join(str(
        (reasons.get(str(task_id)) if isinstance(reasons, dict) else "") or ""
    ).split())
    half = (reason + " ").startswith(HALF_APPLIED_PREFIX)
    if half:
        reason = reason[len(HALF_APPLIED_PREFIX):].strip()
    return (clip(reason, FAILURE_WORDS_CHARS) if reason else ""), half


#: ``metrics_progress.{phase}.named_out``: the tasks taken out of this run's
#: total (:data:`WITHDRAWN_KEY`) that a line already named (fix round 24,
#: live run 10 #7: the stop fixture's lines went "task 1/5", "task 2/4" and
#: nothing said why). The next line after a record that took one out names
#: it beside the new total.
NAMED_OUT_KEY = "named_out"


def _newly_withdrawn_tail(state: dict, phase: str, progress: dict) -> str:
    """What left this run's total since its last line, in
    :func:`left_out_tail`'s words, or ``""``; remembers what it named."""
    withdrawn = progress.get(WITHDRAWN_KEY)
    withdrawn = withdrawn if isinstance(withdrawn, dict) else {}
    named = {str(t) for t in (progress.get(NAMED_OUT_KEY) or [])}
    fresh = {str(t): c for t, c in withdrawn.items() if str(t) not in named}
    if withdrawn:
        progress[NAMED_OUT_KEY] = sorted((str(t) for t in withdrawn), key=_id_key)
    else:
        progress.pop(NAMED_OUT_KEY, None)
    if not fresh:
        return ""
    return left_out_tail(
        _withdrawn_left_out(state, {WITHDRAWN_KEY: fresh}), unit=eta_unit(phase))


#: ``state.json``'s ``metrics_left_out.{phase}``: ``{task id: how it was
#: left}`` for the tasks the native implement emit kept out of the batches it
#: handed the host — refused by the write policy, after a refused task, held
#: by a check whose findings stand (fix round 22, live run 9 #1). The host's
#: ``util metrics finish`` names them on its closing line, as the executor's
#: closing line names the same tasks, also when nothing was dispatched and
#: the host ran no ``util metrics start``. Each emit replaces it; ``finish``
#: removes it.
LEFT_OUT_KEY = "metrics_left_out"
#: How a task was left: refused before dispatch, held by a check
#: (:func:`left_out_check`), or plainly not run.
LEFT_REFUSED = "refused"
LEFT_CHECK_PREFIX = "check:"
LEFT_NOT_RUN = ""
#: A task the run counted that it kept from an earlier run instead (fix
#: round 24: only a line's dropped total names one).
LEFT_KEPT = "kept"
#: How many ids one clause of :func:`left_out_tail` names, and how many
#: clauses it shows.
LEFT_OUT_IDS_SHOWN = 5
LEFT_OUT_CLAUSES_SHOWN = 4


def left_out_check(check_id: str) -> str:
    """How a task held by check *check_id*'s findings was left."""
    return f"{LEFT_CHECK_PREFIX}{check_id}"


def _id_key(task_id: str) -> List[Any]:
    """Sort key for task ids by their numbers: T9 before T10."""
    return [int(part) if part.isdigit() else part
            for part in re.split(r"(\d+)", str(task_id))]


def set_left_out_in_state(
    state: dict, phase: str, left_out: Mapping[str, str],
) -> None:
    """Replace *phase*'s left-out tasks (:data:`LEFT_OUT_KEY`); an empty
    mapping removes them."""
    stash = state.get(LEFT_OUT_KEY)
    stash = dict(stash) if isinstance(stash, dict) else {}
    if left_out:
        stash[phase] = {str(k): str(v or "") for k, v in sorted(left_out.items())}
    else:
        stash.pop(phase, None)
    if stash:
        state[LEFT_OUT_KEY] = stash
    else:
        state.pop(LEFT_OUT_KEY, None)


def left_out_in_state(state: dict, phase: str) -> Dict[str, str]:
    """*phase*'s left-out tasks on record, ``{}`` when none."""
    stash = state.get(LEFT_OUT_KEY)
    entry = stash.get(phase) if isinstance(stash, dict) else None
    if not isinstance(entry, dict):
        return {}
    return {str(k): str(v or "") for k, v in entry.items()}


def _withdrawn_left_out(state: dict, entry: dict) -> Dict[str, str]:
    """A started run's withdrawn tasks, as :func:`left_out_tail` names them:
    the record that took a task out was its own (refused at ``util
    write-prompt``), a check's with findings (held), or a failed task's."""
    withdrawn = entry.get(WITHDRAWN_KEY)
    if not isinstance(withdrawn, dict):
        return {}
    findings = state.get("task_check_findings")
    checks = {str(k) for k in findings} if isinstance(findings, dict) else set()
    left: Dict[str, str] = {}
    for task_id, cause in withdrawn.items():
        if str(cause) == str(task_id):
            left[str(task_id)] = LEFT_REFUSED
        elif str(cause) in checks:
            left[str(task_id)] = left_out_check(str(cause))
        else:
            left[str(task_id)] = LEFT_NOT_RUN
    return left


def left_out_tail(left_out: Mapping[str, str], *, unit: str = "task") -> str:
    """What a run left, for its closing ``[ETA]`` line (fix round 22):
    ``T005 refused before dispatch; T006 not run; T007 not run: check T002
    reported problems``. One clause per way a task was left, in task order;
    at most :data:`LEFT_OUT_IDS_SHOWN` ids a clause and
    :data:`LEFT_OUT_CLAUSES_SHOWN` clauses, the rest counted in *unit*s
    (:func:`eta_unit`: an apply phase's are batches, fix round 23). Both
    legs render it, so the same story closes on the same words."""
    groups: Dict[str, List[str]] = {}
    for task_id, how in left_out.items():
        groups.setdefault(str(how or ""), []).append(str(task_id))
    clauses: List[Tuple[List[Any], str, int]] = []
    for how, ids in groups.items():
        ids = sorted(ids, key=_id_key)
        shown = ids[:LEFT_OUT_IDS_SHOWN]
        named = ", ".join(shown) + (
            f" and {len(ids) - len(shown)} more" if len(ids) > len(shown) else ""
        )
        if how == LEFT_REFUSED:
            text = f"{named} refused before dispatch"
        elif how == LEFT_KEPT:
            text = f"{named} kept from an earlier run"
        elif how.startswith(LEFT_CHECK_PREFIX):
            text = (
                f"{named} not run: check {how[len(LEFT_CHECK_PREFIX):]} "
                f"reported problems"
            )
        else:
            text = f"{named} not run"
        clauses.append((_id_key(ids[0]), text, len(ids)))
    clauses.sort(key=lambda clause: clause[0])
    shown_clauses = clauses[:LEFT_OUT_CLAUSES_SHOWN]
    rest = sum(count for _key, _text, count in clauses[LEFT_OUT_CLAUSES_SHOWN:])
    return "; ".join(
        [text for _key, text, _count in shown_clauses]
        + ([f"{rest} more {_units(unit)} not run"] if rest else [])
    )


#: ``state.json``'s ``metrics_set_aside.{phase}``: ``{task id: how}`` for the
#: tasks the human-task plan set aside, which no runner runs: a manual task
#: left for the user, a task skipped with one, a task skipped at the user's
#: request and one skipped with it (fix round 24, Claude Code racing #6:
#: "task 10/10 done … ALL TASKS COMPLETE" while the manual T011 and T012
#: were left). The native emit writes it, each emit replaces it and
#: ``finish`` removes it; the line that reaches N/N names them
#: (:func:`set_aside_tail`), on the executor from its own plan.
SET_ASIDE_KEY = "metrics_set_aside"
SET_ASIDE_MANUAL = "manual"
SET_ASIDE_WITH_MANUAL = "with-manual"
SET_ASIDE_SKIPPED = "skipped"
SET_ASIDE_WITH_SKIPPED = "with-skipped"
#: Each way a task is set aside, in the order the line names them, with its
#: words (the summary's accounting line's).
_SET_ASIDE_WORDS = (
    (SET_ASIDE_MANUAL, "left for you (manual)"),
    (SET_ASIDE_WITH_MANUAL, "skipped with a manual task"),
    (SET_ASIDE_SKIPPED, "skipped at your request"),
    (SET_ASIDE_WITH_SKIPPED, "skipped with a skipped task"),
)
#: What the N/N line says once the plan set tasks aside: every task the run
#: dispatched is complete, and the line names the others.
ALL_DISPATCHED_COMPLETE = "ALL DISPATCHED TASKS COMPLETE"


def set_set_aside_in_state(
    state: dict, phase: str, aside: Mapping[str, str],
) -> None:
    """Replace *phase*'s set-aside tasks (:data:`SET_ASIDE_KEY`); an empty
    mapping removes them."""
    stash = state.get(SET_ASIDE_KEY)
    stash = dict(stash) if isinstance(stash, dict) else {}
    if aside:
        stash[phase] = {str(k): str(v or "") for k, v in sorted(aside.items())}
    else:
        stash.pop(phase, None)
    if stash:
        state[SET_ASIDE_KEY] = stash
    else:
        state.pop(SET_ASIDE_KEY, None)


def set_aside_in_state(state: dict, phase: str) -> Dict[str, str]:
    """*phase*'s set-aside tasks on record, ``{}`` when none."""
    stash = state.get(SET_ASIDE_KEY)
    entry = stash.get(phase) if isinstance(stash, dict) else None
    if not isinstance(entry, dict):
        return {}
    return {str(k): str(v or "") for k, v in entry.items()}


def set_aside_tail(aside: Mapping[str, str]) -> str:
    """The tasks a complete run did not dispatch, for its N/N line:
    ``T011, T012 left for you (manual); T013 skipped with a manual task``.
    One clause per way, at most :data:`LEFT_OUT_IDS_SHOWN` ids each; ``""``
    when nothing was set aside."""
    groups: Dict[str, List[str]] = {}
    for task_id, how in aside.items():
        groups.setdefault(str(how or ""), []).append(str(task_id))
    clauses = []
    for how, words in _SET_ASIDE_WORDS:
        ids = sorted(groups.get(how) or [], key=_id_key)
        if not ids:
            continue
        shown = ids[:LEFT_OUT_IDS_SHOWN]
        named = ", ".join(shown) + (
            f" and {len(ids) - len(shown)} more" if len(ids) > len(shown) else ""
        )
        clauses.append(f"{named} {words}")
    return "; ".join(clauses)


def eta_unit(phase: str) -> str:
    """What the ``[ETA]`` lines of *phase* count (fix round 22, live run 9):
    implement counts one record per task it dispatches, so its lines say
    "task 1/5" beside "Organized into 3 execution batches: 5 task(s)"; the
    other phases count batches."""
    return "task" if phase == "implement" else "batch"


def _units(unit: str) -> str:
    """*unit*'s count word: ``task(s)``, ``batch(es)``."""
    return "batch(es)" if unit == "batch" else f"{unit}(s)"


def closing_line(
    phase: str, *, done: int, total: int, verb: str = "stopped",
    elapsed_ms: Optional[int] = None, tail: str = "", why: str = "",
) -> str:
    """The closing ``[ETA]`` line of a run that ends short of completing
    its phase, on both legs (fix round 22): ``run stopped after task 4/4 ·
    <what it left>``, ``run stopped with nothing dispatched · …`` when it
    dispatched nothing, then *why* (a failed verify command)."""
    if done <= 0 and total <= 0:
        head = f"run {verb} with nothing dispatched"
    elif done <= 0:
        head = f"run {verb} before any of its {total} {_units(eta_unit(phase))} finished"
    else:
        timing = f" in {format_duration(elapsed_ms)}" if elapsed_ms is not None else ""
        head = f"run {verb} after {eta_unit(phase)} {done}/{total}{timing}"
    return f"[ETA] {phase}: {head}" + "".join(
        f" · {part}" for part in (tail, why) if part
    )


def native_ends_short(state: dict, phase: str) -> bool:
    """Whether the native run on record will end short of completing its
    phase: a record took tasks out of its total or failed, or the emit left
    tasks out (fix round 22). Its last ``[ETA]`` line then claims no
    completion."""
    progress = (state.get("metrics_progress") or {}).get(phase)
    if isinstance(progress, dict) and (
        progress.get(WITHDRAWN_KEY) or progress.get(FAILED_KEY)
    ):
        return True
    return bool(left_out_in_state(state, phase))


def start_phase(state_path: Path, phase: str, total_batches: int) -> None:
    """Record the start time and total batch count for a phase.

    Writes ``metrics_progress.{phase}`` = {"started_at": ISO timestamp,
    "total_batches": int, "run_id": uuid4 hex}. Used by ``record_metric`` to
    compute wall-clock ETA and to recognise this run's own entries.
    Idempotent: a second call for the same phase replaces the prior entry
    (necessary so ``--resume`` runs reset the progress baseline, and start a new
    ``run_id``).
    """
    with state_file_lock(state_path):
        state = _read_state(state_path)
        start_phase_in_state(state, phase, total_batches)
        _write_state(state_path, state)


def finish_phase_in_state(
    state: dict, phase: str
) -> Optional[Tuple[Optional[int], str]]:
    """``finish_phase``'s mutation, applied to an in-memory state dict.

    Returns None — leaving ``state`` untouched — when the phase was never
    started and its emit left no task out; otherwise pops the progress entry
    (and the left-out tasks, :data:`LEFT_OUT_KEY`) and returns
    ``(elapsed_ms, line)``, where ``line`` is the closing ``[ETA] … phase
    complete`` line, or the run's stop line (:func:`closing_line`). It is
    **returned, not printed**, mirroring ``record_metric_in_state``: the
    caller decides where it goes — stderr for the CLI, the phase log for the
    scheduler, which is where every other ``[ETA]`` line of that run already
    went (F7). See ``start_phase_in_state`` for why the in-memory form exists.
    """
    progress = state.get("metrics_progress") or {}
    entry = progress.pop(phase, None)
    left = left_out_in_state(state, phase)
    if entry is None:
        if not left:
            return None
        # Fix round 22 (live run 9 #1, 01b/01c): a native resume that
        # handed out nothing ran no `util metrics start`, and its `finish`
        # printed nothing; every ending closes its run's lines, this one too.
        set_left_out_in_state(state, phase, {})
        set_set_aside_in_state(state, phase, {})
        return None, closing_line(
            phase, done=0, total=0, tail=left_out_tail(left, unit=eta_unit(phase)))
    set_left_out_in_state(state, phase, {})
    set_set_aside_in_state(state, phase, {})

    elapsed_ms: Optional[int] = None
    started_at_raw = entry.get("started_at")
    if started_at_raw:
        try:
            started_at = datetime.fromisoformat(started_at_raw)
            elapsed_ms = int((datetime.now() - started_at).total_seconds() * 1000)
        except (ValueError, TypeError):
            elapsed_ms = None

    # Clean up empty progress dict
    if not progress and "metrics_progress" in state:
        del state["metrics_progress"]
    else:
        state["metrics_progress"] = progress

    left.update(_withdrawn_left_out(state, entry))
    if left or entry.get(FAILED_KEY):
        # Fix round 21 (review of round 20, #1): a native run whose records
        # kept tasks from running (`util batch-done`: held by a check's
        # findings, after a failed task, refused at `util write-prompt`)
        # did not complete its phase, and its closing line said "phase
        # complete" after a check held the last tasks back. Fix round 22
        # (live run 9 #1): the tasks its emit left out are named too, in the
        # executor's closing line's words, and a run whose last task failed
        # closes on "run stopped" as well.
        run_id = entry.get("run_id")
        entries = (state.get("metrics") or {}).get(phase)
        done = sum(
            1 for item in (entries if isinstance(entries, list) else [])
            if isinstance(item, dict) and run_id and item.get("run_id") == run_id
        )
        total = int(entry["total_batches"]) if _is_index(entry.get("total_batches")) else done
        return elapsed_ms, closing_line(
            phase, done=done, total=total, elapsed_ms=elapsed_ms,
            tail=left_out_tail(left, unit=eta_unit(phase)),
        )

    color_on = _should_colorize_stderr()
    complete_segment = _colorize(
        f"phase complete in {format_duration(elapsed_ms)}", "1;32", color_on,
    )
    return elapsed_ms, f"[ETA] {phase}: {complete_segment}"


#: The write run whose ``[ETA]`` lines no ending has closed yet (fix round
#: 21): a callable taking the signal's name and returning that run's closing
#: line. The write scheduler opens it once its baseline is stamped and closes
#: it on every ending; a detached worker's abort handler asks for the line
#: (:func:`aborted_eta_line`), because it ends the process with ``os._exit``
#: before any ``finally`` of the run could print it.
_OPEN_ETA_RUN: Optional[Callable[[str], Optional[str]]] = None


def open_eta_run(closer: Callable[[str], Optional[str]]) -> None:
    """Name the run whose ``[ETA]`` lines an abort closes."""
    global _OPEN_ETA_RUN
    _OPEN_ETA_RUN = closer


def close_eta_run(closer: Callable[[str], Optional[str]]) -> None:
    """Forget *closer*, if it is still the open run (a later run's stays)."""
    global _OPEN_ETA_RUN
    if _OPEN_ETA_RUN is not None and _OPEN_ETA_RUN == closer:
        _OPEN_ETA_RUN = None


def aborted_eta_line(cause: str) -> Optional[str]:
    """The open run's closing ``[ETA]`` line for an abort by *cause* (the
    signal's name), or ``None``. Called from a signal handler: it reads, and
    never raises."""
    closer = _OPEN_ETA_RUN
    if closer is None:
        return None
    try:
        return closer(cause)
    except Exception:  # noqa: BLE001 - an abort's record must still be written
        return None


def finish_phase(state_path: Path, phase: str) -> Optional[int]:
    """Remove ``metrics_progress.{phase}`` and return total elapsed ms.

    Returns None if the phase was never started (graceful no-op).
    """
    with state_file_lock(state_path):
        state = _read_state(state_path)
        if (
            phase not in (state.get("metrics_progress") or {})
            and not left_out_in_state(state, phase)
        ):
            # Never started and nothing left out: nothing to mutate, so
            # nothing to write back.
            return None
        finished = finish_phase_in_state(state, phase)
        if finished is None:  # pragma: no cover - guarded above
            return None
        elapsed_ms, line = finished
        _write_state(state_path, state)
    # The CLI leg is the one that owns stderr; the in-memory twin only returns
    # the line (F7).
    print(line, file=sys.stderr)
    return elapsed_ms


def _compute_eta(
    entries: list,
    progress: Optional[dict],
    phase: str,
    batch_index: int,
    total_batches: int,
    this_duration_ms: Optional[int],
    colorize: bool = False,
    ends_short: bool = False,
    *,
    failure: Optional[str] = None,
    half_applied: bool = False,
    dropped: str = "",
    set_aside: str = "",
) -> dict:
    """Compute ETA from two independent remaining-time estimates.

    ``per_item_ms`` is ``mean(batch duration) * batches_remaining`` and
    ``wall_clock_ms`` is ``(elapsed / done) * batches_remaining`` — both are
    whole-phase remaining-time estimates from different signals, not a
    per-item duration, however the first one used to be labelled: printing
    both used to read as three quantities (a per-item time, a wall-clock
    time, and a remaining time barely different from either), when a batch
    ≠ item phase made "per-item" actively misleading (F13, 2026-09-16). The
    rendered line now reports only the number a reader acts on — ``eta_ms``,
    the min of the two — and keeps the intermediates in the returned dict
    for callers/tests that want them.

    Args:
        entries: List of metric entries for this phase (including the just-
            recorded one).
        progress: ``metrics_progress.{phase}`` dict (or None if absent).
        phase: Phase name.
        batch_index: 1-based index of the just-completed batch.
        total_batches: Total batch count for the phase.
        this_duration_ms: Duration of the just-completed batch (for the
            `done in X` display).
        failure: ``None`` for a task that did not fail; else what failed
            (``""`` when nothing says), and the line reads ``task 2/11
            failed (timeout) after 20m 5s`` with no estimate (fix round 24).
        half_applied: the failed task changed files before it failed.
        dropped: why the total dropped since the run's last line
            (``T007 not run: check T002 reported problems``), or ``""``.
        set_aside: the tasks the plan set aside (:func:`set_aside_tail`),
            named on the N/N line of a run that completes, or ``""``.

    Returns:
        Dict with keys: ``per_item_ms``, ``wall_clock_ms``, ``eta_ms``,
        ``elapsed_ms``, ``done``, ``total``, ``remaining``, ``line``.
    """
    done = max(int(batch_index), 0)
    total = max(int(total_batches), 0)
    remaining = max(total - done, 0) if total > 0 else 0

    def failed(entry: Any) -> bool:
        # Fix round 25: a record that named no task among several failed
        # ones (:data:`NO_TASK_ID_ENTRY_KEY`) is no progress either.
        return isinstance(entry, dict) and bool(
            entry.get(FAILED_ENTRY_KEY) or entry.get(NO_TASK_ID_ENTRY_KEY))

    # Fix round 24 (live run 10 #5): a failed task is no progress. Its
    # duration (a 20-minute timeout) is not how long a task takes, so it is
    # averaged in nowhere, and the wall-clock rate is the time the run spent
    # on the tasks that did not fail, over those tasks.
    durations = [
        e["duration_ms"] for e in entries
        if isinstance(e, dict) and e.get("duration_ms") is not None and not failed(e)
    ]
    per_item_ms: Optional[int] = None
    if durations:
        per_item_ms = (sum(durations) // len(durations)) * remaining
    run_id = progress.get("run_id") if isinstance(progress, dict) else None
    failed_here = [
        e for e in entries if failed(e) and run_id and e.get("run_id") == run_id
    ]
    failed_ms = sum(int(e.get("duration_ms") or 0) for e in failed_here)

    wall_clock_ms: Optional[int] = None
    elapsed_ms: Optional[int] = None
    if progress and progress.get("started_at"):
        try:
            started_at = datetime.fromisoformat(progress["started_at"])
            elapsed_ms = int((datetime.now() - started_at).total_seconds() * 1000)
            worked = done - len(failed_here)
            worked_ms = elapsed_ms - failed_ms
            if worked > 0 and worked_ms >= 0:
                wall_clock_ms = (worked_ms // worked) * remaining
        except (ValueError, TypeError):
            elapsed_ms = None
            wall_clock_ms = None

    if per_item_ms is not None and wall_clock_ms is not None:
        eta_ms: Optional[int] = min(per_item_ms, wall_clock_ms)
    elif per_item_ms is not None:
        eta_ms = per_item_ms
    elif wall_clock_ms is not None:
        eta_ms = wall_clock_ms
    else:
        eta_ms = None

    unit = eta_unit(phase)
    # Fix round 24 (live run 10 #7): the line whose total dropped says why.
    why_total = [f"total now {total} ({dropped})"] if dropped else []
    if failure is not None:
        # Fix round 24 (live run 10 #5): what happened, never "done", and
        # no estimate (the run stops short, or goes on without it).
        parts = [
            f"[ETA] {phase}: {unit} {done}/{total} failed"
            + (f" ({failure})" if failure else "")
            + (f" after {format_duration(this_duration_ms)}"
               if this_duration_ms is not None else "")
        ]
        if half_applied:
            parts.append(HALF_APPLIED_WORDS)
        parts += why_total
    else:
        parts = [
            f"[ETA] {phase}: {unit} {done}/{total} done in "
            f"{format_duration(this_duration_ms)}"
        ] + why_total
        if remaining == 0:
            # Fix round 22 (live run 9 #1): a run about to stop short of
            # completing its phase (*ends_short*) said "ALL BATCHES COMPLETE"
            # on this line and "run stopped" on the next. "N/N done" is all
            # that is true of it; its closing line says what it left.
            if not ends_short:
                if unit != "task":
                    parts.append(_colorize("ALL BATCHES COMPLETE", "1;32", colorize))
                elif set_aside:
                    # Fix round 24 (Claude Code racing #6): manual tasks
                    # left for the user are not complete.
                    parts.append(_colorize(ALL_DISPATCHED_COMPLETE, "1;32", colorize))
                    parts.append(set_aside)
                else:
                    parts.append(_colorize("ALL TASKS COMPLETE", "1;32", colorize))
        elif eta_ms is not None:
            parts.append(_colorize(f"~{format_duration(eta_ms)} remaining", "1;36", colorize))

    if done > total:
        # Defensive: caller bug — emit a warning but still return a usable line.
        parts.append(_colorize("WARNING: batch_index > total_batches", "1;33", colorize))

    line = " · ".join(parts)

    return {
        "per_item_ms": per_item_ms,
        "wall_clock_ms": wall_clock_ms,
        "eta_ms": eta_ms,
        "elapsed_ms": elapsed_ms,
        "done": done,
        "total": total,
        "remaining": remaining,
        "line": line,
    }


def normalize_recorded_executor(value: str) -> str:
    """Map a legacy ``subagent_type`` value onto the recorded executor value.

    ``general-purpose`` is Claude Code vocabulary that exists on no other host
    and carries no information, so it records as ``agent``; ``human`` keeps its
    meaning (no invoker ever ran it). Anything else — notably the resolved
    ``provider:model`` runner spec the Python executor records — passes through
    verbatim, which is what makes the two invokers read differently in
    ``--status`` output instead of both printing ``general-purpose``.
    """
    if value == "general-purpose":
        return "agent"
    return value


#: The measured fields of a metric entry. A record carrying none of them, or
#: only zeros in them, is *empty*: nothing was measured (the host's subagent
#: tool reports no usage) or a zero was fabricated for a value nobody had.
_MEASURED_FIELDS = ("token_count", "tool_uses", "duration_ms")

#: The runner and measurement fields compared separately from task identity.
_PAYLOAD_FIELDS = ("subagent_type",) + _MEASURED_FIELDS

_EMPTY_NONE = "no numbers"
_EMPTY_ZERO = "only zeros"


def _current_run_id(state: dict, phase: str) -> Optional[str]:
    """The ``run_id`` ``start_phase_in_state`` stamped for ``phase``, or None.

    None when the phase was never started (or finished), or was started before
    run ids existed: such a record appends unchecked, exactly as before.
    """
    progress = state.get("metrics_progress")
    if not isinstance(progress, dict):
        return None
    entry = progress.get(phase)
    if not isinstance(entry, dict):
        return None
    run_id = entry.get("run_id")
    return run_id if isinstance(run_id, str) and run_id else None


def _is_index(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _emptiness(entry: dict) -> Optional[str]:
    """Why ``entry`` measured nothing, or None when it carries a real number."""
    measured = [entry[k] for k in _MEASURED_FIELDS if entry.get(k) is not None]
    if not measured:
        return _EMPTY_NONE
    if all(value == 0 for value in measured):
        return _EMPTY_ZERO
    return None


def _payload(entry: dict) -> Dict[str, Any]:
    return {k: entry[k] for k in _PAYLOAD_FIELDS if entry.get(k) is not None}


def _describe_event(phase: str, label: str, batch_index: Optional[int]) -> str:
    where = f" (batch {batch_index})" if batch_index is not None else ""
    return f'{phase}: "{label}"{where}'


def _metric_task_id(entry: dict) -> Optional[str]:
    """The recorded identity, including an implement label that names it."""
    if entry.get("task_id"):
        return str(entry["task_id"])
    named = label_task_id(str(entry.get("label") or ""))
    return named if named and re.fullmatch(r"T\d+", named) else None


def _enrich_metric_identity(existing: dict, new: dict) -> dict:
    """Keep a measurement, adding its identity/failure without erasing either.

    A previously ambiguous record becomes usable once its task is named.
    The caller checks conflicting identities and measurements first.
    """
    merged = dict(existing)
    if new.get("task_id"):
        merged["task_id"] = str(new["task_id"])
    if new.get(FAILED_ENTRY_KEY):
        merged[FAILED_ENTRY_KEY] = True
    if merged.get("task_id"):
        merged.pop(NO_TASK_ID_ENTRY_KEY, None)
    elif new.get(NO_TASK_ID_ENTRY_KEY):
        merged[NO_TASK_ID_ENTRY_KEY] = True
    return merged


def _replacement(existing: dict, new: dict, keep_measured: bool) -> dict:
    """``new``, keeping any field of ``existing`` it does not carry itself.

    The executor role always survives. A measured field survives only from a
    non-empty entry (``keep_measured``): carrying an empty entry's zeros into
    the replacement would re-fabricate exactly what the replacement removes.
    """
    merged = _enrich_metric_identity(new, existing)
    for key in _PAYLOAD_FIELDS:
        if key in merged or existing.get(key) is None:
            continue
        if key == "subagent_type" or keep_measured:
            merged[key] = existing[key]
    return merged


def _collapse_duplicate(
    entries: list, index: int, new: dict, event: str
) -> bool:
    """Settle a second record of the event ``entries[index]`` already holds.

    Returns True when ``entries[index]`` gained numbers, task identity or a
    failure classification (so the caller's ``[ETA]`` line reflects them),
    False when the new record was dropped. Nothing is appended: two entries
    for one batch would count it twice in every per-phase total and average.
    """
    existing = entries[index]
    old_empty = _emptiness(existing)
    new_empty = _emptiness(new)
    old_id, new_id = _metric_task_id(existing), _metric_task_id(new)
    if old_id and new_id and old_id != new_id:
        print(
            f"[METRICS_CONFLICT] {event} recorded twice in this run with "
            f"different task_id: kept {old_id}, dropped {new_id}",
            file=sys.stderr,
        )
        return False
    enriched = _enrich_metric_identity(existing, new)

    def keep_enrichment() -> bool:
        if enriched == existing:
            return False
        entries[index] = enriched
        print(
            f"[METRICS_DUPLICATE] {event} recorded twice in this run; "
            "kept the measurement and added its task identity or failure",
            file=sys.stderr,
        )
        return True

    if new_empty is not None:
        # An empty record never displaces a measured one. Of two empty ones,
        # the one without numbers is kept over the all-zero one (whose zeros
        # were made up and would average in), so the incident's pair
        # (one all zeros, one with none, 45 ms apart) collapses to the same
        # entry whichever write lands first.
        if old_empty == _EMPTY_ZERO and new_empty == _EMPTY_NONE:
            entries[index] = _replacement(existing, new, keep_measured=False)
            print(
                f"[METRICS_DUPLICATE] {event} recorded twice in this run; kept "
                f"the record with no numbers over the one with only zeros",
                file=sys.stderr,
            )
            return True
        if keep_enrichment():
            return True
        print(
            f"[METRICS_DUPLICATE] {event} already recorded in this run; skipped "
            f"the second record (it carried {new_empty})",
            file=sys.stderr,
        )
        return False

    if old_empty is not None:
        # An empty row that landed first must not cost the real numbers.
        entries[index] = _replacement(existing, new, keep_measured=False)
        print(
            f"[METRICS_DUPLICATE] {event} recorded twice in this run; the second "
            f"record replaced the first, which carried {old_empty}",
            file=sys.stderr,
        )
        return True

    old_payload = _payload(existing)
    new_payload = _payload(new)
    differing = sorted(
        k for k in old_payload.keys() & new_payload.keys()
        if old_payload[k] != new_payload[k]
    )
    if differing:
        print(
            f"[METRICS_CONFLICT] {event} recorded twice in this run with "
            f"different {', '.join(differing)}: kept {json.dumps(old_payload, sort_keys=True)}, "
            f"dropped {json.dumps(new_payload, sort_keys=True)}",
            file=sys.stderr,
        )
        return False
    if new_payload.keys() <= old_payload.keys():
        if keep_enrichment():
            return True
        print(
            f"[METRICS_DUPLICATE] {event} already recorded in this run; skipped "
            f"the second record (it repeats the recorded values)",
            file=sys.stderr,
        )
        return False
    entries[index] = _replacement(existing, new, keep_measured=True)
    added = sorted(new_payload.keys() - old_payload.keys())
    print(
        f"[METRICS_DUPLICATE] {event} recorded twice in this run; the second "
        f"record agrees and adds {', '.join(added)}, so it replaced the first",
        file=sys.stderr,
    )
    return True


def record_metric_in_state(
    state: dict,
    phase: str,
    label: str,
    subagent_type: Optional[str] = None,
    token_count: Optional[int] = None,
    tool_uses: Optional[int] = None,
    duration_ms: Optional[int] = None,
    total_batches: Optional[int] = None,
    batch_index: Optional[int] = None,
    ends_short: Optional[bool] = None,
    *,
    task_id: Optional[str] = None,
    failed: Optional[bool] = None,
    failure: str = "",
    half_applied: bool = False,
    dropped: Optional[str] = None,
    set_aside: Optional[str] = None,
) -> Optional[str]:
    """``record_metric``'s mutation, applied to an in-memory state dict.

    Returns the rendered ``[ETA]`` line when ``total_batches`` and
    ``batch_index`` are both given, so the caller decides *where* it goes —
    stderr for the CLI, the phase log for the scheduler — and nothing is
    printed for a caller that wants none. See ``start_phase_in_state`` for why
    the in-memory form exists. *ends_short*: the run will stop short of
    completing its phase, so the line that reaches N/N claims no completion
    (fix round 22); ``None`` reads it off the state (:func:`native_ends_short`).

    Fix round 24 (live run 10): *failed* says the task failed (*failure*:
    what failed, *half_applied*: it changed files first), so its line says
    so and its entry is marked :data:`FAILED_ENTRY_KEY`; ``None`` reads it
    off the state, where ``util batch-done`` recorded it, for *task_id* or
    the id the label starts with (:func:`native_failure`). *dropped* is why
    the total dropped since the last line, ``None`` reading it off the
    tasks a record took out (:func:`_newly_withdrawn_tail`); *set_aside* the
    tasks the N/N line names as not dispatched, ``None`` reading the native
    emit's record (:func:`set_aside_in_state`). The executor passes all four.

    **A second record of the same event collapses; nothing else does.** An
    event is ``(phase, run_id, label, batch_index)``, where ``run_id`` is the
    one ``start_phase_in_state`` stamped for this run. On the native leg the
    orchestrating agent works out each record across separate shell calls, and
    one audited run recorded ``Batch 4 (step_4)`` twice, 45 ms apart, one copy
    all zeros and the other with no numbers. The second record of an event:

    - replaces the first when the first measured nothing and it did;
    - is skipped when it measured nothing (of two empty records, the one with
      no numbers is kept over the all-zero one), or repeats the first, or is a
      subset agreeing on every field it carries;
    - replaces the first when it agrees on every shared field and adds more;
    - enriches a compatible measurement with its missing task identity or
      failure classification, clearing ambiguity once the task is named;
    - is dropped with ``[METRICS_CONFLICT]`` when a shared field differs,
      because appending would count one batch twice in the phase averages.

    An established task identity cannot change, and a recorded failure
    survives an incomplete duplicate, including one that adds measurements.

    Every one of those prints a line on stderr (``[METRICS_DUPLICATE]`` or
    ``[METRICS_CONFLICT]``): it reports a caller's mistake, the way
    ``prior_changes append`` reports a duplicate entry. A skipped or conflicting
    record returns no ``[ETA]`` line, since it recorded no progress.

    A record with no started phase has no ``run_id`` and appends unchecked, as
    before, and an entry without one (every entry recorded before run ids) is
    never matched: keying on ``(phase, label)`` alone would drop a rerun's real
    measurements, since metrics outlive runs in ``state.json``.

    **``batch_index`` is checked against this run's own progress** (only on a
    record that appends): the expected index is the highest one this run has
    recorded, plus one, and anything else prints
    ``[METRICS_INDEX_MISMATCH]``. A warning, never a rejection — a skipped
    batch is legitimate — and the high-water mark means one gap warns once.
    ``len(entries) + 1`` would warn on every record after a rerun or a resume
    (``entries`` spans every run) and after any skipped record. A run's first
    record is not checked: a resumed scheduler run's first index legitimately
    starts past 1, because it counts the batches the resume skipped.
    """
    metrics = state.get("metrics")
    if not isinstance(metrics, dict):
        # Tolerate the `metrics: null` some older state files carry: `"metrics"
        # not in state` was True for a dict and False for a null, so a null
        # would have raised here rather than being replaced.
        metrics = {}
        state["metrics"] = metrics
    entries = metrics.get(phase)
    if not isinstance(entries, list):
        entries = []
        metrics[phase] = entries

    entry = {
        "label": label,
        "timestamp": datetime.now().isoformat(),
    }
    if subagent_type is not None:
        # D2h: the flag name and the JSON key stay put (this is a CLI surface
        # with recorded history in existing metrics.json files); what goes *in*
        # becomes the host-neutral executor role. `general-purpose` carried no
        # information — it is pure Claude Code vocabulary — so it is normalized
        # to `agent`. A resolved `provider:model` runner spec (the executor path)
        # or any other value passes through verbatim.
        entry["subagent_type"] = normalize_recorded_executor(subagent_type)
    if token_count is not None:
        entry["token_count"] = token_count
    if tool_uses is not None:
        entry["tool_uses"] = tool_uses
    if duration_ms is not None:
        entry["duration_ms"] = duration_ms
    if batch_index is not None:
        entry["batch_index"] = batch_index
    if task_id:
        entry["task_id"] = str(task_id)
    no_task_id: List[str] = []
    if failed is None:
        named = task_id or label_task_id(label)
        statuses = state.get("task_status")
        if not task_id and named and not re.fullmatch(r"T\d+", named) and not (
                isinstance(statuses, dict) and named in statuses):
            # ``Retry: …`` starts with a word, not a task of this state.
            named = None
        if not named:
            # Fix round 25 (review of round 24, stops #2): a record naming
            # no task is the one failed task of this run still unrecorded;
            # among two or more it is never guessed.
            candidates = unrecorded_failures(state, phase, entries)
            if len(candidates) == 1:
                named = candidates[0]
                entry["task_id"] = named
            elif candidates:
                no_task_id = candidates
                entry[NO_TASK_ID_ENTRY_KEY] = True
        found = native_failure(state, phase, named)
        failed = found is not None
        if found is not None:
            failure, half_applied = found
    if failed:
        entry[FAILED_ENTRY_KEY] = True

    run_id = _current_run_id(state, phase)
    if run_id is not None:
        entry["run_id"] = run_id
        event = _describe_event(phase, label, batch_index)
        this_run = [
            (i, e) for i, e in enumerate(entries)
            if isinstance(e, dict) and e.get("run_id") == run_id
        ]
        for i, recorded in this_run:
            if recorded.get("label") == label and recorded.get("batch_index") == batch_index:
                if not _collapse_duplicate(entries, i, entry, event):
                    return None
                # An identity-only correction keeps the original numbers.
                # Render the record that survived, including a failure that
                # an incomplete duplicate must not turn into a success.
                entry = entries[i]
                duration_ms = entry.get("duration_ms")
                no_task_id = no_task_id if entry.get(NO_TASK_ID_ENTRY_KEY) else []
                failed = bool(entry.get(FAILED_ENTRY_KEY))
                found = native_failure(state, phase, _metric_task_id(entry))
                if failed and found is not None:
                    failure, half_applied = found
                break
        else:
            marks = [e["batch_index"] for _, e in this_run if _is_index(e.get("batch_index"))]
            if _is_index(batch_index) and marks:
                expected = max(marks) + 1
                if batch_index != expected:
                    print(
                        f"[METRICS_INDEX_MISMATCH] {event} was recorded as batch "
                        f"{batch_index}; this run's next index is {expected} "
                        f"(highest recorded so far: {max(marks)}). Recorded as given.",
                        file=sys.stderr,
                    )
            entries.append(entry)
    else:
        entries.append(entry)

    if no_task_id:
        print(
            f"{NO_TASK_ID_MARKER} {_describe_event(phase, clip(label, 80), batch_index)} "
            f"names no task, and {_named_ids(no_task_id)} failed in this run "
            f"with no record yet, so it is not counted as progress: pass "
            f"--task-id <id> (the task it measures) on every util metrics "
            f"record call of a task.",
            file=sys.stderr,
        )
        return None
    if total_batches is None or batch_index is None:
        return None
    progress = (state.get("metrics_progress") or {}).get(phase)
    if (
        isinstance(progress, dict) and progress.get(WITHDRAWN_KEY)
        and _is_index(progress.get("total_batches"))
    ):
        # Fix round 18: this run's total lost the tasks a record took out
        # (`withdraw_from_progress_in_state`); the host still passes the
        # count it was handed at the emit.
        total_batches = int(progress["total_batches"])
    if dropped is None:
        dropped = (
            _newly_withdrawn_tail(state, phase, progress)
            if isinstance(progress, dict) else ""
        )
    if set_aside is None:
        set_aside = set_aside_tail(set_aside_in_state(state, phase))
    result = _compute_eta(
        entries=entries,
        progress=progress,
        phase=phase,
        batch_index=batch_index,
        total_batches=total_batches,
        this_duration_ms=duration_ms,
        colorize=_should_colorize_stderr(),
        # The executor knows (*ends_short*); on the native leg the state says
        # it (fix round 22).
        ends_short=(
            native_ends_short(state, phase) if ends_short is None else ends_short
        ),
        failure=(failure if failed else None),
        half_applied=bool(failed and half_applied),
        dropped=dropped,
        set_aside=set_aside,
    )
    return result["line"]


def record_metric(
    state_path: Path,
    phase: str,
    label: str,
    subagent_type: Optional[str] = None,
    token_count: Optional[int] = None,
    tool_uses: Optional[int] = None,
    duration_ms: Optional[int] = None,
    total_batches: Optional[int] = None,
    batch_index: Optional[int] = None,
    print_eta: bool = True,
    task_id: Optional[str] = None,
) -> None:
    """Record a single metric entry into the state file.

    Appends to the ``metrics.{phase}`` array in the state JSON, except that a
    second record of an event this run already recorded collapses into the
    first (see ``record_metric_in_state``). Auto-generates a timestamp for the
    entry.

    When both ``total_batches`` and ``batch_index`` are provided and
    ``print_eta`` is True, prints an ``[ETA]`` line to stderr after writing
    the metric.

    Args:
        state_path: Path to the state JSON file (must exist).
        phase: Workflow phase name (e.g. "implement", "apply-suggestions").
        label: Human-readable label for this metric entry.
        subagent_type: Optional executor value ("agent", "human", or the
            resolved provider:model runner spec). The flag and JSON key keep
            their historical name; see normalize_recorded_executor.
        token_count: Optional token count consumed.
        tool_uses: Optional number of tool invocations.
        duration_ms: Optional wall-clock duration in milliseconds.
        total_batches: Optional total batch count (for ETA).
        batch_index: Optional 1-based batch index (for ETA).
        print_eta: When False, suppresses ETA stderr output.
        task_id: Optional id of the task or batch the entry measures (an
            apply batch's label carries none): the line of one ``util
            batch-done`` recorded failed says so (fix round 24).
    """
    with state_file_lock(state_path):
        state = _read_state(state_path)
        eta_line = record_metric_in_state(
            state,
            phase,
            label,
            subagent_type=subagent_type,
            token_count=token_count,
            tool_uses=tool_uses,
            duration_ms=duration_ms,
            total_batches=total_batches,
            batch_index=batch_index,
            task_id=task_id,
        )
        _write_state(state_path, state)

    if print_eta and eta_line:
        print(eta_line, file=sys.stderr)


def generate_phase_report(state_path: Path, phase: str) -> str:
    """Generate a markdown table report for a single phase.

    Returns an empty string if no metrics exist for the phase.

    Args:
        state_path: Path to the state JSON file (must exist).
        phase: Phase name to report on.

    Returns:
        Markdown string with a resource-usage table, or "".
    """
    state = _read_state(state_path)
    entries = state.get("metrics", {}).get(phase, [])
    if not entries:
        return ""

    lines = [
        "## Resource Usage",
        "",
        "| Task | Executor | Tokens | Tool Uses | Duration |",
        "|------|----------|--------|-----------|----------|",
    ]

    total_tokens: Optional[int] = None
    total_tool_uses: Optional[int] = None
    total_duration_ms: Optional[int] = None

    for entry in entries:
        label = _escape_pipe(entry.get("label", ""))
        sa_type = entry.get("subagent_type", "-")
        tokens = entry.get("token_count")
        tools = entry.get("tool_uses")
        dur = entry.get("duration_ms")

        lines.append(
            f"| {label} | {sa_type} | {format_number(tokens)} "
            f"| {format_number(tools)} | {format_duration(dur)} |"
        )

        if tokens is not None:
            total_tokens = (total_tokens or 0) + tokens
        if tools is not None:
            total_tool_uses = (total_tool_uses or 0) + tools
        if dur is not None:
            total_duration_ms = (total_duration_ms or 0) + dur

    # Bold total row
    t_tok = f"**{format_number(total_tokens)}**"
    t_tool = f"**{format_number(total_tool_uses)}**"
    t_dur = f"**{format_duration(total_duration_ms)}**"
    lines.append(f"| **Total** | | {t_tok} | {t_tool} | {t_dur} |")

    lines.append("")
    lines.append("*Duration is cumulative subagent time.*")

    return "\n".join(lines)


def generate_all_phases_report(state_path: Path) -> str:
    """Generate an aggregated markdown report across all phases.

    Phases are sorted alphabetically. Returns an empty string if no
    metrics exist in the state file.

    Args:
        state_path: Path to the state JSON file (must exist).

    Returns:
        Markdown string with a cross-phase summary table, or "".
    """
    state = _read_state(state_path)
    all_metrics = state.get("metrics", {})
    if not all_metrics:
        return ""

    # Filter out phases with empty entry lists
    phases = sorted(p for p, entries in all_metrics.items() if entries)
    if not phases:
        return ""

    lines = [
        "### Resource Usage",
        "",
        "| Phase | Subagent Calls | Tokens | Tool Uses | Duration |",
        "|-------|---------------|--------|-----------|----------|",
    ]

    grand_calls = 0
    grand_tokens: Optional[int] = None
    grand_tool_uses: Optional[int] = None
    grand_duration_ms: Optional[int] = None

    for phase in phases:
        entries = all_metrics[phase]
        count = len(entries)
        grand_calls += count

        phase_tokens: Optional[int] = None
        phase_tools: Optional[int] = None
        phase_dur: Optional[int] = None

        for entry in entries:
            t = entry.get("token_count")
            u = entry.get("tool_uses")
            d = entry.get("duration_ms")
            if t is not None:
                phase_tokens = (phase_tokens or 0) + t
            if u is not None:
                phase_tools = (phase_tools or 0) + u
            if d is not None:
                phase_dur = (phase_dur or 0) + d

        lines.append(
            f"| {_escape_pipe(phase)} | {count} "
            f"| {format_number(phase_tokens)} | {format_number(phase_tools)} "
            f"| {format_duration(phase_dur)} |"
        )

        if phase_tokens is not None:
            grand_tokens = (grand_tokens or 0) + phase_tokens
        if phase_tools is not None:
            grand_tool_uses = (grand_tool_uses or 0) + phase_tools
        if phase_dur is not None:
            grand_duration_ms = (grand_duration_ms or 0) + phase_dur

    t_calls = f"**{grand_calls}**"
    t_tok = f"**{format_number(grand_tokens)}**"
    t_tool = f"**{format_number(grand_tool_uses)}**"
    t_dur = f"**{format_duration(grand_duration_ms)}**"
    lines.append(f"| **Total** | {t_calls} | {t_tok} | {t_tool} | {t_dur} |")

    lines.append("")
    lines.append("*Aggregated from per-phase metrics. Duration is cumulative subagent time.*")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m utils.metrics",
        description="Record and report task resource-usage metrics.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # -- record --
    rec = subparsers.add_parser("record", help="Record a metric entry")
    rec.add_argument("--state-file", required=True, help="Path to state JSON file")
    rec.add_argument("--phase", required=True, help="Workflow phase name")
    rec.add_argument("--label", required=True, help="Human-readable label")
    rec.add_argument("--subagent-type", default=None, help="Subagent type")
    rec.add_argument("--tokens", type=int, default=None, help="Token count")
    rec.add_argument("--tool-uses", type=int, default=None, help="Tool invocation count")
    rec.add_argument("--duration-ms", type=int, default=None, help="Duration in ms")
    rec.add_argument("--total-batches", type=int, default=None,
                     help="Total batch count for ETA (use with --batch-index)")
    rec.add_argument("--batch-index", type=int, default=None,
                     help="1-based index of this batch (use with --total-batches)")
    rec.add_argument("--task-id", default=None,
                     help="The task or batch this entry measures (as given to "
                          "util batch-done), so a failed one's line says so")
    rec.add_argument("--no-eta", action="store_true",
                     help="Suppress ETA stderr line even when --total-batches/--batch-index are set")

    # -- start --
    start = subparsers.add_parser("start", help="Mark phase start for ETA tracking")
    start.add_argument("--state-file", required=True, help="Path to state JSON file")
    start.add_argument("--phase", required=True, help="Workflow phase name")
    start.add_argument("--total-batches", type=int, required=True, help="Total batches in this phase")

    # -- finish --
    finish = subparsers.add_parser("finish", help="Mark phase finish, clear progress")
    finish.add_argument("--state-file", required=True, help="Path to state JSON file")
    finish.add_argument("--phase", required=True, help="Workflow phase name")

    # -- report --
    rep = subparsers.add_parser("report", help="Generate a metrics report")
    rep.add_argument("--state-file", required=True, help="Path to state JSON file")
    group = rep.add_mutually_exclusive_group(required=True)
    group.add_argument("--phase", default=None, help="Report for a single phase")
    group.add_argument(
        "--all-phases", action="store_true", default=False,
        help="Report aggregated across all phases",
    )

    return parser


def main(argv=None) -> int:
    bootstrap_streams()
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_usage(sys.stderr)
        sys.exit(1)

    state_file = Path(args.state_file)

    if not state_file.exists():
        print(f"Error: state file not found: {state_file}", file=sys.stderr)
        sys.exit(1)

    try:
        return _run_command(args, state_file)
    except StateLockTimeout as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def _run_command(args, state_file: Path) -> int:
    """One subcommand of :func:`main` (``record``/``start``/``finish``/``report``)."""
    if args.command == "record":
        record_metric(
            state_path=state_file,
            phase=args.phase,
            label=args.label,
            subagent_type=args.subagent_type,
            token_count=args.tokens,
            tool_uses=args.tool_uses,
            duration_ms=args.duration_ms,
            total_batches=args.total_batches,
            batch_index=args.batch_index,
            print_eta=not args.no_eta,
            task_id=args.task_id,
        )

    elif args.command == "start":
        start_phase(
            state_path=state_file,
            phase=args.phase,
            total_batches=args.total_batches,
        )

    elif args.command == "finish":
        finish_phase(state_path=state_file, phase=args.phase)

    elif args.command == "report":
        if args.all_phases:
            output = generate_all_phases_report(state_file)
        else:
            output = generate_phase_report(state_file, args.phase)
        if output:
            print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
