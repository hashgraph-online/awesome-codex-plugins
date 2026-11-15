"""Approvals and button answers bound to one pending request.

A decision is accepted only when ALL of these hold (each blocks one attack):
* the callback_data parses and names an open request id        (garbage)
* its nonce equals the stored nonce (constant-time compare)    (forged / replayed
                                                                 data from an old card)
* it arrives on the request's own message in the request's chat (copied buttons)
* the presser's numeric id is in the request's approver set      (other group members)
* the request has not expired                                    (stale taps)
* the request is still open; a repeat of the same decision is a
  harmless duplicate, a different one is refused                 (double taps, races)

callback_data layout: "<k>:<rid>:<nonce>:<choice>" - k = "ap" (approval) or
"aq" (ask choice), rid 8 hex chars, nonce 8 url-safe chars; at most ~30 bytes,
well under the 64-byte callback_data limit.
"""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from dataclasses import dataclass
from typing import Any, Callable

from .store import JsonStore

CB_RE = re.compile(r"^(ap|aq):([0-9a-f]{8}):([A-Za-z0-9_-]{8}):([a-z0-9]{1,3})$")
APPROVAL_CHOICES = {"a": "approved", "r": "rejected", "d": "details"}


class IdFactory:
    """Request ids and nonces. Live: `secrets`. Offline: deterministic from a
    seed, so fixtures can contain the exact callback_data of a demo run."""

    def __init__(self, seed: str | None = None):
        self.seed = seed
        self._n = 0

    def pair(self) -> tuple[str, str]:
        if self.seed is None:
            return secrets.token_hex(4), secrets.token_urlsafe(6)[:8].ljust(8, "x")
        self._n += 1
        h = hashlib.sha256(f"{self.seed}:{self._n}".encode()).hexdigest()
        nonce = hashlib.sha256(f"nonce:{self.seed}:{self._n}".encode()).hexdigest()
        return h[:8], ("n" + nonce[:7])


@dataclass
class Resolution:
    outcome: str             # approved | rejected | details | answered | duplicate | already_decided
    #                          | expired | forged | not_allowed | wrong_message
    record: dict[str, Any] | None = None
    choice: str | None = None

    @property
    def accepted(self) -> bool:
        return self.outcome in ("approved", "rejected", "answered")


class ApprovalBook:
    def __init__(self, store: JsonStore, *, clock: Callable[[], float], ids: IdFactory | None = None):
        self.store = store
        self.clock = clock
        self.ids = ids or IdFactory()

    def create(self, kind: str, *, chat_id: int, approvers: set[int], ttl: float,
               summary: str, choices: list[str] | None = None, default: str | None = None) -> dict[str, Any]:
        if kind not in ("approval", "ask"):
            raise ValueError("kind must be approval or ask")
        if not approvers:
            raise ValueError("an approval needs at least one approver id")
        rid, nonce = self.ids.pair()
        now = self.clock()
        rec = {"rid": rid, "nonce": nonce, "kind": kind, "status": "open", "chat": chat_id,
               "message_id": None, "approvers": sorted(approvers), "created": now, "expires": now + ttl,
               "summary": summary, "choices": choices or [], "default": default,
               "decision": None, "by": None, "decided_at": None, "reminded": False}
        self.store.put_pending(rid, rec)
        return rec

    def attach(self, rid: str, message_id: int) -> None:
        rec = self.store.get_pending(rid)
        rec["message_id"] = message_id
        self.store.put_pending(rid, rec)

    @staticmethod
    def callback_data(rec: dict[str, Any], choice: str) -> str:
        prefix = "ap" if rec["kind"] == "approval" else "aq"
        return f"{prefix}:{rec['rid']}:{rec['nonce']}:{choice}"

    def resolve_callback(self, event: dict[str, Any]) -> Resolution:
        """`event` is a classified callback (security.classify)."""
        m = CB_RE.match(event.get("data") or "")
        if not m:
            return Resolution("forged")
        prefix, rid, nonce, choice = m.groups()
        rec = self.store.get_pending(rid)
        if rec is None or not hmac.compare_digest(rec["nonce"], nonce) or \
                ("ap" if rec["kind"] == "approval" else "aq") != prefix:
            return Resolution("forged")
        if rec["chat"] != event.get("chat") or rec["message_id"] != event.get("message_id"):
            return Resolution("wrong_message", rec)
        if event.get("from") not in rec["approvers"]:
            return Resolution("not_allowed", rec)
        if rec["kind"] == "approval":
            if choice not in APPROVAL_CHOICES:
                return Resolution("forged", rec)
            decision = APPROVAL_CHOICES[choice]
        else:
            if not choice.isdigit() or int(choice) >= len(rec["choices"]):
                return Resolution("forged", rec)
            decision = rec["choices"][int(choice)]
        if decision == "details":
            return Resolution("details", rec)        # never decides anything
        return self._decide(rec, decision, event.get("from"), via="button")

    def resolve_text(self, rec: dict[str, Any], user_id: int, text: str) -> Resolution:
        """Typed answer to an ask (reply to its message). Approvals never take
        typed decisions."""
        if rec["kind"] != "ask":
            return Resolution("not_allowed", rec)
        if user_id not in rec["approvers"]:
            return Resolution("not_allowed", rec)
        return self._decide(rec, text, user_id, via="text")

    def _decide(self, rec: dict[str, Any], decision: str, by: int | None, via: str) -> Resolution:
        now = self.clock()
        if rec["status"] != "open":
            same = rec["decision"] == decision and rec["by"] == by
            return Resolution("duplicate" if same else "already_decided", rec, decision)
        if now >= rec["expires"]:
            self._close(rec, "expired", None, now)
            return Resolution("expired", rec)
        self._close(rec, decision, by, now, via=via)
        outcome = decision if rec["kind"] == "approval" else "answered"
        return Resolution(outcome, rec, decision)

    def _close(self, rec: dict[str, Any], decision: str, by: int | None, now: float, via: str | None = None) -> None:
        rec.update(status="expired" if decision == "expired" else "decided", decision=decision, by=by,
                   decided_at=now, via=via)
        self.store.put_pending(rec["rid"], rec)

    def expire_due(self) -> list[dict[str, Any]]:
        now = self.clock()
        due = [r for r in self.store.open_requests().values() if now >= r["expires"]]
        for rec in due:
            self._close(rec, "expired", None, now)
        return due

    def find_by_message(self, chat_id: int, message_id: int) -> dict[str, Any] | None:
        for rec in self.store.open_requests().values():
            if rec["chat"] == chat_id and rec["message_id"] == message_id:
                return rec
        return None


__all__ = ["ApprovalBook", "IdFactory", "Resolution", "CB_RE"]
