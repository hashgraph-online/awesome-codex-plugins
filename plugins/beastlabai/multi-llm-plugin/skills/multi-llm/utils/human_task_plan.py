"""Human tasks: one strategy, resolved once, then a graph walk (D3n).

The failure strategies (``STRATEGIES``), :class:`HumanTaskPlan` and its
resolution from ``--human-task`` answers, the manual gates a run stops
at, and the labels an answered task is recorded under. Both legs read
them: the scheduler, and ``implement``'s native handoff.

``utils.write_batch_scheduler`` re-exports every name defined here for
reading only: patch one here, never through the scheduler
(docs/development/write-scheduler.md#where-the-schedulers-helpers-live).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from . import check_records as _check_records
from . import metrics as _metrics
from . import task_ledger
from .task_ledger import (
    ACCEPTED_AFTER_FAILING_LABEL,
    ACCEPTED_REASON_PREFIX,
    ACCEPTED_WITH_FINDINGS_LABEL,
    ACCEPTED_WITH_FINDINGS_MARK,
    ANSWERED_SKIP_PREFIX,
    COMPLETED_BY_HAND_LABEL,
    COMPLETED_MANUAL_REASON,
    USER_DECLINED_REASON,
    is_declined_reason,
)
from .task_outcome import ExecutorError
from .state_manager import manual_task_gates


STRATEGY_PAUSE = "pause-and-ask"
STRATEGY_SKIP_CONTINUE = "skip-continue"
STRATEGY_SKIP_DEPENDENTS = "skip-dependents"
STRATEGIES = (STRATEGY_PAUSE, STRATEGY_SKIP_CONTINUE, STRATEGY_SKIP_DEPENDENTS)


# ---------------------------------------------------------------------------
# Human tasks: one strategy, resolved once, then a graph walk (D3n)
# ---------------------------------------------------------------------------

@dataclass
class HumanTaskPlan:
    """The resolved human-task decision for a whole phase.

    Resolved **before** the loop and never re-asked on resume, then applied as a
    graph walk. All three strategies live here rather than in markdown, so the skip
    set, the reasons and the override records are byte-identical on both invokers.
    """

    strategy: Optional[str] = None
    #: ``task_id -> reason``. Every skip carries the sentence the markdown specifies.
    skipped: Dict[str, str] = field(default_factory=dict)
    #: ``task_id -> [human task ids treated as satisfied]`` (skip-continue only).
    overrides: Dict[str, List[str]] = field(default_factory=dict)
    #: Human tasks answered ``done`` via ``--human-task <id>=done``.
    completed: List[str] = field(default_factory=list)
    #: Human tasks still waiting for an answer under ``pause-and-ask``.
    pending: List[str] = field(default_factory=list)
    #: ``child -> parent`` chain, for the summary's skip-chain reporting.
    chain: Dict[str, str] = field(default_factory=dict)
    #: ``task_id -> reason`` for a task the last run recorded ``failed`` and
    #: the user answered ``--human-task <id>=done``: treated as satisfied, not
    #: dispatched again, its dependents run (racing re-run 3, 2026-10-05: a
    #: failed check blocked implement for good).
    accepted: Dict[str, str] = field(default_factory=dict)
    #: Failed tasks answered ``--human-task <id>=retry``: dispatched again even
    #: when nothing in the repository changed since the failure.
    retry: List[str] = field(default_factory=list)
    #: Tasks an earlier run recorded ``skipped`` that this plan no longer
    #: skips (``--resume --force-strategy skip-continue`` after a
    #: ``skip-dependents`` run): :func:`persist_human_task_plan` records them
    #: ``pending`` again, dropping the old reason (:func:`mark_no_longer_skipped`).
    unskipped: List[str] = field(default_factory=list)

    def is_skipped(self, task_id: str) -> bool:
        return task_id in self.skipped

    def declined(self) -> Dict[str, str]:
        """The skips that are the user's own decision, with their reasons.

        A pause-and-ask "Skip", a failed code task answered
        ``--human-task <id>=skip``, and every task skipped *because* it depends
        on one of those (``chain``). They are not deferred work: nobody is
        owed them afterwards, so neither the summary's ``## Manual Tasks
        (Deferred)`` section nor ``[WORKFLOW_COMPLETE]``'s manual-task list
        names them (``StateManager._deferred_to_user`` reads the same two
        reasons back from ``state.json``). Everything else in ``skipped`` is a
        deferral: a manual task under a skip strategy and its dependents.
        """
        declined: Dict[str, str] = {}
        for task_id, reason in self.skipped.items():
            if is_declined_reason(reason):
                declined[task_id] = reason
        changed = True
        while changed:
            changed = False
            for child, parent in self.chain.items():
                if child not in declined and parent in declined and child in self.skipped:
                    declined[child] = self.skipped[child]
                    changed = True
        return declined

    def deferred(self) -> Dict[str, str]:
        """``skipped`` minus :meth:`declined`: what is still owed by hand."""
        declined = self.declined()
        return {
            task_id: reason for task_id, reason in self.skipped.items()
            if task_id not in declined
        }


def _declined_split(plan: "HumanTaskPlan") -> Dict[str, List[str]]:
    """The write mirror's two keys for the skips the user chose (fix round 14).

    ``declined_task_ids``: the tasks the user skipped themselves (a
    pause-and-ask "Skip", ``--human-task <id>=skip``);
    ``declined_dependent_task_ids``: the tasks skipped because they depend on
    one of those. Both are in ``skipped_task_ids`` too, and neither is a
    deferral: :meth:`HumanTaskPlan.declined` is the one rule, and
    ``task_ledger.skip_bucket`` names each, as ``status`` names the same
    tasks from ``state.json``. Empty lists are left out, so a run that
    declined nothing mirrors what it did before.
    """
    buckets = {
        task_id: task_ledger.skip_bucket(
            task_id, reason, declined=lambda: True, root=lambda: None)[0]
        for task_id, reason in plan.declined().items()
    }
    seeds = sorted(task_id for task_id, bucket in buckets.items() if bucket == "declined")
    dependents = sorted(
        task_id for task_id, bucket in buckets.items() if bucket == "declined_dependents")
    out: Dict[str, List[str]] = {}
    if seeds:
        out["declined_task_ids"] = seeds
    if dependents:
        out["declined_dependent_task_ids"] = dependents
    return out


def _deferred_split(plan: "HumanTaskPlan") -> Dict[str, Dict[str, str]]:
    """The write mirror's key for the tasks skipped with a deferred manual
    task (fix round 17): ``deferred_waits_on``, ``{task: manual task}``,
    each followed up :attr:`HumanTaskPlan.chain` to the deferral it waits
    on (``task_ledger.skip_bucket``, the rule ``status`` reads from
    ``state.json`` too). They are in ``skipped_task_ids`` too; ``status``
    names them "skipped (depends on manual T005)" instead of "deferred
    manual", since implement runs them once that task is recorded done.
    Left out when empty, as :func:`_declined_split`'s keys are.
    """
    waits: Dict[str, str] = {}
    for task_id, reason in plan.deferred().items():
        bucket, root = task_ledger.skip_bucket(
            task_id, reason, declined=lambda: False,
            root=lambda task_id=task_id: task_ledger.skip_chain_root(
                task_id, plan.chain.get),
        )
        if bucket == "deferred_dependents" and root is not None:
            waits[task_id] = root
    return {"deferred_waits_on": dict(sorted(waits.items()))} if waits else {}


def manual_gate_head(
    phase: str, labels: Mapping[str, str], waiting: Mapping[str, Sequence[str]],
) -> str:
    """What a run a manual task gates says first, on both implement legs
    (fix round 28, live run 12, Codex racing 06): that nothing ran, the
    gating manual task(s) by id and title (*labels*: ``{id: " (title)"}``)
    and how many code tasks wait on each."""
    gating = sorted(waiting, key=_metrics._id_key)
    held = {code for codes in waiting.values() for code in codes}
    if len(gating) == 1:
        task_id = gating[0]
        count = len(held)
        return (
            f"{phase} ran nothing: {count} code "
            + ("task waits" if count == 1 else "tasks wait")
            + f" on manual task {task_id}{labels.get(task_id, '')}, which is "
            f"not recorded done, and no other code task can run"
        )
    named = ", ".join(
        f"{task_id}{labels.get(task_id, '')} holds {len(waiting[task_id])}"
        for task_id in gating
    )
    return (
        f"{phase} ran nothing: every code task left waits on a manual task "
        f"not recorded done ({named})"
    )


def manual_gate_way_on(gating: Sequence[str]) -> str:
    """The gate's ways on, as a stop headline says them (fix round 28):
    the resume recording the gating manual tasks done, then (fix round 29,
    review of round 28 #1) the user's decline, ``--human-task <id>=skip``,
    which skips the task and the code tasks that wait on it."""
    it = "it" if len(gating) == 1 else "them"
    answers = " ".join(f"--human-task {task_id}=done" for task_id in gating)
    if len(gating) == 1:
        decline = (
            f"or, if you will not do {gating[0]}, resume with --human-task "
            f"{gating[0]}=skip instead (it and the code tasks that wait on it "
            f"are skipped)"
        )
    else:
        skips = ", ".join(f"--human-task {task_id}=skip" for task_id in gating)
        decline = (
            f"or, for any of them you will not do, give its answer instead "
            f"({skips}): it and the code tasks that wait on it are skipped"
        )
    return (
        f"To go on: do {', '.join(gating)} by hand, then resume this phase "
        f"with {answers} (the code tasks that wait on {it} then run); "
        f"{decline}."
    )


def plan_manual_gates(
    plan: Optional["HumanTaskPlan"],
    nodes: Sequence[Dict[str, Any]],
    statuses: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """``state_manager.manual_task_gates`` over a resolved *plan*, before
    or after it is persisted (fix round 28, live run 12, Codex racing 06).

    *nodes* is the decomposition (:func:`decomposition_graph`), *statuses*
    ``state.json``'s ``task_status`` as recorded. Done: a task on record
    ``completed`` that the plan does not skip, a manual task the plan
    completes, a failed task it accepts. Owed: the manual tasks the plan
    defers. Dropped: the tasks the user skipped and the ones skipped with
    them (:meth:`HumanTaskPlan.declined`). Both implement legs ask it: the
    executor at the end of a run that dispatched nothing, the native emit
    for the note on recording the manual tasks done."""
    graph: Dict[str, List[str]] = {}
    human: set = set()
    for node in nodes:
        if not isinstance(node, dict):
            continue
        task_id = str(node.get("task_id") or node.get("id") or "")
        if not task_id:
            continue
        graph[task_id] = [str(dep) for dep in (node.get("depends_on") or []) if dep]
        if node.get("is_human") or node.get("executor_role") == "human":
            human.add(task_id)
    if plan is None:
        return manual_task_gates(graph, human_ids=human, done=(), owed=())
    recorded = {str(k): str(v) for k, v in dict(statuses or {}).items()}
    done = (
        {task_id for task_id, status in recorded.items() if status == "completed"}
        | set(plan.completed) | set(plan.accepted)
    ) - set(plan.skipped)
    return manual_task_gates(
        graph,
        human_ids=human,
        done=done,
        owed=[task_id for task_id in plan.deferred() if task_id in human],
        dropped=list(plan.declined()),
    )


def set_aside_by_plan(
    plan: Optional["HumanTaskPlan"], manual_ids: Iterable[str],
) -> Dict[str, str]:
    """``{task id: how}`` for the tasks *plan* set aside, in
    ``metrics.set_aside_tail``'s words (fix round 24, Claude Code racing
    #6: "task 10/10 done … ALL TASKS COMPLETE" while the manual T011 and
    T012 were left): a deferred manual task (*manual_ids*), a task skipped
    with one, a task the user skipped (:meth:`HumanTaskPlan.declined`'s
    seeds) and a task skipped with that one; and a manual task still
    waiting for its answer (``pending``: the native leg's pause-and-ask
    host asks at that task, so a trailing one is unanswered at N/N). Both
    implement legs hand it to the line that reaches N/N, which names them
    instead of claiming every task is complete."""
    if plan is None:
        return {}
    manual = {str(task_id) for task_id in manual_ids}
    declined = plan.declined()
    aside: Dict[str, str] = {
        str(task_id): _metrics.SET_ASIDE_MANUAL for task_id in plan.pending
    }
    for task_id, reason in plan.skipped.items():
        if task_id in declined:
            seed = is_declined_reason(reason)
            aside[str(task_id)] = (
                _metrics.SET_ASIDE_SKIPPED if seed else _metrics.SET_ASIDE_WITH_SKIPPED
            )
        else:
            aside[str(task_id)] = (
                _metrics.SET_ASIDE_MANUAL if str(task_id) in manual
                else _metrics.SET_ASIDE_WITH_MANUAL
            )
    return aside


# The reason words and the labels a task's outcome is named by live in
# `task_ledger`, the classifier both legs and `status` read
# (USER_DECLINED_REASON, ANSWERED_SKIP_PREFIX, ACCEPTED_REASON_PREFIX,
# ACCEPTED_WITH_FINDINGS_MARK, COMPLETED_MANUAL_REASON and the *_LABEL
# strings, imported above).

#: What follows ``<id>=skip`` in the recorded reason of a manual task the
#: user declined under a skip strategy (fix round 29, review of round 28 #1:
#: under ``--yes`` the answer was printed and the task deferred again, so a
#: manual-task gate re-stopped for good and only a false ``=done`` went on).
MANUAL_DECLINED_TAIL = ": you will not do this manual task"



def answered_done_label(plan: Any, task_id: str) -> str:
    """How a task answered ``--human-task <id>=done`` reads in an account:
    "accepted with its check findings" (a check whose findings the user
    accepted), "accepted after failing" (a failed code task) or "completed by
    hand" (a manual task). One wording for summary.md's rows and the resume
    tally (fix round 16)."""
    accepted = getattr(plan, "accepted", None) or {}
    if task_id in accepted:
        return (
            ACCEPTED_WITH_FINDINGS_LABEL
            if ACCEPTED_WITH_FINDINGS_MARK in str(accepted.get(task_id) or "")
            else ACCEPTED_AFTER_FAILING_LABEL
        )
    return COMPLETED_BY_HAND_LABEL


def answered_done_on_record(
    state: Any, *, exclude: Sequence[str] = (),
) -> Tuple[Dict[str, str], List[str]]:
    """The tasks an earlier run recorded done on the user's answer.

    ``(accepted, completed_manual)``: ``accepted`` maps each failed code task
    the user answered ``--human-task <id>=done`` to its recorded reason, and
    ``completed_manual`` lists the manual tasks answered ``done``. Both are
    ``completed`` in ``state.json`` with the reason the answer wrote, so a
    later ``--resume`` materializes neither and the answer no longer applies
    (it applies to a failed task only); read back from that record, they keep
    their bucket in the resumed account instead of dropping out of it and
    shrinking its total (fix round 9). Scoped to the decomposition implement
    recorded last (``implement_task_ids``, else every ``T###`` id), minus
    *exclude* (the tasks this run materialized, which the run's own plan
    accounts for).
    """
    if state is None or not hasattr(state, "get"):
        return {}, []
    try:
        statuses = dict(state.get("task_status") or {})
        reasons = dict(state.get("task_status_reasons") or {})
        current = state.get("implement_task_ids")
    except Exception:  # noqa: BLE001 - an account read must not fail a phase
        return {}, []
    scope = set(current) if isinstance(current, list) else None
    skip = {str(task_id) for task_id in exclude}
    accepted: Dict[str, str] = {}
    completed_manual: List[str] = []
    for task_id, status in sorted(statuses.items()):
        if status != "completed" or task_id in skip:
            continue
        if not _check_records._IMPLEMENT_TASK_ID.match(str(task_id)):
            continue
        if scope is not None and task_id not in scope:
            continue
        reason = str(reasons.get(task_id) or "")
        if reason.startswith(ACCEPTED_REASON_PREFIX):
            accepted[task_id] = reason
        elif reason == COMPLETED_MANUAL_REASON:
            completed_manual.append(task_id)
    return accepted, completed_manual


def _deferred_reason(strategy: Optional[str]) -> str:
    """Why a manual task did not run, naming the strategy and not a person.

    This used to say "user chose to complete manually", which is false when
    ``--yes`` resolved the strategy to ``skip-dependents`` on its own
    (2026-10-01, OpenCode run): nobody was asked.
    """
    return (
        f"deferred — manual task, left for you to complete after "
        f"implementation (human-task strategy: {strategy})"
    )


def resolve_human_task_plan(
    tasks: Sequence[Dict[str, Any]],
    *,
    strategy: Optional[str],
    decisions: Optional[Dict[str, str]] = None,
    check_findings_ids: Sequence[str] = (),
    graph: Optional[Sequence[Dict[str, Any]]] = None,
) -> HumanTaskPlan:
    """Apply ``strategy`` over the task graph and return the resolved plan (D3n).

    * ``pause-and-ask`` routes each human task to the D6 pause: a task answered
      ``done`` is treated as satisfied, one answered ``skip`` seeds the transitive
      propagation, and an unanswered one lands in ``pending`` so the caller can
      exit 3 naming the two ``--human-task`` re-invocations.
    * ``skip-continue`` marks every human task skipped, treats its edges as
      satisfied and records a dependency override per unblocked task.
    * ``skip-dependents`` marks every human task skipped and runs the transitive
      BFS forward walk over ``depends_on``.

    The strategy governs the **manual** tasks. A failed code task answered
    ``--human-task <id>=skip`` always takes its dependents with it, under every
    strategy: ``skip-continue`` means "a manual precondition is not met, run
    the code anyway", and a code task that failed and was then given up is
    not a precondition anyone can meet by hand. Until fix round 8 the
    ``skip-continue`` branch returned before the walk, so the dependents ran
    (with override records) while the stop message and the instructions both
    said they stay undone (reviewer repro, 2026-10-05).

    A check task whose findings hold back the tasks after it
    (*check_findings_ids*, :func:`rerunnable_checks`) is answered the same
    way, and its reason says so: ``done`` accepts the findings (the tasks
    after it run; the findings stay listed for review-code), ``skip`` leaves
    it and its dependents undone, ``retry`` runs the check again on
    unchanged files (fix round 11).

    *graph* is the whole decomposition (:func:`decomposition_graph`) when
    *tasks* are a resume's subset (fix round 12): the walk from a code task
    answered ``skip`` goes through a task this run does not hold (finished
    before the resume, so not skipped) to the tasks after it, which are
    skipped naming the skipped task they depend on — a check answered
    ``skip`` used to leave a task whose chain to it ran through a manual
    task answered done to run. The walk from a manual task stays over
    *tasks*.

    Pure: takes the task list, returns the decision. Persisting it (through
    ``update_task_status`` / ``record_dependency_override``) is the scheduler's job,
    which is what keeps this testable against the native path's expectations.
    """
    decisions = dict(decisions or {})
    with_findings = {str(task_id) for task_id in check_findings_ids}
    by_id: Dict[str, Dict[str, Any]] = {}
    for task in tasks:
        by_id[str(task.get("task_id", ""))] = task
    # A selected dependent can answer its omitted upstream check in the
    # same invocation. Resolve that answer against the recorded graph too;
    # otherwise the new hold would ignore an explicit acceptance or skip.
    for task in graph or ():
        task_id = str(task.get("task_id", ""))
        if (task_id in decisions and task_id not in by_id
                and task.get("executor_role") != "human" and not task.get("is_human")):
            by_id[task_id] = task
    human_ids = [
        task_id for task_id, task in by_id.items()
        if task.get("executor_role") == "human" or task.get("is_human")
    ]
    plan = HumanTaskPlan(strategy=strategy)
    # A decision for a task that is NOT human answers a task the last run
    # recorded `failed` (the orchestrator admits no other): `done` accepts
    # the failure and treats the task as satisfied, `skip` leaves it and what
    # depends on it undone, `retry` re-runs it past the unchanged-tree guard.
    seeds: List[str] = []
    code_seeds: List[str] = []
    for task_id, answer in sorted(decisions.items()):
        if task_id in human_ids or task_id not in by_id:
            continue
        found = task_id in with_findings
        if answer == "done":
            plan.accepted[task_id] = (
                f"{ACCEPTED_REASON_PREFIX}you answered --human-task {task_id}=done "
                + (
                    f"{ACCEPTED_WITH_FINDINGS_MARK}; the findings stand "
                    "(review-code is told about them), the check is not run "
                    "again and the tasks after it run"
                    if found else
                    "after it failed; treated as satisfied and not run again"
                )
            )
        elif answer == "skip":
            plan.skipped[task_id] = (
                f"{ANSWERED_SKIP_PREFIX}{task_id}=skip after "
                + ("its check reported problems" if found else "it failed")
            )
            seeds.append(task_id)
            code_seeds.append(task_id)
        elif answer == "retry":
            plan.retry.append(task_id)
    if not human_ids and not seeds:
        return plan
    if human_ids and strategy is None:
        # Nothing resolved: the caller owns the gate. Reporting the human tasks as
        # pending rather than silently skipping them is the fail-closed half.
        plan.pending = sorted(human_ids)
        return plan
    if strategy is not None and strategy not in STRATEGIES:
        raise ExecutorError(
            f"Unknown human-task strategy {strategy!r}: expected one of "
            f"{', '.join(STRATEGIES)}. Nothing was dispatched."
        )

    if not human_ids:
        pass
    elif strategy == STRATEGY_PAUSE:
        for task_id in sorted(human_ids):
            answer = decisions.get(task_id)
            if answer == "done":
                plan.completed.append(task_id)
            elif answer == "skip":
                plan.skipped[task_id] = USER_DECLINED_REASON
                seeds.append(task_id)
            else:
                plan.pending.append(task_id)
    else:
        for task_id in sorted(human_ids):
            if decisions.get(task_id) == "done":
                # The user did it (fix round 14): `--human-task <id>=done` is
                # how a deferred manual task is closed after the run, and under
                # a skip strategy the answer was printed and ignored, so the
                # task stayed owed on every surface. Its dependents run.
                plan.completed.append(task_id)
                continue
            if decisions.get(task_id) == "skip":
                # The user will not do it (fix round 29, review of round 28
                # #1): skipped at their request, so it is not owed, and under
                # skip-dependents the walk below skips the tasks after it
                # with it (`declined`), which no gate then holds back. Under
                # skip-continue the strategy still runs that code.
                plan.skipped[task_id] = (
                    f"{ANSWERED_SKIP_PREFIX}{task_id}=skip{MANUAL_DECLINED_TAIL}")
                seeds.append(task_id)
                continue
            plan.skipped[task_id] = _deferred_reason(strategy)
            seeds.append(task_id)

    # pause-and-ask (for the tasks answered `skip`) and skip-dependents both walk
    # the graph forward: BFS over "who depends on me", so a chain
    # T001(human) -> T003 -> T005 is skipped in full. skip-continue walks it
    # only from a failed code task answered `skip` (see the docstring).
    dependents: Dict[str, List[str]] = {}
    nodes = list(graph) if graph is not None else list(by_id.values())
    for task in nodes:
        if not isinstance(task, dict):
            continue
        for dep in task.get("depends_on") or []:
            dependents.setdefault(str(dep), []).append(str(task.get("task_id", "")))
    code_set = set(code_seeds)
    # A manual task the user declined under a skip strategy walks first, and
    # its walk takes over a task a deferral reached: a later manual task
    # after code that now never runs is skipped with it, not owed (fix round
    # 29). A failed code task answered `skip` keeps fix round 8's rule: a
    # manual task after it stays owed.
    walked = code_seeds if strategy == STRATEGY_SKIP_CONTINUE else seeds
    declined_seeds = {
        seed for seed in walked
        if plan.skipped.get(seed, "").endswith(MANUAL_DECLINED_TAIL)
    }
    # (task, the skipped task a dependent names, whether the walk may pass
    # through a task this run does not hold — only from a code seed, whether
    # it walks from a manual task the user declined).
    queue = [
        (seed, seed, seed in code_set, seed in declined_seeds)
        for seed in sorted(walked, key=lambda seed: seed not in declined_seeds)
    ]
    reached_declined: set = set(declined_seeds)
    passed: set = set()
    while queue:
        parent, named, through, declined = queue.pop(0)
        named_title = str(by_id.get(named, {}).get("task_title", "") or named)
        for child in sorted(set(dependents.get(parent, []))):
            if not child:
                continue
            if child not in by_id:
                if through and child not in passed:
                    passed.add(child)
                    queue.append((child, named, through, declined))
                continue
            if child in plan.skipped and (
                    not declined or child in reached_declined):
                continue
            plan.skipped[child] = (
                f"skipped — depends on skipped task {named} ({named_title})"
            )
            plan.chain[child] = named
            if declined:
                reached_declined.add(child)
            queue.append((child, child, through, declined))

    if strategy == STRATEGY_SKIP_CONTINUE:
        # A manual task's edges are treated as satisfied: its dependents run,
        # and every one of them gets an override RECORD so "it ran against an
        # unmet precondition" is visible afterwards instead of inferred. A
        # dependent the walk above skipped does not run, so it gets none.
        manual_skipped = {tid for tid in human_ids if tid in plan.skipped}
        for task_id, task in by_id.items():
            if task_id in plan.skipped:
                continue
            overridden = [
                dep for dep in (task.get("depends_on") or [])
                if str(dep) in manual_skipped
            ]
            if overridden:
                plan.overrides[task_id] = sorted(str(dep) for dep in overridden)
    return plan


def mark_no_longer_skipped(
    plan: HumanTaskPlan, task_ids: Sequence[str], recorded: Dict[str, Any],
) -> List[str]:
    """Record on *plan* the tasks *recorded* says ``skipped`` that it runs.

    A ``--resume`` materializes a skipped task again (fix round 8), and only
    a skip the new plan makes used to overwrite its status. After a
    ``skip-dependents`` run, ``--resume --force-strategy skip-continue``
    (``--force-strategy`` outranks the recorded strategy) left a dependent of
    the manual task ``skipped`` with its "depends on skipped task" reason: the
    native host never dispatched it, a stop before it left the record
    standing, and ``[MANUAL_TASK]`` named it owed for good (fix round 9). A
    task of *task_ids* the plan neither skips, completes nor accepts goes in
    ``plan.unskipped``; returns them. A plan with no strategy and manual tasks
    pending resolved nothing (the walk never ran), so it unskips nothing.
    """
    if plan.strategy is None and plan.pending:
        return []
    for task_id in task_ids:
        task_id = str(task_id or "")
        if (
            not task_id or recorded.get(task_id) != "skipped"
            or task_id in plan.skipped or task_id in plan.completed
            or task_id in plan.accepted or task_id in plan.unskipped
        ):
            continue
        plan.unskipped.append(task_id)
    return list(plan.unskipped)


def persist_human_task_plan(state: Any, plan: HumanTaskPlan) -> None:
    """Write a resolved :class:`HumanTaskPlan` into ``state.json`` and save.

    The strategy, a ``skipped`` status (with its reason) for every task the
    walk skipped, ``completed`` for a human task answered ``done`` and for a
    failed code task accepted with ``done``, ``pending`` for a task an
    earlier run skipped that this plan runs (``unskipped``), and one
    dependency override per unblocked task. Shared by the scheduler (before
    its first batch) and by ``implement``'s native emit, which records the
    same plan before it hands the batches to the host: until 2026-10-05 the
    native leg left these writes to the host, which never made them, so a
    task deferred under ``--yes`` never reached ``task_status`` and the
    finished workflow named no manual task (racing re-run 3, Claude Code).
    An unanswered ``pause-and-ask`` task is left without a status here.
    """
    if plan.strategy and state.get("human_task_strategy") != plan.strategy:
        state.set("human_task_strategy", plan.strategy)
    for task_id, reason in sorted(plan.skipped.items()):
        state.update_task_status(task_id, "skipped", reason=reason)
    for task_id in plan.completed:
        state.update_task_status(
            task_id, "completed", reason=COMPLETED_MANUAL_REASON,
        )
    for task_id, reason in sorted(plan.accepted.items()):
        state.update_task_status(task_id, "completed", reason=reason)
    for task_id in plan.unskipped:
        # No reason: the old skip's reason goes with the old status.
        state.update_task_status(task_id, "pending")
    for task_id, overridden in sorted(plan.overrides.items()):
        state.record_dependency_override(task_id, list(overridden))
    state.save()
