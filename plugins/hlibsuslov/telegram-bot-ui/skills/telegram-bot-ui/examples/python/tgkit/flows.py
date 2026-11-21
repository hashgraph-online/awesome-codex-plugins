"""Product-flow helpers for the use-case cookbook (recipes 20-29 and 60-69).

A product bot is a set of screens over per-user state. The same six problems
show up in every product, so they are solved once here:

* callback_data is 1-64 BYTES (API requirement) - `pack()` refuses longer data,
  Cyrillic included, instead of letting the server reject the keyboard;
* a tap on an old screen (stale button, double tap, retried update) must not act
  twice - every screen render bumps a version that travels in callback_data;
* in groups anyone can tap a button - a session belongs to one user, and the
  message->owner map refuses other users (design rule; the API does not do it);
* "Back" must return to the previous screen with its state - a back stack;
* a submit/checkout must not create two orders - `OnceStore` keyed by a
  business id, not by the callback query id (a retry has a new query id);
* every text exists in every sample language - `I18n.missing()`.

Standard library only. Uses `tgkit.transport` (any object with `call()`) and
`tgkit.errors`. Verified against the Bot API docs on 2026-11-15 (Bot API 10.4).
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Callable

from .errors import TelegramError
from .text import escape_html

MAX_CALLBACK_BYTES = 64          # API requirement: callback_data 1-64 bytes
CALLBACK_SEP = ":"
CALLBACK_TEXT_LIMIT = 200        # answerCallbackQuery.text 0-200 characters


class CallbackTooLong(ValueError):
    pass


def pack(*parts: Any) -> str:
    """Join parts into callback_data and enforce the 64-byte limit (UTF-8)."""
    items = [str(p) for p in parts]
    for p in items:
        if CALLBACK_SEP in p:
            raise ValueError(f"callback part {p!r} contains the separator")
    data = CALLBACK_SEP.join(items)
    size = len(data.encode("utf-8"))
    if not 1 <= size <= MAX_CALLBACK_BYTES:
        raise CallbackTooLong(f"callback_data is {size} bytes (1-64 allowed): {data!r}")
    return data


def unpack(data: str | None) -> list[str]:
    return (data or "").split(CALLBACK_SEP)


def b36(n: int) -> str:
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    out = ""
    while True:
        n, r = divmod(n, 36)
        out = digits[r] + out
        if not n:
            return out


# ---- buttons and keyboards ---------------------------------------------------

def btn(text: str, data: str | None = None, *, style: str | None = None, disabled: bool = False,
        icon: str | None = None, **action: Any) -> dict[str, Any]:
    """One inline button with exactly one action field.

    disabled=True -> `disabled: {}` (DisabledButton, Bot API 10.3) and no other action.
    icon -> icon_custom_emoji_id (Bot API 9.4; owner Premium or Fragment usernames).
    """
    b: dict[str, Any] = {"text": text}
    if disabled:
        b["disabled"] = {}
    elif data is not None:
        b["callback_data"] = data
    else:
        if len(action) != 1:
            raise ValueError("a button needs exactly one action")
        b.update(action)
    if icon:
        b["icon_custom_emoji_id"] = icon
    if style:
        b["style"] = style
    return b


def kb(*rows: list[dict[str, Any]] | None, force_reply: bool = False) -> dict[str, Any]:
    """InlineKeyboardMarkup; empty/None rows are dropped. force_reply (10.3) is
    fixed for the message's lifetime: it can't be changed by an edit."""
    markup: dict[str, Any] = {"inline_keyboard": [r for r in rows if r]}
    if force_reply:
        markup["force_reply"] = True
    return markup


def callback_buttons(markup: dict[str, Any] | None) -> list[dict[str, Any]]:
    out = []
    for row in (markup or {}).get("inline_keyboard", []):
        out.extend(row)
    return out


# ---- localization ------------------------------------------------------------

class I18n:
    """Message catalog {lang: {key: template}}. Templates are regular-HTML;
    values passed to `t()` are escaped unless wrapped in `Raw`."""

    def __init__(self, catalog: dict[str, dict[str, str]], default: str = "en"):
        if default not in catalog:
            raise ValueError("the default language must be in the catalog")
        self.catalog = catalog
        self.default = default

    def lang_for(self, language_code: str | None) -> str:
        code = (language_code or "").split("-")[0].lower()
        return code if code in self.catalog else self.default

    def t(self, lang: str, key: str, /, **values: Any) -> str:
        table = self.catalog.get(lang) or self.catalog[self.default]
        template = table.get(key, self.catalog[self.default].get(key))
        if template is None:
            raise KeyError(f"missing copy key {key!r}")
        safe = {k: (v.text if isinstance(v, Raw) else escape_html(str(v))) for k, v in values.items()}
        return template.format(**safe)

    def missing(self) -> dict[str, list[str]]:
        keys = set().union(*(set(t) for t in self.catalog.values()))
        return {lang: sorted(keys - set(t)) for lang, t in self.catalog.items() if keys - set(t)}


@dataclass(frozen=True)
class Raw:
    """Already-safe HTML (e.g. a <tg-time> or <tg-emoji> built by the bot)."""
    text: str


def tg_time(unix: int, fallback: str, fmt: str | None = "wDT") -> Raw:
    """Regular-HTML date-time entity; clients show it in the reader's time zone."""
    f = f' format="{fmt}"' if fmt else ""
    return Raw(f'<tg-time unix="{int(unix)}"{f}>{escape_html(fallback)}</tg-time>')


