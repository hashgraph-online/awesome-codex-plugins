"""Two transports with one interface: `call(method, params) -> result`.

* FakeTransport - offline. Records every call *after a JSON round trip*, so a
  test sees exactly what would go on the wire (a field an SDK would silently
  drop cannot hide here). Responses are scripted per method.
* HttpTransport - live, standard library only. Enabled explicitly through
  `live_transport_from_env()`; never used by tests.

Neither prints the bot token. Live mode is for a dedicated TEST bot only.
"""
from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.request
from collections import defaultdict, deque
from typing import Any, Callable

from .errors import OutcomeUnknown, TelegramError, from_response

Responder = Callable[[str, dict[str, Any]], Any]


class FakeTransport:
    """Offline transport. Script results with `script(method, *results)`.

    A scripted result can be:
      * any JSON value -> returned as `result`
      * {"ok": False, "error_code": ..., "description": ..., "parameters": {...}}
        -> raised as TelegramError
      * the string "TIMEOUT" -> raised as OutcomeUnknown (the request is
        recorded first: it reached the server, the answer was lost)
      * a callable(method, params) -> its return value is used
    Unscripted calls return a plausible default (True, or a Message for send*).
    """

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self._scripts: dict[str, deque] = defaultdict(deque)
        self._next_message_id = 1000

    def script(self, method: str, *results: Any) -> "FakeTransport":
        self._scripts[method].extend(results)
        return self

    def call(self, method: str, params: dict[str, Any]) -> Any:
        wire = json.loads(json.dumps(params, ensure_ascii=False))
        self.calls.append((method, wire))
        queue = self._scripts.get(method)
        result = queue.popleft() if queue else self._default(method, wire)
        if callable(result):
            result = result(method, wire)
        if result == "TIMEOUT":
            raise OutcomeUnknown(method)
        if isinstance(result, dict) and result.get("ok") is False:
            raise from_response(method, result)
        return result

    def methods(self) -> list[str]:
        return [m for m, _ in self.calls]

    def params_of(self, method: str) -> list[dict[str, Any]]:
        return [p for m, p in self.calls if m == method]

    def _default(self, method: str, params: dict[str, Any]) -> Any:
        if method == "sendMediaGroup":          # real API: an array of Messages
            first = self._next_message_id + 1
            self._next_message_id += len(params.get("media") or [None])
            return [{"message_id": i, "date": 0, "chat": {"id": params.get("chat_id")}}
                    for i in range(first, self._next_message_id + 1)]
        if method == "copyMessage":             # real API: a MessageId object
            self._next_message_id += 1
            return {"message_id": self._next_message_id}
        if method.startswith("send") and "Draft" not in method:
            self._next_message_id += 1
            chat_id = params.get("chat_id")
            msg: dict[str, Any] = {
                "message_id": self._next_message_id,
                "date": 0,
                "chat": {"id": chat_id, "type": "private" if isinstance(chat_id, int) and chat_id > 0 else "supergroup"},
            }
            eph = params.get("ephemeral_message_parameters")
            if eph:
                msg["message_id"] = 0
                msg["ephemeral_message_id"] = self._next_message_id
                if eph.get("receiver_user_id"):
                    msg["receiver_user"] = {"id": eph["receiver_user_id"], "is_bot": False, "first_name": "User"}
            if method == "sendWidget":
                msg["widget"] = {"html": params["html"]}
                if params.get("is_shared"):
                    msg["widget"]["id"] = "77700" + str(self._next_message_id)
            if "message_thread_id" in params:
                msg["message_thread_id"] = params["message_thread_id"]
            return msg
        return True


class HttpTransport:
    """Minimal live transport over urllib (JSON bodies, no file uploads)."""

    def __init__(self, token: str, *, test_environment: bool = False,
                 base_url: str = "https://api.telegram.org", timeout: float = 30.0):
        self._token = token
        self._prefix = f"{base_url}/bot{token}/" + ("test/" if test_environment else "")
        self._timeout = timeout

    def __repr__(self) -> str:  # keep the token out of logs and tracebacks
        return "HttpTransport(<token hidden>)"

    def call(self, method: str, params: dict[str, Any]) -> Any:
        body = json.dumps(params, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(self._prefix + method, data=body,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            try:
                payload = json.loads(err.read().decode("utf-8"))
            except ValueError:
                payload = {"ok": False, "error_code": err.code, "description": err.reason}
        except (socket.timeout, TimeoutError, ConnectionResetError) as err:
            # The body may already have been processed by the server.
            raise OutcomeUnknown(method, type(err).__name__) from None
        except urllib.error.URLError as err:
            if isinstance(err.reason, (socket.timeout, TimeoutError)):
                raise OutcomeUnknown(method, "timeout") from None
            raise
        if not payload.get("ok"):
            raise from_response(method, payload)
        return payload.get("result")


def live_transport_from_env() -> HttpTransport | None:
    """Return a live transport only when explicitly enabled.

    TELEGRAM_LIVE=1 and TELEGRAM_TEST_BOT_TOKEN must both be set. Set
    TELEGRAM_TEST_ENV=1 to talk to Telegram's test server (required for the
    group / inline / forward widget scenarios).
    """
    if os.environ.get("TELEGRAM_LIVE") != "1":
        return None
    token = os.environ.get("TELEGRAM_TEST_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_LIVE=1 needs TELEGRAM_TEST_BOT_TOKEN (a test bot).")
    return HttpTransport(token, test_environment=os.environ.get("TELEGRAM_TEST_ENV") == "1")


def TelegramErrorResponse(code: int, description: str, retry_after: float | None = None) -> dict[str, Any]:
    """Helper for scripting FakeTransport errors."""
    body: dict[str, Any] = {"ok": False, "error_code": code, "description": description}
    if retry_after is not None:
        body["parameters"] = {"retry_after": retry_after}
    return body


__all__ = ["FakeTransport", "HttpTransport", "live_transport_from_env",
           "TelegramErrorResponse", "TelegramError", "OutcomeUnknown"]
