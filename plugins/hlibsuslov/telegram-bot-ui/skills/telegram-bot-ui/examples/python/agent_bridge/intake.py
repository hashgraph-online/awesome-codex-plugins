"""Update intake for an agent process: long polling, fixtures, webhooks.

Long polling is the default for an agent: it runs behind NAT on a laptop or a
CI runner, needs no public URL and no TLS. Use a webhook only when the agent
already runs as an always-on HTTPS service.

Facts (Bot API, verified 2026-11-15):
* getUpdates and webhooks are mutually exclusive ("This method will not work
  if an outgoing webhook is set up"); updates are kept on the server for at
  most 24 hours.
* offset must be "greater by one than the highest among the identifiers of
  previously received updates"; recalculate it after each response.
* allowed_updates is remembered by the server until changed - always pass it
  explicitly so a new update type (stopped_message_generation) isn't silently
  missing; omitting it keeps the previous setting.
* a webhook request carries X-Telegram-Bot-Api-Secret-Token when setWebhook
  got `secret_token` (1-256 chars).

Restart safety: offset and recent update_ids live in JsonStore. An update is
marked seen only after its handler returned, so a crash replays it; handlers
that act (commands, decisions) are idempotent through `seen` + ApprovalBook.
"""
from __future__ import annotations

import hmac
import json
from collections import defaultdict, deque
from typing import Any, Callable, Iterator

from .security import Allowlist, classify
from .store import JsonStore

ALLOWED_UPDATES = ["message", "callback_query", "my_chat_member", "stopped_message_generation"]


class PollingSource:
    def __init__(self, call: Callable[[str, dict[str, Any]], Any], store: JsonStore,
                 *, allowed_updates: list[str] | None = None, limit: int = 100):
        self.call, self.store = call, store
        self.allowed_updates = allowed_updates or list(ALLOWED_UPDATES)
        self.limit = limit
        self.exhausted = False          # a live source never runs dry

    def fetch(self, timeout: float) -> list[dict[str, Any]]:
        return self.call("getUpdates", {"offset": self.store.offset, "limit": self.limit,
                                        "timeout": int(max(0, min(timeout, 50))),
                                        "allowed_updates": self.allowed_updates}) or []


class FixtureSource:
    """Offline source: hands out scripted updates, then nothing. `at` lets a
    fixture say "this arrives N seconds after start" (virtual time)."""

    def __init__(self, updates: list[dict[str, Any]], clock: Callable[[], float] | None = None):
        self.queue: deque = deque(updates)
        self.clock = clock

    @property
    def exhausted(self) -> bool:
        return not self.queue

    def fetch(self, timeout: float) -> list[dict[str, Any]]:
        if not self.queue:
            return []
        head = self.queue[0]
        due = head.get("_at")
        if due is not None and self.clock is not None and self.clock() < due:
            return []
        self.queue.popleft()
        return [{k: v for k, v in head.items() if k != "_at"}]


class SenderGate:
    """Per-sender inbound budget: a flood from one account can't starve the
    agent or make it spam replies. Design heuristic: 20 events / 60 s."""

    def __init__(self, clock: Callable[[], float], limit: int = 20, window: float = 60.0):
        self.clock, self.limit, self.window = clock, limit, window
        self.hits: dict[Any, deque] = defaultdict(deque)

    def allow(self, sender: Any) -> bool:
        now, q = self.clock(), self.hits[sender]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(now)
        return True


class Intake:
    def __init__(self, source: Any, store: JsonStore, allow: Allowlist, *,
                 bot_username: str | None = None, clock: Callable[[], float],
                 log: Callable[[dict[str, Any]], None] | None = None):
        self.source, self.store, self.allow = source, store, allow
        self.bot_username = bot_username
        self.gate = SenderGate(clock)
        self.log = log or (lambda e: None)
        self.stats = {"duplicates": 0, "rejected": 0, "throttled": 0}

    def events(self, timeout: float) -> Iterator[dict[str, Any]]:
        for update in self.source.fetch(timeout):
            uid = update.get("update_id")
            if not isinstance(uid, int) or self.store.is_seen(uid):
                self.stats["duplicates"] += 1
                continue
            event = classify(update, self.allow, self.bot_username)
            if event["type"] == "rejected":
                self.stats["rejected"] += 1
                self.log({"event": "rejected", "reason": event["reason"], "from": event["from"], "chat": event["chat"]})
            elif event.get("from") is not None and not self.gate.allow(event["from"]):
                self.stats["throttled"] += 1
                event = {"type": "rejected", "update_id": uid, "reason": "sender_rate_limited",
                         "from": event["from"], "chat": event.get("chat")}
            yield event                 # the consumer handles it here...
            self.store.mark_seen(uid)   # ...and only then is it marked seen
            self.store.save()


def verify_webhook(headers: dict[str, str], secret: str) -> bool:
    got = next((v for k, v in headers.items() if k.lower() == "x-telegram-bot-api-secret-token"), "")
    return bool(secret) and hmac.compare_digest(got.encode(), secret.encode())


def webhook_events(headers: dict[str, str], body: bytes, secret: str, store: JsonStore,
                   allow: Allowlist, bot_username: str | None = None) -> tuple[int, list[dict[str, Any]]]:
    """Webhook variant: (http_status, events). 401 without the right secret;
    a redelivered update (same update_id) yields nothing. Answer 200 quickly
    and do slow work after responding, or Telegram retries the delivery."""
    if not verify_webhook(headers, secret):
        return 401, []
    try:
        update = json.loads(body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return 400, []
    uid = update.get("update_id")
    if not isinstance(uid, int) or not store.mark_seen(uid):
        return 200, []
    store.save()
    return 200, [classify(update, allow, bot_username)]


__all__ = ["ALLOWED_UPDATES", "PollingSource", "FixtureSource", "Intake", "SenderGate",
           "verify_webhook", "webhook_events"]
