#!/usr/bin/env python3
"""The human-decision judging loop's Python half (D2a/D2b/D2i).

Materializing judge prompts without a consumer would leave the loop open, so
this module owns both ends:

* **Producer** — materializes one ``human_decision_judge`` task per
  needs-human-decision item in scope (``human_decision_tasks.json``), with the
  prompt built by ``utils/subagent_prompts.build_human_decision_judge_prompt``
  and the Evaluation-Criteria / Approve-vs-Salvage-vs-Skip rules inlined verbatim
  rather than pointed at (a reference file is a path a headless runner may not be
  able to open).
* **Consumer** — reads the ``human_decision_batch_<group_id>.json`` verdict files the
  invoker persisted, validates each against
  ``schemas/human_decision_verdicts.schema.json`` naming the offending file and
  index, maps verdicts by **stable ``group_id``** (never batch or list position,
  so a reordered or partially-written batch cannot misattribute one), records
  each through ``StateManager.record_human_decision`` keeping today's exact
  translation, rewrites the work set (substituting ``salvaged_description``
  *before* the suggestion reaches ``utils/suggestion_batcher.py``) and persists
  the ingested verdicts into phase state so a crash between judging and applying
  resumes without re-running the judges.

Verdicts stop being inline JSON in a subagent's final message: a verdict that
never touches disk is unrecoverable after a crash, invisible to ``--resume`` and
meaningless under ``--detach``. Both judging legs — the host's native subagent
and the Python executor — therefore land on one recorded state, which is what
makes the recorded records (and so every report overlay) identical across
invokers apart from the ``judge`` they name.
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    from .judge_vocab import (
        JUDGE_AUTO_DECIDE,
        JUDGE_AUTO_DECIDE_SALVAGE,
        JUDGE_BATCH_ID_PREFIX,
        JUDGE_SKIPPED,
        canonical_value,
    )
    from .schema_validator import validate_human_decision_verdicts
    from .subagent_prompts import build_human_decision_judge_prompt
    from .subagent_tasks import (
        PromptBudget,
        build_inputs,
        content_hash,
        file_bytes_sha256,
        make_task,
        make_task_file,
        write_task_file,
    )
except ImportError:  # pragma: no cover - direct-script import shim
    from utils.judge_vocab import (
        JUDGE_AUTO_DECIDE,
        JUDGE_AUTO_DECIDE_SALVAGE,
        JUDGE_BATCH_ID_PREFIX,
        JUDGE_SKIPPED,
        canonical_value,
    )
    from utils.schema_validator import validate_human_decision_verdicts
    from utils.subagent_prompts import build_human_decision_judge_prompt
    from utils.subagent_tasks import (
        PromptBudget,
        build_inputs,
        content_hash,
        file_bytes_sha256,
        make_task,
        make_task_file,
        write_task_file,
    )


__all__ = [
    "JUDGE_TASKS_FILENAME",
    "VERDICT_FILE_PATTERN",
    "DECISION_APPROVE",
    "DECISION_SALVAGE",
    "DECISION_SKIP",
    "VerdictIngest",
    "judge_item_from_group",
    "group_id_of",
    "verdict_output_name",
    "build_judge_tasks",
    "write_judge_tasks",
    "read_verdict_files",
    "ingest_verdicts",
    "judge_labels",
    "native_judge_label",
    "is_judge_source",
    "judge_source_label",
    "judge_outcome",
    "judge_status_label",
    "record_verdicts",
    "apply_verdicts_to_work_set",
]


JUDGE_TASKS_FILENAME = "human_decision_tasks.json"
#: Glob over every verdict file in a phase dir. The token after the prefix is the
#: judged item's stable id (see :func:`verdict_output_name`), never its position,
#: so the glob is deliberately wider than ``_\d+``.
VERDICT_FILE_PATTERN = "human_decision_batch_*.json"

#: The basename charset ``schemas/subagent_tasks.schema.json`` allows for
#: ``output_name``. A token outside it is hashed rather than rejected.
_SAFE_VERDICT_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

DECISION_APPROVE = "approve"
DECISION_SALVAGE = "salvage"
DECISION_SKIP = "skip"

#: Wire ``decision`` -> the value ``record_human_decision`` stores. A salvage is
#: recorded as an **approval** (it approves the rewritten suggestion) carrying the
#: salvage markers, which is what keeps ``--resume`` and every report consumer
#: treating it as an applied approval.
_RECORDED_DECISION = {
    DECISION_APPROVE: "approved",
    DECISION_SKIP: "skipped",
    DECISION_SALVAGE: "approved",
}

_ACTION_PLAIN = JUDGE_AUTO_DECIDE
_ACTION_SALVAGE = JUDGE_AUTO_DECIDE_SALVAGE

#: What a decision the judge made is stored as: ``judge_auto_decide`` /
#: ``judge_auto_decide_salvage`` on ``batch_context``, ``judge_skipped`` on a
#: skipped item. These are persisted keys, not user-facing words — everything a
#: user reads goes through the label functions below. Every reader here also
#: accepts the ``claude_*`` spellings an earlier version wrote, through
#: ``judge_vocab.canonical_value`` (the one legacy map).
JUDGE_SOURCE_PREFIX = JUDGE_AUTO_DECIDE
JUDGE_SKIPPED_STATUS = JUDGE_SKIPPED


def is_judge_source(source: Any) -> bool:
    """Whether a ``decision_source``/``batch_action`` marks a judge's decision."""
    return str(canonical_value(source or "")).startswith(JUDGE_SOURCE_PREFIX)


