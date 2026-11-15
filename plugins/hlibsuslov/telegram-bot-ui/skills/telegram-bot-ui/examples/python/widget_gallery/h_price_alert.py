"""price-alert: configure a price alert for an asset in a private chat.

Request: "set:<above|below>:<price>:<once|every>" - absolute (it names the whole alert), so it needs
no revision. Prices are decimal strings in 0.05 steps; chat_data keeps cents (integers, no float drift).
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from .core import Action, BadRequest, Ctx, Spec, load_demo

DIRECTIONS = ("above", "below")
MODES = ("once", "every")


def decide(state: dict, act: Action, ctx: Ctx):
    if act.verb != "set":
        raise BadRequest(act.raw)
    parts = act.arg.split(":")
    if len(parts) != 3 or parts[0] not in DIRECTIONS or parts[2] not in MODES:
        raise BadRequest(act.raw)
    try:
        cents = Decimal(parts[1]) * 100
    except InvalidOperation:
        raise BadRequest(act.raw) from None
    if not cents.is_finite() or cents != cents.to_integral_value() or cents % 5 or not 5 <= cents <= 10_000_000:
        raise BadRequest(act.raw)
    cents = int(cents)
    px = state["px"]
    if (parts[0] == "above" and cents <= px) or (parts[0] == "below" and cents >= px):
        raise BadRequest(act.raw)
    new = {k: v for k, v in state.items() if k != "at"}
    new = {**new, "st": "active", "dir": parts[0], "th": cents, "mode": parts[2]}
    return (None if new == state else new), {}     # the same alert again: nothing to edit


SPEC = Spec(name="price-alert", decide=decide, demo=load_demo("price-alert"))