# ---- screens, sessions, guards -----------------------------------------------

@dataclass
class Session:
    owner_id: int
    chat_id: int
    lang: str = "en"
    screen: str = ""
    stack: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    args: dict[str, Any] = field(default_factory=dict)       # current screen's arguments
    data: dict[str, Any] = field(default_factory=dict)       # product state of this user
    version: int = 0
    message_id: int | None = None
    inline_message_id: str | None = None
    kind: str = ""                                           # "text" or "rich" of the live message


Render = Callable[["ScreenFlow", Session], dict[str, Any]]
Action = Callable[["ScreenFlow", Session, list[str], dict[str, Any]], Any]


class ScreenFlow:
    """Screen registry with a back stack, rendered into ONE message per session.

    callback_data = "<app>:<version>:<action>[:arg...]". Outcomes of `handle()`:
    "foreign" (another app's button), "expired" (no session), "not_yours"
    (another user's message), "stale" (an older render of this message),
    or whatever the action returns (default "ok"). Every callback query is
    answered exactly once.
    """

    def __init__(self, transport: Any, app: str, *, i18n: I18n | None = None,
                 texts: dict[str, str] | None = None, log: Callable[[dict], None] | None = None):
        self.t = transport
        self.app = app
        self.i18n = i18n
        self.screens: dict[str, Render] = {}
        self.actions: dict[str, Action] = {}
        self.sessions: dict[tuple[int, int], Session] = {}
        self.owners: dict[tuple[int, int], int] = {}        # (chat, message) -> owner user id
        self.log = log or (lambda e: None)
        self._answered: set[str] = set()
        self.texts = {"stale": "This screen has changed. Use the latest message.",
                      "not_yours": "This menu belongs to someone else. Open your own with /start.",
                      "expired": "This menu has expired. Send /start to open a new one.",
                      **(texts or {})}

    # registration
    def screen(self, name: str) -> Callable[[Render], Render]:
        def reg(fn: Render) -> Render:
            self.screens[name] = fn
            return fn
        return reg

    def action(self, name: str) -> Callable[[Action], Action]:
        def reg(fn: Action) -> Action:
            self.actions[name] = fn
            return fn
        return reg

    # sessions
    def session(self, chat_id: int, user_id: int, *, lang: str = "en") -> Session:
        key = (chat_id, user_id)
        if key not in self.sessions:
            self.sessions[key] = Session(owner_id=user_id, chat_id=chat_id, lang=lang)
        return self.sessions[key]

    def cb(self, s: Session, action: str, *args: Any) -> str:
        """callback_data for the NEXT render of `s` (render bumps the version first)."""
        return pack(self.app, b36(s.version), action, *args)

    def tr(self, s: Session, key: str, /, **values: Any) -> str:
        if self.i18n is None:
            raise RuntimeError("no i18n catalog")
        return self.i18n.t(s.lang, key, **values)

    # rendering
    def _params(self, s: Session) -> dict[str, Any]:
        out = self.screens[s.screen](self, s)
        if "text" in out:
            out.setdefault("parse_mode", "HTML")
        return out

    def open(self, s: Session, screen: str, *, new_message: bool = False, **args: Any) -> Any:
        """Replace the stack and show `screen` (a /start, a deep link, a notification)."""
        s.stack.clear()
        return self._show(s, screen, args, new_message=new_message)

    def go(self, s: Session, screen: str, **args: Any) -> Any:
        if s.screen:
            s.stack.append((s.screen, dict(s.args)))
        return self._show(s, screen, args)

    def back(self, s: Session) -> Any:
        if not s.stack:
            return self._show(s, s.screen, s.args)
        screen, args = s.stack.pop()
        return self._show(s, screen, args)

    def refresh(self, s: Session) -> Any:
        return self._show(s, s.screen, s.args)

    def _show(self, s: Session, screen: str, args: dict[str, Any], *, new_message: bool = False) -> Any:
        s.screen, s.args = screen, dict(args)
        s.version += 1
        params = self._params(s)
        kind = "rich" if "rich_message" in params else "text"
        if s.inline_message_id and not new_message:
            return self._edit({"inline_message_id": s.inline_message_id, **params})
        # Switching a live message between plain text and rich content in an edit
        # is not documented: send a new message instead (design heuristic).
        if s.message_id is None or new_message or kind != s.kind:
            if s.message_id is not None:            # the old menu's buttons stop working
                self.owners.pop((s.chat_id, s.message_id), None)
            method = "sendRichMessage" if kind == "rich" else "sendMessage"
            msg = self.t.call(method, {"chat_id": s.chat_id, **params})
            s.message_id, s.kind = msg.get("message_id"), kind
            self.owners[(s.chat_id, s.message_id)] = s.owner_id
            return msg
        return self._edit({"chat_id": s.chat_id, "message_id": s.message_id, **params})

    def _edit(self, params: dict[str, Any]) -> Any:
        method = "editMessageText" if ("text" in params or "rich_message" in params) else "editMessageReplyMarkup"
        try:
            return self.t.call(method, params)
        except TelegramError as err:
            if err.category == "not_modified":   # the screen is already as it should be
                return True
            raise

    # callbacks
    def answer(self, cq: dict[str, Any], text: str | None = None, *, alert: bool = False) -> None:
        """answerCallbackQuery exactly once per query (the client spinner stops)."""
        if cq["id"] in self._answered:
            return
        self._answered.add(cq["id"])
        params: dict[str, Any] = {"callback_query_id": cq["id"]}
        if text:
            params["text"] = text[:CALLBACK_TEXT_LIMIT]
            if alert:
                params["show_alert"] = True
        self.t.call("answerCallbackQuery", params)

    def sys_text(self, status: str, cq: dict[str, Any], s: Session | None = None) -> str:
        """Refusal toast in the presser's language: catalog key `sys_<status>` if
        the catalog has it, else the English default."""
        if self.i18n and f"sys_{status}" in self.i18n.catalog[self.i18n.default]:
            lang = s.lang if s else self.i18n.lang_for(cq["from"].get("language_code"))
            return self.i18n.t(lang, f"sys_{status}")
        return self.texts[status]

    def session_for(self, cq: dict[str, Any]) -> tuple[Session | None, str]:
        user = cq["from"]["id"]
        msg = cq.get("message") or {}
        if "inline_message_id" in cq:
            for s in self.sessions.values():
                if s.inline_message_id == cq["inline_message_id"]:
                    return s, "ok"
            return None, "expired"
        chat = (msg.get("chat") or {}).get("id")
        owner = self.owners.get((chat, msg.get("message_id")))
        if owner is not None and owner != user:
            return None, "not_yours"
        s = self.sessions.get((chat, user))
        if s is None or owner is None:
            return None, "expired"
        return s, "ok"

    def handle(self, cq: dict[str, Any]) -> str:
        parts = unpack(cq.get("data"))
        if len(parts) < 3 or parts[0] != self.app:
            return "foreign"                   # leave it for another handler
        s, status = self.session_for(cq)
        if s is None:
            self.answer(cq, self.sys_text(status, cq), alert=status == "not_yours")
            self.log({"event": "callback_refused", "app": self.app, "why": status})
            return status
        if parts[1] != b36(s.version):
            self.answer(cq, self.sys_text("stale", cq, s))
            self.log({"event": "callback_refused", "app": self.app, "why": "stale"})
            return "stale"
        fn = self.actions.get(parts[2])
        if fn is None:
            self.answer(cq, self.sys_text("stale", cq, s))
            return "stale"
        result = fn(self, s, parts[3:], cq)
        self.answer(cq)                     # no-op if the action already answered
        return result if isinstance(result, str) else "ok"


