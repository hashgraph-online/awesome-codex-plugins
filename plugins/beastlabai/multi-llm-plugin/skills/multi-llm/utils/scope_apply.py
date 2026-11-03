"""The apply side of the scope policy (plans/scope-policy-and-report-tags.md §4, §5).

:mod:`utils.scope_policy` owns the vocabulary, the authority rules and the
gate (:func:`scope_policy.scope_decision`). This module is what the three
apply phases, the write-task bridge, the write scheduler and ``util
write-prompt`` share on top of it:

* resolving the effective apply policy (explicit flag → the round's recorded
  apply override → the round's review policy → ``expand``);
* running the gate over a work set and turning deferrals into the persisted,
  reported records (never invalid, user-skipped, applied, failed or
  processed);
* the scope context a ``preserve`` write task and its prompt carry (selected
  remedy, binding, writer guidance), and the refusal of a task materialized
  under another policy or binding;
* the completion record ("eligible work completed", deferrals kept) and the
  one concrete blocker signal (a ``preserve`` writer decline whose reason
  starts with :data:`BLOCKER_PREFIX`).

Under ``expand`` every function here is a pass-through or returns nothing, so
the default work set, formatting, task files and prompts stay byte-identical.
Pure and import-light, like its parent module: callers own I/O and saving.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

try:
    from . import scope_policy as sp
except ImportError:  # pragma: no cover - script-style import
    from utils import scope_policy as sp  # type: ignore

#: Formatted ``to_apply`` / ``needs_human_review`` items carry their scope
#: context here, under ``preserve`` only.
ITEM_KEY = "scope"
#: A materialized write task's scope block (``subagent_tasks.schema.json``),
#: under ``preserve`` only: ``{policy, policy_source, baseline_id, binding,
#: items: [{id, group_id, relation, reason, proposal_digest, selected_remedy?}]}``.
TASK_KEY = "scope"
#: ``orchestrator_output.json``'s block (present under ``preserve``, and when an
#: ``expand`` override released earlier deferrals).
OUTPUT_KEY = "scope_policy"
#: Keys this module adds to a round's ``state.json`` record (beside the ones
#: :mod:`utils.scope_policy` writes): the completion outcome and the blockers.
COMPLETION_KEY = "completion"
BLOCKERS_KEY = "blockers"
#: The outcome words of :data:`COMPLETION_KEY`.
OUTCOME_ELIGIBLE_DONE = "eligible work completed"
OUTCOME_BLOCKED = "blocked"
#: What a ``preserve`` writer starts a decline reason with when the agreed goal
#: itself cannot be met inside the scope: the one concrete blocker signal.
BLOCKER_PREFIX = "SCOPE BLOCKER:"
#: Marker lines.
DEFERRED_MARKER = "[SCOPE_DEFERRED]"
BLOCKER_MARKER = "[SCOPE_BLOCKER]"
RETIRED_MARKER = "[SCOPE_POLICY_CHANGED]"


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ApplyPolicy:
    """The effective policy of one apply invocation."""

    policy: str
    source: str
    review_policy: str
    baseline_id: Optional[str]
    #: The recorded deferrals of the round before this run touched them.
    recorded_deferrals: Tuple[Dict[str, Any], ...] = ()

    @property
    def preserve(self) -> bool:
        return self.policy == sp.POLICY_PRESERVE


def invalid_policy_message(raw: Any) -> Optional[str]:
    """The exit-3 message for an explicit value that names no policy, else ``None``."""
    if raw is None or sp.is_valid_policy(raw):
        return None
    return (
        f"{sp.FLAG} {raw!r} is not a scope policy (choose "
        f"{' or '.join(sp.POLICIES)}). Nothing was changed."
    )


def resolve_apply_policy(explicit: Any, state: Mapping[str, Any], phase: str) -> ApplyPolicy:
    """Plan §4's order for an apply phase: explicit → the round's recorded
    apply override (continuation) → the round's review policy → ``expand``."""
    record = sp.round_record(state, phase)
    policies = sp.round_policies(state, phase)
    policy, source = sp.resolve_policy(
        explicit=explicit,
        continuation=policies["apply_policy"],
        recorded=policies["review_policy"] if record is not None else None,
    )
    if source == sp.SOURCE_DEFAULT and record is None:
        source = sp.SOURCE_LEGACY
    return ApplyPolicy(
        policy=policy, source=source, review_policy=policies["review_policy"],
        baseline_id=policies["baseline_id"],
        recorded_deferrals=tuple(dict(d) for d in policies["deferrals"]),
    )


