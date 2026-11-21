"""R73 - Mixed eligibility: one bot, icons where the API allows them, Unicode elsewhere.

The owner has Premium; the bot has no Fragment usernames. The same handlers produce the
same screens for every destination; `IconSystem.for_context` decides per message:
private / group / supergroup sent directly by the bot -> custom emoji; the channel
announcement, a business-account reply and an inline result -> Unicode (the Premium route
covers only messages directly sent by the bot to private, group and supergroup chats).

Run:  py -3 examples/python/recipes/r73_mixed_eligibility.py
"""
from __future__ import annotations

import _common as c
from icons.emoji_demo import VOCAB, resolve
from tgkit.icons import Eligibility, IconSystem, SendContext, uses_custom_emoji
from tgkit.transport import FakeTransport

SLOTS = ["announcement", "order", "delivery", "done", "help"]


def order_update(chat_id) -> dict:
    return {"chat_id": chat_id, "parse_mode": "HTML",
            "text": "<b>📦 Order #1042</b>\n🚚 Out for delivery · arrives today",
            "reply_markup": {"inline_keyboard": [[{"text": "✅ Received", "callback_data": "rcv:1042"},
                                                  {"text": "❓ Help", "callback_data": "help"}]]}}


def run():
    icon_map, _ = resolve(["demo_line_icons"], SLOTS, family="demo-line")
    icons = IconSystem(icon_map["icons"], vocabulary=VOCAB, eligibility=Eligibility(owner_premium=True))
    t = FakeTransport()
    plan = [("private", SendContext("private"), 111111111),
            ("group", SendContext("group"), -100200300),
            ("supergroup", SendContext("supergroup"), -1001234567890),
            ("channel", SendContext.channel(), "@example_shop_news"),
            ("business", SendContext("private", business=True), 222222222)]
    for label, ctx, chat in plan:
        params = order_update(chat)
        if ctx.business:
            params["business_connection_id"] = "bc-example"
        icons.send(t, "sendMessage", params, ctx)
    inline = {"inline_query_id": "q1", "results": [{"type": "article", "id": "1", "title": "Order #1042",
                                                   "input_message_content": {"message_text": "📦 Order #1042"},
                                                   "reply_markup": order_update(0)["reply_markup"]}]}
    icons.send(t, "answerInlineQuery", inline, SendContext("private", inline=True))
    return t, icons, plan


def main() -> None:
    t, icons, plan = run()
    c.dump(t, "Mixed eligibility")
    sent = t.params_of("sendMessage")
    flags = {label: uses_custom_emoji(p) for (label, _, _), p in zip(plan, sent)}
    c.check(flags == {"private": True, "group": True, "supergroup": True, "channel": False, "business": False},
            "owner Premium -> icons in private/group/supergroup, Unicode in the channel and business send")
    c.check(sent[3] == order_update("@example_shop_news"), "the channel copy is the untouched Unicode screen")
    c.check(not uses_custom_emoji(t.params_of("answerInlineQuery")[0]), "inline results stay Unicode (sent by the user)")
    for (label, ctx, _), p in zip(plan, sent):
        c.check(icons.eligibility.explain(ctx).startswith("eligible" if flags[label] else "not eligible"),
                f"{label}: {icons.eligibility.explain(ctx)}")


if __name__ == "__main__":
    main()
