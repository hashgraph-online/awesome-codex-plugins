#!/usr/bin/env python3
"""Plan an extraction run.

Computes PDF SHA, dispatches scout (or reads cached scout), generates
<mpn>.plan.json. Stdlib-only. The dispatcher (separate concern) reads the
plan and executes per-task subagents per dispatcher-contract.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_SKILL_ROOT = str(Path(__file__).resolve().parent.parent)
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from datasheet_types.cache_reader import read_json_object, sanitize_mpn  # noqa: E402
from distributor_core.manifest import write_json_atomic  # noqa: E402
from merge_results import _SAFE_TASK_ID  # noqa: E402

PLAN_VERSION = "1.0"

# task_id → (subagent_role, tier, schema_path, prompt_path) relative to repo root
ALWAYS_TASKS = {
    "base":   ("base",   "B", "skills/datasheets/schemas/base.schema.json",
               "skills/datasheets/prompts/base.md"),
    "pinout": ("pinout", "A", "skills/datasheets/schemas/pinout.schema.json",
               "skills/datasheets/prompts/pinout.md"),
}
CATEGORY_TASKS = {
    "regulator":  ("regulator",  "B", "skills/datasheets/schemas/regulator.schema.json",
                   "skills/datasheets/prompts/regulator.md"),
    "diode":      ("diode",      "B", "skills/datasheets/schemas/diode.schema.json",
                   "skills/datasheets/prompts/diode.md"),
    "transistor": ("transistor", "B", "skills/datasheets/schemas/transistor.schema.json",
                   "skills/datasheets/prompts/transistor.md"),
    "opamp":      ("opamp",      "B", "skills/datasheets/schemas/opamp.schema.json",
                   "skills/datasheets/prompts/opamp.md"),
    "mcu":        ("mcu",        "B", "skills/datasheets/schemas/mcu.schema.json",
                   "skills/datasheets/prompts/mcu.md"),
    "crystal":    ("crystal",    "B", "skills/datasheets/schemas/crystal.schema.json",
                   "skills/datasheets/prompts/crystal.md"),
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_existing_extraction(cache_dir: Path, mpn: str) -> dict | None:
    p = cache_dir / f"{sanitize_mpn(mpn)}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _is_cache_current(existing: dict, pdf_sha: str) -> bool:
    """Cache is current iff the recorded SHA matches the PDF's SHA."""
    src_sha = (existing.get("source") or {}).get("sha256")
    return src_sha == pdf_sha


def _drop_stale_results(cache_dir: Path, mpn: str, pdf_sha: str) -> None:
    """Remove the previous plan's task results when the PDF changed, so a
    re-dispatch cannot reuse facts read from another revision."""
    old = read_json_object(cache_dir / f"{sanitize_mpn(mpn)}.plan.json")
    if not old or old.get("pdf_sha256") == pdf_sha:
        return
    removed = 0
    for task in old.get("tasks") or []:
        tid = task.get("task_id") if isinstance(task, dict) else None
        if not isinstance(tid, str) or tid in (".", "..") or not _SAFE_TASK_ID.fullmatch(tid):
            continue
        p = cache_dir / f"{sanitize_mpn(mpn)}.{tid}.result.json"
        if p.parent == cache_dir and (p.is_file() or p.is_symlink()):
            p.unlink()
            removed += 1
    print(f"{mpn}: PDF changed since the previous plan; removed {removed} stale task result(s)",
          file=sys.stderr)


def _load_scout(cache_dir: Path, mpn: str) -> dict:
    p = cache_dir / f"{sanitize_mpn(mpn)}.scout.json"
    if not p.exists():
        raise FileNotFoundError(
            f"Cached scout not found at {p}. Run scout subagent and write its data here, "
            f"or invoke without --use-cached-scout (live scout requires a dispatcher)."
        )
    return json.loads(p.read_text(encoding="utf-8"))


