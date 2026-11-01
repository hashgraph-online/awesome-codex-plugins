"""Scope tags in the review reports (plans/scope-policy-and-report-tags.md §6).

Presentation only: the scope-policy gate (``scope_policy.scope_decision``,
recomputed at every apply) stays authoritative, and nothing here changes a
validity, selection or application decision. Every Markdown generator (plan,
tasks, code, commits, consolidated) and every HTML payload (flat/PR
``report_data.json``, the consolidated ``consolidated_report_data.json``) reads
its scope words through this module, so the three report kinds say the same
thing with the same labels:

* a finding's own tag is the reviewer's **provisional** classification
  (``scope_relation``/``scope_reason`` on the member record);
* a group's tag is the **validated** verdict (``scope_policy.authority``),
  which reads ``Scope unclear`` when it is missing, unbound or stale (the
  proposal changed after validation) — never a confident in-scope badge;
* an umbrella (consolidated group) derives its tag from its underlying
  groups (``scope_policy.combined_relation``) and adds no authority;
* under an effective ``preserve`` policy a group that is not eligible shows
  ``Deferred: scope preservation requested`` beside its tag, whatever its
  validity — a real finding is never shown as a false positive.

Markdown text is flattened and escaped (:func:`md_text`) so a model-written
reason cannot open a heading, forge a checkbox, a metadata line the description
parser keys on, or the issue-digest footer. Pure apart from :func:`read_state`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

try:
    from . import scope_policy as sp
except ImportError:  # pragma: no cover - direct script import
    import scope_policy as sp  # type: ignore

#: ``report_data.json`` / ``consolidated_report_data.json`` key holding the
#: round's policy block (policy line, legend, counts, baseline).
REPORT_KEY = "scopePolicy"
#: Key of the scope entry on each group, suggestion and umbrella payload.
ENTRY_KEY = "scope"

#: Characters escaped in model-written Markdown text: emphasis, links, code,
#: HTML and headings (the same set ``commit_report._md_inline`` escapes).
_MD_ESCAPED = "\\*_[]<>#|~"

#: Top-level keys an imported selection file may never carry into a decision:
#: scope classifications and policy come from the review's own records only.
SELECTION_DENY_PREFIXES = ("scope", "selected_remedy", "selectedremedy")


# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------


def md_text(value: Any, limit: int = sp.REASON_LIMIT) -> str:
    """Model-written text as one inert Markdown line.

    ``scope_policy.flatten_text`` (one line, no leading heading/list/checkbox
    marker, clipped), backticks turned into quotes, then every character that
    opens emphasis, a link, a checkbox, HTML (``<!--`` included) or a heading
    backslash-escaped. A reason holding ``**Importance:**``, ``- [x] Skip``,
    ``### 2.`` or ``<!-- multi-llm:issues-digest … -->`` stays readable but can
    reach none of ``report_parser``'s patterns.
    """
    text = sp.flatten_text(value, limit).replace("`", "'")
    return "".join("\\" + c if c in _MD_ESCAPED else c for c in text)


def _deferred_detail(reason: str) -> str:
    """A deferral reason without its leading ``Deferred: …`` outcome words."""
    prefix = sp.DEFERRED_OUTCOME + ":"
    text = str(reason or "")
    if text.startswith(prefix):
        text = text[len(prefix):]
    return text.strip()


# ---------------------------------------------------------------------------
# The round: policy, baseline, deferrals
# ---------------------------------------------------------------------------


def read_state(phase_dir: Any) -> Dict[str, Any]:
    """``state.json`` beside a review phase dir (``<plan dir>/state.json``), or ``{}``."""
    if phase_dir is None:
        return {}
    path = Path(phase_dir).parent / "state.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def round_info(state: Optional[Mapping[str, Any]], phase: str,
               groups: Iterable[Mapping[str, Any]] = ()) -> Dict[str, Any]:
    """The review round's policy record as the reports show it.

    ``reviewPolicy`` is what the reviewers were asked under; ``applyPolicy`` an
    explicit apply override; ``effectivePolicy`` the one eligibility is shown
    for. A round with no record (a legacy run, or a direct call with no
    ``state.json``) reads ``expand`` — unless the groups carry a decision the
    validation stage stored (``scope_policy_decision``), whose policy is then
    the round's.
    """
    state = state if isinstance(state, Mapping) else {}
    record = sp.round_record(state, phase)
    policies = sp.round_policies(state, phase)
    review = policies["review_policy"]
    source = policies["review_policy_source"]
    if record is None:
        stored = {
            sp.normalize_policy((g.get(sp.DECISION_KEY) or {}).get("policy"))
            for g in groups if isinstance(g, Mapping)
            and isinstance(g.get(sp.DECISION_KEY), Mapping)
        } - {None}
        if len(stored) == 1:
            review = stored.pop()
            source = "validation"
    apply = policies["apply_policy"]
    baseline = (record or {}).get("baseline")
    return {
        "recorded": record is not None,
        "reviewPolicy": review,
        "reviewPolicySource": source,
        "applyPolicy": apply,
        "applyPolicySource": policies["apply_policy_source"],
        "effectivePolicy": apply or review,
        "baselineId": policies["baseline_id"],
        "baseline": dict(baseline) if isinstance(baseline, Mapping) else None,
        "deferrals": [dict(d) for d in policies["deferrals"] if isinstance(d, Mapping)],
    }


def deferral_index(info: Mapping[str, Any]) -> Dict[str, Mapping[str, Any]]:
    """The round's recorded deferrals by group id, for the current policy only."""
    policy = info.get("effectivePolicy")
    index: Dict[str, Mapping[str, Any]] = {}
    for record in info.get("deferrals") or ():
        gid = str(record.get("group_id") or "")
        if gid and sp.normalize_policy(record.get("policy")) == policy:
            index[gid] = record
    return index


