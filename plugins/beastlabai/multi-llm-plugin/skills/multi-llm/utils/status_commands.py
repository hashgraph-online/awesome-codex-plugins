"""The commands ``status`` prints, spelled the way the reader types them.

The speller (:func:`user_speller`), the resume / retry / rerun commands and
the ``resume with:`` block a stopped run gets (:func:`_resume_lines`), and the
``driver.subagent_runner`` section (:func:`render_runner_text`). Reads
``status_views`` only (docs/development/status.md#printed-follow-up-commands).
"""

from __future__ import annotations

import functools
import io
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from . import cli_common, detach, host_capabilities, status_views
from .advisory import note_swallowed
from .cli_common import dispatcher_command
from .status_views import _IMPLEMENT_PHASE
from .task_ledger import mirror_ids


def why_line(why: str) -> str:
    """A command's why on the line under it, as plain text two columns in,
    as the ready section prints it above its command. It was bracketed, and a why that ends
    in a bracket of its own ("… depend on it (T006)", a quoted finding)
    read "(T006))"."""
    return f"        {why}"


#: The modes whose ``--reaggregate`` is the retry-only-the-failures verb a
#: failed run resumes with (D2 step 4): it re-dispatches the failed batches and
#: re-reads the rest. Every mode in neither table keeps ``--force``, the only
#: resume verb it accepts. ``status`` cannot afford to import each
#: orchestrator's parser to derive this, so these are the two tables in this
#: module that are typed rather than read. ``review-commits`` forwards every
#: flag it does not own to review-code, so its
#: retry verb is review-code's.
_REAGGREGATE_MODES = ("review-plan", "review-tasks", "review-code",
                      "review-commits")

#: Modes whose retry verb is neither. ``generate-tasks`` has a ``--reaggregate``
#: too, but there it is the native host's second half — it only ever *consumes*
#: an existing ``task_generation_result.json`` and refuses when there is none —
#: so it never re-dispatches a failed task. The plain re-invoke does both:
#: re-dispatches what failed, consumes a valid result if one is on disk. This is
#: the verb that phase's own retry hint prints, and the ``resume with:`` line
#: has to agree with it: measured 2026-09-14, the two lines disagreed, the
#: session model followed this one, and the run ended on ``--reaggregate found
#: no task_generation_result.json`` with nothing re-dispatched.
#:
#: The four write phases resume with ``--resume``, the flag their own exit-3
#: block names ("re-invoke with --resume, which re-dispatches only the
#: unfinished batches and replays the prior-changes log from disk"). ``--force``
#: is not their resume verb at all — the apply parsers define it as an alias
#: for ``--yes`` (bulk approval), and under it the apply base re-ingests every
#: human decision instead of replaying the recorded ones. Measured 2026-09-15
#: on a failed ``apply-task-suggestions``: the log said ``--resume``, this line
#: said ``--force``, and the session model ran ``--claude-decide --force`` twice
#: before a human typed ``--resume`` by hand.
#:
#: ``full`` resumes with ``--resume`` too, the verb its own row-14 stop names
#: (``full <plan> --resume``, continue from the first phase not recorded). Under
#: ``full`` ``--force`` re-enters every recorded phase, so a stopped ``full`` run
#: told to re-run with it started over instead of continuing.
#:
#: The two review-then-apply composites resume with ``--resume`` as well, and
#: ``--force`` would start a new review round. Their line is not built from
#: this verb and the recorded flags but from the composite's own continuation
#: (:func:`_composite_resume_tokens`); the entries say what that ends with.
#:
#: The commit modes take their fronted
#: phase's verb: ``apply-commit-fixes`` is apply-code-fixes' ``--resume``,
#: and ``improve-commits`` resumes like the other composites.
_RESUME_VERB_BY_MODE = {
    "generate-tasks": "--yes",
    "apply-suggestions": "--resume",
    "apply-task-suggestions": "--resume",
    "apply-code-fixes": "--resume",
    "implement": "--resume",
    "full": "--resume",
    "improve-plan": "--resume",
    "improve-code": "--resume",
    "apply-commit-fixes": "--resume",
    "improve-commits": "--resume",
}

#: The modes whose progress mirror is ``write_subagents``
#: (``write_reports.WriteReports.mirror_status``) rather than ``subagents``.
_WRITE_MODES = ("apply-suggestions", "apply-task-suggestions",
                "apply-code-fixes", "implement")


#: Spells one retry the way the host's user types it: ``(mode, positionals
#: after the plan, flags and verbs) -> command``, or ``None`` to keep the
#: dispatcher command (:func:`user_speller`).
Speller = Any


