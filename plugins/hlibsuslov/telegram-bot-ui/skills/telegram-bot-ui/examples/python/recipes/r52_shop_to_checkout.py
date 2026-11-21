"""R52 - Shop card to checkout: product card (variants, quantity, stock) -> cart widget
(quantities with revisions, delivery choice, checkout) -> receipt widget after payment.
Three widgets, three messages, one order; payment itself stays in the bot's payment flow.

Run:  py -3 examples/python/recipes/r52_shop_to_checkout.py
"""
from __future__ import annotations

import json

import _common as c
from tgkit.router import Router
from tgkit.transport import FakeTransport
from widget_gallery import GalleryBot

BUYER = 111111111


def run(transport: FakeTransport | None = None):
    t = transport or FakeTransport()
    bot = GalleryBot(t)
    router = Router()
    router.on("widget_query")(bot.handle)
    ids = iter(range(1, 100))

    def tap(mid: int, data: str) -> None:
        upd = c.fixture("widget_query_cart_add.json")
        upd["widget_query"].update({"id": f"81234567890123520{next(ids):02d}", "message_id": mid, "data": data})
        router.dispatch(upd)

    card = bot.send("product-card", BUYER)["message_id"]
    tap(card, "add:1:2")          # Moss / 750 ml, 2 units: stock 3 -> 1, cart count 2
    tap(card, "add:1:2")          # only 1 left: refused in words, nothing reserved
    # The bot opens the cart as its own widget (the product card stays a product card).
    cart = bot.send("cart-checkout", BUYER)["message_id"]
    tap(cart, "q:1:+1@0")         # paper filters 2 -> 3, as seen at revision 0
    tap(cart, "q:0:+1@0")         # stale: the widget drew revision 0, the cart is at 1
    tap(cart, "dl:2")             # express delivery (absolute choice, no revision)
    tap(cart, "checkout")         # read-only "awaiting payment"; the bot sends its invoice in the chat
    # Payment confirmed by the bot's payment flow -> a receipt widget with the copyable number.
    bot.send("receipt", BUYER)
    return t, bot, (card, cart), router


def main() -> None:
    t, bot, (card, cart), router = run()
    c.dump(t, "Shop card to checkout")
    answers = [json.loads(p["data"]) for p in t.params_of("answerWidgetQuery")]
    c.check(len(answers) == 6, "every query answered exactly once")
    c.check(answers[0]["ok"] and answers[0]["s"]["ct"] == 2, "add reserves stock and counts the cart")
    c.check(answers[1].get("err") == "stock" and "left" in answers[1]["msg"], "short stock refused in words")
    c.check(answers[3]["err"] == "stale", "a quantity tap from an old view is refused with the fresh cart")
    rec = bot.store.records[f"msg:{BUYER}:{cart}"]
    c.check(rec.state["it"][1][2] == 3 and rec.state["dl"] == 2 and rec.state["ph"] == 1,
            "cart committed: one increment, express delivery, awaiting payment")
    c.check("Pay" in answers[5]["msg"], "checkout tells the next step in words")
    c.check([m for m, _ in t.calls].count("sendWidget") == 3, "product, cart and receipt are separate widgets")
    c.check(all(p.get("reply_markup") for p in t.params_of("sendWidget")), "each widget ships a keyboard alternative")


if __name__ == "__main__":
    main()
