"""The flat/PR report's view model: the payload ``report.html`` embeds and
``report_data.json`` persists.

:func:`build_report_view` turns :class:`ReportInputs` (the parameters of
``html_report_generator.generate_html_report``) into a :class:`ReportView`,
the dict the templates read. Its stages are the builders below; the ones named
``build_*``/``merge_*`` and :func:`plan_title` read nothing from disk or git,
so the code a pinned review shows comes only through the file reader it is
handed (:func:`pinned_file_reader`). The consolidated page shares
:func:`build_model_metadata` and :func:`plan_title`.

The page shows each group under several views (by file, by plan section, by
task). The payload stores every group once, in ``groups``; each view bucket
names its groups by position in that list (``groupIndexes``), and
``globalSuggestions`` names the groups whose suggestions it lists
(:func:`compact_views`). The PR page's ``hydrateViews`` rebuilds the buckets'
``suggestions`` from those indexes before anything renders, so every view
shows the very group objects the page annotates and the decision overlay
stamps. :func:`hydrate_views` is the same rebuild for a Python reader. A
bucket that already holds ``suggestions`` (a sidecar written before the views
were indexed) is read as it is. See
docs/development/review-results.md#report-payload.

This module imports ``html_report_generator``'s primitives; the generator
imports it back inside ``generate_html_report`` only, so neither import runs
the other at load time.
"""

from __future__ import annotations

import json
import re
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import (
    Any, Callable, Dict, List, Mapping, NamedTuple, Optional, Sequence, Set, TypedDict,
)

from . import html_report_generator as _hrg
from . import scope_report as _scope_report
from .metrics import describe_usage
# The git readers are read through their owner at each call: tests patch
# ``git_diff.capture_file_context``.
from . import git_diff

#: The views whose buckets list groups.
VIEW_KEYS = _hrg._GROUP_VIEWS

#: A serialized bucket's list of positions in ``groups``.
GROUP_INDEXES = "groupIndexes"

#: The flat list of the cross-cutting groups' suggestions.
GLOBAL_SUGGESTIONS = "globalSuggestions"

#: ``reader(path, line_range, context_lines=5)``: the numbered lines around
#: *line_range* in the reviewed version of *path*, or ``None``.
FileReader = Callable[..., Optional[List[Dict[str, Any]]]]


@dataclass
class ReportInputs:
    """``generate_html_report``'s parameters, one field each; its docstring
    says what each one does."""

    groups: List[Dict[str, Any]]
    plan_path: Path
    phase_dir: Path
    phase_type: str
    models: List[str]
    failed_models: Optional[Dict[str, str]] = None
    validation_results: Optional[List[Dict[str, Any]]] = None
    base_ref: Optional[str] = None
    tasks_path: Optional[Path] = None
    template_style: str = "pr"
    diff_data: Optional[Dict[str, Any]] = None
    data_source: str = "auto"
    file_snapshots: Optional[Dict[str, list]] = None
    served_models: Optional[Dict[str, Dict[str, Any]]] = None
    usage: Optional[Dict[str, Dict[str, Any]]] = None
    commit_review: Optional[Mapping[str, Any]] = None
    requested_models: Optional[int] = None
    salvage_requested: Optional[Sequence[str]] = None
    head_ref: Optional[str] = None
    repo_root: Optional[str] = None
    file_labels: Optional[Dict[str, str]] = None
    scope_state: Optional[Mapping[str, Any]] = None


class ViewBucket(TypedDict, total=False):
    """One fileView/sectionView/taskView entry."""

    #: The bucket's groups (objects of ``groups``) once hydrated.
    suggestions: List[Dict[str, Any]]
    #: Their positions in ``groups``, as stored.
    groupIndexes: List[int]
    suggestionCount: int
    maxImportance: str
    #: Set on every sectionView and task entry.
    hasSuggestions: bool
    #: taskView only: the task's metadata, or ``None``.
    taskMetadata: Optional[Dict[str, Any]]