def judge_source_label(source: Any) -> str:
    """The host-neutral words for a ``decision_source``; unknown sources pass through."""
    text = str(canonical_value(source or ""))
    if text == _ACTION_SALVAGE:
        return "judge agent (salvaged)"
    if is_judge_source(text):
        return "judge agent"
    return text or "unknown"


def judge_status_label(status: Any) -> str:
    """The host-neutral words for a skipped item's ``status``."""
    if canonical_value(status) == JUDGE_SKIPPED_STATUS:
        return "skipped by judge"
    return str(status or "unknown")


def judge_outcome(record: Dict[str, Any]) -> str:
    """``approved`` / ``salvaged`` / ``skipped`` for a recorded judge decision.

    A salvage is recorded with ``decision == "approved"`` plus the salvage
    marker (see :data:`_RECORDED_DECISION`), so the marker, not ``decision``,
    says it. Reading ``decision`` alone is what made one run's ingest line say
    "1 salvaged" and its ``summary.md`` say "Approved" for the same item.
    """
    context = (record or {}).get("batch_context") or {}
    markers = (context.get("decision_source"), context.get("batch_action"))
    if _ACTION_SALVAGE in (canonical_value(marker) for marker in markers):
        return "salvaged"
    return str((record or {}).get("decision") or "unknown")


#: Who judged when nothing better is known: the host's own agent, unnamed.
NATIVE_JUDGE = "host agent"


# ---------------------------------------------------------------------------
# Item shaping
# ---------------------------------------------------------------------------

def group_id_of(group: Dict[str, Any]) -> str:
    """Return a group's stable id, computing it when the group carries none."""
    existing = group.get("group_hash") or group.get("group_id")
    if existing:
        return str(existing)
    try:
        from .state_manager import generate_group_id
    except ImportError:  # pragma: no cover
        from utils.state_manager import generate_group_id
    return generate_group_id(group)


