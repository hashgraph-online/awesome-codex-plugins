"""Build a review plan JSON for dispatcher consumption.

design_context is an optional Deep Review input; there is no Layer 2
reviewer task. Emits a 1-task plan for the design_context subagent.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))   # skills/kicad/scripts

from deep_review_gate import resolve_run_dir   # noqa: E402
from kicad_core.fileio import atomic_write_text   # noqa: E402


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_plan(analysis_dir):
    """Build a 1-task review plan: design_context only.

    design_context is an optional Deep Review input. The
    schematic input is the current run's (analysis/manifest.json), or
    the one directly in `analysis_dir` for a flat layout.
    """
    analysis_dir = Path(analysis_dir)
    run_dir = resolve_run_dir(analysis_dir)
    now = _now_iso()
    plan = {
        "schema_version": "1.0",
        "plan_id": f"review-{now}",
        "created_at": now,
        "purpose": "phase4_review",
        "tasks": [
            {
                "task_id": "design_context",
                "task_type": "review",
                "tier": "B",
                "prompt_path": "skills/kicad/review/prompts/design_context.md",
                "result_path": str(analysis_dir / "design_context.json"),
                "result_schema": "skills/kicad/review/schemas/design_context.schema.json",
                "input_artifacts": [
                    str(run_dir / "schematic.json"),
                    ".kicad-happy.json",
                ],
            },
        ],
    }
    return plan


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--analysis-dir", required=True, type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    plan = build_plan(args.analysis_dir)
    out = json.dumps(plan, indent=2, sort_keys=True) + "\n"
    if args.output:
        atomic_write_text(args.output, out, follow_symlinks=False)
    else:
        print(out)
    return 0


if __name__ == "__main__":
    from kicad_core.cli import utf8_stdio
    utf8_stdio()
    sys.exit(main())
