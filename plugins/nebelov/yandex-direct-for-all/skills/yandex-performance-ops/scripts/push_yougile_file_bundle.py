#!/usr/bin/env python3
"""Проверить или отправить заранее подтверждённый набор файлов в чат YouGile."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_HOST = "https://ru.yougile.com/api-v2"
ACTION = "push_yougile_file_bundle"
CHAR_LIMIT = 24000


class GateError(RuntimeError):
    """Набор или разрешение не прошли проверку."""


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


def parse_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GateError("expires_at должен иметь формат ISO 8601") from exc
    if parsed.tzinfo is None:
        raise GateError("expires_at должен содержать часовой пояс")
    return parsed.astimezone(timezone.utc)


def guess_lang(path: Path) -> str:
    return {
        ".md": "markdown", ".json": "json", ".tsv": "tsv", ".txt": "text",
        ".py": "python", ".sh": "bash", ".yaml": "yaml", ".yml": "yaml",
    }.get(path.suffix.lower(), "")


def make_chunks(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    language = guess_lang(path)
    header = f"[Материал] {path.name}\n\n"
    fence_open = f"```{language}\n" if language else "```\n"
    if len(header) + len(fence_open) + len(text) + 5 <= CHAR_LIMIT:
        return [f"{header}{fence_open}{text}\n```"]
    chunks: list[str] = []
    buffer: list[str] = []
    size = 0
    part = 1
    for line in text.splitlines():
        extra = len(line) + 1
        if buffer and size + extra + len(header) + len(fence_open) + 80 > CHAR_LIMIT:
            chunks.append(f"{header}(часть {part})\n{fence_open}{chr(10).join(buffer)}\n```")
            buffer = []
            size = 0
            part += 1
        buffer.append(line)
        size += extra
    if buffer:
        chunks.append(f"{header}(часть {part})\n{fence_open}{chr(10).join(buffer)}\n```")
    return chunks


def validate_bundle(bundle_path: Path, bundle: dict[str, Any]) -> tuple[str, str, list[tuple[Path, list[str]]]]:
    target_ref = required_text(bundle.get("target_ref"), "target_ref")
    chat_id = required_text(bundle.get("chat_id"), "chat_id")
    files = bundle.get("files")
    if not isinstance(files, list) or not files:
        raise GateError("files должен быть непустым списком")
    prepared: list[tuple[Path, list[str]]] = []
    seen: set[Path] = set()
    for index, entry in enumerate(files):
        if not isinstance(entry, dict):
            raise GateError(f"files[{index}] должен быть объектом")
        raw_path = required_text(entry.get("path"), f"files[{index}].path")
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = bundle_path.parent / path
        path = path.resolve()
        if path in seen or not path.is_file():
            raise GateError(f"Файл отсутствует или повторяется: {path}")
        seen.add(path)
        expected = required_text(entry.get("sha256"), f"files[{index}].sha256")
        if sha256_file(path) != expected:
            raise GateError(f"Файл изменился после составления набора: {path.name}")
        chunks = make_chunks(path)
        if not chunks:
            raise GateError(f"Пустой файл нельзя отправить: {path.name}")
        prepared.append((path, chunks))
    return target_ref, chat_id, prepared


def authorize(bundle_path: Path, target_ref: str, approval_path: Path) -> str:
    if os.environ.get("YOUGILE_WRITE_ARMED") != "1":
        raise GateError("Для записи требуется YOUGILE_WRITE_ARMED=1")
    api_key = os.environ.get("YOUGILE_WRITE_API_KEY", "").strip()
    if not api_key or any(character.isspace() for character in api_key):
        raise GateError("Для записи требуется отдельная переменная YOUGILE_WRITE_API_KEY")
    approval = load_json(approval_path, private=True)
    if approval.get("approved") is not True:
        raise GateError("Отправка не подтверждена")
    if approval.get("action") != ACTION or approval.get("target_ref") != target_ref:
        raise GateError("Разрешение относится к другому действию или месту назначения")
    if approval.get("spec_sha256") != sha256_file(bundle_path):
        raise GateError("Набор изменился после подтверждения")
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


def apply_bundle(host: str, api_key: str, chat_id: str, prepared: list[tuple[Path, list[str]]], evidence_dir: Path) -> int:
    encoded_chat = urllib.parse.quote(chat_id, safe="")
    before = api_request(host, api_key, "GET", f"chats/{encoded_chat}/messages?limit=100")
    write_private_json(evidence_dir / "before.json", before)
    sent: list[dict[str, Any]] = []
    reversal = {"manual_action_required": "Удаление сообщений не предусмотрено опубликованной схемой REST API", "messages": sent}
    write_private_json(evidence_dir / "reversal-candidate.json", reversal)
    for path, chunks in prepared:
        for part, text in enumerate(chunks, start=1):
            created = api_request(host, api_key, "POST", f"chats/{encoded_chat}/messages", {"text": text})
            message_id = created.get("id")
            if not isinstance(message_id, (int, str)) or isinstance(message_id, bool):
                raise RuntimeError("YouGile не вернул номер созданного сообщения")
            sent.append({"file": str(path), "part": part, "message_id": message_id})
            write_private_json(evidence_dir / "reversal-candidate.json", reversal)
            readback = api_request(host, api_key, "GET", f"chats/{encoded_chat}/messages/{message_id}")
            if readback.get("id") != message_id or readback.get("text") != text:
                raise RuntimeError(f"Контрольное чтение не подтвердило материал {path.name}, часть {part}")
    after = api_request(host, api_key, "GET", f"chats/{encoded_chat}/messages?limit=100")
    write_private_json(evidence_dir / "after.json", after)
    write_private_json(evidence_dir / "readback.json", {"messages": sent})
    write_private_json(evidence_dir / "diff.json", {"sent_count": len(sent), "messages": sent})
    return len(sent)


def main() -> int:
    parser = argparse.ArgumentParser(description="Безопасная отправка набора файлов в YouGile")
    parser.add_argument("--bundle", required=True, help="Закрытое описание набора с правами 0600")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--approval", help="Закрытый JSON-файл разрешения с правами 0600")
    parser.add_argument("--evidence-dir", help="Закрытая папка доказательств")
    parser.add_argument("--host", default=os.environ.get("YOUGILE_API_HOST_URL", DEFAULT_HOST))
    args = parser.parse_args()
    try:
        bundle_path = Path(args.bundle).expanduser().resolve()
        bundle = load_json(bundle_path, private=True)
        target_ref, chat_id, prepared = validate_bundle(bundle_path, bundle)
        chunk_count = sum(len(chunks) for _, chunks in prepared)
        names = ", ".join(path.name for path, _ in prepared)
        print(f"Проверено локально для «{target_ref}»: файлов {len(prepared)}, сообщений {chunk_count}: {names}")
        print(f"Контрольная сумма набора: {sha256_file(bundle_path)}")
        if not args.apply:
            print("Отправка не выполнялась. Для применения нужны --apply, разрешение, вооружение и отдельный ключ записи.")
            return 0
        if not args.approval or not args.evidence_dir:
            raise GateError("Для применения обязательны --approval и --evidence-dir")
        api_key = authorize(bundle_path, target_ref, Path(args.approval).expanduser().resolve())
        evidence_dir = Path(args.evidence_dir).expanduser().resolve()
        sent_count = apply_bundle(args.host, api_key, chat_id, prepared, evidence_dir)
        print(f"Отправка подтверждена контрольным чтением: сообщений {sent_count}.")
        print(f"Закрытые доказательства: {evidence_dir}")
        return 0
    except (GateError, RuntimeError, OSError, KeyError, TypeError, ValueError, UnicodeError) as exc:
        print(f"Отклонено: {exc}", file=os.sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