def judge_item_from_group(group: Dict[str, Any]) -> Dict[str, Any]:
    """Project a suggestion group into the record the judge prompt embeds.

    The judge is handed values, never a path to the report: ``group_id``,
    ``title``, ``description``, ``importance``, ``validation_reason``,
    ``confidence`` and ``models`` — plus ``file`` and ``line_range`` when the
    primary suggestion carries them (mirrors ``apply_code_fixes_orchestrator
    .format_fix_for_output``'s primary/group fallback). A plan-suggestion group
    (apply-suggestions, apply-task-suggestions) never has these; a code-review
    group (apply-code-fixes) always does, and without them the judge decided
    "Approve / Salvage / Skip" about a concrete code change from title and
    prose alone — never told where in the repository to look, even though its
    task runs ``agent-readonly`` and could read the file (F9, 2026-09-16).
    """
    suggestions = group.get("suggestions") or []
    primary = suggestions[0] if suggestions else {}
    descriptions = [
        s.get("desc") or s.get("description") or ""
        for s in suggestions
    ]
    description = "\n\n".join(d for d in descriptions if d)
    item = {
        "group_id": group_id_of(group),
        "title": primary.get("title") or group.get("theme") or "Untitled",
        "description": description or group.get("desc") or group.get("description") or "",
        "importance": (
            primary.get("importance") or group.get("importance") or "MEDIUM"
        ).upper(),
        "validation_reason": group.get("validation_reason", ""),
        "validation_confidence": group.get("validation_confidence", 0.0),
        "models": list(group.get("models", [])),
    }
    file_path = primary.get("file") or group.get("file")
    line_range = primary.get("line_range") or group.get("line_range")
    if file_path:
        item["file"] = file_path
    if line_range:
        item["line_range"] = list(line_range)
    return item


# ---------------------------------------------------------------------------
# Producer: materialize the judging tasks
# ---------------------------------------------------------------------------

def verdict_output_name(token: str) -> str:
    """Return the verdict basename for one judging task, keyed by *token*.

    The token is the item's stable ``group_id`` — **never its position** in the
    materialized list. ``build_judge_tasks`` is called with whatever items are
    still unjudged, so a re-enumerated index names a *different* group's verdict
    file on the next invocation; and because a task counts as done iff its
    ``output_name`` exists, parses and validates, the resumed task would read the
    previous round's already-ingested verdict, never be dispatched, and leave its
    own group unjudged (silently skipped under ``--yes``) — while a native
    invoker would instead overwrite the earlier group's file. Keying by
    ``group_id`` is what makes "resume by id" true of the filenames too.

    A token outside the task schema's basename charset is hashed rather than
    rejected, so an exotic id still names exactly one stable file.
    """
    token = str(token or "")
    if not _SAFE_VERDICT_TOKEN.match(token):
        token = content_hash(token)
    return f"human_decision_batch_{token}.json"


def build_judge_tasks(
    *,
    items: Sequence[Dict[str, Any]],
    phase_dir: str,
    plan_file: str = "",
    grouped_file: Optional[str] = None,
    tasks_file: Optional[str] = None,
    prompt_budget: Optional[PromptBudget] = None,
    trust_note: Optional[str] = None,
) -> Dict[str, Any]:
    """Materialize one judging task per in-scope item.

    One task per item — not one per batch — because a judging task's required
    field is ``group_id`` (D2g), and per-item tasks are what let a partially
    completed judging phase resume by ``group_id`` instead of by batch position.

    Args:
        items: Judge item records (see :func:`judge_item_from_group`).
        phase_dir: The apply phase dir the verdict files land in.
        plan_file: Plan path for ``inputs.plan_sha256`` (provenance only).
        grouped_file: Optional grouped.json path for ``inputs.grouped_sha256``.
        tasks_file: Optional ``tasks/tasks.md`` path for ``inputs.tasks_sha256``,
            passed by the one phase (apply-task-suggestions) whose judged items
            are decisions about that file rather than the plan — without it a
            hand-edited tasks.md does not invalidate a stored judging task the
            way an edited plan already does.
        prompt_budget: Optional D2d budget. A single item's prompt cannot be
            split, so an over-budget prompt fails loudly rather than truncating.
        trust_note: Optional sentence appended to every prompt: on a commit
            review's apply, ``commit_range.DATA_UNDER_REVIEW`` (the findings
            are built from commits and files read at ``head``, all data under
            review; plans/review-commits.md §2.6). ``None`` keeps every
            prompt byte for byte what it was.

    Returns:
        The task-file document (not yet written).
    """
    inputs = build_inputs(
        plan_file=plan_file,
        grouped_file=grouped_file,
        tasks_file=tasks_file,
        items=[item.get("group_id", "") for item in items],
    )
    budget = prompt_budget or PromptBudget(None)

    tasks: List[Dict[str, Any]] = []
    for index, item in enumerate(items):
        group_id = item.get("group_id", "")
        prompt = build_human_decision_judge_prompt([item])
        if trust_note:
            prompt = f"{prompt.rstrip()}\n\n{trust_note}\n"
        if not budget.fits(prompt):
            budget.resolution(prompt, splittable=False)
        # Both identities key off the item, never off its position: this function
        # is called with the *remaining* items, so `index` is reassigned to a
        # different group on every invocation. An item with no id at all falls
        # back to a hash of its own prompt, which is stable for the same reason.
        token = group_id or content_hash(prompt)
        tasks.append(make_task(
            kind="human_decision_judge",
            task_id=f"human_decision_judge-{token}",
            prompt=prompt,
            output_name=verdict_output_name(token),
            inputs=inputs,
            phase_dir=phase_dir,
            extra={
                "group_id": group_id,
                "items_count": 1,
                "batch_index": index,
                "plan_file": plan_file,
            },
        ))

    return make_task_file(
        kind="human_decision_judge",
        tasks=tasks,
        inputs=inputs,
        extra={
            "total_tasks": len(tasks),
            "phase_dir": phase_dir,
            "group_ids": [item.get("group_id", "") for item in items],
        },
    )


