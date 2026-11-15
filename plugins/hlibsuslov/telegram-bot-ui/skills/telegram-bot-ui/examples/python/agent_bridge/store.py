"""Durable state so a restarted agent process can carry on.

What must survive a restart (each one prevents a concrete failure):
* `offset`        - the next getUpdates offset; without it a restart replays
                    or (with a wrong value) silently drops updates.
* `seen`          - recent update_ids; webhook redelivery and a crash between
                    "handled" and "offset saved" must not run a command twice.
* `pending`       - open asks/approvals; a button pressed while the process
                    was down still resolves the right request.
* `cards`         - status-card message ids; a restarted job edits its card
                    instead of posting a second one.

Writes are atomic (temp file + os.replace). One process per state file: two
pollers on one bot token also conflict at the Bot API level.
"""
from __future__ import annotations

import json
import os
import tempfile
from typing import Any

SEEN_MAX = 500


class JsonStore:
    def __init__(self, path: str | None = None):
        self.path = path
        self.data: dict[str, Any] = {"offset": 0, "seen": [], "pending": {}, "cards": {}, "counters": {}}
        if path and os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                self.data.update(json.load(fh))

    # ---- persistence ---------------------------------------------------
    def save(self) -> None:
        if not self.path:
            return
        folder = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(folder, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".agent_bridge.", dir=folder)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(self.data, fh, ensure_ascii=False, indent=1, sort_keys=True)
        os.replace(tmp, self.path)

    # ---- updates -------------------------------------------------------
    @property
    def offset(self) -> int:
        return int(self.data.get("offset", 0))

    def is_seen(self, update_id: int) -> bool:
        return update_id in self.data.get("seen", []) or update_id < self.offset - SEEN_MAX

    def mark_seen(self, update_id: int) -> bool:
        """True the first time an update_id is seen, False for a duplicate."""
        seen: list[int] = self.data.setdefault("seen", [])
        if update_id in seen:
            return False
        seen.append(update_id)
        del seen[:-SEEN_MAX]
        self.data["offset"] = max(self.offset, update_id + 1)
        return True

    # ---- pending requests (asks and approvals) -------------------------
    def put_pending(self, rid: str, record: dict[str, Any]) -> None:
        self.data.setdefault("pending", {})[rid] = record
        self.save()

    def get_pending(self, rid: str) -> dict[str, Any] | None:
        return self.data.get("pending", {}).get(rid)

    def open_requests(self, kind: str | None = None) -> dict[str, dict[str, Any]]:
        return {k: v for k, v in self.data.get("pending", {}).items()
                if v.get("status") == "open" and (kind is None or v.get("kind") == kind)}

    # ---- status cards --------------------------------------------------
    def card(self, key: str) -> dict[str, Any] | None:
        return self.data.get("cards", {}).get(key)

    def put_card(self, key: str, record: dict[str, Any]) -> None:
        self.data.setdefault("cards", {})[key] = record
        self.save()

    def next_counter(self, name: str) -> int:
        counters = self.data.setdefault("counters", {})
        counters[name] = int(counters.get(name, 0)) + 1
        return counters[name]


__all__ = ["JsonStore"]
