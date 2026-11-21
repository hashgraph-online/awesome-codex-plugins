"""media-carousel: five slides with a favorite flag per slide (private chat).

Request: "fav:<i>@<rev>" toggles slide i (0-4) in the favorites bitmask. The toggle depends on what
the user saw, so it is a stale verb. Swiping and the arrows never reach the bot.
"""
from __future__ import annotations

from .core import Action, BadRequest, Ctx, Spec, load_demo

SLIDES = 5


def decide(state: dict, act: Action, ctx: Ctx):
    if act.verb != "fav" or "c" not in state:
        raise BadRequest(act.raw)
    i = act.int_arg(0, SLIDES - 1)
    flags = int(state.get("f", 0)) ^ (1 << i)
    msg = "Added to favorites" if flags >> i & 1 else "Removed from favorites"
    return {**state, "f": flags}, {"msg": msg}


SPEC = Spec(name="media-carousel", decide=decide, demo=load_demo("media-carousel"),
            stale_verbs=frozenset({"fav"}))
