"""The write verdict (D3g): which outcome a classified write dispatch lands on.

``WriteBatchScheduler._classify`` gathers what a dispatch did into
:class:`WriteFacts`, the guards' facts in their order and only until one
matches (:func:`guard`), asks :func:`decide`, and applies the :class:`Verdict`.
Every side effect stays there, around this module: consuming the containment
sweep, restoring a policy violation's files, the jail's records, the audit
line. :func:`decide` is the table and :func:`reason_for` words each row;
both are pure (no I/O, no scheduler). ``status``, ``summary.md`` and the stop
messages print the reasons, so their wording is part of the contract
(``tests/test_write_verdict_table.py`` pins every one).

The rows, their order and why: ``docs/development/write-scheduler.md``,
"The verdict table".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .task_dispatch import (
    STATUS_BATCH_FAILED,
    STATUS_PARTIAL,
    STATUS_POLICY_VIOLATION,
)
from .retry_ladder import STATUS_OK
from .batch_reply import (
    WRITE_APPLIED,
    WRITE_CLEAN_FAILURE,
    WRITE_NO_OP,
    WRITE_PARTIAL,
    WRITE_POLICY_VIOLATION,
)
from .subagent_tasks import SHARED_ARTIFACT_WRITE_KINDS
from .text_clip import with_closing_mark, without_closing_mark


class VerdictRule(Enum):
    """One member per terminal row of :func:`decide`, in the order it checks
    them."""

    POLICY_VIOLATION = "policy-violation"
    REPLACED_TARGET = "replaced-target"
    JAIL_PARTIAL = "jail-partial"
    JAIL_FAILED = "jail-failed"
    CHECK_UNOBSERVED = "check-unobserved"
    CHECK_MOVED = "check-moved"
    CHECK_COULD_NOT_RUN = "check-could-not-run"
    CHECK_FINDINGS = "check-findings"
    VERIFIED = "verified"
    PARTIAL = "partial"
    APPLIED_NO_OP_CLAIMED = "applied-no-op-claimed"
    FAILED = "failed"
    NO_OP = "no-op"
    PARTIAL_OUTSIDE = "partial-outside"
    APPLIED_OUTSIDE = "applied-outside"
    NOT_APPLIED = "not-applied"
    APPLIED = "applied"


#: Each row's ``(write_outcome, status)``.
OUTCOMES: Dict[VerdictRule, Tuple[str, str]] = {
    VerdictRule.POLICY_VIOLATION: (WRITE_POLICY_VIOLATION, STATUS_POLICY_VIOLATION),
    VerdictRule.REPLACED_TARGET: (WRITE_CLEAN_FAILURE, STATUS_BATCH_FAILED),
    VerdictRule.JAIL_PARTIAL: (WRITE_PARTIAL, STATUS_PARTIAL),
    VerdictRule.JAIL_FAILED: (WRITE_CLEAN_FAILURE, STATUS_BATCH_FAILED),
    VerdictRule.CHECK_UNOBSERVED: (WRITE_CLEAN_FAILURE, STATUS_BATCH_FAILED),
    VerdictRule.CHECK_MOVED: (WRITE_PARTIAL, STATUS_PARTIAL),
    VerdictRule.CHECK_COULD_NOT_RUN: (WRITE_CLEAN_FAILURE, STATUS_BATCH_FAILED),
    VerdictRule.CHECK_FINDINGS: (WRITE_NO_OP, STATUS_OK),
    VerdictRule.VERIFIED: (WRITE_NO_OP, STATUS_OK),
    VerdictRule.PARTIAL: (WRITE_PARTIAL, STATUS_PARTIAL),
    VerdictRule.APPLIED_NO_OP_CLAIMED: (WRITE_APPLIED, STATUS_OK),
    VerdictRule.FAILED: (WRITE_CLEAN_FAILURE, STATUS_BATCH_FAILED),
    VerdictRule.NO_OP: (WRITE_NO_OP, STATUS_OK),
    VerdictRule.PARTIAL_OUTSIDE: (WRITE_PARTIAL, STATUS_PARTIAL),
    VerdictRule.APPLIED_OUTSIDE: (WRITE_APPLIED, STATUS_OK),
    VerdictRule.NOT_APPLIED: (WRITE_CLEAN_FAILURE, STATUS_BATCH_FAILED),
    VerdictRule.APPLIED: (WRITE_APPLIED, STATUS_OK),
}


# -- the facts -----------------------------------------------------------------

@dataclass(frozen=True)
class PolicyFacts:
    """The post-run ``WritePolicy.check`` refused these paths (D3l)."""

    message: str
    paths: Tuple[str, ...]


@dataclass(frozen=True)
class TargetReplaced:
    """The write target's inode changed during a plugin-landlock dispatch."""

    label: str
    shown: str
    before_inode: int
    #: ``None``: nothing is at the path any more.
    after_inode: Optional[int]


