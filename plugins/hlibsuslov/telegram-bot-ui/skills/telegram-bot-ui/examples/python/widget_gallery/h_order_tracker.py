"""order-tracker: delivery order timeline (private chat, production).

Requests: "sync" (background) -> the current state; "call" -> the courier is asked to phone the
customer (only while the order is on its way); "help" -> a support thread is opened, any state.
The step and the times are written by the delivery system with editMessageWidgetData, not by taps.
"""
from __future__ import annotations

from .core import Action, BadRequest, Ctx, Spec, load_demo


def decide(state: dict, act: Action, ctx: Ctx):
    if act.verb == "sync":
        return None, {}
    if act.verb == "help":
        return None, {"msg": "Support will write to you here in a minute"}
    if act.verb == "call":
        if state.get("m") == 2 or not 2 <= state.get("s", 0) <= 3:
            raise BadRequest(act.raw)
        return None, {"msg": f"{state.get('cr', 'The courier')} will call you shortly"}
    raise BadRequest(act.raw)


SPEC = Spec(name="order-tracker", decide=decide, demo=load_demo("order-tracker"))