class ReportView(TypedDict, total=False):
    """The flat/PR payload's keys. Every key the templates read is here; a
    key marked *conditional* is absent, never empty, when it does not apply,
    so a default run's ``report_data.json`` carries none of them."""

    planPath: str
    planTitle: str
    title: str
    baseRef: Optional[str]
    phase: str
    readOnly: bool
    generatedAt: str
    models: List[str]
    modelMetadata: Dict[str, Dict[str, Any]]
    failedModels: Dict[str, Any]
    sortConfig: Dict[str, Any]
    groups: List[Dict[str, Any]]
    #: ~15 lines around what each cited reference names (hover text).
    sectionContexts: Dict[str, str]
    logSnippets: Dict[str, str]
    fileView: Dict[str, ViewBucket]
    sectionView: Dict[str, ViewBucket]
    taskView: Dict[str, ViewBucket]
    #: Hydrated: the suggestions of fileView ``_global``'s groups.
    globalSuggestions: List[Dict[str, Any]]
    #: The section text of each heading a reference or the plan names.
    fullSectionContexts: Dict[str, str]
    sectionOrder: List[str]
    notices: List[Dict[str, str]]
    summary: Dict[str, int]
    requestedModels: int  # conditional: the caller counted a requested set
    servedModels: Dict[str, Dict[str, Any]]  # conditional: models_served recorded
    usageTotal: Dict[str, Any]  # conditional: some adapter reported usage
    usageTotalLabel: str  # conditional, with usageTotal
    commitRange: Dict[str, Any]  # conditional: a commit review
    diffData: Dict[str, Any]  # conditional: diff hunks were captured or passed
    fileContexts: Dict[str, Any]  # conditional: a suggestion cites a file
    umbrellaMap: Dict[str, Any]  # conditional: the consolidated data source
    dataSource: str
    templateStyle: str
    scopePolicy: Dict[str, Any]
    #: Added by regenerate_report_with_human_decisions.
    humanDecisionsSummary: Dict[str, int]
    #: Added by code_review_orchestrator.record_review_scope_in_report_data.
    diffCoverage: Dict[str, Any]
    reviewScope: Dict[str, Any]


# ---------------------------------------------------------------------------
# Pure builders
# ---------------------------------------------------------------------------


def build_model_metadata(
    models: Sequence[str],
    served: Optional[Mapping[str, Any]] = None,
    usage: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Dict[str, Any]]:
    """``modelMetadata``: each model's badge data, for every report page.

    The badge text is ``metadata.model`` on every page (``getModelBadgeHtml``,
    templates/shared/report_core.js), so what it says is
    settled here once, from *served* (``models_served``) and *usage*:

    - a fallback model served the turn: ``<model> (fallback: <served>)``,
      because a report must never credit the primary with a fallback's
      output (plan §3.6); any served entry adds ``served_model``/``fallback``;
    - the slot ran with no sandbox: ``(unsandboxed)`` and ``sandbox:
      bypassed``; a contained fallback rung names the rung
      (``sandbox_fallback_label``) and never says unsandboxed;
    - the adapter reported usage: ``usage`` plus ``usage_label``, the
      ``describe_usage`` clause the markdown ``**Models:**`` line also uses.
      A model with no usage gets neither key, never ``$0.00``.

    With neither *served* nor *usage* (a default run), each entry is exactly
    ``get_model_metadata``'s.
    """
    metadata: Dict[str, Dict[str, Any]] = {}
    for model in models:
        entry = _hrg.get_model_metadata(model)
        served_entry = (served or {}).get(model)
        if isinstance(served_entry, dict) and served_entry.get("served_model"):
            served_model = served_entry["served_model"]
            entry["served_model"] = served_model
            entry["fallback"] = bool(served_entry.get("fallback"))
            if served_entry.get("fallback"):
                entry["model"] = f"{entry['model']} (fallback: {served_model})"
        sandbox = str(served_entry.get("sandbox") or "") if isinstance(served_entry, dict) else ""
        if sandbox == "bypassed":
            entry["sandbox"] = "bypassed"
            entry["model"] = f"{entry['model']} (unsandboxed)"
        elif sandbox.startswith(_hrg.SANDBOX_FALLBACK_WORD_PREFIX):
            entry["sandbox"] = sandbox
            entry["model"] = f"{entry['model']} ({_hrg.sandbox_fallback_label(sandbox)})"
        model_usage = (usage or {}).get(model)
        if isinstance(model_usage, dict) and model_usage:
            entry["usage"] = model_usage
            label = describe_usage(model_usage)
            if label:
                entry["usage_label"] = label
        metadata[model] = entry
    return metadata