@dataclass(frozen=True)
class JailFacts:
    """The plugin-landlock jail's denials, read off the child's stream.

    ``hard`` and ``replacements`` are the row's facts and name no path. The
    paths are resolved after :func:`guard` has read those, and only for what
    it then words: the denied paths and the scope sentence when a jail row
    decides, the note's paths when none does."""

    #: A failed ``file_change``, or a command denial on an in-scope path.
    hard: bool
    #: How many ``replacement`` denials.
    replacements: int = 0
    #: A jail row's: every denied path, repo-relative.
    denied: Tuple[str, ...] = ()
    #: A jail row's: why an in-grant path was refused and what to do instead,
    #: ending in a space (``write_grant.WriteGrant.jail_scope_sentence``).
    scope_sentence: str = ""
    #: The note's (:func:`jail_note`), when no jail row decides: the
    #: ``replacement`` denials and the out-of-scope ones, repo-relative.
    replacement: Tuple[str, ...] = ()
    out_of_scope_count: int = 0
    out_of_scope: Tuple[str, ...] = ()


@dataclass(frozen=True)
class WriteFacts:
    """What one dispatch did, as :func:`decide` and :func:`reason_for` read it.

    ``_classify`` gathers the guards' facts in the table's order, each only
    while no guard before it has matched (:func:`guard`), and the facts only
    the rows after the guards read once none has: a fact it did not gather
    keeps its default."""

    task_id: str
    kind: str
    #: The reply's ``status``; ``failed`` for an implement task it declined.
    claimed: str
    #: ``None``: no exit code observed (the native invoker), not zero.
    exit_code: Optional[int]
    #: The DECLARED files whose bytes moved: the snapshot's comparison taken
    #: before the sweep adopts this dispatch's undeclared writes. Never the
    #: rollback set (``files_touched``).
    changed: Tuple[str, ...]
    expected_ids: Tuple[str, ...] = ()
    reported_ids: Tuple[str, ...] = ()
    #: ``reported_ids`` minus the ids also in ``declined``.
    attested_ids: Tuple[str, ...] = ()
    #: An apply batch's declined items, ``{id: reason}``.
    declined: Mapping[str, str] = field(default_factory=dict)
    #: The reason an implement reply declined its task with.
    declined_task: Optional[str] = None
    declined_problems: Tuple[str, ...] = ()
    #: What the sweep saw move outside the declared set; ``own`` leaves out
    #: what a sibling running at the same time also saw (``siblings``).
    undeclared: Tuple[str, ...] = ()
    undeclared_own: Tuple[str, ...] = ()
    siblings: Tuple[str, ...] = ()
    #: ``False``: the sweep could not look (not the same as nothing moved).
    sweep_observed: bool = True
    policy: Optional[PolicyFacts] = None
    replaced: Optional[TargetReplaced] = None
    jail: Optional[JailFacts] = None
    #: An implement task that declares no files.
    verification_only: bool = False
    #: Its reply's ``check`` (``batch_reply.read_check_reply``).
    check: Optional[Tuple[str, ...]] = None
    check_listed: bool = False
    check_could_not_run: bool = False
    # The wording's inputs; no row depends on them. ``declared_names`` is read
    # for the rows in :data:`DECLARED_NAMES_ROWS` only.
    summary: str = ""
    declined_words: str = ""
    declared_names: str = "any declared file"
    snapshot_dir: str = ""
    snapshot_reused: bool = False
    resent: bool = False
    resend_note: Optional[str] = None
    named_files: Tuple[str, ...] = ()
    repo_root: str = ""
    sweep_max_files: int = 0

    @property
    def crashed(self) -> bool:
        return self.exit_code not in (0, None)

    @property
    def missing_ids(self) -> List[str]:
        """The expected ids neither attested nor declined. An id-less reply
        attests nothing: ``ids`` is optional in the result schema."""
        accounted = set(self.attested_ids) | set(self.declined)
        return [item for item in self.expected_ids if item not in accounted]

    @property
    def all_declined(self) -> bool:
        return bool(self.expected_ids) and all(
            item in self.declined for item in self.expected_ids
        )

    @property
    def own(self) -> Tuple[str, ...]:
        """The undeclared writes that can make this batch applied: none for
        a plan or task-list batch, judged on its declared file alone."""
        return () if self.kind in SHARED_ARTIFACT_WRITE_KINDS else self.undeclared_own