def user_speller(
    host_id: Optional[str], plan_arg: str,
    *, plan_path: Optional[Path] = None,
) -> Optional[Speller]:
    """The run view's commands in *host_id*'s spelling, or ``None``.

    ``resume with:`` printed the raw ``uv
    run … multi_llm.py … --host codex --detach --resume`` while every other
    next-step line of the same view (the manual-task note, the next phase) was
    the host's own spelling. Built from the same ``next_command`` template and
    quoting as ``next_phase.phase_command``, with the plan as typed and only
    the flags the user typed (:func:`cli_common.drop_host_composed_flags`
    over what this host's own skill or shim composes:
    :func:`cli_common.file_route_composed_flags`).

    ``None`` on a tool route (``modes.TOOL_ROUTES``): there the tool's server
    re-spells every dispatcher command in the output itself and also hands it
    back as a tool call in ``options``, which it can only do from the
    dispatcher command. ``None`` too when the host has no template for its
    route; the dispatcher command stands then.

    A reader whose environment names no
    route — a shell's ``status`` — spells a run in the route that run was
    started on, passed per call as *route* (its record's ``run.route``,
    :func:`_view_speller`): that route's template and the flags it composes
    (the tool routes' reserved set). A shell's ``status --host codex`` used
    to print the file shim's sentence for a run the plugin's tool started.

    On a commit review (the ``state.json`` at
    *plan_path*, else at *plan_arg*, holds ``commit_range``) a command naming
    review-code, apply-code-fixes or improve-commits reads as the commit mode
    with the pinned range, and leaves out every flag a front door synthesises
    or consumes (``next_phase.commit_view_for``).
    """

    # Imported here to keep run_status, which loads this module, light.
    from . import next_phase

    try:
        modes = next_phase._skill_module("modes")
        host = host_capabilities.resolve_host_id(explicit=host_id)
        if next_phase.resolve_route(host, stderr=io.StringIO()) in modes.TOOL_ROUTES:
            return None
    except Exception as exc:  # noqa: BLE001 - advisory: the dispatcher command stands
        note_swallowed("status: user speller route", exc)
        return None
    brief = next_phase.brief_view(plan_arg, plan_path)

    def spell(
        mode: str, extra: Sequence[str], tokens: Sequence[str],
        route: Optional[str] = None,
    ) -> Optional[str]:
        resolved = modes.resolve(mode)
        if resolved is None:
            return None
        view = next_phase.spelled_view(resolved.name, brief)
        if view is not None:
            # Imported here to keep run_status, which loads this module, light.
            from .commit_spelling import strip_fronted_flags

            tokens = strip_fronted_flags(tokens)
        try:
            chosen = next_phase.resolve_route(
                host, stderr=io.StringIO(), recorded=route)
            template = host_capabilities.next_command_template(host, chosen)
            # A tool route composes the reserved set the servers refuse in
            # a call's flags (`cli_common._HOST_COMPOSED`); a file route its
            # skill's or shim's own.
            composed = (
                cli_common._HOST_COMPOSED if chosen in modes.TOOL_ROUTES
                else cli_common.file_route_composed_flags(host)
            )
        except Exception as exc:  # noqa: BLE001 - advisory: the dispatcher command stands
            note_swallowed("status: user speller template", exc)
            return None
        # What the run's own host composed too, when another host reads it
        # (its `--host` is in the replay): never something the user typed.
        table = dict(composed)
        run_host = cli_common.replay_host(tokens)
        if run_host and run_host != host:
            try:
                table.update(cli_common.file_route_composed_flags(run_host))
            except host_capabilities.UnknownHost:  # an unknown id adds nothing
                pass
            except Exception as exc:  # noqa: BLE001 - advisory: the table stands
                note_swallowed("status: user speller run host flags", exc)
        kept = [str(token) for token in [
            *extra, *cli_common.drop_host_composed_flags(tokens, table)]]
        # A token this one-line spelling cannot carry as it is — an `ask`
        # question with a newline or a tab, an empty value — keeps the
        # dispatcher command, which quotes it whole. Those
        # tokens were dropped, so a two-line question vanished from the
        # line and the command printed did not parse.
        if any(not token or not token.isprintable() for token in kept):
            return None
        if view is not None:
            return template.replace(
                next_phase.ARGS_SLOT,
                next_phase.commit_spelled_args(resolved.name, view, kept))
        words = [f"--{resolved.name}", next_phase.quote_plan_arg(plan_arg)]
        words += [next_phase.quote_plan_arg(token) for token in kept]
        return template.replace(next_phase.ARGS_SLOT, " ".join(words))

    spell.host = host  # type: ignore[attr-defined]
    return spell


