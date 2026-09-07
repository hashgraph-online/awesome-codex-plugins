#!/usr/bin/env python3
"""Проверить или применить описание рабочего пространства YouGile.

Без ``--apply`` сценарий только проверяет локальный файл и не обращается к сети.
Запись требует отдельного ключа, вооружения и закрытого разрешения на точную
контрольную сумму описания. Служебные номера попадают только в закрытые
доказательства с правами 0600.
"""

from __future__ import annotations

import argparse
import hashlib
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
ACTION = "bootstrap_yougile_workspace"


class GateError(RuntimeError):
    """Запись отклонена до изменения внешней системы."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GateError("expires_at должен иметь формат ISO 8601") from exc
    if parsed.tzinfo is None:
        raise GateError("expires_at должен содержать часовой пояс")
    return parsed.astimezone(timezone.utc)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GateError(f"Некорректный JSON: {path}") from exc
    if not isinstance(value, dict):
        raise GateError(f"Файл должен содержать объект JSON: {path}")
    return value


def load_private_json(path: Path) -> dict[str, Any]:
    if not path.is_file() or stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise GateError("Файл разрешения должен существовать и иметь права 0600")
    return load_json(path)


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


def validate_spec(spec: dict[str, Any]) -> dict[str, int | str]:
    project = spec.get("project")
    if not isinstance(project, dict):
        raise GateError("Описание должно содержать объект project")
    project_title = required_text(project.get("title"), "project.title")
    boards = spec.get("boards")
    if not isinstance(boards, list) or not boards:
        raise GateError("Описание должно содержать непустой список boards")
    seen_boards: set[str] = set()
    seen_board_aliases: set[str] = set()
    column_count = 0
    task_count = 0
    for board_index, board in enumerate(boards):
        if not isinstance(board, dict):
            raise GateError(f"boards[{board_index}] должен быть объектом")
        title = required_text(board.get("title"), f"boards[{board_index}].title")
        alias = required_text(board.get("alias"), f"boards[{board_index}].alias")
        if title in seen_boards or alias in seen_board_aliases:
            raise GateError(f"Повторяется название или псевдоним доски: {title}")
        seen_boards.add(title)
        seen_board_aliases.add(alias)
        columns = board.get("columns")
        if not isinstance(columns, list) or not columns:
            raise GateError(f"Доска {title} должна содержать колонки")
        aliases: set[str] = set()
        titles: set[str] = set()
        for column_index, column in enumerate(columns):
            if not isinstance(column, dict):
                raise GateError(f"Колонка {column_index} доски {title} должна быть объектом")
            column_title = required_text(column.get("title"), "column.title")
            column_alias = required_text(column.get("alias"), "column.alias")
            if column_title in titles or column_alias in aliases:
                raise GateError(f"На доске {title} повторяется колонка или псевдоним")
            titles.add(column_title)
            aliases.add(column_alias)
            color = column.get("color")
            if color is not None and (not isinstance(color, int) or isinstance(color, bool)):
                raise GateError(f"Цвет колонки {column_title} должен быть целым числом")
            column_count += 1
        tasks = board.get("tasks", [])
        if not isinstance(tasks, list):
            raise GateError(f"tasks доски {title} должен быть списком")
        seen_tasks: set[tuple[str, str]] = set()
        for task_index, task in enumerate(tasks):
            if not isinstance(task, dict):
                raise GateError(f"Задача {task_index} доски {title} должна быть объектом")
            task_title = required_text(task.get("title"), "task.title")
            column_alias = required_text(task.get("column_alias"), "task.column_alias")
            if column_alias not in aliases:
                raise GateError(f"Задача {task_title} ссылается на неизвестную колонку {column_alias}")
            key = (column_alias, task_title)
            if key in seen_tasks:
                raise GateError(f"На доске {title} повторяется задача {task_title}")
            seen_tasks.add(key)
            task_count += 1
        _ = alias
    return {"project": project_title, "boards": len(boards), "columns": column_count, "tasks": task_count}


def authorize(spec_path: Path, project_title: str, approval_path: Path) -> str:
    if os.environ.get("YOUGILE_WRITE_ARMED") != "1":
        raise GateError("Для записи требуется YOUGILE_WRITE_ARMED=1")
    api_key = os.environ.get("YOUGILE_WRITE_API_KEY", "").strip()
    if not api_key or any(character.isspace() for character in api_key):
        raise GateError("Для записи требуется отдельная переменная YOUGILE_WRITE_API_KEY")
    approval = load_private_json(approval_path)
    expected = sha256_file(spec_path)
    if approval.get("approved") is not True:
        raise GateError("Запись не подтверждена")
    if approval.get("action") != ACTION or approval.get("target_ref") != project_title:
        raise GateError("Разрешение относится к другому действию или проекту")
    if approval.get("spec_sha256") != expected:
        raise GateError("Описание изменилось после подтверждения")
    if parse_time(str(approval.get("expires_at") or "")) <= datetime.now(timezone.utc):
        raise GateError("Срок разрешения истёк")
    return api_key


def api_request(host: str, api_key: str, method: str, path: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"{host.rstrip('/')}/{path.lstrip('/')}"
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8") if data is not None else None
    request = urllib.request.Request(url, data=payload, method=method, headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
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


def paged_list(host: str, api_key: str, path: str, query: dict[str, str] | None = None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    offset = 0
    while True:
        params = dict(query or {})
        params.update({"limit": "100", "offset": str(offset)})
        response = api_request(host, api_key, "GET", f"{path}?{urllib.parse.urlencode(params)}")
        page = response.get("content", [])
        if not isinstance(page, list):
            raise RuntimeError("YouGile вернул список неверной схемы")
        items.extend(item for item in page if isinstance(item, dict))
        next_offset = (response.get("paging") or {}).get("nextOffset")
        if not page or next_offset is None:
            return items
        offset = int(next_offset)


def exact_match(items: list[dict[str, Any]], title: str) -> dict[str, Any] | None:
    matches = [item for item in items if item.get("title") == title]
    if len(matches) > 1:
        raise RuntimeError(f"Найдено несколько объектов с названием {title}")
    return matches[0] if matches else None


def create_and_read(host: str, api_key: str, resource: str, payload: dict[str, Any]) -> dict[str, Any]:
    created = api_request(host, api_key, "POST", resource, payload)
    object_id = required_text(created.get("id"), f"{resource}.id")
    time.sleep(1.25)
    readback = api_request(host, api_key, "GET", f"{resource}/{object_id}")
    if readback.get("id") != object_id or readback.get("title") != payload.get("title"):
        raise RuntimeError(f"Контрольное чтение {resource} не подтвердило запись")
    return readback


def get_or_create(host: str, api_key: str, resource: str, title: str, query: dict[str, str], payload: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    found = exact_match(paged_list(host, api_key, resource, {**query, "title": title}), title)
    return (found, False) if found else (create_and_read(host, api_key, resource, payload), True)


def snapshot_workspace(host: str, api_key: str, project_title: str) -> dict[str, Any]:
    projects = paged_list(host, api_key, "projects", {"title": project_title})
    project = exact_match(projects, project_title)
    if not project:
        return {"project": None, "boards": []}
    project_id = required_text(project.get("id"), "project.id")
    boards = paged_list(host, api_key, "boards", {"projectId": project_id})
    return {"project": project, "boards": boards}


def apply_spec(host: str, api_key: str, spec: dict[str, Any], evidence_dir: Path) -> dict[str, Any]:
    project_title = str(spec["project"]["title"]).strip()
    before = snapshot_workspace(host, api_key, project_title)
    write_private_json(evidence_dir / "before.json", before)
    created_objects: list[dict[str, str]] = []
    write_private_json(evidence_dir / "reversal-candidate.json", {"created": created_objects})

    project, created = get_or_create(host, api_key, "projects", project_title, {}, {"title": project_title})
    project_id = required_text(project.get("id"), "project.id")
    if created:
        created_objects.append({"resource": "projects", "id": project_id, "title": project_title})
        write_private_json(evidence_dir / "reversal-candidate.json", {"created": created_objects})

    expected: dict[str, Any] = {"project": {"id": project_id, "title": project_title}, "boards": []}
    for board_spec in spec["boards"]:
        board_title = str(board_spec["title"]).strip()
        board, created = get_or_create(
            host, api_key, "boards", board_title, {"projectId": project_id},
            {"title": board_title, "projectId": project_id},
        )
        board_id = required_text(board.get("id"), "board.id")
        if created:
            created_objects.append({"resource": "boards", "id": board_id, "title": board_title})
            write_private_json(evidence_dir / "reversal-candidate.json", {"created": created_objects})
        column_ids: dict[str, str] = {}
        board_record: dict[str, Any] = {"id": board_id, "title": board_title, "columns": [], "tasks": []}
        for column_spec in board_spec["columns"]:
            column_title = str(column_spec["title"]).strip()
            payload: dict[str, Any] = {"title": column_title, "boardId": board_id}
            if column_spec.get("color") is not None:
                payload["color"] = column_spec["color"]
            column, created = get_or_create(host, api_key, "columns", column_title, {"boardId": board_id}, payload)
            column_id = required_text(column.get("id"), "column.id")
            column_ids[str(column_spec["alias"]).strip()] = column_id
            board_record["columns"].append(column)
            if created:
                created_objects.append({"resource": "columns", "id": column_id, "title": column_title})
                write_private_json(evidence_dir / "reversal-candidate.json", {"created": created_objects})
        for task_spec in board_spec.get("tasks", []):
            column_id = column_ids[str(task_spec["column_alias"]).strip()]
            task_title = str(task_spec["title"]).strip()
            payload = {"title": task_title, "columnId": column_id, "description": str(task_spec.get("description", ""))}
            if task_spec.get("color"):
                payload["color"] = task_spec["color"]
            task, created = get_or_create(host, api_key, "tasks", task_title, {"columnId": column_id}, payload)
            board_record["tasks"].append(task)
            if created:
                task_id = required_text(task.get("id"), "task.id")
                created_objects.append({"resource": "tasks", "id": task_id, "title": task_title})
                write_private_json(evidence_dir / "reversal-candidate.json", {"created": created_objects})
        expected["boards"].append(board_record)

    after = snapshot_workspace(host, api_key, project_title)
    write_private_json(evidence_dir / "after.json", after)
    write_private_json(evidence_dir / "readback.json", expected)
    write_private_json(evidence_dir / "diff.json", {"created_count": len(created_objects), "created": created_objects})
    return {"created": len(created_objects), "boards": len(expected["boards"])}


def main() -> int:
    parser = argparse.ArgumentParser(description="Безопасная подготовка рабочего пространства YouGile")
    parser.add_argument("--spec", required=True, help="Описание проекта, досок, колонок и задач")
    parser.add_argument("--apply", action="store_true", help="Разрешить запись после прохождения ворот")
    parser.add_argument("--approval", help="Закрытый JSON-файл разрешения с правами 0600")
    parser.add_argument("--evidence-dir", help="Закрытая папка доказательств")
    parser.add_argument("--host", default=os.environ.get("YOUGILE_API_HOST_URL", DEFAULT_HOST))
    args = parser.parse_args()

    try:
        spec_path = Path(args.spec).expanduser().resolve()
        spec = load_json(spec_path)
        summary = validate_spec(spec)
        print(f"Проверено локально: проект «{summary['project']}», досок {summary['boards']}, колонок {summary['columns']}, задач {summary['tasks']}")
        print(f"Контрольная сумма описания: {sha256_file(spec_path)}")
        if not args.apply:
            print("Запись не выполнялась. Для применения нужны --apply, разрешение, вооружение и отдельный ключ записи.")
            return 0
        if not args.approval or not args.evidence_dir:
            raise GateError("Для применения обязательны --approval и --evidence-dir")
        approval_path = Path(args.approval).expanduser().resolve()
        evidence_dir = Path(args.evidence_dir).expanduser().resolve()
        api_key = authorize(spec_path, str(summary["project"]), approval_path)
        result = apply_spec(args.host, api_key, spec, evidence_dir)
        print(f"Применение подтверждено контрольным чтением: досок {result['boards']}, создано объектов {result['created']}.")
        print(f"Закрытые доказательства: {evidence_dir}")
        return 0
    except (GateError, RuntimeError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"Отклонено: {exc}", file=os.sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
