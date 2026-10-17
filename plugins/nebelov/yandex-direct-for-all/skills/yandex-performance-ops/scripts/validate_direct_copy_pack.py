#!/usr/bin/env python3
"""Validate Yandex Direct text assets from a TSV pack.

This script only checks lengths and produces a renderable report.
It does not make marketing decisions.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Dict, List


FIELD_LIMITS = {
    "title_1": 56,
    "title_2": 30,
    "description": 81,
    "display_link": 20,
    "sitelink_text": 30,
    "sitelink_desc": 60,
    "callout": 25,
}

MAX_WORD = {
    "title_1": 22,
    "title_2": 22,
    "description": 23,
}

MAX_SITELINKS = 8
MAX_SITELINKS_WITH_DESCS = 4
MAX_CALLOUT_TOTAL = 132


def norm(value: str) -> str:
    return " ".join((value or "").strip().split())


def longest_word_length(text: str) -> int:
    words = [word.strip(".,:;!?\"'«»()[]{}") for word in norm(text).split()]
    return max((len(word) for word in words if word), default=0)


def split_callouts(text: str) -> List[str]:
    return [norm(item) for item in (text or "").split("|") if norm(item)]


def validate_display_link(value: str) -> List[str]:
    value = norm(value).lower()
    errors: List[str] = []
    if not value:
        return ["display_link: empty"]
    if re.search(r"[a-zA-Z]", value):
        errors.append("display_link: must be Russian, not Latin")
    if not re.search(r"[а-яё]", value):
        errors.append("display_link: must contain Russian text")
    if re.search(r"[^а-яё0-9/%#-]", value):
        errors.append("display_link: unsupported characters")
    if value.endswith(("-", "/")):
        errors.append("display_link: looks truncated")
    return errors


def validate_row(row: Dict[str, str]) -> Dict[str, object]:
    violations: List[str] = []
    lengths: Dict[str, int] = {}

    for field in ("title_1", "title_2", "description", "display_link"):
        value = norm(row.get(field, ""))
        lengths[field] = len(value)
        if len(value) > FIELD_LIMITS[field]:
            violations.append(f"{field}: {len(value)} > {FIELD_LIMITS[field]}")
        if field == "display_link":
            violations.extend(validate_display_link(value))
        if field in MAX_WORD:
            longest = longest_word_length(value)
            lengths[f"{field}_max_word"] = longest
            if longest > MAX_WORD[field]:
                violations.append(
                    f"{field}_max_word: {longest} > {MAX_WORD[field]}"
                )

    sitelink_text_lengths: List[int] = []
    sitelink_desc_lengths: List[int] = []
    used_sitelinks = 0
    described_sitelinks = 0
    for idx in range(1, 5):
        text_key = f"sitelink_{idx}_text"
        url_key = f"sitelink_{idx}_url"
        desc_key = f"sitelink_{idx}_desc"
        text = norm(row.get(text_key, ""))
        url = norm(row.get(url_key, ""))
        desc = norm(row.get(desc_key, ""))
        if text or url or desc:
            used_sitelinks += 1
        if text:
            sitelink_text_lengths.append(len(text))
            if len(text) > FIELD_LIMITS["sitelink_text"]:
                violations.append(
                    f"{text_key}: {len(text)} > {FIELD_LIMITS['sitelink_text']}"
                )
        if desc:
            described_sitelinks += 1
            sitelink_desc_lengths.append(len(desc))
            if len(desc) > FIELD_LIMITS["sitelink_desc"]:
                violations.append(
                    f"{desc_key}: {len(desc)} > {FIELD_LIMITS['sitelink_desc']}"
                )

    if used_sitelinks > MAX_SITELINKS:
        violations.append(f"sitelinks_used: {used_sitelinks} > {MAX_SITELINKS}")
    if described_sitelinks > MAX_SITELINKS_WITH_DESCS:
        violations.append(
            f"sitelinks_with_descs: {described_sitelinks} > {MAX_SITELINKS_WITH_DESCS}"
        )

    callouts = split_callouts(row.get("callouts", ""))
    callout_lengths = [len(item) for item in callouts]
    callout_total = sum(callout_lengths)
    if callout_total > MAX_CALLOUT_TOTAL:
        violations.append(f"callouts_total: {callout_total} > {MAX_CALLOUT_TOTAL}")
    for idx, item in enumerate(callouts, start=1):
        if len(item) > FIELD_LIMITS["callout"]:
            violations.append(
                f"callout_{idx}: {len(item)} > {FIELD_LIMITS['callout']}"
            )

    lengths["sitelinks_used"] = used_sitelinks
    lengths["sitelinks_with_descs"] = described_sitelinks
    lengths["callouts_count"] = len(callouts)
    lengths["callouts_total"] = callout_total

    return {
        "cluster": norm(row.get("cluster", "")),
        "variant": norm(row.get("variant", "")),
        "violations": violations,
        "lengths": lengths,
    }


def write_tsv(path: Path, rows: List[Dict[str, object]]) -> None:
    fieldnames = [
        "cluster",
        "variant",
        "status",
        "title_1_len",
        "title_1_max_word",
        "title_2_len",
        "title_2_max_word",
        "description_len",
        "description_max_word",
        "display_link_len",
        "sitelinks_used",
        "sitelinks_with_descs",
        "callouts_count",
        "callouts_total",
        "violations",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            lengths = row["lengths"]
            writer.writerow(
                {
                    "cluster": row["cluster"],
                    "variant": row["variant"],
                    "status": "ok" if not row["violations"] else "violation",
                    "title_1_len": lengths.get("title_1", 0),
                    "title_1_max_word": lengths.get("title_1_max_word", 0),
                    "title_2_len": lengths.get("title_2", 0),
                    "title_2_max_word": lengths.get("title_2_max_word", 0),
                    "description_len": lengths.get("description", 0),
                    "description_max_word": lengths.get("description_max_word", 0),
                    "display_link_len": lengths.get("display_link", 0),
                    "sitelinks_used": lengths.get("sitelinks_used", 0),
                    "sitelinks_with_descs": lengths.get("sitelinks_with_descs", 0),
                    "callouts_count": lengths.get("callouts_count", 0),
                    "callouts_total": lengths.get("callouts_total", 0),
                    "violations": " | ".join(row["violations"]),
                }
            )


def write_markdown(path: Path, rows: List[Dict[str, object]], source_name: str) -> None:
    ok_count = sum(1 for row in rows if not row["violations"])
    total = len(rows)
    lines = [
        "# Проверка текстов Яндекс Директа",
        "",
        f"Источник: `{source_name}`",
        "",
        f"Проверено строк: `{total}`",
        f"Без нарушений: `{ok_count}`",
        f"С нарушениями: `{total - ok_count}`",
        "",
        "## Правила проверки",
        "",
        "1. Заголовок 1: до 56 знаков.",
        "2. Заголовок 2: до 30 знаков.",
        "3. Описание: до 81 знака.",
        "4. Отображаемая ссылка: до 20 знаков.",
        "   Только русский текст, цифры и знаки `-`, `/`, `%`, `#`; без латиницы и обрезанного хвоста.",
        "5. Текст быстрой ссылки: до 30 знаков.",
        "6. Описание быстрой ссылки: до 60 знаков.",
        "7. Уточнение: до 25 знаков.",
        "8. Сумма уточнений: до 132 знаков.",
        "",
        "## Результат по строкам",
        "",
        "| Кластер | Вариант | Статус | Нарушения |",
        "|---|---|---|---|",
    ]
    for row in rows:
        status = "ok" if not row["violations"] else "violation"
        violations = "; ".join(row["violations"]) or "-"
        lines.append(f"| {row['cluster']} | {row['variant']} | {status} | {violations} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-tsv", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    input_path = Path(args.input_tsv)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, object]] = []
    with input_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for raw_row in reader:
            rows.append(validate_row(raw_row))

    json_path = output_dir / "_summary.json"
    tsv_path = output_dir / "validation.tsv"
    md_path = output_dir / "validation.md"

    summary = {
        "source": str(input_path),
        "rows": len(rows),
        "ok_rows": sum(1 for row in rows if not row["violations"]),
        "violation_rows": sum(1 for row in rows if row["violations"]),
        "limits": {
            **FIELD_LIMITS,
            **{
                "title_1_max_word": MAX_WORD["title_1"],
                "title_2_max_word": MAX_WORD["title_2"],
                "description_max_word": MAX_WORD["description"],
                "max_sitelinks": MAX_SITELINKS,
                "max_sitelinks_with_descs": MAX_SITELINKS_WITH_DESCS,
                "max_callouts_total": MAX_CALLOUT_TOTAL,
            },
        },
    }

    json_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_tsv(tsv_path, rows)
    write_markdown(md_path, rows, input_path.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