def _build_plan(mpn: str, pdf_path: Path, pdf_sha: str, cache_dir: Path, scout: dict) -> dict:
    tasks: list[dict] = []
    for tid, (role, tier, schema, prompt) in ALWAYS_TASKS.items():
        tasks.append({
            "task_id": tid,
            "subagent_role": role,
            "tier": tier,
            "schema": schema,
            "prompt_template": prompt,
            "pages": list(scout["extraction_pages"].get(tid, [])),
            "depends_on": [],
            "status": "pending",
            "result_ref": None,
        })
    for cat in scout.get("categories", []):
        if cat not in CATEGORY_TASKS:
            print(
                f"warning: unsupported category {cat!r} in scout output "
                f"(not yet registered in CATEGORY_TASKS — supported: "
                f"{sorted(CATEGORY_TASKS)}); skipping",
                file=sys.stderr,
            )
            continue
        role, tier, schema, prompt = CATEGORY_TASKS[cat]
        tasks.append({
            "task_id": cat,
            "subagent_role": role,
            "tier": tier,
            "schema": schema,
            "prompt_template": prompt,
            "pages": list(scout["extraction_pages"].get(cat, [])),
            "depends_on": [],
            "status": "pending",
            "result_ref": None,
        })
    return {
        "plan_version": PLAN_VERSION,
        "mpn": mpn,
        "pdf_path": str(pdf_path),
        "pdf_sha256": pdf_sha,
        "cache_dir": str(cache_dir),
        "created_at": _now_iso(),
        "scout_ref": f"{sanitize_mpn(mpn)}.scout.json",
        "tasks": tasks,
        "execution": {"started_at": None, "completed_at": None, "outcomes": []},
    }


def _build_skip_plan(mpn: str, pdf_path: Path, pdf_sha: str, cache_dir: Path) -> dict:
    return {
        "plan_version": PLAN_VERSION,
        "mpn": mpn,
        "pdf_path": str(pdf_path),
        "pdf_sha256": pdf_sha,
        "cache_dir": str(cache_dir),
        "created_at": _now_iso(),
        "scout_ref": f"{sanitize_mpn(mpn)}.scout.json",
        "tasks": [],
        "execution": {"started_at": None, "completed_at": None, "outcomes": []},
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Plan an extraction run.")
    ap.add_argument("mpn")
    ap.add_argument("pdf_path", type=Path)
    ap.add_argument("--cache-dir", type=Path, default=Path("datasheets/extracted"))
    ap.add_argument("--force", action="store_true",
                    help="Regenerate plan even if cache is current.")
    ap.add_argument("--use-cached-scout", action="store_true",
                    help="Read <mpn>.scout.json from cache_dir instead of dispatching scout. "
                         "The stdlib path requires this; live scout dispatch is the dispatcher's job.")
    args = ap.parse_args(argv)

    if not args.pdf_path.exists():
        print(f"error: PDF not found: {args.pdf_path}", file=sys.stderr)
        return 2
    args.cache_dir.mkdir(parents=True, exist_ok=True)

    pdf_sha = _sha256(args.pdf_path)
    existing = _load_existing_extraction(args.cache_dir, args.mpn)
    if existing and _is_cache_current(existing, pdf_sha) and not args.force:
        print(f"{args.mpn}: already up-to-date (PDF SHA matches cache)")
        return 0

    if not args.use_cached_scout:
        print(
            "error: live scout dispatch is not implemented in plan_extraction.py. "
            "Run the scout subagent via dispatch-claude-code.md (or any dispatcher), "
            "write its output to <cache>/<mpn>.scout.json, then re-invoke with --use-cached-scout.",
            file=sys.stderr,
        )
        return 2

    scout = _load_scout(args.cache_dir, args.mpn)
    scout_sha = scout.get("pdf_sha256")
    if scout_sha is None:
        print(f"warning: cached scout for {args.mpn} has no PDF SHA; re-scout if the PDF changed",
              file=sys.stderr)
    elif scout_sha != pdf_sha:
        print(
            f"error: the cached scout for {args.mpn} was not made from this PDF "
            f"(scout pdf_sha256 {scout_sha!r}, PDF {pdf_sha}); "
            "re-run the scout on this PDF and write its pdf_sha256 into the scout file.",
            file=sys.stderr,
        )
        return 2
    _drop_stale_results(args.cache_dir, args.mpn, pdf_sha)

    verdict = (scout.get("quality_verdict") or {}).get("verdict")
    plan_path = args.cache_dir / f"{sanitize_mpn(args.mpn)}.plan.json"
    if verdict == "skip":
        plan = _build_skip_plan(args.mpn, args.pdf_path, pdf_sha, args.cache_dir)
        write_json_atomic(plan_path, plan)
        reason = (scout.get("quality_verdict") or {}).get("reason")
        print(
            f"{args.mpn}: scout verdict 'skip' ({reason}); empty plan written, no extraction dispatched",
            file=sys.stderr,
        )
        return 1

    plan = _build_plan(args.mpn, args.pdf_path, pdf_sha, args.cache_dir, scout)
    write_json_atomic(plan_path, plan)
    print(f"{args.mpn}: plan written to {plan_path} ({len(plan['tasks'])} tasks)")
    print(f"  next: run dispatcher per skills/datasheets/references/dispatch-claude-code.md")
    return 0


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):  # UTF-8 on a cp1252 pipe (Windows)
        if (getattr(_stream, "encoding", "") or "").lower().replace("-", "") != "utf8" \
                and hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    sys.exit(main())