def _retry_command(
    mode: str, plan_path: Path, *args: str, flags: Optional[Sequence[str]] = None,
) -> str:
    """``cli_common.retry_command(mode, plan_path, *args, flags=flags)``, the
    dispatcher spelling of a retry this view prints, in the commit spelling
    on a commit review: the commit mode, the pinned range (the brief path on a root
    range) and none of the flags a front door synthesises or consumes, in
    *args* or in the replayed *flags*. A plan's run, and a direct
    ``--head-ref`` run, keep the command byte for byte."""
    # Imported here to keep run_status, which loads this module, light.
    from . import next_phase

    view = next_phase.commit_view_for(mode, str(plan_path))
    if view is None:
        return cli_common.retry_command(mode, str(plan_path), *args, flags=flags)
    # Imported here to keep run_status, which loads this module, light.
    from .commit_spelling import strip_fronted_flags

    return cli_common.retry_command(
        next_phase.commit_mode_word(mode, view), view.pinned,
        *strip_fronted_flags(args),
        flags=strip_fronted_flags(flags) if flags is not None else None,
    )


def _run_route(view: Mapping[str, Any], host: Optional[str]) -> Optional[str]:
    """The route *view*'s run recorded (``run.route``) when
    that run is *host*'s, else ``None``: another host's route says nothing
    of how this host's user types a command."""
    run = view.get("run") if isinstance(view.get("run"), Mapping) else {}
    route = run.get("route")
    if not isinstance(route, str) or not host or run.get("host") != host:
        return None
    return route


def _view_speller(spell: Optional[Speller], view: Mapping[str, Any]) -> Optional[Speller]:
    """*spell* for one run view: its commands in the route that run was
    started on (:func:`_run_route`), else *spell* as it is."""
    route = _run_route(view, getattr(spell, "host", None)) if spell else None
    if route is None:
        return spell

    return functools.partial(spell, route=route)


def _resume_command(
    view: Dict[str, Any], plan_path: Path, spell: Optional[Speller] = None,
    extra: Sequence[str] = (),
) -> str:
    """The ``resume with:`` command, with the run's own flags spliced back in.

    Flags come from the run record's ``replay_flags`` (the launcher's list,
    D2) through :func:`cli_common.current_replay_flags`, whose live-source rule
    never lets ``status``'s own ``--view run`` argv win here (a different
    mode). ``ask`` re-derives its question positional from the checkpoint's
    ``question`` field — the one place it is stored — and falls back to the
    questionless string when the key is missing. With *spell*
    (:func:`user_speller`) the same retry in the host's spelling.

    A review-then-apply composite (``improve-plan``, ``improve-code``) takes
    its tokens from its own continuation instead (:func:`_composite_resume_tokens`): the
    selectors its launcher
    typed, never ``--force``, then ``--resume``. A run launched with ``--force``
    is then not told to start another round, and the line names the command
    ``util next-command --blocked <composite>`` names when no inner phase has a
    resume of its own.
    """
    run = view["run"]
    mode = str(run.get("mode") or view.get("phase") or "review-plan")
    positionals = [str(plan_path)]
    row = cli_common._modes().resolve(mode)
    if row is not None and row.is_composite and not row.runs_workflow:
        flags: List[str] = []
        verbs = _composite_resume_tokens(row.name, run.get("replay_flags"))
    else:
        flags = cli_common.current_replay_flags(run.get("replay_flags"), mode=mode)
        if mode == "ask" and view.get("question"):
            positionals.append(str(view["question"]))
        verb = _RESUME_VERB_BY_MODE.get(mode) or (
            "--reaggregate" if mode in _REAGGREGATE_MODES else "--force"
        )
        # *extra*: the answers the resume carries (a manual task
        # every code task left waits on, `StopAccount.manual_gate_answers`).
        verbs = [verb, *[str(token) for token in extra]]
    if spell is not None:
        _positionals, tokens = cli_common.retry_tokens(*positionals, *verbs, flags=flags)
        spelled = spell(mode, positionals[1:], tokens)
        if spelled:
            return spelled
    # On a commit review the commit spelling.
    return _retry_command(mode, plan_path, *positionals[1:], *verbs, flags=flags)


