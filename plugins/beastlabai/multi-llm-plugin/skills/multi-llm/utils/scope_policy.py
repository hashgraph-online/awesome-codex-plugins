"""Scope policy and scope classification: the one shared contract.

``--scope-policy {expand,preserve}`` decides whether a review round may carry
remedies that extend the agreed scope (plans/scope-policy-and-report-tags.md).
``expand`` is the default and keeps every existing review, validation, judge,
selection and application decision; under it a scope tag is a report label
and nothing else. Only an effective ``preserve`` policy adds reviewer
suppression, validator rejection and the pre-write gate.

This module owns, for every caller:

* the vocabulary: the two policies, the three relations, the three report
  labels and the policy-source words;
* normalization of model-written scope fields, which never raises and never
  drops the finding it sits on (anything malformed is ``unclear``);
* the scope baseline record (which inputs a round's scope is judged against,
  by hash) and the proposal digest (which exact remedy a verdict classified);
* scope authority: a group's validated verdict counts only while it is bound
  to the round's baseline and to the proposal as it stands now;
* eligibility: :func:`scope_decision` is the gate, a pass-through under
  ``expand``;
* the role- and policy-specific prompt blocks, rendered per call and never
  cached, so an ``expand`` rendering can never be served to a ``preserve``
  run;
* policy resolution and the per-review-round ``state.json`` record;
* the report vocabulary (labels, legend, policy line, flattened reasons).

Pure and import-light: no I/O, no model calls, no argparse. Stable group and
suggestion IDs never include anything defined here.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------

POLICY_EXPAND = "expand"
POLICY_PRESERVE = "preserve"
#: The accepted ``--scope-policy`` values, in help order.
POLICIES: Tuple[str, ...] = (POLICY_EXPAND, POLICY_PRESERVE)
#: A genuinely new run without a choice, and every legacy record.
DEFAULT_POLICY = POLICY_EXPAND

#: The CLI spelling, for help text, replay flags and messages.
FLAG = "--scope-policy"
#: The argparse ``dest``.
DEST = "scope_policy"

IN_SCOPE = "in_scope"
SCOPE_EXTENSION = "scope_extension"
UNCLEAR = "unclear"
RELATIONS: Tuple[str, ...] = (IN_SCOPE, SCOPE_EXTENSION, UNCLEAR)

#: The one set of textual labels every report uses (Markdown and HTML).
LABELS: Dict[str, str] = {
    IN_SCOPE: "Within scope",
    SCOPE_EXTENSION: "Scope extension",
    UNCLEAR: "Scope unclear",
}

#: Member-level (reviewer, provisional) fields; the same names a validator
#: reply uses for its authoritative group verdict.
RELATION_FIELD = "scope_relation"
REASON_FIELD = "scope_reason"
REFERENCE_FIELD = "scope_reference"
SCOPE_FIELDS: Tuple[str, ...] = (RELATION_FIELD, REASON_FIELD, REFERENCE_FIELD)
#: Validator reply field naming the one remedy it classified when a group's
#: members propose materially different ones (``preserve`` only).
SELECTED_REMEDY_FIELD = "selected_remedy"

#: Group-level key holding the authoritative, host-bound verdict
#: (:func:`make_verdict`). Never the members' provisional fields.
VERDICT_KEY = "scope_verdict"
#: Group-level key holding the derived policy decision (:func:`scope_decision`
#: as a dict). Recomputed at every gate; stored only for reports/results.
DECISION_KEY = "scope_policy_decision"
#: Validation-record keys the host stamps beside the model's scope fields.
BASELINE_ID_FIELD = "scope_baseline_id"
PROPOSAL_DIGEST_FIELD = "scope_proposal_digest"

#: Where a policy came from (resolution order of plan §4).
SOURCE_EXPLICIT = "explicit"          # this invocation's flag
SOURCE_CONTINUATION = "continuation"  # the apply/composite's recorded override
SOURCE_REVIEW = "review"              # the originating review round's record
SOURCE_WORKFLOW = "workflow"          # forwarded by a composite / full workflow
SOURCE_DEFAULT = "default"            # a new run without a choice
SOURCE_LEGACY = "legacy"              # a record that predates the policy
POLICY_SOURCES: Tuple[str, ...] = (
    SOURCE_EXPLICIT, SOURCE_CONTINUATION, SOURCE_REVIEW,
    SOURCE_WORKFLOW, SOURCE_DEFAULT, SOURCE_LEGACY,
)

#: The policy outcome shown beside a deferred item's tag.
DEFERRED_OUTCOME = "Deferred: scope preservation requested"
#: A deferral's recovery hint when no usable classification exists.
LEGACY_RECOVERY = (
    "run a fresh classified review, or apply with --scope-policy expand"
)

#: How long a model-written scope reason/reference may be once flattened.
REASON_LIMIT = 300
REFERENCE_LIMIT = 120
SELECTED_REMEDY_LIMIT = 600

#: Review phase that owns each apply phase's round (state record key).
REVIEW_PHASE_OF: Dict[str, str] = {
    "review-plan": "review-plan",
    "apply-suggestions": "review-plan",
    "review-tasks": "review-tasks",
    "apply-task-suggestions": "review-tasks",
    "code-review": "code-review",
    "review-code": "code-review",
    "apply-code-fixes": "code-review",
    "apply-fixes": "code-review",
}

#: ``state.json`` key holding the per-review-round policy records.
STATE_KEY = "scope_policy"


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

_RELATION_ALIASES: Dict[str, str] = {
    "in_scope": IN_SCOPE,
    "inscope": IN_SCOPE,
    "within_scope": IN_SCOPE,
    "within": IN_SCOPE,
    "scope_extension": SCOPE_EXTENSION,
    "extension": SCOPE_EXTENSION,
    "extends_scope": SCOPE_EXTENSION,
    "out_of_scope": SCOPE_EXTENSION,
    "unclear": UNCLEAR,
    "unknown": UNCLEAR,
    "uncertain": UNCLEAR,
}

_WS = re.compile(r"\s+")
# Characters with meaning at the start of a Markdown line or inside HTML.
_MD_LINE_START = re.compile(r"^(?:#+|[-*+]\s*\[[ xX]?\]|[-*+>]|\d+[.)])\s*")


def normalize_policy(value: Any) -> Optional[str]:
    """``value`` as one of :data:`POLICIES`, or ``None`` when absent or invalid.

    Case- and whitespace-insensitive. A caller that must refuse an invalid
    value (the decision-flag exit-3 contract) checks :func:`is_valid_policy`
    on the raw value first; this never raises.
    """
    if not isinstance(value, str):
        return None
    word = value.strip().lower()
    return word if word in POLICIES else None


def is_valid_policy(value: Any) -> bool:
    """True when ``value`` names a policy (``None`` is "not given", not valid)."""
    return normalize_policy(value) is not None


def normalize_relation(value: Any) -> str:
    """A model-written relation as one of :data:`RELATIONS`; anything else is unclear."""
    if not isinstance(value, str):
        return UNCLEAR
    key = _WS.sub("_", value.strip().lower().replace("-", "_"))
    return _RELATION_ALIASES.get(key, UNCLEAR)


def flatten_text(value: Any, limit: int = REASON_LIMIT) -> str:
    """Model-written text as one plain, bounded line safe in Markdown and HTML.

    Whitespace collapses to single spaces and control characters go
    (``text_clip.plain_line``), a leading heading/list/checkbox marker is
    removed so a reason can never become a heading or a checkbox, and the
    result is cut with ``text_clip.clip``. HTML escaping stays the renderer's
    job; this only guarantees one line.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    try:
        from .text_clip import clip, plain_line
    except ImportError:  # pragma: no cover - script-style import
        from utils.text_clip import clip, plain_line
    text = plain_line(value)
    previous = None
    while previous != text:
        previous = text
        text = _MD_LINE_START.sub("", text).strip()
    return clip(text, limit) if len(text) > limit else text


