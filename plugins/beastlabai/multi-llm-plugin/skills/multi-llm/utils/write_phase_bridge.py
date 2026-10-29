#!/usr/bin/env python3
"""Turn each write phase's existing batch output into materialized write tasks.

The four write phases already build a **complete prompt** per batch in Python
(Pattern A: ``utils/suggestion_batcher.format_batch_for_prompt``,
``utils/code_fix_batcher``, ``apply_task_suggestions_orchestrator``,
``implement_orchestrator.build_task_prompt``). What they *don't* build is the
materialized-task envelope the executor is the second invoker of — the
``tasks_schema_version: 2`` shape with ``output_name``, ``inputs`` hashes,
``executor_role``, and the four write fields D3f/D3g/D3h need.

This module is that one conversion, in one place, so:

* the same declared file set drives the disjointness admission, the write policy
  and the snapshot for every phase (rather than each orchestrator deciding);
* ``prior_changes_id`` is derived from a **stable content key** (section key,
  file key, task id) and never from the loop index, which is what makes the
  prior-changes append idempotent across a re-dispatch — and, for the three
  batched phases, the key alone is not enough: many batches share one file key or
  section key, so the id is that key plus a digest of the batch's own member ids
  (:func:`utils.prior_changes.entry_id`), unique per batch and stable across a
  re-dispatch of the same batch. It is the identical id the batchers serialize
  into their ``to_dict()``, so a native invoker and this bridge append under the
  same key;
* adding a write phase is a row in :data:`_ADAPTERS`, not a fifth hand-rolled
  materializer.

Nothing here dispatches: ``utils/write_batch_scheduler`` is the consumer.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

try:  # pragma: no cover - import shim mirrors the rest of utils/
    from .code_fix_batcher import fix_member_ids
    from .prior_changes import entry_id, stable_key
    from .suggestion_batcher import suggestion_member_ids
    from .subagent_tasks import (
        PHASE_BY_WRITE_KIND,
        build_inputs,
        make_task_file,
        make_write_task,
        write_task_file,
    )
except ImportError:  # pragma: no cover - direct-script import shim
    from utils.code_fix_batcher import fix_member_ids
    from utils.prior_changes import entry_id, stable_key
    from utils.suggestion_batcher import suggestion_member_ids
    from utils.subagent_tasks import (
        PHASE_BY_WRITE_KIND,
        build_inputs,
        make_task_file,
        make_write_task,
        write_task_file,
    )


__all__ = [
    "WRITE_TASK_FILENAME",
    "materialize_write_tasks",
    "write_task_file_for_phase",
]


#: The materialized write task file, beside the phase's own orchestrator output.
#: Named for the phase's kind so a phase dir shared by a resumed run cannot mix two.
WRITE_TASK_FILENAME = "write_tasks.json"

#: ``write_tasks.json``'s ``leg`` on a file the native emit wrote (fix round
#: 26): the phase's newest run is the host's own, whatever an earlier
#: executor run left in ``{phase}/.status.json``.
NATIVE_LEG = "native"


#: The first non-empty candidate, else the fallback. Never the loop index.
#: Owned by :mod:`utils.prior_changes` (with :func:`entry_id`, which is built on
#: it) so the bridge and the batchers cannot spell a content key two ways.
_stable_key = stable_key


def _apply_suggestions_task(
    batch: Dict[str, Any], index: int, context: Dict[str, Any]
) -> Dict[str, Any]:
    """apply-suggestions: one shared artifact (the plan), sequential by invariant."""
    suggestions = batch.get("suggestions") or []
    section = _stable_key([batch.get("section_key")], f"batch-{index}")
    member_ids = suggestion_member_ids(suggestions)
    return dict(
        task_id=f"apply-batch-{index}",
        prompt=str(batch.get("prompt") or ""),
        batch_index=index,
        # The plan file is THE artifact: it is what gets snapshotted and what the
        # byte comparison decides on.
        declared_files=[context["plan_file"]],
        expected_ids=member_ids,
        # The RAW section key, not `section`: one section spills into several
        # batches under the same key (batch size, char cap), so the members are
        # what tells them apart — see `prior_changes.entry_id`.
        prior_changes_id=entry_id(
            str(batch.get("section_key") or ""), member_ids,
            fallback=f"batch-{index}",
        ),
        can_parallelize=False,
        task_title=f"apply {len(suggestions)} suggestion(s) to {section}",
        extra={"section_key": section},
    )


def _apply_task_suggestions_task(
    batch: Dict[str, Any], index: int, context: Dict[str, Any]
) -> Dict[str, Any]:
    """apply-task-suggestions: same shape, but the artifact is the tasks file."""
    suggestions = batch.get("suggestions") or []
    section = _stable_key([batch.get("section_key")], f"batch-{index}")
    member_ids = suggestion_member_ids(suggestions)
    artifact = context.get("tasks_file") or context["plan_file"]
    return dict(
        task_id=f"apply-task-batch-{index}",
        prompt=str(batch.get("prompt") or ""),
        batch_index=index,
        declared_files=[artifact],
        expected_ids=member_ids,
        # The RAW section key, for the same reason as apply-suggestions above.
        prior_changes_id=entry_id(
            str(batch.get("section_key") or ""), member_ids,
            fallback=f"batch-{index}",
        ),
        can_parallelize=False,
        task_title=f"apply {len(suggestions)} task suggestion(s) to {section}",
        extra={"section_key": section},
    )


def _apply_code_fixes_task(
    batch: Dict[str, Any], index: int, context: Dict[str, Any]
) -> Dict[str, Any]:
    """apply-code-fixes: partitioned by ``file_key``, so batches CAN parallelize.

    ``can_parallelize`` is set from the partitioning the batcher already performs
    — one file per batch, but **many batches per file**: `MAX_FIXES_PER_BATCH`
    caps a batch at three fixes, the description cap can close one sooner, and
    every security/HIGH fix is isolated in a batch of its own. So the file key
    identifies the *partition*, never the batch (which is why `prior_changes_id`
    digests the members below), and it is only a *permission*: the scheduler still
    needs ``driver.max_concurrent_write_subagents > 1`` and the dispatch-time
    pairwise-disjoint check to agree before two of them run together.
    """
    fixes = batch.get("fixes") or []
    file_key = _stable_key([batch.get("file_key")], f"batch-{index}")
    member_ids = fix_member_ids(fixes)
    return dict(
        task_id=f"apply-fix-batch-{index}",
        prompt=str(batch.get("prompt") or ""),
        batch_index=index,
        declared_files=[file_key],
        expected_ids=member_ids,
        # The RAW file key: 19 of one real run's 44 batches shared one file, and
        # a file-keyed id recorded only the first of them.
        prior_changes_id=entry_id(
            str(batch.get("file_key") or ""), member_ids,
            fallback=f"batch-{index}",
        ),
        can_parallelize=bool(batch.get("file_key")),
        task_title=f"apply {len(fixes)} fix(es) to {file_key}",
        executor_role=str(batch.get("executor_role") or "agent"),
        extra={"file_key": file_key},
    )


def _implement_task(
    task: Dict[str, Any], index: int, context: Dict[str, Any]
) -> Dict[str, Any]:
    """implement: one materialized task per decomposed task, keeping its edges.

    ``depends_on`` travels so the human-task strategies can walk the graph, and
    ``files_to_create``/``files_to_modify`` become the declared set — the same
    partitioning ``implement_orchestrator`` already batches by.
    """
    task_id = _stable_key([task.get("id")], f"task-{index}")
    declared = [
        *(task.get("files_to_modify") or []),
        *(task.get("files_to_create") or []),
    ]
    return dict(
        task_id=task_id,
        prompt=str(task.get("prompt") or ""),
        batch_index=int(context["batch_index"]),
        declared_files=declared,
        expected_ids=[task_id],
        prior_changes_id=task_id,
        can_parallelize=bool(context.get("can_parallelize")),
        depends_on=[str(d) for d in (task.get("depends_on") or [])],
        executor_role=str(task.get("executor_role") or "agent"),
        task_title=str(task.get("title") or task_id),
    )


#: ``kind -> (per-item builder, how the phase's payload is iterated)``.
_ADAPTERS: Dict[str, Callable[..., Dict[str, Any]]] = {
    "apply_suggestions": _apply_suggestions_task,
    "apply_task_suggestions": _apply_task_suggestions_task,
    "apply_code_fixes": _apply_code_fixes_task,
    "implement": _implement_task,
}


def materialize_write_tasks(
    *,
    kind: str,
    batches: Sequence[Dict[str, Any]],
    phase_dir: str,
    plan_file: str,
    tasks_file: Optional[str] = None,
    grouped_file: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Convert a phase's batch payload into materialized write tasks (D2g shape).

    Args:
        batches: For the three apply kinds, the orchestrator's ``batches`` list
            (each carrying ``prompt``). For ``implement``, the ``batches`` list of
            ``{batch_index, can_parallelize, tasks: [...]}``.

    Returns:
        The task list, validated against ``schemas/subagent_tasks.schema.json``.
    """
    if kind not in _ADAPTERS:
        raise ValueError(f"{kind!r} is not a write kind this bridge materializes")
    inputs = build_inputs(
        plan_file=plan_file, grouped_file=grouped_file, tasks_file=tasks_file
    )
    context: Dict[str, Any] = {
        "plan_file": str(Path(plan_file).resolve()) if plan_file else "",
        "tasks_file": str(Path(tasks_file).resolve()) if tasks_file else None,
    }
    builder = _ADAPTERS[kind]
    tasks: List[Dict[str, Any]] = []

    if kind == "implement":
        for batch in batches:
            batch_index = int(batch.get("batch_index", 0))
            for position, inner in enumerate(batch.get("tasks") or []):
                fields = builder(inner, position, {
                    **context,
                    "batch_index": batch_index,
                    "can_parallelize": batch.get("can_parallelize"),
                })
                # Two tasks in one batch cannot share an output_name, and neither
                # ``batch_index`` (it repeats within a parallelizable batch) nor a
                # monotonic counter over this list is unique *per task*: the
                # counter was, until 2026-09-16, and a ``--resume`` — which
                # re-materializes from `format_batches_for_output(skip_completed)`
                # and therefore over a SHORTER list — renamed every survivor onto a
                # predecessor's result file. The plan task's own id is the only
                # token that survives the filter, so `make_write_task` derives the
                # name from it (`subagent_tasks.implement_output_name`) and this
                # site names none.
                tasks.append(make_write_task(
                    kind=kind, inputs=inputs, phase_dir=phase_dir, **fields,
                ))
        return tasks

    for index, batch in enumerate(batches):
        fields = builder(batch, index, context)
        tasks.append(make_write_task(
            kind=kind, inputs=inputs, phase_dir=phase_dir, **fields
        ))
    return tasks


