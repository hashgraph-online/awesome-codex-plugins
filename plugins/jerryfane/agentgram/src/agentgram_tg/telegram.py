"""Small Telegram Bot API client built on the Python standard library."""

from __future__ import annotations

from dataclasses import dataclass
import json
import mimetypes
from pathlib import Path
import re
from typing import Any
from urllib import error, request
import uuid


API_ROOT = "https://api.telegram.org"
TOKEN_RE = re.compile(r"^[0-9]+:[A-Za-z0-9_-]{20,}$")
MAX_DOCUMENT_BYTES = 50 * 1024 * 1024


class TelegramError(RuntimeError):
    """Raised when Telegram returns an error response or cannot be reached."""


@dataclass(frozen=True)
class TelegramClient:
    token: str
    api_root: str = API_ROOT
    timeout: float = 15.0

    def request(self, method: str, payload: dict[str, Any] | None = None) -> Any:
        token = self.token.strip()
        if not looks_like_token(token):
            raise TelegramError("Telegram bot token shape is invalid")
        payload = payload or {}
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            self.method_url(token, method),
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        return self._perform_request(req, token)

    def request_multipart(
        self,
        method: str,
        fields: dict[str, Any],
        file_field: str,
        file_path: Path,
    ) -> Any:
        token = self.token.strip()
        if not looks_like_token(token):
            raise TelegramError("Telegram bot token shape is invalid")
        body, content_type = encode_multipart_form(fields, file_field, file_path)
        req = request.Request(
            self.method_url(token, method),
            data=body,
            headers={"Content-Type": content_type},
            method="POST",
        )
        return self._perform_request(req, token)

    def method_url(self, token: str, method: str) -> str:
        return f"{self.api_root}/bot{token}/{method}"

    def _perform_request(self, req: request.Request, token: str) -> Any:
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            raw_error = exc.read().decode("utf-8", errors="replace")
            raise TelegramError(redact_token(_telegram_error_message(raw_error), token)) from exc
        except error.URLError as exc:
            raise TelegramError(redact_token(f"Telegram request failed: {exc.reason}", token)) from exc

        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise TelegramError("Telegram returned invalid JSON") from exc

        if not isinstance(decoded, dict):
            raise TelegramError("Telegram returned an unexpected JSON response")
        if not decoded.get("ok"):
            description = decoded.get("description") or "Telegram API request failed"
            raise TelegramError(redact_token(str(description), token))
        return decoded.get("result")

    def get_me(self) -> dict[str, Any]:
        result = self.request("getMe", {})
        if not isinstance(result, dict):
            raise TelegramError("Telegram getMe returned an unexpected result")
        return result

    def get_updates(self, limit: int = 20) -> list[dict[str, Any]]:
        result = self.request("getUpdates", {"limit": limit, "timeout": 0})
        if not isinstance(result, list):
            raise TelegramError("Telegram getUpdates returned an unexpected result")
        return result

    def send_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = self.request("sendMessage", payload)
        if not isinstance(result, dict):
            raise TelegramError("Telegram sendMessage returned an unexpected result")
        return result

    def send_document(self, payload: dict[str, Any], document_path: Path) -> dict[str, Any]:
        document_path = validate_document_path(document_path)
        result = self.request_multipart("sendDocument", payload, "document", document_path)
        if not isinstance(result, dict):
            raise TelegramError("Telegram sendDocument returned an unexpected result")
        return result


def validate_document_path(path: str | Path) -> Path:
    candidate = Path(path).expanduser()
    try:
        info = candidate.stat()
    except FileNotFoundError as exc:
        raise TelegramError(f"file does not exist: {candidate}") from exc
    except OSError as exc:
        raise TelegramError(f"cannot inspect file {candidate}: {exc}") from exc

    if not candidate.is_file():
        raise TelegramError(f"path is not a regular file: {candidate}")
    if info.st_size <= 0:
        raise TelegramError(f"file is empty: {candidate}")
    if info.st_size > MAX_DOCUMENT_BYTES:
        raise TelegramError(
            f"file is too large: {info.st_size} bytes; maximum is {MAX_DOCUMENT_BYTES} bytes"
        )
    try:
        with candidate.open("rb"):
            pass
    except OSError as exc:
        raise TelegramError(f"file is not readable: {candidate}: {exc}") from exc
    return candidate


def encode_multipart_form(
    fields: dict[str, Any],
    file_field: str,
    file_path: Path,
    *,
    boundary: str | None = None,
) -> tuple[bytes, str]:
    boundary = boundary or f"agentgram-{uuid.uuid4().hex}"
    filename = file_path.name
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    parts: list[bytes] = []

    for name, value in fields.items():
        if value is None:
            continue
        parts.extend(
            [
                f"--{boundary}\r\n".encode("ascii"),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"),
                multipart_field_value(value).encode("utf-8"),
                b"\r\n",
            ]
        )

    parts.extend(
        [
            f"--{boundary}\r\n".encode("ascii"),
            (
                f'Content-Disposition: form-data; name="{file_field}"; '
                f'filename="{escape_multipart_filename(filename)}"\r\n'
            ).encode("utf-8"),
            f"Content-Type: {content_type}\r\n\r\n".encode("ascii"),
            read_file_bytes(file_path),
            b"\r\n",
            f"--{boundary}--\r\n".encode("ascii"),
        ]
    )
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def read_file_bytes(file_path: Path) -> bytes:
    try:
        return file_path.read_bytes()
    except OSError as exc:
        raise TelegramError(f"cannot read file {file_path}: {exc}") from exc


def multipart_field_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, separators=(",", ":"))
    return str(value)


def escape_multipart_filename(filename: str) -> str:
    return filename.replace("\\", "\\\\").replace('"', '\\"').replace("\r", "_").replace("\n", "_")


def looks_like_token(value: str) -> bool:
    return bool(TOKEN_RE.match(value.strip()))


def redact_token(message: str, token: str | None) -> str:
    if not token:
        return message
    return message.replace(token, "<redacted>")


def _telegram_error_message(raw: str) -> str:
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError:
        return raw or "Telegram API request failed"
    if isinstance(decoded, dict):
        return str(decoded.get("description") or decoded.get("error_code") or "Telegram API request failed")
    return raw or "Telegram API request failed"
