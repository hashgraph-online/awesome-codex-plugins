"""Who may talk to the agent, and what an inbound message may trigger.

Identity is the numeric `from.id` (and `chat.id`) of the update - never a
username, first name or title: those are chosen by the sender and can be
copied by anyone. Usernames appear only in display text.

Every inbound text is UNTRUSTED DATA, even from the operator: it may be a
forwarded message, a pasted log, or a prompt injection crafted by someone the
operator talked to. `classify()` turns an update into an event whose free text
is marked as data. The agent must never execute that text as instructions.

What an inbound message MAY trigger (INBOUND_POLICY):
* answer a pending `ask` (a reply to that question, or one of its buttons);
* decide a pending approval - ONLY through its bound button (approvals.py),
  never through typed text such as "approve";
* run one command from a fixed table (COMMANDS) with validated arguments;
* reach the agent as data (`content_is_untrusted_data: true`).
What it may NOT trigger: shell commands, file reads or uploads it names,
config/allowlist changes, permission widening, sending to other chats, or
revealing secrets. A forwarded message never runs a command.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# Telegram's service account that appears as `from` for anonymous group admins.
GROUP_ANONYMOUS_BOT_ID = 1087968824

COMMANDS: dict[str, dict[str, Any]] = {
    "status": {"args": "none", "effect": "read-only: report job states"},
    "help": {"args": "none", "effect": "read-only: list commands"},
    "pause": {"args": "job_id", "effect": "pause one job at its next safe point"},
    "resume": {"args": "job_id", "effect": "resume a paused job"},
    "stop": {"args": "job_id", "effect": "cancel one job (its own cancellation path)"},
    "ack": {"args": "incident_id", "effect": "acknowledge an incident"},
}
JOB_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")

INBOUND_POLICY = {
    "may": ["answer_pending_ask", "decide_approval_via_bound_button", "run_table_command", "deliver_as_data"],
    "may_not": ["run_shell", "read_or_send_named_files", "change_config_or_allowlist",
                "widen_permissions", "send_to_other_chats", "reveal_secrets", "approve_via_text",
                "run_commands_from_forwarded_messages"],
}

# Labels only - detection is never a defence on its own; the defence is that
# text is data. The label helps the agent and the operator notice an attack.
INJECTION_SIGNALS = [
    ("override", re.compile(r"(?i)\b(ignore|disregard|forget)\b.{0,40}\b(previous|prior|above|all)\b.{0,20}\b(instructions?|rules?|prompts?)\b")),
    ("role_claim", re.compile(r"(?i)\b(system prompt|you are now|developer mode|admin override|as (the )?(system|admin))\b")),
    ("shell", re.compile(r"(?i)(\brm\s+-rf\b|\bcurl\b[^\n]*\|\s*(ba)?sh\b|\bsudo\b|\bchmod\s+\+x\b|`[^`]*`|\$\()")),
    ("exfiltration", re.compile(r"(?i)\b(send|post|upload|print|show|cat)\b.{0,40}\b(\.env|token|secret|password|credentials?|id_rsa|private key)\b")),
    ("approval_claim", re.compile(r"(?i)\b(pre-?approved|already approved|approved by|auto-?approve)\b")),
]


def injection_signals(text: str) -> list[str]:
    return [name for name, rx in INJECTION_SIGNALS if rx.search(text or "")]


@dataclass
class Allowlist:
    """Numeric ids only. `operators` may command and approve; `members` may
    talk to the agent in `group_chats` (answers, data) but not approve unless
    they are also operators."""
    operators: set[int] = field(default_factory=set)
    members: set[int] = field(default_factory=set)
    group_chats: set[int] = field(default_factory=set)

    @classmethod
    def parse(cls, operators: str | None, members: str | None = None, groups: str | None = None) -> "Allowlist":
        return cls(_ids(operators), _ids(members), _ids(groups))

    def is_operator(self, user_id: int | None) -> bool:
        return user_id is not None and user_id in self.operators

    def may_speak(self, user_id: int | None, chat: dict[str, Any]) -> bool:
        if user_id is None:
            return False
        if chat.get("type") == "private":
            return user_id in self.operators and chat.get("id") == user_id
        if chat.get("id") in self.group_chats:
            return user_id in self.operators or user_id in self.members
        return False

    def chat_allowed(self, chat: dict[str, Any]) -> bool:
        if chat.get("type") == "private":
            return chat.get("id") in self.operators
        return chat.get("id") in self.group_chats


def _ids(raw: str | None) -> set[int]:
    out: set[int] = set()
    for part in (raw or "").replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        if not re.fullmatch(r"-?\d{1,20}", part):
            raise ValueError("allowlist entries must be numeric Telegram ids, not usernames")
        out.add(int(part))
    return out


def classify(update: dict[str, Any], allow: Allowlist, bot_username: str | None = None) -> dict[str, Any]:
    """Map one update to an event. Never raises on hostile input."""
    uid = update.get("update_id")
    if "message" in update:
        return _message(uid, update["message"], allow, bot_username)
    if "callback_query" in update:
        cq = update["callback_query"]
        sender = (cq.get("from") or {}).get("id")
        chat = ((cq.get("message") or {}).get("chat")) or {}
        if not chat or not allow.may_speak(sender, chat):
            return _reject(uid, "unknown_sender" if chat else "inline_or_unknown_chat", sender, chat.get("id"))
        return {"type": "callback", "update_id": uid, "from": sender, "chat": chat.get("id"),
                "from_name": display_name(cq.get("from") or {}),
                "callback_query_id": cq.get("id"), "data": cq.get("data", ""),
                "message_id": (cq.get("message") or {}).get("message_id"), "trust": _trust(allow, sender)}
    if "stopped_message_generation" in update:
        s = update["stopped_message_generation"]
        chat = s.get("chat") or {}
        if not allow.chat_allowed(chat):
            return _reject(uid, "unknown_chat", None, chat.get("id"))
        return {"type": "stop_generation", "update_id": uid, "chat": chat.get("id"),
                "message_thread_id": s.get("message_thread_id"), "draft_id": s.get("draft_id")}
    if "my_chat_member" in update:
        m = update["my_chat_member"]
        chat = m.get("chat") or {}
        status = (m.get("new_chat_member") or {}).get("status")
        added = status in ("member", "administrator")
        by = (m.get("from") or {}).get("id")
        if added and not allow.chat_allowed(chat):
            return {"type": "unknown_chat_added", "update_id": uid, "chat": chat.get("id"),
                    "chat_type": chat.get("type"), "by": by, "action": "leave_and_alert"}
        return {"type": "membership", "update_id": uid, "chat": chat.get("id"), "status": status, "by": by}
    kind = next((k for k in update if k != "update_id"), "empty")
    return _reject(uid, f"unhandled_update:{kind}", None, None)


def _message(uid: Any, msg: dict[str, Any], allow: Allowlist, bot_username: str | None) -> dict[str, Any]:
    sender = (msg.get("from") or {})
    sid, chat = sender.get("id"), msg.get("chat") or {}
    if msg.get("sender_chat") or sid == GROUP_ANONYMOUS_BOT_ID:
        return _reject(uid, "anonymous_sender", sid, chat.get("id"))
    if sender.get("is_bot"):
        return _reject(uid, "bot_sender", sid, chat.get("id"))
    if not allow.may_speak(sid, chat):
        return _reject(uid, "unknown_sender" if allow.chat_allowed(chat) or chat.get("type") == "private" else "unknown_chat",
                       sid, chat.get("id"))
    text = msg.get("text") or msg.get("caption") or ""
    base = {"update_id": uid, "from": sid, "chat": chat.get("id"), "message_id": msg.get("message_id"),
            "message_thread_id": msg.get("message_thread_id"), "trust": _trust(allow, sid),
            "from_name": display_name(sender)}
    forwarded = "forward_origin" in msg
    reply_to = (msg.get("reply_to_message") or {}).get("message_id")
    if text.startswith("/") and not forwarded:
        cmd = _command(text, bot_username)
        if cmd is not None:
            name, args = cmd
            if name not in COMMANDS:
                return {**base, "type": "unknown_command", "command": name}
            if base["trust"] != "operator" and COMMANDS[name]["effect"].split(":")[0] != "read-only":
                return _reject(uid, "command_needs_operator", sid, chat.get("id"))
            if COMMANDS[name]["args"] != "none" and not JOB_ID_RE.match(args):
                return {**base, "type": "invalid_command", "command": name, "reason": "bad_argument"}
            return {**base, "type": "command", "command": name, "args": args if COMMANDS[name]["args"] != "none" else ""}
    event = {**base, "type": "reply" if reply_to else "text", "reply_to_message_id": reply_to,
             "text": text, "forwarded": forwarded, "content_is_untrusted_data": True,
             "injection_signals": injection_signals(text)}
    if msg.get("document"):
        event["document"] = {"file_name": msg["document"].get("file_name"), "file_size": msg["document"].get("file_size")}
    return event


def display_name(user: dict[str, Any]) -> str:
    """For DISPLAY only (button labels, cards) - never for identity checks.
    Clipped and stripped of control characters; escape it for the format used."""
    name = str(user.get("first_name") or "").strip() or f"id {user.get('id')}"
    return "".join(ch for ch in name if ch.isprintable())[:32]


def _command(text: str, bot_username: str | None) -> tuple[str, str] | None:
    head, _, rest = text[1:].partition(" ")
    name, _, target = head.partition("@")
    if target and bot_username and target.lower() != bot_username.lower():
        return None                                     # addressed to another bot
    return name.lower(), rest.strip()


def _trust(allow: Allowlist, uid: int | None) -> str:
    return "operator" if allow.is_operator(uid) else "member"


def _reject(uid: Any, reason: str, sender: Any, chat: Any) -> dict[str, Any]:
    # No text, names or usernames of the stranger: a rejected update is logged
    # by numbers only, so the log itself can't be used to inject or leak.
    return {"type": "rejected", "update_id": uid, "reason": reason, "from": sender, "chat": chat}


__all__ = ["Allowlist", "classify", "injection_signals", "COMMANDS", "INBOUND_POLICY"]