def write_judge_tasks(document: Dict[str, Any], phase_dir: str) -> str:
    """Write ``human_decision_tasks.json`` and return its path."""
    path = os.path.join(phase_dir, JUDGE_TASKS_FILENAME)
    write_task_file(path, document)
    return path


# ---------------------------------------------------------------------------
# Consumer: read, validate and ingest verdicts
# ---------------------------------------------------------------------------

@dataclass
class VerdictIngest:
    """The outcome of reading every verdict file in a phase dir."""

    #: ``group_id -> verdict`` in the wire vocabulary, first-wins on identical
    #: duplicates.
    verdicts: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    #: Schema and structural problems, each naming the file and the index in
    #: ``verdicts`` it came from.
    errors: List[str] = field(default_factory=list)
    #: In-scope ``group_id``s no verdict covered. These stay
    #: ``needs-human-decision`` — never silently approved or dropped.
    unresolved: List[str] = field(default_factory=list)
    #: ``group_id``s that appeared more than once with differing objects.
    conflicts: List[str] = field(default_factory=list)
    #: Verdict ``group_id``s that match no in-scope item.
    unexpected: List[str] = field(default_factory=list)
    files_read: List[str] = field(default_factory=list)
    #: ``group_id -> the verdict file it was read from``.
    sources: Dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors and not self.conflicts


def _supply_verdict_version(document: Any) -> Optional[str]:
    try:
        from .schema_validator import supply_schema_version
    except ImportError:  # pragma: no cover - direct-script import shim
        from utils.schema_validator import supply_schema_version
    return supply_schema_version(document, "human_decision_verdicts.schema.json")


def _schema_version_supplied(subject: str, version: str) -> str:
    try:
        from .schema_validator import schema_version_supplied
    except ImportError:  # pragma: no cover - direct-script import shim
        from utils.schema_validator import schema_version_supplied
    return schema_version_supplied(subject, version)


def read_verdict_files(phase_dir: str) -> List[Tuple[str, Any, List[str]]]:
    """Read and schema-validate every verdict file in ``phase_dir``.

    Returns:
        ``[(path, document_or_None, errors)]`` sorted by path, so ingest order is
        deterministic regardless of filesystem enumeration order.
    """
    results: List[Tuple[str, Any, List[str]]] = []
    for path in sorted(glob.glob(os.path.join(phase_dir, VERDICT_FILE_PATTERN))):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                document = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            results.append((path, None, [f"{path}: could not be read as JSON ({exc})"]))
            continue
        # Fix round 28: a host's copy of the judge's reply that left out
        # "schema_version" is read as the one version there is, said once
        # per read, never rewritten here.
        version = _supply_verdict_version(document)
        if version:
            print(
                "[human-decision] "
                + _schema_version_supplied(os.path.basename(path), version)
                + ".",
                file=sys.stderr,
            )
        errors = [
            f"{path}: {message}"
            for message in validate_human_decision_verdicts(document)
        ]
        results.append((path, document if not errors else None, errors))
    return results


