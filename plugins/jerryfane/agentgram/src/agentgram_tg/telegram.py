"""Small Telegram Bot API client built on the Python standard library."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import http.client
import json
import mimetypes
import os
from pathlib import Path
import re
from typing import Any
from urllib import error, request
from urllib.parse import quote
import uuid


API_ROOT = "https://api.telegram.org"
TOKEN_RE = re.compile(r"^[0-9]+:[A-Za-z0-9_-]{20,}$")
MAX_DOCUMENT_BYTES = 50 * 1024 * 1024
MAX_DOWNLOAD_BYTES = 20 * 1024 * 1024


class TelegramError(RuntimeError):
    """Raised when Telegram returns an error response or cannot be reached."""


@dataclass(frozen=True)
class TelegramClient:
    token: str
    api_root: str = API_ROOT
    timeout: float = 15.0

    def request(
        self,
        method: str,
        payload: dict[str, Any] | None = None,
        *,
        timeout: float | None = None,
    ) -> Any:
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
        return self._perform_request(req, token, timeout=timeout)

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

    def file_url(self, token: str, file_path: str) -> str:
        clean_path = validate_file_path(file_path)
        return f"{self.api_root.rstrip('/')}/file/bot{token}/{quote(clean_path, safe='/')}"

    def _perform_request(self, req: request.Request, token: str, *, timeout: float | None = None) -> Any:
        try:
            with request.urlopen(req, timeout=self.timeout if timeout is None else timeout) as response:
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

    def get_updates(
        self,
        limit: int = 20,
        *,
        offset: int | None = None,
        timeout: int = 0,
        allowed_updates: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        update_timeout = validate_update_timeout(timeout)
        payload: dict[str, Any] = {"limit": validate_update_limit(limit), "timeout": update_timeout}
        if offset is not None:
            payload["offset"] = offset
        if allowed_updates is not None:
            payload["allowed_updates"] = validate_allowed_updates(allowed_updates)
        result = self.request("getUpdates", payload, timeout=max(self.timeout, float(update_timeout) + 5.0))
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

    def get_file(self, file_id: str) -> dict[str, Any]:
        file_id = validate_file_id(file_id)
        result = self.request("getFile", {"file_id": file_id})
        if not isinstance(result, dict):
            raise TelegramError("Telegram getFile returned an unexpected result")
        returned_file_id = result.get("file_id")
        if not isinstance(returned_file_id, str) or not returned_file_id.strip():
            raise TelegramError("Telegram getFile returned an invalid file_id")
        file_unique_id = result.get("file_unique_id")
        if file_unique_id is not None and not isinstance(file_unique_id, str):
            raise TelegramError("Telegram getFile returned an invalid file_unique_id")
        file_size = result.get("file_size")
        if file_size is not None and (isinstance(file_size, bool) or not isinstance(file_size, int) or file_size < 0):
            raise TelegramError("Telegram getFile returned an invalid file_size")
        file_path = result.get("file_path")
        if file_path is not None:
            validate_file_path(file_path)
        return result

    def download_file(
        self,
        file_path: str,
        destination: Path,
        *,
        expected_size: int | None = None,
        max_bytes: int = MAX_DOWNLOAD_BYTES,
    ) -> dict[str, Any]:
        token = self.token.strip()
        if not looks_like_token(token):
            raise TelegramError("Telegram bot token shape is invalid")
        clean_path = validate_file_path(file_path)
        destination = validate_download_destination(destination)
        max_bytes = validate_max_download_bytes(max_bytes)
        if expected_size is not None:
            expected_size = validate_expected_file_size(expected_size)
            if expected_size > max_bytes:
                raise TelegramError(f"file is too large: {expected_size} bytes; maximum is {max_bytes} bytes")

        req = request.Request(self.file_url(token, clean_path), method="GET")
        hasher = hashlib.sha256()
        total = 0
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        try:
            fd = os.open(destination, flags, 0o600)
        except FileExistsError as exc:
            raise TelegramError(f"refusing to overwrite existing file: {destination}") from exc
        except OSError as exc:
            raise TelegramError(f"cannot create download file {destination}: {exc}") from exc

        try:
            with os.fdopen(fd, "wb") as output:
                try:
                    with request.urlopen(req, timeout=self.timeout) as response:
                        while True:
                            chunk = response.read(1024 * 64)
                            if not chunk:
                                break
                            total += len(chunk)
                            if total > max_bytes:
                                raise TelegramError(
                                    f"file is too large: more than {max_bytes} bytes; maximum is {max_bytes} bytes"
                                )
                            output.write(chunk)
                            hasher.update(chunk)
                except TelegramError:
                    raise
                except error.HTTPError as exc:
                    raw_error = exc.read().decode("utf-8", errors="replace")
                    raise TelegramError(redact_token(_telegram_error_message(raw_error), token)) from exc
                except error.URLError as exc:
                    raise TelegramError(redact_token(f"Telegram file download failed: {exc.reason}", token)) from exc
                except (http.client.IncompleteRead, OSError, TimeoutError) as exc:
                    raise TelegramError(redact_token(f"Telegram file download failed: {exc}", token)) from exc
                try:
                    output.flush()
                    os.fsync(output.fileno())
                except OSError as exc:
                    raise TelegramError(f"cannot flush download file {destination}: {exc}") from exc
        except Exception:
            remove_partial_download(destination)
            raise

        if expected_size is not None and total != expected_size:
            remove_partial_download(destination)
            raise TelegramError(f"downloaded file size mismatch: expected {expected_size} bytes, got {total} bytes")
        return {"path": str(destination), "bytes": total, "sha256": hasher.hexdigest()}


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


def validate_file_id(file_id: str) -> str:
    if not isinstance(file_id, str) or not file_id.strip():
        raise TelegramError("Telegram file_id is required")
    return file_id.strip()


def validate_file_path(file_path: str) -> str:
    if not isinstance(file_path, str) or not file_path.strip():
        raise TelegramError("Telegram file_path is required")
    clean_path = file_path.strip().lstrip("/")
    if not clean_path or "\x00" in clean_path:
        raise TelegramError("Telegram file_path is invalid")
    parts = clean_path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise TelegramError("Telegram file_path is invalid")
    return clean_path


def validate_download_destination(path: str | Path) -> Path:
    destination = Path(path).expanduser()
    parent = destination.parent
    if not parent.exists() or not parent.is_dir():
        raise TelegramError(f"download parent directory does not exist: {parent}")
    if destination.exists():
        raise TelegramError(f"refusing to overwrite existing file: {destination}")
    return destination


def validate_max_download_bytes(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise TelegramError("max download bytes must be a positive integer")
    if value > MAX_DOWNLOAD_BYTES:
        raise TelegramError(f"max download bytes cannot exceed {MAX_DOWNLOAD_BYTES} bytes")
    return value


def validate_expected_file_size(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise TelegramError("expected file size must be a non-negative integer")
    return value


def remove_partial_download(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        return
    except OSError:
        return


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


def validate_update_limit(limit: int) -> int:
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise TelegramError("Telegram getUpdates limit must be an integer from 1 to 100")
    if limit < 1 or limit > 100:
        raise TelegramError("Telegram getUpdates limit must be from 1 to 100")
    return limit


def validate_update_timeout(timeout: int) -> int:
    if isinstance(timeout, bool) or not isinstance(timeout, int):
        raise TelegramError("Telegram getUpdates timeout must be a non-negative integer")
    if timeout < 0:
        raise TelegramError("Telegram getUpdates timeout must be a non-negative integer")
    return timeout


def validate_allowed_updates(allowed_updates: list[str]) -> list[str]:
    if not isinstance(allowed_updates, list):
        raise TelegramError("Telegram allowed_updates must be a list of strings")
    for update_type in allowed_updates:
        if not isinstance(update_type, str):
            raise TelegramError("Telegram allowed_updates must be a list of strings")
    return allowed_updates


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
