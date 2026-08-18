"""Layer 2 annotation merge tool. Phase 4 spec §4.3.

v2.0: authority caps removed (spec §5 — trust comes from the Deep Review
evidence gate, not permission rules). HI-3 (strip llm_* → byte-identical
baseline) still holds.

Validates review_annotations.json against schema, applies the overlay
(suppressed annotations now always apply), writes
analysis/merged/<analyzer>.json overlay artifacts, and verifies HI-3
strip-LLM round-trip byte equivalence.

Failure semantics: orphan annotations are LOGGED in the merge report and
SKIPPED. The merge itself never fails on these — analyzer outputs always
advance. Schema validation errors are hard-fail (caller's responsibility).

Schema validation uses the stdlib-only mini-validator at
`_mini_jsonschema.py` (kept narrow to the keyword subset Layer 2 needs).
No third-party `jsonschema` dependency. Audit C2 — see CHANGELOG.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
SCHEMA_PATH = REPO_ROOT / "skills" / "kicad" / "review" / "schemas" / "review_annotations.schema.json"

ANALYZER_FILES = ["schematic.json", "pcb.json", "emc.json", "thermal.json",
                   "gerber.json", "cross_analysis.json"]


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def strip_llm_overlays(data):
    """Recursively remove all keys starting with 'llm_'. Phase 4 spec §3.4 / HI-3."""
    if isinstance(data, dict):
        return {k: strip_llm_overlays(v) for k, v in data.items()
                if not k.startswith("llm_")}
    if isinstance(data, list):
        return [strip_llm_overlays(item) for item in data]
    return data


def _load_raw_envelopes(raw_dir: Path) -> dict:
    """Load every analyzer JSON in raw_dir into a dict keyed by stem."""
    envelopes = {}
    for fname in ANALYZER_FILES:
        path = raw_dir / fname
        if path.exists():
            envelopes[path.stem] = json.loads(path.read_text())
    return envelopes


def _validate_review_schema(review: dict) -> None:
    """Hard-fail if review_annotations doesn't match schema (HI-2 protection).

    Uses the stdlib-only mini-validator at `_mini_jsonschema.py` so Layer 2
    works without the optional `jsonschema` package. If the Layer 2 schema
    grows beyond the mini-validator's supported keyword set, the validator
    raises a "unsupported schema keyword" ValidationError — switch this
    consumer back to the real jsonschema package at that point rather than
    silently extending the mini-validator (audit C2).
    """
    from _mini_jsonschema import validate
    schema = json.loads(SCHEMA_PATH.read_text())
    validate(review, schema)


def _find_finding(envelopes: dict, finding_id: str):
    """Find a finding by id across all loaded envelopes; return first match or None.

    Assumes finding_ids are globally unique across analyzer envelopes per the
    Phase 4 finding_id convention `<source>:<rule_id>:<locator>` (the source
    prefix differs per analyzer). Iteration order is deterministic via
    ANALYZER_FILES.
    """
    for env in envelopes.values():
        for f in env.get("findings", []):
            if f.get("finding_id") == finding_id:
                return f
    return None


def merge(raw_dir, review_path, merged_dir) -> dict:
    """Apply Layer 2 review annotations to raw analyzer outputs.

    Returns a merge report dict (also written to merged_dir/_merge_report.json).
    Never raises on per-annotation failure: orphans and invariant violations
    are logged and skipped. Hard-fails only on schema-invalid review JSON or
    HI-3 round-trip byte mismatch.
    """
    raw_dir = Path(raw_dir)
    review_path = Path(review_path)
    merged_dir = Path(merged_dir)

    envelopes = _load_raw_envelopes(raw_dir)
    review = json.loads(review_path.read_text())
    _validate_review_schema(review)  # hard-fail if malformed

    invariant_violations = []
    suppressed_count = 0
    applied = 0

    for ann in review.get("annotations", []):
        finding = _find_finding(envelopes, ann["finding_id"])
        if finding is None:
            invariant_violations.append({
                "type": "orphan_annotation",
                "finding_id": ann["finding_id"],
            })
            continue
        if ann["status"] == "suppressed":
            suppressed_count += 1
        finding["llm_review"] = {
            "status": ann["status"],
            "reason": ann["reason"],
            "confidence": ann["confidence"],
            "reviewed_at": ann["reviewed_at"],
        }
        if ann.get("suggested_severity"):
            finding["llm_review"]["suggested_severity"] = ann["suggested_severity"]
        applied += 1

    # Write merged outputs
    merged_dir.mkdir(parents=True, exist_ok=True)
    for stem, env in envelopes.items():
        (merged_dir / f"{stem}.json").write_text(
            json.dumps(env, indent=2, sort_keys=True) + "\n")

    # HI-3 round-trip verification (per-analyzer)
    for stem in envelopes:
        merged_data = json.loads((merged_dir / f"{stem}.json").read_text())
        original_raw = json.loads((raw_dir / f"{stem}.json").read_text())
        stripped = strip_llm_overlays(merged_data)
        if stripped != original_raw:
            raise RuntimeError(
                f"HI-3 violation: strip_llm_overlays(merged/{stem}.json) != raw/{stem}.json"
            )

    report = {
        "merged_at": _now_iso(),
        "produced_for_run_id": review.get("produced_for_run_id"),
        "annotation_count": len(review.get("annotations", [])),
        "applied_count": applied,
        "suppressed_count": suppressed_count,
        "orphan_annotations": [v for v in invariant_violations
                                if v["type"] == "orphan_annotation"],
        "invariant_violations": [v for v in invariant_violations
                                  if v["type"] != "orphan_annotation"],
        "reviewer_observations_count": len(review.get("reviewer_observations", [])),
    }
    (merged_dir / "_merge_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main():
    p = argparse.ArgumentParser(description="Apply Layer 2 review annotations to raw analyzer outputs.")
    p.add_argument("--raw-dir", required=True, type=Path)
    p.add_argument("--review", required=True, type=Path,
                    help="Path to review_annotations.json")
    p.add_argument("--merged-dir", required=True, type=Path)
    args = p.parse_args()
    report = merge(args.raw_dir, args.review, args.merged_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
