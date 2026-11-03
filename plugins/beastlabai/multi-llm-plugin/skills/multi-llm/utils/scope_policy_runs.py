"""The ``--scope-policy`` choice of a run that is not one review round.

``utils/scope_policy.py`` records the policy of each *review round*
(``state.json`` → ``scope_policy`` → ``review-plan|review-tasks|code-review``),
and the review and apply phases resolve from that record. Six modes own no
round of their own and still have to keep a user's explicit choice across a
later run that omits the flag (plans/scope-policy-and-report-tags.md §4,
"Resolve a composite once", "The same override must survive subsequent
omission"):

* the three improve composites and ``full``, which drive rounds (and, for
  ``full``, generate-tasks and implement) and forward one value to every step;
* ``generate-tasks`` and ``implement``, whose prompts are rendered again on a
  re-run or a ``--resume`` that never repeats the flag.

Each records an explicit choice here, keyed by its **mode word**::

    state.json → "scope_policy_runs" → {
        "<mode>": {"policy": "preserve", "source": "explicit",
                   "recorded_at": "<iso>", ["closed_at": "<iso>"]}
    }

A record is **live** while the run it belongs to is unfinished: it has no
``closed_at`` and the phase that run ends on (:func:`ending_phases`: a composite's
last phase, a leaf's own) has no completion or skip recorded after it. A live
record answers a later run of the same mode with the flag omitted (source
``continuation``); a finished run's record answers nothing, so the next run of
the mode is a new run with the ``expand`` default. A forced new run
(``--force``) never inherits, and starting it without a choice closes the
previous run's record so a later continuation cannot restore that old policy.

**Only a user's choice is ever forwarded.** :func:`resolve_run_choice`
returns ``None`` when the flag was neither typed nor recorded by a live run;
a composite then forwards no ``--scope-policy`` at all and each step resolves
from its own review round's record (a new round's default ``expand``, a
resumed round's recorded policy, an apply's inherited review policy). A
single default forwarded to every phase would override exactly that per-round
inheritance. So a child that receives ``--scope-policy`` can treat it as an
explicit user choice: it always is one, typed on the composite or recorded
from that typing.

It also owns the two leaf modes' prompt blocks (:func:`generation_guidance`,
:func:`implementation_guidance`): rendered per call, empty under ``expand``
so a default prompt is byte for byte what it was, and under ``preserve`` an
instruction not to invent outcomes beyond the accepted plan or task list
(plan §4; the write phases' own block is ``scope_policy.writer_guidance``).

Pure dict helpers, prompt text and one announcement helper; no
``StateManager`` (callers pass ``StateManager.state`` or a raw ``state.json``
document and save themselves), no argparse, no model calls. Imports stay
light.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

try:  # normal import (utils is a package)
    from . import scope_policy as sp
except ImportError:  # pragma: no cover - direct script runs with utils/ on path
    import scope_policy as sp  # type: ignore

#: The ``state.json`` top-level key holding the run records.
RUNS_KEY = "scope_policy_runs"

#: The D6 site (``utils/unattended.ROWS`` row 16) every resolution is recorded under.
SITE_ID = "scope-policy"

#: ``(policy, source)`` of a user's choice.
Choice = Tuple[str, str]


def _now() -> str:
    # Full precision: a completion stamp in the same second as the record must
    # still compare on the right side of it.
    return datetime.now().isoformat()


def _parse(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def ending_phases(mode: str) -> Tuple[str, ...]:
    """The phase(s) whose newer completion finishes *mode*'s run.

    A composite's last phase (``full``: apply-code-fixes; ``improve-plan``:
    apply-suggestions), a leaf mode's own phase (``implement``). Read off the
    mode table, so a new composite needs no edit here.
    """
    try:
        import modes as mode_table  # type: ignore
    except ImportError:  # pragma: no cover - only when utils/ is sys.path[0]
        from .cli_common import modes_table

        mode_table = modes_table()
    row = mode_table.resolve(mode)
    if row is None:
        return ()
    if row.is_composite:
        last = row.last_phase
        return (last,) if last else ()
    return (row.phase,) if row.phase else ()


def run_record(state: Any, key: str) -> Optional[Dict[str, Any]]:
    """The raw record of *key* (a mode word), or ``None``."""
    table = state.get(RUNS_KEY) if isinstance(state, Mapping) else None
    if not isinstance(table, Mapping):
        return None
    record = table.get(key)
    return dict(record) if isinstance(record, Mapping) else None


def record_run_choice(
    state: Dict[str, Any], key: str, policy: str, source: str = sp.SOURCE_EXPLICIT,
) -> Dict[str, Any]:
    """Record *key*'s choice (in place; the caller saves). Replaces any older one."""
    table = state.get(RUNS_KEY)
    if not isinstance(table, dict):
        table = {}
        state[RUNS_KEY] = table
    record = {"policy": sp.effective(policy), "source": source, "recorded_at": _now()}
    table[key] = record
    return record


