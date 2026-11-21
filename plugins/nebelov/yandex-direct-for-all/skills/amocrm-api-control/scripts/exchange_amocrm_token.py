#!/usr/bin/env python3
"""Обменять код или обновить токен amoCRM без секретов в аргументах."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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


def private_json(path: Path) -> dict[str, Any]:
    if not path.is_file() or stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise RuntimeError("Закрытый файл должен существовать и иметь права 0600")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("Закрытый файл должен содержать объект JSON")
    return value


def atomic_json(path: Path, value: dict[str, Any]) -> None:
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


def build_payload(integration: dict[str, Any], code_file: Path | None, token_file: Path, refresh: bool) -> dict[str, Any]:
    required = ["subdomain", "client_id", "client_secret", "redirect_uri"]
    if any(not str(integration.get(field) or "").strip() for field in required):
        raise RuntimeError("Файл интеграции неполный")
    payload = {field: integration[field] for field in ("client_id", "client_secret", "redirect_uri")}
    if refresh:
        current = private_json(token_file)
        token = str(current.get("refresh_token") or "").strip()
        if not token:
            raise RuntimeError("В файле токена нет refresh_token")
        payload.update({"grant_type": "refresh_token", "refresh_token": token})
    else:
        if code_file is None:
            raise RuntimeError("Для первого обмена нужен закрытый файл кода")
        code = str(private_json(code_file).get("authorization_code") or "").strip()
        if not code:
            raise RuntimeError("В закрытом файле отсутствует authorization_code")
        payload.update({"grant_type": "authorization_code", "code": code})
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--integration-file", required=True)
    parser.add_argument("--authorization-code-file")
    parser.add_argument("--token-file", required=True)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    forbidden = {"--client-id", "--client-secret", "--code", "--refresh-token"}
    if any(item in forbidden for item in os.sys.argv[1:]):
        parser.error("Секреты и коды в аргументах запрещены")
    integration = private_json(Path(args.integration_file).expanduser().resolve())
    token_file = Path(args.token_file).expanduser().resolve()
    code_file = Path(args.authorization_code_file).expanduser().resolve() if args.authorization_code_file else None
    if args.refresh and code_file is not None:
        parser.error("При обновлении файл кода не используется")
    payload = build_payload(integration, code_file, token_file, args.refresh)
    response = requests.post(f"https://{integration['subdomain']}.amocrm.ru/oauth2/access_token", json=payload)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict) or not data.get("access_token") or not data.get("refresh_token"):
        raise RuntimeError("amoCRM не вернула полный набор токенов")
    result = {
        "subdomain": integration["subdomain"],
        "base_url": f"https://{integration['subdomain']}.amocrm.ru",
        "client_id": integration["client_id"],
        "redirect_uri": integration["redirect_uri"],
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "token_type": data.get("token_type", "Bearer"),
        "expires_in": data.get("expires_in", 0),
        "server_time": data.get("server_time"),
        "obtained_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    atomic_json(token_file, result)
    if not args.refresh and code_file is not None:
        code_file.unlink(missing_ok=True)
    print(json.dumps({"ok": True, "token_file_updated": True}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
