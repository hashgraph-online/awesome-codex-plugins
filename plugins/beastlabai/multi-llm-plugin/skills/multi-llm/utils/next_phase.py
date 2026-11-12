"""The next-phase command a finished phase ends with.

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
  is that payload's answer, never a second table's, and the walk over them is
  ``utils/phase_walk``'s, the rule ``suggested_next`` is picked by.
* It never reads the environment. The route is resolved by the caller, once,
  with :func:`resolve_route` (``utils/routes``, the only code that reads a
  route signal) and handed in.
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
  ``utils/commit_spelling``. A plan's run, and a direct ``--head-ref`` run, are
  never mapped.
"""

from __future__ import annotations

import json as _json
import os
import re
import sys
from dataclasses import dataclass, replace as _replace
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union

from . import phase_walk
from .advisory import note_swallowed
from .text_clip import plain_line, with_closing_mark

# The route, the plan's spelling, the manual-task words and the phase command
# live below the CLI, where the write phases and the dispatcher plumbing read
# them (docs/development/dispatcher.md#import-layers). This module builds with
# them and re-exports every name for its readers; patch them in their owners.
from .manual_tasks import (  # noqa: F401 - re-exported
    AFTER_IDS_SHOWN,
    GATE_IDS_SHOWN,
    GATE_TITLE_CHARS,
    MAX_RECORDED_WHY_CHARS,
    _TASK_ID,
    _manual_gate_names,
    after_code_note,
    close_command,
    gate_resume_closes_the_manual_tasks,
    manual_close_ids,
    manual_close_lead,
    manual_close_note,
    manual_gate_decline_answers,
    manual_gate_flags,
    manual_gate_ids,
    manual_gate_why,
    manual_note_ids,
    manual_note_named,
    manual_waiting_count,
    waits_on_note,
)
from .next_phase_words import (  # noqa: F401 - re-exported
    brief_view,
    commit_mode_word,
    commit_spelled_args,
    commit_view_for,
    phase_command,
    spelled_view,
)
from .routes import (  # noqa: F401 - re-exported
    ARGS_SLOT,
    RESUME_FLAG,
    SKILL_ROUTE,
    _PLACEHOLDER_PREFIXES,
    _RECORDED_SPELLING,
    _host_capabilities,
    _install_tail,
    _is_skill_install,
    _path_parts,
    _skill_module,
    _steps_back_only_out_of_dirs,
    quote_plan_arg,
    recorded_plan_spelling,
    resolve_route,
)

#: The four line kinds of the block. The text after a command
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
#: (:func:`manual_close_note`). Not a command marker: the line
#: is a sentence that carries the command, never the command alone.
MANUAL_TASK_NOTE_MARKER = "[MANUAL_TASK_NOTE]"
#: The line after ``[MANUAL_TASK_NOTE]``: the command that records the
#: manual tasks done, alone. A command marker
#: like ``[NEXT_COMMAND]``: the Stop hook holds the report to it.
MANUAL_TASK_COMMAND_MARKER = "[MANUAL_TASK_COMMAND]"
#: One line above the block when the command it names is certain to be refused
#: (``check_workflow_prerequisites.repo_wide_sandbox_warning``). Not a command
#: marker: no consumer of the block reads it as one.
RUNNER_WARNING_MARKER = "[RUNNER_WARNING]"

#: The answers line pair ``util next-command`` prints under a resume of a
#: stopped native implement: the why on its own line, then one
#: resume command carrying every ``--human-task`` answer the stop waits for.
#: A command marker like the others: the text after it is the command alone.
NEXT_COMMAND_ANSWERS_WHY_MARKER = "[NEXT_COMMAND_ANSWERS_WHY]"
NEXT_COMMAND_ANSWERS_MARKER = "[NEXT_COMMAND_ANSWERS]"

#: The line ``util next-command`` prints directly above the ``--resume`` of a
#: stopped native implement: what that plain resume does on an
#: unchanged tree (``stop_answers.native_resume_why``), as the
#: answers' why lines say what each answer does. Not a command marker.
NEXT_COMMAND_WHY_MARKER = "[NEXT_COMMAND_WHY]"

