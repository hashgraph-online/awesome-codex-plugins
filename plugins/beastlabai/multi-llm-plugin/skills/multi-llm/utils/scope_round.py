"""The review side of the scope policy: one round's policy, baseline and verdicts.

``utils/scope_policy.py`` owns the vocabulary, the prompt blocks and the gate.
This module is the glue the review orchestrators and the validation merge
share (plans/scope-policy-and-report-tags.md §2, §3.1 and §4):

* **resolution** — a review round's policy is the explicit flag, else (for a
  same-round resume, reaggregate or revalidation) the round's recorded
  ``review_policy``, else ``expand``. An explicit policy that differs from the
  one an unfinished round's reviewers were asked under is refused (exit 3),
  never mixed into the same round;
* **the baseline** — built by host hash from the inputs the round already
  binds (the plan snapshot, the task list, a commit review's pinned endpoints
  and frozen context plan), recorded once per round in ``state.json``;
* **the task-file scope block** — the policy and the baseline the validators
  of one materialized round were given, which the merge stamps each hash-joined
  verdict with (the validators' own baseline, never a later one);
* **the validation-stage decision** — under an effective ``preserve`` each
  validated group gets ``scope_policy_decision`` (``scope_policy.scope_decision``)
  and the round's counts are recorded; under ``expand`` nothing is decided.

Import-light and side-effect free; the only I/O is in the functions that say so.
"""

from __future__ import annotations

import hashlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

try:
    from . import scope_policy as sp
except ImportError:  # pragma: no cover - script-style import
    from utils import scope_policy as sp  # type: ignore

#: The task-file key holding one validation round's scope block.
TASK_SCOPE_KEY = "scope"

#: Primary-document roles: the document whose bytes a validator's first
#: context block carries (a plan, or a commit review's brief).
PRIMARY_ROLES = ("plan", "commit_brief")

#: The ``validation.json`` metadata key with the round's decision counts.
DECISIONS_METADATA_KEY = "scope_policy_decisions"

#: The exit code a refused policy change uses (the uniform "needs a human").
EXIT_NEEDS_HUMAN = 3


def explicit_policy(args: Any) -> Optional[str]:
    """This invocation's ``--scope-policy`` (``None`` when omitted or invalid).

    The flag's parser (and its exit-3 refusal of an invalid value) belongs to
    the shared CLI helpers; this only reads the namespace.
    """
    return sp.normalize_policy(getattr(args, sp.DEST, None))


def guidance_phase(phase: str, *, commit_review: bool = False) -> str:
    """The ``scope_policy`` prompt phase for a review phase name."""
    if commit_review:
        return "commits"
    return sp.review_phase_of(phase)


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RoundPolicy:
    """The effective reviewer/validator policy of one review round."""

    policy: str
    source: str
    #: True when this invocation starts a new round (and records it).
    new_round: bool
    #: The round's recorded baseline id, when there is one.
    baseline_id: Optional[str] = None
    #: One line to print with the round's policy line (``print_round_line``).
    notice: Optional[str] = None


class PolicyConflict(Exception):
    """An explicit policy differs from the one an unfinished round was asked under."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
        self.exit_code = EXIT_NEEDS_HUMAN


def conflict_message(phase: str, recorded: str, requested: str, *,
                     forced_reuse: bool = False) -> str:
    """The exit-3 message naming the new-round control (and the apply override)."""
    flag = sp.FLAG
    if forced_reuse:
        what = (
            f"this forced {phase} round would reuse reviewer results requested "
            f"under scope policy `{recorded}` while asking for `{requested}`"
        )
        fix = (
            f"Add --rerun-all to re-run every reviewer under `{requested}` (a "
            f"fresh round), or pass {flag} {recorded} to keep the existing results."
        )
    else:
        what = (
            f"this {phase} round's reviewers were asked under scope policy "
            f"`{recorded}`, and this invocation asks for `{requested}`"
        )
        fix = (
            f"Omit {flag} to continue this round under `{recorded}`; start a new "
            f"review round with --force --rerun-all {flag} {requested}; or keep "
            f"this review and change only what is applied with the apply phase's "
            f"{flag}."
        )
    return (
        f"[SCOPE_POLICY_CONFLICT] {what}. Reviewer outputs requested under "
        f"different policies are never mixed in one round. {fix}"
    )


def forced_reuse_notice(phase: str, recorded: str) -> str:
    """The notice of a ``--force`` round that keeps its reused results' policy."""
    return (
        f"Scope policy notice: the {phase} reviewer results this --force run "
        f"reuses were requested under `{recorded}`, so it continues under "
        f"`{recorded}`. --force --rerun-all starts a fresh round under the "
        f"default `{sp.DEFAULT_POLICY}` (or the {sp.FLAG} you pass)."
    )