def normalize_scope_fields(record: Any) -> Dict[str, str]:
    """The scope fields of a reviewer finding or validator verdict, normalized.

    Returns ``{"scope_relation", "scope_reason", "scope_reference"}``. Missing,
    malformed or non-string values never raise and never affect the rest of the
    record: the relation degrades to ``unclear``. A definite relation without a
    reason is ``unclear`` too (plan §3: new classified verdicts need a reason).
    """
    if not isinstance(record, Mapping):
        return {RELATION_FIELD: UNCLEAR, REASON_FIELD: "", REFERENCE_FIELD: ""}
    relation = normalize_relation(record.get(RELATION_FIELD))
    reason = flatten_text(record.get(REASON_FIELD), REASON_LIMIT)
    reference = flatten_text(record.get(REFERENCE_FIELD), REFERENCE_LIMIT)
    if relation != UNCLEAR and not reason:
        relation = UNCLEAR
    return {RELATION_FIELD: relation, REASON_FIELD: reason, REFERENCE_FIELD: reference}


def has_scope_fields(record: Any) -> bool:
    """True when ``record`` carries any scope field at all (legacy records do not)."""
    return isinstance(record, Mapping) and any(k in record for k in SCOPE_FIELDS)


def label(relation: Any) -> str:
    """The report label for ``relation`` (unknown values read ``Scope unclear``)."""
    return LABELS[normalize_relation(relation)]


# ---------------------------------------------------------------------------
# Scope baseline
# ---------------------------------------------------------------------------

