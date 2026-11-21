"""Output assembly utilities for apply orchestrators.

Provides shared functions for writing orchestrator output JSON files,
emitting output markers, and printing JSON to stdout. Extracted from
the three apply orchestrators.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, TextIO

from .validation import publish_host_view, remove_host_view

#: The host's view of an apply phase's ``orchestrator_output.json``, beside it.
#: The output's ``batches`` carry each batch's unbound ``prompt`` and its full
#: item records, and ``to_apply`` repeats those records: a native host drives
#: its batch loop from ids and counts, so it reads this file instead, and one
#: batch's detail file (:data:`ORCHESTRATOR_BATCHES_DIRNAME`) at a time. The
#: output stays the source of truth for ``util write-prompt``, ``util
#: batch-done``, the scheduler and ``--output-format json``
#: (docs/development/write-scheduler.md#the-host-summary).
ORCHESTRATOR_SUMMARY_FILENAME = "orchestrator_summary.json"

#: The directory beside the output holding one detail file per batch,
#: ``<task_id>.json``: the batch's output record without its ``prompt`` (its
#: suggestions or fixes and their targets), the items a host checks the batch's
#: edits against.
ORCHESTRATOR_BATCHES_DIRNAME = "orchestrator_batches"

#: Output keys the summary copies, when present: the phase's outcome, its
#: target files, its counts, and every item the host must still decide on.
SUMMARY_OUTPUT_KEYS = (
    "status", "message", "plan_file", "tasks_file", "tasks_file_backup",
    "summary", "needs_human_review", "human_review_config",
    "skipped_items", "user_skipped_items", "skipped_count",
)

#: Keys each summary batch copies from its ``orchestrator_output.json`` batch.
SUMMARY_BATCH_KEYS = ("section_key", "file_key", "executor_role", "prior_changes_id")

#: Keys each summary batch copies from its materialized write task
#: (``write_tasks.json``), the ids ``util write-prompt`` and ``util batch-done``
#: are keyed on.
SUMMARY_TASK_KEYS = ("task_id", "batch_index", "task_title", "expected_ids")

#: A task id that is safe as a detail file's name.
_DETAIL_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def summary_path_for(output_path: os.PathLike | str) -> Path:
    """The summary beside *output_path*."""
    return Path(output_path).with_name(ORCHESTRATOR_SUMMARY_FILENAME)


def batch_detail_path(output_path: os.PathLike | str, task_id: str) -> Path:
    """The detail file of the batch whose write task is *task_id*."""
    return Path(output_path).with_name(ORCHESTRATOR_BATCHES_DIRNAME) / f"{task_id}.json"


def build_batch_detail(batch: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
    """One batch's detail: its write task's ids, then its output record minus ``prompt``."""
    detail: Dict[str, Any] = {"detail_of": "orchestrator_output.json"}
    detail.update({k: task[k] for k in SUMMARY_TASK_KEYS if k in task})
    detail.update({k: v for k, v in batch.items() if k != "prompt"})
    return detail


def build_orchestrator_summary(
    output: Dict[str, Any],
    write_tasks: Optional[Sequence[Dict[str, Any]]] = None,
    output_path: Optional[os.PathLike | str] = None,
) -> Dict[str, Any]:
    """The summary of *output*: outcome, counts, human-review items and batch ids.

    *write_tasks* are the phase's materialized write tasks, the same batches in
    the same order; when there is one per batch, each summary batch also names
    its task id, and with *output_path* its ``detail_path``. Without them a
    batch carries its position and output keys.
    """
    summary: Dict[str, Any] = {"summary_of": "orchestrator_output.json"}
    for key in SUMMARY_OUTPUT_KEYS:
        if key in output:
            summary[key] = output[key]
    batches = list(output.get("batches") or [])
    tasks: List[Dict[str, Any]] = [t for t in (write_tasks or []) if isinstance(t, dict)]
    paired = len(tasks) == len(batches)
    entries: List[Dict[str, Any]] = []
    for position, batch in enumerate(batches):
        entry: Dict[str, Any] = {"batch_index": position}
        if paired:
            entry.update({k: tasks[position][k] for k in SUMMARY_TASK_KEYS
                          if k in tasks[position]})
        if isinstance(batch, dict):
            entry.update({k: batch[k] for k in SUMMARY_BATCH_KEYS if k in batch})
        if paired and output_path is not None and "task_id" in entry:
            entry["detail_path"] = str(batch_detail_path(output_path, entry["task_id"]))
        entries.append(entry)
    summary["batches"] = entries
    return summary


def invalidate_orchestrator_views(output_path: os.PathLike | str) -> None:
    """Remove the summary and every batch detail beside *output_path*.

    Run before ``orchestrator_output.json`` is rewritten, so no view of an
    earlier output survives beside the new one: exit 3, naming the file, when
    one cannot be removed (``validation.remove_host_view``).
    """
    remove_host_view(str(summary_path_for(output_path)))
    details = Path(output_path).with_name(ORCHESTRATOR_BATCHES_DIRNAME)
    if details.is_dir() and not details.is_symlink():
        for entry in sorted(details.iterdir()):
            remove_host_view(str(entry))
    else:
        remove_host_view(str(details))


def publish_orchestrator_views(
    output: Dict[str, Any],
    output_path: os.PathLike | str,
    write_tasks: Optional[Sequence[Dict[str, Any]]] = None,
) -> Optional[Path]:
    """Write each batch's detail file, then the summary naming them; the summary's path.

    Run once ``orchestrator_output.json`` and, when it has batches,
    ``write_tasks.json`` are written: every batch must pair with its write task,
    the ids the loop is keyed on. ``None``, with no summary on disk, when they
    do not pair or a file cannot be written: a host that finds no summary reads
    ``orchestrator_output.json`` and ``write_tasks.json``, the fallback its
    instructions name.
    """
    target = summary_path_for(output_path)
    batches = list(output.get("batches") or [])
    tasks = [t for t in (write_tasks or []) if isinstance(t, dict)]
    if batches and (
        len(tasks) != len(batches)
        or not all(_DETAIL_NAME.match(str(t.get("task_id") or "")) for t in tasks)
    ):
        print(
            f"WARNING: {target.name} not written (the batches do not pair with "
            f"their write tasks); a host reads {Path(output_path).name} instead",
            file=sys.stderr,
        )
        return None
    try:
        details = [
            (batch_detail_path(output_path, task["task_id"]),
             json.dumps(build_batch_detail(batch, task), indent=2) + "\n")
            for batch, task in zip(batches, tasks)
        ]
        text = json.dumps(
            build_orchestrator_summary(output, tasks, output_path), indent=2
        ) + "\n"
    except (TypeError, ValueError) as exc:
        print(
            f"WARNING: {target.name} not written ({exc}); a host reads "
            f"{Path(output_path).name} instead",
            file=sys.stderr,
        )
        return None
    for path, detail in details:
        if not publish_host_view(str(path), detail):
            return None
    if not publish_host_view(str(target), text):
        return None
    return target


def detail_pointer_lines(output_path: os.PathLike | str) -> List[str]:
    """Where a phase's text summary sends the reader for what it leaves out.

    The text summary stops at the counts: every batch with its items is in
    ``orchestrator_output.json``, and what a host's batch loop needs is in the
    summary beside it, so neither is printed again as the command's output.
    """
    output = Path(output_path)
    lines = [f"Batches and their items: {output}"]
    summary = output.with_name(ORCHESTRATOR_SUMMARY_FILENAME)
    if summary.is_file():
        lines.append(f"Batch ids, counts and items to decide: {summary}")
    return lines


def write_and_emit_output(
    output: Dict[str, Any],
    phase_dir: str,
    filename: str = "orchestrator_output.json",
) -> Path:
    """Write orchestrator output to a JSON file and emit the [OUTPUT_FILE] marker.

    This is the shared pattern used by all three apply orchestrators:
    1. Ensure the phase directory exists
    2. Write the output dict as JSON to ``phase_dir/filename``
    3. Print ``[OUTPUT_FILE] <path>`` to stderr

    Args:
        output: The orchestrator output dictionary to serialize.
        phase_dir: Directory for the phase (e.g., ``out_dir/apply-suggestions``).
        filename: Name of the output file (default: ``orchestrator_output.json``).

    Returns:
        The Path to the written output file.
    """
    os.makedirs(phase_dir, exist_ok=True)
    output_file = Path(phase_dir) / filename
    is_output = filename == "orchestrator_output.json"
    if is_output:
        invalidate_orchestrator_views(output_file)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    if is_output:
        # These outputs hand out no batch, so no write task is waited for.
        publish_orchestrator_views(output, output_file)
    print(f"[OUTPUT_FILE] {output_file}", file=sys.stderr)
    return output_file


def emit_json_output(
    output: Dict[str, Any],
    stream: Optional[TextIO] = None,
    indent: Optional[int] = 2,
) -> None:
    """Print orchestrator output as JSON to *stream* (default: stdout).

    The apply orchestrators reach this through
    ``ApplyOrchestratorBase.emit_payload``, which passes the stdout an
    ``--output-format json`` run reserved for its one document.
    """
    print(json.dumps(output, indent=indent), file=stream or sys.stdout)


def build_skipped_output(
    phase: str,
    message: str,
) -> Dict[str, Any]:
    """Build a standard skipped-phase output dictionary.

    Used when an apply phase has no actionable findings and should be
    skipped cleanly. All three orchestrators produce the same shape.

    Args:
        phase: The phase name (e.g., ``apply-task-suggestions``).
        message: Human-readable skip reason.

    Returns:
        Output dict with status='skipped', the message, phase, and empty batches.
    """
    return {
        "status": "skipped",
        "message": message,
        "phase": phase,
        "batches": [],
    }


def build_confirmation_needed_output(
    phase: str,
    message: str,
    item_count: int,
) -> Dict[str, Any]:
    """Build a standard confirmation-needed output dictionary.

    Used when no user selections are found and the orchestrator needs
    the user to confirm before proceeding. All three orchestrators
    produce the same shape.

    Args:
        phase: The phase name.
        message: Human-readable message explaining what will happen.
        item_count: Number of items that would be applied.

    Returns:
        Output dict with status='confirmation_needed'.
    """
    return {
        "status": "confirmation_needed",
        "message": message,
        "phase": phase,
        "item_count": item_count,
    }
