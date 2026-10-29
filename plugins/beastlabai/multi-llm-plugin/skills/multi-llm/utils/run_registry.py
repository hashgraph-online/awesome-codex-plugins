#!/usr/bin/env python3
"""The cross-plan registry of live detached runs.

``{phase}/.lock`` makes two runs on the *same* phase dir impossible, but nothing
in it bounds runs across phases and plans — a retrying shim, or a poll loop that
mistakes exit 2 for "launch again", can fork them without limit, each spawning
provider CLIs. So every detached run drops one small JSON file at
``{project_root}/.multi-llm/runs/<run_id>.json`` in the same step it takes the
lock, and removes it on any terminal state. Two things read it:

* ``--detach`` counts live entries before it forks and refuses above
  ``MULTI_LLM_MAX_DETACHED`` (default 4) — in the foreground, on the caller's
  terminal, before anything daemonizes.
* ``multi_llm.py util runs [--sweep]`` answers "the machine rebooted — what is
  still running?". A reboot leaves stale registry files and no processes, and one
  sweep reconciles both: close out the record, kill any surviving process-group
  member whose creation time still matches, delete the file, prune anything older
  than a week.

Sweeping is never automatic on launch. It kills things, so it is a verb a caller
runs.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

from . import process_control
from .stream_bootstrap import bootstrap_streams

#: Registry location, relative to the project root.
REGISTRY_RELPATH = os.path.join(".multi-llm", "runs")

#: Entries older than this are pruned by ``--sweep`` even if they were never
#: closed out (a reboot with no process left to probe).
PRUNE_AFTER_DAYS = 7

#: Default ceiling on concurrent detached runs per project.
DEFAULT_MAX_DETACHED = 4

#: Env override for the ceiling, so a CI job or a big machine can raise it
#: without a code change.
MAX_DETACHED_ENV = "MULTI_LLM_MAX_DETACHED"


def max_detached(override: Optional[int] = None) -> int:
    """The configured ceiling: flag beats env beats default."""
    if override is not None:
        return max(int(override), 1)
    raw = os.environ.get(MAX_DETACHED_ENV)
    if raw:
        try:
            return max(int(raw), 1)
        except ValueError:
            pass
    return DEFAULT_MAX_DETACHED


def resolve_project_root(anchor: Optional[str] = None) -> str:
    """The project root a registry lives under.

    The git top-level of *anchor* (a plan file or a directory), falling back to
    the anchor's own directory so a plan outside a repo still gets a registry
    rather than silently sharing one with the CWD.
    """
    anchor = str(anchor) if anchor else os.getcwd()
    try:
        from .git_utils import get_project_root, get_project_root_from_dir

        if os.path.isdir(anchor):
            root = get_project_root_from_dir(anchor)
        else:
            root = get_project_root(anchor)
        if root:
            return root
    except Exception:
        pass
    return anchor if os.path.isdir(anchor) else (os.path.dirname(anchor) or ".")


def registry_dir(project_root: str) -> str:
    return os.path.join(str(project_root), REGISTRY_RELPATH)


def entry_path(project_root: str, run_id: str) -> str:
    return os.path.join(registry_dir(project_root), f"{run_id}.json")


def write_entry(project_root: str, entry: Dict[str, Any]) -> Optional[str]:
    """Record one live run. Best-effort: a read-only project must not fail a run."""
    directory = registry_dir(project_root)
    path = entry_path(project_root, entry["run_id"])
    try:
        os.makedirs(directory, exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(entry, f, indent=2)
        os.replace(tmp, path)
        return path
    except (OSError, IOError):
        return None


def remove_entry(project_root: str, run_id: str) -> None:
    try:
        os.unlink(entry_path(project_root, run_id))
    except OSError:
        pass


def list_entries(project_root: str) -> List[Dict[str, Any]]:
    """Every registry entry, each annotated with its own file path."""
    directory = registry_dir(project_root)
    entries: List[Dict[str, Any]] = []
    try:
        names = sorted(os.listdir(directory))
    except OSError:
        return entries
    for name in names:
        if not name.endswith(".json"):
            continue
        path = os.path.join(directory, name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, IOError, ValueError):
            data = {"run_id": name[:-5], "corrupt": True}
        if isinstance(data, dict):
            data["_path"] = path
            entries.append(data)
    return entries


def verdict_for(entry: Dict[str, Any]) -> str:
    """``alive`` / ``dead`` / ``unknown`` for one entry's recorded identity."""
    return process_control.probe(
        entry.get("pid"), entry.get("process_start_time")
    )