def resolve_review_round(
    state: Mapping[str, Any],
    phase: str,
    explicit: Any,
    *,
    force: bool = False,
    has_results: bool = False,
    rerun_all: bool = False,
    same_round: bool = False,
) -> RoundPolicy:
    """The policy one review invocation runs its reviewers and validators under.

    Args:
        state: The raw ``state.json`` dict (``StateManager.state``).
        phase: The review phase (``review-plan``, ``review-tasks``,
            ``code-review``).
        explicit: This invocation's ``--scope-policy`` value, or ``None``.
        force: A ``--force`` fan-out: the existing new-round control.
        has_results: Any reviewer results from this round are on disk,
            including reviewers not selected for this invocation.
        rerun_all: ``--rerun-all``: no existing reviewer result is reused.
        same_round: A reaggregate or revalidation, which by definition belongs
            to the round on record.

    A ``--force`` run without ``--rerun-all`` that reuses results requested
    under another policy keeps that policy when none is typed (with a
    ``notice``), and is refused when a different one is.

    Raises:
        PolicyConflict: an explicit policy differs from the round's on a
            continuation that would mix reviewer outputs (exit 3).
    """
    requested = sp.normalize_policy(explicit)
    record = sp.round_record(state, phase)
    recorded: Optional[str] = None
    recorded_source = sp.SOURCE_REVIEW
    if record is not None:
        recorded = sp.normalize_policy(record.get("review_policy")) or sp.DEFAULT_POLICY
    elif has_results or same_round:
        # Results (or a round) from before the policy existed: legacy = expand.
        recorded = sp.DEFAULT_POLICY
        recorded_source = sp.SOURCE_LEGACY
    baseline_id = sp.baseline_id_of((record or {}).get("baseline"))

    continuing = same_round or (not force and (record is not None or has_results))
    if continuing and recorded is not None:
        if requested and requested != recorded:
            if same_round or has_results:
                raise PolicyConflict(conflict_message(sp.review_phase_of(phase), recorded, requested))
            # Nothing was reviewed yet under the old record: a fresh round.
            return RoundPolicy(requested, sp.SOURCE_EXPLICIT, True)
        return RoundPolicy(recorded, recorded_source, False, baseline_id)

    policy, source = sp.resolve_policy(explicit=requested)
    if force and has_results and not rerun_all and recorded is not None and policy != recorded:
        if requested:
            raise PolicyConflict(conflict_message(
                sp.review_phase_of(phase), recorded, policy, forced_reuse=True,
            ))
        # Nothing typed: the round keeps the policy of the results it reuses.
        return RoundPolicy(recorded, sp.SOURCE_REVIEW, True,
                           notice=forced_reuse_notice(sp.review_phase_of(phase), recorded))
    return RoundPolicy(policy, source, True)


