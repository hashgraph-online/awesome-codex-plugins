#!/usr/bin/env python3
"""Проверить полноту досье сборки до создания пакета записи."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any


def require_nonempty(path: Path, label: str, errors: list[str]) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        errors.append(f"Отсутствует или пуст раздел: {label}")


def validate_architecture(path: Path, errors: list[str]) -> dict[str, int]:
    if not path.is_file():
        errors.append("Отсутствует архитектура кампаний, групп и объявлений")
        return {"campaigns": 0, "groups": 0, "ads": 0}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        errors.append("Архитектура должна быть корректным JSON")
        return {"campaigns": 0, "groups": 0, "ads": 0}
    campaigns = value.get("campaigns") if isinstance(value, dict) else None
    if not isinstance(campaigns, list) or not campaigns:
        errors.append("Архитектура не содержит кампаний")
        return {"campaigns": 0, "groups": 0, "ads": 0}
    group_uids: set[str] = set()
    group_count = 0
    ad_count = 0
    for campaign in campaigns:
        groups = campaign.get("groups") if isinstance(campaign, dict) else None
        if not isinstance(groups, list) or not groups:
            errors.append("Каждая кампания должна содержать группы")
            continue
        for group in groups:
            group_count += 1
            uid = str((group or {}).get("group_uid") or "")
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{7,127}", uid) or uid in group_uids:
                errors.append("group_uid отсутствует, нестабилен или повторяется")
            group_uids.add(uid)
            ads = (group or {}).get("ads")
            if not isinstance(ads, list) or not ads:
                errors.append("Каждая группа должна содержать варианты объявлений")
            else:
                ad_count += len(ads)
    return {"campaigns": len(campaigns), "groups": group_count, "ads": ad_count}


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Проверить досье сборки Яндекс.Директа")
    parser.add_argument("--product-map", required=True)
    parser.add_argument("--protected-words", required=True)
    parser.add_argument("--synonyms", required=True)
    parser.add_argument("--candidate-universe", required=True)
    parser.add_argument("--inclusion-map", required=True)
    parser.add_argument("--exclusion-map", required=True)
    parser.add_argument("--coverage", required=True)
    parser.add_argument("--architecture", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    errors: list[str] = []
    for argument, label in [
        (args.product_map, "карта продукта"),
        (args.protected_words, "защищённые слова"),
        (args.synonyms, "синонимы"),
        (args.candidate_universe, "вселенная кандидатов"),
        (args.inclusion_map, "карта включения"),
        (args.exclusion_map, "карта исключения"),
        (args.coverage, "покрытие"),
    ]:
        require_nonempty(Path(argument), label, errors)
    counts = validate_architecture(Path(args.architecture), errors)
    result = {"status": "ready" if not errors else "rejected", "errors": errors, "counts": counts}
    atomic_json(Path(args.output), result)
    print("Досье готово" if not errors else f"Досье отклонено: {len(errors)} нарушений")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