def live_entries(project_root: str) -> List[Dict[str, Any]]:
    """Entries whose recorded process is alive (or unverifiably so).

    ``unknown`` counts as live on purpose: the ceiling exists to stop runaway
    provider spawning, and refusing to count a run we cannot disprove is the safe
    direction.
    """
    return [e for e in list_entries(project_root) if verdict_for(e) != process_control.DEAD]


def find_launch_key(project_root: str, launch_key: str) -> Optional[Dict[str, Any]]:
    """The live entry for a ``(mode, plan, phase[, ask slug])`` key, if any."""
    for entry in live_entries(project_root):
        if entry.get("launch_key") == launch_key:
            return entry
    return None


def _age_days(entry: Dict[str, Any]) -> Optional[float]:
    path = entry.get("_path")
    if not path:
        return None
    try:
        return (time.time() - os.path.getmtime(path)) / 86400.0
    except OSError:
        return None


def sweep(
    project_root: str,
    *,
    kill: bool = True,
    prune_after_days: int = PRUNE_AFTER_DAYS,
) -> List[Dict[str, Any]]:
    """Close out what earlier sessions left behind. Returns one row per entry.

    Each row carries ``run_id``, the liveness ``verdict``, the ``action`` taken
    (``kept`` / ``closed`` / ``pruned`` / ``killed``) and the entry itself, so the
    CLI and a test can assert on the same data.
    """
    rows: List[Dict[str, Any]] = []
    for entry in list_entries(project_root):
        verdict = verdict_for(entry)
        age = _age_days(entry)
        action = "kept"
        if verdict == process_control.DEAD:
            action = "closed"
            _close_out_phase_dir(entry)
            remove_entry(project_root, entry.get("run_id", ""))
        elif age is not None and age > prune_after_days:
            action = "pruned"
            if kill:
                # `skipped` is a real outcome here: a week-old entry whose
                # identity probe came back `unknown` (the /proc or ps read
                # failed) is a pid we cannot corroborate, and signalling its
                # process group would hit whatever recycled that pid. The entry
                # is still pruned; it is just not reported as killed. On
                # Windows the run's named job is the kill when it opens
                # (`process_control.kill_run_tree`).
                kill_verdict = process_control.kill_run_tree(
                    entry.get("run_id"),
                    entry.get("pid") or 0,
                    start_time=entry.get("process_start_time"),
                    pgid=entry.get("pgid"),
                )
                if kill_verdict in ("killed", "survived"):
                    action = "killed"
            _close_out_phase_dir(entry)
            remove_entry(project_root, entry.get("run_id", ""))
        rows.append(
            {"run_id": entry.get("run_id"), "verdict": verdict, "action": action,
             "age_days": age, "entry": entry}
        )
    return rows


def _close_out_phase_dir(entry: Dict[str, Any]) -> None:
    """Ask the run-lifecycle owner to write the terminal record for this entry.

    Imported lazily: the registry is also read by the launcher's pre-flight, and
    a cycle there would be gratuitous.
    """
    phase_dir = entry.get("phase_dir")
    run_id = entry.get("run_id")
    if not phase_dir or not run_id:
        return
    try:
        from . import detach

        detach.close_out_dead_run(str(phase_dir), reason="heartbeat_timeout")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# `multi_llm.py util runs`
# ---------------------------------------------------------------------------

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
             f"entries older than {PRUNE_AFTER_DAYS} days",
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
    return 0


if __name__ == "__main__":  # pragma: no cover - direct invocation
    sys.exit(main(sys.argv[1:]))