def plan_title(text: str, fallback: str) -> str:
    """The text of the plan's first ``# `` heading, else *fallback*."""
    for line in (text or "").splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return fallback


def read_plan(plan_path: Path) -> str:
    """The plan's text, or ``""`` when it is missing or unreadable."""
    try:
        return Path(plan_path).read_text(encoding="utf-8")
    except OSError:
        return ""


def cited_section_refs(groups: Sequence[Mapping[str, Any]]) -> Set[str]:
    """Every section the groups' suggestions cite. A composite reference is
    split into the sections it names: those are the sectionView's bucket
    keys, and the whole composite string matches no heading in the plan."""
    refs: Set[str] = set()
    for group in groups:
        for sugg in group.get("suggestions", group.get("issues", [])):
            refs.update(_hrg.split_section_refs(sugg.get("reference", sugg.get("section", ""))))
    return refs


class PlanSections(NamedTuple):
    """The plan's text as the report shows it."""

    #: ``sectionContexts``: hover text around each cited reference.
    contexts: Dict[str, str]
    #: ``sectionOrder``: every section heading, in the plan's order.
    order: List[str]
    #: ``fullSectionContexts``: the section text of each heading that the
    #: plan or a reference names (a reference naming no heading has none).
    full: Dict[str, str]


def build_plan_sections(plan_content: str, section_refs: Set[str]) -> PlanSections:
    """The hover contexts, the section order and the full section texts, for
    every plan section and every cited reference, so each plan section has
    rendered content in the PR view."""
    order = _hrg.extract_plan_section_order(plan_content)
    full_refs = set(order) | set(section_refs)
    return PlanSections(
        contexts=_hrg.extract_section_contexts(plan_content, section_refs),
        order=order,
        full=(_hrg.extract_section_contexts(plan_content, full_refs, full_section=True)
              if full_refs else {}),
    )


def _normalize_section_ref(ref: str) -> str:
    """Strip leading # and lowercase for fuzzy matching."""
    return ref.lstrip('#').strip().lower()


def _find_canonical_match(ref: str, canonical_map: Dict[str, str]) -> Optional[str]:
    """The sectionView key a sectionOrder heading matches: exact, else a
    prefix either way (a reviewer's truncated reference)."""
    norm = _normalize_section_ref(ref)
    if norm in canonical_map:
        return canonical_map[norm]
    for canon_norm, canon_key in canonical_map.items():
        if canon_norm.startswith(norm) or norm.startswith(canon_norm):
            return canon_key
    return None


def merge_section_view(section_view: Dict[str, Any], section_order: Sequence[str]) -> Dict[str, Any]:
    """*section_view* with every plan section in it (in place, returned).

    A heading no bucket matches gets an empty entry, so the PR view shows the
    whole document; every entry gets ``hasSuggestions``.
    """
    canonical = {_normalize_section_ref(key): key for key in section_view}
    for ref in section_order:
        match = _find_canonical_match(ref, canonical)
        if match is None:
            section_view[ref] = {
                "suggestions": [],
                "suggestionCount": 0,
                "maxImportance": "",
                "hasSuggestions": False,
            }
        else:
            section_view[match]["hasSuggestions"] = True
    for entry in section_view.values():
        if "hasSuggestions" not in entry:
            entry["hasSuggestions"] = len(entry.get("suggestions", [])) > 0
    return section_view