@dataclass(frozen=True)
class Verdict:
    rule: VerdictRule
    write_outcome: str
    status: str
    applied_without_changes: bool = False
    #: A partial application's items left out of a readable report, which a
    #: ``--human-task <id>=skip`` answer records as skipped.
    unapplied_ids: Tuple[str, ...] = ()
    #: The verification-only row read the reply's check as one that did not
    #: run, whichever row decided: its findings become the runner's notes.
    check_not_run: bool = False


def _verdict(rule: VerdictRule, **extra: Any) -> Verdict:
    write_outcome, status = OUTCOMES[rule]
    return Verdict(rule, write_outcome, status, **extra)


# -- the table -------------------------------------------------------------------

def guard(facts: WriteFacts) -> Optional[Verdict]:
    """The guard row *facts* land on, or ``None``: the write policy, then the
    plugin-landlock rung's replaced target, then its jail denials.

    :func:`decide` asks this first. A guard row reads only its own facts and
    those of the guards before it, so once one matches no fact gathered
    after it changes the verdict: ``_classify`` stops gathering there.
    """
    if facts.policy is not None:
        return _verdict(VerdictRule.POLICY_VIOLATION)
    if facts.replaced is not None:
        return _verdict(VerdictRule.REPLACED_TARGET)
    jail = facts.jail
    if jail is not None and (jail.hard or (jail.replacements and not facts.changed)):
        # A replacement denial counts only while the target is unchanged: once
        # it changed in place, the runner recovered.
        if jail.hard and _jail_moved(facts):
            return _verdict(VerdictRule.JAIL_PARTIAL)
        return _verdict(VerdictRule.JAIL_FAILED)
    return None


def decide(facts: WriteFacts) -> Verdict:
    """The row *facts* land on. The first row that matches decides.

    The guards come first and in this order, each ahead of every claim row:
    the write policy, then the plugin-landlock rung's replaced target and
    jail denials (codex ends a turn whose every write the jail refused with
    exit 0, so the claim alone would read it as applied) (:func:`guard`),
    then a task that declares no files. In the claim rows the claim is never
    the verdict: the bytes decide, and a non-zero exit never lands on APPLIED
    (D3k).
    """
    guarded = guard(facts)
    if guarded is not None:
        return guarded

    check_not_run = False
    if facts.verification_only:
        # The sweep is the whole verdict of a task that promised to change
        # nothing, so "could not look" is no evidence either way.
        if not facts.sweep_observed:
            return _verdict(VerdictRule.CHECK_UNOBSERVED)
        if facts.undeclared or facts.changed:
            return _verdict(VerdictRule.CHECK_MOVED)
        if not facts.crashed:
            # A check that did not run says nothing about the code. A `failed`
            # claim that lists findings ran, and is read as findings.
            if facts.check_could_not_run or (
                facts.claimed == "failed" and not facts.check_listed
            ):
                if facts.claimed != "failed":
                    return _verdict(VerdictRule.CHECK_COULD_NOT_RUN, check_not_run=True)
                check_not_run = True
            elif facts.check:
                return _verdict(VerdictRule.CHECK_FINDINGS)
            else:
                return _verdict(VerdictRule.VERIFIED)
        # A crash, or a `failed` check that did not run: the claim rows'
        # clean failure below.

    changed, crashed, claimed = facts.changed, facts.crashed, facts.claimed
    missing = facts.missing_ids
    if changed and (crashed or claimed == "failed" or missing or facts.all_declined):
        return _verdict(
            VerdictRule.PARTIAL, unapplied_ids=_unapplied(facts),
            check_not_run=check_not_run,
        )
    if changed and claimed == "no-op":
        # Every expected id came back and the runner did not crash: the bytes
        # are real, so it is applied, whatever the claim said.
        return _verdict(VerdictRule.APPLIED_NO_OP_CLAIMED, check_not_run=check_not_run)
    if not changed:
        if crashed or (claimed == "failed" and not facts.all_declined):
            return _verdict(VerdictRule.FAILED, check_not_run=check_not_run)
        if claimed == "no-op" or (facts.all_declined and not facts.own):
            return _verdict(VerdictRule.NO_OP, check_not_run=check_not_run)
        if facts.own:
            if missing or facts.all_declined:
                return _verdict(VerdictRule.PARTIAL_OUTSIDE, check_not_run=check_not_run)
            return _verdict(VerdictRule.APPLIED_OUTSIDE, check_not_run=check_not_run)
        # Success claimed and not one byte of the change moved, after the one
        # re-send: the change did not land.
        return _verdict(
            VerdictRule.NOT_APPLIED, applied_without_changes=True,
            check_not_run=check_not_run,
        )
    # Reachable only on a clean exit: a crash with a non-empty diff is the
    # partial row and one with an empty diff the clean failure (D3k).
    return _verdict(VerdictRule.APPLIED, check_not_run=check_not_run)


