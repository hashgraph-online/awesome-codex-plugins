"""What a stopped write phase offers the user: its answers, the resume's
why, and a headline that fits.

The executor's stop and the native leg's (``util next-command --blocked``,
``status``) compose the same answers (:func:`compose_stop_answers`,
:func:`native_stop_answers`) and the same why (:func:`compose_resume_why`,
:func:`native_resume_why`), each from the facts its leg holds, so the two
legs cannot word a stop differently.

``utils.write_batch_scheduler`` re-exports every name defined here for
reading only: patch one here, never through the scheduler
(docs/development/write-scheduler.md#where-the-schedulers-helpers-live).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Collection, Dict, List, Mapping, Optional, Sequence, Union

from . import check_records as _check_records
from .task_ledger import ACCEPTED_AFTER_FAILING_LABEL, ACCEPTED_WITH_FINDINGS_LABEL
from .text_clip import clip, without_closing_mark
from .batch_reply import row_check_findings
from .write_verdict import findings_clause
from .cli_common import ERROR_MAX_CHARS, plain_line
from .manual_tasks import MAX_RECORDED_WHY_CHARS
from .subagent_tasks import implement_output_name
from .state_manager import TASK_CHECK_TREES_KEY


#: The stop record's key for its headline without the ways forward a resume
#: section carries, which ``util next-command
#: --blocked`` hands the tool routes beside that section.
HEADLINE_BESIDE_SECTION_KEY = "headline_beside_section"

#: A ``--human-task`` answer a stop headline names: ``T005=skip``,
#: ``apply-batch-0=skip``, or the generic ``<check id>=done``.
_HEADLINE_ANSWER = re.compile(r"--human-task (<check id>|[A-Za-z0-9][\w.-]*)=(done|skip|retry)")


def answers_cover(full: str, beside: str, stop: Mapping[str, Any]) -> bool:
    """Whether every ``--human-task`` answer *full* names and *beside* leaves
    out is one of *stop*'s own ``answers`` — the ones its resume section
    lists as commands — or of its ``resume_flags``, the resume the section leads
    with when that resume carries answers itself (a manual-task gate's
    ``--resume --human-task T010=done``). The generic ``<check id>=done`` stands
    for ``=done`` on each of the stop's ``check_task_ids``."""
    wanted = set()
    left_out = set(_HEADLINE_ANSWER.findall(full)) - set(_HEADLINE_ANSWER.findall(beside))
    for task_id, word in left_out:
        if task_id == "<check id>":
            checks = [str(check) for check in stop.get("check_task_ids") or []]
            if not checks:
                return False
            wanted.update((check, word) for check in checks)
        else:
            wanted.add((task_id, word))
    offered = set()
    for entry in list(stop.get("answers") or []) + [
            {"flags": stop.get("resume_flags")}]:
        flags = entry.get("flags") if isinstance(entry, Mapping) else None
        if not isinstance(flags, list):
            continue
        for name, value in zip(flags, flags[1:]):
            if name == "--human-task" and isinstance(value, str) and "=" in value:
                offered.add(tuple(value.rsplit("=", 1)))
    return wanted <= offered


#: The task-title lengths a stop headline tries, in order, once the model's
#: quoted words and the not-run list no longer make it fit
#: (:meth:`WriteBatchScheduler._stop_headline`; ``0`` leaves the title out).
STOP_HEADLINE_LABEL_CAPS = (80, 40, 0)

#: The shortest cut of the model's quoted words worth keeping; below it the
#: quote is left out of the headline (it stays whole in the stop message,
#: summary.md and the report).
STOP_HEADLINE_QUOTE_MIN = 40