def ingest_verdicts(
    *,
    phase_dir: str,
    expected_group_ids: Sequence[str] = (),
) -> VerdictIngest:
    """Parse, validate and index every verdict file in a phase dir.

    Args:
        phase_dir: The apply phase dir the invoker persisted verdicts into.
        expected_group_ids: The in-scope item ids. Anything in scope with no
            verdict is reported as unresolved (and stays needs-human-decision);
            any verdict outside scope is reported as unexpected and ignored.

    Returns:
        A :class:`VerdictIngest`.
    """
    result = VerdictIngest()
    expected = list(expected_group_ids)
    expected_set = set(expected)

    for path, document, errors in read_verdict_files(phase_dir):
        result.files_read.append(path)
        if errors:
            result.errors.extend(errors)
            continue
        for index, verdict in enumerate(document.get("verdicts", [])):
            group_id = verdict["group_id"]
            if expected_set and group_id not in expected_set:
                result.unexpected.append(group_id)
                continue
            previous = result.verdicts.get(group_id)
            if previous is None:
                result.verdicts[group_id] = verdict
                result.sources[group_id] = path
                continue
            if previous == verdict:
                # A duplicate that says the same thing is harmless: first wins.
                continue
            result.conflicts.append(group_id)
            result.errors.append(
                f"{path}: verdicts[{index}] repeats group_id {group_id!r} with a "
                f"different verdict than an earlier file. Duplicate verdicts are "
                f"an error unless the objects are identical; delete the wrong "
                f"file and re-run the judge for that group."
            )

    result.unresolved = [
        group_id for group_id in expected if group_id not in result.verdicts
    ]
    return result


# ---------------------------------------------------------------------------
# Who judged
# ---------------------------------------------------------------------------

def native_judge_label(host_id: Optional[str]) -> str:
    """The judge name for a verdict the host's own agent wrote (no executor)."""
    return f"{host_id} host agent" if host_id else NATIVE_JUDGE


def judge_labels(
    phase_dir: str,
    sources: Dict[str, str],
    *,
    fallback: str = NATIVE_JUDGE,
) -> Dict[str, str]:
    """``group_id -> the runner spec that wrote its verdict file``.

    Read from the judge batch report the executor wrote when it dispatched the
    judges. A verdict file is credited to a runner only while its bytes still
    hash to what the executor recorded, so a report left over from an earlier
    executor run never names the judge of a file the host agent rewrote since;
    every other verdict gets *fallback*.
    """
    try:
        from .subagent_executor import batch_report_path
    except ImportError:  # pragma: no cover
        from utils.subagent_executor import batch_report_path
    runner_by_path: Dict[str, str] = {}
    try:
        with open(batch_report_path(phase_dir, "human_decision_judge"),
                  "r", encoding="utf-8") as handle:
            report = json.load(handle)
    except (OSError, json.JSONDecodeError):
        report = None
    if isinstance(report, dict):
        provenance = report.get("batch_provenance")
        for row in report.get("tasks") or []:
            if not isinstance(row, dict):
                continue
            path, runner = row.get("output_path"), row.get("runner")
            if not path or not runner:
                continue
            if not isinstance(provenance, dict):
                continue
            prov = provenance.get(str(row.get("task_id")))
            if not isinstance(prov, dict) or not prov.get("sha256"):
                continue
            if file_bytes_sha256(path) != prov["sha256"]:
                continue
            runner = prov.get("runner") or runner
            runner_by_path[os.path.realpath(path)] = str(runner)
    labels: Dict[str, str] = {}
    for group_id, path in sources.items():
        runner = runner_by_path.get(os.path.realpath(path))
        if runner is None:
            runner = _with_declared_model(fallback, path)
        labels[group_id] = runner
    return labels


