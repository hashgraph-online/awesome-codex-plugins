"""The next-phase command a finished phase ends with (plans/next-phase-command.md §2.1).

One function builds the string, and every emitter (``multi_llm.main``,
``run_status``'s terminal poll, ``util next-command``) only passes it through:
the ``[NEXT_COMMAND]`` block (:func:`render_next_phase_lines`) and
``MULTI_LLM_RESULT.user_next_step`` (:meth:`NextPhase.to_dict`) are two
renderings of the same :class:`NextPhase`.

The contract, briefly:

* :func:`next_phase_commands` is pure apart from reading ``state.json``, and it
  reads that only through ``check_workflow_prerequisites.get_workflow_status``
  (or the payload a caller already computed with it). It adds no status logic
  of its own: which phases are completed, skipped, pending or ``in_progress``
  is that payload's answer, never a second table's.
* It never reads the environment. The route is resolved by the caller, once,
  with :func:`resolve_route` — the only code here that reads a route signal —
  and handed in.
* It holds no prose. The spelling is the host's ``next_command`` template
  (``hosts/capabilities.yaml``, through ``host_capabilities``), the mode word
  comes from ``modes.py``, and an optional entry's ``why`` is its phase row's
  ``Mode.optional_why`` unless the workflow payload recorded a notice on that
  phase's entry.
* ``plan_arg`` is used verbatim — never resolved, rebased or relativized — and
  is quoted for the model that reads the command, never for a shell
  (:func:`quote_plan_arg`).
* On a commit review (the plan's ``state.json`` holds ``commit_range``) a
  command naming review-code, apply-code-fixes or improve-commits is spelled
  as the commit mode with the pinned range instead, through
  ``utils/commit_spelling`` (plans/review-commits.md §2.8,
  :func:`commit_view_for`). A plan's run, and a direct ``--head-ref`` run, are
  never mapped.
"""

from __future__ import annotations

import importlib
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union

from .text_clip import plain_line

if TYPE_CHECKING:  # pragma: no cover - annotations only
    from .commit_spelling import CommitView

#: The four line kinds of the block (§2.2(2)). The text after a command
#: marker and one space is the builder's ``command`` byte for byte; an
#: optional entry's ``why`` sits on its own line directly above its command.
NEXT_COMMAND_MARKER = "[NEXT_COMMAND]"
NEXT_COMMAND_OPTIONAL_WHY_MARKER = "[NEXT_COMMAND_OPTIONAL_WHY]"
NEXT_COMMAND_OPTIONAL_MARKER = "[NEXT_COMMAND_OPTIONAL]"
WORKFLOW_COMPLETE_MARKER = "[WORKFLOW_COMPLETE]"
#: One line per deferred implement task under ``[WORKFLOW_COMPLETE]``: the id,
#: then the title when ``state.json`` recorded one. Not a command marker.
MANUAL_TASK_MARKER = "[MANUAL_TASK]"
#: One line after the ``[MANUAL_TASK]`` lines: how to record them done
#: (:func:`manual_close_note`, fix round 14). Not a command marker: the line
#: is a sentence that carries the command, never the command alone.
MANUAL_TASK_NOTE_MARKER = "[MANUAL_TASK_NOTE]"
#: The line after ``[MANUAL_TASK_NOTE]``: the command that records the
#: manual tasks done, alone (fix round 22, live run 9: the note carried it at
#: its end, and the tool-route hosts folded it into prose). A command marker
#: like ``[NEXT_COMMAND]``: the Stop hook holds the report to it.
MANUAL_TASK_COMMAND_MARKER = "[MANUAL_TASK_COMMAND]"
#: One line above the block when the command it names is certain to be refused
#: (``check_workflow_prerequisites.repo_wide_sandbox_warning``). Not a command
#: marker: no consumer of the block reads it as one.
RUNNER_WARNING_MARKER = "[RUNNER_WARNING]"

#: The answers line pair ``util next-command`` prints under a resume of a
#: stopped native implement (fix round 14): the why on its own line, then one
#: resume command carrying every ``--human-task`` answer the stop waits for.
#: A command marker like the others: the text after it is the command alone.
NEXT_COMMAND_ANSWERS_WHY_MARKER = "[NEXT_COMMAND_ANSWERS_WHY]"
NEXT_COMMAND_ANSWERS_MARKER = "[NEXT_COMMAND_ANSWERS]"

#: The line ``util next-command`` prints directly above the ``--resume`` of a
#: stopped native implement (fix round 22): what that plain resume does on an
#: unchanged tree (``write_batch_scheduler.native_resume_why``), as the
#: answers' why lines say what each answer does. Not a command marker.
NEXT_COMMAND_WHY_MARKER = "[NEXT_COMMAND_WHY]"

#: The longest why read back from a run's write mirror
#: (:func:`stop_resume_why_on_record`): the folder is writable by every
#: jailed batch, so anything longer, or not one plain line, is not relayed.
MAX_RECORDED_WHY_CHARS = 600

#: One ``--human-task`` value a stop's recorded answer may carry: the shapes
#: the executor composes — an implement task's ``done``/``skip``/``retry``
#: (``write_batch_scheduler.compose_stop_answers``) and an apply batch's
#: ``skip`` of a partial application (``WriteBatchScheduler._stop_answers``).
#: Matched whole (fix round 23).
_RECORDED_ANSWER = re.compile(
    r"T[0-9]{3}=(?:done|skip|retry)|apply-(?:task-|fix-)?batch-[0-9]+=skip")

#: The one line :func:`emit_resume` prints: the command that resumes a stopped
#: write phase, and nothing else on the line (same rule as ``[NEXT_COMMAND]``).
RESUME_COMMAND_MARKER = "[RESUME_COMMAND]"

#: The line ``util next-command`` prints above a stopped native implement's
#: commands when nothing ran the repository's tests
#: (``write_batch_scheduler.native_stop_unverified_line``, fix round 18): the
#: executor stop's own line, for the report. Not a command marker: the text
#: after it is a sentence that names a setting, never a command to copy.
TESTS_NOT_RUN_MARKER = "[TESTS_NOT_RUN]"

#: The lines ``util next-command`` prints around its answer's ``markdown``
#: (fix round 24, live run 10: Claude Code racing 06 put the manual tasks
#: before the next-step fence, and its stops captioned the resume three ways):
#: the report's closing section already written, below the marker lines, for
#: the report to copy as it is. Every line between the two is the section's;
#: the Stop hook reads no marker line there (``report_check.find_blocks``).
NEXT_STEP_MARKDOWN_MARKER = "[NEXT_STEP_MARKDOWN]"
NEXT_STEP_MARKDOWN_END_MARKER = "[NEXT_STEP_MARKDOWN_END]"

#: The block's markers whose lines say what ``user_next_step`` carries itself
#: (its ``complete``, ``command``, ``why``, ``optional_before``, ``answers``
#: and ``manual_tasks`` keys, all in its ``markdown``). A tool server drops
#: these lines from the ``output`` of a result that carries the key (fix
#: round 27, the Fable review of round 26: the model was handed the manual
#: note and the optional whys in both), shipped as the surface's
#: ``dispatcher.next_step_markers``. ``[RUNNER_WARNING]`` and
#: ``[TESTS_NOT_RUN]`` are not among them: the key does not carry them. A
#: shell and the Claude Code leg read every line (its Stop hook does).
CARRIED_BLOCK_MARKERS: Tuple[str, ...] = (
    WORKFLOW_COMPLETE_MARKER,
    NEXT_COMMAND_WHY_MARKER,
    NEXT_COMMAND_MARKER,
    NEXT_COMMAND_OPTIONAL_WHY_MARKER,
    NEXT_COMMAND_OPTIONAL_MARKER,
    NEXT_COMMAND_ANSWERS_WHY_MARKER,
    NEXT_COMMAND_ANSWERS_MARKER,
    MANUAL_TASK_MARKER,
    MANUAL_TASK_NOTE_MARKER,
    MANUAL_TASK_COMMAND_MARKER,
)

#: The one slot every ``next_command`` template ends with (schema pattern
#: ``^[^{}]+\{args\}$``). Filled with ``str.replace``, never ``str.format``.
ARGS_SLOT = "{args}"

#: Appended when the phase a command names is recorded ``in_progress``: a bare
#: re-invocation of a write phase starts it over (§2.1, "``--resume`` is built
#: from state"). Never copied from the finished invocation's argv.
RESUME_FLAG = "--resume"

#: The route key of a plain-skill install, told apart from the plugin by the
#: dispatcher's own skill root rather than by any environment variable.
SKILL_ROUTE = "skill"

#: An implement task id, the whole string (``task_decomposer.TASK_ID_PATTERN``).
#: The manual tasks and the ids a close command answers are read back from
#: ``state.json``, which a repo-wide batch can write (fix round 23).
_TASK_ID = re.compile(r"T[0-9]{3}")

#: Whitespace-free path components in ``install_paths`` that stand for a
#: variable prefix (``$HOME``, ``%USERPROFILE%``, ``~``); the tail after the
#: last one is what a skill root is compared against.
_PLACEHOLDER_PREFIXES = ("$", "%", "~")


# ---------------------------------------------------------------------------
# The answer
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class OptionalStep:
    """One ``optional_before`` entry: an optional phase that may run first."""

    phase: str
    command: str
    why: str

    def to_dict(self) -> Dict[str, Any]:
        return {"phase": self.phase, "command": self.command, "why": self.why}


@dataclass(frozen=True)
class ManualTask:
    """One implement task the run deferred to the user (``state.json``: ``skipped``).

    ``waits_on`` (fix round 17) is set on a task skipped because it depends
    on a deferred manual task: a task implement runs itself once that one is
    recorded done, which the old wording ("no phase will run") denied.
    """

    id: str
    title: Optional[str] = None
    waits_on: Optional[str] = None
    #: A manual task that comes after code tasks implement has not run yet
    #: (fix round 28, live run 12, Codex racing 06: T008 and T009 depend on
    #: code the manual T010 held back): those code tasks, by id. Such a task is not in
    #: the command that records manual tasks done until they have run.
    after: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"id": self.id, "title": self.title}
        if self.waits_on:
            payload["waits_on"] = self.waits_on
        if self.after:
            payload["after"] = list(self.after)
        return payload

    def line(self) -> str:
        """``<id> <title>``, or the id alone when no title was recorded; a
        task that waits on another says so after it, and a manual task that
        comes after code not run yet says that."""
        text = f"{self.id} {self.title}" if self.title else self.id
        if self.waits_on:
            text += f" {waits_on_note(self.waits_on)}"
        elif self.after:
            text += f" {after_code_note(self.after)}"
        return text


#: How many code task ids :func:`after_code_note` names before "and N more".
AFTER_IDS_SHOWN = 5


def after_code_note(task_ids: Sequence[str]) -> str:
    """What a manual task that comes after code not run yet says after its
    title (fix round 28): ``(after T001: do it once implement has run that
    task)``."""
    ids = [str(task_id) for task_id in task_ids]
    shown = ids[:AFTER_IDS_SHOWN]
    named = ", ".join(shown) + (
        f" and {len(ids) - len(shown)} more" if len(ids) > len(shown) else "")
    which = "that task" if len(ids) == 1 else "those tasks"
    return f"(after {named}: do it once implement has run {which})"


def waits_on_note(task_id: str) -> str:
    """What a task skipped with deferred manual task *task_id* is: implement
    runs it on the resume that records *task_id* done (fix round 17)."""
    return f"(waits on {task_id}: implement runs it once {task_id} is recorded done)"


@dataclass(frozen=True)
class AnswersStep:
    """One resume of a stopped implement carrying one or more of the
    ``--human-task`` answers it waits for (:func:`implement_answers`)."""

    command: str
    why: str
    #: ``("T002=done", "T005=skip")``, in the command's order.
    answers: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {"command": self.command, "why": self.why, "answers": list(self.answers)}