def _composite_resume_tokens(mode: str, replay_flags: Any) -> List[str]:
    """A composite run's ``resume with:`` tokens after the plan.

    ``improve_workflow.recorded_continuation`` of the run record's own
    ``replay_flags``, the list ``util next-command --blocked`` reads, so the
    two name one command. A list that is not a list reads as no record
    (``--resume`` alone). Flags the composite's parser rejects (a record from
    an older parser, or one a batch rewrote) cost one stderr line and fall
    back to ``--resume`` alone: replayed as recorded they would not parse
    either, and their ``--force`` would start another round. ``--blocked``
    refuses the same record (exit 3), since it hands its command back as a
    tool call.

    On a composite whose positional is a range (``improve-commits``) the
    tokens never carry a flag its front door synthesises or consumes
    (``--plan-file``, ``--base-ref``, ``--head-ref``, ``--focus``,
    ``--context-plan``): the front door refuses
    the first three, and the brief inherits the rest.
    """
    # Imported here to keep run_status, which loads this module, light.
    from . import improve_workflow

    recorded = replay_flags if isinstance(replay_flags, list) else None
    try:
        tokens = improve_workflow.recorded_continuation(mode, recorded)
        row = cli_common._modes().resolve(mode)
        if row is not None and cli_common._modes().POS_REVS in tuple(row.positionals):
            # Imported here to keep run_status, which loads this module, light.
            from .commit_spelling import strip_fronted_flags

            tokens = strip_fronted_flags(tokens)
        return tokens
    except improve_workflow.ContinuationError as exc:
        detail = " ".join(str(exc).split())
        print(
            f"multi-llm: {mode}'s run recorded flags its parser rejects "
            f"({detail}); resume with: names --resume alone",
            file=sys.stderr,
        )
        return [_RESUME_VERB_BY_MODE.get(mode, "--resume")]


def _manual_gate_answers(
    mode: str, plan_path: Path, workflow: Optional[Dict[str, Any]],
) -> List[str]:
    """``--human-task <id>=done …`` an implement's resume carries while every
    code task it left waits on a manual task the user can do now
    (``next_phase._resume_flags``), else ``[]``."""
    if mode != _IMPLEMENT_PHASE:
        return []
    try:
        if workflow is None:
            workflow = status_views._workflow_payload(plan_path)
        # Imported here to keep run_status, which loads this module, light.
        from . import next_phase

        return next_phase._resume_flags(workflow.get("phases") or {}, _IMPLEMENT_PHASE)[1:]
    except Exception as exc:  # noqa: BLE001 - advisory: the plain resume stands
        note_swallowed("status: manual gate answers", exc)
        return []


def _stale_review_of(phase_name: str, workflow: Dict[str, Any]) -> Optional[str]:
    """The phase name of *phase_name*'s prerequisite review when it is stale too."""
    # Imported here to keep run_status, which loads this module, light.
    import check_workflow_prerequisites as prereq  # type: ignore
    for review in prereq.PHASE_PREREQUISITES.get(phase_name, ()):
        if ((workflow.get("phases") or {}).get(review) or {}).get("stale"):
            return review
    return None


def _rerun_command(
    view: Dict[str, Any], plan_path: Path, *, mode: Optional[str] = None,
    spell: Optional[Speller] = None,
) -> str:
    """The plain re-run of a done run whose phase went stale: no verb at all.

    :func:`_resume_command`'s sibling for the stale case. A
    ``--reaggregate`` re-stamps the stale completion from the artifacts the
    old run left, and ``--force`` is the apply parsers' ``--yes`` alias; the
    plain command is what each phase answers with on a stale record
    (``code_review_orchestrator`` takes its ``--force`` path itself). The run's
    own ``replay_flags`` ride along, as on every retry line — unless *mode*
    names another phase (its stale review), whose run this view has no flags
    for.
    """
    run = view["run"]
    if mode is not None:
        resolved = cli_common._modes().resolve(mode)
        word = resolved.name if resolved is not None else mode
        flags: List[str] = []
    else:
        word = str(run.get("mode") or view.get("phase") or "review-code")
        flags = cli_common.current_replay_flags(run.get("replay_flags"), mode=word)
    if spell is not None:
        # In the host's spelling, as `resume with:` is.
        spelled = spell(word, [], cli_common.retry_tokens(str(plan_path), flags=flags)[1])
        if spelled:
            return spelled
    return _retry_command(word, plan_path, flags=flags)


