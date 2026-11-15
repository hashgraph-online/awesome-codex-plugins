"""R54 - Job progress widget: a long export reported in one card. The job worker pushes stage
changes (throttled), the open widget refreshes itself with background "sync", the elapsed timer
is derived from the state's start time, Cancel is a two-tap in-widget confirm, Retry restarts.

Run:  py -3 examples/python/recipes/r54_job_progress.py
"""
from __future__ import annotations

import json

import _common as c
from tgkit.router import Router
from tgkit.transport import FakeTransport
from widget_gallery import GalleryBot

USER = 111111111
PUSH_EVERY = 10.0      # seconds between server pushes: editMessageWidgetData counts as a sent message


def run(transport: FakeTransport | None = None):
    t = transport or FakeTransport()
    now = [1794736800.0]
    bot = GalleryBot(t, clock=lambda: now[0])
    router = Router()
    router.on("widget_query")(bot.handle)
    msg = bot.send("job-progress", USER, state="queued")
    mid = msg["message_id"]
    key = f"msg:{USER}:{mid}"
    n = iter(range(1, 100))

    def tap(data: str) -> None:
        upd = c.fixture("widget_query_job_cancel.json")
        upd["widget_query"].update({"id": f"81234567890123540{next(n):02d}", "message_id": mid, "data": data})
        router.dispatch(upd)

    # The worker reports progress every second; the bot pushes at most every PUSH_EVERY seconds.
    last_push = -1e9
    for step in range(1, 31):
        now[0] += 1
        st = bot.store.records[key].state
        if st["st"] == "queued" and step >= 5:
            st = {**st, "st": "running", "sg": 1, "t0": int(now[0]), "at": int(now[0]), "eta": 90}
        elif st["st"] == "running":
            el = now[0] - st["t0"]
            st = {**st, "p": int(st["n"] * el / 90), "sg": 1 if el < 36 else 2, "at": int(now[0]), "eta": int(90 - el)}
        if st != bot.store.records[key].state and now[0] - last_push >= PUSH_EVERY:
            bot.push(USER, mid, st)
            last_push = now[0]
    tap("sync")            # the widget on screen asks for fresh state in the background
    tap("cancel")          # the second tap of the in-widget confirm sends it
    tap("cancel")          # nothing left to cancel: refused
    tap("retry")
    return t, bot, mid, router


def main() -> None:
    t, bot, mid, router = run()
    c.dump(t, "Job progress widget")
    first_answer = t.methods().index("answerWidgetQuery")
    pushes = [p for m, p in t.calls[:first_answer] if m == "editMessageWidgetData"]
    c.check(len(pushes) == 4, "30 worker ticks -> 3 throttled pushes, plus the catch-up edit of the widget's sync")
    states = [json.loads(p["chat_data"]) for p in pushes]
    c.check(all(s["r"] == i + 1 for i, s in enumerate(states)), "revisions grow with every push")
    c.check(all("t0" in s for s in states), "the start time is in the state: timers derive from it")
    answers = [json.loads(p["data"]) for p in t.params_of("answerWidgetQuery")]
    c.check(len(answers) == 4, "every query answered once")
    c.check(answers[1]["s"]["st"] == "failed" and answers[2]["err"] == "bad_request",
            "cancel moves to a final state; a repeated cancel is refused")
    c.check(answers[3]["s"]["st"] == "queued", "retry queues the job again")


if __name__ == "__main__":
    main()
