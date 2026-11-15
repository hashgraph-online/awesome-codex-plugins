"""HTML widgets (Bot API 10.4): size checks, authoritative state, query handling.

Rules this module encodes (Widgets guide, verified 2026-11-12):
* code is immutable after sending; only the bot writes state;
* chat_data (one message, one chat; shared by all members in a group) and
  public_data (wherever the widget is shown, forwards included) are separate
  audiences - neither may hold secrets;
* answerWidgetQuery returns data to the asking widget only and does NOT change
  state; state changes go through editMessageWidgetData / editSharedWidgetData;
* every query is answered exactly once, within 15 s, also on failure;
* a shared widget takes at most one edit per second - coalesce;
* production (2026-11-12): private chats with the bot only. Groups, inline mode
  and forwards are test-server features.
"""
from __future__ import annotations

import json
import re
import zlib
from dataclasses import dataclass, field
from typing import Any, Callable

from .errors import TelegramError

HTML_MAX_BYTES = 32768
HTML_MAX_COMPRESSED = 4096
DATA_MAX_BYTES = 1024
QUERY_DATA_MAX_BYTES = 64
ANSWER_MAX_BYTES = 1024
CAPTION_MAX_CHARS = 1024

PRODUCTION_CONTEXTS = {"private"}
TEST_ONLY_CONTEXTS = {"group", "supergroup", "inline", "forward"}


def compressed_size(html: str) -> int:
    """Exactly how the server counts: zlib, level 9, over the UTF-8 bytes."""
    return len(zlib.compress(html.encode("utf-8"), 9))


# (pattern, message) pairs: things a web page relies on that a widget lacks.
_RUNTIME_GAPS = [
    (r"\bfetch\s*\(|XMLHttpRequest|new\s+WebSocket|EventSource|sendBeacon",
     "network APIs throw NetworkDisabledError - widgets are offline; ask the bot via TelegramWidget.request()"),
    (r"<\s*(input|select|textarea|option|fieldset)\b",
     "form controls are removed - there is no keyboard input; use <button> or ask in the chat"),
    (r"<\s*(iframe|video|audio|object|embed|dialog|progress|meter|template)\b",
     "element is outside widget profile 1 and is removed"),
    (r"<\s*script[^>]*\bsrc\s*=|<\s*link\b|@import|@font-face",
     "external scripts, stylesheets and fonts are never loaded; inline everything"),
    (r"<\s*img[^>]*\bsrc\s*=\s*(?![\"']?data:)",
     "images load only from data: URLs (PNG/JPEG/GIF/WebP) - others show a placeholder"),
    (r"\d\s*(vh|dvh|svh|lvh)\b",
     "height-relative units are not supported; content beyond 600 px is clipped"),
    (r"overflow\s*:\s*(auto|scroll)", "nothing scrolls inside a widget (becomes hidden)"),
    (r"position\s*:\s*sticky", "position: sticky becomes relative"),
    (r"\balert\s*\(|\bconfirm\s*\(|\bprompt\s*\(", "dialogs are not shown (confirm() returns false)"),
    (r"navigator\.clipboard", "use TelegramWidget.copyText() on a tap"),
    (r"\b(keydown|keyup|keypress|touchstart|touchmove|wheel)\b",
     "keyboard, touch and wheel events never fire; use pointer events and click"),
    (r"\blocation\.|history\.", "navigation is not available"),
    (r":has\(|:focus|:checked|oklch\(|oklab\(|lab\(|lch\(|hwb\(|color-mix\(|-webkit-line-clamp|text-shadow|"
     r"clip-path|mix-blend-mode|@container|@layer|@property|perspective|rotate[XY3]\(",
     "CSS feature outside profile 1 (removed)"),
    (r"\b(Chart|d3)\.|chart\.js|d3\.v?\d|cdn\.jsdelivr|unpkg\.com|cdnjs",
     "no libraries are bundled or fetched (Chart.js, D3 by CDN do not run) - draw with SVG/canvas"),
    (r"requestFullscreen|navigator\.share|navigator\.vibrate|geolocation|new\s+Worker",
     "browser API not available in widgets"),
]
_SECRET_HINT = re.compile(r"(api[_-]?key|secret|password|bot\d{6,}:|bearer\s)", re.I)