def merge_task_view(task_view: Dict[str, Any],
                    tasks_metadata: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    """*task_view* with every task of *tasks_metadata* in it (in place, returned).

    A task with no bucket gets an empty entry carrying its metadata; every
    task entry gets ``hasSuggestions``. Only bare ``T###`` keys are tasks:
    ``_parse_tasks_markdown`` also keys each task under its header text, the
    same meta dict, which must not become a second, empty entry.
    """
    if tasks_metadata:
        existing: Set[str] = set()
        for key in task_view:
            if key.startswith('_'):
                continue
            m = re.match(r'(T\d+)', key)
            existing.add(m.group(1) if m else key)
        for task_id, meta in tasks_metadata.items():
            if not re.fullmatch(r'T\d+', task_id) or task_id in existing:
                continue
            task_view[task_id] = {
                "taskMetadata": meta,
                "suggestions": [],
                "suggestionCount": 0,
                "maxImportance": "",
                "hasSuggestions": False,
            }
            existing.add(task_id)
    for key, entry in task_view.items():
        if not key.startswith('_') and "hasSuggestions" not in entry:
            entry["hasSuggestions"] = len(entry.get("suggestions", [])) > 0
    return task_view


def _line_range(sugg: Mapping[str, Any]) -> Optional[List[int]]:
    line_range = sugg.get("lineRange")
    if line_range and isinstance(line_range, (list, tuple)) and len(line_range) >= 1:
        return list(line_range)
    return None


def referenced_files(groups: Sequence[Mapping[str, Any]]) -> List[str]:
    """The files the suggestions cite, first-seen order."""
    seen: Dict[str, None] = {}
    for group in groups:
        for sugg in group.get("suggestions", []):
            path = _hrg._extract_file_path(sugg.get("fileRef", ""))
            if path:
                seen.setdefault(path, None)
    return list(seen)


def build_file_contexts(
    groups: Sequence[Mapping[str, Any]],
    diff: Optional[Mapping[str, Any]],
    reader: FileReader,
    labels: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    """``fileContexts``: what the page can show of each cited file.

    Per file, the first of: its diff hunks (``source: diff``), the lines
    *reader* returns around the first suggestion's range (``file``), that
    suggestion's ``anchorText`` (``anchor``), nothing (``none``). Then every
    file without lines yet gets the lines around all its suggestions' ranges
    merged into one (the template shows ±5 lines around each), so an
    outside-the-diff suggestion has context too. *labels* (``{path: label}``,
    a path absent at ``head``) are carried as ``label``. A reader that raises
    counts as no lines.
    """
    contexts: Dict[str, Any] = {}
    for group in groups:
        for sugg in group.get("suggestions", []):
            path = _hrg._extract_file_path(sugg.get("fileRef", ""))
            if not path or path in contexts:
                continue
            if diff and path in diff:
                contexts[path] = {"source": "diff", "available": True}
                continue
            line_range = _line_range(sugg)
            if line_range:
                try:
                    lines = reader(path, line_range)
                except Exception:  # noqa: BLE001 - a context is best-effort
                    lines = None
                if lines is not None:
                    contexts[path] = {"source": "file", "lines": lines, "available": True}
                    continue
            anchor = sugg.get("anchorText")
            contexts[path] = ({"source": "anchor", "anchorText": anchor, "available": True}
                              if anchor else {"source": "none", "available": False})

    ranges: Dict[str, List[List[int]]] = {}
    for group in groups:
        for sugg in group.get("suggestions", []):
            path = _hrg._extract_file_path(sugg.get("fileRef", ""))
            line_range = _line_range(sugg)
            if path and line_range:
                ranges.setdefault(path, []).append(line_range)
    for path, found in ranges.items():
        if contexts.get(path, {}).get("lines"):
            continue
        merged = [min(r[0] for r in found), max(r[1] if len(r) > 1 else r[0] for r in found)]
        try:
            lines = reader(path, merged, context_lines=5)
        except Exception:  # noqa: BLE001 - a context is best-effort
            lines = None
        if lines is None:
            continue
        if path in contexts:
            contexts[path]["lines"] = lines
        else:
            contexts[path] = {"source": "file", "lines": lines, "available": True}

    for path, label in (labels or {}).items():
        if path in contexts and label:
            contexts[path]["label"] = label
    return contexts


def build_summary(effective_groups: Sequence[Mapping[str, Any]],
                  groups_data: Sequence[Mapping[str, Any]]) -> Dict[str, int]:
    """``summary``: the group and suggestion totals and the status counts."""
    def count(status: str) -> int:
        return sum(1 for g in groups_data if g["validationStatus"] == status)

    return {
        "totalGroups": len(effective_groups),
        "totalSuggestions": sum(
            len(g.get("suggestions", g.get("issues", []))) for g in effective_groups),
        "validCount": count("valid"),
        "invalidCount": count("invalid"),
        "needsHumanCount": count("needs-human-decision"),
        "validationFailedCount": count("validation_failed"),
    }


# ---------------------------------------------------------------------------
# Inputs that read the disk or git
# ---------------------------------------------------------------------------


def pinned_file_reader(head_ref: Optional[str],
                       snapshots: Optional[Mapping[str, list]]) -> FileReader:
    """The reader :func:`build_file_contexts` gets: ``capture_file_context``
    over *snapshots*, except that a pinned review (*head_ref* set) never
    falls back to the disk. A path missing from its snapshots is absent at
    ``head``, so it has no file context whatever the disk holds."""
    def read(path: str, line_range: List[int],
             context_lines: int = 5) -> Optional[List[Dict[str, Any]]]:
        if head_ref is not None and (not snapshots or path not in snapshots):
            return None
        return git_diff.capture_file_context(path, line_range, context_lines=context_lines,
                                             file_snapshots=snapshots)
    return read


def _code_sources(inputs: ReportInputs, files: List[str]):
    """``(diff data, snapshots)`` for the cited *files*.

    Passed-in diff data wins over a capture against ``base_ref``; a pinned
    review reads the files as ``head`` holds them unless snapshots were
    passed. A failed git read warns and leaves that source empty.
    """
    base_ref = inputs.base_ref or None
    diff = inputs.diff_data
    if diff is None and base_ref is not None and files:
        try:
            if inputs.head_ref is None:
                diff = git_diff.capture_diff_hunks(base_ref, files)
            else:
                diff = git_diff.capture_diff_hunks(base_ref, files, head_ref=inputs.head_ref,
                                                   cwd=inputs.repo_root)
        except Exception as exc:  # noqa: BLE001 - the report renders without hunks
            warnings.warn(f"Failed to capture diff hunks: {exc}")
            diff = None
    snapshots = inputs.file_snapshots
    if inputs.head_ref is not None and snapshots is None and files:
        try:
            snapshots = git_diff.capture_file_snapshots_at(inputs.head_ref, files,
                                                           cwd=inputs.repo_root)
        except Exception as exc:  # noqa: BLE001 - no snapshot means no file context
            warnings.warn(f"Failed to read files at {inputs.head_ref[:12]}: {exc}")
            snapshots = {}
    return diff, snapshots


def load_tasks_metadata(tasks_path: Optional[Path]) -> Optional[Dict[str, Any]]:
    """The task list's metadata by task id: ``tasks.json``, or ``tasks.md``
    through ``_parse_tasks_markdown``; another suffix tries JSON first.
    ``None`` with no path, or when the file cannot be read."""
    if tasks_path is None:
        return None
    try:
        raw = Path(tasks_path).read_text(encoding="utf-8")
    except OSError as exc:
        _hrg.logger.warning("Could not load tasks metadata from %s: %s", tasks_path, exc)
        return None
    if Path(tasks_path).suffix == ".json":
        return json.loads(raw)
    if Path(tasks_path).suffix == ".md":
        return _hrg._parse_tasks_markdown(raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return _hrg._parse_tasks_markdown(raw)


def build_groups_data(effective_groups: Sequence[Dict[str, Any]],
                      validation_results: Optional[List[Dict[str, Any]]],
                      scope_round: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """``groups``: each group's page data with its scope entry and any
    consolidated metadata, umbrella scopes derived, sorted by priority."""
    groups_data = []
    for index, group in enumerate(effective_groups):
        built = _hrg._build_group_data(group, index, validation_results)
        built[_scope_report.ENTRY_KEY] = _scope_report.group_scope(group, scope_round)
        if group.get("_consolidated_meta") is not None:
            built["_consolidatedMeta"] = group["_consolidated_meta"]
        if group.get("_umbrella_first"):
            built["_umbrellaFirst"] = True
        if group.get("_is_consolidated_flat"):
            built["_isConsolidatedFlat"] = True
        groups_data.append(built)
    # An umbrella's derived scope tag, on the metadata dict its groups share.
    _hrg._scope_umbrellas(groups_data)
    return _hrg.sort_groups_by_priority(groups_data)


# ---------------------------------------------------------------------------
# The view
# ---------------------------------------------------------------------------


def build_report_view(inputs: ReportInputs) -> ReportView:
    """The flat/PR payload for *inputs*, views hydrated (group objects shared).

    Raises ``ValueError`` for an unknown ``data_source``, and what
    ``_load_data_source`` raises for a missing or malformed
    ``consolidated.json`` under ``data_source="consolidated"``.
    """
    if inputs.data_source not in ("auto", "consolidated", "grouped"):
        raise ValueError(
            f"data_source must be 'auto', 'consolidated', or 'grouped', "
            f"got {inputs.data_source!r}"
        )
    plan_path, phase_dir = Path(inputs.plan_path), Path(inputs.phase_dir)
    effective_groups, umbrella_map, source_notices = _hrg._load_data_source(
        phase_dir, inputs.data_source, inputs.groups)

    plan_content = read_plan(plan_path)
    section_refs = cited_section_refs(effective_groups)
    log_snippets = _hrg.embed_log_snippets(phase_dir, inputs.models)
    scope_round = _scope_report.round_info(
        inputs.scope_state if inputs.scope_state is not None
        else _scope_report.read_state(phase_dir),
        inputs.phase_type, effective_groups)
    groups_data = build_groups_data(effective_groups, inputs.validation_results, scope_round)

    file_view = _hrg.build_file_view(groups_data)
    section_view = _hrg.build_section_view(groups_data)
    tasks_metadata = load_tasks_metadata(inputs.tasks_path)
    task_view = _hrg.build_task_view(groups_data, tasks_metadata)

    files = referenced_files(groups_data)
    diff, snapshots = _code_sources(inputs, files)
    file_contexts = build_file_contexts(
        groups_data, diff, pinned_file_reader(inputs.head_ref, snapshots), inputs.file_labels)

    sections = build_plan_sections(plan_content, section_refs)
    merge_section_view(section_view, sections.order)
    merge_task_view(task_view, tasks_metadata)

    title = plan_title(plan_content, plan_path.stem)
    view: ReportView = {
        "planPath": str(plan_path),
        "planTitle": title,
        "title": title,
        "baseRef": inputs.base_ref or None,
        "phase": inputs.phase_type,
        # Interactive controls are enabled in every phase: review-tasks
        # supports skip/override too (review_orchestrator_base.aggregate_results).
        "readOnly": False,
        "generatedAt": datetime.now().isoformat(),
        "models": inputs.models,
        "modelMetadata": build_model_metadata(inputs.models, inputs.served_models, inputs.usage),
        "failedModels": inputs.failed_models or {},
        "sortConfig": _hrg.build_sort_config(),
        "groups": groups_data,
        "sectionContexts": sections.contexts,
        "logSnippets": log_snippets,
        "fileView": file_view,
        "sectionView": section_view,
        "taskView": task_view,
        "globalSuggestions": [
            s for group in file_view.get("_global", {}).get("suggestions", [])
            for s in group.get("suggestions", [])
        ],
        "fullSectionContexts": sections.full,
        "sectionOrder": sections.order,
        "notices": _hrg.build_report_notices(
            source_notices, inputs.failed_models, inputs.requested_models,
            inputs.salvage_requested, served_models=inputs.served_models,
        ),
        "summary": build_summary(effective_groups, groups_data),
    }

    # The denominator of "N of M requested", as the caller counted it: absent
    # rather than guessed when the caller holds no requested set.
    if inputs.requested_models is not None:
        view["requestedModels"] = int(inputs.requested_models)
    # The attribution's structured half, only when models_served recorded
    # something, so a default run's report_data.json gains no key (§3.6).
    if inputs.served_models:
        view["servedModels"] = inputs.served_models
    # The run total, only when some adapter reported usage: never `$0.00`.
    usage_total = _hrg.sum_usage(inputs.usage)
    if usage_total:
        view["usageTotal"] = usage_total
        total_label = describe_usage(usage_total)
        if total_label:
            view["usageTotalLabel"] = total_label
    # A commit review's header, filter, badges and export help
    # (plans/review-commits.md §2.10), read back by a regeneration with no git.
    if inputs.commit_review:
        view[_hrg.COMMIT_RANGE_KEY] = _hrg.commit_range_report_data(inputs.commit_review, groups_data)
    if diff is not None:
        view["diffData"] = diff
    if file_contexts:
        view["fileContexts"] = file_contexts
    if umbrella_map is not None:
        view["umbrellaMap"] = umbrella_map
        view["dataSource"] = "consolidated"
    else:
        view["dataSource"] = "grouped"
    # A post-apply regeneration re-renders with the same template.
    view["templateStyle"] = inputs.template_style
    # The round's policy line, legend and tag counts (distinct groups).
    view[_scope_report.REPORT_KEY] = _scope_report.report_block(
        scope_round, _hrg._scope_counts(groups_data))
    return view


# ---------------------------------------------------------------------------
# Serialized views
# ---------------------------------------------------------------------------


def _compact_bucket(bucket: Any, index_of: Mapping[int, int]) -> Any:
    """*bucket* with its ``suggestions`` (group objects) replaced by their
    positions in ``groups``, in the same place among its keys; unchanged when
    any member is not one of ``groups``' own objects."""
    members = bucket.get("suggestions") if isinstance(bucket, dict) else None
    if not isinstance(members, list):
        return bucket
    indexes = [index_of.get(id(group)) for group in members]
    if any(index is None for index in indexes):
        return bucket
    return {
        (GROUP_INDEXES if key == "suggestions" else key): (indexes if key == "suggestions" else value)
        for key, value in bucket.items()
    }


def _compact_suggestions(suggestions: List[Any], groups: Sequence[Any]) -> Optional[Dict[str, Any]]:
    """``{"groupIndexes": [...]}`` naming the groups whose suggestions, in
    order, are exactly *suggestions*; ``None`` when no such run of groups is."""
    owner = {
        id(suggestion): index
        for index, group in enumerate(groups) if isinstance(group, dict)
        for suggestion in group.get("suggestions") or ()
    }
    indexes: List[int] = []
    for suggestion in suggestions:
        index = owner.get(id(suggestion))
        if index is None:
            return None
        if not indexes or indexes[-1] != index:
            indexes.append(index)
    rebuilt = [id(s) for index in indexes for s in groups[index].get("suggestions") or ()]
    if rebuilt != [id(s) for s in suggestions]:
        return None
    return {GROUP_INDEXES: indexes}


def compact_views(report_data: Mapping[str, Any]) -> Dict[str, Any]:
    """A shallow copy of *report_data* whose views name their groups by index.

    Lossless by construction: a bucket (or ``globalSuggestions``) is indexed
    only when :func:`hydrate_views` rebuilds exactly the objects it held, so
    a payload whose views hold anything else keeps them whole.
    """
    groups = report_data.get("groups") or []
    index_of = {id(group): index for index, group in enumerate(groups)}
    payload = dict(report_data)
    for name in VIEW_KEYS:
        view = report_data.get(name)
        if isinstance(view, dict):
            payload[name] = {key: _compact_bucket(bucket, index_of) for key, bucket in view.items()}
    flat = report_data.get(GLOBAL_SUGGESTIONS)
    if isinstance(flat, list):
        indexed = _compact_suggestions(flat, groups)
        if indexed is not None:
            payload[GLOBAL_SUGGESTIONS] = indexed
    return payload


def hydrate_views(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """Rebuild *report_data*'s views from ``groups`` (in place) and return it.

    The Python twin of the PR template's ``hydrateViews``: each indexed
    bucket gains ``suggestions``, the groups its ``groupIndexes`` name (an
    index outside ``groups`` is dropped), and an indexed
    ``globalSuggestions`` becomes the flat list of those groups' suggestions.
    A bucket that already holds ``suggestions`` is left as it is.
    """
    groups = report_data.get("groups") or []

    def picked(indexes: Any) -> List[Any]:
        return [groups[index] for index in indexes
                if type(index) is int and 0 <= index < len(groups)]

    for name in VIEW_KEYS:
        view = report_data.get(name)
        if not isinstance(view, dict):
            continue
        for bucket in view.values():
            if (isinstance(bucket, dict) and isinstance(bucket.get(GROUP_INDEXES), list)
                    and not isinstance(bucket.get("suggestions"), list)):
                bucket["suggestions"] = picked(bucket[GROUP_INDEXES])
    flat = report_data.get(GLOBAL_SUGGESTIONS)
    if isinstance(flat, dict) and isinstance(flat.get(GROUP_INDEXES), list):
        report_data[GLOBAL_SUGGESTIONS] = [
            suggestion for group in picked(flat[GROUP_INDEXES]) if isinstance(group, dict)
            for suggestion in group.get("suggestions") or ()
        ]
    return report_data
