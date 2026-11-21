"""R74 - Recover after the owner's Premium lapses: one retry, a kill switch, no loop.

The bot relies on the owner-Premium route. One day Telegram refuses a message because of
its custom emoji. `IconSystem.send` retries that message ONCE without custom emoji, flips
the shared kill switch and logs it; every later message goes out as Unicode at the first
attempt. An unrelated 400 is not retried. If even the stripped retry fails, the error is
raised - there is never a second retry. After the owner renews Premium, an operator
resets the switch.

The exact error text for refused custom emoji is not documented by Telegram; the
description below is illustrative. Matching uses CUSTOM_EMOJI_ERROR_HINTS (extend it with
what your logs show).

Run:  py -3 examples/python/recipes/r74_premium_lapse.py
"""
from __future__ import annotations

import _common as c
from icons.emoji_demo import VOCAB, resolve
from tgkit.errors import TelegramError
from tgkit.icons import Eligibility, IconSystem, SendContext, uses_custom_emoji
from tgkit.transport import FakeTransport, TelegramErrorResponse

CHAT = 111111111
REFUSED = TelegramErrorResponse(400, "Bad Request: custom emoji can't be used (illustrative text)")


def screen(n: int) -> dict:
    return {"chat_id": CHAT, "parse_mode": "HTML", "text": f"<b>🔔 Alert {n}</b>\nPrice crossed your level.",
            "reply_markup": {"inline_keyboard": [[{"text": "⚙️ Settings", "callback_data": "s"}]]}}


def make_icons(log: list[str]) -> IconSystem:
    icon_map, _ = resolve(["demo_line_icons"], ["notifications", "settings"], family="demo-line")
    return IconSystem(icon_map["icons"], vocabulary=VOCAB, eligibility=Eligibility(owner_premium=True), log=log.append)


def run():
    log: list[str] = []
    icons = make_icons(log)
    t = FakeTransport().script("sendMessage", {"message_id": 1}, REFUSED)
    ctx = SendContext("private")
    icons.send(t, "sendMessage", screen(1), ctx)      # works with icons
    icons.send(t, "sendMessage", screen(2), ctx)      # refused -> one retry without icons
    icons.send(t, "sendMessage", screen(3), ctx)      # kill switch on: Unicode at the first attempt
    return t, icons, log


def main() -> None:
    t, icons, log = run()
    c.dump(t, "Premium lapse")
    calls = t.params_of("sendMessage")
    c.check(len(calls) == 4 and [uses_custom_emoji(p) for p in calls] == [True, True, False, False],
            "refused once -> exactly one retry without custom emoji, later messages plain from the start")
    c.check(icons.killed and len(log) == 1 and "illustrative" in log[0], "kill switch flipped and logged once")
    c.check(calls[2]["reply_markup"]["inline_keyboard"][0][0]["text"] == "⚙️ Settings",
            "the retry keeps meaning: icons degrade to their Unicode fallbacks together")

    # An unrelated validation error is not treated as an emoji problem.
    icons2 = make_icons([])
    t2 = FakeTransport().script("sendMessage", TelegramErrorResponse(400, "Bad Request: chat not found"))
    try:
        icons2.send(t2, "sendMessage", screen(4), SendContext("private"))
        raise AssertionError("expected TelegramError")
    except TelegramError:
        pass
    c.check(len(t2.calls) == 1 and not icons2.killed, "unrelated 400 -> no retry, no kill switch")

    # Even the stripped retry fails: raise, never loop.
    icons3 = make_icons([])
    t3 = FakeTransport().script("sendMessage", REFUSED, REFUSED, REFUSED)
    try:
        icons3.send(t3, "sendMessage", screen(5), SendContext("private"))
        raise AssertionError("expected TelegramError")
    except TelegramError:
        pass
    c.check(len(t3.calls) == 2, "second failure is raised after exactly two attempts")

    icons.reset_kill_switch()                          # owner confirmed Premium is back
    icons.send(t, "sendMessage", screen(6), SendContext("private"))
    c.check(uses_custom_emoji(t.params_of("sendMessage")[-1]), "after renewal + reset, icons return")


if __name__ == "__main__":
    main()
