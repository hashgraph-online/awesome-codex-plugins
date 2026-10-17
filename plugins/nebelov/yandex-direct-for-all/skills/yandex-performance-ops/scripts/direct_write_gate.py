#!/usr/bin/env python3
"""Единственные программные ворота записи в Яндекс.Директ."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from check_access_paths import sanitize_error

ALLOWED_PAIRS = {
    ("campaigns", "add"), ("campaigns", "update"), ("campaigns", "suspend"),
    ("adgroups", "add"), ("adgroups", "update"),
    ("ads", "add"), ("ads", "update"), ("ads", "suspend"), ("ads", "resume"),
    ("ads", "archive"), ("ads", "moderate"),
    ("keywords", "add"), ("keywords", "update"),
    ("negativekeywordsharedsets", "add"),
}
READ_SERVICES = {
    "campaigns", "adgroups", "ads", "keywords", "negativekeywordsharedsets",
    "sitelinks", "adextensions", "bids", "keywordbids",
}
REVERSIBLE_PAIRS = {
    ("campaigns", "update"), ("adgroups", "update"), ("ads", "update"),
    ("keywords", "update"), ("ads", "suspend"), ("ads", "resume"),
}
REQUIRED_PACK_FIELDS = {
    "schema_version", "run_id", "client_login", "environment", "operation_type",
    "created_at", "expires_at", "source_snapshot_sha256", "owner_approval_ref",
    "max_api_units", "operations",
}
REQUIRED_OPERATION_FIELDS = {
    "id", "service", "method", "version", "params", "depends_on", "readback",
    "expected_after", "reversible", "estimated_api_units", "max_api_units",
}
Writer = Callable[[dict[str, Any], str, str, str], tuple[dict[str, Any], int]]
Reader = Callable[[dict[str, Any], str, str, str], dict[str, Any]]


class GateError(RuntimeError):
    """Отклонение до записи или проверяемая ошибка операции."""


@dataclass
class Prepared:
    pack: dict[str, Any]
    pack_bytes: bytes
    pack_sha256: str
    token: str
    state_root: Path
    lock_path: Path


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GateError("Время пакета должно быть в ISO 8601") from exc
    if parsed.tzinfo is None:
        raise GateError("Время пакета должно содержать часовой пояс")
    return parsed.astimezone(timezone.utc)


def _private_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise GateError("Файл подтверждения владельца не найден")
    if stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise GateError("Файл подтверждения владельца должен иметь права 0600")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError("Файл подтверждения владельца повреждён") from exc
    if not isinstance(value, dict):
        raise GateError("Подтверждение владельца должно быть объектом JSON")
    return value


def _validate_readback(value: Any) -> None:
    if not isinstance(value, dict):
        raise GateError("readback должен быть объектом")
    if set(value) != {"service", "version", "params", "result_key"}:
        raise GateError("readback содержит неверный набор полей")
    if value["service"] not in READ_SERVICES or value["version"] not in {"v5", "v501"}:
        raise GateError("readback использует неподдерживаемый маршрут")
    if not isinstance(value["params"], dict) or not isinstance(value["result_key"], str) or not value["result_key"]:
        raise GateError("readback заполнен неверно")


def validate_structure(pack: dict[str, Any]) -> None:
    if not isinstance(pack, dict):
        raise GateError("Пакет должен быть объектом JSON")
    missing = REQUIRED_PACK_FIELDS - set(pack)
    if missing:
        raise GateError(f"В пакете отсутствует обязательное поле: {sorted(missing)[0]}")
    if set(pack) != REQUIRED_PACK_FIELDS:
        raise GateError("Пакет содержит неподдерживаемые поля")
    if pack["schema_version"] != "1.0":
        raise GateError("Неподдерживаемая версия схемы")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{2,79}", str(pack["run_id"])):
        raise GateError("Неверный run_id")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", str(pack["client_login"])):
        raise GateError("Неверная область клиента")
    if pack["environment"] not in {"sandbox", "production"}:
        raise GateError("Неверная среда")
    if not isinstance(pack["max_api_units"], int) or isinstance(pack["max_api_units"], bool) or pack["max_api_units"] <= 0:
        raise GateError("max_api_units должен быть положительным целым числом")
    if not re.fullmatch(r"[a-f0-9]{64}", str(pack["source_snapshot_sha256"])):
        raise GateError("Неверная контрольная сумма исходного снимка")
    if not isinstance(pack["owner_approval_ref"], str) or not pack["owner_approval_ref"].strip():
        raise GateError("Не задано подтверждение владельца")
    if not isinstance(pack["operations"], list) or not pack["operations"]:
        raise GateError("Пакет не содержит операций")

    operation_type = str(pack["operation_type"])
    if "." not in operation_type or tuple(operation_type.split(".", 1)) not in ALLOWED_PAIRS:
        raise GateError("Неподдерживаемый тип операции")
    identifiers: set[str] = set()
    reserved_total = 0
    for operation in pack["operations"]:
        if not isinstance(operation, dict):
            raise GateError("Операция должна быть объектом")
        missing_operation = REQUIRED_OPERATION_FIELDS - set(operation)
        if missing_operation:
            raise GateError(f"В операции отсутствует поле: {sorted(missing_operation)[0]}")
        if not set(operation).issubset(REQUIRED_OPERATION_FIELDS | {"reversal_fields", "irreversible_reason"}):
            raise GateError("Операция содержит неподдерживаемые поля")
        pair = (str(operation["service"]), str(operation["method"]))
        if pair not in ALLOWED_PAIRS or ".".join(pair) != operation_type:
            raise GateError("Все операции пакета должны иметь подтверждённый тип")
        if operation["version"] not in {"v5", "v501"} or not isinstance(operation["params"], dict):
            raise GateError("Неверная версия или параметры операции")
        identifier = str(operation["id"])
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", identifier) or identifier in identifiers:
            raise GateError("Неверный или повторный идентификатор операции")
        if not isinstance(operation["depends_on"], list) or any(item not in identifiers for item in operation["depends_on"]):
            raise GateError("Зависимость должна ссылаться на предшествующую операцию")
        if not isinstance(operation["reversible"], bool):
            raise GateError("reversible должен быть логическим значением")
        if not isinstance(operation["estimated_api_units"], int) or isinstance(operation["estimated_api_units"], bool) or operation["estimated_api_units"] <= 0:
            raise GateError("estimated_api_units должен быть положительным целым числом")
        if not isinstance(operation["max_api_units"], int) or isinstance(operation["max_api_units"], bool) or operation["max_api_units"] <= 0:
            raise GateError("max_api_units операции должен быть положительным целым числом")
        if operation["estimated_api_units"] > operation["max_api_units"]:
            raise GateError("Оценка единиц API не может превышать предел операции")
        reserved_total += operation["max_api_units"]
        if operation["reversible"] != (pair in REVERSIBLE_PAIRS):
            raise GateError("Признак обратимости не соответствует типу операции")
        if not operation["reversible"]:
            reason = operation.get("irreversible_reason")
            if not isinstance(reason, str) or not reason.strip():
                raise GateError("Необратимая операция должна содержать irreversible_reason")
        if pair[1] == "update" and (not isinstance(operation.get("reversal_fields"), list) or not operation["reversal_fields"]):
            raise GateError("Для обратимого обновления нужны reversal_fields")
        if operation["expected_after"] is None:
            raise GateError("expected_after обязателен")
        _validate_readback(operation["readback"])
        identifiers.add(identifier)
    if reserved_total > pack["max_api_units"]:
        raise GateError("Заявленный бюджет API недостаточен для суммы пределов операций")


def validate_time_window(pack: dict[str, Any], now: datetime) -> None:
    created = _time(str(pack["created_at"]))
    expires = _time(str(pack["expires_at"]))
    if expires <= created or expires - created > timedelta(hours=24):
        raise GateError("Интервал действия пакета должен быть больше нуля и не более 24 часов")
    if now.astimezone(timezone.utc) < created or now.astimezone(timezone.utc) >= expires:
        raise GateError("Пакет ещё не действует или уже просрочен")


def validate_approval(pack: dict[str, Any], pack_sha256: str, now: datetime) -> None:
    approval = _private_json(Path(pack["owner_approval_ref"]).expanduser())
    required = {"approved", "pack_sha256", "client_login", "approved_at", "expires_at"}
    if not required.issubset(approval):
        raise GateError("Подтверждение владельца неполное")
    if approval["approved"] is not True:
        raise GateError("Владелец не подтвердил пакет")
    if approval["pack_sha256"] != pack_sha256 or approval["client_login"] != pack["client_login"]:
        raise GateError("Подтверждение относится к другому пакету или клиенту")
    approved_at = _time(str(approval["approved_at"]))
    expires = _time(str(approval["expires_at"]))
    if approved_at > now.astimezone(timezone.utc) or now.astimezone(timezone.utc) >= expires:
        raise GateError("Подтверждение владельца ещё не действует или просрочено")
    if expires > _time(str(pack["expires_at"])):
        raise GateError("Подтверждение не может действовать дольше пакета")


def prepare(pack_path: Path, sha_path: Path, *, apply: bool, now: datetime | None = None) -> Prepared:
    now = now or datetime.now(timezone.utc)
    pack_bytes = pack_path.read_bytes()
    try:
        pack = json.loads(pack_bytes)
    except json.JSONDecodeError as exc:
        raise GateError("Пакет не является JSON") from exc
    validate_structure(pack)
    digest = hashlib.sha256(pack_bytes).hexdigest()
    try:
        declared = sha_path.read_text(encoding="utf-8").strip().split()[0]
    except (OSError, IndexError) as exc:
        raise GateError("Отдельный файл pack.sha256 отсутствует или повреждён") from exc
    if digest != declared:
        raise GateError("Контрольная сумма пакета не совпала")
    validate_time_window(pack, now)
    validate_approval(pack, digest, now)

    environment = str(pack["environment"])
    runtime_environment = os.environ.get("YANDEX_DIRECT_ENVIRONMENT", "").strip()
    runtime_login = os.environ.get("YANDEX_DIRECT_CLIENT_LOGIN", "").strip()
    if runtime_environment != environment or runtime_login != pack["client_login"]:
        raise GateError("Среда или область клиента не совпадает с пакетом")
    token_name = "YANDEX_DIRECT_SANDBOX_TOKEN" if environment == "sandbox" else "YANDEX_DIRECT_PRODUCTION_WRITE_TOKEN"
    token = os.environ.get(token_name, "").strip()
    if apply and os.environ.get("YD_WRITE_ARMED") != "1":
        raise GateError("Запись не вооружена: требуется YD_WRITE_ARMED=1")
    if apply and not token:
        raise GateError(f"Для записи отсутствует отдельная переменная {token_name}")

    state_root = Path(os.environ.get("YDFALL_STATE_ROOT") or Path.home() / ".local/state/yandex-direct-for-all").expanduser()
    lock_path = state_root / "write-locks" / f"{pack['client_login']}.lock"
    return Prepared(pack, pack_bytes, digest, token, state_root, lock_path)


def _private_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path, 0o700)


def _atomic_json(path: Path, value: Any) -> None:
    _private_dir(path.parent)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def acquire_lock(path: Path, run_id: str) -> None:
    _private_dir(path.parent)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise GateError("Для этой области клиента уже выполняется операция записи") from exc
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(run_id + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _host(environment: str) -> str:
    return "api-sandbox.direct.yandex.com" if environment == "sandbox" else "api.direct.yandex.com"


def _request(service: str, version: str, body: dict[str, Any], token: str, login: str, environment: str) -> tuple[dict[str, Any], Any]:
    raw = _canonical(body)
    request = urllib.request.Request(
        f"https://{_host(environment)}/json/{version}/{service}",
        data=raw,
        headers={"Authorization": f"Bearer {token}", "Client-Login": login, "Accept-Language": "ru", "Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8")), response.headers
    except urllib.error.HTTPError as exc:
        raw_error = exc.read().decode("utf-8", errors="replace")
        raise GateError(sanitize_error(f"HTTP {exc.code}: {raw_error}", (token,))) from exc


def default_writer(operation: dict[str, Any], token: str, login: str, environment: str) -> tuple[dict[str, Any], int]:
    payload, headers = _request(operation["service"], operation["version"], {"method": operation["method"], "params": operation["params"]}, token, login, environment)
    units_raw = str(headers.get("Units") or "0")
    match = re.search(r"\d+", units_raw)
    return payload, int(match.group(0)) if match else 0


def default_reader(readback: dict[str, Any], token: str, login: str, environment: str) -> dict[str, Any]:
    payload, _ = _request(readback["service"], readback["version"], {"method": "get", "params": readback["params"]}, token, login, environment)
    return payload


def _contains(actual: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        return all(key in actual and _contains(actual[key], value) for key, value in expected.items())
    if isinstance(expected, list):
        if not isinstance(actual, list):
            return False
        return all(any(_contains(candidate, wanted) for candidate in actual) for wanted in expected)
    return actual == expected


def _is_partial(payload: dict[str, Any]) -> bool:
    if not isinstance(payload, dict) or payload.get("error") or not isinstance(payload.get("result"), dict):
        return True
    result_lists = [value for key, value in payload["result"].items() if key.endswith("Results") and isinstance(value, list)]
    return bool(result_lists and any(item.get("Errors") for values in result_lists for item in values if isinstance(item, dict)))


def _before_rows(snapshot: dict[str, Any], result_key: str) -> list[dict[str, Any]]:
    rows = ((snapshot.get("result") or {}).get(result_key) or []) if isinstance(snapshot, dict) else []
    return [row for row in rows if isinstance(row, dict)]


def build_reversal(pack: dict[str, Any], before: dict[str, dict[str, Any]]) -> dict[str, Any]:
    operations: list[dict[str, Any]] = []
    for operation in reversed(pack["operations"]):
        if not operation["reversible"]:
            continue
        pair = (operation["service"], operation["method"])
        if pair == ("ads", "suspend"):
            reverse_method, reverse_params = "resume", copy.deepcopy(operation["params"])
        elif pair == ("ads", "resume"):
            reverse_method, reverse_params = "suspend", copy.deepcopy(operation["params"])
        elif operation["method"] == "update":
            write_lists = [(key, value) for key, value in operation["params"].items() if isinstance(value, list)]
            if len(write_lists) != 1:
                raise GateError("Нельзя однозначно построить обратный пакет обновления")
            target_key, _ = write_lists[0]
            rows = _before_rows(before[operation["id"]], operation["readback"]["result_key"])
            reverse_rows = []
            for row in rows:
                if "Id" not in row:
                    raise GateError("В снимке до изменения отсутствует Id")
                reverse_row = {"Id": row["Id"]}
                for field in operation["reversal_fields"]:
                    if field not in row:
                        raise GateError(f"В снимке до изменения отсутствует поле {field}")
                    reverse_row[field] = copy.deepcopy(row[field])
                reverse_rows.append(reverse_row)
            reverse_method, reverse_params = "update", {target_key: reverse_rows}
        else:
            continue
        operations.append({"service": operation["service"], "method": reverse_method, "version": operation["version"], "params": reverse_params, "source_operation": operation["id"]})
    return {"source_run_id": pack["run_id"], "requires_new_owner_approval": True, "operations": operations}


def execute(prepared: Prepared, *, writer: Writer = default_writer, reader: Reader = default_reader) -> dict[str, Any]:
    pack = prepared.pack
    acquire_lock(prepared.lock_path, pack["run_id"])
    try:
        evidence = prepared.state_root / "direct-writes" / pack["run_id"]
        _private_dir(evidence.parent)
        try:
            evidence.mkdir(mode=0o700)
        except FileExistsError as exc:
            raise GateError("Этот run_id уже использован; повторное выполнение пакета запрещено") from exc
        os.chmod(evidence, 0o700)
        _atomic_json(evidence / "pack.json", pack)
        _atomic_json(evidence / "pack.sha256.json", {"sha256": prepared.pack_sha256})
        _atomic_json(evidence / "approval.json", {"ref_name": Path(pack["owner_approval_ref"]).name, "pack_sha256": prepared.pack_sha256})
        before: dict[str, dict[str, Any]] = {}
        statuses: dict[str, str] = {}
        used_units = 0
        result: dict[str, Any] = {"run_id": pack["run_id"], "status": "incomplete", "api_units": 0, "operations": []}
        try:
            for operation in pack["operations"]:
                before[operation["id"]] = reader(operation["readback"], prepared.token, pack["client_login"], pack["environment"])
            _atomic_json(evidence / "before.json", before)
            reversal = build_reversal(pack, before)
            _atomic_json(evidence / "reversal-candidate.json", reversal)

            for index, operation in enumerate(pack["operations"], 1):
                record = {"id": operation["id"], "pair": f"{operation['service']}.{operation['method']}", "status": "pending"}
                result["operations"].append(record)
                if any(statuses.get(dependency) != "ready" for dependency in operation["depends_on"]):
                    record["status"] = "blocked_by_dependency"
                    statuses[operation["id"]] = record["status"]
                    break
                if used_units + operation["max_api_units"] > pack["max_api_units"]:
                    record["status"] = "budget_exhausted_before_write"
                    statuses[operation["id"]] = record["status"]
                    break
                request_evidence = {"service": operation["service"], "method": operation["method"], "version": operation["version"], "params": operation["params"]}
                _atomic_json(evidence / f"request-{index:03d}.json", request_evidence)
                payload, units = writer(operation, prepared.token, pack["client_login"], pack["environment"])
                actual_units = max(0, int(units))
                used_units += actual_units
                _atomic_json(evidence / f"response-{index:03d}.json", payload)
                record["api_units"] = actual_units
                record["approved_max_api_units"] = operation["max_api_units"]
                if actual_units > operation["max_api_units"] or used_units > pack["max_api_units"]:
                    record["status"] = "api_units_bound_exceeded"
                    statuses[operation["id"]] = record["status"]
                    break
                if _is_partial(payload):
                    record["status"] = "partial"
                    statuses[operation["id"]] = record["status"]
                    break
                after = reader(operation["readback"], prepared.token, pack["client_login"], pack["environment"])
                _atomic_json(evidence / f"after-{index:03d}.json", after)
                matches = _contains(after, operation["expected_after"])
                _atomic_json(
                    evidence / f"diff-{index:03d}.json",
                    {
                        "status": "match" if matches else "mismatch",
                        "expected_after": operation["expected_after"],
                        "actual_after": after,
                    },
                )
                if not matches:
                    record["status"] = "readback_mismatch"
                    statuses[operation["id"]] = record["status"]
                    break
                record["status"] = "ready"
                statuses[operation["id"]] = "ready"

            complete = len(statuses) == len(pack["operations"]) and all(value == "ready" for value in statuses.values())
            result["status"] = "complete" if complete else "incomplete"
            result["api_units"] = used_units
            result["reversal_available"] = bool(reversal["operations"])
            _atomic_json(evidence / "result.json", result)
            return result
        except Exception as exc:
            result["error"] = sanitize_error(exc, (prepared.token,))
            result["api_units"] = used_units
            _atomic_json(evidence / "result.json", result)
            return result
    finally:
        prepared.lock_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Проверить или применить подтверждённый пакет записи Директа")
    parser.add_argument("--pack", required=True)
    parser.add_argument("--pack-sha256", required=True)
    parser.add_argument("--apply", action="store_true", help="Без этого флага выполняется только проверка пакета")
    args = parser.parse_args()
    if any(item in {"--token", "--direct-token", "--write-token"} for item in sys.argv[1:]):
        parser.error("сырой токен в командной строке запрещён")
    try:
        prepared = prepare(Path(args.pack), Path(args.pack_sha256), apply=args.apply)
        if not args.apply:
            print("Пакет записи проверен; сетевых вызовов не было")
            return 0
        result = execute(prepared)
    except Exception as exc:
        print(f"Пакет отклонён: {sanitize_error(exc)}", file=sys.stderr)
        return 1
    print(f"Операция {result['run_id']}: {result['status']}")
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