@dataclass(frozen=True)
class NextPhase:
    """The builder's answer: a command to run next, or ``complete``.

    ``optional_before`` lists pending optional phases that precede the primary
    *in workflow order*; every rendering still prints the primary first.
    """

    phase: Optional[str]
    command: Optional[str]
    optional_before: Tuple[OptionalStep, ...] = ()
    complete: bool = False
    #: The workflow payload's early warning on *phase*'s entry (a refusal the
    #: command is certain to hit), rendered above the block and never part of
    #: ``user_next_step``.
    warning: Optional[str] = None
    #: The implement tasks the run deferred: the manual tasks the user still
    #: owes, and the tasks skipped with one, which implement runs once it is
    #: recorded done (``waits_on``, fix round 17; 2026-10-04, OpenCode: `[WORKFLOW_COMPLETE]`
    #: beside two deferred manual playthroughs said nothing about them). On a
    #: ``complete`` answer since then, and on a command answer too since fix
    #: round 16 (Codex racing 06r/07: the host named T009 as manual from the
    #: notice but never the command that records it done; only the complete
    #: answer of 08 carried it). Every block renders them: under
    #: ``[WORKFLOW_COMPLETE]``, and after a command block's commands
    #: (:func:`render_next_phase_lines`).
    manual_tasks: Tuple[ManualTask, ...] = ()
    #: On a ``--resume`` of a stopped implement, from ``util next-command``
    #: only: each answer the stop offers, the one combined command first
    #: (:func:`implement_answers`; fix round 20: each alone too, as the tool
    #: routes list them). Rendered after the primary and the optional
    #: entries, a why line above each command, and carried as the list
    #: ``user_next_step.answers``.
    answers: Tuple[AnswersStep, ...] = ()
    #: Beside ``manual_tasks``: how the user records them done
    #: (:func:`manual_close_lead`, a sentence leading into
    #: ``manual_tasks_command``; fix round 14, the command apart since fix
    #: round 22).
    manual_tasks_note: Optional[str] = None
    #: The command that records the manual tasks done, in the host's spelling
    #: (:func:`close_command`; fix round 22).
    manual_tasks_command: Optional[str] = None
    #: On a stopped native implement's ``--resume``, from ``util
    #: next-command`` only: the line saying nothing ran the repository's tests
    #: (fix round 18), printed as ``[TESTS_NOT_RUN]`` above the commands and
    #: never part of ``user_next_step`` (the tool routes carry it in the
    #: stop's ``error``).
    tests_note: Optional[str] = None
    #: On a stopped native implement's ``--resume``, from ``util
    #: next-command`` only: what that plain resume does on an unchanged tree
    #: (fix round 22, live run 9: the hosts gave it a why of their own, "re-runs
    #: the T002 check", false while the files are unchanged). Printed as
    #: ``[NEXT_COMMAND_WHY]`` above the command and carried as
    #: ``user_next_step.why``.
    why: Optional[str] = None
    #: On a resume of a stopped phase (fix round 24): the line the section
    #: opens with (:func:`resume_lead`), in ``markdown`` only.
    lead: Optional[str] = None
    #: Another way on instead of the primary, each with its why above its
    #: command, rendered after the primary and its optional entries (fix
    #: round 28, live run 12, Codex racing 06: implement left code tasks
    #: waiting on a manual task, and review-code of what ran so far is the
    #: other way on beside the resume that runs them). Carried as
    #: ``user_next_step.instead``; the block prints each as an optional pair.
    instead: Tuple[OptionalStep, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        """The ``user_next_step`` value (§2.1's outcome table).

        Complete is ``{"phase": null, "command": null, "complete": true}``,
        plus ``manual_tasks`` (``[{id, title}]``) when the run deferred any —
        additive, so a reader that knows only the three keys reads the same
        completion; otherwise ``optional_before`` is present only when non-empty.
        Every answer ends with ``markdown``, the step as the report's closing
        section (:func:`render_next_step_markdown`, fix round 22), also additive.
        """
        if self.complete:
            payload = {"phase": None, "command": None, "complete": True}
            if self.manual_tasks:
                payload["manual_tasks"] = [task.to_dict() for task in self.manual_tasks]
                self._close_keys(payload)
            payload["markdown"] = render_next_step_markdown(self)
            return payload
        payload: Dict[str, Any] = {"phase": self.phase, "command": self.command}
        if self.why:
            payload["why"] = self.why
        if self.optional_before:
            payload["optional_before"] = [step.to_dict() for step in self.optional_before]
        if self.instead:
            payload["instead"] = [step.to_dict() for step in self.instead]
        if self.answers:
            payload["answers"] = [step.to_dict() for step in self.answers]
        if self.manual_tasks:
            # Fix round 16: the tool routes relay this key, and `util
            # next-command` prints it as [MANUAL_TASK_NOTE].
            payload["manual_tasks"] = [task.to_dict() for task in self.manual_tasks]
            self._close_keys(payload)
        payload["complete"] = False
        payload["markdown"] = render_next_step_markdown(self)
        return payload

    def _close_keys(self, payload: Dict[str, Any]) -> None:
        """The note and its command, both or neither."""
        if self.manual_tasks_note and self.manual_tasks_command:
            payload["manual_tasks_note"] = self.manual_tasks_note
            payload["manual_tasks_command"] = self.manual_tasks_command


def _complete(
    phases: Mapping[str, Mapping[str, Any]],
    *,
    template: Optional[str] = None,
    plan_arg: Optional[str] = None,
) -> NextPhase:
    """The ``complete`` answer, naming the implement tasks the run deferred.

    Read off the workflow payload's ``implement`` entry
    (``check_workflow_prerequisites.get_workflow_status``), which reads them
    from ``state.json``: no status logic of this module's own. With the
    host's *template* and the *plan_arg*, the answer also says how to record
    them done (:func:`manual_close_note`).
    """
    manual, note, command = _manual_tasks(phases, template=template, plan_arg=plan_arg)
    return NextPhase(
        phase=None, command=None, complete=True, manual_tasks=manual,
        manual_tasks_note=note, manual_tasks_command=command,
    )


def _manual_tasks(
    phases: Mapping[str, Mapping[str, Any]],
    *,
    template: Optional[str] = None,
    plan_arg: Optional[str] = None,
) -> Tuple[Tuple["ManualTask", ...], Optional[str], Optional[str]]:
    """The implement tasks the run deferred, the note saying how to close
    them and the command that does (both ``None`` without a template and
    plan, or with nothing to answer).

    The command answers :func:`manual_close_ids` only (fix round 16).
    """
    implement = phases.get("implement") or {}
    entries = implement.get("manual_tasks") or ()

    def task_id(value: Any) -> Optional[str]:
        return str(value) if value and _TASK_ID.fullmatch(str(value)) else None

    def after_ids(value: Any) -> Tuple[str, ...]:
        if not isinstance(value, (list, tuple)):
            return ()
        return tuple(str(item) for item in value if task_id(item))

    manual = tuple(
        ManualTask(
            str(entry.get("id")), entry.get("title") or None,
            task_id(entry.get("waits_on")), after_ids(entry.get("after")),
        )
        for entry in entries
        if isinstance(entry, Mapping) and task_id(entry.get("id"))
    )
    note = command = None
    ids = manual_note_ids(implement)
    if manual and ids and template is not None and plan_arg is not None:
        note = manual_close_lead(
            len(ids), waiting=manual_waiting_count(implement, ids),
            named=manual_note_named(implement, ids))
        command = close_command(template, plan_arg, ids)
    return manual, note, command


def manual_note_ids(implement: Mapping[str, Any]) -> List[str]:
    """The manual tasks the note under the deferred list records done: while
    a manual-task gate holds (``manual_gate``), only the gate's
    (:func:`manual_gate_ids`) — the resume the stop's section leads with —
    else every one the user can do now (:func:`manual_close_ids`).

    Fix round 29 (review of round 28 #2): with a free manual task beside the
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
    deferred list names (a gate beside a free manual task, fix round 29), so
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
    ``manual_waiting`` map ``check_workflow_prerequisites`` records (fix
    round 28), each code task once."""
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
    names (fix round 28). Recording them done is what lets implement run
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
    (fix round 28): the one resume that runs them, recording only those
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
    note under the deferred list gives (the merge of fix round 28): while a
    gate holds, the note records the gate's manual tasks done and no other
    (:func:`manual_note_ids`, fix round 29). A stop's notice then names the
    tasks and leaves that command to the section."""
    if not implement.get("manual_gate"):
        return False
    ids = manual_gate_ids(implement)
    return bool(ids) and ids == manual_note_ids(implement)


def _manual_gate_names(implement: Mapping[str, Any], ids: Sequence[str]) -> str:
    """``T010 (Provision the checker fixture)``, the ids joined, at most
    :data:`GATE_IDS_SHOWN`, each with its recorded title cut."""
    from .text_clip import clip

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
    """What the resume :func:`manual_gate_flags` spells does (fix round 28,
    live run 12, Codex racing 06), one plain line, or ``None``.

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
    (``[{"flags", "why"}]``, ``--resume`` first), or ``[]`` (fix round 29,
    review of round 28 #1: under ``--yes`` the gate re-stopped on every
    ``--human-task <id>=skip`` and only a false ``=done`` went on).

    For each manual task the gate's resume records done
    (:func:`manual_gate_ids`), ``--human-task <id>=skip``: the user's call
    that they will not do it, which skips it and the code tasks that wait
    on it; the combined answer first when the gate holds on more than one,
    the order ``write_batch_scheduler.compose_stop_answers`` gives a stop's
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


def gate_resume_suggested(workflow: Mapping[str, Any]) -> List[str]:
    """The flags of implement's resume when it, not the payload's
    ``suggested_next``, is the next step, else ``[]`` (fix round 29, review
    of round 28 #4): implement completed with code tasks still waiting on a
    manual task the user can do now (:func:`manual_gate_flags`) and the
    suggestion is a phase after it. ``next_phase_commands`` then leads with
    that resume, the suggested phase kept as the other way on, as its
    ``--after implement`` walk does, and ``status``'s ``suggested next``
    line says the same."""
    phases = workflow.get("phases") or {}
    implement = phases.get("implement") or {}
    primary = workflow.get("suggested_next")
    if implement.get("status") != "completed" or not primary:
        return []
    order = list(_skill_module("modes").PREREQUISITE_PHASES)
    if ("implement" not in order or primary not in order
            or order.index(primary) <= order.index("implement")):
        return []
    return manual_gate_flags(implement)


def instead_why(phase: str) -> str:
    """The why above the way on that stays beside the resume running code
    tasks left waiting on a manual task (fix round 28)."""
    if phase == "code-review":
        return "Or review the code implement has run so far:"
    return "Or go on with the workflow on the code implement has run so far:"


def manual_close_ids(implement: Mapping[str, Any]) -> List[str]:
    """The deferred ids a ``--human-task <id>=done`` closes, off the workflow
    payload's ``implement`` entry: ``manual_close_ids`` (the manual tasks
    themselves, ``StateManager.manual_tasks_to_close``) when present, else
    every ``manual_tasks`` id (a payload built before fix round 16)."""
    recorded = implement.get("manual_close_ids")
    if isinstance(recorded, list):
        return [str(task_id) for task_id in recorded
                if task_id and _TASK_ID.fullmatch(str(task_id))]
    return [
        str(entry.get("id")) for entry in implement.get("manual_tasks") or ()
        if isinstance(entry, Mapping) and entry.get("id")
        and _TASK_ID.fullmatch(str(entry.get("id")))
    ]


def _with_manual_tasks(
    answer: NextPhase,
    phases: Mapping[str, Mapping[str, Any]],
    *,
    template: str,
    plan_arg: str,
) -> NextPhase:
    """*answer* (a command answer) carrying the deferred manual tasks and the
    note on recording them done, when the run deferred any (fix round 16)."""
    manual, note, command = _manual_tasks(phases, template=template, plan_arg=plan_arg)
    if not manual:
        return answer
    from dataclasses import replace as _replace

    return _replace(answer, manual_tasks=manual, manual_tasks_note=note,
                    manual_tasks_command=command)


def close_command(template: str, plan_arg: str, task_ids: Sequence[str]) -> str:
    """``--implement <plan> --resume --human-task <id>=done …``, host-spelled.

    How the user records deferred manual tasks done (fix round 14, Codex
    racing 06/08: T007 was deferred and nothing said how to close it). On
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
    command beside it on its own (fix round 22).

    *count* is how many tasks the command records done. Fix round 26 (live
    run 11, Codex 06): for one task the plural sentence ("these manual
    tasks … keeping a --human-task answer only for each task you did") read
    wrong, and the host rewrote it, dropping the clause; one task gets the
    singular sentence, which has nothing to keep or drop.

    *waiting* is how many code tasks wait on them (fix round 28, live run
    12, Codex racing 06: "No later phase waits for these manual tasks" beside
    nine code tasks waiting on T010): implement has not run those, and the
    command that records the manual task done runs them, so the sentence
    says that instead.

    *named* (fix round 29): the ids the command records, when the list
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

    The command ends the line, with nothing after it (live run 8, Codex
    racing 08: the advice used to follow it in parentheses, and the host
    copied that into the command's fence). *count* and *waiting* as in
    :func:`manual_close_lead`.
    """
    return f"{manual_close_lead(count, waiting=waiting, named=named)} {command}"


# ---------------------------------------------------------------------------
# Imports from the skill root (tolerating a direct script run)
# ---------------------------------------------------------------------------

def _skill_module(name: str):
    """Import a top-level skill module (``modes``, ``check_workflow_prerequisites``)."""
    try:
        return importlib.import_module(name)
    except ImportError:  # pragma: no cover - only when utils/ is sys.path[0]
        sys.path.insert(0, str(Path(os.path.abspath(__file__)).parent.parent))
        return importlib.import_module(name)


def _host_capabilities():
    # Lazy: host_capabilities imports cli_common, which an emitter living in
    # cli_common may import this module from.
    from . import host_capabilities

    return host_capabilities


# ---------------------------------------------------------------------------
# Quoting
# ---------------------------------------------------------------------------

def quote_plan_arg(plan_arg: str) -> str:
    """The plan path as it appears in the command: quoted for a model, not a shell.

    * no whitespace and no quote character → bare;
    * contains ``"`` but not ``'`` → wrapped in single quotes;
    * contains both → wrapped in double quotes as it is (no unescaped spelling
      exists, and no route is claimed to round-trip it);
    * otherwise (whitespace and/or ``'``) → wrapped in double quotes.

    Nothing inside is ever escaped (a Windows path keeps every backslash), and a
    quote character already in ``plan_arg`` is part of the value — it only
    decides which wrapping applies.
    """
    has_double = '"' in plan_arg
    has_single = "'" in plan_arg
    if has_double and not has_single:
        return f"'{plan_arg}'"
    if has_double or has_single or any(ch.isspace() for ch in plan_arg):
        return f'"{plan_arg}"'
    return plan_arg


#: What a plan spelling read back from a file may be made of: the characters
#: ``shlex.quote`` leaves bare, plus a plain space — which
#: :func:`quote_plan_arg` wraps in double quotes, inside which none of these is
#: special. No control character, quote, ``$``, backtick, ``\``, ``;``, ``&``,
#: ``|``, redirection, glob or ``~``.
_RECORDED_SPELLING = re.compile(r"[\w@%+=:,./ -]+", re.ASCII)


def recorded_plan_spelling(recorded: Any, plan: str) -> Optional[str]:
    """A typed plan spelling read back from a phase's ``.status.json``, or ``None``.

    The run's output folder is writable by every jailed batch (a standing
    user decision), so a ``plan_arg`` read from it — a continuation hand-off's
    (``multi_llm._remember_plan_spelling``) or a detached run record's — is
    untrusted, and it reaches a printed command verbatim. It is returned only
    when it

    * is a non-empty string, does not start with ``-``, and is made only of
      :data:`_RECORDED_SPELLING`'s characters, so a printed command can
      neither run a substitution nor split into two lines; and
    * resolves, from this process's cwd and with ``strict=True``, to the same
      existing file as *plan*. Non-strict ``realpath`` collapses a component
      that does not exist against a later ``..``, so
      ``plans/$(touch${IFS}pwned)/../foo.md`` "named" ``plans/foo.md``
      (hooks review of fix round 10).

    Otherwise the caller prints the plan as it received it.
    """
    if not isinstance(recorded, str) or not recorded or recorded.startswith("-"):
        return None
    if not _RECORDED_SPELLING.fullmatch(recorded):
        return None
    if not _steps_back_only_out_of_dirs(recorded):
        return None
    try:
        same = os.path.realpath(recorded, strict=True) == os.path.realpath(
            plan, strict=True
        )
    except (OSError, ValueError):
        return None
    return recorded if same else None


def _steps_back_only_out_of_dirs(spelling: str) -> bool:
    """Whether every component *spelling* steps back out of with ``..`` is an
    existing directory. POSIX ``realpath(strict=True)`` already refuses one
    that is not; Windows' collapses ``missing/..`` before it looks at the disk."""
    head = spelling
    while True:
        head, tail = os.path.split(head)
        if not tail:
            return True
        if tail == os.pardir and head and not os.path.isdir(head):
            return False


# ---------------------------------------------------------------------------
# The route
# ---------------------------------------------------------------------------

def _path_parts(path: str) -> Tuple[str, ...]:
    """Path components split on either separator, so a Windows path compares too."""
    return tuple(part for part in re.split(r"[\\/]+", path) if part and part != ".")


def _install_tail(entry: str) -> Tuple[str, ...]:
    """An ``install_paths`` entry's components after its last variable prefix."""
    parts = _path_parts(entry)
    for index in range(len(parts) - 1, -1, -1):
        if parts[index].startswith(_PLACEHOLDER_PREFIXES):
            return parts[index + 1:]
    return parts


def _is_skill_install(host_id: str, skill_root: Union[str, Path]) -> bool:
    """Whether *skill_root* ends with one of *host_id*'s ``install_paths`` entries.

    Judged by the root's own path, never its ``realpath``: a copy (or a
    symlink) under ``.claude/skills/multi-llm`` is a plain skill whatever it
    points at, and the plugin cache (or a dev checkout linked into it) is not.
    """
    root = _path_parts(str(skill_root))
    install_paths = _host_capabilities().entry(host_id).get("install_paths") or {}
    for entries in install_paths.values():
        for entry in entries or ():
            tail = _install_tail(str(entry))
            if tail and len(root) >= len(tail) and root[-len(tail):] == tail:
                return True
    return False


def resolve_route(
    host_id: str,
    *,
    environ: Optional[Mapping[str, str]] = None,
    skill_root: Optional[Union[str, Path]] = None,
    stderr=None,
    recorded: Optional[str] = None,
) -> Optional[str]:
    """The ``next_command`` route key for this process, or ``None`` for ``default``.

    The only reader of a route signal (§2.1, "Knowing the route"); every
    emitter calls it once and passes the result to :func:`next_phase_commands`.

    * A host whose ``next_command`` carries a ``skill`` key (claude-code) is
      told apart by the dispatcher's own skill root (``cli_common._SKILL_DIR``
      unless *skill_root* is given): ``skill`` when that root ends with one of
      the host's ``install_paths`` entries, else ``None`` (the plugin). The
      route variable is ignored there, and saying so costs one stderr line when
      it is set.
    * Any other host reads ``modes.ROUTE_ENV``, which the tool servers set.
      Unset is ``None``, silently. A value is honoured only when it is a member
      of ``modes.TOOL_ROUTES`` **and** a key of the host's ``next_command``
      cell; any other value (empty, a typo, ``skill``, a product name, a tool
      route this host has no cell for) is ``None`` plus one stderr line naming
      the ignored value.
    * *recorded* is the route the run whose commands are printed was started
      on (:func:`recorded_route`, fix round 24): when the environment names
      none, it is honoured under the same test, silently. Live run 10: a
      shell's ``status --host codex`` spelled a run the Codex plugin's tool
      had started in the file shim's words. The environment still wins, and
      a host that reads its route from the skill root ignores it.

    *environ* defaults to ``os.environ`` and *stderr* to ``sys.stderr``.
    """
    modes = _skill_module("modes")
    env = os.environ if environ is None else environ
    stream = sys.stderr if stderr is None else stderr
    capabilities = _host_capabilities()
    routes = capabilities.next_command_routes(host_id)
    value = env.get(modes.ROUTE_ENV)

    if SKILL_ROUTE in routes:
        if value is not None:
            print(
                f"multi-llm: ignoring {modes.ROUTE_ENV}={value!r}: host "
                f"'{host_id}' takes its next-command route from the skill root, "
                "not the environment",
                file=stream,
            )
        if skill_root is None:
            from . import cli_common

            skill_root = cli_common._SKILL_DIR
        return SKILL_ROUTE if _is_skill_install(host_id, skill_root) else None

    if value is None:
        if recorded in modes.TOOL_ROUTES and recorded in routes:
            return recorded
        return None
    if value in modes.TOOL_ROUTES and value in routes:
        return value
    honoured = [route for route in modes.TOOL_ROUTES if route in routes]
    print(
        f"multi-llm: ignoring {modes.ROUTE_ENV}={value!r} for host '{host_id}' "
        f"(honoured here: {', '.join(honoured) or 'none'}); using the "
        f"'{capabilities.DEFAULT_ROUTE_KEY}' next-command spelling",
        file=stream,
    )
    return None


def recorded_route(
    plan_path: Union[str, Path],
    host_id: str,
    mode_word: Optional[str] = None,
) -> Optional[str]:
    """The tool route a run of *plan_path* on *host_id* was started on, or
    ``None`` (fix round 24).

    The detached worker records its route as ``run.route`` in its phase's
    ``.status.json`` (``detach.RunHandle``): the tool servers set
    ``modes.ROUTE_ENV`` on every child, and a file shim sets nothing. Read
    here for a reader whose environment names no route (:func:`resolve_route`'s
    *recorded*): with *mode_word*, that phase's run when one of this host is
    on record, else the newest run of this host under the plan (by
    ``started_at``). Only a member of ``modes.TOOL_ROUTES`` is returned: the
    folder is writable by every jailed batch. Read-only; ``None`` when
    nothing is on record or it cannot be read.
    """
    from .output_handler import PHASE_DIR_NAMES, output_dir_path, phase_dir_path
    from .status_file import read_status

    modes = _skill_module("modes")

    def run_of(directory: Path) -> Optional[Dict[str, Any]]:
        run = read_status(str(directory)).get("run")
        if not isinstance(run, dict) or run.get("host") != host_id:
            return None
        return run

    def route_of(run: Mapping[str, Any]) -> Optional[str]:
        value = run.get("route")
        return value if isinstance(value, str) and value in modes.TOOL_ROUTES else None

    try:
        source = Path(os.path.abspath(str(plan_path)))
        mode = modes.resolve(mode_word) if mode_word else None
        if mode is not None and mode.phase:
            run = run_of(phase_dir_path(source, mode.phase))
            if run is not None:
                return route_of(run)
        plan_dir = output_dir_path(source)
        newest: Optional[Tuple[str, Dict[str, Any]]] = None
        for child in sorted(plan_dir.iterdir()) if plan_dir.is_dir() else []:
            if not child.is_dir() or child.name not in PHASE_DIR_NAMES:
                continue
            run = run_of(child)
            if run is None:
                continue
            started = str(run.get("started_at") or "")
            if newest is None or started > newest[0]:
                newest = (started, run)
    except Exception:  # noqa: BLE001 - advisory: the default route stands
        return None
    return route_of(newest[1]) if newest else None


# ---------------------------------------------------------------------------
# The commit spelling (plans/review-commits.md §2.8)
# ---------------------------------------------------------------------------
#
# The two phase front doors re-record as the code modes, so every command
# built here from state would read `--apply-code-fixes <brief>`. The mapping
# itself is `commit_spelling`'s; this module only decides, per printed
# command, whether it applies.

#: The why above ``--apply-commit-fixes`` after a commit review (§2.10): the
#: user works through the two reports before applying, and the composite is
#: the way to skip that step.
COMMIT_REPORTS_WHY = (
    "Read the review's two reports before applying: {md} and {html}. A finding "
    "marked skipped, valid or invalid there, or an edited description, is what "
    "the apply honours. --improve-commits would skip this reading step: it "
    "applies the validated fixes unattended."
)


def brief_view(
    plan_arg: Union[str, Path], plan_path: Optional[Union[str, Path]] = None,
) -> Optional["CommitView"]:
    """``commit_spelling.commit_view`` of the plan's ``state.json`` (*plan_path*,
    else *plan_arg* made absolute), the brief spelled as *plan_arg*; ``None``
    for a plan's run, a direct ``--head-ref`` run, or a state it cannot read."""
    from .commit_spelling import commit_view

    try:
        source = plan_arg if plan_path is None else plan_path
        return commit_view(os.path.abspath(str(source)), plan=str(plan_arg))
    except Exception:  # noqa: BLE001 - advisory: the plan spelling stands
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
    with, or ``None`` to print it as today (§2.8, "Spelling of commands").

    Set only when the plan's ``state.json`` holds ``commit_range`` and the
    mode, through the hook, takes a range (:func:`spelled_view`). A plan's
    run and a direct ``review-code --head-ref`` run (``head_ref`` only) are
    never mapped: their commands stay review-code's own and the plan is still
    a plan (§2.5, "Printed commands").
    """
    return spelled_view(mode_word, brief_view(plan_arg, plan_path))


def commit_mode_word(mode_word: str, view: Optional["CommitView"]) -> str:
    """*mode_word* as a command printed for *view* names it (the hook's
    ``spell_mode``), aliases resolved first; unchanged without a view."""
    if view is None:
        return str(mode_word)
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
    from .commit_spelling import spell_args

    word, rest = spell_args(commit_mode_word(mode_word, view), None, flags, view)
    return " ".join([f"--{word}", *(quote_plan_arg(str(token)) for token in rest)])


def fronted_mode_word(mode_word: str) -> str:
    """The phase mode a commit front door's word fronts (``apply-commit-fixes``
    → ``apply-code-fixes``, through ``Mode.commit_view_of``), else *mode_word*:
    what a lookup asked in the commit spelling reads state as."""
    row = _skill_module("modes").resolve(str(mode_word))
    if row is not None and row.commit_view_of:
        return row.commit_view_of
    return str(mode_word)


def _pinned_brief(text: str) -> Optional[str]:
    """The brief a pinned ``<base12>..<head12>`` names
    (``commit_review.brief_for_pinned``, no git call beyond the root), or
    ``None`` for other text or outside a repository."""
    try:
        from .commit_review import brief_for_pinned

        brief = brief_for_pinned(str(text))
    except Exception:  # noqa: BLE001 - not a pinned range here
        return None
    return str(brief) if brief is not None else None


def _shown_path(path: Union[str, Path]) -> str:
    """*path* relative to the cwd when it lies under it (``/``-separated),
    else absolute, as the front door names a brief."""
    text = os.path.abspath(str(path))
    try:
        shown = os.path.relpath(text)
    except ValueError:  # Windows: another drive than the cwd's
        return text
    if shown == os.pardir or shown.startswith(os.pardir + os.sep):
        return text
    return shown.replace(os.sep, "/")


def commit_reports_why(
    plan_arg: Union[str, Path], plan_path: Optional[Union[str, Path]] = None,
) -> str:
    """:data:`COMMIT_REPORTS_WHY` naming the brief's ``code-review/report.md``
    and ``report.html``, each as the front door names the brief."""
    from .output_handler import phase_dir_path

    source = Path(os.path.abspath(str(plan_arg if plan_path is None else plan_path)))
    review = phase_dir_path(source, "code-review")
    return COMMIT_REPORTS_WHY.format(
        md=_shown_path(review / "report.md"), html=_shown_path(review / "report.html"))


# ---------------------------------------------------------------------------
# The builder
# ---------------------------------------------------------------------------

def _workflow_payload(plan_path: Path, host_id: str) -> Dict[str, Any]:
    """``get_workflow_status`` for *plan_path*, as ``run_status`` computes it.

    *host_id* is the emitter's host: the early sandbox warning on the payload
    resolves the subagent runner for it (adversarial review, 2026-10-02).
    """
    from .output_handler import output_dir_path
    from .state_manager import StateManager

    prereq = _skill_module("check_workflow_prerequisites")
    return prereq.get_workflow_status(
        StateManager(plan_path, read_only=True), plan_path,
        output_dir_path(plan_path),
        host_id=host_id,
    )


def next_phase_commands(
    plan_arg: str,
    host_id: str,
    route: Optional[str],
    finished_mode: Optional[str],
    *,
    after_mode: Optional[str] = None,
    plan_path: Optional[Union[str, Path]] = None,
    workflow: Optional[Dict[str, Any]] = None,
) -> Optional[NextPhase]:
    """The next command after *finished_mode*, ``complete``, or ``None``.

    Args:
        plan_arg: The caller's plan argument, printed verbatim (quoted by
            :func:`quote_plan_arg` only when it needs quoting).
        host_id: The host the emitting process resolved.
        route: :func:`resolve_route`'s answer; ``None`` reads the host's
            ``default`` template. A route the host has no template for raises
            ``ValueError`` (a caller bug; emitters treat it as a builder
            failure).
        finished_mode: The mode this invocation ran (a mode word; aliases
            resolve). ``None`` from ``util next-command``.
        after_mode: ``util next-command --after``: where the walk starts, with
            the gate off. Ignored when *finished_mode* is given.
        plan_path: Where ``state.json`` lives — the resolved plan path, used
            for nothing else. Defaults to ``os.path.abspath(plan_arg)``.
        workflow: A ``get_workflow_status`` payload the caller already has
            (``run_status`` computes one). When ``None`` it is computed here.

    Returns:
        ``None`` when there is no answer: *finished_mode* (or *after_mode*) is
        neither a workflow phase nor a composite, or the finished phase is not
        on record (the gate, *finished_mode* only). Otherwise a
        :class:`NextPhase`: the same phase with ``--resume`` when it is
        ``in_progress``; else the first open required phase after it
        (``complete`` when none is left), with the open optional phases in
        between as ``optional_before``. A composite that is not the whole
        workflow (``improve-plan``, ``improve-code``) answers as the phase it
        ends on, ``Mode.last_phase``, gate included (plans/improve-plan-and-
        improve-code.md §2.6). ``full``, and both modes ``None``, answer from
        ``suggested_next`` instead (the fallback).
    """
    modes = _skill_module("modes")
    prereq = _skill_module("check_workflow_prerequisites")

    word = finished_mode if finished_mode is not None else after_mode
    gated = finished_mode is not None
    start: Optional[str] = None
    if word is not None:
        mode = modes.resolve(word)
        if mode is None:
            return None
        if mode.runs_workflow:
            start = None  # `full` names no single phase: the fallback.
        elif mode.is_composite:
            # The phase it ends on, read through the row's helper so the
            # word-to-phase mapping stays in modes.py (`improve-code` ends on
            # `apply-code-fixes`, whose phase word is the same).
            start = mode.last_phase
        elif mode.is_workflow_phase and mode.phase:
            start = mode.phase
        else:
            return None  # ask, status, init, …: no phase, no answer.

    # Looked up before any state is read, so a (host, route) pair with no
    # template raises for every phase answer, complete included.
    template = _host_capabilities().next_command_template(host_id, route)

    if workflow is None:
        source = plan_arg if plan_path is None else plan_path
        workflow = _workflow_payload(Path(os.path.abspath(str(source))), host_id)
    phases: Dict[str, Dict[str, Any]] = workflow.get("phases") or {}
    order: List[str] = list(modes.PREREQUISITE_PHASES)
    done = tuple(prereq.DONE_STATUSES)

    def status_of(phase: str) -> Optional[str]:
        return (phases.get(phase) or {}).get("status")

    def is_open(phase: str) -> bool:
        return status_of(phase) not in done

    def warning_of(phase: str) -> Optional[str]:
        return (phases.get(phase) or {}).get("warning") or None

    implement_entry: Mapping[str, Any] = phases.get("implement") or {}
    # Fix round 28 (live run 12, Codex racing 06): while every code task
    # implement has left waits on a manual task not recorded done, its plain
    # resume runs nothing; the resume records the manual tasks the user can
    # do now done, and only those.
    gate_flags = (
        manual_gate_flags(implement_entry)
        if implement_entry.get("manual_gate") else []
    )
    # plans/review-commits.md §2.8: a commit review's commands read as the
    # commit modes, with the pinned range (read once; `None` for a plan).
    commit_brief = brief_view(plan_arg, plan_path)

    def command_answer(answer: NextPhase) -> NextPhase:
        # Fix round 16: a command answer names the deferred manual tasks
        # and how to record them done, as the complete answer does. The one
        # place a command answer gets them (fix round 17: `emit_answer` had a
        # second writer for `--after implement`, and the two packages that
        # wrote them disagreed on what the answer carries).
        from dataclasses import replace as _replace

        if (answer.phase == "implement" and gate_flags and not answer.why
                and status_of("implement") == "in_progress"):
            answer = _replace(answer, why=manual_gate_why(implement_entry))
        if (answer.phase == "apply-code-fixes" and not answer.why
                and status_of("apply-code-fixes") != "in_progress"
                and spelled_view("apply-code-fixes", commit_brief) is not None):
            # §2.10: after a commit review, the reports come before the
            # apply, and the composite is the way to skip reading them.
            answer = _replace(answer, why=commit_reports_why(plan_arg, plan_path))
        answer = _with_manual_tasks(answer, phases, template=template, plan_arg=plan_arg)
        if (answer.manual_tasks_command
                and answer.manual_tasks_command == answer.command):
            # Fix round 28: the command already leads the section.
            answer = _replace(answer, manual_tasks_note=None, manual_tasks_command=None)
        return answer

    def command_for(phase: str) -> str:
        mode_word = _mode_word(modes, phase)
        view = spelled_view(mode_word, commit_brief)
        if view is not None:
            # No implement on a commit brief, so `--resume` is the one flag.
            resume = [RESUME_FLAG] if status_of(phase) == "in_progress" else []
            return template.replace(ARGS_SLOT, commit_spelled_args(mode_word, view, resume))
        args = f"--{mode_word} {quote_plan_arg(plan_arg)}"
        if status_of(phase) == "in_progress":
            args += f" {RESUME_FLAG}"
            if phase == "implement" and gate_flags:
                args += " " + " ".join(gate_flags[1:])
        return template.replace(ARGS_SLOT, args)

    def optional_steps(span: List[str]) -> Tuple[OptionalStep, ...]:
        # *span* is a slice of the phase order, so each phase appears at most
        # once; a notice never adds or removes an entry, it only supplies the
        # `why` of one the walk listed.
        steps: List[OptionalStep] = []
        for phase in span:
            if phase not in prereq.OPTIONAL_PHASES or not is_open(phase):
                continue
            # Offered only once everything it needs is on record: after
            # generate-tasks, review-tasks is offered and apply-task-suggestions
            # (whose review has not run) is not.
            if any(is_open(need) for need in prereq.PHASE_PREREQUISITES.get(phase, ())):
                continue
            steps.append(OptionalStep(
                phase=phase,
                command=command_for(phase),
                why=_optional_why(modes, phase, phases.get(phase) or {}),
            ))
        return tuple(steps)

    if start is None and gate_resume_suggested(workflow):
        # Fix round 29 (review of round 28 #4): implement finished with code
        # tasks waiting on a manual task the user can do now; the answer
        # leads with its resume, as the `--after implement` walk's does.
        start = "implement"
    if start is None:
        primary = workflow.get("suggested_next")
        if primary is None:
            return _complete(phases, template=template, plan_arg=plan_arg)
        # The optional phases offered are the ones between the furthest phase
        # on record before the suggestion and the suggestion itself, as an
        # `--after` walk offers them: `suggested_next` follows the phase
        # position (fix round 14), so a review-code suggested after a
        # completed implement no longer offers the review-tasks "before
        # implementing" that the implement it follows made moot.
        reached = max(
            (index for index, phase in enumerate(order[: order.index(primary)])
             if not is_open(phase)),
            default=-1,
        )
        return command_answer(NextPhase(
            phase=primary,
            command=command_for(primary),
            optional_before=optional_steps(order[reached + 1: order.index(primary)]),
            warning=warning_of(primary),
        ))

    def is_stale(phase: str) -> bool:
        return bool((phases.get(phase) or {}).get("stale"))

    status = status_of(start)
    if status == "in_progress":
        # A resumable phase is its own answer; the span walk does not run.
        return command_answer(NextPhase(
            phase=start, command=command_for(start), warning=warning_of(start),
        ))
    if gated and status not in done:
        # The finished phase is not on record: exit 0 at a pending marker, a
        # native first call, a fresh detach invoker. Not a finished phase.
        return None

    index = order.index(start)
    # A required phase BEFORE the finished one that was STARTED and not
    # finished comes first: the workflow is not complete, and not at the next
    # phase, while it stands. `suggested_next` (the notice on the same result
    # line, `status`) names it, so a walk that began after the finished phase
    # named another phase than the notice beside it. Measured 2026-10-02 on the
    # OpenCode and Codex racing runs: implement had ended `needs-human` after a
    # write-gate refusal, and apply-code-fixes then answered `complete` while
    # the notice said `suggested next: implement`; review-code answered
    # `--apply-code-fixes` against the same notice. Started means `in_progress`,
    # a seeded task list (`tasks_total`) or a `stale` completion (it ran to
    # the end once; adversarial review, 2026-10-02: `--after apply-code-fixes`
    # under a stale code-review answered `complete`): a phase never begun that
    # sits before a standalone start stays skipped over (a standalone
    # review-code on a fresh plan still walks to apply-code-fixes, "starting
    # mid-workflow never sends the user back").
    earlier = next(
        (
            phase for phase in order[:index]
            if phase not in prereq.OPTIONAL_PHASES and is_open(phase)
            and (status_of(phase) == "in_progress"
                 or (phases.get(phase) or {}).get("tasks_total")
                 or is_stale(phase))
        ),
        None,
    )
    if earlier is not None:
        return command_answer(NextPhase(
            phase=earlier,
            command=command_for(earlier),
            optional_before=optional_steps(order[: order.index(earlier)]),
            warning=warning_of(earlier),
        ))
    if is_stale(start):
        # A stale start (completed before implement's latest completion) is
        # its own answer once nothing earlier is open — the gate is off here,
        # since under it a stale start is "not on record" and returned None
        # above (exit 0 at a pending marker must print nothing). `util
        # next-command --after review-code` on the Codex run of 2026-10-02
        # walked past the stale review to apply-code-fixes while the notice
        # beside it said `suggested next: code-review`.
        return command_answer(NextPhase(
            phase=start, command=command_for(start), warning=warning_of(start),
        ))
    primary = next(
        (
            phase for phase in order[index + 1:]
            if phase not in prereq.OPTIONAL_PHASES and is_open(phase)
        ),
        None,
    )
    if primary is None:
        # An optional phase never keeps a workflow open, and one the walk did
        # not reach is never suggested: no `optional_before` on completion.
        return _complete(phases, template=template, plan_arg=plan_arg)
    waiting_flags = manual_gate_flags(implement_entry) if start == "implement" else []
    if waiting_flags:
        # Fix round 28 (live run 12, Codex racing 06): implement finished
        # with code tasks still waiting on a manual task the user can do
        # now. The section leads with that resume, which runs them; the
        # next phase stays the other way on, over what ran so far.
        return command_answer(NextPhase(
            phase="implement",
            command=template.replace(
                ARGS_SLOT,
                f"--{_mode_word(modes, 'implement')} {quote_plan_arg(plan_arg)} "
                + " ".join(waiting_flags)),
            why=manual_gate_why(implement_entry, stopped=False),
            instead=(OptionalStep(
                phase=primary, command=command_for(primary),
                why=instead_why(primary),
            ),),
            warning=warning_of("implement"),
        ))
    return command_answer(NextPhase(
        phase=primary,
        command=command_for(primary),
        optional_before=optional_steps(order[index + 1: order.index(primary)]),
        warning=warning_of(primary),
    ))


def _mode_word(modes, phase: str) -> str:
    """The dispatcher word for workflow *phase* (``code-review`` → ``review-code``)."""
    for mode in modes.MODES:
        if mode.is_workflow_phase and mode.phase == phase:
            return mode.name
    raise ValueError(f"no workflow-phase mode owns phase '{phase}'")


def _optional_why(modes, phase: str, entry: Mapping[str, Any]) -> str:
    """The workflow payload's notice on *phase*'s entry, else its generic why."""
    notice = entry.get("notice")
    if notice:
        return str(notice)
    for mode in modes.MODES:
        if mode.is_workflow_phase and mode.phase == phase and mode.optional_why:
            return mode.optional_why
    raise ValueError(f"optional phase '{phase}' has no Mode.optional_why")


# ---------------------------------------------------------------------------
# Resuming the SAME phase after a needs-human stop
# ---------------------------------------------------------------------------

#: The phases whose way forward after a failed dispatch is the plain
#: re-invocation, not ``--resume``: ``run_status._RESUME_VERB_BY_MODE`` gives
#: them the dispatcher's bare ``--yes``, which a host spelling never carries.
#: ``generate-tasks``' ``--reaggregate`` only consumes a result already on disk,
#: so the plain re-invoke is what re-dispatches its failed task (and a test
#: holds this tuple to that table).
RERUN_RESUME_PHASES: Tuple[str, ...] = ("generate-tasks",)

#: The in-phase word ``dispatch_subagent_tasks`` writes when a batch ended
#: with a failed task (``review_orchestrator_base``): the one state whose
#: re-invocation re-dispatches the failures.
SUBAGENTS_FAILED_STATE = "subagents_failed"


def _rerun_resumes(phase_status: Mapping[str, Any]) -> bool:
    """Would a plain re-run of this phase's failed dispatch do anything new?

    Only a dispatch that failed (:data:`SUBAGENTS_FAILED_STATE`) and whose
    executor mirror (``progress.subagents``, rewritten with the run record by
    ``claim_run``) names the failures; and only when none of them is one a
    re-run repeats (``retry_ladder.RERUN_FUTILE_STATUSES``) and no runner
    refusal closed the run out. Everything else — a refusal before the
    dispatch, a prerequisite gate, a schema the CLI rejects — is fixed by
    what the phase's own message names, and a command here would only repeat it.
    """
    from .retry_ladder import RERUN_FUTILE_STATUSES

    if phase_status.get("state") != SUBAGENTS_FAILED_STATE:
        return False
    run = phase_status.get("run") if isinstance(phase_status.get("run"), dict) else {}
    if run.get("reason_code") or phase_status.get("reason_code"):
        return False
    progress = phase_status.get("progress")
    mirror = progress.get("subagents") if isinstance(progress, dict) else None
    counts = mirror.get("counts") if isinstance(mirror, dict) else None
    if not isinstance(counts, dict):
        return False
    failed = {str(status) for status, n in counts.items() if status != "ok" and n}
    return bool(failed) and not failed & RERUN_FUTILE_STATUSES


def _prerequisites_unmet(plan_path: Path, phase: str) -> bool:
    """Would the phase's own prerequisite gate refuse a re-run right now?

    The gate refuses before anything is written (D6a), so a refusal leaves an
    earlier attempt's ``.status.json`` — mirror included — exactly as it was,
    and :func:`_rerun_resumes` reads that attempt (adversarial review,
    2026-10-05: the tool routes offered the command the gate had just
    refused). Asked through the same read-only check the gate runs
    (``collect_missing`` over a read-only ``StateManager``), so it writes
    nothing; a skip already recorded satisfies it, as it does the gate.
    """
    from .output_handler import output_dir_path
    from .state_manager import StateManager

    prereq = _skill_module("check_workflow_prerequisites")
    state = StateManager(plan_path, read_only=True)
    return bool(prereq.collect_missing(state, output_dir_path(plan_path), phase))


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
    :func:`quote_plan_arg` (plan improve-plan-and-improve-code §2.4, *Every
    argument is rendered token-safe*): a composite's continuation carries
    ``--files``/``--files-from`` paths, which may hold a space or a quote.
    Every token the other callers pass (``--resume``, ``--human-task``,
    ``T003=done``, ``{task_id}=skip``) has neither and comes back bare.

    On a commit review (the plan's ``state.json``, read at *plan_path* else
    at *plan_arg*, holds ``commit_range``) the command is spelled as the
    commit mode with the pinned range and none of the flags a front door
    synthesises (:func:`commit_spelled_args`, plans/review-commits.md §2.8):
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


def resume_command(
    plan_arg: str,
    host_id: str,
    route: Optional[str],
    mode_word: str,
    *,
    plan_path: Optional[Union[str, Path]] = None,
    workflow: Optional[Dict[str, Any]] = None,
    phase_status: Optional[Mapping[str, Any]] = None,
) -> Optional[str]:
    """The host-spelled command that resumes *mode_word*'s write phase, or ``None``.

    The next-phase rule prints no command after a failure, and that stays right
    for the next PHASE. A resume of the phase that just stopped is a different
    thing: a bare re-invocation of a write phase starts it over, so the user's
    way forward is ``--<mode> <plan> --resume`` (§2.1, "``--resume`` is built
    from state"), and 2026-10-02 neither tool route could say it: Codex ended a
    blocked ``implement`` with the MCP tool's JSON arguments, OpenCode with a
    raw ``uv run`` argv, and neither is something a user types. Built from the
    same ``next_command`` template and the same quoting as
    :func:`next_phase_commands`, so the two spellings cannot drift.

    Only the four write phases answer (the ones whose own exit-3 text says
    "re-invoke with --resume"); a review's way forward is a ``--reaggregate`` or
    a ``--force`` the dispatcher already prints as ``next``. *plan_arg* is used
    verbatim, never resolved. A (host, route) pair with no template raises
    ``ValueError``, as in :func:`next_phase_commands`.

    And only a phase with progress on record answers: the one the workflow
    payload (*workflow*, else ``get_workflow_status`` read for *plan_path*,
    default ``os.path.abspath(plan_arg)``) shows ``in_progress`` — a completed
    batch, or a completed implement task, that a bare re-invocation would redo.
    Every other exit 3 is not something ``--resume`` fixes: a prerequisite
    refusal (``PREREQUISITE_UNMET``) and a stop on pending human-task
    decisions both land before anything is recorded, and the phase's own
    message names the way forward.

    One phase answers without ``--resume``: ``generate-tasks``
    (:data:`RERUN_RESUME_PHASES`), whose recovery after a failed dispatch is
    the plain re-invocation (racing re-run 2026-10-04: a ``schema_invalid``
    task generation left the tool result with no command, and the host model
    invented one). It answers from the phase dir's ``.status.json``
    (*phase_status*, else read for the plan) through :func:`_rerun_resumes`,
    so a failure no re-run can change gets none — and only while the phase's
    prerequisite gate would let the re-run through
    (:func:`_prerequisites_unmet`): a gate refusal writes no status, so the
    file still describes the attempt before it. The servers pass through whatever this
    says and attach nothing when it says nothing; before the adversarial
    review (2026-10-02) they attached ``--resume`` to every write-phase exit 3,
    and ``util next-command does-not-exist.md --blocked implement`` printed
    one for a plan that does not exist. The same rule as
    :func:`next_phase_commands`'s ``command_for``: ``in_progress`` is the one
    status that spells ``--resume``.

    A commit front door's word (``apply-commit-fixes``) answers as the phase
    it fronts, and on a commit review the command is spelled back as the
    commit mode with the pinned range (plans/review-commits.md §2.8).
    """
    modes = _skill_module("modes")
    mode = modes.resolve(fronted_mode_word(mode_word))
    if mode is None or not mode.is_workflow_phase or not mode.phase:
        return None
    from .subagent_tasks import PHASE_BY_WRITE_KIND

    template = _host_capabilities().next_command_template(host_id, route)
    view = commit_view_for(mode.name, plan_arg, plan_path)
    if mode.phase in RERUN_RESUME_PHASES:
        source = Path(os.path.abspath(str(plan_arg if plan_path is None else plan_path)))
        if phase_status is None:
            from .output_handler import phase_dir_path
            from .status_file import read_status

            phase_status = read_status(str(phase_dir_path(source, mode.phase)))
        if not _rerun_resumes(phase_status) or _prerequisites_unmet(source, mode.phase):
            return None
        return template.replace(ARGS_SLOT, f"--{mode.name} {quote_plan_arg(plan_arg)}")
    if mode.phase not in PHASE_BY_WRITE_KIND.values():
        return None
    if workflow is None:
        source = plan_arg if plan_path is None else plan_path
        workflow = _workflow_payload(Path(os.path.abspath(str(source))), host_id)
    phases: Dict[str, Dict[str, Any]] = workflow.get("phases") or {}
    if (phases.get(mode.phase) or {}).get("status") != "in_progress":
        return None
    if view is not None:
        return template.replace(ARGS_SLOT, commit_spelled_args(
            mode.name, view, _resume_flags(phases, mode.phase)))
    args = " ".join(
        [f"--{mode.name}", quote_plan_arg(plan_arg)] + _resume_flags(phases, mode.phase))
    return template.replace(ARGS_SLOT, args)


def _resume_flags(phases: Mapping[str, Mapping[str, Any]], phase: str) -> List[str]:
    """The flags after the plan in *phase*'s resume: ``--resume``, and for an
    implement whose every code task left waits on a manual task the user can
    do now, that task's ``--human-task <id>=done`` too (fix round 28, live run
    12, Codex racing 06: a plain resume of it runs nothing)."""
    if phase == "implement":
        implement = phases.get("implement") or {}
        if implement.get("manual_gate"):
            flags = manual_gate_flags(implement)
            if flags:
                return flags
    return [RESUME_FLAG]


# ---------------------------------------------------------------------------
# The block
# ---------------------------------------------------------------------------

def render_next_phase_lines(answer: NextPhase) -> List[str]:
    """The block's lines, primary first (§2.2(2), §2.1 "Primary first").

    Complete renders ``[WORKFLOW_COMPLETE]``, then one ``[MANUAL_TASK]`` line
    per task the run deferred to the user (none when it deferred nothing), the
    ``[MANUAL_TASK_NOTE]`` line and the ``[MANUAL_TASK_COMMAND]`` line. Otherwise the ``[NEXT_COMMAND]`` line
    comes first (below a ``[RUNNER_WARNING]`` and a ``[TESTS_NOT_RUN]`` line
    when the answer carries them), then each ``optional_before`` entry's
    ``[NEXT_COMMAND_OPTIONAL_WHY]`` / ``[NEXT_COMMAND_OPTIONAL]`` pair in the
    answer's order, the answers pair, and then the same manual-task lines. A
    command line holds the command and nothing else, and every other line
    holds one plain line (:func:`~utils.text_clip.plain_line`, fix round 23):
    a why, a note or a task title comes from records a batch can write, and a
    newline in one would forge a marker line of its own.
    """
    manual_lines = [
        f"{MANUAL_TASK_MARKER} {plain_line(task.line())}"
        for task in answer.manual_tasks
    ]
    if answer.manual_tasks and answer.manual_tasks_note and answer.manual_tasks_command:
        manual_lines.append(
            f"{MANUAL_TASK_NOTE_MARKER} {plain_line(answer.manual_tasks_note)}")
        manual_lines.append(
            f"{MANUAL_TASK_COMMAND_MARKER} {answer.manual_tasks_command}")
    if answer.complete:
        return [WORKFLOW_COMPLETE_MARKER] + manual_lines
    lines = []
    if answer.warning:
        lines.append(f"{RUNNER_WARNING_MARKER} {plain_line(answer.warning)}")
    if answer.tests_note:
        lines.append(f"{TESTS_NOT_RUN_MARKER} {plain_line(answer.tests_note)}")
    if answer.why:
        lines.append(f"{NEXT_COMMAND_WHY_MARKER} {plain_line(answer.why)}")
    lines.append(f"{NEXT_COMMAND_MARKER} {answer.command}")
    for step in answer.optional_before + answer.instead:
        lines.append(f"{NEXT_COMMAND_OPTIONAL_WHY_MARKER} {plain_line(step.why)}")
        lines.append(f"{NEXT_COMMAND_OPTIONAL_MARKER} {step.command}")
    for step in answer.answers:
        lines.append(f"{NEXT_COMMAND_ANSWERS_WHY_MARKER} {plain_line(step.why)}")
        lines.append(f"{NEXT_COMMAND_ANSWERS_MARKER} {step.command}")
    # After the commands, on every command answer that carries them (fix
    # round 16): the tasks implement deferred to the user, and how to record
    # them done.
    return lines + manual_lines


#: The labels :func:`render_next_step_markdown` writes.
#: Above a stopped phase's resume (fix round 24); ``{phase}`` is its mode word.
RESUME_LEAD = "To go on with {phase}:"
OPTIONAL_LEAD = "Optional, before that:"
MANUAL_TASKS_LEAD = "Manual tasks left for you:"
#: The same lead over one task (fix round 26, live run 11: Codex 06 wrote
#: "Manual task left for you:" over the one task the section listed).
MANUAL_TASK_LEAD = "Manual task left for you:"
#: Above a stopped implement's answers (status says "or answer the stop
#: with:"): what the user types instead of the resume.
ANSWERS_LEAD = "Or answer the stop with one of these:"
WORKFLOW_COMPLETE_SENTENCE = "Workflow complete."


def resume_lead(phase: str) -> str:
    """:data:`RESUME_LEAD` for *phase* (fix round 24)."""
    return RESUME_LEAD.replace("{phase}", str(phase))


#: A first character that could open a fence, a heading, a quote, a list, an
#: HTML block or a marker line when a text line of the section starts with it.
_MARKDOWN_OPENERS = frozenset("`~#>[<-*+_|=")


def markdown_text(text: Any) -> str:
    """*text* as one plain text line of the section (:func:`plain_line`),
    its first character escaped (CommonMark's backslash) when it could open
    a block of its own (fix round 24): a why or a note is read back from a
    run's records, which a jailed batch can write, and one starting with
    ``` would fence the commands after it, one starting with ``[`` would
    read as a marker line where the native lookup prints the section."""
    line = plain_line(text)
    if line and line[0] in _MARKDOWN_OPENERS:
        return "\\" + line
    return line


def fenced_command(command: str) -> str:
    """*command* alone in a fenced block whose fence is longer than any run
    of backticks inside it (CommonMark), so it always closes where it
    should."""
    longest = max((len(run) for run in re.findall(r"`+", command)), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{fence}\n{command}\n{fence}"


def render_next_step_markdown(answer: "NextPhase") -> str:
    """*answer* as the report's closing section, already written
    (``user_next_step.markdown``; fix round 22).

    Live run 9: Codex 04 printed the primary and the optional command as bare
    paragraphs, and the manual-task close command reached the user folded
    into prose on Codex and OpenCode, while each route's rule said to fence
    every command. The block puts each command alone in its own fence and
    every why and note as plain text, in the order every route used: the
    ``command`` first (above it, the resume's why when it has one), then
    "Optional, before that:" and each optional entry's ``why`` and command,
    the answers, then the manual tasks, the note and its command — or
    "Workflow complete." in the command's place. The routes copy it as it
    is; the Claude Code leg keeps reading the marker lines. Every why, note
    and task line is one plain line (fix round 23), so nothing read back
    from a run's records opens a fence or a heading of its own.
    """
    blocks: List[str] = []
    if answer.complete:
        blocks.append(WORKFLOW_COMPLETE_SENTENCE)
    else:
        if answer.lead:
            blocks.append(markdown_text(answer.lead))
        if answer.why:
            blocks.append(markdown_text(answer.why))
        blocks.append(fenced_command(str(answer.command)))
        if answer.optional_before:
            blocks.append(OPTIONAL_LEAD)
            for step in answer.optional_before:
                blocks.extend([markdown_text(step.why), fenced_command(step.command)])
        for step in answer.instead:
            blocks.extend([markdown_text(step.why), fenced_command(step.command)])
        if answer.answers:
            blocks.append(ANSWERS_LEAD)
        for step in answer.answers:
            blocks.extend([markdown_text(step.why), fenced_command(step.command)])
    if answer.manual_tasks:
        lead = MANUAL_TASK_LEAD if len(answer.manual_tasks) == 1 else MANUAL_TASKS_LEAD
        blocks.append("\n".join(
            [lead]
            + [f"- {plain_line(task.line())}" for task in answer.manual_tasks]))
        if answer.manual_tasks_note and answer.manual_tasks_command:
            blocks.extend([
                markdown_text(answer.manual_tasks_note),
                fenced_command(answer.manual_tasks_command)])
    return "\n\n".join(block for block in blocks if block)


def render_resume_markdown(
    phase: str, command: str, why: Optional[str],
    answers: Sequence[Mapping[str, Any]],
) -> str:
    """A stopped phase's ways forward as the report's closing section, by
    :func:`render_next_step_markdown`'s rules (fix round 24, live run 10:
    with ``user_next_step`` null at a stop, the hosts composed their own
    blocks, reworded the whys and listed tool calls as options): the lead
    line naming *phase*, the resume's *why* and *command*, then
    :data:`ANSWERS_LEAD` and each answer's why and command. Carried as
    ``user_resume.markdown`` (the tool routes' ``resume_markdown``)."""
    return render_next_step_markdown(NextPhase(
        phase=phase, command=command, why=why or None,
        answers=tuple(
            AnswersStep(str(entry["command"]), str(entry["why"]))
            for entry in answers
        ),
        lead=resume_lead(phase),
    ))


def implement_answers(
    plan_arg: str,
    host_id: str,
    route: Optional[str],
    *,
    plan_path: Optional[Union[str, Path]] = None,
) -> Tuple[AnswersStep, ...]:
    """Each ``--resume`` answer a stopped native implement waits for.

    Fix round 14 (stop fixture, Claude Code fix/accept 01): the native leg's
    stop printed no command, so the host wrote "re-run with --resume" as
    prose, or two separate commands the user had to merge; this answered with
    one command carrying every answer. Fix round 20 (live run 8, Claude Code
    stop 01): that one command was all, while the tool routes list each
    answer alone too (``T005=skip`` alone, ``T002=done`` alone, …), so the
    host described answers the plugin never printed and the fix path had no
    T005-only command to run. The answers now come from the executor's own
    composer (``write_batch_scheduler.native_stop_answers`` →
    ``compose_stop_answers``) over ``state.json`` as recorded: the combined
    command first when more than one task waits, then each task's answers,
    each with its why, in the tool routes' words, every command in this
    host's spelling (:func:`phase_command`). ``()`` when no task waits.
    """
    import json as _json

    source = plan_arg if plan_path is None else plan_path
    state_file = _state_file(os.path.abspath(str(source)))
    try:
        state = _json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ()
    if not isinstance(state, dict):
        return ()
    from .write_batch_scheduler import native_stop_answers

    steps: List[AnswersStep] = []
    for entry in native_stop_answers(state):
        flags = list(entry["flags"])
        steps.append(AnswersStep(
            command=phase_command(plan_arg, host_id, route, "implement", *flags),
            why=str(entry["why"]),
            answers=tuple(
                flags[index + 1] for index, flag in enumerate(flags[:-1])
                if flag == "--human-task"
            ),
        ))
    return tuple(steps)


def gate_decline_steps(
    plan_arg: str,
    host_id: str,
    route: Optional[str],
    phases: Mapping[str, Mapping[str, Any]],
) -> Tuple[AnswersStep, ...]:
    """:func:`manual_gate_decline_answers` for the workflow payload's
    implement entry while its manual-task gate holds (``manual_gate``),
    each command in this host's spelling (:func:`phase_command`); ``()``
    otherwise (fix round 29)."""
    implement = phases.get("implement") or {}
    if not implement.get("manual_gate"):
        return ()
    steps: List[AnswersStep] = []
    for entry in manual_gate_decline_answers(implement):
        flags = list(entry["flags"])
        steps.append(AnswersStep(
            command=phase_command(plan_arg, host_id, route, "implement", *flags),
            why=str(entry["why"]),
            answers=tuple(
                flags[index + 1] for index, flag in enumerate(flags[:-1])
                if flag == "--human-task"),
        ))
    return tuple(steps)


def implement_resume_why(
    plan_arg: str, *, plan_path: Optional[Union[str, Path]] = None,
) -> Optional[str]:
    """What the plain ``--resume`` of a stopped native implement does on an
    unchanged tree (``write_batch_scheduler.native_resume_why`` over
    ``state.json`` as recorded, and the implement folder for the executor's
    check stamps), or ``None`` (fix round 22)."""
    import json as _json

    from .output_handler import phase_dir_path

    source = os.path.abspath(str(plan_arg if plan_path is None else plan_path))
    try:
        state = _json.loads(_state_file(source).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(state, dict):
        return None
    from .write_batch_scheduler import native_resume_why

    return native_resume_why(
        state, phase_dir=str(phase_dir_path(Path(source), "implement")))


# ---------------------------------------------------------------------------
# The emitters' shared step (§2.2)
# ---------------------------------------------------------------------------

class LookupFailed(Exception):
    """Raised by :func:`emit_answer` under ``strict=True``, after its stderr line."""


#: How the one stderr line a failed lookup prints opens. ``util next-command``
#: exits 3 with it, and the Claude Code report quotes it (§2.3).
LOOKUP_FAILED_PREFIX = "multi-llm: next-command lookup failed"


def lookup_failure_line(exc: BaseException) -> str:
    """The one stderr line naming a failed workflow read or builder raise."""
    message = " ".join(part.strip() for part in str(exc).splitlines() if part.strip())
    detail = f"{type(exc).__name__}: {message}" if message else type(exc).__name__
    return f"{LOOKUP_FAILED_PREFIX} ({detail}); no next command printed"


def _state_file(plan_path: Union[str, Path]) -> Path:
    """Where ``StateManager`` keeps *plan_path*'s ``state.json`` (computed only)."""
    from .output_handler import output_dir_path

    return output_dir_path(Path(plan_path).resolve()) / "state.json"


def emit_answer(
    plan_arg: str,
    host_id: str,
    finished_mode: Optional[str],
    *,
    after_mode: Optional[str] = None,
    plan_path: Optional[Union[str, Path]] = None,
    workflow: Optional[Dict[str, Any]] = None,
    stream=None,
    stderr=None,
    strict: bool = False,
    with_answers: bool = False,
    recorded_route: Optional[str] = None,
    with_markdown: bool = False,
) -> Optional[NextPhase]:
    """Build the answer, print its block and set ``user_next_step``: all or nothing.

    The step every emitter shares (``multi_llm.main``, ``run_status``'s terminal
    poll, ``util next-command``), so the block and the key are one rendering of
    one answer. The route is resolved here, once, in the emitting process
    (:func:`resolve_route`); the caller supplies ``plan_arg``, ``host_id`` and
    ``finished_mode`` from its own sources (§2.1, "Where each emitter gets its
    inputs"). The block goes to *stream* (``sys.stdout`` by default; an
    invocation that asked for JSON output passes ``sys.stderr``).

    Outcomes, per §2.1's table: an answer prints the block and records the key
    (``complete`` included); ``None`` prints and records nothing. Any exception
    — the workflow read, the route, the builder — prints and records nothing
    either: one stderr line (:func:`lookup_failure_line`) names it and this
    returns ``None``, or raises :class:`LookupFailed` under *strict*. The block
    is written before the key is recorded, so a failed write leaves no key.
    *recorded_route* is the route the run being answered for was started on
    (:func:`recorded_route`), used when this process names none (fix round
    24).
    With *with_markdown* (``util next-command``, fix round 24) the block is
    followed by the answer's ``markdown`` between
    :data:`NEXT_STEP_MARKDOWN_MARKER` and :data:`NEXT_STEP_MARKDOWN_END_MARKER`,
    the section the Claude Code report copies as it is.

    With *finished_mode* given and no *workflow* handed in, a plan whose
    ``state.json`` does not exist answers ``None`` without reading anything:
    no phase can be on record there, so the gate could only refuse, and the
    workflow read would create the plan's output dir for a run that recorded
    nothing.
    """
    from . import cli_common

    err = sys.stderr if stderr is None else stderr
    try:
        if finished_mode is not None and workflow is None:
            source = plan_arg if plan_path is None else plan_path
            if not _state_file(os.path.abspath(str(source))).is_file():
                return None
        route = resolve_route(host_id, stderr=err, recorded=recorded_route)
        answer = next_phase_commands(
            plan_arg, host_id, route, finished_mode,
            after_mode=after_mode, plan_path=plan_path, workflow=workflow,
        )
        if answer is None:
            return None
        plain_resume = str(answer.command or "").endswith(f" {RESUME_FLAG}")
        # Fix round 28: the resume of an implement every code task of which
        # waits on a manual task carries that task's `=done` answer, and its
        # why is the answer's own (`next_phase_commands`).
        gated_resume = (
            not plain_resume and answer.why is not None and not answer.instead
            and f" {RESUME_FLAG} --human-task " in str(answer.command or "")
        )
        if (
            with_answers and not answer.complete and answer.phase == "implement"
            and (plain_resume or gated_resume)
        ):
            # `util next-command` only (with_answers): a stopped implement's
            # answers, beside its resume (fix round 14; each alone too since
            # fix round 20).
            from dataclasses import replace as _replace

            if plain_resume:
                answers = implement_answers(
                    plan_arg, host_id, route, plan_path=plan_path,
                )
                if answers:
                    answer = _replace(answer, answers=answers)
                # Fix round 22: and what the plain resume does.
                why = implement_resume_why(plan_arg, plan_path=plan_path)
                if why:
                    answer = _replace(answer, why=why)
            else:
                # Fix round 29 (review of round 28 #1): a manual-task gate's
                # other way on, the user's decline, as the executor's stop
                # records it for the tool routes.
                if workflow is None:
                    workflow = _workflow_payload(Path(os.path.abspath(str(
                        plan_arg if plan_path is None else plan_path))), host_id)
                declines = gate_decline_steps(
                    plan_arg, host_id, route, workflow.get("phases") or {})
                if declines:
                    answer = _replace(answer, answers=declines)
            # Fix round 24: under the line the tool routes' section opens with.
            answer = _replace(answer, lead=resume_lead(answer.phase))
            # Fix round 18 (live run 7, Claude Code stop 01): the native
            # stop's line saying nothing ran the repository's tests, which
            # the executor stop prints itself.
            from .write_batch_scheduler import native_stop_unverified_line

            tests = native_stop_unverified_line(
                os.path.abspath(str(plan_arg if plan_path is None else plan_path))
            )
            if tests:
                answer = _replace(answer, tests_note=tests)
        payload = answer.to_dict()
        out = sys.stdout if stream is None else stream
        for line in render_next_phase_lines(answer):
            print(line, file=out)
        if with_markdown:
            print(NEXT_STEP_MARKDOWN_MARKER, file=out)
            print(payload["markdown"], file=out)
            print(NEXT_STEP_MARKDOWN_END_MARKER, file=out)
        try:
            out.flush()
        except (AttributeError, ValueError):  # pragma: no cover - closed stream
            pass
    except Exception as exc:  # noqa: BLE001 - advisory: never fails the caller
        print(lookup_failure_line(exc), file=err)
        if strict:
            raise LookupFailed(str(exc)) from exc
        return None
    cli_common.record_user_next_step(payload)
    return answer


class AlreadyComplete(Exception):
    """Raised by :func:`emit_resume` for a composite whose every step is on
    record for the review on file, after it printed :attr:`line` (§2.3's
    ``[ALREADY_COMPLETE]`` line) on its stream. Not a failed lookup: ``util
    next-command --blocked`` exits 2 on it, the code the composite's own
    re-run exits with in the same state (plans/improve-plan-and-improve-code.md
    §2.6), and records no ``user_resume``."""

    def __init__(self, line: str):
        super().__init__(line)
        self.line = line


def _composite_of(mode_word: str):
    """*mode_word*'s row when it is a composite that is not the whole
    workflow (``improve-plan``, ``improve-code``), else ``None``."""
    mode = _skill_module("modes").resolve(mode_word)
    if mode is None or not mode.is_composite or mode.runs_workflow:
        return None
    return mode


def _blocked_step(mode_word: str, plan_path: Union[str, Path]) -> str:
    """The mode word ``--blocked <mode_word>`` answers for (§2.6).

    *mode_word* itself, unless it names a composite. For a composite, the first
    word of its ``sequence`` that ``improve_workflow.skip_reason`` runs, on the
    ``records`` ``read_records`` builds with no flag typed: the step a bare
    re-run would run first, so a stop inside the composite (review completed,
    apply ``in_progress``) names the apply, never the review. The planner's
    predicate, not a second one; staleness and an apply older than its review
    enter only through it. Raises :class:`AlreadyComplete` when it passes over
    every step, and ``improve_workflow.StateReadError`` for a ``state.json`` it
    cannot read (a failed lookup).
    """
    mode = _composite_of(mode_word)
    if mode is None:
        return mode_word
    from . import improve_workflow

    args = improve_workflow.parse_args(mode.name, ["--plan-file", str(plan_path)])
    records = improve_workflow.read_records(mode.name, plan_path, args)
    for word in mode.sequence:
        if improve_workflow.skip_reason(mode.name, word, args, records) is None:
            return word
    raise AlreadyComplete(improve_workflow.already_complete_line(mode.name, args, records))


def _composite_continuation(mode_word: str, plan_path: Union[str, Path]) -> List[str]:
    """The flags after the plan in a composite's own continuation (§2.6).

    ``improve_workflow.recorded_continuation`` of the ``replay_flags`` the
    composite's ``run`` record holds in its run dir (``{plan}/improve-plan/``):
    the row-14 command its ``_phase_failed`` printed, the user's selectors and
    never ``--force``, plus ``--resume``. ``--resume`` alone with no record (a
    foreground run writes none) or a record whose list is not a list. Raises
    ``improve_workflow.ContinuationError`` for flags the composite's parser
    rejects, and ``ValueError`` for a token one printed line cannot carry: the
    folder is writable by every jailed batch, and both are a failed lookup.
    """
    from . import improve_workflow
    from .output_handler import phase_dir_path
    from .status_file import read_run

    mode = _skill_module("modes").resolve(mode_word)
    source = Path(os.path.abspath(str(plan_path)))
    run = read_run(str(phase_dir_path(source, mode.phase)))
    recorded = run.get("replay_flags") if isinstance(run, dict) else None
    flags = improve_workflow.recorded_continuation(
        mode.name, recorded if isinstance(recorded, list) else None)
    if any(not token or not token.isprintable() for token in flags):
        raise ValueError(
            f"{mode.name}'s run record holds a flag one printed command cannot carry")
    return flags


def emit_resume(
    plan_arg: str,
    host_id: str,
    mode_word: str,
    *,
    plan_path: Optional[Union[str, Path]] = None,
    stream=None,
    stderr=None,
    strict: bool = False,
    recorded_route: Optional[str] = None,
) -> Optional[str]:
    """Print the ``[RESUME_COMMAND]`` line and set ``user_resume``: all or nothing.

    :func:`emit_answer`'s sibling for ``util next-command --blocked``; the
    same failure rule (one stderr line, ``None`` or :class:`LookupFailed`)
    and the same *recorded_route*.
    Nothing is printed for a mode that has no resume command, or for a plan
    whose ``state.json`` does not exist: nothing can be in progress there, and
    the workflow read would create the plan's output dir (as in
    :func:`emit_answer`).

    A composite (``improve-plan``, ``improve-code``) is resolved first, before
    the route, the command, the answers and the why are read, so all of them
    and the payload's ``phase`` read the one mode word whose command is
    printed (§2.6): the step a bare re-run would run first
    (:func:`_blocked_step`), with that phase's own resume, answers, why and
    section when it has a resume; else the composite's own continuation
    (:func:`_composite_continuation`), the composite's word, in the host's
    spelling. Every step on record prints the ``[ALREADY_COMPLETE]`` line on
    *stream* and raises :class:`AlreadyComplete`, with no ``user_resume``.
    ``user_resume.mode`` names the mode its command runs, which the tool
    routes build their option calls from.

    On a commit review (plans/review-commits.md §2.8) a front door's word
    is asked as the phase it fronts, and the command, ``mode``, ``flags``
    and section are spelled back as the commit mode with the pinned range.
    """
    from . import cli_common

    err = sys.stderr if stderr is None else stderr
    out = sys.stdout if stream is None else stream
    continuation: Optional[List[str]] = None
    try:
        source = plan_arg if plan_path is None else plan_path
        if not _state_file(os.path.abspath(str(source))).is_file():
            return None
        asked = fronted_mode_word(mode_word)
        mode_word = _blocked_step(asked, source)
        route = resolve_route(host_id, stderr=err, recorded=recorded_route)
        # Read once here only for a phase whose resume reads it (fix round
        # 28: an implement's resume also carries a manual task's answer);
        # generate-tasks' plain re-invoke reads its own status file.
        from .subagent_tasks import PHASE_BY_WRITE_KIND

        resumed = _skill_module("modes").resolve(mode_word)
        workflow = (
            _workflow_payload(Path(os.path.abspath(str(source))), host_id)
            if resumed is not None and resumed.phase in PHASE_BY_WRITE_KIND.values()
            else None
        )
        command = resume_command(
            plan_arg, host_id, route, mode_word, plan_path=plan_path,
            workflow=workflow,
        )
        if command is None and mode_word != asked:
            # The inner step has no resume of its own (a review that stopped,
            # nothing recorded yet, an apply with no progress for this
            # review): the composite's own continuation, in its word.
            continuation = _composite_continuation(asked, source)
            mode_word = _composite_of(asked).name
            command = phase_command(
                plan_arg, host_id, route, mode_word, *continuation, plan_path=plan_path)
        if command is None:
            return None
        print(f"{RESUME_COMMAND_MARKER} {command}", file=out)
        try:
            out.flush()
        except (AttributeError, ValueError):  # pragma: no cover - closed stream
            pass
    except AlreadyComplete as done:
        print(done.line, file=out)
        try:
            out.flush()
        except (AttributeError, ValueError):  # pragma: no cover - closed stream
            pass
        raise
    except Exception as exc:  # noqa: BLE001 - advisory: never fails the caller
        print(lookup_failure_line(exc), file=err)
        if strict:
            raise LookupFailed(str(exc)) from exc
        return None
    modes = _skill_module("modes")
    mode = modes.resolve(mode_word)
    # §2.8: the mode word the printed command runs, a commit mode on a commit
    # review, and the flags it carries without the front doors' own.
    view = commit_view_for(mode.name, plan_arg, plan_path) if mode is not None else None
    shown_mode = commit_mode_word(mode.name, view) if mode is not None else mode_word
    if continuation is not None:
        # The composite's own continuation: no stop of its own on record, so
        # no answers, why or stop lines; the flags are the command's own, so
        # a tool route's first option is this very command.
        if view is not None:
            from .commit_spelling import strip_fronted_flags

            continuation = strip_fronted_flags(continuation)
        resume = {
            "phase": mode.phase,
            "mode": shown_mode,
            "command": command,
            "flags": list(continuation),
            "markdown": render_resume_markdown(shown_mode, command, None, []),
        }
        cli_common.record_user_resume(resume)
        return command
    phases = (workflow or {}).get("phases") or {}
    resume: Dict[str, Any] = {
        "phase": mode.phase,
        # The mode its command runs (§2.6): a composite asked about answers
        # with an inner phase's resume, and an option call built from the word
        # asked would hand `--human-task` to the composite's parser.
        "mode": shown_mode,
        "command": command,
        # The flags the command carries after the plan, so a tool route
        # offers this very command as its first `options` entry (fix round
        # 14: the first option and `resume_command` must be one command).
        "flags": (
            [] if mode.phase in RERUN_RESUME_PHASES
            else _resume_flags(phases, mode.phase)
        ),
    }
    # Fix round 28: a resume that records a manual task done says why.
    gate_why = (
        manual_gate_why(phases.get("implement") or {})
        if len(resume["flags"]) > 1 else None
    )
    try:
        if gate_why is not None:
            # Fix round 29 (review of round 28 #1): a manual-task gate's
            # answers are the user's decline, read off the workflow on both
            # legs (the executor's stop records the same ones).
            answers = [
                {"command": step.command,
                 "flags": [RESUME_FLAG] + [
                     token for answer in step.answers
                     for token in ("--human-task", answer)],
                 "why": step.why}
                for step in gate_decline_steps(plan_arg, host_id, route, phases)
            ]
        else:
            answers = resume_answers(
                plan_arg, host_id, route, mode_word, plan_path=plan_path,
            )
    except Exception as exc:  # noqa: BLE001 - advisory: the resume still stands
        print(lookup_failure_line(exc), file=err)
        answers = []
    if answers:
        resume["answers"] = answers
        resume["answers_text"] = render_resume_answers(answers)
    # Fix round 22: what the plain resume does, as each answer says.
    why = gate_why or stop_resume_why_on_record(
        plan_arg if plan_path is None else plan_path, mode_word)
    if why:
        resume["why"] = why
    # Fix round 24: all of it as the report's closing section, ready to copy.
    resume["markdown"] = render_resume_markdown(shown_mode, command, why, answers or [])
    # Fix round 28 (live run 12 #5): the stop's own line as recorded, and the
    # same line without the ways forward this section carries, which the
    # servers relay in its place beside the section.
    try:
        lines = stop_headlines_on_record(
            plan_arg if plan_path is None else plan_path, mode_word,
            section_flags=resume["flags"])
    except Exception as exc:  # noqa: BLE001 - advisory: the resume still stands
        print(lookup_failure_line(exc), file=err)
        lines = None
    if lines is not None:
        resume["error_line"], resume["error_beside_section"] = lines
    cli_common.record_user_resume(resume)
    return command


def stop_answers_on_record(
    plan_path: Union[str, Path], mode_word: str,
) -> List[Dict[str, Any]]:
    """The answers the phase's last stop recorded, as data, or ``[]``.

    Read from ``{phase}/.status.json``'s write mirror
    (``progress.write_subagents.stop.answers``, written by
    ``write_batch_scheduler._stop_answers``): the run's own record of which
    ``--human-task`` answers its stop named. The folder is writable by every
    jailed batch and the entries become the tool routes' options, so each is
    kept only in the shape the plugin composes (fix round 23, review of round
    22 relay #5): ``flags`` as :func:`recorded_answer_flags` reads them and a
    ``why`` that passes :func:`recorded_why`. Any other entry is dropped,
    never relayed.
    """
    from .output_handler import phase_dir_path
    from .status_file import read_status

    modes = _skill_module("modes")
    mode = modes.resolve(mode_word)
    if mode is None or not mode.phase:
        return []
    source = Path(os.path.abspath(str(plan_path)))
    status = read_status(str(phase_dir_path(source, mode.phase)))
    progress = status.get("progress") if isinstance(status, dict) else None
    mirror = progress.get("write_subagents") if isinstance(progress, dict) else None
    stop = mirror.get("stop") if isinstance(mirror, dict) else None
    raw = stop.get("answers") if isinstance(stop, dict) else None
    answers: List[Dict[str, Any]] = []
    for entry in raw if isinstance(raw, list) else []:
        if not isinstance(entry, dict):
            continue
        flags = recorded_answer_flags(entry.get("flags"))
        why = recorded_why(entry.get("why"))
        if flags is not None and why is not None:
            answers.append({"flags": flags, "why": why})
    return answers


def stop_headlines_on_record(
    plan_path: Union[str, Path], mode_word: str,
    *, section_flags: Optional[Sequence[str]] = None,
) -> Optional[Tuple[str, str]]:
    """``(headline, beside_section)`` of the phase's last stop, as it
    recorded them (``progress.write_subagents.stop``: ``headline`` and
    ``write_batch_scheduler.HEADLINE_BESIDE_SECTION_KEY``), or ``None``
    (fix round 28, live run 12 #5).

    The second is the first without the ways forward the stop's resume
    section carries: what stopped, what it reported, what did not run, the
    fixes only the user can make and the tests line. ``util next-command
    --blocked`` hands both to the tool routes, which relay the second in the
    result's ``error`` while that ``error`` is still the first, word for
    word, so a stop the record does not describe is never re-worded. Each
    must be one plain line within ``cli_common.ERROR_MAX_CHARS``, and every
    answer the stop recorded must have passed :func:`stop_answers_on_record`
    (the section lists all of them), else ``None``: the folder is writable
    by every jailed batch. A stop whose own resume carries answers (a
    manual-task gate's ``resume_flags``, the merge of fix round 28) hands
    the lines back only while those flags are the plugin's shape and the
    section's resume, *section_flags*, is that very resume.
    """
    from . import cli_common
    from .output_handler import phase_dir_path
    from .status_file import read_status
    from .write_batch_scheduler import HEADLINE_BESIDE_SECTION_KEY

    modes = _skill_module("modes")
    mode = modes.resolve(mode_word)
    if mode is None or not mode.phase:
        return None
    source = Path(os.path.abspath(str(plan_path)))
    status = read_status(str(phase_dir_path(source, mode.phase)))
    progress = status.get("progress") if isinstance(status, dict) else None
    mirror = progress.get("write_subagents") if isinstance(progress, dict) else None
    stop = mirror.get("stop") if isinstance(mirror, dict) else None
    if not isinstance(stop, dict):
        return None

    def plain(value: Any) -> Optional[str]:
        if (not isinstance(value, str) or not value.strip()
                or len(value) > cli_common.ERROR_MAX_CHARS
                or plain_line(value) != value):
            return None
        return value

    headline = plain(stop.get("headline"))
    beside = plain(stop.get(HEADLINE_BESIDE_SECTION_KEY))
    if headline is None or beside is None or beside == headline:
        return None
    raw = stop.get("answers")
    recorded = raw if isinstance(raw, list) else []
    if len(stop_answers_on_record(source, mode_word)) != len(recorded):
        return None
    if "resume_flags" in stop:
        flags = recorded_answer_flags(stop.get("resume_flags"))
        if flags is None or flags != list(section_flags or ()):
            return None
    return headline, beside


def recorded_answer_flags(flags: Any) -> Optional[List[str]]:
    """*flags*, a stop answer's flags read back from a run's output folder,
    when they are what the plugin composes: ``--resume`` and then one or
    more ``--human-task <answer>`` pairs, each answer one
    :data:`_RECORDED_ANSWER`; else ``None`` (fix round 23)."""
    if (not isinstance(flags, list) or len(flags) < 3 or len(flags) % 2 == 0
            or flags[0] != RESUME_FLAG):
        return None
    for name, value in zip(flags[1::2], flags[2::2]):
        if (name != "--human-task" or not isinstance(value, str)
                or not _RECORDED_ANSWER.fullmatch(value)):
            return None
    return list(flags)


def stop_resume_why_on_record(
    plan_path: Union[str, Path], mode_word: str,
) -> Optional[str]:
    """What the plain resume of the phase's last stop does, as the stop
    recorded it (``progress.write_subagents.stop.resume_why``, written by
    ``write_batch_scheduler._stop_resume_why``; fix round 22), or ``None``.

    The run's output folder is writable by every jailed batch, so the value
    is relayed only when it is one plain line of at most
    :data:`MAX_RECORDED_WHY_CHARS` characters."""
    from .output_handler import phase_dir_path
    from .status_file import read_status

    modes = _skill_module("modes")
    mode = modes.resolve(mode_word)
    if mode is None or not mode.phase:
        return None
    source = Path(os.path.abspath(str(plan_path)))
    status = read_status(str(phase_dir_path(source, mode.phase)))
    progress = status.get("progress") if isinstance(status, dict) else None
    mirror = progress.get("write_subagents") if isinstance(progress, dict) else None
    stop = mirror.get("stop") if isinstance(mirror, dict) else None
    return recorded_why(stop.get("resume_why") if isinstance(stop, dict) else None)


def recorded_why(value: Any) -> Optional[str]:
    """*value*, a why read back from a run's output folder, when it is one
    plain line of at most :data:`MAX_RECORDED_WHY_CHARS` characters, else
    ``None``."""
    if not isinstance(value, str):
        return None
    why = value.strip()
    if (not why or len(why) > MAX_RECORDED_WHY_CHARS
            or any(not ch.isprintable() for ch in why)):
        return None
    return why


def resume_answers(
    plan_arg: str,
    host_id: str,
    route: Optional[str],
    mode_word: str,
    *,
    plan_path: Optional[Union[str, Path]] = None,
) -> List[Dict[str, Any]]:
    """Each answer the last stop offers, spelled the way this host's user types it.

    ``[{"command", "flags", "why"}]`` from :func:`stop_answers_on_record`,
    each command built by :func:`phase_command` — the same template and
    quoting as the resume command beside it. Fix round 14 (live run 5): the
    tool routes handed the user only the bare ``--resume`` in ``message`` and
    ``options`` while the answers the stop named sat in ``error``, and hosts
    relayed them in two of four first stops.
    """
    source = plan_arg if plan_path is None else plan_path
    return [
        {
            "command": phase_command(
                plan_arg, host_id, route, mode_word, *entry["flags"], plan_path=plan_path),
            "flags": entry["flags"],
            "why": entry["why"],
        }
        for entry in stop_answers_on_record(source, mode_word)
    ]


def render_resume_answers(answers: Sequence[Mapping[str, Any]]) -> str:
    """The answers as one run of text: `` `<command>` — <why>.`` each, one
    sentence apiece, the last ending the text.

    What the tool routes put in their needs-human ``message`` through the
    surface's ``needs_human_message.answers`` clause, so a host that relays
    only the message relays every way forward. Python owns the wording.
    The merge of fix round 28: each why was bracketed and the answers
    ``; ``-joined, so a why that ends in a bracket of its own ("… depend on
    it (T006)", a quoted finding "… (found 2)") read "(T006))", and the
    clause's stop after the last doubled one that ends in "…"; ``status``
    prints each unbracketed (``run_status.why_line``). Each why now follows
    its command and ends its sentence once (``text_clip.with_closing_mark``),
    and the clause adds no mark of its own after the text.
    """
    from .text_clip import with_closing_mark

    return " ".join(
        f"`{entry['command']}` — {with_closing_mark(entry['why'])}"
        for entry in answers)


# ---------------------------------------------------------------------------
# `multi_llm.py util next-command` (§2.2(3))
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    """``util next-command <plan> [--after <mode> | --blocked <mode>] [--host <id>]``.

    Read-only: it resolves the plan path only to find ``state.json`` and hands
    the plan string as received to the builder, with no ``finished_mode`` (the
    gate is off) and ``--after`` as ``after_mode``. Exit 0 with the block on
    stdout and the key set, or with nothing printed when there is no answer;
    exit 3 with one stderr line for an unknown ``--after``, a missing plan, or
    a workflow read / builder that raised. ``--blocked`` answers from the same
    ``state.json`` and refuses a missing plan the same way (adversarial review,
    2026-10-02: it skipped the plan check and read no state). ``--blocked`` of
    a composite whose every step is on record prints the ``[ALREADY_COMPLETE]``
    line and exits 2 (plans/improve-plan-and-improve-code.md §2.6).
    """
    import argparse

    modes = _skill_module("modes")
    # The composites that are not the whole workflow, from the table.
    composites = [m for m in modes.MODES if m.is_composite and not m.runs_workflow]
    composite_words = "|".join(m.name for m in composites)
    parser = argparse.ArgumentParser(
        prog="multi_llm.py util next-command",
        description=(
            "Print the workflow's next-phase command for a plan, as the "
            "next-command block (or the workflow-complete line), and set "
            "MULTI_LLM_RESULT.user_next_step. Read-only; reports state.json as "
            "recorded. Prints nothing when there is no answer."
        ),
        epilog=(
            "exit codes: 0 = answered, or nothing to answer | 2 = --blocked "
            f"{composite_words}: every step is on record for this review "
            "([ALREADY_COMPLETE] printed, nothing to resume) | 3 = unknown "
            "--after or --blocked mode, missing plan, or the lookup failed (one "
            "stderr line, no command printed)."
        ),
    )
    parser.add_argument("plan", help="Path to the plan file, as the user typed it")
    parser.add_argument(
        "--after", metavar="MODE", default=None,
        help="The mode that just ran: the walk starts after its phase "
             "(any mode word or alias; `full` reads suggested_next; "
             + "; ".join(f"`{m.name}` starts after {m.sequence[-1]}"
                         for m in composites)
             + ")",
    )
    parser.add_argument(
        "--blocked", metavar="MODE", default=None, dest="blocked",
        help="Instead of the next phase, print the command that resumes MODE's "
             "own stopped phase — a write phase with progress on record, or a "
             "generate-tasks whose dispatch failed in a way a re-run can change "
             "(`[RESUME_COMMAND]`, and "
             "MULTI_LLM_RESULT.user_resume). The tool routes ask this after an "
             "exit 3. Prints nothing for a mode that has none. "
             f"For {composite_words}: the step a plain re-run would run first, "
             "with that phase's own resume when it has one, else the "
             "composite's own continuation; when every step is on record, the "
             "[ALREADY_COMPLETE] line and exit 2. Excludes --after.",
    )
    parser.add_argument(
        "--host", default=None,
        help="Host whose spelling to print (default: $MULTI_LLM_HOST, else "
             "claude-code)",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.blocked is not None and args.after is not None:
        print("ERROR: --blocked and --after are mutually exclusive.",
              file=sys.stderr)
        return 3
    if args.blocked is not None and modes.resolve(args.blocked) is None:
        print(f"ERROR: unknown --blocked mode '{args.blocked}'.",
              file=sys.stderr)
        return 3
    if args.after is not None and modes.resolve(args.after) is None:
        aliases = ", ".join(f"{a}={t}" for a, t in sorted(modes.ALIASES.items()))
        print(
            f"ERROR: unknown --after mode '{args.after}'. Valid modes: "
            f"{', '.join(modes.mode_names())} (aliases: {aliases})",
            file=sys.stderr,
        )
        return 3
    plan_path = os.path.abspath(args.plan)
    if not os.path.isfile(plan_path):
        # plans/review-commits.md §2.8/§2.9: a commit review's pinned
        # `<base12>..<head12>` names its brief by name, as `status` maps it
        # (the tool routes' `--blocked` lookup carries the pinned range).
        brief = _pinned_brief(args.plan)
        if brief is not None:
            plan_path = brief
    if not os.path.isfile(plan_path):
        print(f"ERROR: plan file not found: {plan_path}", file=sys.stderr)
        return 3
    # A commit front door's word reads state as the phase it fronts; the
    # commands printed are spelled back as the commit mode (§2.8).
    if args.after is not None:
        args.after = fronted_mode_word(args.after)
    if args.blocked is not None:
        args.blocked = fronted_mode_word(args.blocked)
    host_id = _host_capabilities().resolve_host_id(explicit=args.host)
    # Fix round 24: from a shell, the route the plan's run was started on.
    recorded = recorded_route(plan_path, host_id, args.blocked or args.after)

    if args.blocked is not None:
        try:
            emit_resume(
                args.plan, host_id, args.blocked, plan_path=plan_path, strict=True,
                recorded_route=recorded,
            )
        except AlreadyComplete:
            return 2
        except LookupFailed:
            return 3
        return 0

    try:
        emit_answer(
            args.plan, host_id, None,
            after_mode=args.after, plan_path=plan_path, strict=True,
            with_answers=True, recorded_route=recorded, with_markdown=True,
        )
    except LookupFailed:
        return 3
    return 0
