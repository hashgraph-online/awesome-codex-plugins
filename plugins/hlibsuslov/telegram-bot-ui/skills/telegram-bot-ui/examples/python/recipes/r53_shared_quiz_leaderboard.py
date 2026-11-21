"""R53 - Shared quiz and leaderboard: each player answers a private quiz widget (the correct
answer never reaches the widget before the tap); one SHARED leaderboard widget is created once
and re-sent to every player with sendSharedWidget; votes are one per (widget_id, from.id);
shared edits are coalesced to <= 1 per second.

Run:  py -3 examples/python/recipes/r53_shared_quiz_leaderboard.py
"""
from __future__ import annotations

import json

import _common as c
from tgkit.router import Router
from tgkit.transport import FakeTransport
from widget_gallery import GalleryBot

HOST = 555555555                 # the bot owner's own chat: the first send creates the shared widget
PLAYERS = (111111111, 222222222)


def run(transport: FakeTransport | None = None):
    t = transport or FakeTransport()
    now = [1794736800.0]
    bot = GalleryBot(t, clock=lambda: now[0])
    router = Router()
    router.on("widget_query")(bot.handle)
    n = iter(range(1, 100))

    def tap(user: int, mid: int, data: str, widget_id: str | None = None) -> None:
        upd = c.fixture("widget_query_quiz_answer.json")
        q = upd["widget_query"]
        q.update({"id": f"81234567890123530{next(n):02d}", "message_id": mid, "data": data,
                  "from": {**q["from"], "id": user}, "chat": {"id": user, "type": "private"}})
        if widget_id:
            q["widget_id"] = widget_id
        router.dispatch(upd)

    # 1) Private quiz per player (static widget, chat_data): question 2 of 5, nothing revealed yet.
    quiz = bot.send("quiz", PLAYERS[1])["message_id"]
    tap(PLAYERS[1], quiz, "a:1:2@0")              # Canberra: correct, revealed with the explanation
    tap(PLAYERS[1], quiz, "a:1:0@0")              # a second answer from an old view: stale
    tap(PLAYERS[1], quiz, "next@1")
    # 2) The leaderboard: created once (is_shared + allow_queries), then re-sent by widget_id.
    first = bot.send("leaderboard", HOST)
    wid = first["widget"]["id"]
    sent = [bot.send("leaderboard", p, widget_id=wid) for p in PLAYERS]
    # 3) Votes from both players within one second: answered at once, written once.
    tap(PLAYERS[0], sent[0]["message_id"], "v:0", wid)
    now[0] += 0.3
    tap(PLAYERS[1], sent[1]["message_id"], "v:2", wid)
    tap(PLAYERS[1], sent[1]["message_id"], "v:2", wid)   # same choice again: no change
    now[0] += 1.0
    bot.flush(now[0])
    return t, bot, wid, router


def main() -> None:
    t, bot, wid, router = run()
    c.dump(t, "Shared quiz and leaderboard")
    sends = t.params_of("sendWidget")
    quiz_state = json.loads(sends[0]["chat_data"])
    c.check("ok" not in quiz_state and "ex" not in quiz_state, "the correct answer is not in the state before the tap")
    answers = [json.loads(p["data"]) for p in t.params_of("answerWidgetQuery")]
    c.check(answers[0]["s"]["ok"] == 2 and answers[0]["s"]["sc"] == 2, "the answer reveals and scores")
    c.check(answers[1]["err"] == "stale", "a second tap from an old view is refused")
    c.check(sends[1]["is_shared"] and sends[1]["allow_queries"], "the leaderboard is created once as a shared widget")
    c.check(len(t.params_of("sendSharedWidget")) == 2, "re-sent to each player by widget_id")
    c.check(all(a["ok"] for a in answers[3:]) and answers[4]["my"] == 2, "each voter gets their own vote back")
    edits = t.params_of("editSharedWidgetData")
    c.check(len(edits) == 2 and all(e["widget_id"] == wid for e in edits), "two votes, coalesced shared writes by widget_id")
    last = json.loads(edits[-1]["public_data"])
    c.check([o[1] for o in last["poll"]["o"]] == [213, 148, 98], "one vote per user counted")


if __name__ == "__main__":
    main()
