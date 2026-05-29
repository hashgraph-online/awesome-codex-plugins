"""Small Telegram Bot API client built on the Python standard library."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any
from urllib import error, request


API_ROOT = "https://api.telegram.org"
TOKEN_RE = re.compile(r"^[0-9]+:[A-Za-z0-9_-]{20,}$")


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
        url = f"{self.api_root}/bot{token}/{method}"
        req = request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
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

        if not decoded.get("ok"):
            description = decoded.get("description") or "Telegram API request failed"
            raise TelegramError(redact_token(str(description), token))
        return decoded.get("result")

    def get_me(self) -> dict[str, Any]:
        return self.request("getMe", {})

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
    return str(decoded.get("description") or decoded.get("error_code") or "Telegram API request failed")