BASELINE_VERSION = 1


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def baseline_source(
    role: str,
    *,
    sha256: Optional[str],
    path: Optional[str] = None,
    snapshot: Optional[str] = None,
    endpoints: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """One input of a scope baseline.

    Args:
        role: What the input is to the scope question: ``plan``, ``tasks``,
            ``context_plan`` (a commit review's frozen plan), ``commit_brief``,
            ``commit_messages``, ``focus``, ``decisions``, ``diff``.
        sha256: The hash of the bytes the round read (a ``BoundDocument``'s).
            ``None`` means the input was not readable; the baseline then cannot
            settle scope questions that depend on it.
        path: The display path (plan-relative or repository-relative); never
            part of the identity.
        snapshot: The phase-dir snapshot name that holds those bytes.
        endpoints: Pinned endpoints for a commit range (``base``/``head``).
    """
    source: Dict[str, Any] = {"role": str(role), "sha256": sha256 or None}
    if path:
        source["path"] = str(path)
    if snapshot:
        source["snapshot"] = str(snapshot)
    if endpoints:
        source["endpoints"] = {str(k): v for k, v in endpoints.items() if v is not None}
    return source


def baseline_source_from_document(document: Any, role: Optional[str] = None,
                                  snapshot: Optional[str] = None) -> Dict[str, Any]:
    """:func:`baseline_source` for a ``validation.BoundDocument`` (duck-typed)."""
    import os

    path = getattr(document, "path", None)
    snap = snapshot
    if snap is None and path and getattr(document, "in_phase_dir", False):
        snap = os.path.basename(path)
    return baseline_source(
        role or str(getattr(document, "label", "") or "document"),
        sha256=getattr(document, "sha256", None),
        path=getattr(document, "source_path", None) or path,
        snapshot=snap,
    )


def build_baseline(sources: Iterable[Mapping[str, Any]], *, phase: str = "") -> Dict[str, Any]:
    """The scope baseline record for one review round.

    ``baseline_id`` is host-computed over each source's role, hash and pinned
    endpoints (sorted by role then hash), never over a display path, so the
    same inputs read from another checkout bind the same id. A round whose
    inputs differ is a different baseline.
    """
    cleaned = [dict(s) for s in sources if isinstance(s, Mapping) and s.get("role")]
    identity = sorted(
        (
            {
                "role": s.get("role"),
                "sha256": s.get("sha256"),
                "endpoints": s.get("endpoints") or {},
            }
            for s in cleaned
        ),
        key=lambda s: (str(s["role"]), str(s["sha256"])),
    )
    baseline_id = _sha256(_canonical({"v": BASELINE_VERSION, "sources": identity}))[:16]
    record: Dict[str, Any] = {
        "version": BASELINE_VERSION,
        "baseline_id": baseline_id,
        "sources": cleaned,
    }
    if phase:
        record["phase"] = phase
    return record


def baseline_id_of(baseline: Any) -> Optional[str]:
    """The id of a baseline record (or the string itself), else ``None``."""
    if isinstance(baseline, str):
        return baseline or None
    if isinstance(baseline, Mapping):
        value = baseline.get("baseline_id")
        return value if isinstance(value, str) and value else None
    return None


def baseline_unreadable_roles(baseline: Any) -> List[str]:
    """Roles of a baseline's sources that were not readable (no hash)."""
    if not isinstance(baseline, Mapping):
        return []
    return [
        str(s.get("role")) for s in baseline.get("sources") or []
        if isinstance(s, Mapping) and not s.get("sha256")
    ]


# ---------------------------------------------------------------------------
# Proposals: what a verdict classified, and what a writer is sent
# ---------------------------------------------------------------------------

#: Member fields that make up a proposed action. Identity, provenance and
#: scope fields are not part of it, so restamping IDs or adding tags never
#: invalidates a binding; an edited description or a removed member does.
_PROPOSAL_MEMBER_FIELDS: Tuple[str, ...] = (
    "title", "desc", "description", "details", "type", "reference", "section",
    "file", "line_range", "anchor_text", "suggested_fix",
)


def group_members(group: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    """A group's retained member records (``suggestions`` or ``issues``)."""
    members = group.get("suggestions")
    if members is None:
        members = group.get("issues")
    return [m for m in members or [] if isinstance(m, Mapping)]


def _member_proposal(member: Mapping[str, Any]) -> Dict[str, Any]:
    entry: Dict[str, Any] = {}
    for key in _PROPOSAL_MEMBER_FIELDS:
        value = member.get(key)
        if value in (None, "", [], {}):
            continue
        entry[key] = value
    # desc / description / details are one field to a writer.
    text = entry.pop("desc", None) or entry.pop("description", None) or entry.pop("details", None)
    entry.pop("description", None)
    entry.pop("details", None)
    if text is not None:
        entry["desc"] = text
    return entry


def selected_remedy_of(group: Mapping[str, Any]) -> Optional[str]:
    """The remedy a ``preserve`` validation selected for this group, if any."""
    verdict = group.get(VERDICT_KEY)
    if isinstance(verdict, Mapping):
        remedy = verdict.get(SELECTED_REMEDY_FIELD)
        if isinstance(remedy, str) and remedy.strip():
            return remedy.strip()
    return None


def proposal_payload(group: Mapping[str, Any]) -> Dict[str, Any]:
    """The group's complete proposed action, as the validator and writer see it.

    The theme plus every retained member's proposal fields, in member order.
    The one extraction both sides use (plan §3), so a validator never
    classifies one reading of a group while the writer is sent another.
    """
    return {
        "theme": str(group.get("theme", "") or ""),
        "members": [_member_proposal(m) for m in group_members(group)],
    }


def proposal_digest(group: Mapping[str, Any], selected_remedy: Optional[str] = None) -> str:
    """sha256 (hex) over :func:`proposal_payload` and any selected remedy.

    Unlike the stable group hash (which truncates descriptions), this covers
    every byte of every retained member's proposal, so an edit anywhere in a
    description, a per-member skip or a salvage rewrite changes it.
    """
    payload = proposal_payload(group)
    remedy = selected_remedy if selected_remedy is not None else selected_remedy_of(group)
    if remedy:
        payload = dict(payload, selected_remedy=remedy)
    return _sha256(_canonical(payload))


# ---------------------------------------------------------------------------
# Verdicts and authority
# ---------------------------------------------------------------------------


def make_verdict(
    record: Mapping[str, Any],
    group: Mapping[str, Any],
    *,
    baseline_id: Optional[str],
    source: str = "validation",
    allow_selected_remedy: bool = False,
) -> Dict[str, Any]:
    """The authoritative group verdict for a hash-joined validation record.

    ``record`` is one normalized validator result (its scope fields are read
    through :func:`normalize_scope_fields`); ``group`` is the group exactly as
    the validator was shown it. The host stamps the baseline id and the
    proposal digest itself: a model's echo of either is never trusted.
    ``allow_selected_remedy`` is set only for an effective ``preserve`` round
    (plan §3: remedy narrowing is preserve-only; under ``expand`` annotation
    never changes the remedy).
    """
    fields = normalize_scope_fields(record)
    remedy = None
    if allow_selected_remedy:
        raw = record.get(SELECTED_REMEDY_FIELD) if isinstance(record, Mapping) else None
        if isinstance(raw, str) and raw.strip():
            remedy = flatten_text(raw, SELECTED_REMEDY_LIMIT)
    verdict: Dict[str, Any] = {
        "relation": fields[RELATION_FIELD],
        "reason": fields[REASON_FIELD],
        "reference": fields[REFERENCE_FIELD],
        "baseline_id": baseline_id or None,
        "source": source,
    }
    if remedy:
        verdict[SELECTED_REMEDY_FIELD] = remedy
    verdict["proposal_digest"] = proposal_digest(group, selected_remedy=remedy)
    if not has_scope_fields(record):
        verdict["relation"] = UNCLEAR
        verdict["reason"] = ""
        verdict["missing"] = True
    return verdict


#: Host-stamped record keys (never trusted from a model reply).
_STAMP_KEYS = (BASELINE_ID_FIELD, PROPOSAL_DIGEST_FIELD, "scope_source", "scope_missing")


def stamp_validation_record(
    record: Mapping[str, Any],
    group: Mapping[str, Any],
    *,
    baseline_id: Optional[str],
    source: str = "validation",
    allow_selected_remedy: bool = False,
) -> Dict[str, Any]:
    """A validation result record with its scope fields normalized and bound.

    Called by the host when it merges a validator's reply, with ``group`` the
    group (from ``grouped.json``) whose hash the record joined on. The record's
    own scope fields are normalized (never raising, never dropping the
    verdict); any model-supplied ``scope_baseline_id``/``scope_proposal_digest``
    is discarded and replaced by the host's own values. ``selected_remedy``
    survives only when ``allow_selected_remedy`` (an effective ``preserve``).
    Everything else in ``record`` is returned unchanged.
    """
    stamped = {k: v for k, v in dict(record).items() if k not in _STAMP_KEYS}
    verdict = make_verdict(record, group, baseline_id=baseline_id, source=source,
                           allow_selected_remedy=allow_selected_remedy)
    stamped[RELATION_FIELD] = verdict["relation"]
    stamped[REASON_FIELD] = verdict["reason"]
    stamped[REFERENCE_FIELD] = verdict["reference"]
    stamped.pop(SELECTED_REMEDY_FIELD, None)
    if verdict.get(SELECTED_REMEDY_FIELD):
        stamped[SELECTED_REMEDY_FIELD] = verdict[SELECTED_REMEDY_FIELD]
    stamped[BASELINE_ID_FIELD] = verdict["baseline_id"]
    stamped[PROPOSAL_DIGEST_FIELD] = verdict["proposal_digest"]
    stamped["scope_source"] = source
    if verdict.get("missing"):
        stamped["scope_missing"] = True
    return stamped


def verdict_from_record(record: Any) -> Optional[Dict[str, Any]]:
    """The group verdict a **stamped** validation record carries, else ``None``.

    Reads the digest and baseline id the host stamped at validation time; it
    never recomputes them from the group as it stands now (that would let an
    edited proposal inherit the old verdict). A record without a stamped digest
    (hash-less legacy, or never stamped) yields ``None``: no scope authority.
    """
    if not isinstance(record, Mapping):
        return None
    digest = record.get(PROPOSAL_DIGEST_FIELD)
    if not isinstance(digest, str) or not digest:
        return None
    fields = normalize_scope_fields(record)
    verdict: Dict[str, Any] = {
        "relation": fields[RELATION_FIELD],
        "reason": fields[REASON_FIELD],
        "reference": fields[REFERENCE_FIELD],
        "baseline_id": record.get(BASELINE_ID_FIELD) or None,
        "source": record.get("scope_source") or "validation",
        "proposal_digest": digest,
    }
    remedy = record.get(SELECTED_REMEDY_FIELD)
    if isinstance(remedy, str) and remedy.strip():
        verdict[SELECTED_REMEDY_FIELD] = remedy.strip()
    if record.get("scope_missing"):
        verdict["relation"] = UNCLEAR
        verdict["reason"] = ""
        verdict["missing"] = True
    return verdict


def attach_verdict(group: Dict[str, Any], record: Any, *, hash_matched: bool) -> Dict[str, Any]:
    """Put a stamped record's verdict on ``group`` (in place), or clear it.

    Scope authority transfers **only** through a stable-hash join: an index
    fallback (``hash_matched=False``), a hash-less legacy record or an
    unstamped one removes any verdict instead, so the group reads ``unclear``.
    Validity merging is the caller's business and is unaffected.
    """
    verdict = verdict_from_record(record) if hash_matched else None
    if verdict is None:
        group.pop(VERDICT_KEY, None)
    else:
        group[VERDICT_KEY] = verdict
    return group


@dataclass(frozen=True)
class Authority:
    """A group's scope as the host can vouch for it right now."""

    relation: str
    reason: str
    reference: str = ""
    #: ``bound`` (authoritative), ``missing`` (never classified), ``stale``
    #: (proposal changed), ``other-baseline``, ``unbound`` (no baseline id).
    state: str = "missing"
    selected_remedy: Optional[str] = None

    @property
    def authoritative(self) -> bool:
        return self.state == "bound"


def authority(group: Mapping[str, Any], baseline_id: Optional[str] = None) -> Authority:
    """The group's authoritative scope, or ``unclear`` with why it is not.

    A verdict counts only when it was hash-joined at validation (it lives in
    :data:`VERDICT_KEY`), carries a baseline id equal to ``baseline_id`` (when
    one is given) and its proposal digest still matches the group as it stands
    now. A reviewer's provisional member tag never counts.
    """
    verdict = group.get(VERDICT_KEY) if isinstance(group, Mapping) else None
    if not isinstance(verdict, Mapping) or verdict.get("missing"):
        return Authority(UNCLEAR, "no validated scope classification", state="missing")
    relation = normalize_relation(verdict.get("relation"))
    reason = flatten_text(verdict.get("reason"))
    reference = flatten_text(verdict.get("reference"), REFERENCE_LIMIT)
    remedy = verdict.get(SELECTED_REMEDY_FIELD) if isinstance(verdict.get(SELECTED_REMEDY_FIELD), str) else None
    bound_to = verdict.get("baseline_id")
    if not bound_to:
        return Authority(UNCLEAR, "the scope classification is not bound to a baseline",
                         reference, state="unbound")
    if baseline_id and bound_to != baseline_id:
        return Authority(UNCLEAR, "the scope classification was made against a different baseline",
                         reference, state="other-baseline")
    if verdict.get("proposal_digest") != proposal_digest(group):
        return Authority(UNCLEAR, "the proposal changed after its scope was validated",
                         reference, state="stale")
    return Authority(relation, reason, reference, state="bound", selected_remedy=remedy)


def provisional_relation(member: Mapping[str, Any]) -> str:
    """A member's reviewer-provided (provisional) relation."""
    return normalize_scope_fields(member)[RELATION_FIELD]


def combined_relation(relations: Iterable[Any]) -> str:
    """The relation of an unsplit proposal or umbrella from its parts.

    Any extension makes it an extension; otherwise any unknown part makes it
    unclear; otherwise in scope. No majority vote, and an empty input is
    unclear.
    """
    seen = [normalize_relation(r) for r in relations]
    if not seen:
        return UNCLEAR
    if SCOPE_EXTENSION in seen:
        return SCOPE_EXTENSION
    if UNCLEAR in seen:
        return UNCLEAR
    return IN_SCOPE


# ---------------------------------------------------------------------------
# Eligibility: the scope-policy gate
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScopeDecision:
    """The scope-policy gate's decision for one group."""

    policy: str
    eligible: bool
    relation: str
    reason: str = ""
    #: ``eligible`` or ``deferred``.
    outcome: str = "eligible"
    authority_state: str = "missing"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy": self.policy,
            "eligible": self.eligible,
            "relation": self.relation,
            "label": LABELS[self.relation],
            "reason": self.reason,
            "outcome": self.outcome,
            "authority": self.authority_state,
        }


def effective(policy: Any) -> str:
    """``policy`` normalized, with omission meaning :data:`DEFAULT_POLICY`."""
    return normalize_policy(policy) or DEFAULT_POLICY


def scope_decision(
    group: Mapping[str, Any],
    policy: Any,
    baseline_id: Optional[str] = None,
) -> ScopeDecision:
    """The gate. ``expand`` passes everything; ``preserve`` passes only a bound ``in_scope``.

    Recomputed from the current policy and the group's bound metadata every
    time, so a stale approval, an import or an old artifact cannot authorize a
    write under ``preserve``.
    """
    policy = effective(policy)
    auth = authority(group, baseline_id)
    if policy == POLICY_EXPAND:
        return ScopeDecision(policy, True, auth.relation, auth.reason, "eligible", auth.state)
    if auth.authoritative and auth.relation == IN_SCOPE:
        return ScopeDecision(policy, True, IN_SCOPE, auth.reason, "eligible", auth.state)
    if auth.authoritative and auth.relation == SCOPE_EXTENSION:
        why = f"{DEFERRED_OUTCOME}: the proposed remedy extends the agreed scope"
        if auth.reason:
            why += f" ({auth.reason})"
    elif auth.state == "missing":
        why = f"{DEFERRED_OUTCOME}: no validated scope classification; {LEGACY_RECOVERY}"
    elif auth.authoritative:
        why = f"{DEFERRED_OUTCOME}: scope unclear"
        if auth.reason:
            why += f" ({auth.reason})"
    else:
        why = f"{DEFERRED_OUTCOME}: {auth.reason}; {LEGACY_RECOVERY}"
    return ScopeDecision(policy, False, auth.relation, why, "deferred", auth.state)


def partition(
    groups: Iterable[Mapping[str, Any]],
    policy: Any,
    baseline_id: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Split ``groups`` into (eligible, deferred) copies, each with :data:`DECISION_KEY`."""
    eligible: List[Dict[str, Any]] = []
    deferred: List[Dict[str, Any]] = []
    for group in groups:
        decision = scope_decision(group, policy, baseline_id)
        copy = dict(group)
        copy[DECISION_KEY] = decision.to_dict()
        (eligible if decision.eligible else deferred).append(copy)
    return eligible, deferred


def deferral_record(group: Mapping[str, Any], decision: ScopeDecision,
                    baseline_id: Optional[str] = None) -> Dict[str, Any]:
    """The persisted record of one scope deferral (separate from skips/invalid)."""
    gid = group.get("group_hash") or group.get("group_id") or group.get("id") or ""
    return {
        "group_id": str(gid),
        "theme": flatten_text(group.get("theme"), 160),
        "relation": decision.relation,
        "label": LABELS[decision.relation],
        "reason": decision.reason,
        "policy": decision.policy,
        "baseline_id": baseline_id or None,
        "authority": decision.authority_state,
    }


# ---------------------------------------------------------------------------
# Prompt guidance (rendered per call; never cache a policy-specific block)
# ---------------------------------------------------------------------------

#: What each review phase's scope is judged against (plan §2).
_BASELINE_DESCRIPTIONS: Dict[str, str] = {
    "review-plan": (
        "the reviewed plan's own goals, requirements and explicit limits or "
        "exclusions"
    ),
    "review-tasks": (
        "the source plan's goals, requirements and explicit limits or "
        "exclusions. The task list is judged against that plan: a task that "
        "adds a feature the plan does not authorize does not make the feature "
        "in scope by listing it"
    ),
    "code-review": (
        "the accepted plan and its requirements, limits and recorded "
        "decisions. The diff and the task list are evidence of what was "
        "built, not of what was asked for: drift in the implementation cannot "
        "authorize itself. Fixing a regression the change introduced is "
        "ordinarily within scope"
    ),
    "commits": (
        "the commit brief: the pinned commit messages, the review focus, and "
        "the frozen context plan when one is supplied. A focus limits where "
        "you look; it does not add goals. Commit messages too vague to settle "
        "a product-scope question make the answer \"unclear\", not a guess"
    ),
}


def baseline_description(phase: str) -> str:
    """The phase's scope baseline in prompt wording."""
    key = REVIEW_PHASE_OF.get(phase, phase)
    if phase in ("commits", "review-commits", "commit-review"):
        key = "commits"
    return _BASELINE_DESCRIPTIONS.get(key, _BASELINE_DESCRIPTIONS["review-plan"])


_RELATION_DEFINITIONS = '''- "in_scope": the action completes, corrects or clarifies what the baseline
  already asks for. Completing an existing requirement is in scope even when it
  is substantial work, and so is a prerequisite in another file, fixing a
  regression the work introduced, and removing behaviour or content the
  baseline never asked for (existing scope creep).
- "scope_extension": the action adds a capability, outcome or unrelated cleanup
  the baseline does not ask for, or changes an agreed outcome, even when it is
  worthwhile or needed to make the overall goal achievable.
- "unclear": the baseline does not settle it (missing, truncated or vague
  intent), or materially different fixes would differ in scope and none is
  chosen.'''

_FIELD_LINES = '''Give each finding these three extra fields:
- "scope_relation": "in_scope" | "scope_extension" | "unclear"
- "scope_reason": string (one short line saying why, against the baseline)
- "scope_reference": string (optional: the baseline section or text it rests on, or "")'''


def reviewer_guidance(policy: Any, phase: str) -> str:
    """The reviewer prompt's scope block for ``policy`` (filled into ``{scope_policy_guidance}``).

    ``expand`` adds informational annotation only: the existing checklist and
    criteria stand unchanged, and nothing about suppression appears. Only
    ``preserve`` adds the rule that reviewers do not propose new scope.
    """
    baseline = baseline_description(phase)
    if effective(policy) == POLICY_PRESERVE:
        return f'''## Scope Policy: Preserve
The user asked to preserve the agreed scope for this review. The scope baseline
is {baseline}. This rule takes precedence over the broader checklists above.

- Report only findings whose proposed correction stays within the agreed
  outcome and its stated limits. Do not propose new features or product
  outcomes, unrelated refactors, or optional cleanup outside that outcome, even
  when they would be beneficial.
- Keep reporting missing or incomplete agreed requirements, bugs and security
  regressions the work introduces, and contradictions or gaps in it.
- Keep reporting existing scope creep: behaviour or content the baseline never
  asked for. A finding that removes it brings the work back within scope, so
  report it and classify it "in_scope"; a finding about scope is not banned.
- Explicit exclusions in the baseline (for example "do not change the API")
  bind: never propose a remedy that crosses one.
- If an agreed requirement cannot be met without extending the scope, or the
  right fix is uncertain, do not hide the problem and do not prescribe the
  expansion as the fix: report the blocker with its evidence, classify the
  remedy honestly as "scope_extension" or "unclear", and say in the
  description which scope decision the user has to make.
- Returning no findings is acceptable.

Classify the proposed action of every finding you return:
{_RELATION_DEFINITIONS}

{_FIELD_LINES}'''
    return f'''## Scope Classification (labels only)
Follow every instruction above exactly as written: nothing in this section
changes which findings you report. For the report's labels, also classify each
finding's proposed action against the scope baseline, which is {baseline}.
This classification is informational: do not leave out a finding, change its
importance, or narrow its fix because it extends the scope or because its scope
is uncertain.

{_RELATION_DEFINITIONS}

{_FIELD_LINES}'''


#: Reply-contract fields the validator adds per group; policy-independent.
VALIDATOR_REPLY_FIELDS = (
    '"scope_relation": "in_scope|scope_extension|unclear", '
    '"scope_reason": "<one brief sentence>", "scope_reference": "<baseline section, or empty>"'
)


def validator_guidance(policy: Any, phase: str, *, revalidation_baseline_differs: bool = False) -> str:
    """The validator prompt's scope block for ``policy``.

    ``expand`` leaves the existing definition of ``valid`` alone and asks for
    an informational classification. ``preserve`` adds the independent
    rejection of leaked extensions, kept separate from correctness.
    ``revalidation_baseline_differs`` adds the note that the scope baseline is
    the original round's, not the current document a revalidation reads.
    """
    baseline = baseline_description(phase)
    original = ""
    if revalidation_baseline_differs:
        original = (
            "\n\nThis is a revalidation: correctness is judged against the current "
            "document, but scope is judged against the original review round's "
            "baseline, labelled as such above. Do not adopt the current document "
            "as the scope baseline."
        )
    if effective(policy) == POLICY_PRESERVE:
        return f'''## Scope Policy: Preserve
The user asked to preserve the agreed scope for this run. Verify each group's
facts and set "status" exactly as the task above says. Then, separately and
independently, check each group's full proposed remedy (every member's proposed
change together) against the original requirements and limits, which are
{baseline}.

- Classify independently of the reviewers' own `scope_relation` tags, their
  confidence, how many models agree, and their wording. Do not assume a
  reviewer obeyed an instruction to stay in scope, and do not accept a remedy
  because its description calls a new feature "required".
- "scope_extension": the remedy extends those limits. It is rejected for this
  run, even if its facts are correct or its importance is high.
- "unclear": you cannot establish that the remedy stays within those limits. An
  uncertain remedy is deferred, never approved for automatic application.
- "in_scope": the remedy completes, corrects or clarifies an agreed
  requirement, fixes a regression the work introduced, or removes behaviour the
  baseline never asked for.
- Keep correctness and scope separate. A factually correct suggestion whose
  remedy extends the scope stays "valid"; never mark it "invalid" to keep it
  out — the scope classification is what holds it back. If the problem is real
  but only an extension would fix it, keep its status, classify the remedy
  "scope_extension", and name in `scope_reason` the scope decision it needs.
- When the members propose materially different remedies and one of them stays
  within scope, you may name that one in "selected_remedy" (one line) and
  classify that remedy; otherwise classify the remedies together, and any
  extension among them makes the group "scope_extension".
- Explicit exclusions in the baseline bind under every policy.

Add to each result: {VALIDATOR_REPLY_FIELDS}, and optionally
"selected_remedy": "<the one in-scope remedy you classified>". Give the
evidence for the scope decision in `scope_reason`.{original}'''
    return f'''## Scope Classification (labels only)
Judge "status" exactly as the task above says; this section does not change it.
For the report's labels, also classify each group's full proposed action (every
member's proposed change together) against the scope baseline, which is
{baseline}. Classify independently of the reviewers' own `scope_relation` tags.
This classification is informational: a group whose issue is real is "valid"
whether or not it extends the scope, and its status, confidence and reason must
not depend on its scope.

{_RELATION_DEFINITIONS}

Add to each result: {VALIDATOR_REPLY_FIELDS}.{original}'''


def writer_guidance(policy: Any) -> str:
    """The write prompt's scope block: empty under ``expand`` (instructions unchanged)."""
    if effective(policy) != POLICY_PRESERVE:
        return ""
    return '''## Scope Policy: Preserve
This run preserves the agreed scope. Apply each item exactly as its instruction
says, and only within the scope its validation established. If you find that an
item cannot be completed without adding a feature, outcome or change beyond that
scope, do not make the expansion: decline that item with the reason. If you had
already edited files for it, say what you changed rather than reporting a clean
decline.'''


# ---------------------------------------------------------------------------
# Policy resolution and the per-round state record
# ---------------------------------------------------------------------------


def resolve_policy(
    *,
    explicit: Any = None,
    continuation: Any = None,
    recorded: Any = None,
    forwarded: Any = None,
) -> Tuple[str, str]:
    """``(policy, source)`` by plan §4's order.

    1. ``explicit``: this invocation's flag.
    2. ``continuation``: the current apply/composite continuation's recorded
       effective override.
    3. ``forwarded`` (a driving composite/full workflow's explicit value) or
       ``recorded`` (the originating review's policy when starting its apply).
    4. :data:`DEFAULT_POLICY` for a new run and for legacy records.
    """
    for value, source in (
        (explicit, SOURCE_EXPLICIT),
        (continuation, SOURCE_CONTINUATION),
        (forwarded, SOURCE_WORKFLOW),
        (recorded, SOURCE_REVIEW),
    ):
        policy = normalize_policy(value)
        if policy:
            return policy, source
    return DEFAULT_POLICY, SOURCE_DEFAULT


def review_phase_of(phase: str) -> str:
    """The review phase whose round ``phase`` belongs to (itself if unknown)."""
    return REVIEW_PHASE_OF.get(phase, phase)


def round_record(state: Mapping[str, Any], phase: str) -> Optional[Dict[str, Any]]:
    """The ``state.json`` scope-policy record of ``phase``'s review round, if any."""
    table = state.get(STATE_KEY) if isinstance(state, Mapping) else None
    if not isinstance(table, Mapping):
        return None
    record = table.get(review_phase_of(phase))
    return dict(record) if isinstance(record, Mapping) else None


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def record_review_round(
    state: Dict[str, Any],
    phase: str,
    policy: str,
    source: str,
    baseline: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Start (or keep) a review round's record: the reviewer-prompt policy.

    A fresh round replaces the previous record, which drops any apply override
    and deferrals of the old round. Callers must not call this for a resume,
    reaggregate or revalidation of the same round (they keep their policy and
    baseline); use :func:`update_round_baseline` to attach the baseline later.
    """
    table = state.setdefault(STATE_KEY, {})
    record: Dict[str, Any] = {
        "review_policy": effective(policy),
        "review_policy_source": source,
        "recorded_at": _now(),
    }
    if baseline:
        record["baseline"] = dict(baseline)
    table[review_phase_of(phase)] = record
    return record


def update_round_baseline(state: Dict[str, Any], phase: str, baseline: Mapping[str, Any]) -> None:
    """Attach the round's scope baseline (first binding wins; never rebased)."""
    table = state.setdefault(STATE_KEY, {})
    record = table.setdefault(review_phase_of(phase), {
        "review_policy": DEFAULT_POLICY,
        "review_policy_source": SOURCE_LEGACY,
        "recorded_at": _now(),
    })
    if not record.get("baseline"):
        record["baseline"] = dict(baseline)


def record_apply_policy(state: Dict[str, Any], phase: str, policy: str, source: str) -> Dict[str, Any]:
    """Record the effective apply policy (an explicit override survives later omission)."""
    table = state.setdefault(STATE_KEY, {})
    record = table.setdefault(review_phase_of(phase), {
        "review_policy": DEFAULT_POLICY,
        "review_policy_source": SOURCE_LEGACY,
        "recorded_at": _now(),
    })
    record["apply_policy"] = effective(policy)
    record["apply_policy_source"] = source
    record["apply_recorded_at"] = _now()
    return record


def record_deferrals(state: Dict[str, Any], phase: str, deferrals: Sequence[Mapping[str, Any]]) -> None:
    """Replace the round's scope deferrals (by group id; never processed/applied ids)."""
    table = state.setdefault(STATE_KEY, {})
    record = table.setdefault(review_phase_of(phase), {
        "review_policy": DEFAULT_POLICY,
        "review_policy_source": SOURCE_LEGACY,
        "recorded_at": _now(),
    })
    record["deferrals"] = [dict(d) for d in deferrals]


def round_policies(state: Mapping[str, Any], phase: str) -> Dict[str, Any]:
    """``{"review_policy", "apply_policy", "baseline_id", ...}`` for display/resolution.

    A missing record (legacy round) reads as ``expand``/``legacy``.
    """
    record = round_record(state, phase) or {}
    review = normalize_policy(record.get("review_policy")) or DEFAULT_POLICY
    return {
        "review_policy": review,
        "review_policy_source": record.get("review_policy_source") or SOURCE_LEGACY,
        "apply_policy": normalize_policy(record.get("apply_policy")),
        "apply_policy_source": record.get("apply_policy_source"),
        "baseline_id": baseline_id_of(record.get("baseline")),
        "deferrals": list(record.get("deferrals") or []),
    }


# ---------------------------------------------------------------------------
# Report vocabulary
# ---------------------------------------------------------------------------


def legend_text() -> str:
    """The one-line legend every report shows beside its scope tags."""
    return (
        f"Scope tags: `{LABELS[IN_SCOPE]}` completes or corrects the agreed outcome; "
        f"`{LABELS[SCOPE_EXTENSION]}` adds to it; `{LABELS[UNCLEAR]}` could not be "
        "settled. Tags describe proposals; they are separate from validity and selection."
    )


def policy_line(review_policy: Any, apply_policy: Any = None) -> str:
    """The effective-policy line; names the review policy when an apply override differs."""
    review = effective(review_policy)
    applied = normalize_policy(apply_policy) or review
    line = f"Scope policy: {applied}"
    if applied != review:
        line += f" (the review was requested under {review})"
    if review == POLICY_PRESERVE:
        line += (
            ". Additional scope was not solicited from reviewers; extension "
            "counts cover returned findings only"
        )
    elif applied == POLICY_EXPAND:
        line += ". Scope tags are informational"
    return line + "."


def markdown_tag(relation: Any, reason: Any = "", *, provisional: bool = False,
                 stale: bool = False) -> str:
    """``` `Scope extension` — reason``` as inline Markdown (one line, flattened)."""
    text = f"`{label(relation)}`"
    qualifiers = []
    if provisional:
        qualifiers.append("reviewer, provisional")
    if stale:
        qualifiers.append("may be stale: the proposal changed")
    if qualifiers:
        text += f" ({'; '.join(qualifiers)})"
    flat = flatten_text(reason).replace("`", "'")
    if flat:
        text += f" — {flat}"
    return text


def count_relations(groups: Iterable[Mapping[str, Any]], baseline_id: Optional[str] = None) -> Dict[str, int]:
    """Distinct-group counts per relation (authoritative relation of each group)."""
    counts = {r: 0 for r in RELATIONS}
    seen = set()
    for group in groups:
        gid = group.get("group_hash") or group.get("group_id") or id(group)
        if gid in seen:
            continue
        seen.add(gid)
        counts[authority(group, baseline_id).relation] += 1
    return counts


__all__ = [
    "Authority", "BASELINE_ID_FIELD", "DECISION_KEY", "DEFAULT_POLICY",
    "DEFERRED_OUTCOME", "DEST", "FLAG", "IN_SCOPE", "LABELS", "LEGACY_RECOVERY",
    "POLICIES", "POLICY_EXPAND", "POLICY_PRESERVE", "POLICY_SOURCES",
    "PROPOSAL_DIGEST_FIELD", "REASON_FIELD", "REFERENCE_FIELD", "RELATIONS",
    "RELATION_FIELD", "REVIEW_PHASE_OF", "SCOPE_EXTENSION", "SCOPE_FIELDS",
    "SELECTED_REMEDY_FIELD", "SOURCE_CONTINUATION", "SOURCE_DEFAULT",
    "SOURCE_EXPLICIT", "SOURCE_LEGACY", "SOURCE_REVIEW", "SOURCE_WORKFLOW",
    "STATE_KEY", "ScopeDecision", "UNCLEAR", "VALIDATOR_REPLY_FIELDS",
    "VERDICT_KEY", "attach_verdict", "authority", "baseline_description", "baseline_id_of",
    "baseline_source", "baseline_source_from_document",
    "baseline_unreadable_roles", "build_baseline", "combined_relation",
    "count_relations", "deferral_record", "effective", "flatten_text",
    "group_members", "has_scope_fields", "is_valid_policy", "label",
    "legend_text", "make_verdict", "markdown_tag", "normalize_policy",
    "normalize_relation", "normalize_scope_fields", "partition", "policy_line",
    "proposal_digest", "proposal_payload", "provisional_relation",
    "record_apply_policy", "record_deferrals", "record_review_round",
    "resolve_policy", "review_phase_of", "reviewer_guidance", "round_policies",
    "round_record", "scope_decision", "selected_remedy_of",
    "stamp_validation_record", "verdict_from_record",
    "update_round_baseline", "validator_guidance", "writer_guidance",
]
