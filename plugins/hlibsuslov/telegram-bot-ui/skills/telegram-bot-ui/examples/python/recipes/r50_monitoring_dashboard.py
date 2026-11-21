"""R50 - Monitoring dashboard widget: a live service-health card in the on-call engineer's
private chat. Server pushes on incidents (state + caption), taps switch the period, background
sync refreshes on screen; owner check, duplicate updates, failed edits.

Run:  py -3 examples/python/recipes/r50_monitoring_dashboard.py
"""
from __future__ import annotations

import json

import _common as c
from tgkit.router import Router
from tgkit.transport import FakeTransport, TelegramErrorResponse
from widget_gallery import GalleryBot

ONCALL = 111111111


def run(transport: FakeTransport | None = None):
    t = transport or FakeTransport()
    bot = GalleryBot(t)
    # 1) Send the card: caption mirrors the headline, the keyboard is the plain alternative.
    msg = bot.send("metrics-dashboard", ONCALL)
    mid = msg["message_id"]
    key = f"msg:{ONCALL}:{mid}"
    router = Router()
    router.on("widget_query")(bot.handle)

    def tap(name: str, **patch) -> None:
        upd = c.fixture(name)
        upd["widget_query"].update({"message_id": mid, **patch})
        router.dispatch(upd)

    # 2) The widget appears on screen: background sync (no tap needed in the private chat).
    tap("widget_query_sync.json")
    # 3) The alerting pipeline sees 5xx: the bot pushes the new state and mirrors the caption.
    degraded = {**bot.store.records[key].state, "st": 1, "inc": "Elevated 5xx on /pay since 09:42",
                "kpi": [["Uptime", "99.2", "%", -0.7, 1], ["p95", "640", " ms", 420, 0],
                        ["Errors", "4.8", "%", 4.4, 0], ["RPS", "980", "", -18, 1]]}
    bot.push(ONCALL, mid, degraded, caption="api-prod · Degraded · p95 640 ms · errors 4.8%")
    # 4) The engineer taps 7d; Telegram redelivers the same update once.
    tap("widget_query_dashboard_period.json")
    tap("widget_query_dashboard_period.json")
    # 5) A crafted query from someone else for this message is refused.
    tap("widget_query_dashboard_foreign.json", chat={"id": ONCALL, "type": "private"})
    # 6) Flood wait on the edit: the answer says so, the record keeps its period.
    t.script("editMessageWidgetData", TelegramErrorResponse(429, "Too Many Requests: retry after 4", 4))
    tap("widget_query_dashboard_period.json", id="8123456789012350003", data="p:1h")
    return t, bot, mid, router


def main() -> None:
    t, bot, mid, router = run()
    c.dump(t, "Monitoring dashboard widget")
    c.check(router.allowed_updates() == ["widget_query"], "subscribe to widget_query explicitly")
    c.check(bot.outcomes == ["ok", "ok", "duplicate", "denied", "edit_failed"], f"outcomes {bot.outcomes}")
    send = t.params_of("sendWidget")[0]
    c.check(send["caption"].startswith("api-prod") and send["reply_markup"]["inline_keyboard"],
            "caption mirrors the headline; a keyboard is the plain alternative")
    caps = t.params_of("editMessageCaption")
    c.check(len(caps) == 1 and "Degraded" in caps[0]["caption"], "a server-side change also updates the caption")
    answers = [json.loads(p["data"]) for p in t.params_of("answerWidgetQuery")]
    c.check(len(answers) == 4, "each distinct query answered exactly once")
    c.check(answers[2] == {"ok": False, "err": "not_allowed"}, "only the chat's user may change the card")
    c.check(answers[3]["ok"] is False and answers[3]["err"] == "busy", "failed edit -> error answer")
    rec = bot.store.records[f"msg:{ONCALL}:{mid}"]
    c.check(rec.state["p"] == "7d" and rec.state["st"] == 1 and rec.revision == 2,
            "push and tap committed in order; the failed edit changed nothing")
    edits = [json.loads(p["chat_data"]) for p in t.params_of("editMessageWidgetData")]
    c.check([e["r"] for e in edits] == [1, 2, 3], "every pushed state carries a growing revision")
    c.check(all(len(p["data"].encode()) <= 1024 for p in t.params_of("answerWidgetQuery")),
            "answers with the state stay within 1024 bytes")


if __name__ == "__main__":
    main()
