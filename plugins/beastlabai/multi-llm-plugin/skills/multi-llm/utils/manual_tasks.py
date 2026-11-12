"""The words a deferred manual task is relayed with: gates, notes, close commands.

What a stop says about the manual tasks implement deferred to the user, off
the workflow payload's ``implement`` entry (``check_workflow_prerequisites``):
which ones a gate holds (:func:`manual_gate_ids`), the resume that runs the
code waiting on them and why (:func:`manual_gate_flags`,
:func:`manual_gate_why`), the other ways on (:func:`manual_gate_decline_answers`),
and the command that records them done (:func:`close_command`,
:func:`manual_close_note`). The executor's stop (``write_stop``,
``write_reports``, ``stop_answers``) and every reader of a native run word them
alike from here (docs/development/dispatcher.md#import-layers). ``next_phase``
re-exports every name.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Optional, Sequence

from .routes import ARGS_SLOT, RESUME_FLAG, quote_plan_arg
from .text_clip import plain_line, clip


#: The longest why read back from a run's write mirror
#: (:func:`stop_resume_why_on_record`): the folder is writable by every
#: jailed batch, so anything longer, or not one plain line, is not relayed.
MAX_RECORDED_WHY_CHARS = 600


#: An implement task id, the whole string (``task_decomposer.TASK_ID_PATTERN``).
#: The manual tasks and the ids a close command answers are read back from
#: ``state.json``, which a repo-wide batch can write.
_TASK_ID = re.compile(r"T[0-9]{3}")


#: How many code task ids :func:`after_code_note` names before "and N more".
AFTER_IDS_SHOWN = 5


def after_code_note(task_ids: Sequence[str]) -> str:
    """What a manual task that comes after code not run yet says after its
    title: ``(after T001: do it once implement has run that
    task)``."""
    ids = [str(task_id) for task_id in task_ids]
    shown = ids[:AFTER_IDS_SHOWN]
    named = ", ".join(shown) + (
        f" and {len(ids) - len(shown)} more" if len(ids) > len(shown) else "")
    which = "that task" if len(ids) == 1 else "those tasks"
    return f"(after {named}: do it once implement has run {which})"


def waits_on_note(task_id: str) -> str:
    """What a task skipped with deferred manual task *task_id* is: implement
    runs it on the resume that records *task_id* done."""
    return f"(waits on {task_id}: implement runs it once {task_id} is recorded done)"


def manual_note_ids(implement: Mapping[str, Any]) -> List[str]:
    """The manual tasks the note under the deferred list records done: while
    a manual-task gate holds (``manual_gate``), only the gate's
    (:func:`manual_gate_ids`) — the resume the stop's section leads with —
    else every one the user can do now (:func:`manual_close_ids`).

    With a free manual task beside the
    gating one, summary.md's note, ``status``'s trailer and the lookup's note
    gave ``--human-task T001=done --human-task T002=done`` beside the
    section's ``--human-task T002=done``: two different record-done commands
    on one surface. The free task stays listed under the manual tasks left
    for the user; its command comes once the gate's resume has run."""
    if implement.get("manual_gate"):
        ids = manual_gate_ids(implement)
        if ids:
            return ids
    return manual_close_ids(implement)


def manual_note_named(
    implement: Mapping[str, Any], ids: Sequence[str],
) -> Optional[List[str]]:
    """*ids*, when the note's command records fewer manual tasks than the
    deferred list names (a gate beside a free manual task), so
    its lead names them rather than saying "this manual task"; else
    ``None``."""
    if not implement.get("manual_gate"):
        return None
    # A deferred entry with no `waits_on` is a manual task itself.
    manual = {
        str(entry.get("id")) for entry in implement.get("manual_tasks") or ()
        if isinstance(entry, Mapping) and entry.get("id")
        and not entry.get("waits_on")
    }
    return list(ids) if manual - set(ids) else None


def manual_waiting_count(
    implement: Mapping[str, Any], ids: Optional[Sequence[str]] = None,
) -> int:
    """How many code tasks wait on the manual tasks *ids* (every one the
    workflow payload's ``implement`` entry names, by default): the
    ``manual_waiting`` map ``check_workflow_prerequisites`` records, each code task once."""
    waiting = implement.get("manual_waiting")
    if not isinstance(waiting, Mapping):
        return 0
    wanted = None if ids is None else {str(item) for item in ids}
    codes = set()
    for manual, tasks in waiting.items():
        if wanted is not None and str(manual) not in wanted:
            continue
        if isinstance(tasks, (list, tuple)):
            codes.update(str(item) for item in tasks if _TASK_ID.fullmatch(str(item)))
    return len(codes)


#: How many manual tasks a gate's why names before "and N more".
GATE_IDS_SHOWN = 3