def effective_from_state(state: Mapping[str, Any], phase: str) -> Tuple[str, Optional[str]]:
    """``(policy, baseline_id)`` a dispatch enforces, read from ``state.json``
    alone (``util write-prompt``, and a scheduler not handed a policy)."""
    resolved = resolve_apply_policy(None, state if isinstance(state, Mapping) else {}, phase)
    return resolved.policy, resolved.baseline_id


# ---------------------------------------------------------------------------
# The gate over a work set
# ---------------------------------------------------------------------------


def gate(groups: Sequence[Dict[str, Any]], applied: ApplyPolicy) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """``(eligible, deferred)`` groups, in order; a pass-through under ``expand``.

    Under ``preserve`` each group gets its decision as
    :data:`scope_policy.DECISION_KEY` (for reports and results), recomputed
    from the policy and the group's bound verdict as it stands now.
    """
    if not applied.preserve:
        return list(groups), []
    eligible: List[Dict[str, Any]] = []
    deferred: List[Dict[str, Any]] = []
    for group in groups:
        decision = sp.scope_decision(group, applied.policy, applied.baseline_id)
        group[sp.DECISION_KEY] = decision.to_dict()
        (eligible if decision.eligible else deferred).append(group)
    return eligible, deferred


def group_title(group: Mapping[str, Any]) -> str:
    members = sp.group_members(group)
    if members and members[0].get("title"):
        return str(members[0].get("title"))
    return str(group.get("theme") or "Unknown")


def deferral_entry(group: Mapping[str, Any], applied: ApplyPolicy, *, importance: str = "") -> Dict[str, Any]:
    """One persisted / reported deferral (``scope_policy.deferral_record`` plus
    what a summary names it by)."""
    decision = sp.scope_decision(group, applied.policy, applied.baseline_id)
    entry = sp.deferral_record(group, decision, applied.baseline_id)
    entry["title"] = sp.flatten_text(group_title(group), 160)
    if importance:
        entry["importance"] = importance
    entry["validation_status"] = str(group.get("validation_status") or "")
    entry["outcome"] = sp.DEFERRED_OUTCOME
    return entry


def deferral_note(entries: Sequence[Mapping[str, Any]], item_noun_plural: str) -> Optional[str]:
    """The result line's notice for this run's deferrals, else ``None``."""
    if not entries:
        return None
    labels: Dict[str, int] = {}
    for entry in entries:
        labels[str(entry.get("label") or sp.LABELS[sp.UNCLEAR])] = (
            labels.get(str(entry.get("label") or sp.LABELS[sp.UNCLEAR]), 0) + 1)
    shown = ", ".join(f"{count} {label}" for label, count in sorted(labels.items()))
    return (
        f"{len(entries)} {item_noun_plural} deferred by {sp.FLAG} preserve "
        f"({shown}); they stay on record as deferred, not applied, skipped or "
        f"invalid, and an apply with {sp.FLAG} expand offers them again"
    )


def output_block(applied: Optional[ApplyPolicy], entries: Sequence[Mapping[str, Any]],
                 released: Sequence[str] = ()) -> Dict[str, Any]:
    """``{"scope_policy": {...}}`` for ``orchestrator_output.json``, or ``{}``.

    Empty under ``expand`` unless this run released earlier deferrals, so a
    default run's output keeps exactly its keys.
    """
    if applied is None or (not applied.preserve and not released):
        return {}
    block: Dict[str, Any] = {
        "policy": applied.policy,
        "policy_source": applied.source,
        "review_policy": applied.review_policy,
        "baseline_id": applied.baseline_id,
        "deferred_count": len(entries),
        "deferred_items": [dict(e) for e in entries],
    }
    if released:
        block["released_count"] = len(released)
        block["released_group_ids"] = list(released)
    return {OUTPUT_KEY: block}