def _jail_moved(facts: WriteFacts) -> List[str]:
    """What moved under a jail denial: the declared files, then the rest."""
    return list(facts.changed) + [
        path for path in facts.undeclared if path not in facts.changed
    ]


def _partial_cause(facts: WriteFacts) -> str:
    """Which reason a partial application with moved declared bytes gives
    after any crash (the first of these that holds)."""
    missing = facts.missing_ids
    if facts.declined_task is not None:
        return "declined-task"
    if facts.claimed == "failed":
        return "failed"
    if facts.all_declined and not missing:
        return "all-declined"
    if missing and not facts.reported_ids and not facts.declined:
        return "unattested"
    if missing:
        return "missing"
    return ""


def _unapplied(facts: WriteFacts) -> Tuple[str, ...]:
    """The items a readable report left out of both lists, when it attests
    at least one applied: a report that only declined has nothing to keep."""
    if (
        _partial_cause(facts) == "missing"
        and not facts.crashed and facts.claimed != "failed"
        and any(item in facts.expected_ids for item in facts.attested_ids)
    ):
        return tuple(facts.missing_ids)
    return ()


# -- the wording -------------------------------------------------------------------

#: The rows whose reason names the declared files
#: (``WriteFacts.declared_names``): ``_classify`` reads the snapshot's
#: declarations for these rows only.
DECLARED_NAMES_ROWS = frozenset({
    VerdictRule.JAIL_FAILED,
    VerdictRule.FAILED,
    VerdictRule.NO_OP,
    VerdictRule.PARTIAL_OUTSIDE,
    VerdictRule.APPLIED_OUTSIDE,
    VerdictRule.NOT_APPLIED,
})


#: ``TaskSnapshot.restore``'s state for a path its snapshot holds nothing
#: for: the one ``skipped:`` state that says no rollback point was taken.
NOT_IN_SNAPSHOT = "skipped: not in this task's snapshot"


@dataclass(frozen=True)
class PolicyRestore:
    """What restoring a policy violation's paths did, one list per outcome."""

    restored: Tuple[str, ...] = ()
    #: Put back from what the commit review's guard kept.
    from_guard: Tuple[str, ...] = ()
    #: No rollback point, so left on disk.
    stranded: Tuple[str, ...] = ()
    #: Left on disk for another reason, each with the restore's own: a
    #: rollback point it refused to write (the file's folder replaced
    #: meanwhile, say), one gone or altered, the guard's copy missing or stale.
    refused: Tuple[Tuple[str, str], ...] = ()

    @classmethod
    def from_report(
        cls, report: Mapping[str, str], guard_states: Iterable[str] = (),
    ) -> "PolicyRestore":
        """*report* (``TaskSnapshot.restore``'s, ``path -> state``) split;
        *guard_states* are the states the commit guard's fallback writes."""
        guard = set(guard_states)
        return cls(
            restored=tuple(sorted(
                path for path, state in report.items()
                if not state.startswith("skipped:") and state not in guard
            )),
            from_guard=tuple(sorted(
                path for path, state in report.items() if state in guard
            )),
            stranded=tuple(sorted(
                path for path, state in report.items() if state == NOT_IN_SNAPSHOT
            )),
            refused=tuple(sorted(
                (path, state[len("skipped:"):].strip())
                for path, state in report.items()
                if state.startswith("skipped:") and state != NOT_IN_SNAPSHOT
            )),
        )

    def not_restored(self) -> str:
        """The sentences naming what is left on disk: no rollback point, or
        the restore's own reason for each path, never one for the other."""
        left = ""
        if self.stranded:
            many = len(self.stranded) != 1
            # A path the sweep could not retain bytes for (a policy-denied one
            # above all: its bytes are never copied into an executor artifact)
            # is not restored, and says so.
            left += (
                f" Not restored, because no rollback point exists "
                f"({_names(self.stranded)}): left on disk as "
                f"{'they are' if many else 'it is'} now, so inspect "
                f"{'them' if many else 'it'} by hand."
            )
        if self.refused:
            many = len(self.refused) != 1
            reasons = "; ".join(
                f"{path}: {without_closing_mark(why)}" for path, why in self.refused[:5]
            ) + ("; …" if len(self.refused) > 5 else "")
            left += (
                f" Not restored ({reasons}): left on disk as "
                f"{'they are' if many else 'it is'} now, so inspect "
                f"{'them' if many else 'it'} by hand."
            )
        return left


