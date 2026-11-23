"""Bot settings from code (Bot API 10.5): setMySettings, getMe -> BotFullInfo,
callback_query_mode, the topic sidebar and owner invite links.

Facts this module is built on (Bot API 10.5, verified 2026-11-22):

* `setMySettings` changes only the settings it is given; the rest stay as they
  are. It covers what used to be BotFather-only switches: inline mode and its
  placeholder, the inline location request, the share of chosen inline results,
  joining groups, privacy mode, business connections, managed bots, guest and
  join-request queries, topics in private chats (+ the sidebar), bot-to-bot
  communication and the callback query mode.
* `getMe` returns `BotFullInfo` (not `User`); the getMe-only flags left `User`.
  Three settings are write-only: `inline_feedback_share_denominator`,
  `can_communicate_with_bots` and `callback_query_mode` are not in BotFullInfo.
* `callback_query_mode`: "default" (always `message`, an InaccessibleMessage
  when the bot can't access it), "auto" (`inline_message_id` instead when the
  message is inaccessible) or "inline" (always `inline_message_id`). A callback
  that carries `inline_message_id` has no chat: edit it by that id, and keep
  everything the handler needs in `callback_data` or in state keyed by the user.
* Owners invite up to 10 users at once with https://t.me/botinvite/<username>;
  the invited user's chat starts with a `write_access_allowed` service message
  whose `inviter` is the owner, and the bot may write to that user.
"""
from __future__ import annotations

from typing import Any

# setMySettings parameter -> BotFullInfo field it can be read back from (None: write-only).
READABLE = {
    "supports_inline_queries": "supports_inline_queries",
    "inline_query_placeholder": "inline_query_placeholder",
    "needs_inline_query_location": "needs_inline_query_location",
    "can_join_groups": "can_join_groups",
    "can_read_all_group_messages": "can_read_all_group_messages",
    "can_connect_to_business": "can_connect_to_business",
    "can_manage_bots": "can_manage_bots",
    "supports_guest_queries": "supports_guest_queries",
    "supports_join_request_queries": "supports_join_request_queries",
    "has_topics_enabled": "has_topics_enabled",
    "allows_users_to_create_topics": "allows_users_to_create_topics",
    "has_topic_sidebar": "has_topic_sidebar",
}
WRITE_ONLY = ("inline_feedback_share_denominator", "can_communicate_with_bots", "callback_query_mode")
SETTINGS = tuple(READABLE) + WRITE_ONLY

CALLBACK_QUERY_MODES = ("default", "auto", "inline")
FEEDBACK_DENOMINATORS = (0, 1, 10, 100, 1000)
INVITE_LIMIT = 10      # users per press of the botinvite link


def validate(params: dict[str, Any]) -> tuple[list[str], list[str]]:
    """(errors, warnings) for a setMySettings request. Errors are API rules;
    warnings are design consequences worth a human's yes."""
    errors: list[str] = []
    warnings: list[str] = []
    for key, value in params.items():
        if key not in SETTINGS:
            errors.append(f"unknown setting {key!r}")
        elif key == "inline_query_placeholder":
            if not isinstance(value, str):
                errors.append("inline_query_placeholder must be a string ('' = default placeholder)")
        elif key == "inline_feedback_share_denominator":
            if isinstance(value, bool) or not isinstance(value, int) or value not in FEEDBACK_DENOMINATORS:
                errors.append("inline_feedback_share_denominator must be one of 1, 10, 100, 1000 (0 = off)")
        elif key == "callback_query_mode":
            if value not in CALLBACK_QUERY_MODES:
                errors.append("callback_query_mode must be 'default', 'auto' or 'inline'")
        elif not isinstance(value, bool):
            errors.append(f"{key} must be true or false")
    if params.get("can_read_all_group_messages") is True:
        warnings.append("privacy mode off: the bot receives every group message - store none of it it doesn't need")
    if params.get("needs_inline_query_location") is True:
        warnings.append("every inline query asks the user for location - only when results depend on it")
    if params.get("callback_query_mode") in ("auto", "inline"):
        warnings.append("callbacks may arrive with inline_message_id and no chat - route by callback_data, edit by that id")
    if params.get("can_communicate_with_bots") is True:
        warnings.append("other bots can talk to this one - treat their messages as untrusted input and stop loops")
    return errors, warnings


def plan(current: dict[str, Any], desired: dict[str, Any]) -> dict[str, Any]:
    """setMySettings params that change something, given getMe's BotFullInfo.
    Readable settings already equal to `desired` are left out (an empty plan =
    no call); write-only ones are always sent when desired."""
    out: dict[str, Any] = {}
    for key, value in desired.items():
        field = READABLE.get(key)
        if field is None:
            out[key] = value
            continue
        have = current.get(field)
        if key == "inline_query_placeholder":
            have = have or ""                  # omitted in BotFullInfo = default placeholder = ""
        if have != value:
            out[key] = value
    return out


def apply(transport: Any, desired: dict[str, Any]) -> dict[str, Any]:
    """getMe, then one setMySettings with only the changes. Returns what was sent ({} = nothing)."""
    errors, _ = validate(desired)
    if errors:
        raise ValueError("; ".join(errors))
    me = transport.call("getMe", {})
    changes = plan(me, desired)
    if changes:
        transport.call("setMySettings", changes)
    return changes


def usernames(me: dict[str, Any]) -> list[str]:
    """Every name the bot answers to: active_usernames (10.5) when present, else username."""
    names = me.get("active_usernames") or ([me["username"]] if me.get("username") else [])
    return [n.lower() for n in names]


def addressed_to_me(text: str, me: dict[str, Any]) -> bool:
    """'/cmd@name args' in a group is for this bot if `name` is ANY active username."""
    parts = (text or "").split(maxsplit=1)
    head = parts[0] if parts else ""
    command, at, name = head[1:].partition("@") if head.startswith("/") else ("", "", "")
    if not command:
        return False
    return not at or name.lower() in usernames(me)


def callback_target(cq: dict[str, Any]) -> dict[str, Any] | None:
    """Edit address for the message a callback came from, in any callback_query_mode.
    None: the message is an InaccessibleMessage (date 0, e.g. deleted) - don't edit it,
    answer the query and send a fresh message if the user still needs the result."""
    if cq.get("inline_message_id"):
        return {"inline_message_id": cq["inline_message_id"]}
    msg = cq.get("message") or {}
    if not msg.get("chat"):
        raise ValueError("callback without message or inline_message_id")
    if msg.get("date") == 0:
        return None
    return {"chat_id": msg["chat"]["id"], "message_id": msg["message_id"]}


def invite_link(me: dict[str, Any]) -> str:
    """Owner-only link: invites up to 10 users to private chats with the bot."""
    if not me.get("username"):
        raise ValueError("the bot has no username")
    return f"https://t.me/botinvite/{me['username']}"


def inviter_of(message: dict[str, Any]) -> dict[str, Any] | None:
    """The owner who invited this user (write_access_allowed.inviter), else None."""
    return (message.get("write_access_allowed") or {}).get("inviter")