def persist_deferrals(state: Dict[str, Any], phase: str, entries: Sequence[Mapping[str, Any]]) -> None:
    """Replace the round's deferrals and drop a stale completion record.

    A new gate run is a new account of the round's remaining work; the
    previous run's completion outcome no longer describes it. A ``blocked``
    completion is the exception: only a completion that finds no blocker
    (:func:`record_completion`) clears it, so a run that stops before its
    completion leaves the phase blocked for its dependents.
    """
    sp.record_deferrals(state, phase, entries)
    record = state.get(sp.STATE_KEY, {}).get(sp.review_phase_of(phase))
    if isinstance(record, dict):
        completion = record.get(COMPLETION_KEY)
        if isinstance(completion, Mapping) and completion.get("outcome") == OUTCOME_BLOCKED:
            return
        record.pop(COMPLETION_KEY, None)
        record.pop(BLOCKERS_KEY, None)


# ---------------------------------------------------------------------------
# Formatting: the selected remedy is the instruction under preserve
# ---------------------------------------------------------------------------


def selected_remedy(group: Mapping[str, Any], applied: Optional[ApplyPolicy]) -> Optional[str]:
    """The bound remedy a ``preserve`` validation selected, else ``None``.

    Only under ``preserve`` and only while the verdict is authoritative: under
    ``expand`` scope annotation never changes the remedy (plan §3).
    """
    if applied is None or not applied.preserve:
        return None
    auth = sp.authority(group, applied.baseline_id)
    if auth.authoritative and auth.relation == sp.IN_SCOPE and auth.selected_remedy:
        return auth.selected_remedy
    return None


def annotate_item(formatted: Dict[str, Any], group: Mapping[str, Any],
                  applied: Optional[ApplyPolicy], *,
                  original_description: Optional[str] = None) -> Dict[str, Any]:
    """Add the ``preserve`` scope context to one formatted item (in place).

    With a selected remedy, the remedy becomes the item's ``description``
    (and ``desc``): it is the instruction. The original member descriptions
    are kept only under ``scope.original_description`` in the output JSON,
    never in a write prompt, so a discarded extension cannot come back as an
    instruction. A no-op under ``expand``.
    """
    if applied is None or not applied.preserve:
        return formatted
    auth = sp.authority(group, applied.baseline_id)
    verdict = group.get(sp.VERDICT_KEY) if isinstance(group.get(sp.VERDICT_KEY), Mapping) else {}
    block: Dict[str, Any] = {
        "policy": applied.policy,
        "relation": auth.relation,
        "label": sp.LABELS[auth.relation],
        "reason": auth.reason,
        "reference": auth.reference,
        "authority": auth.state,
        "baseline_id": applied.baseline_id,
        "proposal_digest": verdict.get("proposal_digest") if auth.authoritative else None,
    }
    remedy = selected_remedy(group, applied)
    if remedy:
        block["selected_remedy"] = remedy
        block["original_description"] = (
            formatted.get("description", "") if original_description is None
            else original_description)
        formatted["description"] = remedy
        if "desc" in formatted:
            formatted["desc"] = remedy
    formatted[ITEM_KEY] = block
    return formatted


# ---------------------------------------------------------------------------
# Write tasks: the scope block, the writer prompt block, the stale check
# ---------------------------------------------------------------------------