def findings_clause(findings: Sequence[Any]) -> str:
    """*findings* as one clause, joined with "; ", each without its own
    closing stop (``…found 2).; src/…`` read as two marks, fix round 28)."""
    return "; ".join(
        without_closing_mark(" ".join(str(item).split())) for item in findings
        if str(item).strip()
    )


def _names(paths: Sequence[str]) -> str:
    """The first five of *paths*, with an ellipsis for the rest."""
    return ", ".join(paths[:5]) + (", …" if len(paths) > 5 else "")


def _no_status(claimed: str) -> str:
    return repr(claimed or "no status")


def _runner_summary(facts: WriteFacts) -> str:
    return f" Runner summary: {facts.summary}" if facts.summary else ""


def reason_for(
    verdict: Verdict, facts: WriteFacts, restore: Optional[PolicyRestore] = None,
) -> Optional[str]:
    """The ``reason`` *verdict*'s row records. ``None`` only for a plain
    APPLIED, whose outcome keeps the reason it had. *restore* is what
    restoring a policy violation's paths did (its row only)."""
    rule = verdict.rule
    if rule is VerdictRule.POLICY_VIOLATION:
        assert facts.policy is not None
        return policy_reason(facts.policy, restore or PolicyRestore())
    if rule is VerdictRule.REPLACED_TARGET:
        assert facts.replaced is not None
        return replaced_target_reason(facts.replaced, facts.snapshot_dir, facts.claimed)
    if rule in (VerdictRule.JAIL_PARTIAL, VerdictRule.JAIL_FAILED):
        return _jail_reason(rule, facts)
    if rule in _CHECK_REASONS:
        return _CHECK_REASONS[rule](facts)
    return _CLAIM_REASONS[rule](facts)


def policy_reason(policy: PolicyFacts, restore: PolicyRestore) -> str:
    # The sweep sees that a path moved during the task's window, not who moved
    # it, so the reason never names the runner as the author; each path is in
    # exactly one of the lists.
    many = len(policy.paths) != 1
    restored, from_guard = restore.restored, restore.from_guard
    return (
        f"{policy.message} "
        f"{'These paths' if many else 'This path'} changed during this "
        f"task's window; the executor sees that they moved, not who "
        f"moved them, so the change may be another process's or your "
        f"own edit and not the runner's."
        + (
            f" Restored from the pre-batch snapshot: "
            f"{', '.join(restored)}."
            if restored else ""
        )
        + (
            f" Put back as {'it was' if len(from_guard) == 1 else 'they were'} "
            f"before the batch from what the commit review's guard kept "
            f"(its copy, or a deletion of a file that did not exist): "
            f"{', '.join(from_guard)}."
            if from_guard else ""
        )
        + restore.not_restored()
        + " The loop stops here."
    )


def replaced_target_reason(
    replaced: TargetReplaced, snapshot_dir: str, claimed: str,
    *, ended: Optional[str] = None,
) -> str:
    """The replaced-target row's reason; ``ended`` is the status of a
    dispatch that never reached the classification, named in the claim's
    place."""
    now = "is gone" if replaced.after_inode is None else "now names a different file"
    over = (
        f"whatever the runner claimed ({_no_status(claimed)})"
        if ended is None
        else f"whatever the dispatch itself ended as ({ended!r})"
    )
    after = "none" if replaced.after_inode is None else replaced.after_inode
    return (
        f"FAILED (target replaced): {replaced.label} was replaced while the runner "
        f"was editing it, and the jail's grant stayed on the old file, so "
        f"the runner's edits were refused or lost — {replaced.shown} {now} "
        f"(inode {replaced.before_inode} before the dispatch, "
        f"{after} after), {over}. Nothing was "
        f"rolled back over the file now at that path: its bytes are not the "
        f"runner's. The pre-batch snapshot is kept at {snapshot_dir} "
        f"for comparison. The loop stops here; --resume re-dispatches this "
        f"batch against the file now at the path, under a fresh grant."
    )


def _jail_reason(rule: VerdictRule, facts: WriteFacts) -> str:
    jail = facts.jail
    assert jail is not None
    denied_text = (
        f"the plugin-landlock jail refused the runner's write to "
        f"{', '.join(jail.denied) or 'a path it did not name'}"
    )
    tail = jail.scope_sentence
    if rule is VerdictRule.JAIL_PARTIAL:
        moved = _jail_moved(facts)
        return (
            f"PARTIAL APPLICATION (jail-denied edit): {len(moved)} "
            f"file(s) changed ({', '.join(moved)}) but {denied_text}; "
            f"the bytes, not the runner's claim ({_no_status(facts.claimed)}), "
            f"say what landed. {tail}The batch loop stops here, the "
            f"pre-batch snapshot is kept at {facts.snapshot_dir}, and "
            f"the phase is NOT marked completed — an automatic revert "
            f"would destroy the half-applied state a human needs to "
            f"inspect."
        )
    return (
        f"FAILED (jail-denied edit): {denied_text}, and the "
        f"pre-batch snapshot comparison confirms no byte changes in "
        f"{facts.declared_names}. The runner claimed "
        f"{_no_status(facts.claimed)}; a denied edit is never "
        f"recorded as applied. {tail}Nothing to restore; the loop "
        f"stops here and --resume re-dispatches this batch under "
        f"the same grant."
    )


