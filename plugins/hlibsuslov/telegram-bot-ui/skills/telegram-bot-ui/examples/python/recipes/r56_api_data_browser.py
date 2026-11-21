"""R56 - API data browser: a widget as the front end of a REST backend. The widget has no network;
the bot is the bridge: query -> handler -> backend (mock here) -> state edit + answer within 15 s.
Filter and page through queries, open a detail, act on it, survive a slow upstream with cached
data, push a backend-originated change, and hand off to the Mini App for what a widget can't do.

Run:  py -3 examples/python/recipes/r56_api_data_browser.py
"""
from __future__ import annotations

import json

import _common as c
from tgkit.router import Router
from tgkit.transport import FakeTransport
from widget_gallery import GalleryBot
from widget_gallery import h_api_browser as api_browser

AGENT = 111111111


def run(transport: FakeTransport | None = None):
    t = transport or FakeTransport()
    api = api_browser.use_api(api_browser.MockTicketsApi())     # swap: use_api(RestTicketsApi())
    now = [1794736800.0]
    bot = GalleryBot(t, clock=lambda: now[0])
    msg = bot.send("api-browser", AGENT)
    mid = msg["message_id"]
    key = f"msg:{AGENT}:{mid}"
    router = Router()
    router.on("widget_query")(bot.handle)
    n = iter(range(1, 100))

    def tap(data: str) -> None:
        upd = c.fixture("widget_query_api_open.json")
        upd["widget_query"].update({"id": f"81234567890123560{next(n):02d}", "message_id": mid, "data": data})
        router.dispatch(upd)

    tap("sync")              # on screen: fresh first page (cached for 30 s per user, filter, page)
    tap("f:all")             # filter through a query: the bot calls GET /tickets?filter=all&page=1
    tap("pg:2")              # page 2
    tap("o:4104")            # detail: GET /tickets/4104
    tap("x:4104:assign")     # action: POST /tickets/4104/assign, re-checked by the backend
    tap("b")                 # back to the list (the write invalidated the cache: fresh page)
    now[0] += 60             # the cache expired and the upstream times out once
    api.fail_next = 1
    tap("sync")              # answered from the cached page, marked stale, not a TIMEOUT
    # A webhook from the backend: ticket 4109 was closed elsewhere -> the bot pushes the list.
    api.tickets[4109]["status"] = "closed"
    st = bot.store.records[key].state
    page = api.list("u7", st["f"], st["pg"], api_browser.PAGE)
    bot.push(AGENT, mid, {**st, "it": [api_browser._row(x) for x in page["items"]], "at": int(now[0]), "stale": 0})
    return t, bot, key, router


def main() -> None:
    t, bot, key, router = run()
    c.dump(t, "API data browser widget")
    answers = [json.loads(p["data"]) for p in t.params_of("answerWidgetQuery")]
    c.check(len(answers) == 7 and all(len(p["data"].encode()) <= 1024 for p in t.params_of("answerWidgetQuery")),
            "seven queries, seven answers, each within 1024 bytes")
    c.check(answers[1]["s"]["f"] == "all" and answers[2]["s"]["pg"] == 2, "filter and page travel as queries")
    c.check(answers[3]["s"]["v"] == "d" and answers[3]["s"]["app"].startswith("t.me/"), "detail view with a Mini App hand-off link")
    c.check(answers[4]["msg"].startswith("Assigned to you"), "the action's outcome in words")
    c.check(answers[6]["s"]["stale"] == 1 and "cached" in answers[6]["msg"], "slow upstream -> cached data marked stale")
    send = t.params_of("sendWidget")[0]
    c.check(not any(w in send["html"].lower() for w in ("bearer", "api_key", "token")), "no credentials in widget code")
    c.check(not any(w in send["chat_data"].lower() for w in ("bearer", "token", "u7")), "no credentials or backend ids in state")
    rec = bot.store.records[key]
    c.check(rec.state["it"][0][2] in ("o", "p", "c") and rec.revision == len(t.params_of("editMessageWidgetData")),
            "server-pushed change committed with its own revision")


if __name__ == "__main__":
    main()
