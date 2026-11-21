"""R05 - Interactive widget in a private chat (production): an order card with a
delivery choice and Confirm, authoritative state on the bot, revisions, errors.

Run:  py -3 examples/python/recipes/r05_private_widget.py
"""
from __future__ import annotations

import json

import _common as c
from tgkit.router import Router
from tgkit.transport import FakeTransport, TelegramErrorResponse
from tgkit.widgets import StateRecord, WidgetStore, check_widget, encode_state, handle_widget_query

CHAT = 111111111
ORDER = {"o": "1042", "items": [{"q": 2, "n": "Margherita", "p": 950}, {"q": 1, "n": "Lemonade", "p": 450}],
         "opt": "std", "st": "draft"}


def send_order_widget(t: FakeTransport, store: WidgetStore) -> dict:
    html = c.widget_html("order-card.html")
    caption = "Order #1042 · $23.50 · Standard delivery"   # list, notifications, search, a11y
    report = check_widget(html, caption=caption, chat_data=encode_state({**ORDER, "r": 0}),
                          context="private", environment="production")
    if not report.ok:
        raise SystemExit("\n".join(report.errors))
    msg = t.call("sendWidget", {"chat_id": CHAT, "html": html, "chat_data": encode_state({**ORDER, "r": 0}),
                                "caption": caption, "allow_queries": True,
                                "reply_markup": {"inline_keyboard": [[   # text/button alternative
                                    {"text": "Change in chat", "callback_data": "order:1042:edit"}]]}})
    # Authoritative copy, keyed by the message the widget lives in.
    store.records[f"msg:{CHAT}:{msg['message_id']}"] = StateRecord(state=dict(ORDER))
    return msg


def decide(query, action, record):
    """Business rules live here, against the stored state - never the widget's."""
    st = record.state
    if not st:
        raise PermissionError("unknown widget")
    if action["verb"] == "sync":
        return None, {"with_state": True}
    if st["st"] != "draft":
        return None, {"msg": "This order is already confirmed.", "with_state": True}
    if action["verb"] == "ship" and action["arg"] in ("std", "fast"):
        return {**st, "opt": action["arg"]}, {"with_state": True}
    if action["verb"] == "confirm":
        return {**st, "st": "confirmed"}, {"with_state": True}
    return None, {"msg": "Unknown action"}


def run(transport: FakeTransport | None = None):
    t = transport or FakeTransport()
    store = WidgetStore()
    msg = send_order_widget(t, store)
    router = Router()
    outcomes = []

    @router.on("widget_query")
    def on_query(q):
        q = {**q, "message_id": msg["message_id"]}
        outcomes.append(handle_widget_query(q, store, t, decide))

    ship = c.fixture("widget_query_ship.json")
    router.dispatch(ship)
    router.dispatch(ship)                                   # redelivered update
    router.dispatch(c.fixture("widget_query_sync.json"))
    t.script("editMessageWidgetData", TelegramErrorResponse(429, "Too Many Requests: retry after 3", 3))
    router.dispatch(c.fixture("widget_query_confirm.json"))  # flood wait -> not committed
    retry = c.fixture("widget_query_confirm.json")
    retry["widget_query"]["id"] = "8123456789012345690"
    router.dispatch(retry)
    return t, store, outcomes, msg, router


def main() -> None:
    t, store, outcomes, msg, router = run()
    c.dump(t, "Private widget")
    c.check(router.allowed_updates() == ["widget_query"], "subscribe to widget_query explicitly")
    c.check(outcomes == ["ok", "duplicate", "ok", "edit_failed", "ok"], f"outcomes {outcomes}")
    answers = [json.loads(p["data"]) for p in t.params_of("answerWidgetQuery")]
    c.check(len(answers) == 4, "every distinct query answered once (duplicate skipped)")
    c.check(answers[2] == {"ok": False, "err": "busy", "r": 1}, "failed edit -> error answer, revision unchanged")
    rec = store.records[f"msg:{CHAT}:{msg['message_id']}"]
    c.check(rec.state["st"] == "confirmed" and rec.revision == 2, "state committed only after successful edits")
    edits = t.params_of("editMessageWidgetData")
    c.check(all(json.loads(e["chat_data"])["r"] >= 1 for e in edits), "every pushed state carries a revision")
    send = t.params_of("sendWidget")[0]
    c.check(send["caption"] and send["allow_queries"] and "reply_markup" in send,
            "caption + queries + a plain button alternative")


if __name__ == "__main__":
    main()