def jail_note(jail: JailFacts) -> Optional[str]:
    """The denials that left the verdict alone (a replacement the runner
    recovered from in place, out-of-scope denials), for the batch's line and
    its outcome's reason; ``None`` when there are none."""
    notes = []
    if jail.replacement:
        notes.append(
            f"{len(jail.replacement)} replacement denial(s) the runner recovered "
            f"from in place ({', '.join(jail.replacement)})"
        )
    if jail.out_of_scope_count:
        shown = ", ".join(jail.out_of_scope)
        notes.append(
            f"{jail.out_of_scope_count} out-of-scope denial(s)"
            + (f" ({shown})" if shown else "")
        )
    if not notes:
        return None
    return (
        f"The plugin-landlock jail refused {'; '.join(notes)} — none "
        f"of them changes the verdict."
    )


def _check_unobserved(facts: WriteFacts) -> str:
    return (
        f"BATCH FAILED: {facts.task_id} declares no files (a "
        f"verification-only task), so the post-run containment sweep "
        f"is its whole verdict, and the sweep could not run: the tree "
        f"under {facts.repo_root} holds more than {facts.sweep_max_files} "
        f"files after the run (D3l). Whether the task changed anything "
        f"is unknown, so it is not VERIFIED. Inspect the working tree, "
        f"take the untracked trees (node_modules/, build output) out "
        f"of the checkout or list the files it may change under "
        f"`Files to modify`, and re-run with --resume."
    )


def _check_moved(facts: WriteFacts) -> str:
    # `changed` joins the sweep's paths: a reused snapshot still carries the
    # entries an earlier dispatch's sweep adopted, so a stray edit that run
    # left on disk stays partial until it is declared or restored.
    moved = sorted(set(facts.undeclared) | set(facts.changed))
    earlier = [path for path in moved if path not in facts.undeclared]
    return (
        f"PARTIAL APPLICATION: {facts.task_id} declares no files (a "
        f"verification-only task) but {len(moved)} file(s) changed "
        f"during its run ({_names(moved)}). "
        + (
            f"{len(earlier)} of them ({_names(earlier)}) "
            f"still differ from the pre-batch snapshot an earlier "
            f"dispatch of this task took: left on disk by that run, "
            f"not restored since. "
            if earlier and facts.snapshot_reused
            else ""
        )
        + f"The loop stops here and the "
        f"pre-batch snapshot is kept at {facts.snapshot_dir}. If this "
        f"task is meant to fix what it checks, list those files under "
        f"`Files to modify` in the tasks file and re-run with --resume; "
        f"otherwise restore them with `util restore-batch`."
    )


def _check_could_not_run(facts: WriteFacts) -> str:
    return (
        f"FAILED: {facts.task_id}'s reply says a check could not "
        f"run (`check.could_not_run`, beside status "
        f"{facts.claimed or 'none'!r}) and no file changed. A check that "
        f"did not run says nothing about the code, so the loop stops "
        f"here and --resume re-dispatches this batch."
        + _runner_summary(facts)
    )


def _check_findings(facts: WriteFacts) -> str:
    check = list(facts.check or ())
    # Each finding keeps its words without its closing stop, and the
    # sentence gets one stop.
    shown = findings_clause(check[:3]) + (
        f"; +{len(check) - 3} more" if len(check) > 3 else ""
    )
    return (
        f"CHECK FINDINGS: {facts.task_id}'s check ran and reported "
        f"{len(check)} problem(s): {with_closing_mark(shown)} No file "
        f"changed, so the loop continues; the findings are listed in the "
        f"implementation summary and go to review-code."
        + (
            " Its reply said `failed`, but it listed what the check "
            "found and did not say the check could not run "
            "(`check.could_not_run`), so it is read as findings."
            if facts.claimed == "failed" else ""
        )
    )


def _verified(facts: WriteFacts) -> str:
    return (
        f"VERIFIED: {facts.task_id} declares no files and the sweep found "
        f"no file changed during its run"
        + (
            " and its check reported that it passed"
            if facts.check is not None else
            " (its reply reported no `check` result)"
        )
        + ". Recorded; the loop continues."
        + _runner_summary(facts)
    )


