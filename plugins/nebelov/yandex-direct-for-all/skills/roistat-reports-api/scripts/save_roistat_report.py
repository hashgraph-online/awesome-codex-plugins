#!/usr/bin/env python3
"""Проверить или применить утверждённый пакет сохранённого отчёта Roistat."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable


class GateError(RuntimeError):
    pass


Api = Callable[[str, dict[str, Any]], dict[str, Any]]


@dataclass
class Prepared:
    project: str
    action: str
    target_ref: str
    spec: dict[str, Any]
    spec_sha256: str
    api_key: str
    base_url: str
    state_root: Path


def parse_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GateError("Время подтверждения должно быть ISO 8601") from exc
    if parsed.tzinfo is None:
        raise GateError("Время подтверждения должно содержать часовой пояс")
    return parsed.astimezone(timezone.utc)


def private_json(path: Path) -> dict[str, Any]:
    if not path.is_file() or stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise GateError("Закрытый файл должен существовать и иметь права 0600")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise GateError("Закрытый файл должен содержать объект JSON")
    return value


def private_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path, 0o700)


def atomic_json(path: Path, value: Any) -> None:
    private_dir(path.parent)
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


def prepare(project: str, action: str, target_ref: str, spec_path: Path, sha_path: Path, approval_path: Path, *, apply: bool, now: datetime | None = None) -> Prepared:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    raw = spec_path.read_bytes()
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise GateError("Спецификация отчёта не является JSON") from exc
    if not isinstance(spec, dict) or not isinstance(spec.get("title"), str) or not spec["title"].strip() or not isinstance(spec.get("settings"), dict):
        raise GateError("Спецификация должна содержать title и settings")
    if action not in {"create", "update"} or not target_ref.strip():
        raise GateError("Нужны точные action и target-ref")
    digest = hashlib.sha256(raw).hexdigest()
    try:
        declared = sha_path.read_text(encoding="utf-8").strip().split()[0]
    except (OSError, IndexError) as exc:
        raise GateError("Файл контрольной суммы отсутствует") from exc
    if declared != digest:
        raise GateError("Контрольная сумма спецификации не совпала")
    approval = private_json(approval_path)
    required = {"approved", "spec_sha256", "project", "action", "target_ref", "approved_at", "expires_at"}
    if not required.issubset(approval) or approval["approved"] is not True:
        raise GateError("Подтверждение владельца неполное")
    if approval["spec_sha256"] != digest or str(approval["project"]) != project or approval["action"] != action or str(approval["target_ref"]) != target_ref:
        raise GateError("Подтверждение относится к другой цели")
    approved_at = parse_time(str(approval["approved_at"]))
    expires_at = parse_time(str(approval["expires_at"]))
    if approved_at > now or expires_at <= now or expires_at - approved_at > timedelta(hours=24):
        raise GateError("Подтверждение ещё не действует, просрочено или выдано более чем на 24 часа")
    if os.environ.get("ROISTAT_PROJECT", "").strip() != project:
        raise GateError("Область проекта не совпадает")
    api_key = os.environ.get("ROISTAT_WRITE_API_KEY", "").strip()
    if apply and os.environ.get("ROISTAT_WRITE_ARMED") != "1":
        raise GateError("Запись Roistat не вооружена")
    if apply and not api_key:
        raise GateError("Для записи нужна отдельная переменная ROISTAT_WRITE_API_KEY")
    state_root = Path(os.environ.get("YDFALL_STATE_ROOT") or Path.home() / ".local/state/yandex-direct-for-all").expanduser()
    base_url = os.environ.get("ROISTAT_BASE_URL", "https://cloud.roistat.com/api/v1").strip()
    return Prepared(project, action, target_ref, spec, digest, api_key, base_url, state_root)


def default_api(prepared: Prepared, endpoint: str, body: dict[str, Any]) -> dict[str, Any]:
    url = f"{prepared.base_url.rstrip('/')}/{endpoint}?project={urllib.parse.quote(prepared.project)}"
    request = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode("utf-8"), headers={"Api-key": prepared.api_key, "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request) as response:
            value = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        raise GateError(f"{endpoint}: HTTP {exc.code}") from exc
    if not isinstance(value, dict) or value.get("status") == "error":
        raise GateError(f"{endpoint}: интерфейс вернул ошибку")
    return value


def report_list(value: dict[str, Any]) -> list[dict[str, Any]]:
    rows = value.get("reports")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise GateError("Ответ списка отчётов имеет неверную схему")
    return rows


def execute(prepared: Prepared, api: Callable[[Prepared, str, dict[str, Any]], dict[str, Any]] = default_api) -> dict[str, Any]:
    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{prepared.spec_sha256[:12]}"
    evidence = prepared.state_root / "roistat-writes" / run_id
    private_dir(evidence)
    before_response = api(prepared, "project/analytics/reports", {})
    before = report_list(before_response)
    atomic_json(evidence / "before.json", {"reports": before})
    atomic_json(evidence / "spec.json", prepared.spec)
    before_by_id = {str(row.get("id")): row for row in before}
    if prepared.action == "create":
        if prepared.target_ref != prepared.spec["title"] or any(row.get("title") == prepared.spec["title"] for row in before):
            raise GateError("Создаваемая цель не совпала или название уже занято")
        request_report = dict(prepared.spec)
        previous_target = None
    else:
        previous_target = before_by_id.get(prepared.target_ref)
        if previous_target is None:
            raise GateError("Точный изменяемый отчёт не найден")
        request_report = {**prepared.spec, "id": prepared.target_ref}
    atomic_json(evidence / "request.json", {"report": request_report})
    response = api(prepared, "project/analytics/report", {"report": request_report})
    atomic_json(evidence / "response.json", response)
    after = report_list(api(prepared, "project/analytics/reports", {}))
    atomic_json(evidence / "after.json", {"reports": after})
    after_by_id = {str(row.get("id")): row for row in after}
    if prepared.action == "update":
        target = after_by_id.get(prepared.target_ref)
        unchanged_before = {key: value for key, value in before_by_id.items() if key != prepared.target_ref}
        unchanged_after = {key: value for key, value in after_by_id.items() if key != prepared.target_ref}
        if unchanged_before != unchanged_after:
            raise GateError("Изменились посторонние сохранённые отчёты")
        atomic_json(evidence / "reversal-candidate.json", {"requires_new_approval": True, "report": previous_target})
    else:
        new_ids = set(after_by_id) - set(before_by_id)
        if len(new_ids) != 1:
            raise GateError("Созданный отчёт нельзя определить однозначно")
        if any(after_by_id.get(key) != value for key, value in before_by_id.items()):
            raise GateError("При создании изменились существующие отчёты")
        target = after_by_id[next(iter(new_ids))]
        atomic_json(evidence / "reversal-candidate.json", {"requires_new_approval": True, "action": "manual_delete_review", "report": target})
    if not target or target.get("title") != prepared.spec["title"] or target.get("settings") != prepared.spec["settings"]:
        raise GateError("Чтение после записи не совпало со спецификацией")
    result = {"status": "complete", "run_id": run_id, "action": prepared.action, "title": target.get("title")}
    atomic_json(evidence / "result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--report-spec", required=True)
    parser.add_argument("--spec-sha256", required=True)
    parser.add_argument("--approval", required=True)
    parser.add_argument("--action", choices=["create", "update"], required=True)
    parser.add_argument("--target-ref", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        prepared = prepare(args.project, args.action, args.target_ref, Path(args.report_spec), Path(args.spec_sha256), Path(args.approval), apply=args.apply)
        if not args.apply:
            print("Пакет отчёта проверен; сетевых вызовов не было")
            return 0
        result = execute(prepared)
    except Exception as exc:
        print(f"Пакет отклонён: {exc}")
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
