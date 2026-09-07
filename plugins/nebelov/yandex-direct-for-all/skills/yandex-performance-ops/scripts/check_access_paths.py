#!/usr/bin/env python3
"""Безопасная основа чтения Яндекс.Директа и проверка локальных доступов.

Сырые токены не принимаются через командную строку. Настройки читаются из
переменных процесса или защищённого JSON-файла с правами только владельца.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

DIRECT_SERVICES = {
    "campaigns",
    "adgroups",
    "ads",
    "keywords",
    "negativekeywordsharedsets",
    "sitelinks",
    "adextensions",
    "bids",
    "keywordbids",
}
DIRECT_VERSIONS = {"v5", "v501"}


class AccessError(RuntimeError):
    """Ошибка доступа, безопасная для вывода пользователю."""


@dataclass(frozen=True)
class DirectAccess:
    token: str
    client_login: str
    environment: str


@dataclass(frozen=True)
class MetrikaAccess:
    token: str


@dataclass
class PageManifest:
    service: str
    result_key: str
    pages: int
    objects: int
    complete: bool
    checksum: str
    error: str = ""


@dataclass
class PageResult:
    rows: list[dict[str, Any]]
    manifest: PageManifest


class PageManifestStore:
    """Немедленно сохраняет доказательства каждой постраничной выгрузки."""

    def __init__(self, path: Path):
        self.path = path
        self.sources: dict[str, dict[str, Any]] = {}

    def add(self, name: str, result: PageResult) -> PageResult:
        if not name or name in self.sources:
            raise AccessError("Имя источника манифеста должно быть непустым и уникальным")
        self.sources[name] = asdict(result.manifest)
        atomic_write_json(
            self.path,
            {
                "complete": bool(self.sources) and all(item["complete"] for item in self.sources.values()),
                "source_count": len(self.sources),
                "sources": self.sources,
            },
        )
        return result


def sanitize_error(value: object, secrets: tuple[str, ...] = ()) -> str:
    text = str(value)
    for secret in secrets:
        if secret:
            text = text.replace(secret, "[СКРЫТО]")
    text = re.sub(r"(?i)(authorization\s*[:=]\s*)(?:bearer|oauth)?\s*[^\s,;]+", r"\1[СКРЫТО]", text)
    text = re.sub(r"(?i)(access_token|token|client_secret)(\s*[:=]\s*)[^\s,;\"']+", r"\1\2[СКРЫТО]", text)
    home = str(Path.home())
    if home and home != "/":
        text = text.replace(home, "~")
    text = re.sub(r"/(?:Users|home)/[^/\s]+", "~", text)
    return text[:800]


def _require_private_file(path: Path) -> None:
    if not path.is_file():
        raise AccessError("Защищённый файл доступа не найден")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        raise AccessError("Файл доступа должен иметь права 0600")


def _read_private_json(path: Path) -> dict[str, Any]:
    _require_private_file(path)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AccessError(sanitize_error(exc)) from exc
    if not isinstance(value, dict):
        raise AccessError("Файл доступа должен содержать объект JSON")
    return value


def _token_from_file(path_value: str) -> str:
    data = _read_private_json(Path(path_value).expanduser())
    token = str(data.get("access_token") or data.get("token") or "").strip()
    if not token:
        raise AccessError("В защищённом файле нет access_token")
    return token


def load_direct_access(access_file: str | None = None) -> DirectAccess:
    config: dict[str, Any] = {}
    configured = access_file or os.environ.get("YANDEX_DIRECT_ACCESS_FILE", "").strip()
    if configured:
        config = _read_private_json(Path(configured).expanduser())

    environment = str(config.get("environment") or os.environ.get("YANDEX_DIRECT_ENVIRONMENT") or "sandbox").strip().lower()
    if environment not in {"sandbox", "production"}:
        raise AccessError("YANDEX_DIRECT_ENVIRONMENT допускает только sandbox или production")

    token = str(config.get("access_token") or "").strip()
    token_file = str(config.get("token_file") or "").strip()
    if not token and token_file:
        token = _token_from_file(token_file)
    expected_env = "YANDEX_DIRECT_SANDBOX_TOKEN" if environment == "sandbox" else "YANDEX_DIRECT_PRODUCTION_READ_TOKEN"
    if not token:
        token = os.environ.get(expected_env, "").strip()
    if not token:
        raise AccessError(f"Для выбранной среды отсутствует {expected_env}")

    client_login = str(config.get("client_login") or os.environ.get("YANDEX_DIRECT_CLIENT_LOGIN") or "").strip()
    if not client_login:
        raise AccessError("Не задан client_login или YANDEX_DIRECT_CLIENT_LOGIN: чтение без явной области клиента запрещено")
    return DirectAccess(token=token, client_login=client_login, environment=environment)


def load_metrika_access(access_file: str | None = None) -> MetrikaAccess:
    configured = access_file or os.environ.get("YANDEX_METRIKA_ACCESS_FILE", "").strip()
    token = ""
    if configured:
        config = _read_private_json(Path(configured).expanduser())
        token = str(config.get("access_token") or "").strip()
        token_file = str(config.get("token_file") or "").strip()
        if not token and token_file:
            token = _token_from_file(token_file)
    if not token:
        token = os.environ.get("YANDEX_METRIKA_TOKEN", "").strip()
    if not token:
        raise AccessError("Не задан защищённый доступ Метрики")
    return MetrikaAccess(token=token)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
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


def atomic_write_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _header(headers: Any, name: str, default: str = "") -> str:
    if headers is None:
        return default
    for key, value in headers.items():
        if str(key).lower() == name.lower():
            return str(value)
    return default


def _report_http(url: str, headers: dict[str, str], body: bytes) -> tuple[int, bytes, Any]:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, response.read(), response.headers
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), exc.headers


def fetch_direct_report(
    access: DirectAccess,
    params: dict[str, Any],
    output_dir: Path,
    *,
    requester: Callable[[str, dict[str, str], bytes], tuple[int, bytes, Any]] = _report_http,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Получить Reports API с сохраняемым договором запроса, очереди и результата."""
    if not access.client_login.strip():
        raise AccessError("Reports API запрещён без явной области клиента")
    body = _canonical_bytes({"params": params})
    request_sha256 = hashlib.sha256(body).hexdigest()
    output_dir = output_dir.expanduser().resolve()
    request_path = output_dir / f"_api_reports_{request_sha256}.request.json"
    state_path = output_dir / f"_api_reports_{request_sha256}.state.json"
    artifact_path = output_dir / f"_api_reports_{request_sha256}.tsv"
    atomic_write_bytes(request_path, body)
    host = "api-sandbox.direct.yandex.com" if access.environment == "sandbox" else "api.direct.yandex.com"
    headers = {
        "Authorization": f"Bearer {access.token}",
        "Accept-Language": "ru",
        "Content-Type": "application/json; charset=utf-8",
        "processingMode": "auto",
        "returnMoneyInMicros": "false",
        "skipReportHeader": "true",
        "skipColumnHeader": "false",
        "skipReportSummary": "true",
    }
    headers["Client-Login"] = access.client_login
    url = f"https://{host}/json/v5/reports"
    while True:
        try:
            status, payload, response_headers = requester(url, headers, body)
        except Exception as exc:
            state = {
                "status": "error",
                "request_sha256": request_sha256,
                "request_artifact": request_path.name,
                "error": sanitize_error(exc, (access.token,)),
            }
            atomic_write_json(state_path, state)
            return state
        request_id = _header(response_headers, "RequestId")
        if status == 200 and payload:
            atomic_write_bytes(artifact_path, payload)
            state = {
                "status": "ready",
                "request_sha256": request_sha256,
                "request_artifact": request_path.name,
                "request_id": request_id,
                "artifact_path": str(artifact_path),
                "artifact_sha256": hashlib.sha256(payload).hexdigest(),
                "bytes": len(payload),
            }
            atomic_write_json(state_path, state)
            return state
        if status == 200:
            state = {
                "status": "error",
                "request_sha256": request_sha256,
                "request_artifact": request_path.name,
                "request_id": request_id,
                "http_status": status,
                "error": "empty_report",
            }
            atomic_write_json(state_path, state)
            return state
        if status in {201, 202}:
            retry_raw = _header(response_headers, "retryIn", "1")
            try:
                retry_in = max(float(retry_raw), 0.0)
            except ValueError:
                retry_in = 1.0
            state = {
                "status": "queued" if status == 201 else "pending",
                "request_sha256": request_sha256,
                "request_artifact": request_path.name,
                "request_id": request_id,
                "retry_in": retry_in,
                "reports_in_queue": _header(response_headers, "reportsInQueue"),
            }
            atomic_write_json(state_path, state)
            sleeper(retry_in)
            continue
        state = {
            "status": "error",
            "request_sha256": request_sha256,
            "request_artifact": request_path.name,
            "request_id": request_id,
            "http_status": status,
            "error": sanitize_error(payload.decode("utf-8", errors="replace"), (access.token,)),
        }
        atomic_write_json(state_path, state)
        return state