_CHECK_REASONS = {
    VerdictRule.CHECK_UNOBSERVED: _check_unobserved,
    VerdictRule.CHECK_MOVED: _check_moved,
    VerdictRule.CHECK_COULD_NOT_RUN: _check_could_not_run,
    VerdictRule.CHECK_FINDINGS: _check_findings,
    VerdictRule.VERIFIED: _verified,
}


def _partial(facts: WriteFacts) -> str:
    expected, missing = list(facts.expected_ids), facts.missing_ids
    details = []
    if facts.crashed:
        details.append(
            f"the runner exited {facts.exit_code} (claiming "
            f"{_no_status(facts.claimed)})"
        )
    cause = _partial_cause(facts)
    if cause == "declined-task":
        details.append(f"the runner declined the task ({facts.declined_task})")
    elif cause == "failed":
        details.append(f"the batch reported {facts.claimed!r}")
    elif cause == "all-declined":
        details.append(
            f"the batch declined every item it held ({facts.declined_words})"
        )
    elif cause == "unattested":
        details.append(
            f"it reported no `ids` at all, so nothing attests that the "
            f"{len(expected)} expected change(s) "
            f"({_names(expected)}) are what landed"
        )
    elif cause == "missing":
        # Counted from the expected side: the reply's own `ids` may name
        # things this batch does not hold.
        matched = len(expected) - len(missing)
        unexpected = [i for i in facts.reported_ids if i not in expected]
        details.append(
            (f"only {matched} of {len(expected)}" if matched
             else f"none of the {len(expected)}")
            + f" expected id(s) came back (missing: "
            f"{', '.join(missing)})"
            + (
                f" — {len(facts.declined)} of them declined"
                if facts.declined else ""
            )
            + (
                f"; the reply named {len(unexpected)} id(s) this batch "
                f"does not hold ({', '.join(repr(i) for i in unexpected[:5])}"
                f"{', …' if len(unexpected) > 5 else ''})"
                if unexpected else ""
            )
            + (
                f"; its `declined` could not be read for: "
                f"{'; '.join(facts.declined_problems[:5])}"
                if facts.declined_problems else ""
            )
        )
    return (
        f"PARTIAL APPLICATION: {len(facts.changed)} file(s) changed "
        f"({', '.join(facts.changed)}) but {' and '.join(details)}. The batch "
        f"loop stops here, the pre-batch snapshot is kept at "
        f"{facts.snapshot_dir}, and the phase is NOT marked completed — an "
        f"automatic revert would destroy the half-applied state a human "
        f"needs to inspect."
    )


def _applied_no_op_claimed(facts: WriteFacts) -> str:
    # Two different events read identically from the bytes: the snapshot was
    # reused from an earlier dispatch of this batch (the diff is that
    # attempt's), or this dispatch's own snapshot disagrees with the claim.
    changed_names = ", ".join(facts.changed)
    if facts.snapshot_reused:
        return (
            f"APPLIED (kept from an earlier attempt): the edits an "
            f"earlier attempt made to {changed_names} are kept and "
            f"count as applied; this run's model found them already "
            f"in place (it reported no change). The rollback point "
            f"is still the pre-batch snapshot taken before that "
            f"first attempt."
        )
    return (
        f"APPLIED (no-op claimed, bytes moved): {changed_names} "
        f"differ from the snapshot taken at the start of THIS "
        f"dispatch — a foreign-or-undeclared-write signature, not "
        f"an artifact of resume. Recorded as applied because the "
        f"bytes are real; the 'no-op' claim should not be trusted."
    )


def _failed(facts: WriteFacts) -> str:
    outside = list(facts.undeclared)
    what = (
        f"the runner exited {facts.exit_code} (claiming "
        f"{_no_status(facts.claimed)})"
        if facts.crashed else
        f"the runner declined the task ({facts.declined_task})"
        if facts.declined_task is not None else
        f"the batch reported {facts.claimed!r}"
    )
    return (
        f"FAILED: {what} and the pre-batch snapshot comparison "
        f"confirms no byte changes in {facts.declared_names}. "
        + (
            f"It declined {with_closing_mark(facts.declined_words)} "
            if facts.declined else ""
        )
        + (
            f"{len(outside)} file(s) outside it changed "
            f"({_names(outside)}): inspect them, restore them with "
            f"util restore-batch or keep them; "
            if outside else "Nothing to restore; "
        )
        + "the loop stops here and --resume re-dispatches this "
        "batch."
        + _runner_summary(facts)
    )