#: A manual task's title, cut to this many characters in a gate's why.
GATE_TITLE_CHARS = 80


def manual_gate_ids(implement: Mapping[str, Any]) -> List[str]:
    """The manual tasks code tasks wait on that the user can do now: the
    workflow payload's ``manual_close_ids`` that its ``manual_waiting`` map
    names. Recording them done is what lets implement run
    the code tasks they hold."""
    waiting = implement.get("manual_waiting")
    if not isinstance(waiting, Mapping):
        return []
    return [
        task_id for task_id in manual_close_ids(implement)
        if isinstance(waiting.get(task_id), (list, tuple)) and waiting.get(task_id)
    ]


def manual_gate_flags(implement: Mapping[str, Any]) -> List[str]:
    """``--resume --human-task <id>=done …`` for :func:`manual_gate_ids`,
    or ``[]`` when no code task waits on a manual task the user can do now
    The one resume that runs them, recording only those
    manual tasks done, never a later one that comes after code not run."""
    ids = manual_gate_ids(implement)
    if not ids:
        return []
    flags = [RESUME_FLAG]
    for task_id in ids:
        flags += ["--human-task", f"{task_id}=done"]
    return flags


def gate_resume_closes_the_manual_tasks(implement: Mapping[str, Any]) -> bool:
    """Whether the resume a stopped implement's section leads with
    (:func:`_resume_flags` under ``manual_gate``) is the very command the
    note under the deferred list gives: while a
    gate holds, the note records the gate's manual tasks done and no other
    (:func:`manual_note_ids`). A stop's notice then names the
    tasks and leaves that command to the section."""
    if not implement.get("manual_gate"):
        return False
    ids = manual_gate_ids(implement)
    return bool(ids) and ids == manual_note_ids(implement)


def _manual_gate_names(implement: Mapping[str, Any], ids: Sequence[str]) -> str:
    """``T010 (Provision the checker fixture)``, the ids joined, at most
    :data:`GATE_IDS_SHOWN`, each with its recorded title cut."""

    titles = {
        str(entry.get("id")): entry.get("title")
        for entry in implement.get("manual_tasks") or ()
        if isinstance(entry, Mapping)
    }
    named = []
    for task_id in ids[:GATE_IDS_SHOWN]:
        title = titles.get(task_id)
        named.append(
            f"{task_id} ({clip(plain_line(title), GATE_TITLE_CHARS)})"
            if title else task_id)
    rest = len(ids) - len(named)
    return ", ".join(named) + (f" and {rest} more" if rest > 0 else "")


def manual_gate_why(implement: Mapping[str, Any], *, stopped: bool = True) -> Optional[str]:
    """What the resume :func:`manual_gate_flags` spells does, one plain line, or ``None``.

    *stopped*: implement is not finished and a plain resume runs nothing
    (``manual_gate`` on the payload); else it finished with these code tasks
    left waiting."""
    ids = manual_gate_ids(implement)
    if not ids:
        return None
    count = manual_waiting_count(implement, ids)
    tasks = "the code task" if count == 1 else f"the {count} code tasks"
    that_wait = f"{tasks} that {'waits' if count == 1 else 'wait'}"
    names = _manual_gate_names(implement, ids)
    if len(ids) == 1:
        task_id = ids[0]
        held = (
            f"Implement can run no code task until manual task {names} is "
            f"recorded done, so a plain resume runs nothing."
            if stopped else
            f"Implement has not run {that_wait} on manual task {names}."
        )
        return (
            f"{held} Once you have done {task_id} by hand, this command records "
            f"it done and runs {that_wait} on it."
        )
    held = (
        f"Implement can run no code task until a manual task is recorded done "
        f"({names}), so a plain resume runs nothing."
        if stopped else
        f"Implement has not run {that_wait} on manual tasks {names}."
    )
    return (
        f"{held} Once you have done them by hand, this command records them "
        f"done and runs {that_wait} on them; leave out the --human-task "
        f"answer of any you have not done."
    )