#: One ``--human-task`` value a stop's recorded answer may carry: the shapes
#: the executor composes — an implement task's ``done``/``skip``/``retry``
#: (``stop_answers.compose_stop_answers``) and an apply batch's
#: ``skip`` of a partial application (``WriteBatchScheduler._stop_answers``).
#: Matched whole.
_RECORDED_ANSWER = re.compile(
    r"T[0-9]{3}=(?:done|skip|retry)|apply-(?:task-|fix-)?batch-[0-9]+=skip")

#: The one line :func:`emit_resume` prints: the command that resumes a stopped
#: write phase, and nothing else on the line (same rule as ``[NEXT_COMMAND]``).
RESUME_COMMAND_MARKER = "[RESUME_COMMAND]"

#: The line ``util next-command`` prints above a stopped native implement's
#: commands when nothing ran the repository's tests
#: (``verification_lines.native_stop_unverified_line``): the
#: executor stop's own line, for the report. Not a command marker: the text
#: after it is a sentence that names a setting, never a command to copy.
TESTS_NOT_RUN_MARKER = "[TESTS_NOT_RUN]"

#: The lines ``util next-command`` prints around its answer's ``markdown``:
#: the report's closing section already written, below the marker lines, for
#: the report to copy as it is. Every line between the two is the section's;
#: the Stop hook reads no marker line there (``report_check.find_blocks``).
NEXT_STEP_MARKDOWN_MARKER = "[NEXT_STEP_MARKDOWN]"
NEXT_STEP_MARKDOWN_END_MARKER = "[NEXT_STEP_MARKDOWN_END]"

#: The block's markers whose lines say what ``user_next_step`` carries itself
#: (its ``complete``, ``command``, ``why``, ``optional_before``, ``answers``
#: and ``manual_tasks`` keys, all in its ``markdown``). A tool server drops
#: these lines from the ``output`` of a result that carries the key, shipped as the surface's
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

    ``waits_on`` is set on a task skipped because it depends
    on a deferred manual task: a task implement runs itself once that one is
    recorded done, which the old wording ("no phase will run") denied.
    """

    id: str
    title: Optional[str] = None
    waits_on: Optional[str] = None
    #: A manual task that comes after code tasks implement has not run yet: those
    #: code tasks, by id. Such a task is not in
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
    #: recorded done (``waits_on``). Present on a ``complete`` answer and on a
    #: command answer. Every block renders them: under ``[WORKFLOW_COMPLETE]``,
    #: and after a command block's commands (:func:`render_next_phase_lines`).
    manual_tasks: Tuple[ManualTask, ...] = ()
    #: On a ``--resume`` of a stopped implement, from ``util next-command``
    #: only: each answer the stop offers, the one combined command first
    #: (:func:`implement_answers`; each alone too, as the tool
    #: routes list them). Rendered after the primary and the optional
    #: entries, a why line above each command, and carried as the list
    #: ``user_next_step.answers``.
    answers: Tuple[AnswersStep, ...] = ()
    #: Beside ``manual_tasks``: how the user records them done
    #: (:func:`manual_close_lead`, a sentence leading into
    #: ``manual_tasks_command``, the command apart).
    manual_tasks_note: Optional[str] = None
    #: The command that records the manual tasks done, in the host's spelling
    #: (:func:`close_command`).
    manual_tasks_command: Optional[str] = None
    #: On a stopped native implement's ``--resume``, from ``util
    #: next-command`` only: the line saying nothing ran the repository's tests, printed
    #: as ``[TESTS_NOT_RUN]`` above the commands and
    #: never part of ``user_next_step`` (the tool routes carry it in the
    #: stop's ``error``).
    tests_note: Optional[str] = None
    #: On a stopped native implement's ``--resume``, from ``util
    #: next-command`` only: what that plain resume does on an unchanged tree. Printed as
    #: ``[NEXT_COMMAND_WHY]`` above the command and carried as
    #: ``user_next_step.why``.
    why: Optional[str] = None
    #: On a resume of a stopped phase: the line the section
    #: opens with (:func:`resume_lead`), in ``markdown`` only.
    lead: Optional[str] = None
    #: Another way on instead of the primary, each with its why above its
    #: command, rendered after the primary and its optional entries. Carried as
    #: ``user_next_step.instead``; the block prints each as an optional pair.
    instead: Tuple[OptionalStep, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        """The ``user_next_step`` value (the outcome table).

        Complete is ``{"phase": null, "command": null, "complete": true}``,
        plus ``manual_tasks`` (``[{id, title}]``) when the run deferred any —
        additive, so a reader that knows only the three keys reads the same
        completion; otherwise ``optional_before`` is present only when non-empty.
        Every answer ends with ``markdown``, the step as the report's closing
        section (:func:`render_next_step_markdown`), also additive.
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
            # The tool routes relay this key, and `util
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

    The command answers :func:`manual_close_ids` only.
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