@dataclass
class WidgetReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    raw_bytes: int = 0
    compressed_bytes: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors


def check_widget(html: str, *, caption: str | None = None, public_data: str | None = None,
                 chat_data: str | None = None, context: str = "private",
                 environment: str = "production") -> WidgetReport:
    rep = WidgetReport(raw_bytes=len(html.encode("utf-8")), compressed_bytes=compressed_size(html))
    if not html:
        rep.errors.append("html is empty (1-32768 bytes required)")
    if rep.raw_bytes > HTML_MAX_BYTES:
        rep.errors.append(f"html is {rep.raw_bytes} bytes > {HTML_MAX_BYTES} (INPUT_MEDIA_WIDGET_TOO_LARGE)")
    if rep.compressed_bytes > HTML_MAX_COMPRESSED:
        rep.errors.append(f"html compresses to {rep.compressed_bytes} bytes > {HTML_MAX_COMPRESSED} "
                          "with zlib level 9 (INPUT_MEDIA_WIDGET_TOO_LARGE)")
    if "\x00" in html:
        rep.errors.append("html contains NUL (INPUT_MEDIA_WIDGET_HTML_INVALID)")
    for name, value in (("public_data", public_data), ("chat_data", chat_data)):
        if value is None:
            continue
        n = len(value.encode("utf-8"))
        if n > DATA_MAX_BYTES:
            rep.errors.append(f"{name} is {n} UTF-8 bytes > {DATA_MAX_BYTES} (INPUT_MEDIA_WIDGET_DATA_TOO_LARGE)")
        if "\x00" in value:
            rep.errors.append(f"{name} contains NUL (INPUT_MEDIA_WIDGET_DATA_INVALID)")
    for name, value in (("html", html), ("public_data", public_data or "")):
        if _SECRET_HINT.search(value):
            rep.errors.append(f"{name} looks like it carries a secret - code and public state are public")
    if context not in PRODUCTION_CONTEXTS | TEST_ONLY_CONTEXTS:
        rep.errors.append(f"unknown context {context!r}")
    elif environment == "production" and context in TEST_ONLY_CONTEXTS:
        rep.errors.append(f"widgets in {context!r} are test-server only (production: private chats with the bot)")
    if not caption:
        rep.warnings.append("no caption: chat list, notifications, search, accessibility and "
                            "apps without widget support show only the caption")
    elif len(caption) > CAPTION_MAX_CHARS:
        rep.errors.append(f"caption is {len(caption)} chars > {CAPTION_MAX_CHARS}")
    for pattern, message in _RUNTIME_GAPS:
        if re.search(pattern, html, re.I):
            rep.warnings.append(message)
    if rep.compressed_bytes > HTML_MAX_COMPRESSED * 0.9 and rep.compressed_bytes <= HTML_MAX_COMPRESSED:
        rep.warnings.append("within 10% of the compressed limit - other zlib builds differ; trust this number")
    return rep


def encode_state(state: dict[str, Any]) -> str:
    text = json.dumps(state, separators=(",", ":"), ensure_ascii=False)
    if len(text.encode("utf-8")) > DATA_MAX_BYTES:
        raise ValueError("state exceeds 1024 UTF-8 bytes - keep the full record server-side")
    return text


@dataclass
class StateRecord:
    state: dict[str, Any]
    revision: int = 0


class WidgetStore:
    """Authoritative widget state on the bot's side. The query never carries
    the widget's state, so every decision is made against this store."""

    def __init__(self) -> None:
        self.records: dict[str, StateRecord] = {}
        self.answered: set[str] = set()

    @staticmethod
    def key_for(query: dict[str, Any]) -> str:
        if query.get("inline_message_id"):
            return "inline:" + query["inline_message_id"]
        if query.get("chat") and query.get("message_id"):
            return f"msg:{query['chat']['id']}:{query['message_id']}"
        return "shared:" + query["widget_id"]   # a forward: only widget_id is known


def edit_target(query: dict[str, Any]) -> dict[str, Any]:
    """Addressing for editMessageWidgetData from a widget_query."""
    if query.get("inline_message_id"):
        return {"inline_message_id": query["inline_message_id"]}
    return {"chat_id": query["chat"]["id"], "message_id": query["message_id"]}


