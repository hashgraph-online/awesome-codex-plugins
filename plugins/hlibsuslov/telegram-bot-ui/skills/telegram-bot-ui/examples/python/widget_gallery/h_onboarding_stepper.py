"""onboarding-stepper: 4-step setup for a bot (language, notifications, timezone, finish).

Requests: "set:<l|n|z>:<value>" -> stores one choice (absolute, validated against the options the
bot put into state); "finish" -> completes setup once every choice is made. Back/Next never reach
the bot. The step strings (titles, bodies, option labels) are localized by the bot and live in state.
"""
from __future__ import annotations

from .core import Action, BadRequest, Ctx, Spec, load_demo

KEYS = "lnz"
DONE_TEXT = "Setup complete. Alerts follow your timezone."


def decide(state: dict, act: Action, ctx: Ctx):
    if state.get("d"):
        raise BadRequest(act.raw)
    opts, vals = state.get("o"), state.get("v")
    if not opts or not vals:
        raise BadRequest(act.raw)
    if act.verb == "set":
        key, _, value = act.arg.partition(":")
        if len(key) != 1 or key not in KEYS:
            raise BadRequest(act.raw)
        i = KEYS.index(key)
        if value not in [o[0] for o in opts[i]]:
            raise BadRequest(act.raw)
        if vals[i] == value:
            return None, {}
        new_vals = list(vals)
        new_vals[i] = value
        return {**state, "v": new_vals, "p": max(state.get("p", 0), i + 1)}, {}
    if act.verb == "finish":
        if "" in vals:
            raise BadRequest(act.raw)
        return {**state, "d": 1, "p": 3, "dn": DONE_TEXT}, {"msg": "You're all set"}
    raise BadRequest(act.raw)


SPEC = Spec(name="onboarding-stepper", decide=decide, demo=load_demo("onboarding-stepper"))