# ---------------------------------------------------------------------------
# Entries: one per member, group and umbrella
# ---------------------------------------------------------------------------


def member_scope(member: Mapping[str, Any]) -> Dict[str, Any]:
    """A finding's own (reviewer, provisional) classification."""
    fields = sp.normalize_scope_fields(member)
    classified = sp.has_scope_fields(member)
    relation = fields[sp.RELATION_FIELD]
    return {
        "relation": relation,
        "label": sp.LABELS[relation],
        "reason": fields[sp.REASON_FIELD] if classified else "",
        "reference": fields[sp.REFERENCE_FIELD] if classified else "",
        "classified": classified,
        "provisional": True,
    }


def _decision_payload(decision: "sp.ScopeDecision",
                      deferral: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    data = decision.to_dict()
    if not decision.eligible and deferral and deferral.get("reason"):
        # The apply phase's own recorded words for this deferral.
        data["reason"] = sp.flatten_text(deferral.get("reason"), sp.REASON_LIMIT * 2)
        data["recorded"] = True
    data["detail"] = _deferred_detail(data["reason"]) if not decision.eligible else ""
    data["outcomeText"] = sp.DEFERRED_OUTCOME if not decision.eligible else (
        "Eligible under scope preservation" if decision.policy == sp.POLICY_PRESERVE
        else "Eligible")
    return data


def group_scope(group: Mapping[str, Any], info: Mapping[str, Any],
                deferrals: Optional[Mapping[str, Mapping[str, Any]]] = None) -> Dict[str, Any]:
    """A group's validated scope and its eligibility under the effective policy.

    The relation is ``scope_policy.authority``'s: ``unclear`` unless the
    verdict is hash-joined, bound to this round's baseline and its proposal
    digest still matches. A stale verdict keeps what it classified as
    ``classifiedRelation`` (shown as "validated as … before the change") but
    never as the group's relation. The decision is ``scope_decision`` for
    ``info["effectivePolicy"]``.
    """
    baseline_id = info.get("baselineId")
    auth = sp.authority(group, baseline_id)
    entry: Dict[str, Any] = {
        "relation": auth.relation,
        "label": sp.LABELS[auth.relation],
        "reason": auth.reason,
        "reference": auth.reference,
        "authority": auth.state,
        "validated": auth.authoritative,
        "stale": auth.state == "stale",
        "provisional": False,
    }
    verdict = group.get(sp.VERDICT_KEY) if isinstance(group, Mapping) else None
    if isinstance(verdict, Mapping) and not verdict.get("missing"):
        classified = sp.normalize_relation(verdict.get("relation"))
        entry["classifiedRelation"] = classified
        entry["classifiedLabel"] = sp.LABELS[classified]
        entry["classifiedReason"] = sp.flatten_text(verdict.get("reason"))
        entry["baselineId"] = verdict.get("baseline_id") or None
        entry["proposalDigest"] = verdict.get("proposal_digest") or None
        remedy = verdict.get(sp.SELECTED_REMEDY_FIELD)
        if isinstance(remedy, str) and remedy.strip():
            entry["selectedRemedy"] = sp.flatten_text(remedy, sp.SELECTED_REMEDY_LIMIT)
    gid = str(group.get("group_hash") or group.get("group_id") or "") if isinstance(group, Mapping) else ""
    if deferrals is None:
        deferrals = deferral_index(info)
    decision = sp.scope_decision(group, info.get("effectivePolicy"), baseline_id)
    entry["decision"] = _decision_payload(decision, deferrals.get(gid))
    return entry


def replay_decision(entry: Mapping[str, Any], policy: Any,
                    deferral: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """``scope_decision`` for a persisted group entry, with no live group.

    Regeneration has only the saved payload: this rebuilds a stand-in group
    whose authority state equals the one recorded at review time and asks the
    one gate (``scope_policy.scope_decision``) again under *policy*, so an
    apply override changes eligibility while the historical classification
    stays exactly as recorded.
    """
    stand_in: Dict[str, Any] = {"theme": "", "suggestions": []}
    digest = sp.proposal_digest(stand_in)
    state = str(entry.get("authority") or "missing")
    anchor = "recorded-baseline"
    if state in ("bound", "stale", "other-baseline", "unbound"):
        relation = entry.get("classifiedRelation") or entry.get("relation")
        stand_in[sp.VERDICT_KEY] = {
            "relation": relation,
            "reason": entry.get("classifiedReason") or entry.get("reason") or "",
            "reference": entry.get("reference") or "",
            "baseline_id": {"unbound": None, "other-baseline": "another-baseline"}.get(state, anchor),
            "proposal_digest": "stale" if state == "stale" else digest,
        }
    return _decision_payload(sp.scope_decision(stand_in, policy, anchor), deferral)


def umbrella_scope(members: Sequence[Tuple[str, Mapping[str, Any]]]) -> Dict[str, Any]:
    """An umbrella's tag from its underlying groups' validated entries.

    *members* is ``[(display label, group entry), ...]``. Any extension makes
    it ``Scope extension`` ("contains extension"), otherwise any unknown member
    ``Scope unclear``, otherwise ``Within scope`` — no majority vote, and no
    authority of its own: each underlying group keeps its tag and its gate.
    """
    relations = [str(e.get("relation") or sp.UNCLEAR) for _l, e in members]
    relation = sp.combined_relation(relations)
    counts = {r: relations.count(r) for r in sp.RELATIONS}
    mixed = len(set(relations)) > 1
    if relation == sp.SCOPE_EXTENSION:
        named = [label for label, e in members if e.get("relation") == sp.SCOPE_EXTENSION]
        reason = "contains extension" + (f" ({', '.join(named)})" if named else "")
    elif relation == sp.UNCLEAR:
        reason = ("contains members whose scope is unclear" if relations
                  else "no underlying group to classify")
    else:
        reason = "every underlying group is within scope"
    deferred = [label for label, e in members
                if (e.get("decision") or {}).get("outcome") == "deferred"]
    return {
        "relation": relation,
        "label": sp.LABELS[relation],
        "reason": reason,
        "mixed": mixed,
        "counts": counts,
        "members": len(members),
        "deferred": deferred,
        "derived": True,
    }


def count_entries(entries: Iterable[Tuple[str, Mapping[str, Any]]]) -> Dict[str, int]:
    """Relation counts over distinct group ids (a duplicate id counts once)."""
    counts = {r: 0 for r in sp.RELATIONS}
    counts["deferred"] = 0
    seen = set()
    for gid, entry in entries:
        key = gid or id(entry)
        if key in seen:
            continue
        seen.add(key)
        counts[sp.normalize_relation(entry.get("relation"))] += 1
        if (entry.get("decision") or {}).get("outcome") == "deferred":
            counts["deferred"] += 1
    return counts


def report_block(info: Mapping[str, Any], counts: Mapping[str, int]) -> Dict[str, Any]:
    """The payload's ``scopePolicy`` block (persisted; read by every template)."""
    return {
        "reviewPolicy": info.get("reviewPolicy"),
        "reviewPolicySource": info.get("reviewPolicySource"),
        "applyPolicy": info.get("applyPolicy"),
        "applyPolicySource": info.get("applyPolicySource"),
        "effectivePolicy": info.get("effectivePolicy"),
        "recorded": bool(info.get("recorded")),
        "baselineId": info.get("baselineId"),
        "baseline": info.get("baseline"),
        "policyLine": sp.policy_line(info.get("reviewPolicy"), info.get("applyPolicy")),
        "legend": sp.legend_text(),
        "labels": dict(sp.LABELS),
        "deferredOutcome": sp.DEFERRED_OUTCOME,
        "counts": dict(counts),
    }


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------


def md_member_line(member: Mapping[str, Any]) -> str:
    """``**Scope:** `Scope extension` (reviewer, provisional) — reason``."""
    entry = member_scope(member)
    reason = entry["reason"] if entry["classified"] else "not classified"
    line = "**Scope:** " + sp.markdown_tag(entry["relation"], provisional=True)
    shown = md_text(reason)
    return line + (f" — {shown}" if shown else "")


def md_group_lines(entry: Mapping[str, Any], *, field: str = "Group scope") -> List[str]:
    """A group's validated tag, any selected remedy, and its policy outcome."""
    state = entry.get("authority")
    if state == "bound":
        head = sp.markdown_tag(entry.get("relation")) + " (validated)"
        reason = md_text(entry.get("reason"))
    elif state == "stale":
        head = sp.markdown_tag(sp.UNCLEAR, stale=True)
        reason = f"validated as `{entry.get('classifiedLabel') or sp.LABELS[sp.UNCLEAR]}` before the change"
        prior = md_text(entry.get("classifiedReason"))
        if prior:
            reason += f": {prior}"
    else:
        head = sp.markdown_tag(sp.UNCLEAR)
        reason = md_text(entry.get("reason"))
    lines = [f"**{field}:** {head}" + (f" — {reason}" if reason else "")]
    if state == "bound" and entry.get("selectedRemedy"):
        lines.append(f"**Selected remedy:** {md_text(entry['selectedRemedy'], sp.SELECTED_REMEDY_LIMIT)}")
    lines.extend(md_outcome_lines(entry.get("decision") or {}))
    return lines


def md_outcome_lines(decision: Mapping[str, Any]) -> List[str]:
    """``**Scope outcome:**`` under ``preserve``; nothing under ``expand``."""
    if sp.normalize_policy(decision.get("policy")) != sp.POLICY_PRESERVE:
        return []
    if decision.get("outcome") == "deferred":
        detail = md_text(decision.get("detail"))
        return [f"**Scope outcome:** {sp.DEFERRED_OUTCOME}" + (f" — {detail}" if detail else "")]
    return ["**Scope outcome:** Eligible under scope preservation"]


def md_umbrella_lines(umbrella: Mapping[str, Any]) -> List[str]:
    """A consolidated group's derived tag (and how many members defer)."""
    qualifiers = ["derived from its groups"]
    if umbrella.get("mixed"):
        qualifiers.append("mixed members")
    line = (f"**Scope:** `{umbrella.get('label') or sp.LABELS[sp.UNCLEAR]}` "
            f"({'; '.join(qualifiers)}) — {md_text(umbrella.get('reason'))}")
    lines = [line]
    deferred = list(umbrella.get("deferred") or [])
    if deferred:
        lines.append(
            f"**Scope outcome:** {sp.DEFERRED_OUTCOME} for {len(deferred)} of "
            f"{umbrella.get('members', len(deferred))} groups ({md_text(', '.join(deferred))}); "
            "each group is decided on its own")
    return lines


def md_header_lines(info: Mapping[str, Any], counts: Mapping[str, int], *,
                    noun: str = "groups") -> List[str]:
    """The effective-policy line and the distinct-group tag counts."""
    line = sp.policy_line(info.get("reviewPolicy"), info.get("applyPolicy"))
    if line.startswith("Scope policy:"):
        line = "**Scope policy:**" + line[len("Scope policy:"):]
    total = sum(counts.get(r, 0) for r in sp.RELATIONS)
    tags = (f"**Scope tags:** {counts.get(sp.IN_SCOPE, 0)} `{sp.LABELS[sp.IN_SCOPE]}`, "
            f"{counts.get(sp.SCOPE_EXTENSION, 0)} `{sp.LABELS[sp.SCOPE_EXTENSION]}`, "
            f"{counts.get(sp.UNCLEAR, 0)} `{sp.LABELS[sp.UNCLEAR]}` "
            f"(validated, of {total} {noun})")
    if sp.normalize_policy(info.get("effectivePolicy")) == sp.POLICY_PRESERVE:
        tags += f"; {counts.get('deferred', 0)} deferred: scope preservation requested"
    return [line, tags]


def md_legend_line() -> str:
    """The legend, as a line of the report's note blockquote."""
    return "> " + sp.legend_text()


# ---------------------------------------------------------------------------
# Verdicts for groups read back from grouped.json + validation.json
# ---------------------------------------------------------------------------


def with_verdicts(groups: Sequence[Mapping[str, Any]],
                  validation: Optional[Sequence[Mapping[str, Any]]]) -> List[Dict[str, Any]]:
    """Copies of *groups*, each carrying the validated verdict when one exists.

    A group already holding ``scope_verdict`` keeps it. Otherwise a stamped
    validation record joins **only** by the group's stable hash
    (``scope_policy.attach_verdict(..., hash_matched=True)``); a record found
    by index alone never transfers scope authority.
    """
    by_hash: Dict[str, Mapping[str, Any]] = {}
    for record in validation or ():
        if isinstance(record, Mapping):
            key = record.get("group_id") or record.get("group_hash")
            if key:
                by_hash[str(key)] = record
    out: List[Dict[str, Any]] = []
    for group in groups:
        copy = dict(group) if isinstance(group, Mapping) else {}
        if sp.VERDICT_KEY not in copy:
            record = by_hash.get(str(copy.get("group_hash") or ""))
            if record is not None and copy.get("group_hash"):
                sp.attach_verdict(copy, record, hash_matched=True)
        out.append(copy)
    return out


def strip_selection_scope_fields(data: Any, source: str = "selections") -> Any:
    """Drop scope/policy-like keys from an imported selection export.

    An exported ``user_selections.json`` carries ids and choices only; scope
    classifications, remedies and the policy come from the review's own
    records and the CLI, never from an imported file. Returns *data* without
    those keys (and says on stderr which it ignored).
    """
    if not isinstance(data, dict):
        return data
    dropped = [k for k in list(data)
               if str(k).replace("-", "_").lower().startswith(SELECTION_DENY_PREFIXES)]
    if dropped:
        import sys

        for key in dropped:
            data.pop(key, None)
        print(f"WARNING: {source} carries {', '.join(sorted(map(str, dropped)))}; "
              "scope tags and policy come from the review's records and the "
              "command line, so these fields are ignored.", file=sys.stderr)
    return data


__all__ = [
    "ENTRY_KEY", "REPORT_KEY", "count_entries", "deferral_index", "group_scope", "md_group_lines",
    "md_header_lines", "md_legend_line", "md_member_line", "md_outcome_lines",
    "md_text", "md_umbrella_lines", "member_scope", "read_state", "replay_decision",
    "report_block", "round_info", "strip_selection_scope_fields", "umbrella_scope",
    "with_verdicts",
]