def fit_stop_headline(
    head: str,
    reported: Optional[str],
    not_run: Sequence[str],
    body: Sequence[str],
    terminator: str = ".",
    *,
    tail: Optional[str] = None,
    budget: Optional[int] = None,
    last_resort: bool = True,
) -> Optional[str]:
    """A stop headline within *budget* (default ``cli_common.ERROR_MAX_CHARS``),
    as one :func:`~utils.cli_common.plain_line`.

    ``head [reported]<terminator> Not run: … <body…> <tail>``. What gives way,
    in order: *reported* (the model's own words: cut with ``…``, or left out
    below :data:`STOP_HEADLINE_QUOTE_MIN`), then the not-run list (``Not run:
    T003, T004 and 9 more.``, then left out: the summary lists every one).
    *body* (the remedy and the answers) and *tail* (the tests line) stay
    whole. ``None`` when that is not enough and
    *last_resort* is false: the caller tries again with shorter task titles.
    Under *last_resort* the head is cut, and when even the bare remedy, the
    answers and the tests line do not fit, everything before *tail* is.
    """
    limit = ERROR_MAX_CHARS if budget is None else int(budget)
    head = plain_line(head)
    quote = plain_line(reported) if reported else ""
    ids = [plain_line(i) for i in not_run if plain_line(i)]
    pieces = [plain_line(piece) for piece in body if plain_line(piece)]
    end = f" {plain_line(tail)}" if tail and plain_line(tail) else ""

    def listed(shown: Optional[int] = None) -> str:
        if not ids:
            return ""
        if shown is None or shown >= len(ids):
            return f"Not run: {', '.join(ids)}."
        if shown <= 0:
            return ""
        return f"Not run: {', '.join(ids[:shown])} and {len(ids) - shown} more."

    def core(lead: str, said: str, nr: str) -> str:
        text = lead + (f" [{said}]" if said else "") + terminator
        return " ".join([text, *([nr] if nr else []), *pieces])

    nr = listed()
    text = core(head, quote, nr)
    if len(text) + len(end) <= limit:
        return text + end
    if quote:
        room = limit - len(end) - len(core(head, "", nr)) - len(" […]")
        quote = clip(quote, room + 1) if room >= STOP_HEADLINE_QUOTE_MIN else ""
        text = core(head, quote, nr)
        if len(text) + len(end) <= limit:
            return text + end
    for shown in range(len(ids) - 1, -1, -1):
        nr = listed(shown)
        text = core(head, "", nr)
        if len(text) + len(end) <= limit:
            return text + end
    if not last_resort:
        return None
    room = limit - len(end) - len(core("", "", nr))
    if room >= 2:
        return core(clip(head, room), "", nr) + end
    text = core(head, "", nr)
    return clip(text, max(limit - len(end), 0)) + end


#: How the resume's why ends when a failed batch moved bytes
#: (:func:`compose_resume_why`; ``status``'s own words).
HALF_APPLIED_LEFT_CLAUSE = (
    "the half-applied state is left in place — inspect it, or "
    "`util restore-batch` the failed batch, before resuming"
)


def implement_tasks_done(state: Any) -> int:
    """How many tasks of the decomposition implement ran last
    (``implement_task_ids``, else every ``T###`` id) ``state.json`` records
    ``completed``: the workflow view's ``tasks_done``, which ``status``
    counted as a resume's kept tasks. ``0`` when it cannot be read."""
    if state is None or not hasattr(state, "get"):
        return 0
    try:
        statuses = dict(state.get("task_status") or {})
        current = state.get("implement_task_ids")
    except Exception:  # noqa: BLE001 - an advisory count
        return 0
    if isinstance(current, list) and current:
        return sum(1 for task_id in current if statuses.get(str(task_id)) == "completed")
    return sum(
        1 for task_id, status in statuses.items()
        if _check_records._IMPLEMENT_TASK_ID.match(str(task_id)) and status == "completed"
    )


@dataclass(frozen=True)
class FailedAnswerable:
    """A failed implement task a stop's ``--human-task`` answers can answer
    (:func:`compose_stop_answers`): ``unlanded`` when its reply said applied
    and nothing it declares changed, ``not_rerun`` when a
    resume kept a failed check from running again on unchanged files."""

    task_id: str
    unlanded: bool = False
    not_rerun: bool = False
    #: A check task (it declares no file) whose failure a resume does not run
    #: again while the files are unchanged (the executor's
    #: ``CheckHolds.unchanged_since_failure``, :func:`compose_resume_why`):
    #: only one whose verdict carries the tree it failed on, or one the run
    #: already kept.
    check: bool = False