def _resume_shape(view: Dict[str, Any]) -> "tuple":
    """``(shape, repair, redispatch, kept)`` from the document, in two reads.

    1. the run record's close-out — D4's ``{"state": "runner_rejected",
       "reason_code": …}``, written at the checkpoint's top level and mirrored
       into the view — is the refusal's classification made durable and, after
       a refusal, the only thing on disk ⇒ shape 1. ``claim_run`` retires the
       whole close-out (``status_file.REFUSAL_KEYS``), so one beside a run
       record is that run's;
    2. otherwise ``progress.subagents`` (``_mirror_status``), whose ``counts``
       split by ``FATAL_STATUSES`` ⇒ shape 1 or 2. Its freshness is the
       writer's property: ``claim_run`` drops the predecessor's ``run`` **and**
       ``progress`` together, so a mirror beside a run record is that run's.
    3. neither ⇒ shape 2, the transient default.

    Never ``subagent_batch_report.json``: the report in the phase dir may be
    the previous run's, and it is an arbitrarily large read on a command that
    must stay sub-second.
    """
    run = view["run"]
    reason_code = None
    if run.get("state") == "runner_rejected" or view.get("state") == "runner_rejected":
        reason_code = run.get("reason_code") or view.get("reason_code") or "runner_rejected"
    progress = view.get("progress") or {}
    mirror = progress.get("subagents") or {}
    if not mirror and isinstance(progress.get("write_subagents"), dict):
        # A write phase mirrors per-batch outcomes instead of a counts table
        # (`write_reports.WriteReports.mirror_status`); its shape is the transient
        # default and its cost line counts batches.
        mirror = _write_mirror_as_counts(progress["write_subagents"])
    counts = mirror.get("counts") if isinstance(mirror.get("counts"), dict) else {}
    shape = cli_common.retry_shape(reason_code=reason_code, statuses=counts.keys())
    repair = None
    if shape == cli_common.SHAPE_REPAIR:
        repair = cli_common.repair_sentence(
            reason_code=reason_code, explanation=_reason_explanation(reason_code),
            counts=counts,
        )
    redispatch = len(mirror.get("failed_task_ids") or []) or None
    kept = mirror.get("ok") if isinstance(mirror.get("ok"), int) else None
    return shape, repair, redispatch, kept


def _write_mirror_as_counts(mirror: Dict[str, Any]) -> Dict[str, Any]:
    """``progress.write_subagents`` in the shape ``_resume_shape`` reads.

    ``ok`` counts every batch the mirror records as ``ok`` — the ones this run
    applied and the ones a resume skipped because their result file was already
    on disk — and ``failed_task_ids`` is the rows' (``task_ledger.mirror_ids``).
    """
    tasks = mirror.get("tasks") if isinstance(mirror.get("tasks"), list) else []
    counts: Dict[str, int] = {}
    for row in tasks:
        status = str((row or {}).get("status") or "")
        if status:
            counts[status] = counts.get(status, 0) + 1
    return {
        "counts": counts,
        "ok": counts.get("ok", 0),
        "failed_task_ids": list(mirror_ids(mirror, "failed_task_ids") or []),
    }


def _stop_resume_why(view: Dict[str, Any]) -> Optional[str]:
    """The write run's stop's ``resume_why``, from its mirror,
    under ``next_phase.stop_resume_why_on_record``'s rule: one plain line of
    a sane length, since a jailed batch can write the folder it lives in."""
    # Imported here to keep run_status, which loads this module, light.
    from .next_phase import recorded_why

    progress = view.get("progress") or {}
    mirror = progress.get("write_subagents") if isinstance(progress, dict) else None
    stop = mirror.get("stop") if isinstance(mirror, dict) else None
    return recorded_why(stop.get("resume_why") if isinstance(stop, dict) else None)


def _failed_batches_moved_nothing(view: Dict[str, Any]) -> bool:
    """Whether every failed row of a write run's mirror records that no file
    moved (``files_touched`` present and empty). A row without the key — an
    older mirror — says nothing, so the answer is ``False`` and the status
    line keeps its "half-applied" wording.

    ``files_touched`` is the rollback set, so a row also has to name no
    ``unrestorable`` file (moved, with no rollback point) and must not be a
    partial application, which moved bytes by definition."""
    progress = view.get("progress") or {}
    mirror = progress.get("write_subagents") if isinstance(progress, dict) else None
    if not isinstance(mirror, dict):
        return False
    failed_ids = set(mirror_ids(mirror, "failed_task_ids") or [])
    rows = [
        row for row in (mirror.get("tasks") or [])
        if isinstance(row, dict) and row.get("task_id") in failed_ids
    ]
    if not rows:
        return False
    return all(
        isinstance(row.get("files_touched"), list) and not row["files_touched"]
        and not row.get("unrestorable")
        and row.get("write_outcome") != "partial-application"
        for row in rows
    )


def _reason_explanation(reason_code: Optional[str]) -> Optional[str]:
    """``_REASON_EXPLANATION[reason_code]``, imported only on this failed path."""
    if not reason_code:
        return None
    try:
        # Imported here to keep run_status, which loads this module, light.
        from .runner_selection import _REASON_EXPLANATION
    except Exception as exc:  # pragma: no cover - a broken install still prints the code
        note_swallowed("status: reason explanation import", exc)
        return None
    return _REASON_EXPLANATION.get(reason_code)


