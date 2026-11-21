#!/usr/bin/env python3
"""Read-only evidence audit for a persistent agent workspace."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3


OBJECTIVE_FILES = ("MANDATE.md", "CHARACTER.md", "AGENTS.md")


def finding(identifier: str, status: str, summary: str, evidence=None) -> dict:
    return {"id": identifier, "status": status, "summary": summary, "evidence": evidence or []}


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text())
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def sqlite_evidence(path: Path) -> tuple[set[str], bool]:
    try:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        healthy = connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        connection.close()
        return tables, healthy
    except sqlite3.Error:
        return set(), False


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_timestamp(value) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def audit(project: Path, state_dir: Path) -> dict:
    project, state_dir = project.resolve(), state_dir.resolve()
    results = []
    objectives = [project / name for name in OBJECTIVE_FILES if (project / name).is_file()]
    results.append(finding("authoritative-objective", "pass" if objectives else "fail",
        "An explicit objective or boundary source exists." if objectives else "No objective or boundary source found.",
        [str(path) for path in objectives]))

    sqlite_files = sorted(state_dir.glob("*.sqlite")) if state_dir.is_dir() else []
    json_files = sorted(state_dir.glob("*.json")) if state_dir.is_dir() else []
    results.append(finding("structured-state", "pass" if sqlite_files or json_files else "fail",
        "Structured durable state exists." if sqlite_files or json_files else "Only prose or no durable state was found.",
        [str(path) for path in sqlite_files + json_files[:10]]))

    database_evidence = {str(path): sqlite_evidence(path) for path in sqlite_files}
    corrupt_databases = [path for path, (_, healthy) in database_evidence.items() if not healthy]
    results.append(finding("state-integrity", "pass" if sqlite_files and not corrupt_databases else "warn",
        "SQLite state passed an integrity check." if sqlite_files and not corrupt_databases
        else "No healthy SQLite state was proven." if not sqlite_files else "One or more SQLite state files failed integrity checks.",
        corrupt_databases or [str(path) for path in sqlite_files]))
    correction_sources = [path for path, (tables, healthy) in database_evidence.items()
                          if healthy and {"correction_events", "memory_edges"} & tables]
    results.append(finding("correction-path", "pass" if correction_sources else "warn",
        "A structured correction or supersession path exists." if correction_sources
        else "No structured correction path was proven; stale beliefs may survive corrections.", correction_sources))

    candidates = [path for path in json_files if "continuity" in path.name or "resume" in path.name]
    continuity = next((value for path in candidates if (value := read_json(path))), {})
    transport = continuity.get("transportHealthy")
    generated = parse_timestamp(continuity.get("generatedAt"))
    age_hours = (datetime.now(timezone.utc) - generated.astimezone(timezone.utc)).total_seconds() / 3600 if generated else None
    current = age_hours is not None and -0.1 <= age_hours <= 24
    results.append(finding("continuity-verifier", "pass" if transport is True and current else "warn",
        "A current continuity report claims healthy transport; this is reported evidence, not an independent probe."
        if transport is True and current else "No current healthy continuity report was found.",
        [{"path": str(path), "ageHours": round(age_hours, 2) if age_hours is not None else None} for path in candidates]))

    declared_documents = continuity.get("continuity", {}).get("documents", {})
    drift = []
    for name in OBJECTIVE_FILES:
        declared = declared_documents.get(name)
        path = project / name
        if declared and (not path.is_file() or declared.get("sha256") != sha256_file(path)):
            drift.append(name)
    mandate = continuity.get("mandate", {})
    mandate_source = Path(mandate["source"]) if isinstance(mandate.get("source"), str) else None
    if mandate_source and (not mandate_source.is_file() or mandate.get("sha256") != sha256_file(mandate_source)):
        drift.append("mandate.source")
    has_declared_objective = bool(set(OBJECTIVE_FILES) & set(declared_documents)) or bool(mandate)
    results.append(finding("objective-drift", "pass" if has_declared_objective and not drift else "warn",
        "Declared objective evidence matches current file contents." if has_declared_objective and not drift
        else "Objective evidence is missing or differs from current files.", sorted(set(drift))))

    proof = continuity.get("rebootProof", {})
    restarted = proof.get("verifiedAcrossRestart") is True
    results.append(finding("actual-restart-proof", "pass" if restarted else "warn",
        "Recovery was witnessed across distinct boots." if restarted
        else "Restart recovery is not proven by an observation from a different boot.", [proof] if proof else []))

    operations = continuity.get("operations", {})
    operations_present = isinstance(operations, dict) and "humanRequired" in operations
    human_required = operations.get("humanRequired") is True if operations_present else False
    results.append(finding("authority-exceptions", "warn" if human_required or not operations_present else "pass",
        "Human authority is currently required." if human_required else
        "No current human-required exception is reported." if operations_present else "Authority-exception evidence is missing.",
        operations.get("issues", []) if isinstance(operations, dict) else []))

    finance = continuity.get("finance", {})
    contribution = finance.get("ownerAvailableContributionUsd")
    floor = finance.get("freedomFloorMonthlyUsd")
    floor_proven = (finance.get("freedomFloorProven") is True
                    and finance.get("settledPayoutsObserved") is True
                    and finance.get("rolling30DayMature") is True
                    and isinstance(contribution, (int, float)) and isinstance(floor, (int, float))
                    and contribution >= floor)
    results.append(finding("commercial-outcome", "pass" if floor_proven else "warn",
        "The declared commercial floor is supported by mature settled-payout fields." if floor_proven
        else "Commercial completion is unproven; operational health must not be presented as income.",
        [finance] if finance else []))

    units = continuity.get("continuity", {}).get("units", {})
    unhealthy = [name for name, state in units.items() if not state.get("active") or not state.get("enabled")]
    results.append(finding("scheduler-health", "pass" if units and not unhealthy and current else "warn",
        "A current report says required scheduled units are active and enabled; this is not an independent scheduler probe." if units and not unhealthy and current
        else "Scheduler presence and health are not fully proven.", unhealthy or list(units)))

    severity = {"pass": 0, "warn": 1, "fail": 2}
    overall = max(results, key=lambda item: severity[item["status"]])["status"]
    inventory = hashlib.sha256()
    for path in sqlite_files + json_files:
        inventory.update(str(path.relative_to(state_dir)).encode())
        inventory.update(b"\0")
        try:
            inventory.update(sha256_file(path).encode())
        except OSError:
            inventory.update(b"unreadable")
        inventory.update(b"\n")
    return {"schemaVersion": 2, "overall": overall, "project": str(project), "stateDir": str(state_dir),
        "sourceInventoryHash": inventory.hexdigest(), "findings": results,
        "claimBoundary": "This checks durable evidence surfaces; it does not prove quality, safety, demand, or revenue by absence of findings."}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = audit(args.project, args.state_dir or args.project / ".agent-state")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Agency continuity audit: {result['overall']}")
        for item in result["findings"]:
            print(f"[{item['status'].upper()}] {item['id']}: {item['summary']}")
    return 1 if result["overall"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