def gate_resume_suggested(workflow: Mapping[str, Any]) -> List[str]:
    """The flags of implement's resume when it, not the payload's
    ``suggested_next``, is the next step, else ``[]``: implement completed with code
    tasks still waiting on a
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
    order = _skill_module("modes").PREREQUISITE_PHASES
    if not phase_walk.comes_after(order, primary, "implement"):
        return []
    return manual_gate_flags(implement)


def instead_why(phase: str) -> str:
    """The why above the way on that stays beside the resume running code
    tasks left waiting on a manual task."""
    if phase == "code-review":
        return "Or review the code implement has run so far:"
    return "Or go on with the workflow on the code implement has run so far:"


def _with_manual_tasks(
    answer: NextPhase,
    phases: Mapping[str, Mapping[str, Any]],
    *,
    template: str,
    plan_arg: str,
) -> NextPhase:
    """*answer* (a command answer) carrying the deferred manual tasks and the
    note on recording them done, when the run deferred any."""
    manual, note, command = _manual_tasks(phases, template=template, plan_arg=plan_arg)
    if not manual:
        return answer

    return _replace(answer, manual_tasks=manual, manual_tasks_note=note,
                    manual_tasks_command=command)


# ---------------------------------------------------------------------------
# The route a run was started on
# ---------------------------------------------------------------------------

def recorded_route(
    plan_path: Union[str, Path],
    host_id: str,
    mode_word: Optional[str] = None,
) -> Optional[str]:
    """The tool route a run of *plan_path* on *host_id* was started on, or
    ``None``.

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
    # Imported here to keep next_phase light.
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
    except Exception as exc:  # noqa: BLE001 - advisory: the default route stands
        note_swallowed("next phase: recorded route", exc)
        return None
    return route_of(newest[1]) if newest else None


# ---------------------------------------------------------------------------
# The commit spelling
# ---------------------------------------------------------------------------
#
# The two phase front doors re-record as the code modes, so every command
# built here from state would read `--apply-code-fixes <brief>`. The mapping
# itself is `commit_spelling`'s; this module only decides, per printed
# command, whether it applies.

