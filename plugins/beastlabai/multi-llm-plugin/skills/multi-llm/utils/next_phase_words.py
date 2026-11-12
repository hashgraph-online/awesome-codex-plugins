"""The command a write phase's stop prints: one mode, this host's spelling.

:func:`phase_command` spells ``--<mode> <plan> [flags…]`` from the host's
``next_command`` template, and on a commit review the commit mode with its
pinned range instead (:func:`commit_view_for`, :func:`commit_spelled_args`,
through ``utils/commit_spelling``). The apply and implement orchestrators
build their stop answers with it; ``next_phase`` builds its own commands with
the same functions and re-exports every name
(docs/development/dispatcher.md#import-layers).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Sequence, Union

from .advisory import note_swallowed
from .routes import ARGS_SLOT, _host_capabilities, _skill_module, quote_plan_arg

if TYPE_CHECKING:  # pragma: no cover - annotations only
    from .commit_spelling import CommitView


def brief_view(
    plan_arg: Union[str, Path], plan_path: Optional[Union[str, Path]] = None,
) -> Optional["CommitView"]:
    """``commit_spelling.commit_view`` of the plan's ``state.json`` (*plan_path*,
    else *plan_arg* made absolute), the brief spelled as *plan_arg*; ``None``
    for a plan's run, a direct ``--head-ref`` run, or a state it cannot read."""
    # Imported here to keep next_phase, which loads this module, light.
    from .commit_spelling import commit_view

    try:
        source = plan_arg if plan_path is None else plan_path
        return commit_view(os.path.abspath(str(source)), plan=str(plan_arg))
    except Exception as exc:  # noqa: BLE001 - advisory: the plan spelling stands
        note_swallowed("next phase: commit brief view", exc)
        return None


def spelled_view(mode_word: str, view: Optional["CommitView"]) -> Optional["CommitView"]:
    """*view* when ``--<mode_word>`` is printed in the commit spelling, else ``None``.

    Only a mode that takes a range reads the pinned spelling: the hook maps
    ``review-code`` and ``apply-code-fixes`` to the front doors, and
    ``improve-commits`` is one. A command naming any other mode on a brief
    (``ask``, a fallback ``review-plan``) keeps the brief path, which that mode
    takes as its plan.
    """
    if view is None:
        return None
    # Imported here to keep next_phase, which loads this module, light.
    from .commit_spelling import spell_mode

    modes = _skill_module("modes")
    row = modes.resolve(str(mode_word))
    spelled = modes.resolve(spell_mode(row.name if row is not None else str(mode_word), view))
    if spelled is None or modes.POS_REVS not in tuple(spelled.positionals):
        return None
    return view


def commit_view_for(
    mode_word: str,
    plan_arg: Union[str, Path],
    plan_path: Optional[Union[str, Path]] = None,
) -> Optional["CommitView"]:
    """The ``CommitView`` a printed ``--<mode_word> <plan_arg> …`` is spelled
    with, or ``None`` to print it as today.

    Set only when the plan's ``state.json`` holds ``commit_range`` and the
    mode, through the hook, takes a range (:func:`spelled_view`). A plan's
    run and a direct ``review-code --head-ref`` run (``head_ref`` only) are
    never mapped: their commands stay review-code's own and the plan is still
    a plan.
    """
    return spelled_view(mode_word, brief_view(plan_arg, plan_path))


def commit_mode_word(mode_word: str, view: Optional["CommitView"]) -> str:
    """*mode_word* as a command printed for *view* names it (the hook's
    ``spell_mode``), aliases resolved first; unchanged without a view."""
    if view is None:
        return str(mode_word)
    # Imported here to keep next_phase, which loads this module, light.
    from .commit_spelling import spell_mode

    row = _skill_module("modes").resolve(str(mode_word))
    return spell_mode(row.name if row is not None else str(mode_word), view)


def commit_spelled_args(
    mode_word: str, view: "CommitView", flags: Sequence[Any] = (),
) -> str:
    """``--<commit mode> <pinned> [flags…]``, the text a route's template
    wraps: the hook's ``spell_args`` (the pinned range, or the brief path on
    a root range, and none of the flags a front door synthesises or
    consumes), each token through :func:`quote_plan_arg`."""
    # Imported here to keep next_phase, which loads this module, light.
    from .commit_spelling import spell_args

    word, rest = spell_args(commit_mode_word(mode_word, view), None, flags, view)
    return " ".join([f"--{word}", *(quote_plan_arg(str(token)) for token in rest)])


def phase_command(
    plan_arg: str, host_id: str, route: Optional[str], mode_word: str,
    *flags: str,
    plan_path: Optional[Union[str, Path]] = None,
) -> str:
    """``<host spelling> --<mode> <plan as typed> [flags…]``, from the same
    ``next_command`` template and the same quoting as :func:`resume_command`.

    What a write phase's stop message prints as the way forward (racing
    re-run 3, 2026-10-05): the resume, the review-code / apply-code-fixes pair
    that fixes what a failed check reported, and the ``--human-task`` variants
    that accept the failure. No gate: the caller has just stopped the phase
    it names. Raises ``ValueError`` for a (host, route) pair with no template.

    Every flag token goes through the plan argument's own rule,
    :func:`quote_plan_arg`: a composite's continuation carries
    ``--files``/``--files-from`` paths, which may hold a space or a quote.
    Every token the other callers pass (``--resume``, ``--human-task``,
    ``T003=done``, ``{task_id}=skip``) has neither and comes back bare.

    On a commit review (the plan's ``state.json``, read at *plan_path* else
    at *plan_arg*, holds ``commit_range``) the command is spelled as the
    commit mode with the pinned range and none of the flags a front door
    synthesises (:func:`commit_spelled_args`):
    ``[IMPROVE_RERUN]``, an apply stop's ``skip`` answer and the resume
    answers all come through here.
    """
    modes = _skill_module("modes")
    mode = modes.resolve(mode_word)
    if mode is None:
        raise ValueError(f"unknown mode {mode_word!r}")
    template = _host_capabilities().next_command_template(host_id, route)
    view = commit_view_for(mode.name, plan_arg, plan_path)
    if view is not None:
        return template.replace(ARGS_SLOT, commit_spelled_args(mode.name, view, flags))
    args = " ".join([
        f"--{mode.name}", quote_plan_arg(plan_arg),
        *(quote_plan_arg(str(flag)) for flag in flags),
    ])
    return template.replace(ARGS_SLOT, args)