def compose_resume_why(
    *,
    refused: Sequence[str],
    policy: Collection[str] = (),
    outside: Collection[str] = (),
    failed: Sequence[FailedAnswerable] = (),
    checks: Sequence[str] = (),
    rerun_checks: Collection[str] = (),
    blocked: Mapping[str, str] = {},
    undone_with: Callable[[str], List[str]] = lambda _task_id: [],
    unit: str = "tasks",
    kept: int = 0,
    half_applied: bool = False,
) -> Optional[str]:
    """What the plain ``--resume`` of a stopped write phase does on an
    unchanged tree, from the stop's own facts, or ``None`` when nothing
    waits.

    Live run 9 (the stop-path fixture): every surface gave each
    ``--human-task`` answer its why and the plain resume none, and the hosts
    invented one — "(re-runs the T002 check)", false on unchanged files, or
    "To resume after addressing the write policy:". One clause per task the
    resume does not simply run: each check of *checks* whose findings hold
    tasks back (*blocked*) is not run again while the files are unchanged,
    unless *rerun_checks* names it (no record of the tree it ran on, so a
    resume runs it again); a *failed* check task the resume
    keeps (``FailedAnswerable.check``) neither, and any other failed task is
    dispatched again; a task *refused* before dispatch stays refused until
    ``driver.write_paths`` changes when *policy* names it — or for good when
    *outside* does too, since no rule can allow a file outside the
    repository — else is checked again before it is dispatched.
    *undone_with* names the tasks waiting on a
    task that does not run. Both legs compose it from the facts they answer
    the stop from (the executor's ``StopAccount.stop_resume_why``,
    :func:`native_resume_why`), and it is cut at a word to
    ``next_phase.MAX_RECORDED_WHY_CHARS``.

    It ends with what the resume keeps — *kept* tasks or batches already
    done, and, with *half_applied*, that a failed batch's edits are left in
    place — so every surface that relays the why says it in the same words:
    ``status`` used to append those clauses itself, and the tool routes'
    ``resume_why`` and ``util next-command --blocked`` did not. The cut takes the facts before them,
    never them.
    """

    def waits(ids: Sequence[str]) -> str:
        if not ids:
            return ""
        return f" ({', '.join(ids)} {'waits' if len(ids) == 1 else 'wait'} on it)"

    unchanged = "is not run again while the files are unchanged"
    parts: List[str] = []
    for check_id in checks:
        waiting = sorted(t for t, c in blocked.items() if c == check_id)
        if check_id in rerun_checks:
            parts.append(f"{check_id}'s check runs again{waits(waiting)}")
        else:
            parts.append(f"{check_id}'s check {unchanged}{waits(waiting)}")
    for item in failed:
        if item.check or item.not_rerun:
            parts.append(
                f"{item.task_id}'s check {unchanged}{waits(undone_with(item.task_id))}")
        else:
            parts.append(f"{item.task_id} is dispatched again")
    for task_id in refused:
        if task_id in outside:
            parts.append(
                f"{task_id} stays refused: it declares a file outside the "
                f"repository{waits(undone_with(task_id))}")
        elif task_id in policy:
            parts.append(
                f"{task_id} stays refused until driver.write_paths changes"
                f"{waits(undone_with(task_id))}")
        else:
            parts.append(f"{task_id} is checked again before it is dispatched")
    if not parts:
        return None
    # "done", not
    # "applied" — a kept check task applied nothing, and the host told the
    # user "3 of 7 applied" from "keeps the 4 already applied".
    noun = {"tasks": "task", "batches": "batch"}.get(unit, unit) if kept == 1 else unit
    tail = f"; keeps the {kept} {noun} already done" if kept else ""
    if half_applied:
        tail += f"; {HALF_APPLIED_LEFT_CLAUSE}"
    # Within the length a route
    # reads back from the run's folder (`next_phase.recorded_why`), cut at a
    # word, so the tool routes and status carry the why the native block
    # prints instead of falling back on a large stop.
    return clip(f"runs the {unit} that can run; " + "; ".join(parts),
                MAX_RECORDED_WHY_CHARS - len(tail)) + tail