def _with_declared_model(fallback: str, path: str) -> str:
    """A native judge's label, plus the model it says it is, when it said.

    "claude-code host agent" names no model (2026-10-01). The verdict file's
    optional ``judge`` is the subagent's own account of itself, so it only
    qualifies a native label, never "unrecorded" or an executor's.
    """
    if not str(fallback).endswith("host agent"):
        return fallback
    try:
        with open(path, "r", encoding="utf-8") as handle:
            declared = (json.load(handle) or {}).get("judge")
    except (OSError, json.JSONDecodeError, AttributeError):
        return fallback
    declared = str(declared or "").strip()
    return f"{declared} ({fallback})" if declared and len(declared) <= 80 else fallback


def _decided_reason(judge: str, reason: str) -> str:
    return f"Agent decide [{judge}]: {reason}"


# ---------------------------------------------------------------------------
# Recording — byte-identical to what an interactive pass produces
# ---------------------------------------------------------------------------

def _batch_id(group_ids: Sequence[str]) -> str:
    """Deterministic batch id for a judged set (stable across re-runs)."""
    return JUDGE_BATCH_ID_PREFIX + content_hash("|".join(sorted(group_ids)))[:8]


def record_verdicts(
    *,
    state: Any,
    phase: str,
    ingest: VerdictIngest,
    items_by_group: Dict[str, Dict[str, Any]],
    judges: Optional[Dict[str, str]] = None,
    default_judge: str = NATIVE_JUDGE,
) -> Dict[str, Dict[str, Any]]:
    """Record every ingested verdict through ``record_human_decision``.

    The three-value ``decision`` is a *wire* vocabulary; what lands in state is
    today's translation exactly: ``approve`` -> ``approved``, ``skip`` ->
    ``skipped``, ``salvage`` -> ``approved`` carrying
    ``batch_action``/``decision_source`` ``judge_auto_decide_salvage`` plus
    ``salvaged_description`` and ``dropped`` in ``batch_context``. That is what
    makes a run judged through the executor produce the same recorded records —
    and therefore the same report overlay — as the interactive path that judged
    natively, apart from the ``judge`` each record names.

    Returns:
        ``group_id -> the decision record written``.
    """
    batch_id = _batch_id(list(ingest.verdicts))
    written: Dict[str, Dict[str, Any]] = {}

    for group_id, verdict in ingest.verdicts.items():
        decision = verdict["decision"]
        item = items_by_group.get(group_id, {})
        importance = (item.get("importance") or "MEDIUM").upper()
        salvaged = verdict.get("salvaged_description")
        dropped = verdict.get("dropped")
        model_reason = verdict.get("reason", "")
        judge = (judges or {}).get(group_id) or default_judge

        batch_context: Dict[str, Any] = {
            "batch_id": batch_id,
            "batch_action": _ACTION_PLAIN,
            "decision_source": _ACTION_PLAIN,
            "importance_at_decision": importance,
            "judge": judge,
        }
        if decision == DECISION_SALVAGE:
            reason = (
                f"Agent decide [{judge}] (salvaged): kept {salvaged}; "
                f"dropped {dropped}"
            )
            batch_context["batch_action"] = _ACTION_SALVAGE
            batch_context["decision_source"] = _ACTION_SALVAGE
            batch_context["salvaged_description"] = salvaged
            batch_context["dropped"] = dropped
        else:
            reason = _decided_reason(judge, model_reason)

        state.record_human_decision(
            phase=phase,
            group_id=group_id,
            decision=_RECORDED_DECISION[decision],
            reason=reason,
            batch_context=batch_context,
        )
        written[group_id] = {
            "decision": _RECORDED_DECISION[decision],
            "reason": reason,
            "batch_context": batch_context,
        }

    # Persist the wire verdicts too (including `dropped` and the salvaged text),
    # so a crash between judging and applying resumes without re-running judges.
    _persist_ingested_verdicts(state, phase, ingest)
    return written


def _persist_ingested_verdicts(state: Any, phase: str, ingest: VerdictIngest) -> None:
    """Store the raw ingested verdicts under a phase-scoped state key."""
    key = f"human_decision_verdicts_{phase}"
    stored = state.state.setdefault(key, {})
    for group_id, verdict in ingest.verdicts.items():
        stored[group_id] = dict(verdict)
    if ingest.unresolved:
        state.state.setdefault(f"human_decision_unresolved_{phase}", [])
        state.state[f"human_decision_unresolved_{phase}"] = list(ingest.unresolved)