Decision = Callable[[dict[str, Any], dict[str, Any], StateRecord], tuple[dict[str, Any] | None, dict[str, Any]]]


def handle_widget_query(query: dict[str, Any], store: WidgetStore, transport: Any, decide: Decision, *,
                        state_field: str = "chat_data",
                        log: Callable[[dict], None] = lambda e: None) -> str:
    """One query -> at most one state edit -> exactly one answer.

    `decide(query, parsed_action, record)` returns (new_state or None, answer).
    Order: decide -> edit state -> commit only if the edit went through ->
    answer (the answer carries the new revision so the widget can drop older
    pushes). Returns the outcome for logs/tests.

    This version is synchronous. In an async port, reserve the query id BEFORE the
    first await and serialize per widget key (see handleWidgetQuery in
    examples/ts/tgkit.ts), or concurrent updates duplicate edits and lose increments.
    """
    qid = query["id"]
    if qid in store.answered:                       # redelivered update
        return "duplicate"
    raw = query.get("data", "")
    if not 1 <= len(raw.encode("utf-8")) <= QUERY_DATA_MAX_BYTES:
        return _answer(transport, store, qid, {"ok": False, "err": "bad_request"}, "invalid")
    action = {"raw": raw, "verb": raw.split(":", 1)[0], "arg": raw.split(":", 1)[1] if ":" in raw else ""}
    key = store.key_for(query)
    record = store.records.setdefault(key, StateRecord(state={}))
    try:
        new_state, answer = decide(query, action, record)
    except PermissionError:
        return _answer(transport, store, qid, {"ok": False, "err": "not_allowed"}, "denied")
    if new_state is not None:
        candidate = StateRecord(state=new_state, revision=record.revision + 1)
        payload = encode_state({**candidate.state, "r": candidate.revision})
        try:
            if key.startswith("shared:"):
                transport.call("editSharedWidgetData", {"widget_id": query["widget_id"],
                                                        "public_data": payload})
            else:
                transport.call("editMessageWidgetData", {**edit_target(query), state_field: payload})
        except TelegramError as err:
            if err.category != "not_modified":
                log({"event": "widget_edit_failed", "class": err.category})
                code = "busy" if err.category == "rate_limited" else "failed"
                return _answer(transport, store, qid, {"ok": False, "err": code,
                                                       "r": record.revision}, "edit_failed")
        store.records[key] = candidate              # commit after the edit
        record = candidate
    answer = dict(answer)
    if answer.pop("with_state", False):
        # The asking widget needs the new state now; pushes may arrive later.
        answer["s"] = {**record.state, "r": record.revision}
    answer["r"] = record.revision
    return _answer(transport, store, qid, {"ok": True, **answer}, "ok")


def _answer(transport: Any, store: WidgetStore, qid: str, data: dict[str, Any], outcome: str) -> str:
    text = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    if len(text.encode("utf-8")) > ANSWER_MAX_BYTES:
        text = '{"ok":false,"err":"too_large"}'
    try:
        transport.call("answerWidgetQuery", {"widget_query_id": qid, "data": text})
    except TelegramError as err:
        if err.category != "query_too_old":
            raise
        outcome = "answered_late"                 # the widget already showed TIMEOUT
    store.answered.add(qid)
    return outcome


class SharedWidgetWriter:
    """Coalesces shared-state edits to at most one per `min_interval` seconds."""

    def __init__(self, transport: Any, widget_id: str, *, min_interval: float = 1.0):
        self.transport = transport
        self.widget_id = widget_id
        self.min_interval = min_interval
        self.pending: str | None = None
        self.last_write: float | None = None
        self.writes = 0

    def submit(self, public_data: str, now: float) -> None:
        self.pending = public_data
        self.flush(now)

    def flush(self, now: float) -> bool:
        if self.pending is None:
            return False
        if self.last_write is not None and now - self.last_write < self.min_interval:
            return False
        try:
            self.transport.call("editSharedWidgetData", {"widget_id": self.widget_id,
                                                         "public_data": self.pending})
        except TelegramError as err:
            if err.category == "rate_limited":
                self.last_write = now + float(err.retry_after or 1) - self.min_interval
                return False
            if err.category != "not_modified":
                raise
        self.pending = None
        self.last_write = now
        self.writes += 1
        return True
