"""Build a review plan JSON for dispatcher consumption.

design_context is an optional Deep Review input (v2.0 spec §3.B); the
Layer 2 reviewer role is retired (spec §5). Emits a 1-task plan for the
design_context subagent.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_plan(analysis_dir):
    """Build a 1-task review plan: design_context only.

    The Layer 2 reviewer task is retired in v2.0 (spec §5).
    design_context remains as an optional Deep Review input.
    """
    analysis_dir = Path(analysis_dir)
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
                    str(analysis_dir / "schematic.json"),
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
        args.output.write_text(out)
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
