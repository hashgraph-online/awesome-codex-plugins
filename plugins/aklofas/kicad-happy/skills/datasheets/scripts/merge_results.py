#!/usr/bin/env python3
"""Phase 3a — Merge per-task result files into <mpn>.json.

Reads <mpn>.plan.json + per-task wrapped result files, validates each `data`
against the declared schema (using referencing.Registry for local $ref
resolution), splices into the canonical extraction shape, and writes <mpn>.json.

Failure semantics (Phase 3a):
- status:"complete" + schema-valid  → splice into top-level field.
- status:"failed" OR schema-invalid → on first failure, mark task for retry
  (no auto re-dispatch — the dispatcher recipe handles re-run); on second
  failure, partial-merge with {"_extraction_failed": true, "reason": ...}.

Stdlib + jsonschema + referencing (already dev deps). Requires jsonschema and
referencing — extraction_schema imports them when validation runs and raises
RuntimeError when they are missing; no fallback. The script's only purpose is
schema validation; silent-pass on missing deps is dangerous.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from extraction_schema import validate_against_schema


SKILL_ROOT = Path(__file__).resolve().parents[1]          # skills/datasheets
SCHEMA_DIR = SKILL_ROOT / "schemas"
_LEGACY_PREFIX = "skills/datasheets/"


def resolve_skill_resource(rel: str) -> Path:
    """Map a resource reference to a path inside this skill.

    Extraction plans persisted before v3 carry repo-relative strings such as
    'skills/datasheets/schemas/base.schema.json'; a copied skill still owns
    that file at SKILL_ROOT / 'schemas/base.schema.json'. Absolute paths pass
    through unchanged (custom schema locations)."""
    p = Path(rel)
    if p.is_absolute():
        return p
    s = p.as_posix()
    if s.startswith(_LEGACY_PREFIX):
        s = s[len(_LEGACY_PREFIX):]
    return SKILL_ROOT / s


EXTRACTOR_SCHEMA_VERSION = "1.0"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_result(cache: Path, mpn: str, task_id: str) -> "dict | None":
    p = cache / f"{mpn}.{task_id}.result.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "task_id": task_id,
            "status": "failed",
            "error": f"result file is not valid JSON: {exc}",
            "data": None,
        }


def _classify(result: "dict | None", schema: dict) -> "tuple[str, str | None]":
    """Return ('complete'|'failed', error_message)."""
    if result is None:
        return "failed", "no result file found"
    if result.get("status") != "complete":
        return "failed", result.get("error") or "result file status != 'complete'"
    err = validate_against_schema(result.get("data"), schema)
    if err:
        return "failed", f"schema validation: {err}"
    return "complete", None


def _splice_field(extraction: dict, task_id: str, role: str, data) -> None:
    """Place `data` at the right top-level field per spec.

    - base task data  → extraction["base"] (object).
    - pinout task data → extraction["base"]["pinout"] (list[Pin]).
      If base was already merged, the pinout task's data overwrites base.pinout.
    - category tasks  → extraction[role] (e.g. extraction["regulator"]).
    """
    if role == "base":
        # Preserve pinout if it was spliced before base (shouldn't happen, but
        # defend against task ordering variations).
        existing_pinout = (
            extraction.get("base", {}).get("pinout")
            if extraction.get("base")
            else None
        )
        extraction["base"] = data
        if existing_pinout is not None:
            extraction["base"]["pinout"] = existing_pinout
    elif role == "pinout":
        # Pinout task data is list[Pin]; nest under base.pinout.
        extraction.setdefault("base", {})["pinout"] = data
    else:
        # Category extension keyed by role (regulator, mcu, ...).
        extraction[role] = data
        cats = extraction.setdefault("categories", [])
        if role not in cats:
            cats.append(role)


def _initial_extraction(plan: dict) -> dict:
    return {
        "schema_version": {"base": "1.0", "categories": {}},
        "source": {
            "manufacturer": "",
            "mpn": plan["mpn"],
            "datasheet_revision": None,
            "datasheet_date": None,
            "source_url": None,
            "local_path": plan["pdf_path"],
            "sha256": plan["pdf_sha256"],
            "page_count": None,
            "family_ref": None,
        },
        "extraction": {
            "extracted_at": _now_iso(),
            "extractor_scout": None,
            "extractor_schema_version": EXTRACTOR_SCHEMA_VERSION,
            "quality_score": None,
            "plan_ref": f"{plan['mpn']}.plan.json",
        },
        "base": {},
        "categories": [],
    }


def _enrich_source_from_scout(extraction: dict, cache: Path, mpn: str) -> None:
    """Overlay scout metadata onto the source block. Silent on missing file."""
    p = cache / f"{mpn}.scout.json"
    if not p.exists():
        return
    try:
        scout = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    md = scout.get("metadata", {}) or {}
    src = extraction["source"]
    src["manufacturer"] = md.get("manufacturer", src["manufacturer"])
    src["datasheet_revision"] = md.get("datasheet_revision", src["datasheet_revision"])
    src["datasheet_date"] = md.get("datasheet_date", src["datasheet_date"])
    src["source_url"] = md.get("source_url", src["source_url"])
    src["page_count"] = md.get("page_count", src["page_count"])


def _record_outcome(
    plan: dict,
    task_id: str,
    attempts: int,
    status: str,
    err: "str | None",
) -> None:
    outcomes = plan["execution"]["outcomes"]
    for o in outcomes:
        if o["task_id"] == task_id:
            o["attempts"] = attempts
            o["final_status"] = status
            o["last_error"] = err
            return
    outcomes.append(
        {
            "task_id": task_id,
            "attempts": attempts,
            "final_status": status,
            "last_error": err,
        }
    )


# ---------------------------------------------------------------------------
# Core merge logic
# ---------------------------------------------------------------------------


def merge(cache: Path, mpn: str, *, retry_failed: bool = False) -> int:
    plan_path = cache / f"{mpn}.plan.json"
    if not plan_path.exists():
        print(f"error: plan not found at {plan_path}", file=sys.stderr)
        return 2
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if plan["execution"]["started_at"] is None:
        plan["execution"]["started_at"] = _now_iso()

    extraction = _initial_extraction(plan)
    _enrich_source_from_scout(extraction, cache, mpn)

    failed_tasks: list[tuple[dict, str]] = []
    schema_versions: dict[str, str] = {}

    for task in plan["tasks"]:
        tid = task["task_id"]
        role = task["subagent_role"]
        schema_path = resolve_skill_resource(task["schema"])
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        result = _read_result(cache, mpn, tid)
        status, err = _classify(result, schema)

        # Track attempt count — start from any prior recorded attempts.
        prior = next(
            (o for o in plan["execution"]["outcomes"] if o["task_id"] == tid), None
        )
        attempts = (prior["attempts"] if prior else 0) + 1

        if status == "complete":
            _splice_field(extraction, tid, role, result["data"])
            task["status"] = "complete"
            task["result_ref"] = f"{mpn}.{tid}.result.json"
            _record_outcome(plan, tid, attempts, "complete", None)
            sv = result.get("schema_version")
            if sv and role not in ("base", "pinout"):
                schema_versions[role] = sv
        else:
            failed_tasks.append((task, err or "unknown failure"))
            task["status"] = "failed"
            _record_outcome(plan, tid, attempts, "failed", err)

    if schema_versions:
        extraction["schema_version"]["categories"].update(schema_versions)

    # Phase 3a failure/retry policy.
    if failed_tasks and not retry_failed:
        # First merge with failures: write plan state, exit nonzero.
        # Caller re-dispatches failed tasks, then re-runs with --retry-failed.
        plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True))
        for task, err in failed_tasks:
            print(f"failed: {task['task_id']}: {err}", file=sys.stderr)
        print(
            "re-dispatch failed tasks per dispatcher recipe, "
            "then re-run with --retry-failed",
            file=sys.stderr,
        )
        return 1

    if failed_tasks and retry_failed:
        # Second failure after retry: partial-merge with sentinel.
        for task, err in failed_tasks:
            tid = task["task_id"]
            role = task["subagent_role"]
            sentinel = {"_extraction_failed": True, "reason": err}
            if role == "base":
                extraction["base"] = sentinel
            elif role == "pinout":
                extraction.setdefault("base", {})["pinout"] = sentinel
            else:
                extraction[role] = sentinel
                cats = extraction.setdefault("categories", [])
                if role not in cats:
                    cats.append(role)
            _record_outcome(plan, tid, 2, "partial", err)

    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from datasheet_score import score_v14_extraction
        extraction["extraction"]["quality_score"] = score_v14_extraction(extraction)["score"]
    except Exception as exc:  # noqa: BLE001
        print(f"warning: quality scoring failed: {exc}", file=sys.stderr)
        extraction["extraction"]["quality_score"] = None
    plan["execution"]["completed_at"] = _now_iso()

    out_path = cache / f"{mpn}.json"
    out_path.write_text(json.dumps(extraction, indent=2, sort_keys=True))
    plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True))
    print(f"{mpn}: merged → {out_path}")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: "list[str] | None" = None) -> int:
    ap = argparse.ArgumentParser(
        description="Merge per-task result files into <mpn>.json."
    )
    ap.add_argument("mpn")
    ap.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("datasheets/extracted"),
    )
    ap.add_argument(
        "--retry-failed",
        action="store_true",
        help=(
            "Treat this as the post-retry merge — "
            "partial-merge any still-failing tasks."
        ),
    )
    args = ap.parse_args(argv)
    return merge(args.cache_dir, args.mpn, retry_failed=args.retry_failed)


if __name__ == "__main__":
    sys.exit(main())
