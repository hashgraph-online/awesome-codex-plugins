"""``multi_llm.py util runs [--sweep]``: this project's detached runs, listed
and swept.

The registry (``utils/run_registry.py``) holds the entries and decides what a
sweep does with each one; closing a run out and stopping its processes belong
to the run-lifecycle owner, ``detach`` (``close_out_entry``,
``stop_recorded_run``), which sits above the registry. This command is where
the two meet: :func:`sweep` hands ``detach``'s two to ``run_registry.sweep``,
so the registry imports nothing above its layer
(docs/development/dispatcher.md#import-layers).
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

from . import detach, run_registry
from .run_registry import (
    NEEDS_ATTENTION,
    PRUNE_AFTER_DAYS,
    _age_days,
    list_entries,
    registry_dir,
    resolve_project_root,
    verdict_for,
)
from .stream_bootstrap import bootstrap_streams


def sweep(project_root: str, **options: Any) -> List[Dict[str, Any]]:
    """:func:`run_registry.sweep` with the run-lifecycle owner's close-out and
    kill, ``detach.close_out_entry`` and ``detach.stop_recorded_run``, read
    from ``detach`` on each call. *options* are the sweep's own (``kill``,
    ``prune_after_days``)."""
    return run_registry.sweep(
        project_root,
        close_out_entry=detach.close_out_entry,
        stop_recorded_run=detach.stop_recorded_run,
        **options,
    )


def _render_row(row: Dict[str, Any]) -> str:
    entry = row["entry"]
    age = row["age_days"]
    age_text = f"{age * 24:.1f}h" if age is not None and age < 1 else (
        f"{age:.1f}d" if age is not None else "?"
    )
    return (
        f"  {str(row['run_id'])[:8]}  {row['verdict']:<7} {row['action']:<7} "
        f"{age_text:<7} {entry.get('mode', '?'):<14} "
        f"{entry.get('phase_dir', '?')}"
    )


def main(argv: Optional[List[str]] = None) -> int:
    """``util runs [--sweep]``: list every registry entry with its verdict."""
    bootstrap_streams()
    parser = argparse.ArgumentParser(
        prog="multi_llm.py util runs",
        description="List (and optionally sweep) this project's detached runs.",
    )
    parser.add_argument(
        "--project-root",
        default=None,
        help="Project root holding .multi-llm/runs (default: git root of --plan-file or CWD)",
    )
    parser.add_argument(
        "--plan-file",
        default=None,
        help="Resolve the project root from this plan file instead of the CWD",
    )
    parser.add_argument(
        "--sweep",
        action="store_true",
        help="Close out entries whose identity probe fails, kill surviving "
             "process-group members, delete their registry files and prune "
             f"entries older than {PRUNE_AFTER_DAYS} days; exit 3 when a run's "
             "processes could not all be confirmed stopped (its entry is kept)",
    )
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    args = parser.parse_args(argv)

    root = args.project_root or resolve_project_root(args.plan_file)
    if args.sweep:
        rows = sweep(root)
    else:
        rows = [
            {"run_id": e.get("run_id"), "verdict": verdict_for(e), "action": "listed",
             "age_days": _age_days(e), "entry": e}
            for e in list_entries(root)
        ]

    if args.json:
        print(json.dumps({"project_root": str(root), "runs": rows}, indent=2, default=str))
    else:
        print(f"detached runs registered under {registry_dir(root)}:")
        if not rows:
            print("  (none)")
        for row in rows:
            print(_render_row(row))
        if not args.sweep:
            print("\nRun with --sweep to close out and remove dead entries.")
        elif any(row["action"] == NEEDS_ATTENTION for row in rows):
            print("\nneeds_attention: not every process of these runs could be "
                  "confirmed stopped, and what could not be identified as theirs "
                  "was not signalled; their entries are kept for the next sweep. "
                  "Check each one's process group by hand.")
    if args.sweep and any(row["action"] == NEEDS_ATTENTION for row in rows):
        return 3
    return 0


if __name__ == "__main__":  # pragma: no cover - direct invocation
    sys.exit(main(sys.argv[1:]))
