#!/usr/bin/env python3
"""Общий читающий сборщик с независимыми манифестами каждого источника."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

from check_access_paths import atomic_write_json, load_metrika_access, metrika_get, sanitize_error
from collect_direct_cabinet_snapshot import _ids, collect as collect_direct


def _checksum(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def collect_metrika(access_file: str | None, counter_id: str, output_dir: Path) -> dict[str, Any]:
    access = load_metrika_access(access_file)
    if counter_id:
        payload = metrika_get(access, f"management/v1/counter/{counter_id}", {"field": "goals,filters,operations"})
    else:
        payload = metrika_get(access, "management/v1/counters", {"per_page": 1000})
    atomic_write_json(output_dir / "data.json", payload)
    count = 1 if counter_id else len(payload.get("counters") or [])
    manifest = {"complete": True, "pages": 1, "objects": count, "checksum": _checksum(payload), "artifact": "data.json"}
    atomic_write_json(output_dir / "manifest.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Собрать данные Директа и Метрики по независимым источникам")
    parser.add_argument("--direct-access-file", help="Защищённый файл доступа Директа")
    parser.add_argument("--metrika-access-file", help="Защищённый файл доступа Метрики")
    parser.add_argument("--campaign-ids", default="")
    parser.add_argument("--metrika-counter", default="")
    parser.add_argument("--from", dest="date_from", default="")
    parser.add_argument("--to", dest="date_to", default="")
    parser.add_argument("--include-sqr", action="store_true")
    parser.add_argument("--include-metrika", action="store_true")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    forbidden = {"--token", "--direct-token", "--roistat-key", "--metrika-token"}
    if any(item in forbidden for item in sys.argv[1:]):
        parser.error("учётные данные в командной строке запрещены")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(output_dir, 0o700)
    sources: dict[str, Any] = {}

    try:
        direct = collect_direct(args.direct_access_file, output_dir / "direct", _ids(args.campaign_ids), args.date_from, args.date_to, args.include_sqr)
        sources["direct"] = {"required": True, "complete": direct["complete"], "manifest": "direct/manifest.json"}
    except Exception as exc:
        sources["direct"] = {"required": True, "complete": False, "error": sanitize_error(exc)}

    if args.include_metrika:
        try:
            metrika = collect_metrika(args.metrika_access_file, args.metrika_counter, output_dir / "metrika")
            sources["metrika"] = {"required": True, "complete": metrika["complete"], "manifest": "metrika/manifest.json"}
        except Exception as exc:
            sources["metrika"] = {"required": True, "complete": False, "error": sanitize_error(exc)}

    overall = {"complete": all(item.get("complete") for item in sources.values()), "sources": sources}
    atomic_write_json(output_dir / "manifest.json", overall)
    print("Сбор завершён полностью" if overall["complete"] else "Сбор завершён частично")
    return 0 if overall["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