def close_run_choice(state: Dict[str, Any], key: str) -> bool:
    """Mark *key*'s record finished (in place). ``True`` when something changed."""
    table = state.get(RUNS_KEY)
    if not isinstance(table, dict):
        return False
    record = table.get(key)
    if not isinstance(record, dict) or record.get("closed_at"):
        return False
    record["closed_at"] = _now()
    return True


def record_run_start(state: Dict[str, Any], key: str, choice: Optional[Choice]) -> bool:
    """Persist this run's choice; return whether the caller must save state.

    A typed choice replaces the previous one. No choice closes the older
    record: resolution may have ignored it because this is a forced new run,
    and it must stay ignored when that run resumes. A continuation keeps its
    original timestamp. Call only past the write boundary, outside dry runs.
    """
    if choice is None:
        return close_run_choice(state, key)
    policy, source = choice
    if source == sp.SOURCE_EXPLICIT:
        record_run_choice(state, key, policy, source)
        return True
    return False


def _finished_after(state: Mapping[str, Any], phase: str, since: datetime) -> bool:
    """Whether *phase* has a completion or skip recorded after *since*.

    A stamp that does not parse is not evidence either way and keeps the
    record live (the rule ``state_manager`` applies to missing dates).
    """
    completed = state.get("phases_completed")
    if isinstance(completed, Mapping):
        done = _parse(completed.get(phase))
        if done is not None and done > since:
            return True
    skipped = state.get("phases_skipped")
    if isinstance(skipped, Mapping):
        entry = skipped.get(phase)
        passed = _parse(entry.get("skipped_at")) if isinstance(entry, Mapping) else None
        if passed is not None and passed > since:
            return True
    return False


def live_run_choice(
    state: Any, key: str, *, ends_with: Optional[Sequence[str]] = None,
) -> Optional[str]:
    """The policy *key*'s live record holds, else ``None`` (see the module doc).

    *ends_with* defaults to :func:`ending_phases` of *key*.
    """
    record = run_record(state, key)
    if record is None or record.get("closed_at"):
        return None
    policy = sp.normalize_policy(record.get("policy"))
    if policy is None:
        return None
    since = _parse(record.get("recorded_at"))
    if since is None:
        return None
    phases = ending_phases(key) if ends_with is None else tuple(ends_with)
    if any(_finished_after(state, phase, since) for phase in phases):
        return None
    return policy


def resolve_run_choice(
    explicit: Any,
    state: Any,
    key: str,
    *,
    new_run: bool = False,
    ends_with: Optional[Sequence[str]] = None,
) -> Optional[Choice]:
    """The user's choice for this run of *key*: typed, else a live record's.

    ``(policy, "explicit")`` for a typed value; ``(policy, "continuation")``
    for a live record (never on a *new_run*, e.g. ``--force``); ``None`` when
    there is no choice, which a composite forwards as no flag at all and a
    leaf mode reads as :data:`scope_policy.DEFAULT_POLICY` (:func:`effective_choice`).
    """
    typed = sp.normalize_policy(explicit)
    if typed is not None:
        return typed, sp.SOURCE_EXPLICIT
    if not new_run:
        recorded = live_run_choice(state, key, ends_with=ends_with)
        if recorded is not None:
            return recorded, sp.SOURCE_CONTINUATION
    return None


def effective_choice(choice: Optional[Choice]) -> Choice:
    """*choice*, or ``(expand, "default")`` when there is none."""
    return choice if choice is not None else (sp.DEFAULT_POLICY, sp.SOURCE_DEFAULT)


