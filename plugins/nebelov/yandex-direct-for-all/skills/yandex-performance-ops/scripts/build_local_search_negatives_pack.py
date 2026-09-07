#!/usr/bin/env python3
"""Сформировать только трассируемые кандидаты без смыслового вердикта."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import tempfile
from pathlib import Path

DECISION_FIELDS = [
    "source",
    "evidence",
    "scope",
    "reviewer",
    "reviewed_at",
    "expires_at",
    "decision",
    "reversal_ref",
    "source_row_sha256",
    "candidate_status",
]


def candidate_rows(rows: list[dict[str, str]], source: str, scope: str) -> list[dict[str, str]]:
    output = []
    for row in rows:
        evidence = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        marked = dict(row)
        marked.update(
            {
                "source": source,
                "evidence": evidence,
                "scope": scope,
                "reviewer": "",
                "reviewed_at": "",
                "expires_at": "",
                "decision": "",
                "reversal_ref": "",
                "source_row_sha256": hashlib.sha256(evidence.encode("utf-8")).hexdigest(),
                "candidate_status": "pending_review",
            }
        )
        output.append(marked)
    return output


def write_tsv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
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
    parser = argparse.ArgumentParser(description="Добавить ручной контур решений без сокращения входа")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--source", required=True, help="Название исходного набора")
    parser.add_argument("--scope", required=True, help="Понятная область ручной проверки")
    args = parser.parse_args()
    with Path(args.input).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    if any(field in fields for field in DECISION_FIELDS):
        raise SystemExit("Вход уже содержит поля ручного решения")
    output = candidate_rows(rows, args.source, args.scope)
    if len(output) != len(rows):
        raise SystemExit("Число строк изменилось; результат не записан")
    write_tsv(Path(args.output), fields + DECISION_FIELDS, output)
    print(f"Кандидатов на ручную проверку: {len(output)}; автоматических решений: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