#: What a write run refused before its first batch gets in place of a
#: ``resume with:`` command (racing re-run 2026-10-04, codex #5: implement
#: refused on the jail before batch 1 offered ``--resume``, which repeats the
#: refusal). No command: the way forward is the remedy the refusal names.
NO_RESUME_BEFORE_DISPATCH = (
    "no resume: nothing was dispatched and the phase has no progress on record, "
    "so a resume would only repeat this stop; fix what the error above names "
    "first, then run the phase again"
)


def _dispatched_nothing(view: Dict[str, Any]) -> bool:
    """A write run whose own mirror records no dispatched and no ``ok`` batch.

    ``progress.write_subagents.batches_dispatched`` is appended per dispatched
    batch (``write_batch_scheduler``), and ``claim_run`` drops a predecessor's
    ``progress`` with its ``run``, so an empty list beside this run record
    means this run sent nothing. A mirror without the key says nothing.
    """
    progress = view.get("progress") or {}
    mirror = progress.get("write_subagents") if isinstance(progress, dict) else None
    if not isinstance(mirror, dict):
        return False
    dispatched = mirror.get("batches_dispatched")
    if not isinstance(dispatched, list) or dispatched:
        return False
    rows = mirror.get("tasks") if isinstance(mirror.get("tasks"), list) else []
    return not any((row or {}).get("status") == "ok" for row in rows)


def _phase_in_progress(
    view: Dict[str, Any], plan_path: Path, workflow: Optional[Dict[str, Any]],
) -> bool:
    """Whether the workflow view shows *view*'s phase ``in_progress``.

    Read from *workflow* when the caller has it, else from ``state.json`` once
    (this is the failure path only). A read that fails answers ``True``, which
    keeps the ``resume with:`` line this predicate would otherwise remove.
    """
    if workflow is None:
        try:
            workflow = status_views._workflow_payload(plan_path)
        except Exception as exc:  # noqa: BLE001 - advisory: keep the old line
            note_swallowed("status: phase in progress", exc)
            return True
    phase = view.get("phase") or cli_common._modes().phase_for(
        str((view.get("run") or {}).get("mode") or ""))
    entry = (workflow.get("phases") or {}).get(phase) or {}
    return entry.get("status") == "in_progress"


def _resume_lines(
    view: Dict[str, Any], plan_path: Path,
    workflow: Optional[Dict[str, Any]] = None,
    spell: Optional[Speller] = None,
) -> List[str]:
    """The shaped resume block: the repair first when there is one, then the
    single ``resume with:`` command, then what it costs.

    A write run that dispatched nothing, under a phase with no progress on
    record, gets :data:`NO_RESUME_BEFORE_DISPATCH` instead: its ``--resume``
    would repeat the refusal, and a tool route scrapes every command printed
    here into an option.
    """
    mode = str(view["run"].get("mode") or view.get("phase") or "")
    if (
        mode in _WRITE_MODES and _dispatched_nothing(view)
        and not _phase_in_progress(view, plan_path, workflow)
    ):
        return [f"      {NO_RESUME_BEFORE_DISPATCH}"]
    shape, repair, redispatch, kept = _resume_shape(view)
    if mode == _IMPLEMENT_PHASE and redispatch:
        # The mirror holds only this run's rows, so a resume
        # that kept T001/T003/T004 from an earlier run (and T002's findings)
        # read "keeps the 1 already applied". state.json counts every task
        # of the decomposition on record as done.
        done = _implement_tasks_done(plan_path, workflow)
        if done is not None and done > (kept or 0):
            kept = done
    lines: List[str] = []
    if shape == cli_common.SHAPE_REPAIR:
        lines.append(f"      repair first: {repair}")
    resume = _resume_command(
        view, plan_path, spell, extra=_manual_gate_answers(mode, plan_path, workflow))
    lines.append(f"      resume with: {resume}")
    # A write run's stop says what its plain
    # resume does on an unchanged tree; that replaces the cost line, which
    # read "re-dispatches the 1 failed batch(es)" of a task the write policy
    # refuses again.
    # Printed as recorded,
    # which ends with what the resume keeps and whether a failed batch is
    # half-applied, so it reads word for word as the tool routes'
    # `resume_why` and `util next-command --blocked` relay it.
    why = _stop_resume_why(view) if mode in _WRITE_MODES else None
    if why:
        # Under the command, unbracketed (`why_line`).
        lines.append(why_line(why))
    elif redispatch:
        mode = str(view["run"].get("mode") or view.get("phase") or "")
        if mode in _WRITE_MODES:
            # The write loop stops at the failed batch, so what a resume
            # re-dispatches is that batch and everything after it; the kept
            # count is the batches whose result files it skips over.
            cost = f"re-dispatches the {redispatch} failed batch(es) and the ones never reached"
            if kept:
                cost += f", keeps the {kept} already applied"
            if _failed_batches_moved_nothing(view):
                # A task refused before
                # dispatch, a clean failure, a timeout that wrote nothing —
                # no byte moved, so nothing is half-applied. The stop's own block says
                # so, and this view
                # shows its last lines, so the line no longer says it again.
                lines.append(f"      ({cost})")
            else:
                lines.append(
                    f"      ({cost}; the half-applied state is left in place — inspect "
                    f"it, or `util restore-batch` the failed batch, before resuming)"
                )
        else:
            cost = f"re-dispatches the {redispatch} failed task(s)"
            if kept is not None:
                cost += f" and keeps the {kept} valid result(s) already on disk"
            lines.append(f"      ({cost}; --force is not needed and would re-run the reviewer panel)")
    return lines


