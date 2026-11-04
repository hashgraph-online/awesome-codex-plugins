#!/usr/bin/env python3
"""``multi_llm.py util restore-batch`` — explicit, verified rollback (D3l).

D3h's per-task pre-batch snapshots become *usable* through this command. Three
properties are the whole design:

* **Never automatic.** A partial application stops the write loop and leaves the
  bytes in place; the exit-3 message *names* this command rather than silently
  reverting, because an automatic revert would destroy the half-applied state a
  human needs to inspect.
* **Verified.** It restores snapshot bytes for exactly the files the audit record
  lists as touched, and **refuses** a file whose current sha256 no longer matches
  what the audit recorded at completion — someone edited it since the run, and
  reverting their edit would be a second data-loss bug. ``--force`` overrides,
  deliberately explicitly. The record is the batch's own, found by the items
  its snapshot manifest names (an apply id is positional, and a set-aside
  snapshot's record sits under an id another batch now owns); a snapshot with
  no record at all is UNVERIFIED and restored only under ``--force``.
* **Auditable.** It appends its own ``restored`` line to
  ``{phase}/subagent_audit.jsonl``, so a rollback is an event in the same log the
  dispatch is.

``git`` is never assumed as the rollback mechanism: the target file is frequently
untracked, which every ``git diff`` / ``git checkout`` variant handles wrongly for
this purpose (D3g).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

try:  # pragma: no cover - import shim mirrors the rest of utils/
    from .stream_bootstrap import bootstrap_streams
    from .write_safety import (
        AuditLog, TaskSnapshot, WriteSafetyError, resolve_repo_root, safety_dir,
    )
except ImportError:  # pragma: no cover - direct-script invocation
    from stream_bootstrap import bootstrap_streams
    from write_safety import (  # type: ignore[no-redef]
        AuditLog, TaskSnapshot, WriteSafetyError, resolve_repo_root, safety_dir,
    )


EXIT_OK = 0
EXIT_ERROR = 1
EXIT_NOTHING_TO_DO = 2
EXIT_NEEDS_HUMAN = 3


def _task_ids(phase_dir: str, args: argparse.Namespace) -> List[str]:
    """The snapshot directory names to restore.

    ``--all-failed`` resolves each failed completion to the snapshot holding
    its items (``TaskSnapshot.locate``): the slot, or the set-aside copy a
    later resume moved it to when the slot's positional id went to other
    items. A failure with no snapshot on disk keeps its id, so the restore
    reports the missing snapshot by name rather than dropping it silently.
    """
    if args.task_id:
        return list(args.task_id)
    audit = AuditLog(phase_dir)
    names: List[str] = []
    for record in audit.failed_completions():
        task_id = str(record.get("task_id"))
        name = TaskSnapshot.locate(phase_dir, task_id, record.get("expected_ids"))
        name = name or task_id
        if name not in names:
            names.append(name)
    return names


def restore(
    *,
    phase_dir: str,
    task_ids: Sequence[str],
    force: bool = False,
    dry_run: bool = False,
) -> Dict[str, Dict[str, str]]:
    """Restore each task's snapshot, verifying against the audit record.

    Returns ``{task_id: {relative_path: outcome}}``. An outcome beginning
    ``skipped:`` is a refusal, never a silent no-op.
    """
    audit = AuditLog(phase_dir)
    results: Dict[str, Dict[str, str]] = {}
    # The root a snapshot may be restored under is this phase dir's own
    # repository, pinned independently of git's configuration; a manifest
    # naming another root is refused by `TaskSnapshot.load` (review fixes
    # 2026-10-05). A root that cannot be pinned refuses every restore.
    try:
        repo_root = resolve_repo_root(phase_dir)
    except WriteSafetyError as exc:
        return {task_id: {"*": f"skipped: {exc.message}"} for task_id in task_ids}
    for task_id in task_ids:
        try:
            snapshot = TaskSnapshot.load(phase_dir, task_id, expected_root=repo_root)
        except WriteSafetyError as exc:
            results[task_id] = {"*": f"skipped: {exc.message}"}
            continue
        if snapshot is None:
            results[task_id] = {
                "*": (
                    "skipped: no pre-batch snapshot under "
                    f"{Path(safety_dir(phase_dir)) / 'pre_batch' / task_id}"
                )
            }
            continue
        # The completion record is the batch's, found by the items the
        # manifest names rather than by the directory name: a set-aside
        # snapshot (`<id>.items-<sha8>`) has its record under the id another
        # batch now owns, and the slot's record may be that other batch's.
        recorded = audit.completion_for(
            snapshot.task_id, expected_ids=snapshot.expected_ids,
        )
        touched = list((recorded or {}).get("files_touched") or [])
        expected = AuditLog.hashes_from(recorded)
        verified = recorded is not None
        if recorded is None:
            # No completion record: the run died before classifying. Nothing
            # says what the batch touched or what the files looked like after
            # it, so a restore here is UNVERIFIED — every snapshotted file,
            # whatever its bytes are now — and only `--force` may take it
            # (adversarial review, 2026-10-02: this branch used to restore at
            # exit 0 and wiped a later batch's edit and the user's own).
            touched = [entry.relative for entry in snapshot.entries]
            expected = {}
            if not force:
                results[task_id] = {
                    "*": (
                        "skipped: UNVERIFIED — the audit log records no "
                        "completion for these items, so nothing says what "
                        "the batch touched or whether the files changed "
                        "since; pass --force to restore every snapshotted "
                        "file anyway ("
                        + ", ".join(touched) + ")"
                    )
                }
                continue
        if not touched:
            results[task_id] = {
                "*": "skipped: the audit record lists no touched files for this task"
            }
            continue
        if dry_run:
            word = "would restore" if verified else "would restore (UNVERIFIED)"
            results[task_id] = {path: word for path in touched}
            continue
        report = snapshot.restore(touched, expected=expected or None, force=force)
        audit.restored(
            task_id=task_id, report=report, force=force, verified=verified,
        )
        results[task_id] = report
    return results


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point. Exit 0 restored, 2 nothing to restore, 3 a refusal, 1 error."""
    bootstrap_streams()
    parser = argparse.ArgumentParser(
        prog="multi_llm.py util restore-batch",
        description=(
            "Restore a failed write batch from its pre-batch snapshot, refusing "
            "any file that changed after the run."
        ),
    )
    parser.add_argument(
        "--phase-dir", required=True,
        help="The write phase's directory (where pre_batch/ and "
             "subagent_audit.jsonl live).",
    )
    parser.add_argument(
        "--task-id", action="append", default=[],
        help="Task id to restore. Repeatable. Omit with --all-failed.",
    )
    parser.add_argument(
        "--all-failed", action="store_true",
        help="Restore every task the audit log records as failed, partially "
             "applied or policy-violating.",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Restore even a file whose current sha256 no longer matches what the "
             "audit recorded at completion (i.e. one edited since the run). "
             "Never the default: that edit would be destroyed.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would be restored and change nothing.",
    )
    parser.add_argument(
        "--json", action="store_true", help="Emit the result map as JSON.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    # Keep the lexical alias until trusted discovery checks it: resolving a
    # replaced symlink here would discard the identity bound before dispatch.
    phase_dir = os.path.abspath(args.phase_dir)
    if not Path(phase_dir).is_dir():
        print(f"ERROR: phase dir not found: {phase_dir}", file=sys.stderr)
        return EXIT_ERROR
    if not args.task_id and not args.all_failed:
        print(
            "ERROR: pass --task-id <id> (repeatable) or --all-failed. Restoring "
            "everything by default would be exactly the automatic revert this "
            "command exists to avoid.",
            file=sys.stderr,
        )
        return EXIT_NEEDS_HUMAN

    try:
        safety_dir(phase_dir)
        task_ids = _task_ids(phase_dir, args)
    except WriteSafetyError as exc:
        print(f"ERROR: {exc.message}", file=sys.stderr)
        return EXIT_NEEDS_HUMAN
    if not task_ids:
        print(
            f"Nothing to restore: {AuditLog(phase_dir).path} records no failed "
            f"write task.",
        )
        return EXIT_NOTHING_TO_DO

    results = restore(
        phase_dir=phase_dir, task_ids=task_ids, force=args.force,
        dry_run=args.dry_run,
    )
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for task_id, report in results.items():
            print(f"{task_id}:")
            for path, outcome in sorted(report.items()):
                print(f"  {path}: {outcome}")

    refused = [
        (task_id, path, outcome)
        for task_id, report in results.items()
        for path, outcome in report.items()
        if outcome.startswith("skipped:")
    ]
    if refused:
        print(
            f"\n{len(refused)} file(s) were NOT restored. A file that changed "
            f"after the run is refused on purpose — inspect it, then re-run with "
            f"--force if you really want the snapshot bytes back.",
            file=sys.stderr,
        )
        return EXIT_NEEDS_HUMAN
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
