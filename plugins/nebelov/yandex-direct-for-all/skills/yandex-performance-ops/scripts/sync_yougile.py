#!/usr/bin/env python3
"""Проверить или синхронизировать подтверждённый набор задач с YouGile."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
import stat
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_HOST = "https://ru.yougile.com/api-v2"
ACTION = "sync_yougile_tasks"
PRIORITY_COLUMN = {
    "CRITICAL": "planning", "P1": "planning", "HIGH": "planning", "P2": "backlog",
    "MEDIUM": "backlog", "P3": "backlog", "LOW": "future", "P4": "future",
}
CATEGORY_COLOR = {
    "SETTING_CHANGE": "red", "PLACEMENT_CHANGE": "red", "NEGATIVE_KEYWORD": "yellow",
    "AD_COMPONENT": "blue", "BID_ADJUSTMENT": "yellow", "STRUCTURE_CHANGE": "violet",
    "scale": "blue", "optimize": "yellow", "review": "turquoise", "monitor": "turquoise",
}


class GateError(RuntimeError):
    """Пакет или разрешение не прошли проверку."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path, *, private: bool = False) -> dict[str, Any]:
    if private and (not path.is_file() or stat.S_IMODE(path.stat().st_mode) & 0o077):
        raise GateError(f"Закрытый файл должен иметь права 0600: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GateError(f"Некорректный JSON: {path}") from exc
    if not isinstance(value, dict):
        raise GateError(f"Файл должен содержать объект JSON: {path}")
    return value


def write_private_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    os.chmod(path, 0o600)


def required_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GateError(f"Поле {field} должно быть непустой строкой")
    return value.strip()


def resolve_input(package_path: Path, raw: Any, field: str) -> Path:
    path = Path(required_text(raw, field)).expanduser()
    if not path.is_absolute():
        path = package_path.parent / path
    path = path.resolve()
    if not path.is_file():
        raise GateError(f"Не найден файл {field}: {path}")
    return path


def parse_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GateError("expires_at должен иметь формат ISO 8601") from exc
    if parsed.tzinfo is None:
        raise GateError("expires_at должен содержать часовой пояс")
    return parsed.astimezone(timezone.utc)


def load_tasks(path: Path, category: str | None, priority: str | None) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = set(reader.fieldnames or [])
        required = {"action", "priority"}
        if not required.issubset(fields):
            raise GateError(f"В таблице задач отсутствуют поля: {', '.join(sorted(required - fields))}")
        tasks = []
        for row in reader:
            row_category = row.get("category") or row.get("type") or "unknown"
            if category and row_category != category:
                continue
            if priority and row.get("priority") != priority:
                continue
            if not (row.get("action") or "").strip():
                raise GateError("В таблице найдена задача без действия")
            tasks.append({key: value or "" for key, value in row.items() if key is not None})
    return tasks


def load_columns(path: Path, preset: str) -> dict[str, str]:
    value = load_json(path, private=True)
    raw = value.get(preset)
    if not isinstance(raw, dict) or not raw:
        raise GateError(f"В файле колонок нет набора {preset}")
    columns: dict[str, str] = {}
    for alias, object_id in raw.items():
        clean_alias = required_text(alias, "псевдоним колонки")
        clean_id = required_text(object_id, f"колонка {clean_alias}")
        if clean_id.startswith("REPLACE_") or clean_id.startswith("COLUMN_"):
            raise GateError(f"Для колонки {clean_alias} оставлена заглушка")
        columns[clean_alias] = clean_id
    if "backlog" not in columns:
        raise GateError("Набор колонок должен содержать backlog")
    return columns


def prepare_package(package_path: Path, package: dict[str, Any]) -> dict[str, Any]:
    target_ref = required_text(package.get("target_ref"), "target_ref")
    tasks_path = resolve_input(package_path, package.get("tasks_file"), "tasks_file")
    columns_path = resolve_input(package_path, package.get("columns_file"), "columns_file")
    if sha256_file(tasks_path) != required_text(package.get("tasks_sha256"), "tasks_sha256"):
        raise GateError("Таблица задач изменилась после составления пакета")
    if sha256_file(columns_path) != required_text(package.get("columns_sha256"), "columns_sha256"):
        raise GateError("Файл колонок изменился после составления пакета")
    preset = required_text(package.get("board_preset"), "board_preset")
    campaign = required_text(package.get("campaign_name", "Директ"), "campaign_name")
    category = package.get("category")
    priority = package.get("priority")
    if category is not None and not isinstance(category, str):
        raise GateError("category должен быть строкой или null")
    if priority is not None and not isinstance(priority, str):
        raise GateError("priority должен быть строкой или null")
    columns = load_columns(columns_path, preset)
    tasks = load_tasks(tasks_path, category, priority)
    needed = {PRIORITY_COLUMN.get(task["priority"], "backlog") for task in tasks}
    missing = needed - set(columns)
    if missing:
        raise GateError(f"Не заданы целевые колонки: {', '.join(sorted(missing))}")
    return {
        "target_ref": target_ref, "tasks_path": tasks_path, "columns_path": columns_path,
        "campaign": campaign, "columns": columns, "tasks": tasks,
    }


def authorize(package_path: Path, target_ref: str, approval_path: Path) -> str:
    if os.environ.get("YOUGILE_WRITE_ARMED") != "1":
        raise GateError("Для записи требуется YOUGILE_WRITE_ARMED=1")
    api_key = os.environ.get("YOUGILE_WRITE_API_KEY", "").strip()
    if not api_key or any(character.isspace() for character in api_key):
        raise GateError("Для записи требуется отдельная переменная YOUGILE_WRITE_API_KEY")
    approval = load_json(approval_path, private=True)
    if approval.get("approved") is not True:
        raise GateError("Синхронизация не подтверждена")
    if approval.get("action") != ACTION or approval.get("target_ref") != target_ref:
        raise GateError("Разрешение относится к другому действию или доске")
    if approval.get("spec_sha256") != sha256_file(package_path):
        raise GateError("Пакет изменился после подтверждения")
    if parse_time(str(approval.get("expires_at") or "")) <= datetime.now(timezone.utc):
        raise GateError("Срок разрешения истёк")
    return api_key


def api_request(host: str, api_key: str, method: str, path: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"{host.rstrip('/')}/{path.lstrip('/')}"
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8") if data is not None else None
    request = urllib.request.Request(url, data=payload, method=method, headers={
        "Authorization": f"Bearer {api_key}", "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(request) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        exc.read()
        raise RuntimeError(f"YouGile отклонил {method} {path}: HTTP {exc.code}") from exc
    try:
        value = json.loads(raw) if raw else {}
    except json.JSONDecodeError as exc:
        raise RuntimeError("YouGile вернул некорректный JSON") from exc
    if not isinstance(value, dict):
        raise RuntimeError("YouGile вернул ответ неверной схемы")
    return value


def list_column_tasks(host: str, api_key: str, column_id: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    offset = 0
    while True:
        query = urllib.parse.urlencode({"columnId": column_id, "limit": 100, "offset": offset})
        response = api_request(host, api_key, "GET", f"task-list?{query}")
        page = response.get("content", [])
        if not isinstance(page, list):
            raise RuntimeError("YouGile вернул список задач неверной схемы")
        items.extend(item for item in page if isinstance(item, dict))
        next_offset = (response.get("paging") or {}).get("nextOffset")
        if not page or next_offset is None:
            return items
        offset = int(next_offset)


def task_title(campaign: str, row: dict[str, str]) -> str:
    detail = row.get("description") or row.get("rationale") or row.get("notes") or row.get("expected_impact") or row["action"]
    target = row.get("target_name") or row.get("entity") or ""
    suffix = f" — {target.strip()}" if target.strip() else ""
    return f"[{campaign}] {detail.strip()[:100]}{suffix}"[:180]


def task_description(row: dict[str, str]) -> str:
    category = row.get("category") or row.get("type") or "unknown"
    pieces = [
        f"<p><b>{html.escape(category)}</b> | Приоритет: {html.escape(row['priority'])}</p>",
        f"<p><b>Действие:</b> {html.escape(row['action'])}</p>",
    ]
    for label, keys in (
        ("Параметры", ("params_json", "params")),
        ("Обоснование", ("evidence", "rationale", "expected_impact")),
        ("Ожидаемая экономия за 30 дней", ("savings_30d",)),
        ("Цель", ("target_name", "entity")),
    ):
        value = next((row.get(key, "").strip() for key in keys if row.get(key, "").strip()), "")
        if value:
            pieces.append(f"<p><b>{label}:</b> {html.escape(value)}</p>")
    return "".join(pieces)


def apply_tasks(host: str, api_key: str, prepared: dict[str, Any], evidence_dir: Path) -> dict[str, int]:
    columns: dict[str, str] = prepared["columns"]
    before: dict[str, Any] = {}
    existing_titles: set[str] = set()
    for alias, column_id in columns.items():
        tasks = list_column_tasks(host, api_key, column_id)
        before[alias] = tasks
        existing_titles.update(str(task.get("title")) for task in tasks if task.get("title"))
    write_private_json(evidence_dir / "before.json", before)
    created: list[dict[str, Any]] = []
    write_private_json(evidence_dir / "reversal-candidate.json", {"created_tasks": created})
    skipped = 0
    for row in prepared["tasks"]:
        title = task_title(prepared["campaign"], row)
        if title in existing_titles:
            skipped += 1
            continue
        alias = PRIORITY_COLUMN.get(row["priority"], "backlog")
        column_id = columns[alias]
        category = row.get("category") or row.get("type") or "unknown"
        payload = {
            "title": title,
            "columnId": column_id,
            "description": task_description(row),
            "color": CATEGORY_COLOR.get(category, "yellow"),
        }
        created_response = api_request(host, api_key, "POST", "tasks", payload)
        task_id = required_text(created_response.get("id"), "task.id")
        created.append({"id": task_id, "title": title, "column_alias": alias})
        write_private_json(evidence_dir / "reversal-candidate.json", {"created_tasks": created})
        time.sleep(1.25)
        readback = api_request(host, api_key, "GET", f"tasks/{task_id}")
        if readback.get("id") != task_id or readback.get("title") != title or readback.get("columnId") != column_id:
            raise RuntimeError(f"Контрольное чтение не подтвердило задачу «{title}»")
        existing_titles.add(title)
    after: dict[str, Any] = {}
    for alias, column_id in columns.items():
        after[alias] = list_column_tasks(host, api_key, column_id)
    write_private_json(evidence_dir / "after.json", after)
    write_private_json(evidence_dir / "readback.json", {"created_tasks": created})
    write_private_json(evidence_dir / "diff.json", {"created_count": len(created), "skipped_count": skipped, "created_tasks": created})
    return {"created": len(created), "skipped": skipped}


def main() -> int:
    parser = argparse.ArgumentParser(description="Безопасная синхронизация задач с YouGile")
    parser.add_argument("--package", required=True, help="Закрытый пакет синхронизации с правами 0600")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--approval", help="Закрытый JSON-файл разрешения с правами 0600")
    parser.add_argument("--evidence-dir", help="Закрытая папка доказательств")
    parser.add_argument("--host", default=os.environ.get("YOUGILE_API_HOST_URL", DEFAULT_HOST))
    args = parser.parse_args()
    try:
        package_path = Path(args.package).expanduser().resolve()
        package = load_json(package_path, private=True)
        prepared = prepare_package(package_path, package)
        print(f"Проверено локально для «{prepared['target_ref']}»: задач {len(prepared['tasks'])}, набор колонок готов.")
        print(f"Контрольная сумма пакета: {sha256_file(package_path)}")
        if not args.apply:
            print("Синхронизация не выполнялась. Для применения нужны --apply, разрешение, вооружение и отдельный ключ записи.")
            return 0
        if not args.approval or not args.evidence_dir:
            raise GateError("Для применения обязательны --approval и --evidence-dir")
        api_key = authorize(package_path, prepared["target_ref"], Path(args.approval).expanduser().resolve())
        evidence_dir = Path(args.evidence_dir).expanduser().resolve()
        result = apply_tasks(args.host, api_key, prepared, evidence_dir)
        print(f"Синхронизация подтверждена контрольным чтением: создано {result['created']}, уже существовало {result['skipped']}.")
        print(f"Закрытые доказательства: {evidence_dir}")
        return 0
    except (GateError, RuntimeError, OSError, KeyError, TypeError, ValueError, UnicodeError) as exc:
        print(f"Отклонено: {exc}", file=os.sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