def compose_stop_answers(
    *,
    refused: Sequence[str],
    failed: Sequence[FailedAnswerable],
    checks: Sequence[str],
    blocked: Mapping[str, str],
    findings: Mapping[str, Sequence[str]],
    undone_with: Callable[[str], List[str]],
) -> List[Dict[str, Any]]:
    """A stopped implement's ``--human-task`` answers, as data, on both legs.

    ``[{"flags": ["--resume", …], "why": …}]`` in the order a user weighs
    them: the one combined command that goes on without fixing anything
    (when more than one task needs an answer), then each task's own answers
    — a task *refused* before dispatch (``skip``, ``done``), each *failed*
    one (``done``, ``skip``, ``retry`` when it was not run again; ``skip``
    then ``done`` when its change never landed) and each of *checks* whose
    findings hold tasks back (``done``, ``skip``, ``retry``). *blocked* maps
    each held task to its check, *findings* each check to what it reported,
    and *undone_with* names the tasks a ``skip`` leaves undone with a task.

    The executor's stop (:meth:`WriteBatchScheduler._stop_answers`) and the
    native leg's (:func:`native_stop_answers`) both answer
    through this, so each answer and its why read the same on every host:
    on live run 8 the native block offered only the combined command while
    the tool routes listed six, and the Claude Code host described a
    T005-only answer the plugin never printed.
    """

    def answer(task_id: str, word: str) -> List[str]:
        return ["--human-task", f"{task_id}={word}"]

    def skipped_clause(task_id: str) -> str:
        deps = undone_with(task_id)
        return f"leave {task_id} undone" + (
            f", with the tasks that depend on it ({', '.join(deps)})" if deps else ""
        )

    def made_by_hand(task_id: str) -> Dict[str, Any]:
        return {
            "flags": answer(task_id, "done"),
            "why": (f"once you have made {task_id}'s change yourself: "
                    f"{task_id} counts as done and the tasks after it run"),
        }

    each: List[Dict[str, Any]] = []
    for task_id in refused:
        each.append({"flags": answer(task_id, "skip"),
                     "why": skipped_clause(task_id)})
        each.append(made_by_hand(task_id))
    for item in failed:
        task_id = item.task_id
        if item.unlanded:
            # Its change did not land, so there is
            # no failure to accept — going on without it comes first, and
            # `done` is for a change the user made by hand, as the stop
            # message says.
            each.append({"flags": answer(task_id, "skip"),
                         "why": skipped_clause(task_id)})
            each.append(made_by_hand(task_id))
            continue
        each.append({
            "flags": answer(task_id, "done"),
            "why": (f"accept {task_id}'s failure: {task_id} counts as done "
                    "and the tasks after it run"),
        })
        each.append({"flags": answer(task_id, "skip"),
                     "why": skipped_clause(task_id)})
        if item.not_rerun:
            each.append({
                "flags": answer(task_id, "retry"),
                "why": f"run {task_id}'s check again on unchanged files",
            })
    for check_id in checks:
        waiting = sorted(t for t, c in blocked.items() if c == check_id)
        reported = list(findings.get(check_id) or [])
        # The findings
        # closed the why in brackets, "… review-code (… requires 3.)", which
        # status's own brackets made "3.))"; they follow a semicolon now,
        # without their closing stop, as no why ends in one.
        each.append({
            "flags": answer(check_id, "done"),
            "why": (f"accept {check_id}'s check findings: "
                    f"{', '.join(waiting)} then run, told that you accepted "
                    "the findings, and the findings stay listed for "
                    "review-code"
                    + (f"; {check_id} reported: "
                       f"{without_closing_mark(clip(findings_clause(reported), 200))}"
                       if reported else "")),
        })
        each.append({
            "flags": answer(check_id, "skip"),
            "why": f"leave {check_id} and {', '.join(waiting)} undone",
        })
        each.append({
            "flags": answer(check_id, "retry"),
            "why": f"run {check_id}'s check again on unchanged files",
        })
    # One command that goes on without fixing anything: every check with
    # findings accepted, every refused or failed task left undone.
    combined_flags: List[str] = []
    clauses: List[str] = []
    for check_id in checks:
        combined_flags += answer(check_id, "done")
        clauses.append(f"accept {check_id}'s check findings")
    for task_id in [*refused, *(item.task_id for item in failed)]:
        combined_flags += answer(task_id, "skip")
        clauses.append(skipped_clause(task_id))
    # Each why within the length the tool routes read back
    # from the run's folder (`next_phase.stop_answers_on_record`), cut at a
    # word, so a large stop's answers are not dropped on the way.
    rest = "; the rest runs"
    answers: List[Dict[str, Any]] = []
    if len(clauses) > 1:
        answers.append({
            "flags": ["--resume", *combined_flags],
            "why": clip(" and ".join(clauses), MAX_RECORDED_WHY_CHARS - len(rest)) + rest,
        })
    answers.extend(
        {"flags": ["--resume", *item["flags"]],
         "why": clip(item["why"], MAX_RECORDED_WHY_CHARS)}
        for item in each
    )
    return answers


