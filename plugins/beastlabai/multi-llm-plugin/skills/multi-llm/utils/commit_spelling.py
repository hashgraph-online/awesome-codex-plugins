"""The commit spelling hook: print a commit review's commands as the commit modes.

The two phase front doors re-record their run as the phase they front
(``review-commits`` as ``review-code``, ``apply-commit-fixes`` as
``apply-code-fixes``), so detach, ``status``, run records and the next-step
table all see one phase vocabulary (plans/review-commits.md §2.1, "What step 7
records"). Left alone, every command those readers print would then read
``apply-code-fixes <brief> --base-ref <sha> --head-ref <sha>``: a fronted mode
word plus three flags the front doors refuse with ``[COMMIT_FLAG_CONFLICT]``.

This module is the one place that turns such a command back into the commit
spelling (§2.8, "Spelling of commands"): when the anchor's ``state.json`` holds
``commit_range``, the mode word is mapped back through ``modes.Mode.
commit_view_of``, the plan argument becomes the pinned ``<base12>..<head12>``
(the brief path for a range that starts at the root commit), and the flags the
front door synthesised or consumes are dropped. A plan's run, and a direct
``review-code --head-ref`` run (``head_ref`` only), are never mapped: the plan
is still called a plan and the commands stay review-code's own.

It also owns the second, row-keyed mapping (§2.8, "A second mapping site"):
on a composite whose positional is a range (``improve-commits``) the step words
``review-code`` / ``apply-code-fixes`` read as the commit modes in lines a user
reads, with no anchor state to key on.

Pure apart from reading one ``state.json`` (read-only, no lock, no git call).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Mapping, Optional, Sequence, Tuple, Union

#: Flags a front door synthesises or consumes; a printed commit command never
#: carries one (the front doors refuse the first three, and the rest are
#: either hidden plumbing or inherited from ``commit_range``).
DROPPED_FLAGS: Tuple[str, ...] = (
    "--plan-file", "--base-ref", "--head-ref", "--commit-stage", "--revs",
    "--focus", "--context-plan",
)


@dataclass(frozen=True)
class CommitView:
    """What a rendered command needs to know about a commit review."""

    brief: str
    base: Optional[str]
    head: str

    @property
    def pinned(self) -> str:
        """The range as typed back: ``<base12>..<head12>``, or the brief path
        for a range that starts at the root commit (§2.2, "What is typed back")."""
        if self.base:
            return f"{self.base[:12]}..{self.head[:12]}"
        return self.brief


def _state_path_for(plan: Union[str, Path]) -> Path:
    from .output_handler import output_dir_path

    return output_dir_path(Path(plan)) / "state.json"


def _read_state(plan: Union[str, Path]) -> Optional[Mapping[str, Any]]:
    try:
        with open(_state_path_for(plan), encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, Mapping) else None


def commit_view(
    anchor: Union[None, str, Path, Mapping[str, Any]],
    *,
    plan: Union[None, str, Path] = None,
) -> Optional[CommitView]:
    """The commit review behind *anchor*, or ``None`` for anything else.

    *anchor* is a plan/brief path (its ``state.json`` is read) or an already
    loaded state mapping. With a mapping, *plan* names the brief as the caller
    spells it; else the record's own ``brief`` (repo-relative) is used.
    """
    if anchor is None:
        return None
    if isinstance(anchor, Mapping):
        state: Optional[Mapping[str, Any]] = anchor
    else:
        state = _read_state(anchor)
        plan = anchor if plan is None else plan
    if not state:
        return None
    record = state.get("commit_range")
    if not isinstance(record, Mapping):
        return None
    head = record.get("head")
    if not isinstance(head, str) or not head:
        return None
    base = record.get("base")
    brief = str(plan) if plan is not None else str(record.get("brief") or "")
    return CommitView(brief=brief, base=base if isinstance(base, str) and base else None,
                      head=head)


def spell_mode(mode: str, view: Optional[CommitView]) -> str:
    """``review-code`` → ``review-commits`` and ``apply-code-fixes`` →
    ``apply-commit-fixes`` for a commit review; every other word unchanged."""
    if view is None:
        return mode
    import modes as mode_table

    for row in mode_table.MODES:
        if row.commit_view_of == mode:
            return row.name
    return mode


def strip_fronted_flags(args: Sequence[Union[str, Path]]) -> List[str]:
    """*args* without :data:`DROPPED_FLAGS` (and their values, ``--x=v`` too)."""
    kept: List[str] = []
    index = 0
    items = [str(arg) for arg in args]
    while index < len(items):
        token = items[index]
        name = token.split("=", 1)[0]
        if name in DROPPED_FLAGS:
            index += 1 if "=" in token else 2
            continue
        kept.append(token)
        index += 1
    return kept


def spell_args(
    mode: str,
    plan: Union[None, str, Path],
    args: Sequence[Union[str, Path]],
    view: Optional[CommitView],
) -> Tuple[str, List[str]]:
    """``(mode, [plan, *args])`` in the commit spelling when *view* is set.

    Without a view the mode, plan and flags come back unchanged (the plan
    first, when given), so a caller can route every command through here.
    """
    if view is None:
        head = [str(plan)] if plan is not None else []
        return mode, head + [str(arg) for arg in args]
    return spell_mode(mode, view), [view.pinned] + strip_fronted_flags(args)


def spell_command(
    mode: str,
    plan: Union[None, str, Path],
    *args: Union[str, Path],
    view: Optional[CommitView] = None,
    base: Optional[Path] = None,
) -> str:
    """``dispatcher_command`` in the commit spelling (unchanged without a view)."""
    from .cli_common import dispatcher_command

    word, rest = spell_args(mode, plan, args, view)
    return dispatcher_command(word, *rest, base=base)


def step_word(row_name: str, word: str) -> str:
    """The row-keyed mapping: a composite step word as the user reads it.

    On a composite row whose positional is a range (``improve-commits``), each
    sequence word is spelled through the front-door row whose
    ``commit_view_of`` names it. improve-plan and improve-code keep their words.
    """
    import modes as mode_table

    row = mode_table.resolve(row_name)
    if row is None or not row.is_composite:
        return word
    if tuple(row.positionals) != (mode_table.POS_REVS,):
        return word
    for other in mode_table.MODES:
        if other.commit_view_of == word:
            return other.name
    return word


def spell_retry_command(
    mode: str,
    plan_path: Union[str, Path],
    *args: Union[str, Path],
    typed_plan: Union[None, str, Path] = None,
    flags: Optional[Sequence[str]] = None,
    base: Optional[Path] = None,
) -> str:
    """``cli_common.retry_command`` in the commit spelling on a commit review.

    *plan_path* locates the run's ``state.json``; *typed_plan* is the plan as
    the command should spell it when no mapping applies (defaults to
    *plan_path*). On a commit review whose *mode* maps to a commit mode
    (``review-code`` → ``review-commits``), the command names the pinned range
    and carries none of the flags a front door synthesises or consumes, in
    *args* or in the replayed *flags*: ``review-commits <pinned> --reaggregate``
    goes back through the front door, which forwards the verb and restarts
    nothing. A plan's run and a direct ``--head-ref`` run keep the command byte
    for byte (review D, finding 3; plans/review-commits.md §5 "Follow-up
    commands").
    """
    from .cli_common import retry_command

    view = commit_view(plan_path)
    word = spell_mode(mode, view)
    if view is None or word == mode:
        shown = typed_plan if typed_plan is not None else plan_path
        return retry_command(mode, shown, *args, flags=flags, base=base)
    return retry_command(
        word, view.pinned, *strip_fronted_flags(args),
        flags=strip_fronted_flags(flags) if flags is not None else None,
        base=base,
    )
