"""The bot side of a Mini App: launch points, results back to the chat, follow-up messages.

Standard library only. `transport` is anything with `.call(method, params)` (tgkit's FakeTransport offline,
HttpTransport with a TEST token from the environment for a live check). Every method here is a plain Bot API
call; references/mini-apps-bridge.md has the bot-side reference, references/mini-apps/ the app side.

Invariants this module keeps:
* a `query_id` is answered once (answerWebAppQuery), a replay is refused;
* the bot writes first only after `write_access_allowed` (or the user started the bot);
* `start_param` and `web_app_data` are untrusted text: allowlist-parsed, size-limited;
* prices are computed here from item ids, never taken from the client;
* a join-request query is answered within Telegram's 10 seconds (open the app or decide).
"""
from __future__ import annotations

import json
import re
import time
from typing import Any, Callable, Protocol

START_PARAM = re.compile(r"^[A-Za-z0-9_-]{1,512}$")


class Transport(Protocol):
    def call(self, method: str, params: dict[str, Any]) -> Any: ...


class MiniAppBot:
    def __init__(self, transport: Transport, *, bot_username: str, app_url: str, app_short_name: str | None = None,
                 clock: Callable[[], float] = time.time):
        self.t = transport
        self.bot = bot_username.lstrip("@")
        self.app_url = app_url
        self.short_name = app_short_name
        self.clock = clock
        self.answered_queries: set[str] = set()
        self.write_allowed: set[int] = set()

    # ------------------------------------------------------------- launch points

    def link(self, start_param: str | None = None, *, mode: str | None = None) -> str:
        """Main Mini App (`t.me/<bot>?startapp`) or a named app (`t.me/<bot>/<app>?startapp`)."""
        if start_param is not None and not START_PARAM.fullmatch(start_param):
            raise ValueError("start_param: 1-512 characters of A-Z a-z 0-9 _ -")
        if mode not in (None, "compact", "fullscreen"):
            raise ValueError("mode: compact or fullscreen")
        base = f"https://t.me/{self.bot}/{self.short_name}" if self.short_name else f"https://t.me/{self.bot}"
        query = [f"startapp={start_param}" if start_param is not None else "startapp"]
        if mode:
            query.append(f"mode={mode}")
        return f"{base}?{'&'.join(query)}"

    def app_url_for(self, path: str = "") -> str:
        """The app URL plus a path, query or fragment. Anything else could change the host (`@evil.example`)."""
        if path and path[0] not in "/?#":
            raise ValueError("path starts with /, ? or #")
        return self.app_url + path

    def set_menu_button(self, chat_id: int | None = None, text: str = "Open") -> Any:
        params: dict[str, Any] = {"menu_button": {"type": "web_app", "text": text, "web_app": {"url": self.app_url}}}
        if chat_id is not None:
            params["chat_id"] = chat_id
        return self.t.call("setChatMenuButton", params)

    def send_open_button(self, chat_id: int, text: str, button: str, path: str = "") -> Any:
        """Inline web_app button (private chat with the bot): the app gets a query_id for answerWebAppQuery."""
        return self.t.call("sendMessage", {"chat_id": chat_id, "text": text, "reply_markup": {
            "inline_keyboard": [[{"text": button, "web_app": {"url": self.app_url_for(path)}}]]}})

    def send_keyboard_button(self, chat_id: int, text: str, button: str, path: str = "") -> Any:
        """Reply-keyboard web_app button: the only launch where the app may call sendData."""
        return self.t.call("sendMessage", {"chat_id": chat_id, "text": text, "reply_markup": {
            "keyboard": [[{"text": button, "web_app": {"url": self.app_url_for(path)}}]],
            "resize_keyboard": True, "one_time_keyboard": True}})

    def send_alert_with_link(self, chat_id: int, text: str, button: str, start_param: str) -> Any:
        """A notification that opens the exact screen (works in any chat type, unlike web_app buttons)."""
        return self.t.call("sendMessage", {"chat_id": chat_id, "text": text, "reply_markup": {
            "inline_keyboard": [[{"text": button, "url": self.link(start_param)}]]}})

    # ------------------------------------------------------------- results back to the chat

    def answer_query_once(self, query_id: str, result: dict) -> bool:
        """answerWebAppQuery once per query_id (taken from VERIFIED initData). False on a replay.

        `result` is built on the server: the message appears in the chat under the bot's name, so client-supplied
        text in it would be a phishing vector. The answered set here is in memory for the example; in production
        use a durable store shared by all workers (an atomic insert with a TTL), written only after the call
        succeeds, so a failed call does not burn the query id."""
        if not query_id or query_id in self.answered_queries:
            return False
        self.t.call("answerWebAppQuery", {"web_app_query_id": query_id, "result": result})
        self.answered_queries.add(query_id)
        return True

    def on_web_app_data(self, message: dict, schema: Callable[[dict], dict]) -> dict | None:
        """`web_app_data` (reply-keyboard launch): authentic sender, user-controlled content."""
        data = (message.get("web_app_data") or {}).get("data", "")
        chat_id = message["chat"]["id"]
        if len(data.encode()) > 4096:
            return None
        try:
            payload = json.loads(data)
            if not isinstance(payload, dict):
                raise TypeError("an object is expected")
            parsed = schema(payload)
        except (ValueError, KeyError, TypeError, RecursionError):
            self.t.call("sendMessage", {"chat_id": chat_id, "text": "That did not come through. Open the form again."})
            return None
        return parsed

    def send_order_card(self, chat_id: int, order_no: str, lines: list[tuple[str, str]], total: str,
                        path: str = "") -> Any:
        """The result of a Mini App order: a Rich Message receipt (a compact table) with its actions on the
        keyboard under it. Open order and Repeat act on the whole message, so they are not buttons inside the
        document (references/rich-message-buttons.md). web_app buttons work in private chats with the bot only.
        Item names come from the server's order, and are escaped anyway: the message speaks with the bot's name.
        The "order:repeat:<no>" handler checks that the order belongs to callback_query.from_user.id before it
        repeats anything: callback data can be forged."""
        if not re.fullmatch(r"[A-Za-z0-9-]{1,40}", order_no):
            raise ValueError("order_no: 1-40 of A-Z a-z 0-9 -")
        rows = "".join(f"<tr><td>{_esc(name)}</td><td>{_esc(price)}</td></tr>" for name, price in lines)
        html = (f"<p><b>Order {order_no}</b> is being prepared</p>"
                f"<table compact>{rows}<tr><td><b>Total</b></td><td><b>{_esc(total)}</b></td></tr></table>")
        keyboard = {"inline_keyboard": [[{"text": "Open order", "web_app": {"url": self.app_url_for(path)}},
                                         {"text": "Repeat", "callback_data": f"order:repeat:{order_no}"}]]}
        return self.t.call("sendRichMessage", {"chat_id": chat_id, "rich_message": {"html": html}, "reply_markup": keyboard})

    def prepare_share(self, user_id: int, result: dict, *, chats: tuple[str, ...] = ("users", "groups")) -> Any:
        """savePreparedInlineMessage for WebApp.shareMessage(id). One per share: ids expire."""
        params: dict[str, Any] = {"user_id": user_id, "result": result}
        for kind in chats:
            params[f"allow_{kind[:-1]}_chats"] = True
        return self.t.call("savePreparedInlineMessage", params)

    def prepare_chat_picker(self, user_id: int, request_id: int, text: str = "Choose a group") -> Any:
        """savePreparedKeyboardButton (9.6) for WebApp.requestChat(id); the result arrives as chat_shared."""
        return self.t.call("savePreparedKeyboardButton", {"user_id": user_id, "button": {
            "text": text, "request_chat": {"request_id": request_id, "chat_is_channel": False, "bot_is_member": True}}})

    # ------------------------------------------------------------- follow-up messages

    def on_write_access_allowed(self, message: dict) -> None:
        if message.get("write_access_allowed") is not None:
            self.write_allowed.add(message["from"]["id"])

    def notify(self, user_id: int, text: str, **extra: Any) -> bool:
        """The bot writes first only with permission; otherwise the app shows it in place."""
        if user_id not in self.write_allowed:
            return False
        if "chat_id" in extra:
            raise ValueError("chat_id comes from the write-access gate, not from extra")
        self.t.call("sendMessage", {**extra, "text": text, "chat_id": user_id})
        return True

    def join_request(self, update: dict, *, verify_in_app: bool = True) -> Any:
        """chat_join_request with query_id (bot handles joins): open the app or decide, within 10 s."""
        req = update["chat_join_request"]
        qid = req.get("query_id")
        if not qid:
            return None
        if verify_in_app:
            return self.t.call("sendChatJoinRequestWebApp", {"chat_join_request_query_id": qid,
                                                              "web_app_url": self.app_url + "/verify"})
        return self.t.call("answerChatJoinRequestQuery", {"chat_join_request_query_id": qid, "result": "queue"})


def _esc(text: object) -> str:
    """Text and attribute values inside Rich HTML."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def parse_start_param(raw: str | None, routes: dict[str, re.Pattern]) -> tuple[str, re.Match] | None:
    """Server-side twin of the kit's parseStartParam: the first matching route, else None."""
    if not raw or not START_PARAM.fullmatch(raw):
        return None
    for name, pattern in routes.items():
        m = pattern.fullmatch(raw)
        if m:
            return name, m
    return None