def _implement_tasks_done(
    plan_path: Path, workflow: Optional[Dict[str, Any]],
) -> Optional[int]:
    """``phases.implement.tasks_done`` from the workflow view, read once if
    the caller has none; ``None`` when it is not on record or unreadable."""
    if workflow is None:
        try:
            workflow = status_views._workflow_payload(plan_path)
        except Exception as exc:  # noqa: BLE001 - advisory: the mirror count stands
            note_swallowed("status: implement tasks done", exc)
            return None
    done = ((workflow.get("phases") or {}).get(_IMPLEMENT_PHASE) or {}).get("tasks_done")
    return done if isinstance(done, int) and not isinstance(done, bool) else None


def _abort_command(plan_path: Path, view: Dict[str, Any]) -> str:
    """The one selector-carrying ``--abort`` spelling for a single listed run."""
    run_id = str(view["run"].get("run_id") or "")
    if run_id:
        return detach.abort_command_for(str(plan_path), run_id=run_id)
    phase = view.get("phase") or os.path.basename(view["phase_dir"])
    return dispatcher_command("status", str(plan_path), "--abort", "--phase", str(phase))


def _run_runner_facts(
    views: Sequence[Dict[str, Any]]
) -> "tuple":
    """``(host, specs, source)`` the listed runs recorded about their own
    subagents.

    The host is the first one any listed run wrote into ``.status.json``
    (``RunHandle`` records the launcher's ``--host``); the specs are the runner
    keys that same run's executor mirror pinned, i.e. what its dispatches
    actually ran on rather than what a fresh resolution would pick now. Checked
    under both mirror keys — ``subagents`` (the read path) and
    ``write_subagents`` (`write_reports.WriteReports.mirror_status`, F7) — a write
    phase carries only the second, and until it recorded a runner at all
    `status` polled outside the launching session fell through to a fresh
    resolution and named the *polling* host's model instead of the run's.

    **A host-bearing view that recorded no spec must not win outright**: with several
    phases listed, the first one carrying a host can
    be a run whose executor mirror is empty (a failed-before-dispatch run, a
    stale pre-fix record, ``--dry-run-subagents``) while a *later* view holds
    the real answer. Measured on a `generate-tasks` run: the default view's
    ``apply-suggestions`` row sorted first, its mirror had recorded nothing,
    and the search stopped there instead of reaching the `generate-tasks` row
    one below it that had. So an empty-spec view is skipped rather than
    returned, and its host is kept only as the fallback for when no view in
    the whole list ever recorded a spec.

    **Among the views that DID record a spec, the most recently updated one
    wins — not whichever sorts first**: ``discover_phase_dirs``
    lists phases in alphabetical directory order, so a `generate-tasks` run's
    pre-`--variant low` record outranked `review-tasks`' own `:low` record
    directly below it, under a line that claimed to be "recorded by this run's
    own dispatches". Every view carries ``updated_at``, so the candidates are
    collected first and the freshest one answers. ``source`` names which run
    the winning spec came from — ``None`` when only one view ever recorded a
    spec, so the caller's existing "this run's own dispatches" wording stays
    exactly as specific as it always was; a phase name, when more than one
    view recorded one, so the line stops asserting an ownership it cannot back.
    """
    fallback_host: Optional[str] = None
    candidates: List[Dict[str, Any]] = []
    for view in views or ():
        run = view.get("run") or {}
        host = run.get("host")
        if not isinstance(host, str) or not host.strip():
            continue
        progress = view.get("progress") or {}
        mirror = progress.get("subagents")
        versions = mirror.get("runner_versions") if isinstance(mirror, dict) else None
        if not isinstance(versions, dict) or not versions:
            mirror = progress.get("write_subagents")
            versions = mirror.get("runner_versions") if isinstance(mirror, dict) else None
        specs = sorted(str(spec) for spec in versions) if isinstance(versions, dict) else []
        if specs:
            name = view.get("phase") or os.path.basename(str(view.get("phase_dir") or "")) or None
            candidates.append({
                "host": host.strip(),
                "specs": specs,
                "name": name,
                "updated_at": str(view.get("updated_at") or ""),
            })
            continue
        if fallback_host is None:
            fallback_host = host.strip()
    if candidates:
        candidates.sort(key=lambda c: c["updated_at"])
        winner = candidates[-1]
        source = winner["name"] if len(candidates) > 1 else None
        return winner["host"], winner["specs"], source
    return fallback_host, [], None


