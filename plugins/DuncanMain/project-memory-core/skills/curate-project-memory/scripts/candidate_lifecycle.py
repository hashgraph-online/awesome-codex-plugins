#!/usr/bin/env python3
"""Inspect or safely transition one Project Memory promotion candidate."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


HEADING = re.compile(r"^###\s+(PM-\S+)\s+(?:—|-|â€”)\s+(.+)$", re.MULTILINE)
FIELDS = ("Operation", "Target", "Confidence", "Evidence", "Proposed change", "Conflicts", "Existing claim", "Existing evidence", "Conflict resolution")
ALLOWED = {
    "pending": {"approved", "rejected", "deferred"},
    "deferred": {"approved", "rejected", "deferred"},
    "approved": {"approved", "applying", "deferred", "rejected"},
    "applying": {"applied", "conflict", "failed"},
    "conflict": {"approved", "rejected", "deferred"},
    "failed": {"approved", "rejected", "deferred"},
    "applied": set(),
    "rejected": set(),
}


def field(block: str, name: str) -> str:
    match = re.search(rf"^- {re.escape(name)}:[ \t]*(.*)$", block, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else ""


def fingerprint(block: str) -> str:
    value = "\n".join(field(block, name).strip().replace("\r\n", "\n") for name in FIELDS)
    hash_value = 0x811C9DC5
    encoded = value.encode("utf-16-le", errors="surrogatepass")
    for index in range(0, len(encoded), 2):
        hash_value ^= int.from_bytes(encoded[index:index + 2], "little")
        hash_value = (hash_value * 0x01000193) & 0xFFFFFFFF
    return f"fnv1a32:{hash_value:08x}"


def candidate(text: str, candidate_id: str) -> tuple[int, int, str] | None:
    headings = list(HEADING.finditer(text))
    for index, match in enumerate(headings):
        if match.group(1) != candidate_id:
            continue
        start = match.start()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        return start, end, text[start:end]
    return None


def set_field(block: str, name: str, value: str) -> str:
    pattern = re.compile(rf"^(- {re.escape(name)}:)[ \t]*.*$", re.IGNORECASE | re.MULTILINE)
    if pattern.search(block):
        return pattern.sub(lambda match: f"{match.group(1)} {value}", block, count=1)
    return re.sub(r"^- Status:[ \t]*.*$", lambda match: f"{match.group(0)}\n- {name}: {value}", block, count=1, flags=re.IGNORECASE | re.MULTILINE)


def transition(text: str, candidate_id: str, status: str, *, actor: str = "", at: str = "", target: str = "", revision: str = "", error: str = "") -> str:
    found = candidate(text, candidate_id)
    if found is None:
        raise ValueError(f"candidate not found: {candidate_id}")
    start, end, block = found
    current = field(block, "Status").casefold() or "pending"
    if status not in ALLOWED.get(current, set()):
        raise ValueError(f"invalid candidate transition: {current} -> {status}")
    if status == "applying" and field(block, "Approval fingerprint") != fingerprint(block):
        raise ValueError("approval fingerprint does not match the current proposal")
    block = set_field(block, "Status", status)
    if status == "approved":
        block = set_field(block, "Approved at", at)
        block = set_field(block, "Approved by", actor)
        block = set_field(block, "Approval fingerprint", fingerprint(block))
        block = set_field(block, "Application error", "")
    elif status == "applying":
        block = set_field(block, "Application target", target)
    elif status == "applied":
        block = set_field(block, "Applied at", at)
        block = set_field(block, "Applied by", actor)
        block = set_field(block, "Application target", target or field(block, "Application target"))
        block = set_field(block, "Application revision", revision)
    elif status in {"conflict", "failed"}:
        block = set_field(block, "Application error", error or "No application outcome was recorded.")
    return text[:start] + block + text[end:]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inbox", type=Path)
    parser.add_argument("candidate_id")
    parser.add_argument("--status", choices=sorted(ALLOWED))
    parser.add_argument("--actor", default="")
    parser.add_argument("--at", default="")
    parser.add_argument("--target", default="")
    parser.add_argument("--revision", default="")
    parser.add_argument("--error", default="")
    args = parser.parse_args()
    text = args.inbox.read_text(encoding="utf-8")
    found = candidate(text, args.candidate_id)
    if found is None:
        parser.error(f"candidate not found: {args.candidate_id}")
    if args.status:
        if not args.at and args.status in {"approved", "applied"}:
            parser.error("--at is required for approved and applied transitions")
        text = transition(text, args.candidate_id, args.status, actor=args.actor, at=args.at, target=args.target, revision=args.revision, error=args.error)
        args.inbox.write_text(text, encoding="utf-8")
        found = candidate(text, args.candidate_id)
    assert found is not None
    block = found[2]
    print(json.dumps({"id": args.candidate_id, "status": field(block, "Status"), "fingerprint": fingerprint(block), "approval_fingerprint": field(block, "Approval fingerprint")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