def _items_of(batch: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    items = batch.get("suggestions")
    if items is None:
        items = batch.get("fixes")
    return [i for i in items or [] if isinstance(i, Mapping)]


def _binding(policy: str, baseline_id: Optional[str], items: Sequence[Mapping[str, Any]]) -> str:
    payload = json.dumps({"policy": policy, "baseline_id": baseline_id, "items": list(items)},
                         sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def task_block(batch: Mapping[str, Any], member_ids: Sequence[str],
               applied: Optional[ApplyPolicy]) -> Optional[Dict[str, Any]]:
    """The :data:`TASK_KEY` block for one apply batch, or ``None`` under ``expand``."""
    if applied is None or not applied.preserve:
        return None
    items: List[Dict[str, Any]] = []
    for member_id, item in zip(member_ids, _items_of(batch)):
        scope = item.get(ITEM_KEY) if isinstance(item.get(ITEM_KEY), Mapping) else {}
        entry: Dict[str, Any] = {
            "id": str(member_id),
            "group_id": str(item.get("group_id") or ""),
            "relation": str(scope.get("relation") or sp.UNCLEAR),
            "reason": str(scope.get("reason") or ""),
            "proposal_digest": scope.get("proposal_digest"),
        }
        if scope.get("selected_remedy"):
            entry["selected_remedy"] = str(scope["selected_remedy"])
        items.append(entry)
    return {
        "policy": applied.policy,
        "policy_source": applied.source,
        "baseline_id": applied.baseline_id,
        "binding": _binding(applied.policy, applied.baseline_id, items),
        "items": items,
    }


def task_policy(task: Mapping[str, Any]) -> str:
    """The policy *task* was materialized under (no block: ``expand``, legacy too)."""
    block = task.get(TASK_KEY) if isinstance(task, Mapping) else None
    if isinstance(block, Mapping):
        return sp.effective(block.get("policy"))
    return sp.DEFAULT_POLICY


def writer_block(task: Mapping[str, Any]) -> str:
    """The write prompt's scope section for a ``preserve`` task; ``""`` otherwise.

    :func:`scope_policy.writer_guidance` plus each item's validated scope and
    the one blocker convention. Rendered per call from the task's own block.
    """
    block = task.get(TASK_KEY) if isinstance(task, Mapping) else None
    if not isinstance(block, Mapping) or sp.effective(block.get("policy")) != sp.POLICY_PRESERVE:
        return ""
    lines = [sp.writer_guidance(sp.POLICY_PRESERVE), ""]
    baseline = block.get("baseline_id") or "(none recorded)"
    lines.append(f"Scope baseline: {baseline}. The validated scope of each item:")
    for item in block.get("items") or []:
        if not isinstance(item, Mapping):
            continue
        text = f"- `{item.get('id')}`: {sp.label(item.get('relation'))}"
        reason = sp.flatten_text(item.get("reason"))
        if reason:
            text += f" — {reason}"
        if item.get("selected_remedy"):
            text += " (validation selected the remedy given as its instruction above; apply only that)"
        lines.append(text)
    lines.append("")
    lines.append(
        f"If an item's agreed requirement itself cannot be met without such an "
        f"expansion, begin its decline reason with `{BLOCKER_PREFIX}` and name the "
        f"scope decision the user has to make."
    )
    return "\n".join(lines)


def stale_task_refusal(task: Mapping[str, Any], policy: Any,
                       baseline_id: Optional[str] = None) -> Optional[str]:
    """Why *task* must not be dispatched under the effective *policy*, else ``None``.

    Missing scope metadata never blocks an ``expand`` dispatch the existing
    lifecycle permits. A task materialized under the other policy is refused
    either way (its prompt would enforce the wrong one), and under
    ``preserve`` the task's baseline, binding and per-item relations must
    hold: a legacy task file cannot acquire authority from a flag.
    """
    effective = sp.effective(policy)
    task_id = str(task.get("task_id") or "?")
    materialized = task_policy(task)
    recovery = (
        "Nothing was dispatched. Re-run the phase's orchestrator: it "
        "rematerializes the tasks under the current policy (batches already "
        "applied keep their ids and are not applied again)"
    )
    if effective == sp.POLICY_EXPAND and materialized == sp.POLICY_EXPAND:
        return None
    if materialized != effective:
        return (
            f"{task_id} was materialized under {sp.FLAG} {materialized}, but the "
            f"round's effective policy is now {effective}, so its prompt would "
            f"enforce the wrong policy"
            + ("; a task file from before the policy cannot acquire scope "
               "authority from a flag" if materialized == sp.POLICY_EXPAND else "")
            + f". {recovery}."
        )
    block = task.get(TASK_KEY)
    if not isinstance(block, Mapping):  # pragma: no cover - guarded by task_policy
        return f"{task_id} carries no scope binding. {recovery}."
    if baseline_id and block.get("baseline_id") != baseline_id:
        return (
            f"{task_id} was bound to scope baseline {block.get('baseline_id')}, but "
            f"the round's baseline is {baseline_id}. {recovery}."
        )
    items = [dict(i) for i in block.get("items") or [] if isinstance(i, Mapping)]
    if block.get("binding") != _binding(effective, block.get("baseline_id"), items):
        return f"{task_id}'s scope binding does not match its items. {recovery}."
    by_id = {str(i.get("id")): i for i in items}
    for member in task.get("expected_ids") or []:
        item = by_id.get(str(member))
        if item is None or sp.normalize_relation(item.get("relation")) != sp.IN_SCOPE:
            return (
                f"{task_id} carries `{member}` without a bound in-scope verdict. "
                f"{recovery}."
            )
    return None


# ---------------------------------------------------------------------------
# A policy change between materializations (plan §5, "Resume")
# ---------------------------------------------------------------------------


@dataclass
class PolicyChange:
    """What an earlier materialization of this review means for this run."""

    previous: str
    current: str
    #: Member ids an earlier run of this review landed (applied, no-op or
    #: skipped records): kept, never dispatched again.
    landed: List[str]
    #: Member ids of a batch that did not finish (``failed`` records).
    unsettled: List[str]
    #: The first batch index past every earlier batch, so new work never takes
    #: a completed batch's id.
    next_index: int
    previous_task_file: Optional[str]


def _batch_number(task_id: str) -> Optional[int]:
    tail = str(task_id or "").rsplit("-", 1)[-1]
    return int(tail) if tail.isdigit() else None


def detect_policy_change(
    phase_dir: str, *, current_policy: str, review_stamp: str,
    processed: Mapping[str, Any],
) -> Optional[PolicyChange]:
    """The change, when ``{phase}/write_tasks.json`` holds this review's tasks
    materialized under another policy; ``None`` otherwise (no file, another
    review, or the same policy)."""
    path = os.path.join(phase_dir, "write_tasks.json")
    try:
        with open(path, encoding="utf-8") as handle:
            document = json.load(handle)
    except (OSError, ValueError):
        return None
    if not isinstance(document, dict):
        return None
    tasks = [t for t in document.get("batches") or document.get("tasks") or []
             if isinstance(t, dict)]
    if not tasks:
        return None
    inputs = document.get("inputs") if isinstance(document.get("inputs"), dict) else {}
    stamp = str(inputs.get("grouped_sha256") or "")
    if review_stamp and stamp and stamp != review_stamp:
        return None
    previous = task_policy(tasks[0])
    if previous == sp.effective(current_policy):
        return None
    landed: List[str] = []
    unsettled: List[str] = []
    indices: List[int] = [int(t.get("batch_index", 0)) for t in tasks]
    for item_id, record in (processed or {}).items():
        if not isinstance(record, Mapping):
            continue
        details = record.get("details") if isinstance(record.get("details"), Mapping) else {}
        record_stamp = str(details.get("grouped_sha256") or "")
        if review_stamp and record_stamp and record_stamp != review_stamp:
            continue
        number = _batch_number(str(details.get("task_id") or ""))
        if number is not None:
            indices.append(number)
        status = record.get("status")
        if status == "failed":
            unsettled.append(str(item_id))
        elif status != "declined":
            # Applied, no-op, or skipped at the user's request: kept. A batch's
            # decline is reconsidered under the new policy (the writer may have
            # declined it because only an expansion would do).
            landed.append(str(item_id))
    return PolicyChange(
        previous=previous, current=sp.effective(current_policy),
        landed=landed, unsettled=unsettled,
        next_index=(max(indices) + 1) if indices else 0,
        previous_task_file=path,
    )


def retire_task_file(change: PolicyChange) -> Optional[str]:
    """Keep the obsolete task file aside (never deleted); the new name."""
    path = change.previous_task_file
    if not path or not os.path.isfile(path):
        return None
    with open(path, "rb") as handle:
        digest = hashlib.sha256(handle.read()).hexdigest()[:8]
    target = os.path.join(
        os.path.dirname(path), f"write_tasks.retired-{change.previous}-{digest}.json")
    os.replace(path, target)
    return target


def unsettled_refusal(change: PolicyChange, *, mode_word: str) -> List[str]:
    """The exit-3 lines for a policy change over a batch that did not finish."""
    shown = ", ".join(change.unsettled[:5]) + (
        f" (+{len(change.unsettled) - 5} more)" if len(change.unsettled) > 5 else "")
    return [
        f"{RETIRED_MARKER} {mode_word}: this review's tasks were materialized under "
        f"{sp.FLAG} {change.previous} and this run's policy is {change.current}, but "
        f"a batch of the earlier run did not finish ({shown}); rebuilding the "
        f"batches now could apply its half-applied items again. Nothing was "
        f"changed.",
        f"  1) Settle it first: re-run {mode_word} with --resume {sp.FLAG} "
        f"{change.previous}, or restore its pre-batch snapshot with util "
        f"restore-batch, then run {mode_word} {sp.FLAG} {change.current} again.",
        f"  2) Or start a fresh review of the current artifact under {sp.FLAG} "
        f"{change.current}.",
    ]


# ---------------------------------------------------------------------------
# Completion and blockers
# ---------------------------------------------------------------------------


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def blockers_from_processed(processed: Mapping[str, Any], review_stamp: str = "") -> List[Dict[str, Any]]:
    """Declined items whose reason starts with :data:`BLOCKER_PREFIX`."""
    found: List[Dict[str, Any]] = []
    for item_id, record in (processed or {}).items():
        if not isinstance(record, Mapping) or record.get("status") != "declined":
            continue
        details = record.get("details") if isinstance(record.get("details"), Mapping) else {}
        stamp = str(details.get("grouped_sha256") or "")
        if review_stamp and stamp and stamp != review_stamp:
            continue
        reason = str(details.get("reason") or "").strip()
        if reason.upper().startswith(BLOCKER_PREFIX):
            found.append({
                "group_id": str(item_id),
                "task_id": str(details.get("task_id") or ""),
                "reason": sp.flatten_text(reason[len(BLOCKER_PREFIX):].strip()
                                          or reason, sp.REASON_LIMIT),
            })
    return found


def record_completion(state: Dict[str, Any], phase: str, applied: Optional[ApplyPolicy],
                      blockers: Sequence[Mapping[str, Any]] = ()) -> Optional[Dict[str, Any]]:
    """Write the round's completion outcome; the record, or ``None`` when there
    is nothing to say (no deferrals, no blockers: an ordinary completion).

    ``eligible work completed`` keeps the deferrals beside it, so a bounded
    apply that left optional extensions deferred is finished, not owed work;
    ``blocked`` names the blockers dependent phases must not build past.
    """
    record = sp.round_record(state, phase)
    if record is None:
        return None
    table = state[sp.STATE_KEY][sp.review_phase_of(phase)]
    deferrals = list(table.get("deferrals") or [])
    if blockers:
        table[BLOCKERS_KEY] = [dict(b) for b in blockers]
    else:
        table.pop(BLOCKERS_KEY, None)
    if not deferrals and not blockers:
        table.pop(COMPLETION_KEY, None)
        return None
    outcome = {
        "outcome": OUTCOME_BLOCKED if blockers else OUTCOME_ELIGIBLE_DONE,
        "policy": applied.policy if applied else sp.effective(
            table.get("apply_policy") or table.get("review_policy")),
        "deferred": len(deferrals),
        "blockers": len(blockers),
        "at": _now(),
    }
    table[COMPLETION_KEY] = outcome
    return outcome


def recorded_blockers(state: Mapping[str, Any], phase: str) -> List[Dict[str, Any]]:
    """The blockers the round's last completion recorded (none when a later run cleared them).

    An apply phase's only: the record is keyed by the review round, but a
    blocker is the apply's outcome, so a review phase (or an unknown word)
    never reads as blocked — the apply that must run again to clear it
    would otherwise refuse its own prerequisite.
    """
    if sp.review_phase_of(phase) == phase:
        return []
    record = sp.round_record(state, phase) or {}
    completion = record.get(COMPLETION_KEY)
    if not isinstance(completion, Mapping) or completion.get("outcome") != OUTCOME_BLOCKED:
        return []
    return [dict(b) for b in record.get(BLOCKERS_KEY) or [] if isinstance(b, Mapping)]


def recorded_deferrals(state: Mapping[str, Any], phase: str) -> List[Dict[str, Any]]:
    """The round's open deferrals (``[]`` for a legacy round)."""
    return list(sp.round_policies(state, phase)["deferrals"])


def releases_deferrals(state: Mapping[str, Any], phase: str, chosen: Any) -> bool:
    """Whether the user's ``expand`` would offer the round's remaining scope work again.

    The predicate an "already complete" guard asks (plan §4: a completed
    ``preserve`` apply that still has deferrals, or stopped on a scope
    blocker, is not complete for an ``expand`` override). *chosen* is the
    user's choice for this run: the typed flag, or a composite's/full's live
    recorded choice, so the override survives a later run that omits it.
    Deferrals and blockers only come from a ``preserve`` apply, so ``expand``
    is the one policy that releases them; omission never releases anything.
    """
    if sp.review_phase_of(phase) == phase:
        return False  # a review phase (or an unknown word): never an apply's guard
    if sp.normalize_policy(chosen) != sp.POLICY_EXPAND:
        return False
    return bool(recorded_deferrals(state, phase) or recorded_blockers(state, phase))


def blocker_lines(blockers: Sequence[Mapping[str, Any]], *, mode_word: str) -> List[str]:
    lines = []
    for blocker in blockers:
        lines.append(
            f"{BLOCKER_MARKER} {mode_word}: {blocker.get('group_id')} "
            f"({blocker.get('task_id') or 'batch'}) cannot be completed within the "
            f"agreed scope: {blocker.get('reason')}"
        )
    if blockers:
        lines.append(
            f"  The agreed goal is not complete. Decide the scope question: amend the "
            f"plan and start a fresh review, or apply with {sp.FLAG} expand."
        )
    return lines


def blocker_error(blockers: Sequence[Mapping[str, Any]], *, mode_word: str) -> str:
    first = blockers[0] if blockers else {}
    more = f" (+{len(blockers) - 1} more)" if len(blockers) > 1 else ""
    return (
        f"{mode_word} stopped on a scope blocker: {first.get('group_id')} cannot be "
        f"completed within the agreed scope ({first.get('reason')}){more}. Amend the "
        f"plan and start a fresh review, or apply with {sp.FLAG} expand."
    )


__all__ = [
    "ApplyPolicy", "BLOCKERS_KEY", "BLOCKER_MARKER", "BLOCKER_PREFIX",
    "COMPLETION_KEY", "DEFERRED_MARKER", "ITEM_KEY", "OUTCOME_BLOCKED",
    "OUTCOME_ELIGIBLE_DONE", "OUTPUT_KEY", "PolicyChange", "RETIRED_MARKER",
    "TASK_KEY", "annotate_item", "blocker_error", "blocker_lines",
    "blockers_from_processed", "deferral_entry", "deferral_note",
    "detect_policy_change", "effective_from_state", "gate", "group_title",
    "invalid_policy_message", "output_block", "persist_deferrals",
    "record_completion", "recorded_blockers", "recorded_deferrals",
    "releases_deferrals", "resolve_apply_policy", "retire_task_file",
    "selected_remedy", "stale_task_refusal", "task_block", "task_policy",
    "unsettled_refusal", "writer_block",
]