def render_runner_text(
    plan_path: Path,
    host_id: Optional[str] = None,
    *,
    views: Sequence[Dict[str, Any]] = (),
) -> List[str]:
    """The resolved subagent runner, its layer of origin, and who consults it (D3o).

    **The run's host wins over the invoking one.** A poll is routinely typed
    from a different host than the one that launched the run — measured
    2026-09-16, three ``status`` calls on an ``opencode`` run whose eleven
    batches all dispatched to ``opencode:openrouter/…`` each printed
    ``claude-code:sonnet``, because the host came from *this* invocation's argv
    while the run's own sat unread in ``.status.json``. So the run's host is
    what this reports, and with it:

    * the specs the run's executor mirror recorded, when it has dispatched
      anything — the only account on disk of what its subagents really ran on,
      and, when more than one listed view recorded one, the most recently
      updated view's, named in the printed line rather than
      claimed as "this run's own";
    * otherwise a fresh resolution for that host, with the **session** rung
      skipped whenever the run was launched elsewhere: that rung reads
      ``MULTI_LLM_HOST_SESSION_MODEL`` off *this* process, which is the polling
      session's model and not the run's. The plugin's own poll passes
      ``--host opencode`` from inside the session that launched the run, so
      there the rung still applies and still answers ``(supplied by session)``.

    "I set ``driver.subagent_runner`` and nothing changed" has three different
    answers — a higher layer won, no layer expressed an opinion so the running
    host's own ``default_subagent_runner`` answered, or this host dispatches
    subagents natively and never consults the key outside ``--exec-subagents`` —
    and a merged value printed on its own distinguishes none of them. So the
    layer is printed with the value, resolved through the *same*
    ``resolve_subagent_runner`` a dispatch takes rather than re-derived here.

    It is reported, never resolved: ``status`` writes nothing, takes no lock and
    must stay sub-second, so a config layer that cannot be read (a ``ConfigError``
    from a broken override, an unknown ``--host``, a partial install) prints
    nothing at all rather than failing a poll. Text only — the ``--json`` views
    stay exactly two keys, ``workflow`` and ``runs``, because this is a config
    fact and blending it into either state view is what ``--view`` exists to
    prevent.
    """
    try:
        # Imported here to keep run_status, which loads this module, light.
        from .provider_registry import resolve_subagent_runner

        invoking_host = host_capabilities.resolve_host_id(sys.argv[1:], explicit=host_id)
        run_host, recorded, recorded_by = _run_runner_facts(views)
        resolved_host = run_host or invoking_host
        if recorded:
            spec = ", ".join(recorded)
            source = (
                f"recorded by {recorded_by}'s own dispatches" if recorded_by
                else "recorded by this run's own dispatches"
            )
        else:
            spec, layer = resolve_subagent_runner(
                "full", anchor=str(plan_path), host_id=resolved_host,
                skip_session=resolved_host != invoking_host,
            )
            source = f"supplied by {layer}"
        native = str(host_capabilities.entry(resolved_host).get("subagents")) == "native"
    except host_capabilities.UnknownHost:  # an unknown host prints nothing (above)
        return []
    except Exception as exc:  # noqa: BLE001 - reported, never resolved (above)
        note_swallowed("status: runner text", exc)
        return []
    scope = (
        f"{resolved_host} dispatches subagents natively, so it is consulted "
        "only under --exec-subagents"
        if native
        else f"every subagent {resolved_host} dispatches runs through it"
    )
    return [
        "driver.subagent_runner — what a dispatched subagent would run:",
        f"  {spec}  ({source})",
        f"  {scope}",
    ]