def record_round(state_manager: Any, phase: str, round_policy: RoundPolicy,
                 baseline: Optional[Mapping[str, Any]]) -> Optional[str]:
    """Record the round in ``state.json`` (I/O: saves the state file).

    A new round replaces the record (``record_review_round``); a continuation
    only attaches a baseline the round does not have yet
    (``update_round_baseline``: first binding wins, never rebased). Returns the
    round's baseline id as recorded. Never raises: a state file that cannot be
    written leaves the round unrecorded and is reported.
    """
    state = getattr(state_manager, "state", None)
    if not isinstance(state, dict):
        return sp.baseline_id_of(baseline)
    if round_policy.new_round:
        sp.record_review_round(state, phase, round_policy.policy, round_policy.source, baseline)
    elif baseline:
        sp.update_round_baseline(state, phase, baseline)
    elif sp.round_record(state, phase) is None:
        # A legacy round without a baseline still gets its (expand) record.
        state.setdefault(sp.STATE_KEY, {})[sp.review_phase_of(phase)] = {
            "review_policy": round_policy.policy,
            "review_policy_source": round_policy.source,
            "recorded_at": sp._now(),
        }
    try:
        state_manager.save()
    except Exception as exc:  # noqa: BLE001 - a record must not fail the phase
        print(f"Warning: could not record the scope-policy round: {exc}", file=sys.stderr)
    record = sp.round_record(state, phase) or {}
    return sp.baseline_id_of(record.get("baseline"))


def round_baseline(state: Mapping[str, Any], phase: str) -> Optional[Dict[str, Any]]:
    """The round's recorded baseline record, if any."""
    record = sp.round_record(state, phase) or {}
    baseline = record.get("baseline")
    return dict(baseline) if isinstance(baseline, Mapping) else None


def print_round_line(phase: str, round_policy: RoundPolicy) -> None:
    """One informational line naming the round's policy and where it came from
    (followed by the round's ``notice``, when it has one)."""
    origin = "new round" if round_policy.new_round else "this round's record"
    print(f"Scope policy: {round_policy.policy} ({round_policy.source}; {origin})")
    if round_policy.notice:
        print(round_policy.notice)


# ---------------------------------------------------------------------------
# Baselines
# ---------------------------------------------------------------------------


def _bytes_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_source(role: str, path: Optional[str], *, snapshot: Optional[str] = None,
                data: Optional[bytes] = None) -> Optional[Dict[str, Any]]:
    """A baseline source for a file read now (``None`` when there is no path)."""
    if not path and data is None:
        return None
    digest: Optional[str] = None
    if data is None:
        try:
            data = Path(str(path)).read_bytes()
        except OSError:
            data = None
    if data is not None:
        digest = _bytes_sha256(data)
    return sp.baseline_source(role, sha256=digest, path=path, snapshot=snapshot)