def get_persisted_verdicts(state: Any, phase: str) -> Dict[str, Dict[str, Any]]:
    """Return the verdicts previously ingested for ``phase`` (possibly empty)."""
    return dict(state.state.get(f"human_decision_verdicts_{phase}", {}))


# ---------------------------------------------------------------------------
# Rewriting the work set
# ---------------------------------------------------------------------------

def substitute_salvaged_description(
    group: Dict[str, Any], salvaged_description: str
) -> Dict[str, Any]:
    """Replace a group's suggestion text with the salvaged rewrite, in place.

    A salvaged item is applied like an approval except the **rewritten**
    description is what gets applied — never the original — and salvage only ever
    *narrows*, so the group collapses to one suggestion carrying the rewrite. This
    runs before ``utils/suggestion_batcher.py`` sees the group, which is the only
    point at which the substitution is guaranteed to reach the apply prompt.
    """
    suggestions = group.get("suggestions") or []
    primary = dict(suggestions[0]) if suggestions else {}
    primary["desc"] = salvaged_description
    if "description" in primary or not suggestions:
        primary["description"] = salvaged_description
    group["suggestions"] = [primary]
    if "desc" in group:
        group["desc"] = salvaged_description
    if "description" in group:
        group["description"] = salvaged_description
    group["salvaged_description"] = salvaged_description
    return group


def apply_verdicts_to_work_set(
    *,
    verdicts: Dict[str, Dict[str, Any]],
    needs_human: List[Dict[str, Any]],
    valid: List[Dict[str, Any]],
    skipped: List[Dict[str, Any]],
    judges: Optional[Dict[str, str]] = None,
    default_judge: str = NATIVE_JUDGE,
) -> Dict[str, int]:
    """Rebuild the work set from the recorded verdicts.

    ``to_apply`` and the skip list are rebuilt from the *decisions*, not from the
    pre-judging snapshot: an approved or salvaged group moves into ``valid`` (with
    the rewrite substituted first), a skipped group moves into ``skipped``, and a
    group with no verdict stays in ``needs_human`` — never silently approved or
    dropped.

    Args:
        verdicts: ``group_id -> wire verdict``.
        needs_human: The needs-human-decision groups; mutated in place.
        valid: The apply set; mutated in place.
        skipped: The skipped set; mutated in place.
        judges: ``group_id -> who judged it`` (:func:`judge_labels`).
        default_judge: The judge of a group *judges* does not name.

    Returns:
        Counts keyed ``approved``/``salvaged``/``skipped``/``unresolved``.
    """
    counts = {"approved": 0, "salvaged": 0, "skipped": 0, "unresolved": 0}
    remaining: List[Dict[str, Any]] = []

    for group in needs_human:
        group_id = group_id_of(group)
        verdict = verdicts.get(group_id)
        if verdict is None:
            counts["unresolved"] += 1
            remaining.append(group)
            continue

        decision = verdict["decision"]
        judge = (judges or {}).get(group_id) or default_judge
        group["judge"] = judge
        if decision == DECISION_SKIP:
            group["validation_status"] = "skipped"
            group["reason"] = _decided_reason(judge, verdict.get("reason", ""))
            group["decision_source"] = _ACTION_PLAIN
            skipped.append(group)
            counts["skipped"] += 1
            continue

        if decision == DECISION_SALVAGE:
            substitute_salvaged_description(
                group, verdict.get("salvaged_description") or ""
            )
            group["decision_source"] = _ACTION_SALVAGE
            group["dropped"] = verdict.get("dropped")
            counts["salvaged"] += 1
        else:
            group["decision_source"] = _ACTION_PLAIN
            counts["approved"] += 1

        # Recorded as an approval either way, so it joins the apply set.
        group["validation_status"] = "valid"
        group["auto_approved"] = True
        group["auto_approval_reason"] = _decided_reason(judge, verdict.get("reason", ""))
        valid.append(group)

    needs_human[:] = remaining
    return counts
