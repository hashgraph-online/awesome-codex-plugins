"""Raw-update routing that does not lose update types an SDK doesn't know yet.

Three facts drive this module (Bot API, getUpdates/setWebhook `allowed_updates`):

1. If `allowed_updates` is not specified, the PREVIOUS setting is kept: a bot
   that once subscribed to a fixed list keeps it after an upgrade.
2. An empty list means "all except chat_member, message_reaction and
   message_reaction_count".
3. SDKs that compute allowed_updates from registered handlers (aiogram's
   `resolve_used_update_types`, grammY's DEFAULT_UPDATE_TYPES) leave out every
   update type they have no handler class for - widget_query and
   shared_widget_query in SDKs that predate Bot API 10.4. The widget then waits
   15 s and fails with TIMEOUT on the user's screen.
"""
from __future__ import annotations

from typing import Any, Callable

# Update fields added by the releases this skill covers. Keep in sync with the
# registry (recipes/registry.json).
NEW_UPDATE_TYPES = {
    "stopped_message_generation": "10.3",
    "widget_query": "10.4",
    "shared_widget_query": "10.4",
}

# A non-exhaustive list of long-standing update types, enough for routing.
KNOWN_UPDATE_TYPES = (
    "message", "edited_message", "channel_post", "edited_channel_post",
    "business_connection", "business_message", "edited_business_message",
    "deleted_business_messages", "guest_message", "message_reaction",
    "message_reaction_count", "inline_query", "chosen_inline_result",
    "callback_query", "shipping_query", "pre_checkout_query",
    "purchased_paid_media", "poll", "poll_answer", "my_chat_member",
    "chat_member", "chat_join_request", "chat_boost", "removed_chat_boost",
    "managed_bot", "subscription",
) + tuple(NEW_UPDATE_TYPES)

Handler = Callable[[dict[str, Any]], Any]


def update_type(update: dict[str, Any]) -> str | None:
    for key in update:
        if key != "update_id":
            return key
    return None


class Router:
    def __init__(self, log: Callable[[dict[str, Any]], None] | None = None):
        self._handlers: dict[str, Handler] = {}
        self._log = log or (lambda event: None)
        self.unhandled: list[str] = []

    def on(self, kind: str) -> Callable[[Handler], Handler]:
        def register(fn: Handler) -> Handler:
            self._handlers[kind] = fn
            return fn
        return register

    def allowed_updates(self) -> list[str]:
        """Exactly the types we handle. Pass this explicitly on EVERY
        getUpdates/setWebhook call - never rely on the sticky previous value."""
        return sorted(self._handlers)

    def dispatch(self, update: dict[str, Any]) -> Any:
        kind = update_type(update)
        handler = self._handlers.get(kind or "")
        if handler is None:
            # Never silent: an unknown type usually means an outdated SDK or a
            # subscription that is wider than the handlers.
            self.unhandled.append(kind or "<empty>")
            self._log({"event": "unhandled_update", "type": kind,
                       "update_id": update.get("update_id")})
            return None
        return handler(update[kind])


def check_subscription(allowed_updates: list[str] | None, handled: list[str]) -> list[str]:
    """Return handled update types that the subscription would NOT deliver."""
    if allowed_updates is None:
        return ["<allowed_updates not passed: the previous setting stays in force>"]
    if allowed_updates == []:
        excluded = {"chat_member", "message_reaction", "message_reaction_count"}
        return [t for t in handled if t in excluded]
    return [t for t in handled if t not in allowed_updates]