def endpoints_source(role: str, endpoints: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
    """A baseline source naming a pinned range by its endpoints.

    ``sha256`` is the hash of the endpoint pair itself, so the source is
    readable by construction: what it pins is the range, not any one file.
    """
    pair = {str(k): str(v) for k, v in endpoints.items() if v}
    if not pair:
        return None
    text = "..".join(pair.get(key, "") for key in ("base", "head"))
    return sp.baseline_source(role, sha256=_bytes_sha256(text.encode("utf-8")),
                              endpoints=pair)


def build_round_baseline(
    phase: str,
    *,
    plan_document: Any = None,
    plan_path: Optional[str] = None,
    tasks_path: Optional[str] = None,
    tasks_document: Any = None,
    primary_role: str = "plan",
    extra_sources: Iterable[Optional[Mapping[str, Any]]] = (),
) -> Dict[str, Any]:
    """The baseline record for one review round, from the inputs it binds.

    ``plan_document`` is the round's bound plan (a ``BoundDocument``; its
    snapshot is ``validation-snapshot.md``); without one the plan file is
    hashed as read now. ``tasks_document``/``tasks_path`` is the task list
    (review-tasks: the artifact the plan constrains; code-review: evidence).
    """
    sources: List[Dict[str, Any]] = []
    if plan_document is not None:
        sources.append(sp.baseline_source_from_document(plan_document, primary_role))
    elif plan_path:
        source = file_source(primary_role, plan_path)
        if source:
            sources.append(source)
    if tasks_document is not None:
        sources.append(sp.baseline_source_from_document(tasks_document, "tasks"))
    elif tasks_path:
        source = file_source("tasks", tasks_path)
        if source:
            sources.append(source)
    for source in extra_sources:
        if source:
            sources.append(dict(source))
    return sp.build_baseline(sources, phase=sp.review_phase_of(phase))


def validators_baseline(
    phase: str,
    recorded: Optional[Mapping[str, Any]],
    *,
    plan_document: Any = None,
    tasks_document: Any = None,
) -> Dict[str, Any]:
    """The baseline the validators of a materialized round are really shown.

    The round's recorded baseline with each source the validation prompts
    embed re-hashed from the bytes they embed: the primary document from
    ``plan_document``, the task list from ``tasks_document``. Unchanged inputs
    give the round's own id; a document that changed since the round began
    gives a different id, so its verdicts can never be mistaken for the
    round's (they read ``other-baseline``, i.e. unclear). With no recorded
    baseline (a legacy round) the documents alone make it.
    """
    if not isinstance(recorded, Mapping) or not recorded.get("sources"):
        return build_round_baseline(phase, plan_document=plan_document,
                                    tasks_document=tasks_document)
    sources: List[Dict[str, Any]] = []
    for source in recorded.get("sources") or []:
        if not isinstance(source, Mapping):
            continue
        role = str(source.get("role") or "")
        document = None
        if role in PRIMARY_ROLES:
            document = plan_document
        elif role == "tasks":
            document = tasks_document
        if document is not None and getattr(document, "sha256", None):
            fresh = sp.baseline_source_from_document(document, role)
            if source.get("endpoints"):
                fresh["endpoints"] = dict(source["endpoints"])
            sources.append(fresh)
        else:
            sources.append(dict(source))
    return sp.build_baseline(sources, phase=str(recorded.get("phase") or sp.review_phase_of(phase)))


def code_review_extra_sources(state: Any, *, base_ref: Optional[str],
                              head_ref: Optional[str] = None) -> List[Dict[str, Any]]:
    """The pinned-range and frozen-context-plan sources of a code/commit review."""
    getter = getattr(state, "get", None)
    record = getter("commit_range") if callable(getter) else None
    sources: List[Dict[str, Any]] = []
    if isinstance(record, Mapping):
        endpoints = endpoints_source(
            "commit_messages", {"base": record.get("base"), "head": record.get("head")}
        )
        if endpoints:
            sources.append(endpoints)
        digest = record.get("plan_sha256")
        if isinstance(digest, str) and digest:
            sources.append(sp.baseline_source(
                "context_plan", sha256=digest,
                snapshot=record.get("plan_snapshot") or None,
            ))
        focus = record.get("focus")
        if isinstance(focus, str) and focus.strip():
            sources.append(sp.baseline_source(
                "focus", sha256=_bytes_sha256(focus.strip().encode("utf-8")),
            ))
        return sources
    endpoints = endpoints_source("diff", {"base": base_ref, "head": head_ref})
    if endpoints:
        sources.append(endpoints)
    return sources


# ---------------------------------------------------------------------------
# The task-file scope block
# ---------------------------------------------------------------------------


def scope_block(
    policy: Any,
    phase: str,
    *,
    source: Optional[str] = None,
    baseline: Optional[Mapping[str, Any]] = None,
    round_baseline_id: Optional[str] = None,
    revalidation_baseline_differs: bool = False,
) -> Dict[str, Any]:
    """The ``scope`` block a validation/revalidation task file records.

    ``baseline`` is what the validators were shown; ``round_baseline_id`` the
    round's own, which the validation-stage decision is judged against.
    """
    baseline_id = sp.baseline_id_of(baseline)
    return {
        "policy": sp.effective(policy),
        "policy_source": source or sp.SOURCE_DEFAULT,
        "phase": phase,
        "baseline_id": baseline_id,
        "round_baseline_id": round_baseline_id or baseline_id,
        **({"baseline": dict(baseline)} if baseline else {}),
        **({"revalidation_baseline_differs": True} if revalidation_baseline_differs else {}),
    }


def task_scope(document: Any) -> Dict[str, Any]:
    """A task file's scope block, or the legacy reading (``expand``, unbound)."""
    block = document.get(TASK_SCOPE_KEY) if isinstance(document, Mapping) else None
    if not isinstance(block, Mapping):
        return {"policy": sp.DEFAULT_POLICY, "policy_source": sp.SOURCE_LEGACY,
                "baseline_id": None, "round_baseline_id": None, "legacy": True}
    return dict(block)


def validation_metadata(block: Mapping[str, Any],
                        decisions: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """The ``validation.json`` metadata keys recording a round's policy and baseline."""
    meta: Dict[str, Any] = {
        "scope_policy": sp.effective(block.get("policy")),
        "scope_policy_source": block.get("policy_source") or sp.SOURCE_DEFAULT,
        "scope_baseline_id": block.get("baseline_id"),
        "scope_round_baseline_id": block.get("round_baseline_id") or block.get("baseline_id"),
    }
    if decisions:
        meta[DECISIONS_METADATA_KEY] = dict(decisions)
    return meta


# ---------------------------------------------------------------------------
# Verdicts: stamping and attaching
# ---------------------------------------------------------------------------

#: Host-stamped record keys a model reply may never supply.
STAMP_KEYS = (sp.BASELINE_ID_FIELD, sp.PROPOSAL_DIGEST_FIELD, "scope_source", "scope_missing")

#: Every scope key a validation record may carry, in save order.
RECORD_SCOPE_KEYS = (
    sp.RELATION_FIELD, sp.REASON_FIELD, sp.REFERENCE_FIELD, sp.SELECTED_REMEDY_FIELD,
    sp.BASELINE_ID_FIELD, sp.PROPOSAL_DIGEST_FIELD, "scope_source", "scope_missing",
    sp.DECISION_KEY,
)


def unbound_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """``record`` (in place) with no scope authority: stamps dropped, fields normalized.

    For a verdict that did not join by hash (an index fallback, a placeholder)
    or a merge with no host groups to bind against. A model-supplied digest or
    baseline id is never kept, so nothing downstream can read it as stamped.
    """
    for key in STAMP_KEYS:
        record.pop(key, None)
    record.pop(sp.SELECTED_REMEDY_FIELD, None)
    record.pop(sp.DECISION_KEY, None)
    if sp.has_scope_fields(record):
        record.update(sp.normalize_scope_fields(record))
    return record


def stamp(record: Dict[str, Any], group: Mapping[str, Any], block: Mapping[str, Any],
          *, source: str = "validation") -> Dict[str, Any]:
    """``record`` stamped against the host's ``group`` under the task's scope block.

    ``group`` must be the host's own copy (the one whose stable hash the
    record joined on), never anything the reply carried.
    """
    policy = sp.effective(block.get("policy"))
    return sp.stamp_validation_record(
        record, group,
        baseline_id=block.get("baseline_id"),
        source=source,
        allow_selected_remedy=(policy == sp.POLICY_PRESERVE),
    )


def group_dict(group: Any) -> Dict[str, Any]:
    return group.to_dict() if hasattr(group, "to_dict") else dict(group)


def groups_by_hash(groups: Optional[Sequence[Any]]) -> Dict[str, Dict[str, Any]]:
    """``{stable group id: host group}`` for a list of groups."""
    if not groups:
        return {}
    try:
        from .state_manager import generate_group_id
    except ImportError:  # pragma: no cover
        from utils.state_manager import generate_group_id  # type: ignore
    table: Dict[str, Dict[str, Any]] = {}
    for group in groups:
        data = group_dict(group)
        table.setdefault(generate_group_id(data), data)
    return table


# ---------------------------------------------------------------------------
# The validation-stage decision (preserve only)
# ---------------------------------------------------------------------------


def annotate_decisions(
    groups: Optional[List[Dict[str, Any]]],
    policy: Any,
    baseline_id: Optional[str],
) -> Optional[Dict[str, int]]:
    """Under ``preserve``, put ``scope_policy_decision`` on each validated group.

    Validity is untouched: a ``valid`` group stays ``valid`` and keeps its tag;
    the decision is a separate outcome. Only groups whose validation reached a
    verdict about the finding (``valid``, ``needs-human-decision``) count as
    deferrals; an ``invalid`` group gets its decision for display but is not a
    deferral. A ``validation_failed`` group reached no verdict at all: it gets
    no decision (its way out is a revalidation, not a scope choice) and is not
    counted. Under ``expand`` nothing is stored and ``None`` is returned.
    """
    if sp.effective(policy) != sp.POLICY_PRESERVE or not groups:
        return None
    counts = {"eligible": 0, "deferred": 0, sp.IN_SCOPE: 0, sp.SCOPE_EXTENSION: 0, sp.UNCLEAR: 0}
    for group in groups:
        if not isinstance(group, dict):
            continue
        status = group.get("validation_status")
        if status == "validation_failed":
            group.pop(sp.DECISION_KEY, None)
            continue
        decision = sp.scope_decision(group, sp.POLICY_PRESERVE, baseline_id)
        group[sp.DECISION_KEY] = decision.to_dict()
        if status == "invalid":
            continue
        counts["eligible" if decision.eligible else "deferred"] += 1
        counts[decision.relation] += 1
    return counts


def decisions_line(counts: Optional[Mapping[str, int]]) -> Optional[str]:
    """The summary line for a preserve round's validation-stage decisions."""
    if not counts:
        return None
    return (
        f"[SCOPE_POLICY] preserve: {counts.get('deferred', 0)} validated group(s) "
        f"deferred by scope policy ({counts.get(sp.SCOPE_EXTENSION, 0)} scope "
        f"extension, {counts.get(sp.UNCLEAR, 0)} unclear), "
        f"{counts.get('eligible', 0)} within scope. Validity is unchanged; "
        f"deferred findings stay in the report."
    )


def record_decisions(phase_dir: Optional[str], counts: Optional[Mapping[str, int]]) -> None:
    """Print the decision line and record the counts in ``.status.json`` (I/O)."""
    line = decisions_line(counts)
    if line:
        print(line)
    if not phase_dir:
        return
    try:
        from .status_file import remove_status_keys, update_status
    except ImportError:  # pragma: no cover
        from utils.status_file import remove_status_keys, update_status  # type: ignore
    try:
        if counts:
            update_status(str(phase_dir), {DECISIONS_METADATA_KEY: dict(counts)})
        elif os.path.exists(os.path.join(str(phase_dir), ".status.json")):
            remove_status_keys(str(phase_dir), [DECISIONS_METADATA_KEY])
    except Exception:  # noqa: BLE001 - a status note never fails the phase
        pass


def attach_verdicts(groups: Optional[List[Dict[str, Any]]],
                    records: Optional[Sequence[Mapping[str, Any]]]) -> None:
    """Attach stamped verdicts to ``groups`` (in place) by stable hash only.

    For report inputs built outside :func:`utils.validation.apply_validation_to_groups`
    (consolidation reads ``grouped.json`` and ``validation.json`` itself). A
    group whose hash no record carries has any verdict removed.
    """
    if not groups:
        return
    try:
        from .state_manager import generate_group_id
    except ImportError:  # pragma: no cover
        from utils.state_manager import generate_group_id  # type: ignore
    by_hash = {
        r.get("group_id") or r.get("group_hash"): r
        for r in records or [] if isinstance(r, Mapping) and (r.get("group_id") or r.get("group_hash"))
    }
    for group in groups:
        if not isinstance(group, dict):
            continue
        record = by_hash.get(generate_group_id(group))
        sp.attach_verdict(group, record, hash_matched=record is not None)


__all__ = [
    "DECISIONS_METADATA_KEY", "EXIT_NEEDS_HUMAN", "PolicyConflict", "PRIMARY_ROLES",
    "RECORD_SCOPE_KEYS", "RoundPolicy", "STAMP_KEYS", "TASK_SCOPE_KEY",
    "annotate_decisions", "attach_verdicts", "build_round_baseline",
    "code_review_extra_sources", "conflict_message", "decisions_line",
    "endpoints_source", "explicit_policy", "file_source", "groups_by_hash",
    "guidance_phase", "print_round_line", "record_decisions", "record_round",
    "resolve_review_round", "round_baseline", "scope_block", "stamp",
    "task_scope", "unbound_record", "validation_metadata", "validators_baseline",
]
