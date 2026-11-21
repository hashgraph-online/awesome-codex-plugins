"""product-card: product with variants and an Add to cart action (private chat, production).

Requests: "add:<variant>:<qty>" -> the bot checks the stock, reserves the units, edits chat_data
(stock down, ct up) and answers with the new state. The variant is an index into k
(colour * sizes + size); it names a fixed catalogue slot, so the verb is not stale-sensitive.
"""
from __future__ import annotations

from .core import Action, BadRequest, Ctx, Spec, load_demo


def decide(state: dict, act: Action, ctx: Ctx):
    if act.verb != "add":
        raise BadRequest(act.raw)
    variant, _, qty = act.arg.partition(":")
    if not (variant.isdigit() and qty.isdigit() and 1 <= int(qty) <= 9 and int(variant) < len(state["k"])):
        raise BadRequest(act.raw)
    i, n = int(variant), int(qty)
    have = state["k"][i]
    if have < n:
        msg = f"Only {have} left" if have else "Sold out"
        return None, {"err": "stock", "msg": msg}
    stock = list(state["k"])
    stock[i] = have - n
    return {**state, "k": stock, "ct": state.get("ct", 0) + n}, {"msg": "Added to cart"}


SPEC = Spec(name="product-card", decide=decide, demo=load_demo("product-card"))