#: How the native emit opens the reason it records for a task the write
#: policy refuses (``implement_orchestrator``'s ``refused`` map).
NATIVE_REFUSED_PREFIX = "refused before dispatch: "

#: How ``util batch-done --status failed --partial`` opens the reason of a
#: native task that failed after its subagent changed files:
#: the executor's partial application, which no ``--human-task`` answer is
#: offered for until the half-applied state is inspected.
HALF_APPLIED_PREFIX = "half-applied: "

#: The reason the native instructions prescribe for a reply that said
#: ``applied`` and changed no file, twice: the executor's
#: ``applied_without_changes``, answered ``skip`` first, then ``done`` for a
#: change made by hand.
UNLANDED_REASON = "said applied, no file changed"


def _native_stop_facts(state: Any) -> Optional[Dict[str, Any]]:
    """The facts a stopped native implement is answered from, read from
    ``state.json`` as recorded (:func:`native_stop_answers`,
    :func:`native_resume_why`), or ``None`` when none waits or the record
    cannot be read."""
    if state is None or not hasattr(state, "get"):
        return None
    try:
        statuses = dict(state.get("task_status") or {})
        reasons = dict(state.get("task_status_reasons") or {})
        scope = state.get("implement_task_ids")
        human = {str(t) for t in (state.get("implement_human_task_ids") or [])}
        recorded = state.get("task_check_findings") or {}
    except Exception:  # noqa: BLE001 - an advisory read, never fatal
        return None
    failed_ids = sorted(
        str(task_id) for task_id, status in statuses.items()
        if status == "failed" and _check_records._IMPLEMENT_TASK_ID.match(str(task_id))
        and (not isinstance(scope, list) or task_id in scope)
    )
    held = _check_records.held_back_by_checks([], state)
    blocked = {task_id: check_id for task_id, check_id in held}
    checks = sorted(set(blocked.values()))
    if not failed_ids and not checks:
        return None
    graph = _check_records.decomposition_graph([], state)
    manual = human | {
        str(node.get("task_id", "")) for node in graph
        if node.get("executor_role") == "human" or node.get("is_human")
    }

    def undone_with(task_id: str) -> List[str]:
        return [
            dep for dep in _check_records.transitive_dependents(graph, task_id)
            if dep not in manual
            and statuses.get(dep) not in ("completed", "skipped")
            and (not isinstance(scope, list) or dep in scope)
        ]

    def reason(task_id: str) -> str:
        return str(reasons.get(task_id) or "")

    refused = [
        task_id for task_id in failed_ids
        if reason(task_id).startswith(NATIVE_REFUSED_PREFIX)
    ]
    return {
        "failed_ids": failed_ids,
        "refused": refused,
        "reason": reason,
        "checks": checks,
        "blocked": blocked,
        "findings": {
            check_id: [str(f) for f in (recorded.get(check_id) or [])]
            for check_id in checks
        } if isinstance(recorded, dict) else {},
        "undone_with": undone_with,
    }


