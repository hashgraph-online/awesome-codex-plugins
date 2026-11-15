"""receipt: invoice with a status stamp (private chat, production).

Request: "refund" -> only for a paid receipt: the bot files the request, sets rq and answers with
a message. Copy number (copyText) and Download PDF (openLink) are taps handled by the client.
"""
from __future__ import annotations

from .core import Action, BadRequest, Ctx, Spec, load_demo


def decide(state: dict, act: Action, ctx: Ctx):
    if act.verb == "refund" and not act.arg and state.get("ps") == 0 and not state.get("rq"):
        return {**state, "rq": 1}, {"msg": "Refund requested. We reply within 2 business days."}
    raise BadRequest(act.raw)


SPEC = Spec(name="receipt", decide=decide, demo=load_demo("receipt"))
