"""rating-feedback: stars plus tag chips for one delivered order (private chat).

Request: "r:<stars 1-5>:<tag bitmask>" (absolute) -> stores the rating once and returns the thanks
state with a coupon code. A second rating is refused. Stars and chips are local until Send.
Free text cannot be typed in a widget: the "Write a comment" button deep-links into the bot chat.
"""
from __future__ import annotations

from .core import Action, BadRequest, Ctx, Spec, load_demo

COUPON = "THANKS10"   # stand-in: a real bot issues a unique single-use code


def decide(state: dict, act: Action, ctx: Ctx):
    if act.verb != "r" or state.get("k", 0) != 0 or "pos" not in state:
        raise BadRequest(act.raw)
    stars_raw, _, mask_raw = act.arg.partition(":")
    try:
        stars, mask = int(stars_raw), int(mask_raw)
    except ValueError:
        raise BadRequest(act.raw) from None
    tags = state["pos"] if stars > 3 else state["neg"]
    if not 1 <= stars <= 5 or not 0 <= mask < 1 << len(tags):
        raise BadRequest(act.raw)
    return {**state, "v": stars, "m": mask, "k": 1, "c": COUPON}, {"msg": "Thanks for the feedback"}


SPEC = Spec(name="rating-feedback", decide=decide, demo=load_demo("rating-feedback"))