#: ``write_tasks.json``'s record of the native apply run its batches belong
#: to (fix round 29): ``{started_at, items, emitted_at}``. A native
#: ``--resume`` re-materializes the file with only the batches still to run,
#: so the file alone no longer says what the run handed out; and a bare
#: re-run keeps the earlier run's ``processed_<phase>`` records. ``status``
#: counts the run's ``items`` and the records written since ``started_at``
#: (``run_status._native_apply_not_applied``).
NATIVE_RUN_KEY = "native_run"


def native_run_record(
    phase_dir: str,
    tasks: Sequence[Dict[str, Any]],
    *,
    resume: bool,
    now: Optional[str] = None,
) -> Dict[str, Any]:
    """The :data:`NATIVE_RUN_KEY` record the native emit of *tasks* writes.

    ``started_at`` is when the run began and ``items`` every item it handed
    out, in order; ``emitted_at`` is when this file was written. A
    ``--resume`` (*resume*) of the review the previous native file applied
    (the same ``inputs.grouped_sha256``) carries that file's ``started_at``
    and adds its own items to that file's ``items``. A ``--resume`` with no
    such file before it (an executor run's, or one written before this
    record existed) records ``started_at: None``, so every record of the
    review counts, as it did before. Any other emit — a first run, a bare
    re-run, ``--fresh`` — starts a run: ``started_at`` is *now*."""
    from datetime import datetime

    now = now or datetime.now().isoformat()
    items: List[str] = []
    for task in tasks:
        for item in (task.get("expected_ids") or []) if isinstance(task, dict) else []:
            if str(item) and str(item) not in items:
                items.append(str(item))
    if not resume:
        return {"started_at": now, "items": items, "emitted_at": now}
    previous: Any = None
    try:
        import json

        with open(os.path.join(phase_dir, WRITE_TASK_FILENAME), encoding="utf-8") as handle:
            previous = json.load(handle)
    except (OSError, ValueError):
        previous = None
    run = previous.get(NATIVE_RUN_KEY) if isinstance(previous, dict) else None

    def _stamp(inputs: Any) -> str:
        return str(inputs.get("grouped_sha256") or "") if isinstance(inputs, dict) else ""

    current = next((_stamp(t.get("inputs")) for t in tasks if isinstance(t, dict)), "")
    if (not isinstance(run, dict) or previous.get("leg") != NATIVE_LEG
            or _stamp(previous.get("inputs")) != current):
        return {"started_at": None, "items": items, "emitted_at": now}
    earlier = [str(i) for i in (run.get("items") or []) if str(i)] if isinstance(
        run.get("items"), list) else []
    started = run.get("started_at")
    return {
        "started_at": started if isinstance(started, str) and started else None,
        "items": earlier + [item for item in items if item not in earlier],
        "emitted_at": now,
    }