# ---- idempotency, dedup, state machines --------------------------------------

class OnceStore:
    """Run a side effect at most once per business key (order id, form id, cart
    version). The result of the first run is returned to every repeat."""

    def __init__(self) -> None:
        self.done: dict[str, Any] = {}
        self.runs = 0

    def run(self, key: str, fn: Callable[[], Any]) -> tuple[Any, bool]:
        if key in self.done:
            return self.done[key], False
        self.runs += 1
        result = fn()
        self.done[key] = result
        return result, True


class UpdateDedup:
    """Telegram may deliver an update again (webhook retry, restart). Drop
    update_ids already processed. Keep a bounded window in production."""

    def __init__(self, window: int = 10000) -> None:
        self.seen: list[int] = []
        self.window = window

    def first_time(self, update: dict[str, Any]) -> bool:
        uid = update.get("update_id")
        if uid in self.seen:
            return False
        self.seen.append(uid)
        del self.seen[:-self.window]
        return True


class IllegalTransition(ValueError):
    pass


class Machine:
    """Explicit status transitions. A status the product doesn't allow (a
    delivered parcel going back to "packed", a cancelled booking confirmed)
    raises instead of silently corrupting the record."""

    def __init__(self, transitions: dict[str, dict[str, str]], initial: str):
        self.transitions = transitions
        self.initial = initial

    def next(self, state: str, event: str) -> str:
        try:
            return self.transitions[state][event]
        except KeyError:
            raise IllegalTransition(f"{event!r} is not allowed in state {state!r}") from None

    def allowed(self, state: str) -> list[str]:
        return sorted(self.transitions.get(state, {}))


