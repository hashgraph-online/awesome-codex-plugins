#!/usr/bin/env python3
"""Пометить совпадения, не удаляя и не утверждая ни одной входной строки."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

ADDED_FIELDS = [
    "source_row_sha256",
    "matched_minus_words",
    "matched_decision_sha256",
    "candidate_status",
    "manual_decision",
]


def normalize(value: str) -> str:
    return " ".join(re.findall(r"[0-9a-zа-яё]+", (value or "").casefold()))


def load_decisions(path: Path) -> list[dict[str, str]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("Файл известных решений должен содержать список")
    decisions = []
    for item in value:
        word = str((item or {}).get("minus_word") or "").strip()
        digest = str((item or {}).get("decision_sha256") or "").strip()
        if not word or not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ValueError("Каждое известное решение должно иметь minus_word и decision_sha256")
        decisions.append({"minus_word": word, "normalized": normalize(word), "decision_sha256": digest})
    return decisions


def mark_rows(rows: list[dict[str, str]], text_field: str, decisions: list[dict[str, str]]) -> list[dict[str, str]]:
    output = []
    for row in rows:
        source = {key: value for key, value in row.items()}
        source_hash = hashlib.sha256(
            json.dumps(source, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        text = f" {normalize(row.get(text_field, ''))} "
        matched = [item for item in decisions if item["normalized"] and f" {item['normalized']} " in text]
        marked = dict(source)
        marked.update(
            {
                "source_row_sha256": source_hash,
                "matched_minus_words": json.dumps([item["minus_word"] for item in matched], ensure_ascii=False),
                "matched_decision_sha256": json.dumps([item["decision_sha256"] for item in matched], ensure_ascii=False),
                "candidate_status": "pending_review",
                "manual_decision": "",
            }
        )
        output.append(marked)
    return output


def atomic_tsv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", extrasaction="raise")
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> int:
    parser = argparse.ArgumentParser(description="Пометить очередь без автоматического сокращения")
    parser.add_argument("--input", required=True)
    parser.add_argument("--known-decisions", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--text-field", default="query")
    args = parser.parse_args()

    with Path(args.input).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    if args.text_field not in fields:
        raise SystemExit(f"Во входе нет поля {args.text_field}")
    if any(field in fields for field in ADDED_FIELDS):
        raise SystemExit("Вход уже содержит служебные поля пометки")
    marked = mark_rows(rows, args.text_field, load_decisions(Path(args.known_decisions)))
    if len(marked) != len(rows):
        raise SystemExit("Число строк изменилось; запись отменена")
    atomic_tsv(Path(args.output), fields + ADDED_FIELDS, marked)
    print(f"Сохранено строк без сокращения: {len(marked)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