def direct_api_get(
    access: DirectAccess,
    service: str,
    params: dict[str, Any],
    *,
    version: str = "v5",
) -> dict[str, Any]:
    service = service.lower()
    if not access.client_login.strip():
        raise AccessError("Чтение Директа запрещено без явной области клиента")
    if service not in DIRECT_SERVICES or version not in DIRECT_VERSIONS:
        raise AccessError("Запрошен неподдерживаемый маршрут чтения Директа")
    host = "api-sandbox.direct.yandex.com" if access.environment == "sandbox" else "api.direct.yandex.com"
    body = _canonical_bytes({"method": "get", "params": params})
    headers = {
        "Authorization": f"Bearer {access.token}",
        "Accept-Language": "ru",
        "Content-Type": "application/json; charset=utf-8",
    }
    headers["Client-Login"] = access.client_login
    request = urllib.request.Request(
        f"https://{host}/json/{version}/{service}",
        data=body,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise AccessError(sanitize_error(f"{service}.get: HTTP {exc.code}: {raw}", (access.token,))) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise AccessError(sanitize_error(f"{service}.get: {exc}", (access.token,))) from exc
    if not isinstance(payload, dict):
        raise AccessError(f"{service}.get вернул неожиданный ответ")
    if payload.get("error"):
        raise AccessError(sanitize_error(f"{service}.get: {payload['error']}", (access.token,)))
    return payload


def metrika_get(access: MetrikaAccess, path: str, query: dict[str, Any] | None = None) -> dict[str, Any]:
    encoded = urllib.parse.urlencode(query or {}, doseq=True)
    url = f"https://api-metrika.yandex.net/{path.lstrip('/')}"
    if encoded:
        url += f"?{encoded}"
    request = urllib.request.Request(url, headers={"Authorization": f"OAuth {access.token}", "Accept-Language": "ru"})
    try:
        with urllib.request.urlopen(request) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise AccessError(sanitize_error(f"Метрика: HTTP {exc.code}: {raw}", (access.token,))) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise AccessError(sanitize_error(f"Метрика: {exc}", (access.token,))) from exc
    if not isinstance(payload, dict):
        raise AccessError("Метрика вернула неожиданный ответ")
    return payload


def fetch_direct_pages(
    access: DirectAccess,
    service: str,
    params: dict[str, Any],
    result_key: str,
    *,
    version: str = "v5",
    limit: int = 10_000,
    requester: Callable[[DirectAccess, str, dict[str, Any]], dict[str, Any]] | None = None,
) -> PageResult:
    rows: list[dict[str, Any]] = []
    seen_page_hashes: set[str] = set()
    seen_offsets: set[int] = set()
    offset = 0
    pages = 0
    complete = False
    error = ""
    call = requester or (lambda current, name, page: direct_api_get(current, name, page, version=version))

    while True:
        page_params = json.loads(json.dumps(params, ensure_ascii=False))
        page_params["Page"] = {"Limit": limit, "Offset": offset}
        try:
            payload = call(access, service, page_params)
            result = payload.get("result") or {}
            page_rows = result.get(result_key) or []
            if not isinstance(page_rows, list):
                raise AccessError(f"{service}.get: поле {result_key} не является списком")
            page_hash = hashlib.sha256(_canonical_bytes(page_rows)).hexdigest()
            if page_rows and page_hash in seen_page_hashes:
                raise AccessError(f"{service}.get: обнаружен повтор страницы")
            seen_page_hashes.add(page_hash)
            pages += 1
            rows.extend(item for item in page_rows if isinstance(item, dict))
            limited_by = result.get("LimitedBy")
            if limited_by in (None, "") or not page_rows:
                complete = True
                break
            next_offset = int(limited_by)
            if next_offset <= offset or next_offset in seen_offsets:
                raise AccessError(f"{service}.get: постраничный указатель повторился")
            seen_offsets.add(offset)
            offset = next_offset
        except Exception as exc:  # манифест обязан сохранить частичный результат
            error = sanitize_error(exc, (access.token,))
            break

    checksum = hashlib.sha256(_canonical_bytes(rows)).hexdigest()
    return PageResult(
        rows=rows,
        manifest=PageManifest(
            service=service,
            result_key=result_key,
            pages=pages,
            objects=len(rows),
            complete=complete,
            checksum=checksum,
            error=error,
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Проверить защищённый доступ чтения Яндекс.Директа")
    parser.add_argument("--access-file", help="Защищённый JSON-файл; сырой токен не принимается")
    parser.add_argument("--output", help="Необязательный защищённый JSON с обезличенным итогом")
    args = parser.parse_args()
    if any(item in {"--token", "--direct-token"} for item in os.sys.argv[1:]):
        parser.error("сырой токен в командной строке запрещён")
    try:
        access = load_direct_access(args.access_file)
        result = fetch_direct_pages(
            access,
            "campaigns",
            {"SelectionCriteria": {}, "FieldNames": ["Id"]},
            "Campaigns",
            limit=1,
        )
        summary = {
            "service": "direct",
            "environment": access.environment,
            "readable": result.manifest.complete,
            "pages": result.manifest.pages,
            "objects_seen": result.manifest.objects,
            "error": result.manifest.error,
        }
        if args.output:
            atomic_write_json(Path(args.output), summary)
        print("Доступ Директа подтверждён" if summary["readable"] else "Доступ Директа не подтверждён")
        return 0 if summary["readable"] else 1
    except Exception as exc:
        print(f"Доступ Директа не подтверждён: {sanitize_error(exc)}", file=os.sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