def write_task_file_for_phase(
    *,
    kind: str,
    tasks: Sequence[Dict[str, Any]],
    phase_dir: str,
    plan_file: str,
    grouped_file: Optional[str] = None,
    tasks_file: Optional[str] = None,
    native_host: Optional[str] = None,
    native_run: Optional[Dict[str, Any]] = None,
) -> str:
    """Persist the phase's materialized write tasks. Returns the path written.

    The file is written even under ``--dry-run-subagents``: it is the input a
    ``--resume`` re-reads and the artifact that makes "what exactly would have been
    dispatched" inspectable without re-deriving it from an orchestrator run.

    ``tasks_file`` (apply-task-suggestions only, mirroring the same argument on
    :func:`materialize_write_tasks`) stamps ``inputs.tasks_sha256`` on the
    document too, so a hand-edited ``tasks/tasks.md`` invalidates a stored
    ``write_tasks.json`` on ``--resume`` the way an edited plan already does.

    *native_host* (the native emit's, fix round 26): the file is stamped
    ``leg: native`` with that host, because every run of the phase rewrites
    it, on either leg, and an executor run's ``{phase}/.status.json`` stays
    behind when the phase goes on natively; ``status`` reads the stamp to
    show the native run as the current one (:data:`NATIVE_LEG`). The
    executor leg passes none, so its rewrite drops the stamp.

    *native_run* (the native apply emit's, fix round 29;
    :func:`native_run_record`) is written beside that stamp as
    :data:`NATIVE_RUN_KEY`.
    """
    extra: Dict[str, Any] = {
        "total_batches": len(tasks),
        "phase": PHASE_BY_WRITE_KIND[kind],
        "phase_dir": str(phase_dir),
    }
    if native_host is not None:
        extra["leg"] = NATIVE_LEG
        extra["host"] = str(native_host)
        if native_run is not None:
            extra[NATIVE_RUN_KEY] = dict(native_run)
    document = make_task_file(
        kind=kind,
        tasks=list(tasks),
        inputs=build_inputs(
            plan_file=plan_file, grouped_file=grouped_file, tasks_file=tasks_file
        ),
        task_list_key="batches",
        extra=extra,
    )
    os.makedirs(phase_dir, exist_ok=True)
    path = os.path.join(phase_dir, WRITE_TASK_FILENAME)
    write_task_file(path, document)
    return path
