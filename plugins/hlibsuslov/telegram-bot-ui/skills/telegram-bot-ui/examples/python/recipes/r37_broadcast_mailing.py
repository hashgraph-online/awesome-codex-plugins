"""R37 - Broadcast to subscribers: throttled, 429-aware, per-recipient outcomes.

Each subscriber gets a personalized text built from the content model (names
become plain text + entities, so `<`, `_` or `*` in a name can't break it).
One failure never stops the batch: 403 -> blocked (never retried), 400 ->
invalid, timeout -> unknown (not resent), 429 -> wait retry_after and retry;
a flood wait longer than the policy allows defers the rest of the run.

Run:  py -3 examples/python/recipes/r37_broadcast_mailing.py
"""
from __future__ import annotations

import _common as c
from tgkit.errors import RetryPolicy
from tgkit.publish import FanOut, Ledger, Post, plan
from tgkit.transport import FakeTransport, TelegramErrorResponse

SUBSCRIBERS = [(201, "Anna"), (202, "<b>Bo_b*</b>"), (203, "Олена"), (204, "Chen"), (205, "Dmytro"), (206, "Eve")]


def personal(name: str) -> Post:
    return Post(kind="text", blocks=[
        {"type": "paragraph", "text": ["Hi, ", {"bold": name}, "! The winter market opens on Saturday."]},
        {"type": "paragraph", "text": "You get this because you subscribed to event alerts."}],
        buttons=[[{"text": "Unsubscribe", "callback_data": "alerts:off"}]])


def jobs():
    return [(str(uid), plan(personal(name), uid)) for uid, name in SUBSCRIBERS]


class FakeClock:
    def __init__(self):
        self.now, self.sleeps = 0.0, []

    def sleep(self, s: float) -> None:
        self.sleeps.append(round(s, 3))
        self.now += s

    def __call__(self) -> float:
        return self.now


def run(transport: FakeTransport | None = None):
    t = transport or FakeTransport().script(
        "sendMessage",
        {"message_id": 1, "date": 0, "chat": {"id": 201, "type": "private"}},
        TelegramErrorResponse(403, "Forbidden: bot was blocked by the user"),
        TelegramErrorResponse(429, "Too Many Requests: retry after 3", retry_after=3),
        {"message_id": 2, "date": 0, "chat": {"id": 203, "type": "private"}},
        TelegramErrorResponse(400, "Bad Request: chat not found"),
        "TIMEOUT",
        {"message_id": 3, "date": 0, "chat": {"id": 206, "type": "private"}})
    clock = FakeClock()
    ledger = Ledger()
    fan = FanOut(t, per_second=25, ledger=ledger, sleep=clock.sleep, clock=clock)
    first = fan.run("market-2026-11", jobs())
    calls_after_first = len(t.calls)
    second = FanOut(t, per_second=25, ledger=ledger, sleep=clock.sleep, clock=clock).run("market-2026-11", jobs())
    # A long flood wait (> max_wait) defers the remainder instead of sleeping for minutes.
    t2 = FakeTransport().script("sendMessage", {"message_id": 9, "date": 0, "chat": {"id": 201}},
                                TelegramErrorResponse(429, "Too Many Requests: retry after 600", retry_after=600))
    c2 = FakeClock()
    deferred = FanOut(t2, ledger=Ledger(), policy=RetryPolicy(max_attempts=3, max_wait=60), sleep=c2.sleep,
                      clock=c2).run("market-2026-11", jobs())
    return t, first, second, calls_after_first, clock, deferred, t2


def main() -> None:
    t, first, second, calls_after_first, clock, deferred, t2 = run()
    c.dump(t, "Broadcast with per-recipient outcomes")
    c.check(first.summary() == {"sent": 3, "blocked": 1, "invalid": 1, "unknown": 1, "deferred": 0, "skipped": 0},
            f"first run {first.summary()}")
    c.check(3 in clock.sleeps, "429: waited retry_after (3 s) before retrying the same recipient")
    c.check(calls_after_first == 7, "6 recipients + 1 retry = 7 calls: no tight loop")
    c.check(all(s <= 3 for s in clock.sleeps) and sum(1 for s in clock.sleeps if s < 1) >= 1,
            "throttle spaces calls (1/25 s) and never sleeps longer than needed")
    c.check(second.summary()["skipped"] == 3 and second.blocked == ["202"] and second.unknown == ["205"] and
            len(t.calls) == calls_after_first + 1, "re-run: sent skipped, blocked and unknown not resent, invalid retried")
    p202 = t.params_of("sendMessage")[1]
    c.check("<b>Bo_b*</b>" in p202["text"] and p202["entities"][0] == {"type": "bold", "offset": 4, "length": 12},
            "hostile name stays literal text; bold is an entity")
    c.check(deferred.deferred == ["202", "203", "204", "205", "206"] and len(t2.calls) == 2,
            "a 600 s flood wait defers the remaining 5 recipients (no sleeping for minutes)")


if __name__ == "__main__":
    main()
