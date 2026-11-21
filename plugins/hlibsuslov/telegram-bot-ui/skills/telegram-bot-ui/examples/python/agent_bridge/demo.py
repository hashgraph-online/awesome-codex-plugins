"""Offline demo helpers shared by recipes 40-49 and the MCP example.

Ids are demo values used across the fixtures: operator 111111111 (Alice),
teammate 222222222 (Bob), stranger 333333333, team group -1001234567890.
"""
from __future__ import annotations

from typing import Any

from .approvals import IdFactory
from .bridge import AgentBridge, BridgeConfig, VirtualClock
from .intake import FixtureSource
from .redact import Redactor
from .security import Allowlist
from .store import JsonStore
from .transport import DryRunTransport

OPERATOR, TEAMMATE, STRANGER, TEAM_GROUP = 111111111, 222222222, 333333333, -1001234567890
START = 1_762_900_000.0
NAMES = {OPERATOR: "Alice", TEAMMATE: "Bob", STRANGER: "Alice"}   # the stranger copies the display name


def make_bridge(updates: list[dict[str, Any]] | None = None, *, transport: Any = None, store: JsonStore | None = None,
                members: set[int] | None = None, groups: set[int] | None = None,
                operators: set[int] | None = None, seed: str = "offline", **cfg: Any):
    clock = VirtualClock(START)
    allow = Allowlist(operators or {OPERATOR}, members or set(), groups or set())
    t = transport or DryRunTransport()
    bridge = AgentBridge(t, BridgeConfig(chat_id=OPERATOR, allow=allow, bot_username="agent_demo_bot", **cfg),
                         store=store or JsonStore(), source=FixtureSource(list(updates or []), clock=clock),
                         clock=clock, sleep=clock.sleep, ids=IdFactory(seed), redactor=Redactor())
    return bridge, t, clock


def tap(rec: dict[str, Any], choice: str, *, user: int = OPERATOR, uid: int, at: float | None = None) -> dict[str, Any]:
    """A button press on the request's own message (the real shape of a callback_query)."""
    chat = rec["chat"]
    upd: dict[str, Any] = {"update_id": uid, "callback_query": {
        "id": f"43820000000{uid}", "from": {"id": user, "is_bot": False, "first_name": NAMES.get(user, "User")},
        "message": {"message_id": rec["message_id"], "date": 0,
                    "chat": {"id": chat, "type": "private" if chat > 0 else "supergroup"}},
        "chat_instance": "-5550002",
        "data": f"{'ap' if rec['kind'] == 'approval' else 'aq'}:{rec['rid']}:{rec['nonce']}:{choice}"}}
    if at is not None:
        upd["_at"] = at
    return upd


def reply(rec: dict[str, Any], text: str, *, user: int = OPERATOR, uid: int, at: float | None = None) -> dict[str, Any]:
    chat = rec["chat"]
    upd: dict[str, Any] = {"update_id": uid, "message": {
        "message_id": 3000 + uid % 1000, "date": 0, "text": text,
        "chat": {"id": chat, "type": "private" if chat > 0 else "supergroup"},
        "from": {"id": user, "is_bot": False, "first_name": NAMES.get(user, "User")},
        "reply_to_message": {"message_id": rec["message_id"], "date": 0, "chat": {"id": chat}}}}
    if at is not None:
        upd["_at"] = at
    return upd


def text_message(text: str, *, user: int = OPERATOR, chat: int | None = None, uid: int,
                 thread: int | None = None, at: float | None = None) -> dict[str, Any]:
    chat = chat if chat is not None else user
    msg: dict[str, Any] = {"message_id": 3000 + uid % 1000, "date": 0, "text": text,
                           "chat": {"id": chat, "type": "private" if chat > 0 else "supergroup"},
                           "from": {"id": user, "is_bot": False, "first_name": NAMES.get(user, "User")}}
    if thread:
        msg["message_thread_id"], msg["is_topic_message"] = thread, True
    upd: dict[str, Any] = {"update_id": uid, "message": msg}
    if at is not None:
        upd["_at"] = at
    return upd


__all__ = ["make_bridge", "tap", "reply", "text_message", "OPERATOR", "TEAMMATE", "STRANGER", "TEAM_GROUP", "START"]
