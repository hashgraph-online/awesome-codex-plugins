#!/usr/bin/env python3
"""Проверить проект исследования по переносимому манифесту."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import tempfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse


class VerificationError(RuntimeError):
    pass


def safe_relative(value: str) -> Path:
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts or not pure.parts:
        raise VerificationError(f"Небезопасный путь в манифесте: {value}")
    return Path(*pure.parts)


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), list(reader)


def validate_source_register(path: Path, errors: list[str]) -> bool:
    if not path.is_file():
        return False
    fields, rows = read_tsv(path)
    required = {
        "source_id", "source_type", "source_url", "captured_at", "status", "evidence_path",
        "reviewer", "reviewed_at", "expires_at", "reversal_ref",
    }
    missing = required - set(fields)
    if missing:
        errors.append(f"source-register.tsv: отсутствуют поля {sorted(missing)}")
        return False
    confirmed_ready = True
    for number, row in enumerate(rows, 2):
        status = (row.get("status") or "").strip()
        fact_values = [row.get("source_type"), row.get("source_url"), row.get("captured_at"), row.get("evidence_path"), row.get("reviewer"), row.get("reviewed_at")]
        if status == "confirmed" and not all((value or "").strip() for value in fact_values):
            errors.append(f"source-register.tsv:{number}: confirmed без источника, времени, доказательства или проверяющего")
        if status != "confirmed":
            confirmed_ready = False
    return confirmed_ready and bool(rows)


def _specific_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_routing(path: Path, errors: list[str]) -> bool:
    if not path.is_file():
        return False
    fields, rows = read_tsv(path)
    required = {"intent", "domain", "serp_page_url", "site_page_url", "campaign_name", "adgroup_name", "status"}
    missing = required - set(fields)
    if missing:
        errors.append(f"routing-map.tsv: отсутствуют поля {sorted(missing)}")
        return False
    ready = True
    for number, row in enumerate(rows, 2):
        domain = (row.get("domain") or "").strip()
        if domain and ("://" in domain or "/" in domain or not re.fullmatch(r"[A-Za-z0-9.-]+", domain)):
            errors.append(f"routing-map.tsv:{number}: поле domain смешано с адресом страницы")
        for field in ("serp_page_url", "site_page_url"):
            value = (row.get(field) or "").strip()
            if value and not _specific_url(value):
                errors.append(f"routing-map.tsv:{number}: {field} должен содержать полный адрес конкретной страницы")
        status = (row.get("status") or "").strip()
        meaningful = any((row.get(field) or "").strip() for field in ("intent", "serp_page_url", "site_page_url", "campaign_name", "adgroup_name"))
        if not meaningful and status != "unverified":
            errors.append(f"routing-map.tsv:{number}: пустой маршрут должен иметь status=unverified")
        if status != "confirmed":
            ready = False
    return ready and bool(rows)


def validate_facts(path: Path, source_path: Path, errors: list[str]) -> bool:
    if not path.is_file() or not source_path.is_file():
        return False
    fields, rows = read_tsv(path)
    required = {"fact_id", "fact", "source_id", "status", "evidence_path", "reviewer", "reviewed_at", "expires_at"}
    missing = required - set(fields)
    if missing:
        errors.append(f"fact-check-log.tsv: отсутствуют поля {sorted(missing)}")
        return False
    _, sources = read_tsv(source_path)
    confirmed_sources = {(row.get("source_id") or "").strip() for row in sources if (row.get("status") or "").strip() == "confirmed"}
    ready = True
    for number, row in enumerate(rows, 2):
        status = (row.get("status") or "").strip()
        if status == "confirmed":
            values = [row.get("fact"), row.get("source_id"), row.get("evidence_path"), row.get("reviewer"), row.get("reviewed_at")]
            if not all((value or "").strip() for value in values):
                errors.append(f"fact-check-log.tsv:{number}: confirmed без источника, времени, доказательства или проверяющего")
            elif (row.get("source_id") or "").strip() not in confirmed_sources:
                errors.append(f"fact-check-log.tsv:{number}: confirmed ссылается на неподтверждённый источник")
        else:
            ready = False
    return ready and bool(rows)


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def verify(root: Path, manifest_path: Path) -> dict[str, object]:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VerificationError("Манифест отсутствует или повреждён") from exc
    if manifest.get("schema_version") != "1.0" or not isinstance(manifest.get("artifacts"), list):
        raise VerificationError("Манифест имеет неподдерживаемую схему")
    errors: list[str] = []
    checks: list[dict[str, object]] = []
    for item in manifest["artifacts"]:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            errors.append("Манифест содержит неверное описание артефакта")
            continue
        relative = safe_relative(item["path"])
        path = root / relative
        kind = item.get("kind", "file")
        exists = path.is_file() if kind == "file" else path.is_dir()
        if item.get("required", True) and not exists:
            errors.append(f"Отсутствует обязательный артефакт: {relative.as_posix()}")
        checks.append({"path": relative.as_posix(), "kind": kind, "exists": exists})
    for relative, required_fields in (manifest.get("tsv_contracts") or {}).items():
        path = root / safe_relative(relative)
        if not path.is_file():
            continue
        fields, _ = read_tsv(path)
        missing = set(required_fields) - set(fields)
        if missing:
            errors.append(f"{relative}: отсутствуют поля {sorted(missing)}")
    sources_ready = validate_source_register(root / "source-register.tsv", errors)
    routes_ready = validate_routing(root / "routing-map.tsv", errors)
    facts_ready = validate_facts(root / "fact-check-log.tsv", root / "source-register.tsv", errors)
    return {
        "status": "ready" if not errors else "rejected",
        "structure_complete": not any(error.startswith("Отсутствует обязательный") for error in errors),
        "confirmed_sources_ready": sources_ready,
        "confirmed_routes_ready": routes_ready,
        "confirmed_facts_ready": facts_ready,
        "checks": checks,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--manifest")
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()
    root = Path(args.project_dir).expanduser().resolve()
    manifest_path = Path(args.manifest).expanduser().resolve() if args.manifest else root / "research-manifest.json"
    try:
        result = verify(root, manifest_path)
    except VerificationError as exc:
        result = {"status": "rejected", "structure_complete": False, "confirmed_sources_ready": False, "confirmed_routes_ready": False, "confirmed_facts_ready": False, "checks": [], "errors": [str(exc)]}
    atomic_json(Path(args.output_json).expanduser().resolve(), result)
    print(json.dumps({key: result[key] for key in ("status", "structure_complete", "confirmed_sources_ready", "confirmed_routes_ready", "confirmed_facts_ready")}, ensure_ascii=False))
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
