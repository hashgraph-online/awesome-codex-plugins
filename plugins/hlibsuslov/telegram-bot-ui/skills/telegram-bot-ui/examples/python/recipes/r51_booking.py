"""R51 - Booking flow in a widget: day strip + slot grid, pick -> confirm, with a race against
another customer (the slot is taken between pick and confirm), a stale pick refused by revision,
and the caption mirrored after booking.

Run:  py -3 examples/python/recipes/r51_booking.py
"""
from __future__ import annotations

import json

import _common as c
from tgkit.router import Router
from tgkit.transport import FakeTransport
from widget_gallery import GalleryBot
from widget_gallery.h_slot_booking import label, with_bit

CLIENT = 111111111


def run(transport: FakeTransport | None = None):
    t = transport or FakeTransport()
    bot = GalleryBot(t)
    msg = bot.send("slot-booking", CLIENT)
    mid = msg["message_id"]
    key = f"msg:{CLIENT}:{mid}"
    router = Router()
    n = [0]

    @router.on("widget_query")
    def on_query(q):
        before = bot.store.records[key].state.get("bk")
        bot.handle(q)
        after = bot.store.records[key].state.get("bk")
        if after and after != before:       # booked: the chat list must say so too
            t.call("editMessageCaption", {"chat_id": CLIENT, "message_id": mid,
                                          "caption": f"Booked: {label(bot.store.records[key].state, after)} · "
                                                     "Haircut and styling"})

    def tap(data: str | None = None, *, same_id: bool = False) -> None:
        upd = c.fixture("widget_query_slot_pick.json")
        if not same_id:
            n[0] += 1
            upd["widget_query"]["id"] = f"81234567890123510{n[0]:02d}"
        upd["widget_query"]["message_id"] = mid
        if data:
            upd["widget_query"]["data"] = data
        router.dispatch(upd)

    tap(same_id=True)                        # pick day 1, 10:30 as seen at revision 0 -> r1
    tap(same_id=True)                        # Telegram redelivers an update with the original id
    # Another customer books 10:30 through the website: the bot's inventory pushes the change.
    st = bot.store.records[key].state
    bot.push(CLIENT, mid, {**st, "m": with_bit(st, 1, 3, False)})                       # r2
    tap("book")                              # refused: taken; the selection is cleared -> r3
    tap("pick:1:1100@0")                     # stale: the widget still drew revision 0
    tap("pick:1:1100@3")                     # fresh pick -> r4
    tap("book")                              # booked -> r5, caption mirrored
    return t, bot, mid, router


def main() -> None:
    t, bot, mid, router = run()
    c.dump(t, "Booking widget")
    answers = [json.loads(p["data"]) for p in t.params_of("answerWidgetQuery")]
    c.check(len(answers) == 5, "five distinct queries, five answers (the redelivered update skipped)")
    c.check(answers[1].get("err") == "taken" and "taken" in answers[1]["msg"], "a slot lost to a race is refused in words")
    c.check(answers[2]["err"] == "stale" and answers[2]["s"]["r"] == 3, "a pick from an old view gets the fresh state")
    c.check(answers[4]["ok"] and answers[4]["msg"].startswith("Booked for"), "confirmation sentence in the answer")
    rec = bot.store.records[f"msg:{CLIENT}:{mid}"]
    c.check(rec.state["bk"] == "1:1100" and rec.revision == 5, "booking committed once, revisions in order")
    c.check(not int(rec.state["m"][1], 16) >> 4 & 1, "the booked slot is no longer offered")
    caps = t.params_of("editMessageCaption")
    c.check(len(caps) == 1 and caps[0]["caption"].startswith("Booked:"), "caption mirrors the booking")
    c.check(t.params_of("sendWidget")[0]["reply_markup"]["inline_keyboard"], "plain keyboard alternative sent")


if __name__ == "__main__":
    main()
