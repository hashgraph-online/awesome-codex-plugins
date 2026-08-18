#!/usr/bin/env python3
"""Сохранить схему amoCRM чтением и предоставить сверку заявок."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

for candidate in (
    Path(__file__).resolve().parents[3] / "scripts",
    Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "plugins/yandex-direct-for-all/scripts",
    Path(os.environ.get("CLAUDE_HOME", Path.home() / ".claude")) / "plugins/yandex-direct-for-all/scripts",
):
    if (candidate / "portable_http.py").is_file():
        sys.path.insert(0, str(candidate))
        break
else:
    raise RuntimeError("Не найден переносимый HTTP-слой yandex-direct-for-all")

import portable_http as requests  # noqa: E402


RECONCILIATION_FIELDS = ("source", "occurred_at", "status", "responsible", "external_link")


def private_credentials(path: Path) -> dict[str, Any]:
    if not path.is_file() or stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise RuntimeError("Файл доступа amoCRM должен иметь права 0600")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not value.get("base_url") or not value.get("access_token"):
        raise RuntimeError("Файл доступа amoCRM неполный")
    return value


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


def fetch_paginated(getter: Callable[[str], dict[str, Any]], first_url: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    next_url = first_url
    seen: set[str] = set()
    complete = False
    while next_url:
        if next_url in seen:
            raise RuntimeError("amoCRM вернула повторную страницу")
        seen.add(next_url)
        value = getter(next_url)
        if not isinstance(value, dict):
            raise RuntimeError("Страница amoCRM имеет неверную схему")
        pages.append(value)
        link = ((value.get("_links") or {}).get("next") or {}).get("href")
        if not link:
            complete = True
            break
        next_url = str(link)
    return pages, {"pages": len(pages), "complete": complete, "status": "complete" if complete else "partial"}


def reconcile_leads(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for row in left + right:
        missing = [field for field in RECONCILIATION_FIELDS if field not in row]
        if missing:
            raise ValueError(f"Строка сверки не содержит полей: {missing}")
        if not str(row["external_link"]).strip():
            raise ValueError("Внешняя ссылка для сверки не может быть пустой")
    for name, rows in (("первом", left), ("втором", right)):
        links = [str(row["external_link"]) for row in rows]
        if len(links) != len(set(links)):
            raise ValueError(f"В {name} источнике есть дубли внешней ссылки")
    right_by_link = {str(row["external_link"]): row for row in right if str(row["external_link"]).strip()}
    result: list[dict[str, Any]] = []
    used: set[str] = set()
    for row in left:
        link = str(row["external_link"])
        other = right_by_link.get(link)
        if other:
            used.add(link)
        result.append({
            "external_link": link,
            "left": row,
            "right": other,
            "source_match": bool(other) and row["source"] == other["source"],
            "time_match": bool(other) and row["occurred_at"] == other["occurred_at"],
            "status_match": bool(other) and row["status"] == other["status"],
            "responsible_match": bool(other) and row["responsible"] == other["responsible"],
            "status": "matched" if other and all(row[field] == other[field] for field in RECONCILIATION_FIELDS) else "mismatch",
        })
    for link, row in right_by_link.items():
        if link not in used:
            result.append({"external_link": link, "left": None, "right": row, "source_match": False, "time_match": False, "status_match": False, "responsible_match": False, "status": "right_only"})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--credentials", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    credentials = private_credentials(Path(args.credentials).expanduser().resolve())
    base_url = str(credentials["base_url"]).rstrip("/")
    token = str(credentials["access_token"])
    output = Path(args.output_dir).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(output, 0o700)

    def getter(url: str) -> dict[str, Any]:
        response = requests.get(url if url.startswith("http") else base_url + url, headers={"Authorization": f"Bearer {token}"})
        response.raise_for_status()
        value = response.json()
        if not isinstance(value, dict):
            raise RuntimeError("amoCRM вернула неверный JSON")
        return value

    targets = {
        "account.json": "/api/v4/account",
        "pipelines.json": "/api/v4/leads/pipelines?limit=250",
        "lead-fields.json": "/api/v4/leads/custom_fields?limit=250",
        "contact-fields.json": "/api/v4/contacts/custom_fields?limit=250",
    }
    states: dict[str, Any] = {}
    for filename, endpoint in targets.items():
        pages, state = fetch_paginated(getter, base_url + endpoint)
        atomic_json(output / filename, {"pages": pages, "state": state})
        states[filename] = state
    summary = {"status": "complete" if all(state["complete"] for state in states.values()) else "partial", "sources": states}
    atomic_json(output / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if summary["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