def native_stop_answers(state: Any) -> List[Dict[str, Any]]:
    """:func:`compose_stop_answers` for a stopped native implement, read from
    ``state.json`` as recorded (a ``StateManager`` or the file's dict).

    The native leg leaves no stop record: the answers are what the record
    shows waiting for one — each task of the decomposition implement ran
    last (``implement_task_ids``) recorded ``failed`` (one the emit refused
    before dispatch, :data:`NATIVE_REFUSED_PREFIX`, answered as the executor
    answers a refusal), and each check whose findings hold tasks back
    (:func:`held_back_by_checks`). A ``skip`` leaves undone the tasks that
    depend on its task and have not run (not a manual one). ``[]`` when none
    waits, or when the record cannot be read.

    A failed task whose edits are half-applied
    (:data:`HALF_APPLIED_PREFIX`, ``util batch-done --partial``) gets no
    answer, as the executor offers none for a partial application: it is
    inspected first. One whose reply said ``applied`` and changed nothing
    (:data:`UNLANDED_REASON`) is answered ``skip`` first, then ``done`` for
    a change made by hand, as the executor answers it.
    """
    facts = _native_stop_facts(state)
    if facts is None:
        return []
    reason = facts["reason"]
    refused = facts["refused"]
    return compose_stop_answers(
        refused=refused,
        failed=[
            FailedAnswerable(
                task_id,
                unlanded=reason(task_id).lower().startswith(UNLANDED_REASON),
            )
            for task_id in facts["failed_ids"]
            if task_id not in refused
            and not reason(task_id).startswith(HALF_APPLIED_PREFIX)
        ],
        checks=facts["checks"],
        blocked=facts["blocked"],
        findings=facts["findings"],
        undone_with=facts["undone_with"],
    )


def executor_check_stamp(
    phase_dir: Union[str, Path], check_id: str, findings: Any,
) -> Optional[str]:
    """The tree the ``--exec-subagents`` leg stamped on *check_id*'s verdict.

    ``verdict.tree_fingerprint`` of ``{phase}/implement_batch_<id>.json``
    (:meth:`WriteBatchScheduler._stamp_verdict`, re-stamped with the tree the
    run left by its ``CheckHolds.restamp_check_trees``), the same digest
    ``write_prompt.check_tree_fingerprint`` takes. Only a verdict that is an
    ``ok`` check with findings, and the very findings ``state.json`` holds
    (*findings*), so a stamp is never read off another run of the check than
    the one on record. ``None`` otherwise. Shared by the native ``--resume``
    (``implement_orchestrator._executor_check_stamp``) and the native why
    (:func:`check_kept_on_resume`).
    """
    if not isinstance(findings, list) or not findings:
        return None
    path = Path(phase_dir) / implement_output_name(check_id)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    verdict = data.get("verdict") if isinstance(data, dict) else None
    if not isinstance(verdict, dict) or verdict.get("ok") is not True:
        return None
    if not verdict.get("verification_only"):
        return None
    if row_check_findings(verdict) != [str(item) for item in findings]:
        return None
    stamp = verdict.get("tree_fingerprint")
    return stamp if isinstance(stamp, str) and stamp else None


def check_kept_on_resume(
    state: Any, check_id: str, phase_dir: Optional[Union[str, Path]] = None,
) -> bool:
    """Whether a native ``--resume`` on an unchanged tree keeps *check_id*'s
    findings instead of handing the check out again
    (``implement_orchestrator._native_check_reruns``): a ``task_check_trees``
    stamp on record, else, with *phase_dir*, the executor's verdict stamp
    (:func:`executor_check_stamp`). With neither, the check runs again, and
    the resume's why says so."""
    try:
        stamps = state.get(TASK_CHECK_TREES_KEY)
        findings = (state.get("task_check_findings") or {})
    except Exception:  # noqa: BLE001 - an advisory read
        return False
    if isinstance(stamps, dict) and stamps.get(check_id):
        return True
    if phase_dir is None or not isinstance(findings, dict):
        return False
    return executor_check_stamp(phase_dir, check_id, findings.get(check_id)) is not None