#: The why above ``--apply-commit-fixes`` after a commit review: the
#: user works through the two reports before applying, and the composite is
#: the way to skip that step.
COMMIT_REPORTS_WHY = (
    "Read the review's two reports before applying: {md} and {html}. A finding "
    "marked skipped, valid or invalid there, or an edited description, is what "
    "the apply honours. --improve-commits would skip this reading step: it "
    "applies the validated fixes unattended."
)


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
    (``commit_paths.brief_for_pinned``, no git call beyond the root), or
    ``None`` for other text or outside a repository."""
    try:
        # Imported here to keep next_phase light.
        from .commit_paths import brief_for_pinned

        brief = brief_for_pinned(str(text))
    except Exception as exc:  # noqa: BLE001 - not a pinned range here
        note_swallowed("next phase: pinned brief", exc)
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
    # Imported here to keep next_phase light.
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
    # Imported here to keep next_phase light.
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
        ends on, ``Mode.last_phase``, gate included. ``full``, and both modes ``None``, answer from
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

    def status_of(phase: str) -> Optional[str]:
        return phase_walk.entry_of(phases, phase).get("status")

    def is_open(phase: str) -> bool:
        return phase_walk.is_open(phase_walk.entry_of(phases, phase))

    def warning_of(phase: str) -> Optional[str]:
        return (phases.get(phase) or {}).get("warning") or None

    implement_entry: Mapping[str, Any] = phases.get("implement") or {}
    # While every code task
    # implement has left waits on a manual task not recorded done, its plain
    # resume runs nothing; the resume records the manual tasks the user can
    # do now done, and only those.
    gate_flags = (
        manual_gate_flags(implement_entry)
        if implement_entry.get("manual_gate") else []
    )
    # A commit review's commands read as the
    # commit modes, with the pinned range (read once; `None` for a plan).
    commit_brief = brief_view(plan_arg, plan_path)

    def command_answer(answer: NextPhase) -> NextPhase:
        # A command answer names the deferred manual tasks
        # and how to record them done, as the complete answer does. The one
        # place a command answer gets them (`emit_answer` had a
        # second writer for `--after implement`, and the two packages that
        # wrote them disagreed on what the answer carries).
        if (answer.phase == "implement" and gate_flags and not answer.why
                and status_of("implement") == "in_progress"):
            answer = _replace(answer, why=manual_gate_why(implement_entry))
        if (answer.phase == "apply-code-fixes" and not answer.why
                and status_of("apply-code-fixes") != "in_progress"
                and spelled_view("apply-code-fixes", commit_brief) is not None):
            # After a commit review, the reports come before the
            # apply, and the composite is the way to skip reading them.
            answer = _replace(answer, why=commit_reports_why(plan_arg, plan_path))
        answer = _with_manual_tasks(answer, phases, template=template, plan_arg=plan_arg)
        if (answer.manual_tasks_command
                and answer.manual_tasks_command == answer.command):
            # The command already leads the section.
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
            if phase_walk.is_required(phase) or not is_open(phase):
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
        # Implement finished with code
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
        # position, so a review-code suggested after a
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

    # The walk from *start* (`phase_walk.next_step`, the rule `suggested_next`
    # is picked by): the start itself in progress, else a required phase
    # before it that was started and not finished, else a stale start, else
    # the first open required phase after it.
    step = phase_walk.next_step(phases, order, after=start)
    if step.kind == phase_walk.RESUME:
        # A resumable phase is its own answer; the span walk does not run.
        return command_answer(NextPhase(
            phase=start, command=command_for(start), warning=warning_of(start),
        ))
    if gated and is_open(start):
        # The finished phase is not on record: exit 0 at a pending marker, a
        # native first call, a fresh detach invoker. Not a finished phase.
        return None

    index = order.index(start)
    if step.kind == phase_walk.STARTED:
        # An earlier phase started and not finished comes first, so this
        # answer and `suggested_next` (the notice on the same result line,
        # `status`) name the same phase; see docs/development/status.md.
        earlier = step.phase
        return command_answer(NextPhase(
            phase=earlier,
            command=command_for(earlier),
            optional_before=optional_steps(order[: order.index(earlier)]),
            warning=warning_of(earlier),
        ))
    if step.kind == phase_walk.STALE:
        # Reached only with the gate off: under it a stale start is "not on
        # record" and returned None above (exit 0 at a pending marker must
        # print nothing).
        return command_answer(NextPhase(
            phase=start, command=command_for(start), warning=warning_of(start),
        ))
    primary = step.phase
    if primary is None:
        # An optional phase never keeps a workflow open, and one the walk did
        # not reach is never suggested: no `optional_before` on completion.
        return _complete(phases, template=template, plan_arg=plan_arg)
    waiting_flags = manual_gate_flags(implement_entry) if start == "implement" else []
    if waiting_flags:
        # Implement finished
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
    # Imported here to keep next_phase light.
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
    # Imported here to keep next_phase light.
    from .output_handler import output_dir_path
    from .state_manager import StateManager

    prereq = _skill_module("check_workflow_prerequisites")
    state = StateManager(plan_path, read_only=True)
    return bool(prereq.collect_missing(state, output_dir_path(plan_path), phase))


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
    way forward is ``--<mode> <plan> --resume``, and 2026-10-02 neither tool route could
    say it: Codex ended a
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
    review they attached ``--resume`` to every write-phase exit 3,
    and ``util next-command does-not-exist.md --blocked implement`` printed
    one for a plan that does not exist. The same rule as
    :func:`next_phase_commands`'s ``command_for``: ``in_progress`` is the one
    status that spells ``--resume``.

    A commit front door's word (``apply-commit-fixes``) answers as the phase
    it fronts, and on a commit review the command is spelled back as the
    commit mode with the pinned range.
    """
    modes = _skill_module("modes")
    mode = modes.resolve(fronted_mode_word(mode_word))
    if mode is None or not mode.is_workflow_phase or not mode.phase:
        return None
    # Imported here to keep next_phase light.
    from .subagent_tasks import PHASE_BY_WRITE_KIND

    template = _host_capabilities().next_command_template(host_id, route)
    view = commit_view_for(mode.name, plan_arg, plan_path)
    if mode.phase in RERUN_RESUME_PHASES:
        source = Path(os.path.abspath(str(plan_arg if plan_path is None else plan_path)))
        if phase_status is None:
            # Imported here to keep next_phase light.
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
    do now, that task's ``--human-task <id>=done`` too."""
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
    """The block's lines, primary first.

    Complete renders ``[WORKFLOW_COMPLETE]``, then one ``[MANUAL_TASK]`` line
    per task the run deferred to the user (none when it deferred nothing), the
    ``[MANUAL_TASK_NOTE]`` line and the ``[MANUAL_TASK_COMMAND]`` line. Otherwise the ``[NEXT_COMMAND]`` line
    comes first (below a ``[RUNNER_WARNING]`` and a ``[TESTS_NOT_RUN]`` line
    when the answer carries them), then each ``optional_before`` entry's
    ``[NEXT_COMMAND_OPTIONAL_WHY]`` / ``[NEXT_COMMAND_OPTIONAL]`` pair in the
    answer's order, the answers pair, and then the same manual-task lines. A
    command line holds the command and nothing else, and every other line
    holds one plain line (:func:`~utils.text_clip.plain_line`):
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
    # After the commands, on every command answer that carries them: the tasks implement
    # deferred to the user, and how to record
    # them done.
    return lines + manual_lines


#: The labels :func:`render_next_step_markdown` writes.
#: Above a stopped phase's resume; ``{phase}`` is its mode word.
RESUME_LEAD = "To go on with {phase}:"
OPTIONAL_LEAD = "Optional, before that:"
MANUAL_TASKS_LEAD = "Manual tasks left for you:"
#: The same lead over one task.
MANUAL_TASK_LEAD = "Manual task left for you:"
#: Above a stopped implement's answers (status says "or answer the stop
#: with:"): what the user types instead of the resume.
ANSWERS_LEAD = "Or answer the stop with one of these:"
WORKFLOW_COMPLETE_SENTENCE = "Workflow complete."


def resume_lead(phase: str) -> str:
    """:data:`RESUME_LEAD` for *phase*."""
    return RESUME_LEAD.replace("{phase}", str(phase))


#: A first character that could open a fence, a heading, a quote, a list, an
#: HTML block or a marker line when a text line of the section starts with it.
_MARKDOWN_OPENERS = frozenset("`~#>[<-*+_|=")


def markdown_text(text: Any) -> str:
    """*text* as one plain text line of the section (:func:`plain_line`),
    its first character escaped (CommonMark's backslash) when it could open
    a block of its own: a why or a note is read back from a
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
    (``user_next_step.markdown``).

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
    and task line is one plain line, so nothing read back
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
    :func:`render_next_step_markdown`'s rules: the lead
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

    The native leg's
    stop printed no command, so the host wrote "re-run with --resume" as
    prose, or two separate commands the user had to merge; this answered with
    one command carrying every answer. That one command was all, while the tool routes list each
    answer alone too (``T005=skip`` alone, ``T002=done`` alone, …), so the
    host described answers the plugin never printed and the fix path had no
    T005-only command to run. The answers now come from the executor's own
    composer (``stop_answers.native_stop_answers`` →
    ``compose_stop_answers``) over ``state.json`` as recorded: the combined
    command first when more than one task waits, then each task's answers,
    each with its why, in the tool routes' words, every command in this
    host's spelling (:func:`phase_command`). ``()`` when no task waits.
    """

    source = plan_arg if plan_path is None else plan_path
    state_file = _state_file(os.path.abspath(str(source)))
    try:
        state = _json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ()
    if not isinstance(state, dict):
        return ()
    # Imported here to keep next_phase light.
    from .stop_answers import native_stop_answers

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
    otherwise."""
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
    unchanged tree (``stop_answers.native_resume_why`` over
    ``state.json`` as recorded, and the implement folder for the executor's
    check stamps), or ``None``."""

    # Imported here to keep next_phase light.
    from .output_handler import phase_dir_path

    source = os.path.abspath(str(plan_arg if plan_path is None else plan_path))
    try:
        state = _json.loads(_state_file(source).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(state, dict):
        return None
    # Imported here to keep next_phase light.
    from .stop_answers import native_resume_why

    return native_resume_why(
        state, phase_dir=str(phase_dir_path(Path(source), "implement")))


# ---------------------------------------------------------------------------
# The emitters' shared step
# ---------------------------------------------------------------------------

class LookupFailed(Exception):
    """Raised by :func:`emit_answer` under ``strict=True``, after its stderr line."""


#: How the one stderr line a failed lookup prints opens. ``util next-command``
#: exits 3 with it, and the Claude Code report quotes it.
LOOKUP_FAILED_PREFIX = "multi-llm: next-command lookup failed"


def lookup_failure_line(exc: BaseException) -> str:
    """The one stderr line naming a failed workflow read or builder raise."""
    message = " ".join(part.strip() for part in str(exc).splitlines() if part.strip())
    detail = f"{type(exc).__name__}: {message}" if message else type(exc).__name__
    return f"{LOOKUP_FAILED_PREFIX} ({detail}); no next command printed"


def _state_file(plan_path: Union[str, Path]) -> Path:
    """Where ``StateManager`` keeps *plan_path*'s ``state.json`` (computed only)."""
    # Imported here to keep next_phase light.
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
    ``finished_mode`` from its own sources. The block goes to *stream* (``sys.stdout``
    by default; an
    invocation that asked for JSON output passes ``sys.stderr``).

    Outcomes, per the table: an answer prints the block and records the key
    (``complete`` included); ``None`` prints and records nothing. Any exception
    — the workflow read, the route, the builder — prints and records nothing
    either: one stderr line (:func:`lookup_failure_line`) names it and this
    returns ``None``, or raises :class:`LookupFailed` under *strict*. The block
    is written before the key is recorded, so a failed write leaves no key.
    *recorded_route* is the route the run being answered for was started on
    (:func:`recorded_route`), used when this process names none.
    With *with_markdown* (``util next-command``) the block is
    followed by the answer's ``markdown`` between
    :data:`NEXT_STEP_MARKDOWN_MARKER` and :data:`NEXT_STEP_MARKDOWN_END_MARKER`,
    the section the Claude Code report copies as it is.

    With *finished_mode* given and no *workflow* handed in, a plan whose
    ``state.json`` does not exist answers ``None`` without reading anything:
    no phase can be on record there, so the gate could only refuse, and the
    workflow read would create the plan's output dir for a run that recorded
    nothing.
    """
    # Imported here to keep next_phase light.
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
        # The resume of an implement every code task of which
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
            # answers, beside its resume.
            if plain_resume:
                answers = implement_answers(
                    plan_arg, host_id, route, plan_path=plan_path,
                )
                if answers:
                    answer = _replace(answer, answers=answers)
                # And what the plain resume does.
                why = implement_resume_why(plan_arg, plan_path=plan_path)
                if why:
                    answer = _replace(answer, why=why)
            else:
                # A manual-task gate's
                # other way on, the user's decline, as the executor's stop
                # records it for the tool routes.
                if workflow is None:
                    workflow = _workflow_payload(Path(os.path.abspath(str(
                        plan_arg if plan_path is None else plan_path))), host_id)
                declines = gate_decline_steps(
                    plan_arg, host_id, route, workflow.get("phases") or {})
                if declines:
                    answer = _replace(answer, answers=declines)
            # Under the line the tool routes' section opens with.
            answer = _replace(answer, lead=resume_lead(answer.phase))
            # The native
            # stop's line saying nothing ran the repository's tests, which
            # the executor stop prints itself.
            # Imported here to keep next_phase light.
            from .verification_lines import native_stop_unverified_line

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
    record for the review on file, after it printed :attr:`line` (the
    ``[ALREADY_COMPLETE]`` line) on its stream. Not a failed lookup: ``util
    next-command --blocked`` exits 2 on it, the code the composite's own
    re-run exits with in the same state, and records no ``user_resume``."""

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
    """The mode word ``--blocked <mode_word>`` answers for.

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
    # Imported here to keep next_phase light.
    from . import improve_workflow

    args = improve_workflow.parse_args(mode.name, ["--plan-file", str(plan_path)])
    records = improve_workflow.read_records(mode.name, plan_path, args)
    for word in mode.sequence:
        if improve_workflow.skip_reason(mode.name, word, args, records) is None:
            return word
    raise AlreadyComplete(improve_workflow.already_complete_line(mode.name, args, records))


def _composite_continuation(mode_word: str, plan_path: Union[str, Path]) -> List[str]:
    """The flags after the plan in a composite's own continuation.

    ``improve_workflow.recorded_continuation`` of the ``replay_flags`` the
    composite's ``run`` record holds in its run dir (``{plan}/improve-plan/``):
    the row-14 command its ``_phase_failed`` printed, the user's selectors and
    never ``--force``, plus ``--resume``. ``--resume`` alone with no record (a
    foreground run writes none) or a record whose list is not a list. Raises
    ``improve_workflow.ContinuationError`` for flags the composite's parser
    rejects, and ``ValueError`` for a token one printed line cannot carry: the
    folder is writable by every jailed batch, and both are a failed lookup.
    """
    # Imported here to keep next_phase light.
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
    printed: the step a bare re-run would run first
    (:func:`_blocked_step`), with that phase's own resume, answers, why and
    section when it has a resume; else the composite's own continuation
    (:func:`_composite_continuation`), the composite's word, in the host's
    spelling. Every step on record prints the ``[ALREADY_COMPLETE]`` line on
    *stream* and raises :class:`AlreadyComplete`, with no ``user_resume``.
    ``user_resume.mode`` names the mode its command runs, which the tool
    routes build their option calls from.

    On a commit review a front door's word
    is asked as the phase it fronts, and the command, ``mode``, ``flags``
    and section are spelled back as the commit mode with the pinned range.
    """
    # Imported here to keep next_phase light.
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
        # Read once here only for a phase whose resume reads it (an implement's resume
        # also carries a manual task's answer);
        # generate-tasks' plain re-invoke reads its own status file.
        # Imported here to keep next_phase light.
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
    # The mode word the printed command runs, a commit mode on a commit
    # review, and the flags it carries without the front doors' own.
    view = commit_view_for(mode.name, plan_arg, plan_path) if mode is not None else None
    shown_mode = commit_mode_word(mode.name, view) if mode is not None else mode_word
    if continuation is not None:
        # The composite's own continuation: no stop of its own on record, so
        # no answers, why or stop lines; the flags are the command's own, so
        # a tool route's first option is this very command.
        if view is not None:
            # Imported here to keep next_phase light.
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
        # The mode its command runs: a composite asked about answers
        # with an inner phase's resume, and an option call built from the word
        # asked would hand `--human-task` to the composite's parser.
        "mode": shown_mode,
        "command": command,
        # The flags the command carries after the plan, so a tool route
        # offers this very command as its first `options` entry (the first option and
        # `resume_command` must be one command).
        "flags": (
            [] if mode.phase in RERUN_RESUME_PHASES
            else _resume_flags(phases, mode.phase)
        ),
    }
    # A resume that records a manual task done says why.
    gate_why = (
        manual_gate_why(phases.get("implement") or {})
        if len(resume["flags"]) > 1 else None
    )
    try:
        if gate_why is not None:
            # A manual-task gate's
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
    # What the plain resume does, as each answer says.
    why = gate_why or stop_resume_why_on_record(
        plan_arg if plan_path is None else plan_path, mode_word)
    if why:
        resume["why"] = why
    # All of it as the report's closing section, ready to copy.
    resume["markdown"] = render_resume_markdown(shown_mode, command, why, answers or [])
    # The stop's own line as recorded, and the
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
    ``write_stop.StopAccount.stop_answers``): the run's own record of which
    ``--human-task`` answers its stop named. The folder is writable by every
    jailed batch and the entries become the tool routes' options, so each is
    kept only in the shape the plugin composes: ``flags`` as
    :func:`recorded_answer_flags` reads them and a
    ``why`` that passes :func:`recorded_why`. Any other entry is dropped,
    never relayed.
    """
    # Imported here to keep next_phase light.
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
    ``stop_answers.HEADLINE_BESIDE_SECTION_KEY``), or ``None``.

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
    manual-task gate's ``resume_flags``) hands
    the lines back only while those flags are the plugin's shape and the
    section's resume, *section_flags*, is that very resume.
    """
    # Imported here to keep next_phase light.
    from . import cli_common
    from .output_handler import phase_dir_path
    from .status_file import read_status
    from .stop_answers import HEADLINE_BESIDE_SECTION_KEY

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
    :data:`_RECORDED_ANSWER`; else ``None``."""
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
    ``write_stop.StopAccount.stop_resume_why``), or ``None``.

    The run's output folder is writable by every jailed batch, so the value
    is relayed only when it is one plain line of at most
    :data:`MAX_RECORDED_WHY_CHARS` characters."""
    # Imported here to keep next_phase light.
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
    quoting as the resume command beside it. The
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
    The: each why was bracketed and the answers
    ``; ``-joined, so a why that ends in a bracket of its own ("… depend on
    it (T006)", a quoted finding "… (found 2)") read "(T006))", and the
    clause's stop after the last doubled one that ends in "…"; ``status``
    prints each unbracketed (``run_status.why_line``). Each why now follows
    its command and ends its sentence once (``text_clip.with_closing_mark``),
    and the clause adds no mark of its own after the text.
    """

    return " ".join(
        f"`{entry['command']}` — {with_closing_mark(entry['why'])}"
        for entry in answers)


# ---------------------------------------------------------------------------
# `multi_llm.py util next-command`
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
    line and exits 2.
    """
    # Imported here: next_phase does not otherwise load argparse.
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
        # A commit review's pinned
        # `<base12>..<head12>` names its brief by name, as `status` maps it
        # (the tool routes' `--blocked` lookup carries the pinned range).
        brief = _pinned_brief(args.plan)
        if brief is not None:
            plan_path = brief
    if not os.path.isfile(plan_path):
        print(f"ERROR: plan file not found: {plan_path}", file=sys.stderr)
        return 3
    # A commit front door's word reads state as the phase it fronts; the
    # commands printed are spelled back as the commit mode.
    if args.after is not None:
        args.after = fronted_mode_word(args.after)
    if args.blocked is not None:
        args.blocked = fronted_mode_word(args.blocked)
    host_id = _host_capabilities().resolve_host_id(explicit=args.host)
    # From a shell, the route the plan's run was started on.
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