def forwarded_flags(choice: Optional[Choice]) -> List[str]:
    """The tokens a composite appends to every step's argv: one flag, or none."""
    if choice is None:
        return []
    return [sp.FLAG, choice[0]]


def resolution_text(policy: str, source: str, *, mode: str = "") -> str:
    """The ``[AUTO_RESOLVED] scope-policy: …`` decision for a non-typed policy."""
    policy = sp.effective(policy)
    if source == sp.SOURCE_CONTINUATION:
        where = f"this {mode} run's" if mode else "this run's"
        return f"{policy} (kept from {where} recorded {sp.FLAG})"
    if source == sp.SOURCE_REVIEW:
        return f"{policy} (the review round's recorded policy)"
    if source == sp.SOURCE_WORKFLOW:
        return f"{policy} (forwarded by the driving workflow)"
    if source == sp.SOURCE_LEGACY:
        return f"{policy} (a record that predates {sp.FLAG})"
    return f"{policy} (no {sp.FLAG} given: the default for a new run)"


def announce(
    phase_dir: Optional[str],
    policy: str,
    source: str,
    *,
    unattended: bool,
    mode: str = "",
    quiet: bool = False,
) -> Optional[str]:
    """Record a policy nobody typed as D6 row 16's auto-resolution.

    Only under ``--yes`` (an attended run stays byte-for-byte what it was) and
    never for a typed value, which is an explicit-flag answer, not an
    auto-selection. Returns the decision text when one was recorded.
    """
    if not unattended or source == sp.SOURCE_EXPLICIT:
        return None
    try:
        from . import unattended as unattended_mod
    except ImportError:  # pragma: no cover - direct script runs
        import unattended as unattended_mod  # type: ignore
    decision = resolution_text(policy, source, mode=mode)
    unattended_mod.record_resolution(phase_dir, SITE_ID, decision, quiet=quiet)
    return decision


# ---------------------------------------------------------------------------
# generate-tasks and implement: the preserve-only prompt blocks
# ---------------------------------------------------------------------------


def generation_guidance(policy: Any) -> str:
    """generate-tasks' block: empty under ``expand`` (the prompt is unchanged)."""
    if sp.effective(policy) != sp.POLICY_PRESERVE:
        return ""
    return """## Scope Policy: Preserve

The user asked to preserve the agreed scope. Write tasks only for what the plan
above asks for: its goals, its requirements and its stated limits or
exclusions. Do not add tasks for features, outcomes, refactors or cleanup the
plan does not ask for, even when they would be beneficial. A prerequisite an
agreed requirement needs (a change in another file, a migration, a test of the
required behaviour) is within scope. If a requirement cannot be delivered
without going beyond the plan's limits, do not add the expansion as a task: say
in `plan_preamble` which requirement is blocked and which scope decision it
needs."""


def implementation_guidance(policy: Any) -> str:
    """implement's per-task block: empty under ``expand`` (the prompt is unchanged)."""
    if sp.effective(policy) != sp.POLICY_PRESERVE:
        return ""
    return """## Scope Policy: Preserve
This run preserves the agreed scope. Implement this task as it is described,
within the accepted plan and task list. Do not add features, outcomes,
refactors or cleanup the task does not ask for, even when they would be
beneficial. If the task cannot be completed without going beyond that scope, do
not make the expansion: reply "failed" and say in your notes what blocks it and
which scope decision it needs. If you had already edited files for it, say
what you changed rather than reporting a clean stop."""


def with_guidance(prompt: str, block: str, *, before: Optional[str] = None) -> str:
    """*prompt* with *block* inserted ahead of the **last** *before* (else appended).

    The last occurrence, because a template's own closing section follows
    any embedded plan text, which may carry the same heading. An empty
    *block* returns *prompt* unchanged, byte for byte.
    """
    if not block:
        return prompt
    if before:
        index = prompt.rfind(before)
        if index >= 0:
            return prompt[:index] + block + "\n\n" + prompt[index:]
    return prompt.rstrip("\n") + "\n\n" + block + "\n"


__all__ = [
    "Choice", "RUNS_KEY", "SITE_ID", "announce", "close_run_choice",
    "effective_choice", "ending_phases", "forwarded_flags", "generation_guidance",
    "implementation_guidance", "live_run_choice", "record_run_choice", "record_run_start",
    "resolution_text", "resolve_run_choice", "run_record", "with_guidance",
]
