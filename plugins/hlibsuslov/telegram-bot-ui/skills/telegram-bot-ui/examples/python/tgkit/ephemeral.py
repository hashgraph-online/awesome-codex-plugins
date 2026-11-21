"""Personal answers on a shared timeline (ephemeral messages, Bot API 10.2-10.4).

Invariant enforced here: personal content keeps its audience. If it cannot be
shown privately, it is NOT posted to the chat. The fallbacks that keep the
audience are, in order:

1. ephemeral reply to the callback query (shown only to the presser);
2. answerCallbackQuery `text`/`show_alert` (only the presser sees the toast;
   0-200 characters, so only for short, low-sensitivity content);
3. answerCallbackQuery `url` = t.me/<bot>?start=<token>: opens the private chat
   with the bot. It does not prove the user will start it - never claim
   "sent to your DMs".

A successful ephemeral send does not prove delivery ("not guaranteed ...
especially if they are offline"), so the shared card must never depend on the
panel having been seen, and tapping again must simply re-render it.
"""
from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .errors import OutcomeUnknown, TelegramError

CALLBACK_TEXT_LIMIT = 200


class AudienceViolation(RuntimeError):
    """Raised before personal content would reach a wider audience."""


def ephemeral_params(cq: dict[str, Any], *, api: str = "10.4",
                     replace_original: bool = False) -> dict[str, Any]:
    """Addressing for an ephemeral reply to callback query `cq`.

    10.4: `callback_query_id` without `receiver_user_id` -> shown to the
          presser in any chat except channel direct-messages chats; `chat_id`
          may be omitted (it is ignored without receiver_user_id).
    10.3: `receiver_user_id` (must equal the presser) + `callback_query_id`
          + `chat_id`; the 10.3 form still works on 10.4 servers.
    `replace_callback_query_message` must be False when the button is on an
    ephemeral message - edit that message with editEphemeralMessage* instead.
    """
    msg = cq.get("message") or {}
    chat = msg.get("chat") or {}
    from_ephemeral = bool(msg.get("ephemeral_message_id"))
    if chat.get("is_direct_messages"):
        raise AudienceViolation("ephemeral replies are not available in channel direct messages chats")
    if replace_original and from_ephemeral:
        raise ValueError("callback from an ephemeral message: edit it, don't replace")
    eph: dict[str, Any] = {"callback_query_id": cq["id"]}
    out: dict[str, Any] = {}
    if api == "10.3":
        if not chat:
            raise ValueError("10.3 needs chat_id; inline-message callbacks need the 10.4 form")
        eph["receiver_user_id"] = cq["from"]["id"]
        out["chat_id"] = chat["id"]
    if replace_original:
        eph["replace_callback_query_message"] = True
    out["ephemeral_message_parameters"] = eph
    return out


def migrate_ephemeral_10_2(params: dict[str, Any]) -> dict[str, Any]:
    """Bot API 10.2 -> 10.3: `receiver_user_id` and `callback_query_id` moved from
    the send method into `ephemeral_message_parameters` (sendMessage, sendPhoto, …).
    A 10.3+ server does not document the old top-level parameters any more."""
    out = {k: v for k, v in params.items() if k not in ("receiver_user_id", "callback_query_id")}
    eph = {k: params[k] for k in ("receiver_user_id", "callback_query_id") if k in params}
    if eph:
        out["ephemeral_message_parameters"] = {**params.get("ephemeral_message_parameters", {}), **eph}
    return out


def guard_audience(method: str, params: dict[str, Any], *, personal: bool,
                   owner_id: int) -> None:
    """Refuse a call that would show personal content to anyone else."""
    if not personal or not method.startswith("send"):
        return
    eph = params.get("ephemeral_message_parameters")
    if eph:
        receiver = eph.get("receiver_user_id")
        if receiver is not None and receiver != owner_id:
            raise AudienceViolation("ephemeral receiver differs from the owner")
        return
    if params.get("chat_id") == owner_id:   # the owner's private chat with the bot
        return
    raise AudienceViolation(f"{method} would publish personal content to chat {params.get('chat_id')}")


@dataclass
class Panel:
    owner_id: int
    chat_id: int | None
    ephemeral_message_id: int | None
    created_at: float
    version: int = 1