def manual_gate_decline_answers(implement: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """The other ways on from a manual-task gate, as stop answers
    (``[{"flags", "why"}]``, ``--resume`` first), or ``[]`` (under ``--yes`` the gate
    re-stopped on every
    ``--human-task <id>=skip`` and only a false ``=done`` went on).

    For each manual task the gate's resume records done
    (:func:`manual_gate_ids`), ``--human-task <id>=skip``: the user's call
    that they will not do it, which skips it and the code tasks that wait
    on it; the combined answer first when the gate holds on more than one,
    the order ``stop_answers.compose_stop_answers`` gives a stop's
    answers. The executor records them on its stop and every reader of a
    native gate derives them from ``state.json``, so both legs word them
    alike."""
    ids = manual_gate_ids(implement)
    if not ids:
        return []

    def tasks(count: int, pronoun: str) -> str:
        if count == 1:
            return f"the code task that waits on {pronoun}"
        return f"the {count} code tasks that wait on {pronoun}"

    answers: List[Dict[str, Any]] = []
    if len(ids) > 1:
        flags = [RESUME_FLAG]
        for task_id in ids:
            flags += ["--human-task", f"{task_id}=skip"]
        answers.append({
            "flags": flags,
            "why": (
                f"if you will do none of {_manual_gate_names(implement, ids)}, "
                f"skip them and {tasks(manual_waiting_count(implement, ids), 'them')}, "
                f"and implement goes on without them"),
        })
    for task_id in ids:
        answers.append({
            "flags": [RESUME_FLAG, "--human-task", f"{task_id}=skip"],
            "why": (
                f"if you will not do {_manual_gate_names(implement, [task_id])}, "
                f"skip it and {tasks(manual_waiting_count(implement, [task_id]), 'it')}, "
                f"and implement goes on without them"),
        })
    return answers


def manual_close_ids(implement: Mapping[str, Any]) -> List[str]:
    """The deferred ids a ``--human-task <id>=done`` closes, off the workflow
    payload's ``implement`` entry: ``manual_close_ids`` (the manual tasks
    themselves, ``StateManager.manual_tasks_to_close``) when present, else
    every ``manual_tasks`` id (a payload built)."""
    recorded = implement.get("manual_close_ids")
    if isinstance(recorded, list):
        return [str(task_id) for task_id in recorded
                if task_id and _TASK_ID.fullmatch(str(task_id))]
    return [
        str(entry.get("id")) for entry in implement.get("manual_tasks") or ()
        if isinstance(entry, Mapping) and entry.get("id")
        and _TASK_ID.fullmatch(str(entry.get("id")))
    ]


def close_command(template: str, plan_arg: str, task_ids: Sequence[str]) -> str:
    """``--implement <plan> --resume --human-task <id>=done …``, host-spelled.

    How the user records deferred manual tasks done. On
    implement's resume a ``done`` answer completes a manual task under every
    strategy, and a resume that only records answers keeps implement's
    completion date, so the review after it does not go stale.
    """
    answers = " ".join(f"--human-task {task_id}=done" for task_id in task_ids)
    args = f"--implement {quote_plan_arg(plan_arg)} {RESUME_FLAG} {answers}"
    return template.replace(ARGS_SLOT, args)


def manual_close_lead(
    count: Optional[int] = None, *, waiting: int = 0,
    named: Optional[Sequence[str]] = None,
) -> str:
    """The sentence that leads into the command closing deferred manual
    tasks (:func:`close_command`), ending with a colon: what
    ``user_next_step.manual_tasks_note`` and ``[MANUAL_TASK_NOTE]`` say, the
    command beside it on its own.

    *count* is how many tasks the command records done. For one task the plural sentence
    ("these manual
    tasks … keeping a --human-task answer only for each task you did") read
    wrong, and the host rewrote it, dropping the clause; one task gets the
    singular sentence, which has nothing to keep or drop.

    *waiting* is how many code tasks wait on them: implement has not run those, and the
    command that records the manual task done runs them, so the sentence
    says that instead.

    *named*: the ids the command records, when the list
    above it names other manual tasks too (a manual-task gate beside a free
    one): the sentence names them instead of saying "this manual task".
    """
    if waiting:
        tasks = (
            "the code task that waits" if waiting == 1
            else f"the {waiting} code tasks that wait"
        )
        if count == 1:
            which = f"manual task {named[0]}" if named else "this manual task"
            return (
                f"Implement has not run {tasks} on {which}. Once you "
                f"have done it by hand, this command records it done and runs "
                f"{'it' if waiting == 1 else 'them'}:"
            )
        which = (
            f"manual tasks {', '.join(named)}" if named else "these manual tasks")
        return (
            f"Implement has not run {tasks} on {which}. Once you "
            "have done one by hand, this command records it done and runs what "
            "no longer waits; keep a --human-task answer only for each task you "
            "did:"
        )
    if count == 1:
        return (
            "No later phase waits for this manual task. Once you have done it "
            "by hand, record it done with this command:"
        )
    return (
        "No later phase waits for these manual tasks. Once you have done one "
        "by hand, record it done with this command, keeping a --human-task "
        "answer only for each task you did:"
    )


def manual_close_note(
    command: str, count: Optional[int] = None, *, waiting: int = 0,
    named: Optional[Sequence[str]] = None,
) -> str:
    """The one plain line that says how to close deferred manual tasks, for a
    surface that is one line of text (a summary, ``status``'s trailer).

    The command ends the line, with nothing after it. *count* and *waiting* as in
    :func:`manual_close_lead`.
    """
    return f"{manual_close_lead(count, waiting=waiting, named=named)} {command}"
