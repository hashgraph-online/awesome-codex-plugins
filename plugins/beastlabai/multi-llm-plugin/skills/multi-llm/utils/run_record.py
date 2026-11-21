"""The run record's writers: the active run handle, the progress and
resolution writes that go through it, and the checkpoint's stamp reader.

A detached worker owns its phase dir through one :class:`utils.detach.RunHandle`,
installed here as :data:`_ACTIVE` while the run lasts (``RunHandle.start`` and
``finish``). The writers below decide by that handle which door a write goes
through, so a module below the execution layer (``result_files``,
``unattended``) records progress and resolutions without importing
``detach``. ``detach`` re-exports every name here for reading; the handle
itself is read here, ``run_record._ACTIVE``, and a test patches it here
(docs/development/dispatcher.md#import-layers).
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from . import status_file
from .clock import parse_local

if TYPE_CHECKING:  # pragma: no cover - annotations only
    from .detach import RunHandle


# ---------------------------------------------------------------------------
# The checkpoint's stamps
# ---------------------------------------------------------------------------

def _elapsed_since(stamp: Any, now: Optional[float] = None) -> Optional[float]:
    """Seconds since an ISO timestamp, or ``None`` when it is absent/unreadable.

    The one ISO reader for the whole checkpoint (``heartbeat_at``,
    ``started_at``, ``dispatched_at``, and every ``progress.models`` row), so its
    failure modes are ``status``'s failure modes.

    **A timezone-aware stamp is one of them** (F4, 2026-09-20). Every writer here
    is ``status_file.now_iso`` → ``datetime.now().isoformat()``, which is naive,
    but a hand-edited or foreign file is exactly what ``read_status``'s contract
    says must not make ``status`` crash — and
    ``datetime.fromisoformat("2026-09-19T10:14:03Z")`` parses to an *aware*
    datetime on 3.11+ (that ``Z`` form is the schema example in the plan, and
    what the JS tests emit), after which ``datetime.now() - when`` raises
    ``TypeError``, not the ``ValueError`` this only used to catch. One aware
    ``started_at`` anywhere in the map therefore took down the whole command.
    Normalised rather than refused, because a stamp we *can* read is worth an
    honest elapsed: an aware stamp is converted to this machine's local wall
    clock, the same clock the naive stamps are already on.
    """
    when = _parse_stamp(stamp)
    if when is None:
        return None
    try:
        reference = datetime.now() if now is None else datetime.fromtimestamp(now)
        return max((reference - when).total_seconds(), 0.0)
    except (ValueError, TypeError, OverflowError, OSError):
        return None


def _parse_stamp(stamp: Any) -> Optional[Any]:
    """An ISO stamp as a naive local ``datetime.datetime``, or ``None`` if unreadable.

    The parsing half of :func:`_elapsed_since`, split out (2026-09-21) for the
    one stamp the checkpoint carries that lies in the *future*:
    ``progress.models[*].stagger_until``, which
    ``progress_tracker.entry_stagger_remaining_s`` reads as a countdown rather
    than an age. ``_elapsed_since`` clamps at zero, so a future stamp through it
    reads ``0`` — honest for an age, useless for a countdown — and a second
    ``fromisoformat`` call site would be a second place to forget the aware-stamp
    normalisation F4 was about. Same failure modes, same answer: anything that
    does not parse is ``None``, never a raise.
    """
    if not stamp:
        return None
    try:
        return parse_local(str(stamp))
    except (ValueError, TypeError, OverflowError, OSError):
        return None


# ---------------------------------------------------------------------------
# The active run
# ---------------------------------------------------------------------------

#: The run this process owns as a detached worker: its ``RunHandle``,
#: installed by ``RunHandle.start`` and removed by ``RunHandle.finish``.
_ACTIVE: Optional["RunHandle"] = None


def report_progress(phase_dir: str, **updates: Any) -> None:
    """Merge *updates* into this phase's reserved ``progress`` object — on every
    run, foreground or detached.

    The invariant narrowed when the foreground path landed: "a foreground run's
    ``.status.json`` gains no new keys" became **"a foreground ``.status.json``
    gains a ``progress`` object and still no ``run`` object"**. That is the whole
    of the change a reader has to hold. ``progress`` is display-only — nothing
    resumes, reaggregates or branches on it — while ``run`` is the *process*
    machine, and only a detached worker's ``claim_run`` ever writes it. So "with
    ``--detach`` unset, behavior is unchanged" still holds everywhere a reader
    actually decides something, and a foreground run stops being a phase dir that
    reports nothing for the length of a fan-out.

    The handle decides **which door** the write goes through, never *whether* it
    happens. Three cases, and the last one is the non-obvious half:

    * **No handle** (``_ACTIVE is None``) — the foreground, and also a Claude Code
      native-background run, which is a foreground run inside a background Bash.
      Write straight through :func:`status_file.update_progress`. That is the
      entire foreground path, and it deliberately lands under the *same* reserved
      object in the *same* shape a detached run writes, so one renderer serves
      both and no second file is invented for the foreground.
    * **The handle owns this phase dir** — through ``handle.progress``, so a
      detached worker keeps one door onto its own checkpoint and anything that
      later has to travel with a run (the heartbeat stamp, the run_id
      compare-and-set) has a single place to attach.
    * **A handle owned by a *different* phase dir** — written **directly, into
      the dir the caller named** (F3, 2026-09-20). This branch used to drop the
      write silently, and the stated reason — "one run's ticker would scribble
      into another run's map" — conflated two directories that are never the
      same one: a tracker writes to the dir it was *built for* and has no way to
      address the handle's, so no scribbling was ever possible. What the drop
      really cost was ``full --detach``, which claims ``{plan}/full/`` and then
      calls each phase's ``main()`` in process while every phase tracker targets
      ``{plan}/<phase>/``: **every** progress write of the longest-running mode
      the tool has was discarded, silently, so the log filled with ``[PROGRESS]``
      lines while ``status --phase review-plan`` showed no map, no counters and
      no step at all. What the handle legitimately guards is its own record —
      the heartbeat stamp and the ``run_id`` compare-and-set — which is why a
      foreign dir goes through ``update_progress`` rather than ``handle.progress``
      and why ``record_output_files``/``record_resolution`` keep the guard
      wholesale: those really are the detached hand-back.

    All three branches end in ``status_file.update_status`` under
    ``checkpoint_lock`` — the critical section that already serializes the 10 s
    heartbeat thread against the orchestrator's main-thread phase transitions — so
    the new foreground writer adds no race. ``progress`` merges key by key at its
    top level, so a write here never erases a sibling another site wrote
    (``step``, ``sandbox_bypassed``, ``sandbox_fallback``, the ``subagents`` /
    ``write_subagents`` executor mirrors). The merge is one level *deep* only: a nested value such as
    the per-model ``models`` map is a single key, and a write carrying it replaces
    the stored map wholesale rather than deep-merging into it.
    """
    handle = _ACTIVE
    # No handle, or a handle that owns some *other* dir: the same direct write,
    # into the dir the caller named. The only thing the handle adds is its own
    # record's heartbeat stamp, and that belongs to its own dir alone.
    if handle is None or os.path.abspath(handle.phase_dir) != os.path.abspath(
        str(phase_dir)
    ):
        status_file.update_progress(str(phase_dir), updates)
        return
    handle.progress(**updates)


def record_resolution(phase_dir: str, site: str, decision: str) -> None:
    """Record one auto-resolved decision point, for a detached run only."""
    handle = _ACTIVE
    if handle is None or os.path.abspath(handle.phase_dir) != os.path.abspath(str(phase_dir)):
        return
    handle.resolution(site, decision)