@dataclass
class PersonalPanels:
    """Per-user ephemeral panels over a shared card."""

    transport: Any
    bot_username: str
    ttl: float = 600.0
    clock: Callable[[], float] = time.monotonic
    log: Callable[[dict], None] = lambda e: None
    panels: dict[tuple[int, int], Panel] = field(default_factory=dict)
    start_tokens: dict[str, int] = field(default_factory=dict)

    def show(self, cq: dict[str, Any], render: Callable[[int], str], *,
             api: str = "10.4") -> str:
        """Show `render(user_id)` privately to the presser. Returns the route used."""
        user_id = cq["from"]["id"]
        chat_id = (cq.get("message") or {}).get("chat", {}).get("id")
        text = render(user_id)              # only this user's data, built server-side
        params = {**ephemeral_params(cq, api=api), "text": text,
                  "reply_markup": {"inline_keyboard": [[
                      {"text": "Refresh", "callback_data": "panel:refresh"},
                      {"text": "Close", "callback_data": "panel:close"}]]}}
        guard_audience("sendMessage", params, personal=True, owner_id=user_id)
        try:
            msg = self.transport.call("sendMessage", params)
        except (TelegramError, OutcomeUnknown) as err:
            return self._fallback(cq, text, err)
        self.panels[(chat_id or 0, user_id)] = Panel(
            # 10.4 sends may omit chat_id, but editEphemeralMessage* still requires it.
            owner_id=user_id, chat_id=(msg.get("chat") or {}).get("id") or chat_id,
            ephemeral_message_id=msg.get("ephemeral_message_id"),
            created_at=self.clock())
        self.transport.call("answerCallbackQuery", {"callback_query_id": cq["id"]})
        self.log({"event": "panel_shown", "route": "ephemeral"})
        return "ephemeral"

    def on_panel_button(self, cq: dict[str, Any], render: Callable[[int], str]) -> str:
        """A button inside someone's panel. Re-checks ownership server-side."""
        user_id = cq["from"]["id"]
        msg = cq.get("message") or {}
        chat_id = (msg.get("chat") or {}).get("id") or 0
        panel = self.panels.get((chat_id, user_id))
        receiver = (msg.get("receiver_user") or {}).get("id")
        if panel is None or (receiver is not None and receiver != user_id):
            self.transport.call("answerCallbackQuery", {
                "callback_query_id": cq["id"], "text": "This panel has expired. Tap the card again."})
            return "stale"
        if self.clock() - panel.created_at > self.ttl:
            self.panels.pop((chat_id, user_id), None)
            self.transport.call("answerCallbackQuery", {
                "callback_query_id": cq["id"], "text": "This panel has expired. Tap the card again."})
            return "expired"
        action = cq.get("data", "")
        base = {"chat_id": panel.chat_id, "receiver_user_id": user_id,
                "ephemeral_message_id": panel.ephemeral_message_id}
        try:
            if action == "panel:close":
                self.transport.call("deleteEphemeralMessage", base)
                self.panels.pop((chat_id, user_id), None)
            else:
                panel.version += 1
                self.transport.call("editEphemeralMessageText", {
                    **base, "text": render(user_id),
                    "reply_markup": {"inline_keyboard": [[
                        {"text": "Refresh", "callback_data": "panel:refresh"},
                        {"text": "Close", "callback_data": "panel:close"}]]}})
        except TelegramError as err:
            if err.category != "not_modified":
                self.panels.pop((chat_id, user_id), None)   # gone: next tap re-creates
                self.transport.call("answerCallbackQuery", {
                    "callback_query_id": cq["id"], "text": "This panel has expired. Tap the card again."})
                return "gone"
        self.transport.call("answerCallbackQuery", {"callback_query_id": cq["id"]})
        return "edited" if action != "panel:close" else "closed"

    def _fallback(self, cq: dict[str, Any], text: str, err: Exception) -> str:
        cls = getattr(err, "category", "outcome_unknown")
        self.log({"event": "panel_fallback", "class": cls})
        if isinstance(err, OutcomeUnknown):
            # The panel may have appeared. Answer neutrally; a repeat tap re-renders.
            self.transport.call("answerCallbackQuery", {"callback_query_id": cq["id"]})
            return "unknown"
        if len(text) <= CALLBACK_TEXT_LIMIT:
            self.transport.call("answerCallbackQuery", {
                "callback_query_id": cq["id"], "text": text, "show_alert": True})
            return "alert"
        token = secrets.token_urlsafe(8)
        self.start_tokens[token] = cq["from"]["id"]   # redeemed only by this user
        self.transport.call("answerCallbackQuery", {
            "callback_query_id": cq["id"],
            "url": f"https://t.me/{self.bot_username}?start=panel_{token}"})
        return "deep_link"

    def redeem_start(self, user_id: int, payload: str) -> bool:
        """/start panel_<token> in the private chat: only the issuing user may redeem it."""
        if not payload.startswith("panel_"):
            return False
        token = payload[len("panel_"):]
        if self.start_tokens.get(token) != user_id:
            return False                    # someone else's link: don't burn it
        del self.start_tokens[token]
        return True
