"""Server side of the widget gallery: one bot that sends any gallery widget and answers its
queries with the invariants every widget handler needs (Bot API 10.4, checked 2026-11-15).

Invariants (status: API = Bot API requirement, Guide = Widgets guide, H = heuristic):
* API   the query never carries the widget's state; decide against the stored record.
* Guide `from` is authenticated by Telegram; per-user and owner checks key on from.id.
* H     request data is "verb[:arg][@rev]"; `@rev` is the revision the user saw. Actions that
        depend on what was on screen (toggle, increment, pick an item by index) are refused as
        stale when rev != the stored revision, and the answer carries the fresh state.
* API   every query is answered exactly once within 15 s, also on failure; a redelivered
        update is skipped (tgkit.widgets.handle_widget_query keeps the answered ids).
* API   the answer does not change state: edit first (commit after success), then answer with
        the new state for the asking widget ("with_state").
* API   a shared widget takes at most one edit per second: votes are coalesced.
* H     server-only fields (owner, secrets, full records) never go into chat_data/public_data.
"""
from __future__ import annotations

import importlib
import json
import os
import pkgutil
from dataclasses import dataclass, field
from typing import Any, Callable

from tgkit.errors import TelegramError
from tgkit.widgets import (SharedWidgetWriter, StateRecord, WidgetStore, check_widget, encode_state,
                           handle_widget_query)

HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLES = os.path.dirname(os.path.dirname(HERE))
WIDGETS = os.path.join(EXAMPLES, "widgets")


@dataclass
class Action:
    raw: str
    verb: str
    arg: str = ""
    rev: int | None = None

    def int_arg(self, lo: int, hi: int) -> int:
        """The argument as an integer in [lo, hi]; anything else is a bad request."""
        try:
            v = int(self.arg)
        except ValueError:
            raise BadRequest(self.raw) from None
        if not lo <= v <= hi:
            raise BadRequest(self.raw)
        return v


class BadRequest(Exception):
    """Untrusted data that does not name a valid action for the current state."""


def parse(raw: str) -> Action:
    body, rev = raw, None
    if "@" in raw:
        body, _, tail = raw.rpartition("@")
        if tail.isdigit():
            rev = int(tail)
        else:
            body = raw
    verb, _, arg = body.partition(":")
    return Action(raw=raw, verb=verb, arg=arg, rev=rev)


@dataclass
class Ctx:
    user_id: int
    now: float
    query: dict[str, Any]
    lang: str = "en"
    memo: dict[str, Any] = field(default_factory=dict)   # server-only data of this widget (never sent)


# decide(state, action, ctx) -> (new_state | None, answer). Raise PermissionError to refuse,
# BadRequest for invalid data. Return {"msg": ...} in the answer for a human sentence.
Decide = Callable[[dict[str, Any], Action, Ctx], tuple[dict[str, Any] | None, dict[str, Any]]]


@dataclass
class Spec:
    name: str
    decide: Decide
    demo: dict[str, Any]
    field: str = "chat_data"             # which state the handler owns
    owner_only: bool = True               # only the user the widget was sent to may act
    stale_verbs: frozenset[str] = frozenset()   # verbs refused when @rev is not current
    shared: bool = False                  # one public state for every message (sendSharedWidget)

    @property
    def html(self) -> str:
        with open(os.path.join(WIDGETS, self.name + ".html"), encoding="utf-8") as fh:
            return fh.read()

    def state(self, name: str = "default") -> dict[str, Any] | None:
        st = self.demo["states"][name]
        return st.get("chatData" if self.field == "chat_data" else "publicData")


def load_demo(name: str) -> dict[str, Any]:
    with open(os.path.join(WIDGETS, "demo", name + ".json"), encoding="utf-8") as fh:
        return json.load(fh)


def _discover() -> dict[str, Spec]:
    specs = {}
    for mod in pkgutil.iter_modules([HERE]):
        if mod.name.startswith("h_"):
            spec = importlib.import_module(f"{__package__}.{mod.name}").SPEC
            specs[spec.name] = spec
    return specs