def _no_op(facts: WriteFacts) -> str:
    if facts.all_declined:
        return (
            f"NO-OP: the batch declined every item it held "
            f"({facts.declined_words}) and the "
            f"pre-batch snapshot comparison confirms no byte "
            f"changes in {facts.declared_names}. Recorded; the loop "
            f"continues."
        )
    return (
        f"NO-OP: the batch reported 'no-op' and the pre-batch "
        f"snapshot comparison confirms no byte changes in "
        f"{facts.declared_names}. Recorded; the loop continues."
    )


def _partial_outside(facts: WriteFacts) -> str:
    own, missing = facts.own, facts.missing_ids
    return (
        f"PARTIAL APPLICATION: none of the files the batch "
        f"declares changed ({facts.declared_names}), while "
        f"{len(own)} file(s) outside them did "
        f"({_names(own)}), and "
        + (
            f"not every expected id came back (missing: "
            f"{', '.join(missing)})"
            if missing else
            "the batch declined every item it held"
        )
        + f". The batch "
        f"loop stops here, the pre-batch snapshot is kept at "
        f"{facts.snapshot_dir}, and the phase is NOT marked "
        f"completed — an automatic revert would destroy the "
        f"half-applied state a human needs to inspect."
    )


def _applied_outside(facts: WriteFacts) -> str:
    own = facts.own
    return (
        f"APPLIED outside the declared files: none of "
        f"{facts.declared_names} changed, but {len(own)} "
        f"other file(s) did ({_names(own)}) and the reply "
        f"attests every expected id; the bytes decide."
    )


def _not_applied(facts: WriteFacts) -> str:
    outside, siblings, named = list(facts.undeclared), facts.siblings, facts.named_files
    if facts.resent:
        again = (
            " — the second time: it was sent once more, told that "
            + (
                f"its previous attempt had not changed "
                f"{facts.declared_names}"
                if outside else
                "its previous attempt had changed no file"
            )
            + ", and that reply said the same"
        )
    elif facts.resend_note:
        again = f" ({facts.resend_note})"
    elif outside and siblings:
        again = (
            " (not sent again: files moved during its run, so a "
            "second dispatch could apply its work twice)"
        )
    elif not facts.sweep_observed:
        again = (
            " (no re-send: the containment sweep could not see "
            "whether any other file changed, so the batch was not "
            "sent again)"
        )
    else:
        again = ""
    if outside and siblings:
        # The sweep cannot say whose a path is that a sibling running at the
        # same time also saw move.
        elsewhere = (
            f"; {len(outside)} file(s) outside them changed "
            f"({_names(outside)}), but {', '.join(siblings)}, "
            f"running at the same time, saw "
            f"{'it' if len(outside) == 1 else 'them'} change too, "
            f"so {'it is' if len(outside) == 1 else 'they are'} "
            f"not counted as this task's change"
        )
    elif outside:
        elsewhere = (
            f"; {len(outside)} file(s) outside it changed "
            f"({_names(outside)}), which is not this batch's change"
        )
    elif facts.sweep_observed:
        elsewhere = ", and no other file changed either"
    else:
        elsewhere = ""
    return (
        f"NOT APPLIED: the batch reported {_no_status(facts.claimed)}"
        + (
            f" and named {_names(list(named))} as edited"
            if named else ""
        )
        + f", but the pre-batch snapshot comparison found no byte "
        f"change in {facts.declared_names}"
        + elsewhere
        + f"{again}. Its change did not land, so it is not recorded "
        f"as done: the loop stops here, "
        + (
            "the files outside it are left as they are (restore "
            "them with util restore-batch, or keep them), "
            if outside else "there is nothing to restore, "
        )
        + "and --resume dispatches it again."
        + _runner_summary(facts)
    )


def _applied(facts: WriteFacts) -> Optional[str]:
    if not facts.declined:
        return None
    # Complete, and what it left out is said.
    applied = len(facts.expected_ids) - len(facts.declined)
    return (
        f"APPLIED {applied} of {len(facts.expected_ids)} item(s); the batch "
        f"declined the rest, so they are not applied: "
        f"{with_closing_mark(facts.declined_words)}"
    )


_CLAIM_REASONS = {
    VerdictRule.PARTIAL: _partial,
    VerdictRule.APPLIED_NO_OP_CLAIMED: _applied_no_op_claimed,
    VerdictRule.FAILED: _failed,
    VerdictRule.NO_OP: _no_op,
    VerdictRule.PARTIAL_OUTSIDE: _partial_outside,
    VerdictRule.APPLIED_OUTSIDE: _applied_outside,
    VerdictRule.NOT_APPLIED: _not_applied,
    VerdictRule.APPLIED: _applied,
}