#: What a refusal of a file outside the repository says
#: (``write_safety.policy_outside_note``), read off a native refusal's reason.
OUTSIDE_REFUSAL_WORDS = "outside the repository, so no driver.write_paths rule can allow"


def native_resume_why(
    state: Any, *, phase_dir: Optional[Union[str, Path]] = None,
) -> Optional[str]:
    """:func:`compose_resume_why` for a stopped native implement, from the
    facts :func:`native_stop_answers` answers it from: every
    refusal the native emit records is the write policy's, and a failed task
    — a half-applied one too — is handed out again on a resume. A check
    whose findings hold tasks back is said to stay unrun only when the
    resume keeps it (:func:`check_kept_on_resume`, with the implement
    *phase_dir* for the executor's stamp)."""
    facts = _native_stop_facts(state)
    if facts is None:
        return None
    refused = facts["refused"]
    reason = facts["reason"]
    return compose_resume_why(
        refused=refused,
        policy=set(refused),
        # The refusal's own words (`write_safety.policy_outside_note`).
        outside={
            task_id for task_id in refused
            if OUTSIDE_REFUSAL_WORDS in reason(task_id)
        },
        failed=[
            FailedAnswerable(task_id) for task_id in facts["failed_ids"]
            if task_id not in refused
        ],
        checks=facts["checks"],
        rerun_checks={
            check_id for check_id in facts["checks"]
            if not check_kept_on_resume(state, check_id, phase_dir)
        },
        blocked=facts["blocked"],
        undone_with=facts["undone_with"],
        # What it keeps, as the executor's why says it.
        kept=implement_tasks_done(state),
    )


def _accounting_line(account: Dict[str, Any]) -> str:
    """``N tasks in this decomposition: a done, b failed (…), …`` — every
    bucket, named, adding up to the total."""
    parts = [f"{len(account['done'])} done"]
    flagged = account.get("check_findings") or []
    if flagged:
        # Inside the done bucket, so the buckets still add up to the total.
        parts[0] += f" ({len(flagged)} with check findings: {', '.join(flagged)})"
    if account["failed"]:
        parts.append(f"{len(account['failed'])} failed ({', '.join(account['failed'])})")
    if account["not_run"]:
        blocked = account.get("blocked") or {}
        stopped = [tid for tid in account["not_run"] if tid not in blocked]
        named = [", ".join(stopped)] if stopped else []
        for check_id in sorted(set(blocked.values())):
            waiting = [tid for tid in account["not_run"] if blocked.get(tid) == check_id]
            named.append(
                f"{', '.join(waiting)}: upstream check {check_id} reported problems"
            )
        parts.append(f"{len(account['not_run'])} not run ({'; '.join(named)})")
    with_findings = account.get("accepted_with_findings") or []
    after_failing = [tid for tid in account["accepted"] if tid not in with_findings]
    # The bucket names are the labels every other surface uses (this line still read
    # "accepted with their
    # check findings" beside the table's "accepted with its check findings").
    if after_failing:
        parts.append(
            f"{len(after_failing)} {ACCEPTED_AFTER_FAILING_LABEL} "
            f"({', '.join(after_failing)})"
        )
    if with_findings:
        parts.append(
            f"{len(with_findings)} {ACCEPTED_WITH_FINDINGS_LABEL} "
            f"({', '.join(with_findings)})"
        )
    if account["completed_manual"]:
        parts.append(
            f"{len(account['completed_manual'])} completed manual "
            f"({', '.join(account['completed_manual'])})"
        )
    if account["declined"]:
        parts.append(
            f"{len(account['declined'])} skipped at your request "
            f"({', '.join(account['declined'])})"
        )
    if account["skipped_dependents"]:
        parts.append(
            f"{len(account['skipped_dependents'])} skipped with a skipped task "
            f"({', '.join(account['skipped_dependents'])})"
        )
    if account["deferred"]:
        parts.append(
            f"{len(account['deferred'])} deferred manual ({', '.join(account['deferred'])})"
        )
    total = account["total"]
    return (
        f"**Tasks in this decomposition**: {total} — " + ", ".join(parts) + "."
    )