# ---- lists -------------------------------------------------------------------

def paginate(items: list[Any], page: int, size: int) -> tuple[list[Any], int, int]:
    """Slice for page (clamped). Returns (items, page, pages); pages >= 1."""
    pages = max(1, -(-len(items) // size))
    page = min(max(page, 0), pages - 1)
    return items[page * size:(page + 1) * size], page, pages


def pager_row(flow: ScreenFlow, s: Session, page: int, pages: int, action: str = "page",
              *extra: Any) -> list[dict[str, Any]]:
    """← 2/5 → with the arrows DISABLED (not removed) at the ends, so the row keeps
    its shape. The counter is a disabled button: it shows state, has no action."""
    if pages <= 1:
        return []
    prev_ = btn("←", flow.cb(s, action, page - 1, *extra)) if page > 0 else btn("←", disabled=True)
    next_ = btn("→", flow.cb(s, action, page + 1, *extra)) if page < pages - 1 else btn("→", disabled=True)
    return [prev_, btn(f"{page + 1}/{pages}", disabled=True), next_]


# ---- time-based jobs (reminders, expiry, digests) ----------------------------

@dataclass(order=True)
class Job:
    at: float
    key: str
    payload: dict[str, Any] = field(compare=False, default_factory=dict)


class Scheduler:
    """In-memory stand-in for a persistent job queue. Keys make jobs
    replaceable (rescheduling a booking replaces its reminders)."""

    def __init__(self) -> None:
        self.jobs: dict[str, Job] = {}

    def at(self, when: float, key: str, **payload: Any) -> None:
        self.jobs[key] = Job(when, key, payload)

    def cancel(self, prefix: str) -> int:
        gone = [k for k in self.jobs if k.startswith(prefix)]
        for k in gone:
            del self.jobs[k]
        return len(gone)

    def due(self, now: float) -> list[Job]:
        ready = sorted(j for j in self.jobs.values() if j.at <= now)
        for j in ready:
            del self.jobs[j.key]
        return ready


# ---- updates and payloads ----------------------------------------------------

def user(uid: int, name: str = "User", lang: str = "en") -> dict[str, Any]:
    return {"id": uid, "is_bot": False, "first_name": name, "language_code": lang}


def callback(cq_id: str, frm: dict[str, Any], data: str, *, chat_id: int | None = None,
             message_id: int | None = None, chat_type: str = "private",
             inline_message_id: str | None = None) -> dict[str, Any]:
    """A callback_query object as Telegram sends it (only the fields we read)."""
    cq: dict[str, Any] = {"id": cq_id, "from": frm, "chat_instance": "-1", "data": data}
    if inline_message_id:
        cq["inline_message_id"] = inline_message_id
    else:
        cq["message"] = {"message_id": message_id, "date": 0,
                         "chat": {"id": chat_id, "type": chat_type}}
    return cq


def text_message(frm: dict[str, Any], text: str, *, chat_id: int | None = None, message_id: int = 1,
                 chat_type: str = "private", reply_to: int | None = None, **extra: Any) -> dict[str, Any]:
    msg: dict[str, Any] = {"message_id": message_id, "date": 0, "from": frm,
                           "chat": {"id": chat_id or frm["id"], "type": chat_type}, "text": text, **extra}
    if reply_to is not None:
        msg["reply_to_message"] = {"message_id": reply_to, "date": 0,
                                   "chat": {"id": chat_id or frm["id"], "type": chat_type}}
    return msg


def markups(transport: Any) -> list[tuple[str, dict[str, Any]]]:
    """Every reply_markup and rich message the flow put on the wire (for validators)."""
    out = []
    for method, params in transport.calls:
        if "reply_markup" in params:
            out.append((method, params["reply_markup"]))
        if "rich_message" in params:
            out.append((method, params["rich_message"]))
        for r in params.get("results", []) or []:
            if isinstance(r, dict) and "reply_markup" in r:
                out.append((method, r["reply_markup"]))
    return out


def payload_doc(scenario: str, transport: Any, *, status: str, context: str) -> dict[str, Any]:
    return {"scenario": scenario, "status": status, "context": context,
            "evidence": "offline contract: captured from the recipe code via FakeTransport; not sent to Telegram",
            "bot_api": "10.4 (verified 2026-11-15)",
            "steps": [{"method": m, "params": p} for m, p in transport.calls]}


def payload_text(doc: dict[str, Any]) -> str:
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


def payload_path(scenario: str) -> str:
    here = os.path.dirname(os.path.abspath(__file__))            # examples/python/tgkit
    return os.path.join(os.path.dirname(os.path.dirname(here)), "payloads", f"{scenario}.json")


def write_payload(doc: dict[str, Any]) -> str:
    path = payload_path(doc["scenario"])
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(payload_text(doc))
    return path


__all__ = [
    "MAX_CALLBACK_BYTES", "CallbackTooLong", "pack", "unpack", "b36", "btn", "kb", "callback_buttons",
    "I18n", "Raw", "tg_time", "Session", "ScreenFlow", "OnceStore", "UpdateDedup", "Machine",
    "IllegalTransition", "paginate", "pager_row", "Job", "Scheduler", "user", "callback",
    "text_message", "markups", "payload_doc", "payload_text", "payload_path", "write_payload",
]