@dataclass
class GalleryBot:
    """Sends gallery widgets and answers their queries. Transport: tgkit FakeTransport offline."""
    transport: Any
    clock: Callable[[], float] = lambda: 1794736800.0   # 2026-11-15 10:00 UTC
    store: WidgetStore = field(default_factory=WidgetStore)
    owners: dict[str, int] = field(default_factory=dict)
    widgets: dict[str, str] = field(default_factory=dict)       # store key -> gallery name
    shared: dict[str, dict[str, Any]] = field(default_factory=dict)   # widget_id -> {spec, writer}
    outcomes: list[str] = field(default_factory=list)
    memos: dict[str, dict[str, Any]] = field(default_factory=dict)   # store key or widget_id -> memo

    def send(self, name: str, chat_id: int, *, state: str = "default", state_override: dict | None = None,
             widget_id: str | None = None, html: str | None = None) -> dict[str, Any]:
        """Send a gallery widget. `html`: another build of it, e.g. the user's language."""
        spec = SPECS[name]
        html = html or spec.html
        demo = spec.demo
        st = demo["states"][state]
        chat_data = st.get("chatData")
        public_data = st.get("publicData")
        if state_override is not None:
            if spec.field == "chat_data":
                chat_data = state_override
            else:
                public_data = state_override
        enc = lambda v: None if v is None else encode_state(v)   # noqa: E731
        send = demo.get("send", {})
        if widget_id:   # an existing shared widget: only chat_data and the caption are per message
            params = {"chat_id": chat_id, "widget_id": widget_id, "caption": demo["caption"]}
            if chat_data is not None:
                params["chat_data"] = enc(chat_data)
            msg = self.transport.call("sendSharedWidget", params)
            return msg
        report = check_widget(html, caption=demo["caption"], chat_data=enc(chat_data),
                              public_data=enc(public_data))
        if not report.ok:
            raise ValueError("; ".join(report.errors))
        params = {"chat_id": chat_id, "html": html, "caption": demo["caption"]}
        for key, value in (("chat_data", chat_data), ("public_data", public_data)):
            if value is not None:
                params[key] = enc(value)
        for flag in ("allow_queries", "is_shared"):
            if send.get(flag):
                params[flag] = True
        if demo.get("fallback"):
            params["reply_markup"] = demo["fallback"]   # the text/button alternative
        msg = self.transport.call("sendWidget", params)
        authoritative = dict((chat_data if spec.field == "chat_data" else public_data) or {})
        authoritative.pop("r", None)
        if spec.shared:
            wid = msg["widget"]["id"]
            self.shared[wid] = {"spec": spec, "record": StateRecord(state=authoritative),
                                "writer": SharedWidgetWriter(self.transport, wid)}
        else:
            key = f"msg:{chat_id}:{msg['message_id']}"
            self.store.records[key] = StateRecord(state=authoritative)
            self.owners[key] = chat_id      # private chat: the user the widget was sent to
            self.widgets[key] = name
        return msg

    def push(self, chat_id: int, message_id: int, state: dict[str, Any], *, caption: str | None = None) -> bool:
        """A change that starts on the server (an alert, a job step): edit, then commit.
        Mirrors the main fact into the caption when given (the chat list shows only it).
        Returns False when the edit failed; the record is then unchanged."""
        key = f"msg:{chat_id}:{message_id}"
        record = self.store.records[key]
        field_name = SPECS[self.widgets[key]].field
        candidate = StateRecord(state=state, revision=record.revision + 1)
        try:
            self.transport.call("editMessageWidgetData", {
                "chat_id": chat_id, "message_id": message_id,
                field_name: encode_state({**state, "r": candidate.revision})})
        except TelegramError as err:
            if err.category != "not_modified":
                return False
        self.store.records[key] = candidate
        if caption:
            try:
                self.transport.call("editMessageCaption", {"chat_id": chat_id, "message_id": message_id,
                                                           "caption": caption})
            except TelegramError as err:
                if err.category != "not_modified":
                    raise
        return True

    # -------------------------------------------------------------- queries

    def handle(self, update: dict[str, Any]) -> str:
        # An Update, or the inner query object a router hands over.
        q = update.get("widget_query") or update.get("shared_widget_query") or (update if "data" in update else None)
        if q is None:
            return "ignored"
        wid = q.get("widget_id")
        if wid in self.shared:
            outcome = self._handle_shared(q, self.shared[wid])
        else:
            key = self.store.key_for(q)
            name = self.widgets.get(key)
            if name is None:
                outcome = self._refuse(q, "not_allowed")
            else:
                outcome = handle_widget_query(q, self.store, self.transport, self._decider(SPECS[name], key),
                                              state_field=SPECS[name].field)
        self.outcomes.append(outcome)
        return outcome

    def _ctx(self, q: dict[str, Any], key: str) -> Ctx:
        return Ctx(user_id=q["from"]["id"], now=self.clock(), query=q, lang=q["from"].get("language_code", "en"),
                   memo=self.memos.setdefault(key, {}))

    def _decider(self, spec: Spec, key: str):
        def decide(query, action, record):
            if spec.owner_only and self.owners.get(key) != query["from"]["id"]:
                raise PermissionError("not the owner")
            act = parse(action["raw"])
            if act.verb in spec.stale_verbs and act.rev != record.revision:
                return None, {"err": "stale", "with_state": True}
            try:
                new, answer = spec.decide(dict(record.state), act, self._ctx(query, key))
            except BadRequest:
                return None, {"err": "bad_request", "with_state": True}
            return new, {"with_state": True, **answer}
        return decide

    def _refuse(self, q: dict[str, Any], err: str) -> str:
        if q["id"] in self.store.answered:
            return "duplicate"
        self.transport.call("answerWidgetQuery", {"widget_query_id": q["id"],
                                                  "data": json.dumps({"ok": False, "err": err})})
        self.store.answered.add(q["id"])
        return "denied"

    def _handle_shared(self, q: dict[str, Any], entry: dict[str, Any]) -> str:
        """Shared widget: one public state keyed by widget_id; answer the voter with the new
        state at once, write the shared state coalesced to <= 1 edit per second."""
        if q["id"] in self.store.answered:
            return "duplicate"
        spec, record = entry["spec"], entry["record"]
        act = parse(q.get("data", ""))
        try:
            new, answer = spec.decide(dict(record.state), act, self._ctx(q, "shared:" + q["widget_id"]))
            ok = True
        except (BadRequest, PermissionError) as err:
            new, answer, ok = None, {"err": "bad_request" if isinstance(err, BadRequest) else "not_allowed"}, False
        if new is not None:
            record.state, record.revision = new, record.revision + 1
            entry["writer"].submit(encode_state({**new, "r": record.revision}), self.clock())
        data = {"ok": ok, **answer, "s": {**record.state, "r": record.revision}, "r": record.revision}
        try:
            self.transport.call("answerWidgetQuery", {"widget_query_id": q["id"],
                                                      "data": json.dumps(data, separators=(",", ":"), ensure_ascii=False)})
        except TelegramError as err:
            if err.category != "query_too_old":
                raise
        self.store.answered.add(q["id"])
        return "ok" if ok else "denied"

    def flush(self, now: float) -> None:
        for entry in self.shared.values():
            entry["writer"].flush(now)


SPECS: dict[str, Spec] = {}


def register() -> dict[str, Spec]:
    SPECS.update(_discover())
    return SPECS


def query(data: str, *, user: int = 111111111, chat: int | None = None, message_id: int = 1001,
          qid: str = "q1", widget_id: str | None = None, lang: str = "en") -> dict[str, Any]:
    """A widget_query update for tests and the preview server (shape of the official example)."""
    chat = user if chat is None else chat
    q: dict[str, Any] = {"id": qid, "from": {"id": user, "is_bot": False, "first_name": "Alice", "language_code": lang},
                         "chat": {"id": chat, "type": "private", "first_name": "Alice"}, "message_id": message_id,
                         "chat_instance": "901234567890123456", "type": {"type": "data"}, "data": data}
    if widget_id:
        q["widget_id"] = widget_id
    return {"update_id": 100000100, "widget_query": q}
