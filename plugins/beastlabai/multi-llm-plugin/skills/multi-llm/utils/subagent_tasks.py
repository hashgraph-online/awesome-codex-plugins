#!/usr/bin/env python3
"""Materialized task files: construction, hashing, budget and refusals (D2a/D2c-D2h).

``utils/subagent_prompts.py`` renders the prompt text; this module owns
everything else a materialized task file needs:

* the canonical task object and its ``tasks_schema_version: 2`` file wrapper,
  validated against ``schemas/subagent_tasks.schema.json`` **on write and on
  read** (D2g);
* the ``inputs`` hash block that binds a task to the inputs it was materialized
  from, computed with the same content hash ``StateManager`` uses for the plan,
  and the resume-time recomputation that refuses a stale file with **exit 3**;
* the ``executor_role`` derivation that replaces every ``subagent_type ==
  "human"`` test (D2h);
* the pre-dispatch refusals — ``result_channel: inline-json``,
  ``executor_role: human``, and ``context_mode: workspace-read`` against a runner
  with no workspace-read capability — as reusable functions, so the Phase-3
  executor calls exactly the code these tests pin (D2a/D2c);
* the D2d prompt budget: a per-runner ceiling measured in **UTF-16 code units**
  (astral characters count double, the unit Windows actually limits), unbounded
  for a non-argv transport, with over-budget resolved by splitting the batch or
  downgrading to ``workspace-read`` — never by silently truncating.

Nothing here dispatches anything; ``utils/subagent_executor.py`` (D3) is the
consumer.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:  # pragma: no cover - import shim mirrors the rest of utils/
    from .schema_validator import (
        TASKS_SCHEMA_VERSION,
        validate_subagent_task,
        validate_subagent_task_file,
    )
    from .llm_client import (
        CMDLINE_CAP_UTF16_BATCH,
        CMDLINE_CAP_UTF16_NATIVE,
        CMDLINE_UTF16_HEADROOM,
        _utf16_code_units,
    )
except ImportError:  # pragma: no cover
    from utils.schema_validator import (
        TASKS_SCHEMA_VERSION,
        validate_subagent_task,
        validate_subagent_task_file,
    )
    from utils.llm_client import (
        CMDLINE_CAP_UTF16_BATCH,
        CMDLINE_CAP_UTF16_NATIVE,
        CMDLINE_UTF16_HEADROOM,
        _utf16_code_units,
    )


__all__ = [
    "TASKS_SCHEMA_VERSION",
    "KINDS",
    "READ_KINDS",
    "WRITE_KINDS",
    "SHARED_ARTIFACT_WRITE_KINDS",
    "APPLY_WRITE_KINDS",
    "PHASE_BY_WRITE_KIND",
    "WRITE_KIND_BY_PHASE",
    "PRIOR_CHANGES_TOKEN",
    "is_write_kind",
    "make_write_task",
    "write_output_name",
    "implement_output_name",
    "WRITE_OUTPUT_NAME_TEMPLATE",
    "declared_file_set",
    "snapshot_file_set",
    "TaskFileError",
    "TaskRefusal",
    "content_hash",
    "file_content_hash",
    "build_inputs",
    "derive_executor_role",
    "subagent_type_for_role",
    "make_task",
    "make_task_file",
    "tasks_of",
    "write_task_file",
    "read_task_file",
    "assert_dispatchable",
    "refuse_reason",
    "resolve_output_path",
    "utf16_units",
    "preferred_prompt_transport",
    "prompt_budget_utf16",
    "PromptBudget",
]


#: The read/analyze kinds: their answer IS a JSON document and no invoker of them
#: ever needs write access (D3e pins them to ``agent-readonly``).
READ_KINDS = (
    "validation",
    "revalidation",
    "consolidation",
    "salvage",
    "human_decision_judge",
    "task_generation",
)

#: The write kinds (D3f/D3g/D3n): their answer is the *edit*, and the JSON they
#: print on stdout is the batch result contract, not the deliverable. One kind per
#: phase rather than a single ``apply`` kind, because the four differ in what they
#: snapshot, how they partition and which log they append to — and because the
#: per-kind ``output_name`` pattern is what stops one phase's result from being
#: written into another's reaggregation glob (D3f).
WRITE_KINDS = (
    "apply_suggestions",
    "apply_task_suggestions",
    "apply_code_fixes",
    "implement",
)

#: Every kind a materialized task file may declare.
KINDS = READ_KINDS + WRITE_KINDS

#: Write kinds that edit ONE shared artifact, so their batches are strictly
#: sequential no matter what the driver config permits (D3h — this is the
#: batchers' own invariant, enforced here rather than trusted from them).
SHARED_ARTIFACT_WRITE_KINDS = ("apply_suggestions", "apply_task_suggestions")

#: The apply phases' write kinds: a batch of review items, any of which the
#: batch may decline with a reason (the result contract's ``declined``, fix
#: round 18). ``implement`` is not one: its batch is one task of the plan, and
#: a task its runner will not do is ``failed``, for the user to answer.
APPLY_WRITE_KINDS = ("apply_suggestions", "apply_task_suggestions", "apply_code_fixes")

#: The phase name each write kind belongs to, so the scheduler's ``prior_changes``
#: and ``metrics`` calls use the same ``--phase`` value the markdown specifies.
PHASE_BY_WRITE_KIND = {
    "apply_suggestions": "apply-suggestions",
    "apply_task_suggestions": "apply-task-suggestions",
    "apply_code_fixes": "apply-code-fixes",
    "implement": "implement",
}

#: The reverse map, for a caller that knows only the phase word.
WRITE_KIND_BY_PHASE = {phase: kind for kind, phase in PHASE_BY_WRITE_KIND.items()}


def is_write_kind(kind: Optional[str]) -> bool:
    """Whether ``kind`` is an edit-capable (``agent-write``) task kind."""
    return kind in WRITE_KINDS


#: The literal token every apply prompt carries and the scheduler substitutes
#: immediately before dispatch (D3n). Defined here, next to the refusals, because
#: "this token must never reach a runner" is a dispatch contract rather than a
#: string one producer happens to use.
#: A prompt-template placeholder, not an authentication credential.
PRIOR_CHANGES_TOKEN: str = "{prior_changes_context}"

#: Providers that carry a real non-argv prompt transport (D2d). Kept here rather
#: than imported so this module stays usable without instantiating adapters.
_NON_ARGV_TRANSPORT_PROVIDERS = ("claude-code", "codex", "opencode")


class TaskFileError(Exception):
    """A materialized task file cannot be used, and the phase must re-materialize.

    Carries ``exit_code = 3`` ("needs a human"): every raise site names the
    offending file, what changed, and the fix.
    """

    exit_code = 3

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class TaskRefusal(TaskFileError):
    """A single task must not be dispatched. ``task_id`` is always named."""

    def __init__(self, message: str, task_id: str = "") -> None:
        super().__init__(message)
        self.task_id = task_id


# ---------------------------------------------------------------------------
# Hashing — the same content hash StateManager already uses for the plan
# ---------------------------------------------------------------------------

def content_hash(text: str) -> str:
    """Return the 16-char content hash used throughout the skill.

    Identical to ``StateManager._compute_plan_hash``'s digest so a task file's
    ``inputs.plan_sha256`` and ``state.plan_hash`` are directly comparable.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def file_content_hash(path: Optional[str]) -> str:
    """Hash a file's contents, or return ``""`` when it does not exist.

    Mirrors ``_compute_plan_hash``'s empty-string-for-missing behavior so a
    phase with no plan file (or a unit test with none) round-trips instead of
    failing the resume check.
    """
    if not path:
        return ""
    try:
        return content_hash(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return ""


def build_inputs(
    *,
    plan_file: Optional[str] = None,
    grouped_file: Optional[str] = None,
    tasks_file: Optional[str] = None,
    diff_base: Optional[str] = None,
    diff_text: Optional[str] = None,
    reviewed_code: Optional[str] = None,
    salvage_request_file: Optional[str] = None,
    items: Optional[Any] = None,
    context_plan_sha256: Optional[str] = None,
) -> Dict[str, str]:
    """Build the ``inputs`` hash block for a task file.

    Every key is optional except ``plan_sha256``, which is always present (empty
    string when the phase has no plan file). A task file is a *snapshot* and a
    phase dir outlives the run that wrote it, so these hashes are what stop a
    stale prompt from producing a confidently wrong result against text nobody is
    reviewing any more.

    ``tasks_sha256`` is added only when a phase really has a task list under
    review (review-tasks), so review-plan's block is unchanged. It is what makes
    an edited ``tasks/tasks.md`` invalidate a review-tasks validation file the
    way an edited plan already does — that phase's prompts embed the task text,
    so a stale one is as wrong as a stale plan excerpt.

    ``reviewed_code_sha256`` is the code-review equivalent: the hash of the
    **code excerpt the prompts embed**, not of the files it was cut from, so
    the thing hashed is exactly the thing a validator reads. ``diff_base``
    alone pins the ref the diff was taken *against* and moves for neither an
    edit nor a commit on the other side of it, which is how a file edited
    between fan-out and validation used to invalidate nothing. On a review
    pinned to a commit (``--head-ref``) it reads ``<base>..<head>``, and the
    excerpt is read at ``head``, so neither moves with the working tree.

    ``context_plan_sha256`` is a commit review's frozen context plan
    (``commit_range.plan_sha256``, the SHA-256 of its snapshot's bytes,
    plans/review-commits.md §2.4): passed as recorded rather than re-read, so
    a resume or a reaggregate whose snapshot no longer hashes to it is refused
    like a changed plan. Absent everywhere else, so no other block moves.
    """
    inputs: Dict[str, str] = {"plan_sha256": file_content_hash(plan_file)}
    if grouped_file is not None:
        inputs["grouped_sha256"] = file_content_hash(grouped_file)
    if tasks_file:
        inputs["tasks_sha256"] = file_content_hash(tasks_file)
    if diff_base:
        inputs["diff_base"] = diff_base
    if diff_text is not None:
        inputs["diff_sha256"] = content_hash(diff_text)
    if reviewed_code is not None:
        inputs["reviewed_code_sha256"] = content_hash(reviewed_code)
    if salvage_request_file is not None:
        inputs["salvage_request_sha256"] = file_content_hash(salvage_request_file)
    if items is not None:
        inputs["items_sha256"] = content_hash(
            json.dumps(items, sort_keys=True, ensure_ascii=False)
        )
    if context_plan_sha256 is not None:
        inputs["context_plan_sha256"] = context_plan_sha256
    return inputs


# ---------------------------------------------------------------------------
# executor_role (D2h)
# ---------------------------------------------------------------------------

def derive_executor_role(subagent_type: Optional[str]) -> str:
    """Map a legacy ``subagent_type`` onto the host-neutral executor role.

    ``"human"`` was never an agent type — it is the marker that no subagent may
    run this task — so it becomes ``"human"``. Everything else (``
    general-purpose`` carries no information; it is pure Claude Code vocabulary)
    becomes ``"agent"``.
    """
    return "human" if subagent_type == "human" else "agent"


def subagent_type_for_role(executor_role: str) -> str:
    """The Claude-Code-only ``subagent_type`` that agrees with a given role.

    The schema rejects a task whose ``subagent_type`` disagrees with its
    ``executor_role``, so producers derive one from the other rather than setting
    both by hand.
    """
    return "human" if executor_role == "human" else "general-purpose"


# ---------------------------------------------------------------------------
# Task construction
# ---------------------------------------------------------------------------

#: Canonical key order. Deterministic output keeps golden task fixtures stable.
_TASK_KEY_ORDER = (
    "tasks_schema_version",
    "task_id",
    "kind",
    "prompt",
    "output_name",
    "output_path",
    "prompt_path",
    "prompt_lines",
    "result_channel",
    "context_mode",
    "capability_tier",
    "executor_role",
    "subagent_type",
    "model_hint",
    "inputs",
    "batch_index",
    "group_indices",
    "group_ids",
    "groups_count",
    "is_high_priority",
    "section_key",
    "group_id",
    "items_count",
    "suggestion_id",
    "model",
    "phase",
    "repo_root",
    "plan_file",
    "grouped_file",
    # Write kinds (D3f/D3g/D3h/D3n)
    "task_title",
    "declared_files",
    "snapshot_files",
    "expected_ids",
    "prior_changes_id",
    "can_parallelize",
    "depends_on",
    "is_human",
    "file_key",
)


def make_task(
    *,
    kind: str,
    task_id: str,
    prompt: str,
    output_name: str,
    inputs: Dict[str, str],
    phase_dir: Optional[str] = None,
    output_path: Optional[str] = None,
    context_mode: str = "inline",
    capability_tier: str = "full",
    executor_role: str = "agent",
    result_channel: str = "file",
    subagent_type: Optional[str] = None,
    model_hint: Optional[str] = None,
    prompt_path: Optional[str] = None,
    prompt_lines: Optional[int] = None,
    extra: Optional[Dict[str, Any]] = None,
    validate: bool = True,
) -> Dict[str, Any]:
    """Build one materialized task object.

    Args:
        kind: One of :data:`KINDS`.
        task_id: Stable, path-free identifier, named in every refusal message.
        prompt: The complete prompt (see ``utils/subagent_prompts.py``).
        output_name: Bare basename, resolved against the phase dir on read.
        inputs: The block from :func:`build_inputs`.
        phase_dir: Used to derive the absolute ``output_path`` convenience field.
        output_path: Explicit absolute output path (overrides ``phase_dir``).
        context_mode: ``inline`` (the default and the only mode produced today)
            or ``workspace-read``.
        capability_tier: ``full`` for every currently materialized kind.
        executor_role: ``agent`` or ``human``.
        result_channel: Always ``file`` for a materialized task.
        subagent_type: Optional Claude-Code-only metadata; derived from
            ``executor_role`` when omitted, which is what every producer does —
            so the field is written on every task on every host (see the
            emit site below). Pass ``""`` to omit it entirely.
        model_hint: Free-form model string or ``auto``; keeps its historical
            meaning. ``full``/``cheap`` belong to ``capability_tier`` alone.
        prompt_path: Absolute path of a sidecar holding exactly the bytes of
            ``prompt`` (validation, revalidation, consolidation and task
            generation only). Invoker plumbing of
            the same class as ``output_path``, so it is a named kwarg rather
            than an ``extra`` key: it is not per-kind metadata a reader
            consults, it is how a native-subagent host hands ``prompt`` to a
            subagent without re-emitting it.
        prompt_lines: Line count of ``prompt``, so that host can tell the
            subagent which line to read through.
        extra: Per-kind fields (``batch_index``, ``group_ids``, ``group_id``,
            ``suggestion_id``, …).
        validate: Validate against the schema before returning (write-side
            check). Only tests that deliberately build an invalid task pass
            ``False``.

    Returns:
        The task dict, keys in canonical order.

    Raises:
        TaskFileError: when ``validate`` is set and the task does not validate.
    """
    task: Dict[str, Any] = {
        "tasks_schema_version": TASKS_SCHEMA_VERSION,
        "task_id": task_id,
        "kind": kind,
        "prompt": prompt,
        "output_name": output_name,
        "result_channel": result_channel,
        "context_mode": context_mode,
        "capability_tier": capability_tier,
        "executor_role": executor_role,
        "inputs": dict(inputs),
    }
    # D2h: the derived value is emitted unconditionally, on every host. D2h has a
    # host with no agent-type vocabulary (``subagents: executor``) receiving task
    # files without the field, and ``subagent_type=""`` is that path — but no
    # producer threads a host id in to take it, because the field is metadata no
    # reader consults and host-dependent task bytes would make a phase
    # materialized under one host and resumed under another differ for nothing.
    # Recorded as a deviation in ``plans/host-harness-portability.md``; the
    # release that drops the field deletes it here rather than in every producer.
    if subagent_type is None:
        task["subagent_type"] = subagent_type_for_role(executor_role)
    elif subagent_type:
        task["subagent_type"] = subagent_type
    if model_hint is not None:
        task["model_hint"] = model_hint
    if output_path:
        task["output_path"] = output_path
    elif phase_dir:
        task["output_path"] = os.path.join(phase_dir, output_name)
    if prompt_path:
        task["prompt_path"] = prompt_path
    if prompt_lines:
        task["prompt_lines"] = prompt_lines
    if extra:
        task.update(extra)

    ordered = {k: task[k] for k in _TASK_KEY_ORDER if k in task}
    ordered.update({k: v for k, v in task.items() if k not in ordered})

    if validate:
        errors = validate_subagent_task(ordered, where=f"task {task_id}")
        if errors:
            raise TaskFileError(
                f"Refusing to materialize task {task_id!r} ({kind}): it does not "
                f"match schemas/subagent_tasks.schema.json — "
                + "; ".join(errors)
            )
    return ordered


#: The per-kind ``output_name`` template for a write batch result (D3g). Kept next
#: to the kind table so a new write kind cannot ship without one; the executor's
#: ``OUTPUT_NAME_PATTERN_BY_KIND`` is the matching regex and the two are
#: cross-checked by ``tests/test_subagent_tasks.py``.
WRITE_OUTPUT_NAME_TEMPLATE = {
    "apply_suggestions": "apply_batch_{index}.json",
    "apply_task_suggestions": "apply_task_batch_{index}.json",
    "apply_code_fixes": "apply_fix_batch_{index}.json",
    # `implement` is the one write kind whose token is the plan task's own id
    # rather than a position — see `implement_output_name`. The `{index}`
    # spelling stays here because a bare index is still a legal token (the regex
    # admits both), which keeps the template/regex cross-check covering the kind.
    "implement": "implement_batch_{index}.json",
}

#: The basename charset ``schemas/subagent_tasks.schema.json`` admits for an
#: ``output_name`` token. Mirrors ``human_decisions._SAFE_VERDICT_TOKEN``.
_SAFE_OUTPUT_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def write_output_name(kind: str, batch_index: int) -> str:
    """The ``output_name`` a write batch's result JSON is persisted under (D3g)."""
    try:
        template = WRITE_OUTPUT_NAME_TEMPLATE[kind]
    except KeyError:
        raise TaskFileError(
            f"Refusing to name a write result for kind {kind!r}: known write kinds "
            f"are {', '.join(WRITE_KINDS)}."
        ) from None
    return template.format(index=int(batch_index))


def implement_output_name(task_id: str) -> str:
    """The result basename for one implement task, keyed by the *task id*.

    **Never its position** in the materialized list.
    ``implement_orchestrator`` re-materializes from
    ``format_batches_for_output(skip_completed=--resume)``, so the list a counter
    would run over *shrinks* on a resume and every survivor is renamed: measured
    2026-09-16, a resumed run re-pointed T006 at T001's ``implement_batch_0.json``,
    ``_already_done`` found an ``applied`` file with no fingerprint under T006 and
    declared five never-dispatched tasks complete — the phase exited 0 having
    implemented four of the fourteen tasks it reported. The judging phase hit the
    identical defect and fixed it the identical way
    (``human_decisions.verdict_output_name``); keying by the task id is what makes
    "resume by id" true of the filenames too.

    A token outside the task schema's basename charset is hashed rather than
    rejected, so an exotic id still names exactly one stable file.
    """
    token = str(task_id or "")
    if not _SAFE_OUTPUT_TOKEN.match(token):
        token = content_hash(token)
    return f"implement_batch_{token}.json"


def _default_write_output_name(kind: str, task_id: str, batch_index: int) -> str:
    """The ``output_name`` a write task gets when its producer names none.

    Split out so ``implement``'s id-keyed name is the *default*, not something a
    producer has to remember to pass: the one materializer that forgot is how
    five unrun tasks were declared complete on a resume.
    """
    if kind == "implement":
        return implement_output_name(task_id)
    return write_output_name(kind, batch_index)


def make_write_task(
    *,
    kind: str,
    task_id: str,
    prompt: str,
    inputs: Dict[str, str],
    batch_index: int,
    prior_changes_id: str,
    phase_dir: Optional[str] = None,
    declared_files: Optional[Sequence[str]] = None,
    snapshot_files: Optional[Sequence[str]] = None,
    expected_ids: Optional[Sequence[str]] = None,
    can_parallelize: bool = False,
    depends_on: Optional[Sequence[str]] = None,
    executor_role: str = "agent",
    output_name: Optional[str] = None,
    task_title: str = "",
    file_key: str = "",
    model_hint: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
    validate: bool = True,
) -> Dict[str, Any]:
    """Build one materialized **write** task (``agent-write``, D3f/D3g/D3n).

    Same envelope as :func:`make_task` — so both invokers read one shape — plus the
    four fields a write dispatch cannot be safe without:

    * ``declared_files`` — what D3h admits (or refuses) for co-scheduling and what
      D3l checks against ``driver.write_paths`` *before* the runner starts. An
      empty list means "undeclared", which runs the task alone; it never means
      "touches nothing".
    * ``snapshot_files`` — what the executor copies under
      ``{phase}/pre_batch/{task_id}/`` so the post-run byte comparison has a
      rollback point. Defaults to ``declared_files``.
    * ``expected_ids`` — what D3g spot-checks, so "bytes moved" is not mistaken
      for "this batch's changes landed".
    * ``prior_changes_id`` — the stable ``--id`` for the prior-changes append,
      never the loop index, so a re-dispatched batch appends once.

    ``context_mode`` is fixed at ``workspace-read``: a write batch edits files in
    the target repository, so a runner with no workspace access cannot serve it and
    is refused before dispatch rather than handed a prompt full of unreadable
    paths.
    """
    if kind not in WRITE_KINDS:
        raise TaskFileError(
            f"Refusing to materialize write task {task_id!r}: {kind!r} is not a "
            f"write kind (known: {', '.join(WRITE_KINDS)})."
        )
    if not str(prior_changes_id or "").strip():
        raise TaskFileError(
            f"Refusing to materialize write task {task_id!r}: prior_changes_id is "
            f"required — the prior-changes log is keyed by a stable content key, "
            f"never by the loop index, so a re-dispatched batch appends once."
        )
    write_extra: Dict[str, Any] = {
        "batch_index": int(batch_index),
        "declared_files": [str(path) for path in (declared_files or [])],
        "prior_changes_id": str(prior_changes_id),
        "can_parallelize": bool(can_parallelize),
    }
    if snapshot_files is not None:
        write_extra["snapshot_files"] = [str(path) for path in snapshot_files]
    if expected_ids is not None:
        write_extra["expected_ids"] = [str(item) for item in expected_ids]
    if depends_on is not None:
        write_extra["depends_on"] = [str(item) for item in depends_on]
    if task_title:
        write_extra["task_title"] = task_title
    if file_key:
        write_extra["file_key"] = file_key
    write_extra["is_human"] = executor_role == "human"
    if extra:
        write_extra.update(extra)

    return make_task(
        kind=kind,
        task_id=task_id,
        prompt=prompt,
        output_name=output_name or _default_write_output_name(
            kind, task_id, batch_index
        ),
        inputs=inputs,
        phase_dir=phase_dir,
        context_mode="workspace-read",
        capability_tier="full",
        executor_role=executor_role,
        model_hint=model_hint,
        extra=write_extra,
        validate=validate,
    )


def declared_file_set(task: Dict[str, Any]) -> List[str]:
    """A write task's declared file set, normalized (D3h).

    Reads ``declared_files`` and falls back to the batchers' own historical
    spellings (``file_key`` for code fixes, ``files_to_modify`` /
    ``files_to_create`` for implement tasks) so a task shaped by a producer that
    predates ``declared_files`` still declares something rather than silently
    reading as "undeclared" and being co-scheduled with everything.
    """
    declared = task.get("declared_files")
    if isinstance(declared, list) and declared:
        return [str(item) for item in declared if str(item).strip()]
    collected: List[str] = []
    for key in ("file_key",):
        value = task.get(key)
        if isinstance(value, str) and value.strip():
            collected.append(value.strip())
    for key in ("files_to_modify", "files_to_create"):
        value = task.get(key)
        if isinstance(value, list):
            collected.extend(str(item) for item in value if str(item).strip())
    seen: Dict[str, None] = {}
    for item in collected:
        seen.setdefault(item, None)
    return list(seen)


def snapshot_file_set(task: Dict[str, Any]) -> List[str]:
    """Which files the executor must snapshot before dispatching ``task`` (D3h)."""
    declared = task.get("snapshot_files")
    if isinstance(declared, list) and declared:
        return [str(item) for item in declared if str(item).strip()]
    return declared_file_set(task)


def tasks_of(document: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return a task file's task list under whichever key it uses.

    The batched kinds carry their tasks under the historical ``batches`` key
    (which the merge and reaggregation paths already read) and everything else
    under ``tasks``. Storing the list twice would double a several-hundred-KB
    phase file for nothing, so there is one list and one accessor.
    """
    listed = document.get("tasks")
    if listed is None:
        listed = document.get("batches")
    return list(listed or [])


def file_bytes_sha256(path: Optional[str]) -> str:
    """Full sha256 hex digest of a file's **bytes**, or ``""`` when unreadable.

    Unlike :func:`file_content_hash` (text-decoded, truncated to 16 hex for the
    ``inputs`` block) this is the byte-exact identity a batch result file is
    bound by (§7.1/§7.3): ``validation.json``'s ``metadata.batch_sha256`` and the
    executor's ``batch_provenance`` rows. Content, never mtime — a ``cp -p``
    restore keeps an old mtime and a ``git checkout`` sets a new one, and
    neither changes what the file says.
    """
    if not path:
        return ""
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return ""


def task_round(tasks: Sequence[Dict[str, Any]]) -> str:
    """A fingerprint of one materialized round's task → output mapping (§7.1a).

    Revalidation reuses the ``validation_batch_<n>.json`` names with a different
    subset mapping, so a filename alone cannot say which round a batch file (or
    a hash recorded against it) belongs to. The round is the sha256 of the
    canonical ``(task_id, batch_index, output_name, group_ids, group_indices)``
    list of every non-human task: the same materialization always yields the
    same value, and a round that maps any name to different groups does not.
    Prompts are deliberately excluded — which *groups* a file answers is what a
    merge depends on.
    """
    rows = [
        {
            "task_id": task.get("task_id"),
            "batch_index": task.get("batch_index"),
            "output_name": task.get("output_name"),
            "group_ids": task.get("group_ids"),
            "group_indices": task.get("group_indices"),
        }
        for task in tasks
        if isinstance(task, dict) and task.get("executor_role") != "human"
    ]
    canonical = json.dumps(rows, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def batch_manifest(document: Dict[str, Any]) -> Dict[str, str]:
    """``{kind, round}`` for a batched task file (§7.1a/§7.3a).

    ``kind`` defaults to ``validation`` — the kind every validation-family
    reader already assumes for a document that omits it.
    """
    return {
        "kind": str(document.get("kind") or "validation"),
        "round": task_round(tasks_of(document)),
    }


def make_task_file(
    *,
    kind: str,
    tasks: Sequence[Dict[str, Any]],
    inputs: Dict[str, str],
    extra: Optional[Dict[str, Any]] = None,
    validate: bool = True,
    task_list_key: str = "tasks",
) -> Dict[str, Any]:
    """Wrap materialized tasks in the ``tasks_schema_version: 2`` file envelope.

    Args:
        task_list_key: ``"tasks"`` (the default) or ``"batches"`` for the batched
            kinds whose readers already use that name. Either way the list
            appears exactly once; :func:`tasks_of` is the accessor.
    """
    document: Dict[str, Any] = {
        "tasks_schema_version": TASKS_SCHEMA_VERSION,
        "kind": kind,
        "inputs": dict(inputs),
        task_list_key: list(tasks),
    }
    if extra:
        document.update(extra)
        # `extra` may legitimately restate the list key (a producer building its
        # historical payload); the materialized tasks always win.
        document[task_list_key] = list(tasks)
    if validate:
        errors = validate_subagent_task_file(document)
        if errors:
            raise TaskFileError(
                "Refusing to write a task file that does not match "
                "schemas/subagent_tasks.schema.json — " + "; ".join(errors)
            )
    return document


def write_task_file(path: str, document: Dict[str, Any]) -> None:
    """Validate a task file and write it, creating parent directories."""
    errors = validate_subagent_task_file(document)
    if errors:
        raise TaskFileError(
            f"Refusing to write {path}: it does not match "
            "schemas/subagent_tasks.schema.json — " + "; ".join(errors)
        )
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2)


# ---------------------------------------------------------------------------
# Read side (resume): version window + inputs binding, both exit 3
# ---------------------------------------------------------------------------

_REMATERIALIZE_FIX = (
    "Prompts are derived data, so a stale task file is never patched: either "
    "finish the phase under the skill version that wrote it, or re-run the "
    "phase with --force to re-materialize it"
)


def check_task_file_version(document: Any, path: str, phase_dir: str) -> None:
    """Raise :class:`TaskFileError` unless the file is ``tasks_schema_version: 2``.

    A missing field means version 1 — today's implicit reference-based shape,
    which contains no prompts to recover, so "migrating" it is just re-running
    the phase. ``> 2`` is refused the same way. There is no silent upconversion
    in either direction.
    """
    if not isinstance(document, dict):
        raise TaskFileError(
            f"Refusing task file {path}: expected a JSON object, got "
            f"{type(document).__name__}. Phase dir: {phase_dir}. "
            f"{_REMATERIALIZE_FIX}."
        )
    found = document.get("tasks_schema_version")
    if found == TASKS_SCHEMA_VERSION:
        return
    described = "missing (which means version 1)" if found is None else repr(found)
    raise TaskFileError(
        f"Refusing task file {path}: tasks_schema_version is {described}, but "
        f"this release reads and writes {TASKS_SCHEMA_VERSION}. Phase dir: "
        f"{phase_dir}. {_REMATERIALIZE_FIX}."
    )


#: What each recorded input hash *is*, said in the words a reader can act on.
#: A bare `tasks_sha256: materialized from 'a1b2', now 'c3d4'` names a key
#: nothing on screen explains: a `review-tasks --reaggregate` after
#: apply-task-suggestions rewrote `tasks/tasks.md` is a routine exit 3, and the
#: refusal has to say which file moved before "--force" means anything.
_INPUT_CHANGE_REASONS = {
    "plan_sha256": "the plan file was edited since this phase materialized",
    "grouped_sha256": "grouped.json was rewritten (a re-group or a reaggregate)",
    "tasks_sha256": (
        "tasks.md changed since validation — apply-task-suggestions rewrites it"
    ),
    "diff_sha256": "the diff under review changed",
    "diff_base": "the diff was taken against a different base ref",
    "reviewed_code_sha256": "a reviewed file changed at the lines these issues cite",
    "context_plan_sha256": (
        "the context plan's frozen snapshot no longer hashes to the "
        "plan_sha256 the commit review recorded"
    ),
    "salvage_request_sha256": "the salvage request was rewritten",
    "items_sha256": "the item list changed",
}


def check_task_file_inputs(
    document: Dict[str, Any],
    path: str,
    phase_dir: str,
    current_inputs: Dict[str, str],
) -> None:
    """Raise :class:`TaskFileError` when any recorded input hash has moved.

    Editing the plan, regrouping, or moving HEAD between materialization and
    resume leaves prompts that still validate cleanly and produce confidently
    wrong results. Only keys present in *both* blocks are compared, so a caller
    that cannot recompute an input (no diff available on this code path, say)
    simply does not check it rather than failing the file spuriously.
    """
    recorded = document.get("inputs") or {}
    if not isinstance(recorded, dict):
        raise TaskFileError(
            f"Refusing task file {path}: its `inputs` block is not an object. "
            f"Phase dir: {phase_dir}. {_REMATERIALIZE_FIX}."
        )
    changed = [
        (key, recorded.get(key), current_inputs[key])
        for key in sorted(current_inputs)
        if key in recorded and recorded.get(key) != current_inputs[key]
    ]
    if not changed:
        return
    details = "; ".join(
        f"{key} ({_INPUT_CHANGE_REASONS.get(key, 'changed')}): materialized "
        f"from {was!r}, now {now!r}"
        for key, was, now in changed
    )
    raise TaskFileError(
        f"Refusing task file {path}: the inputs it was materialized from have "
        f"changed ({details}). Phase dir: {phase_dir}. Re-run the phase with "
        f"--force to re-materialize it, or restore the changed input. Nothing "
        f"was dispatched."
    )


def read_task_file(
    path: str,
    *,
    phase_dir: Optional[str] = None,
    current_inputs: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Read, version-check, schema-check and input-bind a materialized task file.

    Args:
        path: The task file to read.
        phase_dir: The phase dir named in refusal messages and used to resolve
            each task's ``output_name``. Defaults to the file's own directory.
        current_inputs: Freshly recomputed input hashes; when given, any recorded
            hash that has moved refuses the file.

    Returns:
        The parsed document.

    Raises:
        TaskFileError: exit code 3 — wrong version, invalid shape, or moved
            inputs. Nothing is dispatched in any of those cases.
    """
    resolved_phase_dir = phase_dir or os.path.dirname(os.path.abspath(path))
    try:
        with open(path, "r", encoding="utf-8") as handle:
            document = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise TaskFileError(
            f"Refusing task file {path}: it could not be read as JSON ({exc}). "
            f"Phase dir: {resolved_phase_dir}. {_REMATERIALIZE_FIX}."
        ) from exc

    check_task_file_version(document, path, resolved_phase_dir)
    errors = validate_subagent_task_file(document)
    if errors:
        raise TaskFileError(
            f"Refusing task file {path}: it does not match "
            f"schemas/subagent_tasks.schema.json — " + "; ".join(errors)
            + f". Phase dir: {resolved_phase_dir}. {_REMATERIALIZE_FIX}."
        )
    if current_inputs:
        check_task_file_inputs(document, path, resolved_phase_dir, current_inputs)
    return document


def write_salvage_task_file(
    *,
    salvage_request: Dict[str, Any],
    salvage_request_path: str,
    phase_dir: str,
    plan_file: str = "",
) -> str:
    """Materialize the salvage task that goes with a ``[SALVAGE_NEEDED]`` marker.

    The salvage *request* file is left exactly as it was — it is what the task's
    ``inputs.salvage_request_sha256`` binds to, so a re-materialized prompt cannot
    silently pair with a rewritten request. The task lands in a sibling
    ``salvage_task_<model>.json``, whose name matches the reaggregation
    exclude-pattern list and so is never parsed as a model result.

    Args:
        salvage_request: The already-written request record.
        salvage_request_path: Where it was written (hashed for ``inputs``).
        phase_dir: The phase directory; the task file and ``output_name`` resolve
            against it.
        plan_file: Plan path for ``inputs.plan_sha256`` (provenance only).

    Returns:
        The path of the task file written.
    """
    from .subagent_prompts import build_salvage_prompt  # local: avoid cycles

    output_name = os.path.basename(salvage_request.get("output_path", "") or "")
    suggestion_id = os.path.splitext(output_name)[0] or "unknown"
    task = make_task(
        kind="salvage",
        task_id=f"salvage-{suggestion_id}",
        prompt=build_salvage_prompt(salvage_request),
        output_name=output_name or f"{suggestion_id}.json",
        inputs=build_inputs(
            plan_file=plan_file,
            salvage_request_file=salvage_request_path,
        ),
        phase_dir=phase_dir,
        extra={
            "suggestion_id": suggestion_id,
            "model": salvage_request.get("model", ""),
            "phase": salvage_request.get("phase", ""),
        },
    )
    document = make_task_file(
        kind="salvage",
        tasks=[task],
        inputs=task["inputs"],
        extra={
            "total_tasks": 1,
            "phase_dir": phase_dir,
            "salvage_request_path": salvage_request_path,
        },
    )
    task_path = os.path.join(phase_dir, f"salvage_task_{suggestion_id}.json")
    write_task_file(task_path, document)
    return task_path


def resolve_output_path(task: Dict[str, Any], phase_dir: str) -> str:
    """Resolve a task's ``output_name`` against the phase dir it was loaded from.

    ``output_path`` on the task is a derived convenience field for native
    invokers; ``output_name`` plus the loaded-from dir is authoritative, which is
    what lets a moved or copied phase dir still work.
    """
    return os.path.join(phase_dir, task["output_name"])


# ---------------------------------------------------------------------------
# Pre-dispatch refusals (D2a / D2c / D2h) — reusable by the D3 executor
# ---------------------------------------------------------------------------

def refuse_reason(
    task: Dict[str, Any],
    *,
    supports_workspace_reads: bool = True,
    runner: str = "the configured runner",
) -> Optional[str]:
    """Return why ``task`` must not be dispatched, or ``None`` when it may be.

    Three refusals, all pre-dispatch and all naming the ``task_id``:

    * ``result_channel: inline-json`` — a verdict that never touches disk is
      unrecoverable after a crash, invisible to ``--resume`` and meaningless
      under ``--detach``. The executor's write leg never branches on
      ``result_channel``, so an ``inline-json`` materialized task can only mean a
      stale or wrong producer, and the field it got wrong is precisely the one
      that says whether ``output_name`` was derived at all — there is often no
      path to normalize *to*.
    * ``executor_role: human`` — not an agent type at all, but the marker that no
      invoker ever dispatches this task; it routes to the human-task pause.
    * ``context_mode: workspace-read`` against a runner that declares no
      workspace-read capability — better than sending a prompt full of
      unreadable paths, which degrades into a confidently empty answer.
    """
    task_id = task.get("task_id", "<unnamed>")
    channel = task.get("result_channel")
    if channel != "file":
        return (
            f"Task {task_id}: result_channel is {channel!r}, but every "
            f"materialized task must be 'file' — a result that never touches "
            f"disk cannot survive a crash, --resume or --detach. This task was "
            f"written by a stale or incorrect producer; re-run the phase with "
            f"--force to re-materialize it. Nothing was dispatched."
        )
    if task.get("executor_role") == "human":
        return (
            f"Task {task_id}: executor_role is 'human', which means no invoker "
            f"ever dispatches it — it routes to the human-task pause. Nothing "
            f"was dispatched."
        )
    if task.get("context_mode") == "workspace-read" and not supports_workspace_reads:
        if task.get("kind") in ("validation", "revalidation"):
            # §2.3 step 4a, at dispatch: a batch materialized to name its
            # snapshot by path is never re-materialized inline behind the
            # operator's back — it fails with a named error instead.
            return (
                f"{task.get('kind')} batch {task.get('batch_index', task_id)} "
                f"needs workspace reads; runner {runner} cannot read files; "
                f"rematerialize with a capable runner (task {task_id}: "
                f"context_mode 'workspace-read' names a hash-bound snapshot by "
                f"path). Nothing was dispatched."
            )
        return (
            f"Task {task_id}: context_mode is 'workspace-read', which requires a "
            f"runner declaring supports_workspace_reads; {runner} does not. "
            f"Nothing was dispatched."
        )
    return None


def assert_dispatchable(
    task: Dict[str, Any],
    *,
    supports_workspace_reads: bool = True,
    runner: str = "the configured runner",
) -> None:
    """Raise :class:`TaskRefusal` (exit 3) when ``task`` must not be dispatched."""
    reason = refuse_reason(
        task, supports_workspace_reads=supports_workspace_reads, runner=runner
    )
    if reason is not None:
        raise TaskRefusal(reason, task_id=task.get("task_id", ""))


# ---------------------------------------------------------------------------
# D2d — prompt transport and budget
# ---------------------------------------------------------------------------

def utf16_units(text: str) -> int:
    """Length of ``text`` in UTF-16 code units (astral characters count twice)."""
    return _utf16_code_units(text)


def preferred_prompt_transport(provider_name: Optional[str]) -> str:
    """The transport a runner should use for a materialized prompt.

    ``stdin`` wherever the adapter has a real non-argv transport (the
    ``subagent_runner``-eligible providers), ``argv`` otherwise. A materialized
    prompt is far larger than the metadata JSON it replaces, and argv cannot
    carry a 30 KB prompt on Windows, so the transport is chosen explicitly rather
    than inherited by accident.
    """
    if not provider_name:
        return "argv"
    base = provider_name.split(":", 1)[0]
    try:  # ask the adapter itself; fall back to the known-good list
        from .provider_registry import get_provider  # local: avoids a cycle
    except ImportError:  # pragma: no cover
        try:
            from utils.provider_registry import get_provider
        except ImportError:
            get_provider = None  # type: ignore[assignment]
    if get_provider is not None:
        provider = get_provider(base)
        if provider is not None:
            for candidate in ("stdin", "file"):
                if provider.supports_prompt_transport(candidate):
                    return candidate
            return "argv"
    return "stdin" if base in _NON_ARGV_TRANSPORT_PROVIDERS else "argv"


def prompt_budget_utf16(
    *,
    transport: str = "argv",
    non_prompt_argv: Optional[Iterable[str]] = None,
    is_batch_shim: bool = False,
    enforce_on_posix: bool = False,
) -> Optional[int]:
    """Return the prompt ceiling in UTF-16 code units, or ``None`` for unbounded.

    * ``stdin`` / ``file`` transports are effectively unbounded — the prompt never
      reaches a command line.
    * an ``argv`` transport is bounded by the applicable Windows cap
      (8,191 units for a ``.cmd``/``.bat`` shim run through cmd.exe, 32,767 for a
      native ``CreateProcess``) minus ``CMDLINE_UTF16_HEADROOM`` minus the
      rendered non-prompt argv.

    The caps are a Windows constraint, so on POSIX the budget is unbounded unless
    ``enforce_on_posix`` is set (which the tests use to pin the arithmetic on any
    platform).
    """
    if transport in ("stdin", "file"):
        return None
    if os.name != "nt" and not enforce_on_posix:
        return None
    cap = CMDLINE_CAP_UTF16_BATCH if is_batch_shim else CMDLINE_CAP_UTF16_NATIVE
    budget = cap - CMDLINE_UTF16_HEADROOM
    if non_prompt_argv:
        import subprocess  # local: keeps module import cheap and side-effect free

        budget -= _utf16_code_units(subprocess.list2cmdline(list(non_prompt_argv)))
    return max(budget, 0)


class PromptBudget:
    """A prompt ceiling plus the over-budget decision (split, or downgrade).

    Never truncates: truncating the instruction tail turns a validation prompt
    into an unanswerable one, and truncating a salvage ``raw_output`` salvages
    half an array.
    """

    def __init__(
        self,
        max_units: Optional[int] = None,
        *,
        transport: str = "argv",
        supports_workspace_reads: bool = False,
    ) -> None:
        self.max_units = max_units
        self.transport = transport
        self.supports_workspace_reads = supports_workspace_reads

    @property
    def unbounded(self) -> bool:
        return self.max_units is None

    def units(self, prompt: str) -> int:
        return utf16_units(prompt)

    def fits(self, prompt: str) -> bool:
        return self.max_units is None or utf16_units(prompt) <= self.max_units

    def exceeded_by(self, prompt: str) -> int:
        """How many UTF-16 code units over budget ``prompt`` is (0 when it fits)."""
        if self.max_units is None:
            return 0
        return max(0, utf16_units(prompt) - self.max_units)

    def resolution(self, prompt: str, *, splittable: bool) -> str:
        """What to do about ``prompt``: ``"ok"``, ``"split"``, ``"workspace-read"``.

        Raises:
            TaskFileError: when the prompt is over budget and neither splitting
                nor a workspace-read downgrade is available — the one case where
                there is nothing to do but fail loudly, since truncation is never
                an option.
        """
        if self.fits(prompt):
            return "ok"
        if splittable:
            return "split"
        if self.supports_workspace_reads:
            return "workspace-read"
        raise TaskFileError(
            f"A materialized prompt is {utf16_units(prompt)} UTF-16 code units "
            f"but the runner's {self.transport} transport allows "
            f"{self.max_units}; it cannot be split further and the runner "
            f"declares no workspace-read capability. Configure a runner with a "
            f"stdin/file prompt transport (driver.subagent_runner) or one that "
            f"supports workspace reads. The prompt is never truncated."
        )


def split_indices(indices: Sequence[int]) -> Tuple[List[int], List[int]]:
    """Halve a batch's index list. Returns ``(first, second)``; second may be empty."""
    if len(indices) < 2:
        return list(indices), []
    middle = len(indices) // 2
    return list(indices[:middle]), list(indices[middle:])
