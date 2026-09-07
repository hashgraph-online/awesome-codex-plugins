#!/usr/bin/env python3
"""Extract high-confidence human messages from caller-supplied Codex JSONL."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REQUEST_MARKER = "# My request for Codex:"

# These are deliberately narrow. The client_id check below is the primary
# machine-injection boundary; these patterns catch known generated envelopes
# even if a future producer happens to attach a client id.
MACHINE_ECHO_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "internal_context",
        re.compile(
            r"^\s*<(?:codex_internal_context|environment_context|permissions|"
            r"skills_instructions|apps_instructions|plugins_instructions)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "fresh_context_refuter",
        re.compile(
            r"^\s*You are (?:a|the) fresh-context, cross-family reviewer\b",
            re.IGNORECASE,
        ),
    ),
    (
        "agent_message_envelope",
        re.compile(
            r"^\s*Message Type:\s*(?:NEW_TASK|MESSAGE|FINAL_ANSWER)\b",
            re.IGNORECASE,
        ),
    ),
)


@dataclass(frozen=True)
class Candidate:
    source_path: str
    line: int
    timestamp: datetime
    timestamp_text: str
    text: str
    client_id: str


def parse_instant(value: str, label: str) -> datetime:
    candidate = value.strip()
    if candidate.endswith(("Z", "z")):
        candidate = f"{candidate[:-1]}+00:00"
    try:
        instant = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{label} is not ISO-8601: {value!r}") from exc
    if instant.tzinfo is None:
        raise argparse.ArgumentTypeError(f"{label} must include a timezone: {value!r}")
    return instant.astimezone(timezone.utc)


def canonical_instant(instant: datetime) -> str:
    return (
        instant.astimezone(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def normalize_request(message: str) -> str:
    """Remove Codex attachment/IDE headers while retaining the explicit request."""
    normalized = message.replace("\r\n", "\n").replace("\r", "\n")
    if REQUEST_MARKER in normalized:
        normalized = normalized.split(REQUEST_MARKER, 1)[1]
    lines = [line.rstrip() for line in normalized.strip().split("\n")]
    return "\n".join(lines).strip()


def machine_echo_reason(text: str) -> str | None:
    for name, pattern in MACHINE_ECHO_PATTERNS:
        if pattern.search(text):
            return name
    return None


def is_user_message(record: Any) -> bool:
    return (
        isinstance(record, dict)
        and record.get("type") == "event_msg"
        and isinstance(record.get("payload"), dict)
        and record["payload"].get("type") == "user_message"
    )


def iter_records(path: Path) -> Iterable[tuple[int, bytes]]:
    with path.open("rb") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            yield line_number, raw_line


def extract(paths: list[Path], since: datetime, until: datetime) -> dict[str, Any]:
    exclusions: dict[str, Any] = {
        "invalid_json": 0,
        "non_user_message": 0,
        "invalid_timestamp": 0,
        "outside_window": 0,
        "missing_client_id": 0,
        "machine_echo": 0,
        "machine_echo_by_pattern": {name: 0 for name, _ in MACHINE_ECHO_PATTERNS},
        "empty_after_normalization": 0,
        "duplicate_client_id": 0,
        "duplicate_client_id_text_conflict": 0,
    }
    input_lines = 0
    parsed_records = 0
    candidate_user_messages = 0
    candidates: list[Candidate] = []

    for path in paths:
        for line_number, raw_line in iter_records(path):
            input_lines += 1
            try:
                record = json.loads(raw_line.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                exclusions["invalid_json"] += 1
                continue
            parsed_records += 1
            if not is_user_message(record):
                exclusions["non_user_message"] += 1
                continue

            candidate_user_messages += 1
            timestamp_value = record.get("timestamp")
            if not isinstance(timestamp_value, str):
                exclusions["invalid_timestamp"] += 1
                continue
            try:
                timestamp = parse_instant(timestamp_value, "record timestamp")
            except argparse.ArgumentTypeError:
                exclusions["invalid_timestamp"] += 1
                continue
            if not since <= timestamp < until:
                exclusions["outside_window"] += 1
                continue

            payload = record["payload"]
            message = payload.get("message")
            if not isinstance(message, str):
                exclusions["empty_after_normalization"] += 1
                continue
            text = normalize_request(message)
            if not text:
                exclusions["empty_after_normalization"] += 1
                continue
            echo_reason = machine_echo_reason(text)
            if echo_reason is not None:
                exclusions["machine_echo"] += 1
                exclusions["machine_echo_by_pattern"][echo_reason] += 1
                continue

            client_id = payload.get("client_id")
            if not isinstance(client_id, str) or not client_id.strip():
                exclusions["missing_client_id"] += 1
                continue

            candidates.append(
                Candidate(
                    source_path=str(path),
                    line=line_number,
                    timestamp=timestamp,
                    timestamp_text=canonical_instant(timestamp),
                    text=text,
                    client_id=client_id.strip(),
                )
            )

    # Sorting before selection makes output independent of caller path order and
    # chooses the earliest source occurrence when restored/forked sessions repeat
    # the same UI client event.
    candidates.sort(
        key=lambda item: (item.timestamp, item.source_path, item.line, item.client_id)
    )
    retained: list[Candidate] = []
    by_client_id: dict[str, Candidate] = {}
    for candidate in candidates:
        previous = by_client_id.get(candidate.client_id)
        if previous is not None:
            exclusions["duplicate_client_id"] += 1
            if previous.text != candidate.text:
                exclusions["duplicate_client_id_text_conflict"] += 1
            continue
        by_client_id[candidate.client_id] = candidate
        retained.append(candidate)

    return {
        "schema_version": 1,
        "window": {
            "since_inclusive": canonical_instant(since),
            "until_exclusive": canonical_instant(until),
        },
        "inputs": [str(path) for path in paths],
        "counts": {
            "input_files": len(paths),
            "input_lines": input_lines,
            "parsed_records": parsed_records,
            "candidate_user_messages": candidate_user_messages,
            "emitted_messages": len(retained),
            "excluded": exclusions,
        },
        "messages": [
            {
                "source_path": item.source_path,
                "line": item.line,
                "timestamp": item.timestamp_text,
                "text": item.text,
            }
            for item in retained
        ],
        "checked": [
            "Only the explicitly supplied JSONL paths were read.",
            "The time window was applied since-inclusive and until-exclusive in UTC.",
            "Only event_msg/user_message records with a nonempty client_id were retained.",
            "Codex attachment wrappers were reduced to the text after '# My request for Codex:'.",
            "Known generated envelopes were excluded and restored/forked copies were deduplicated by client_id.",
        ],
        "not_checked": [
            "Attachment file contents and any session paths not explicitly supplied were not read.",
            "A client_id is strong UI-origin evidence, not proof of a particular human author.",
            "Messages without client_id were not classified as human, including any directly typed by a client that omits that field.",
            "No semantic clustering, pain scoring, recommendation, tracker mutation, or automation scheduling was performed.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Extract high-confidence recent human messages from caller-supplied "
            "Codex JSONL sessions. Writes one JSON report to stdout."
        )
    )
    parser.add_argument("--since", required=True, help="inclusive ISO-8601 timestamp")
    parser.add_argument("--until", required=True, help="exclusive ISO-8601 timestamp")
    parser.add_argument(
        "sessions", nargs="+", help="explicit Codex JSONL session paths"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        since = parse_instant(args.since, "--since")
        until = parse_instant(args.until, "--until")
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))
    if since >= until:
        parser.error("--since must be earlier than --until")

    unique_paths: dict[str, Path] = {}
    for supplied in args.sessions:
        path = Path(supplied).expanduser().resolve()
        if not path.is_file():
            parser.error(f"session path is not a file: {supplied}")
        unique_paths[str(path)] = path
    paths = [unique_paths[key] for key in sorted(unique_paths)]

    json.dump(extract(paths, since, until), sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
