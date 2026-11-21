#!/usr/bin/env python3
"""Оркестратор читающего снимка кабинета с отдельными манифестами источников."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

from check_access_paths import atomic_write_json, sanitize_error
from collect_direct_management_snapshot import _ids, collect as collect_management
from fetch_sqr_parallel import collect as collect_sqr


def collect(
    access_file: str | None,
    output_dir: Path,
    campaign_ids: list[int],
    date_from: str,
    date_to: str,
    include_sqr: bool,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(output_dir, 0o700)
    sources: dict[str, Any] = {}

    management = collect_management(access_file, output_dir / "management", campaign_ids)
    sources["management"] = {
        "required": True,
        "complete": bool(management.get("complete")),
        "manifest": "management/manifest.json",
    }

    selected = campaign_ids
    if not selected:
        campaigns_file = output_dir / "management" / "campaigns.json"
        if campaigns_file.exists():
            import json

            selected = [int(row["Id"]) for row in json.loads(campaigns_file.read_text(encoding="utf-8")) if row.get("Id")]

    if include_sqr:
        if not date_from or not date_to:
            sources["search_queries"] = {"required": True, "complete": False, "error": "Для отчёта нужны обе даты"}
        elif not selected:
            sources["search_queries"] = {"required": True, "complete": False, "error": "Нет кампаний для отчёта"}
        else:
            sqr = collect_sqr(access_file, selected, date_from, date_to, output_dir / "search_queries", workers=2)
            sources["search_queries"] = {
                "required": True,
                "complete": bool(sqr.get("complete")),
                "manifest": "search_queries/manifest.json",
            }

    required = [item for item in sources.values() if item.get("required")]
    overall = {"complete": bool(required) and all(item.get("complete") for item in required), "sources": sources}
    atomic_write_json(output_dir / "manifest.json", overall)
    return overall


def main() -> int:
    parser = argparse.ArgumentParser(description="Собрать проверяемый снимок кабинета Яндекс.Директа")
    parser.add_argument("--access-file", help="Защищённый JSON-файл доступа")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--campaign-ids", default="")
    parser.add_argument("--from", dest="date_from", default="")
    parser.add_argument("--to", dest="date_to", default="")
    parser.add_argument("--include-sqr", action="store_true")
    args = parser.parse_args()
    if any(item in {"--token", "--direct-token"} for item in sys.argv[1:]):
        parser.error("сырой токен в командной строке запрещён")
    try:
        result = collect(args.access_file, Path(args.output_dir), _ids(args.campaign_ids), args.date_from, args.date_to, args.include_sqr)
    except Exception as exc:
        print(f"Снимок не собран: {sanitize_error(exc)}", file=sys.stderr)
        return 1
    print("Снимок кабинета полный" if result["complete"] else "Снимок кабинета неполный")
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
