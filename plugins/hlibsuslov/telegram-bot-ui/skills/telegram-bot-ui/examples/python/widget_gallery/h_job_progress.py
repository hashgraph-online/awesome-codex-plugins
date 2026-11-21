"""job-progress: long export job in a private chat.

Requests: "sync" (background; the stand-in worker advances the job from the elapsed time),
"cancel" (running or queued -> failed with a cancelled line), "retry" (failed -> queued again).
The widget derives its elapsed timer from t0; the server only moves the state forward.
"""
from __future__ import annotations

from .core import Action, BadRequest, Ctx, Spec, load_demo

DURATION = 90   # seconds a job takes in this stand-in worker


def decide(state: dict, act: Action, ctx: Ctx):
    now, st = int(ctx.now), state.get("st")
    if act.verb == "sync":
        if st == "queued" and now - state["t0"] >= 5:
            return {**state, "st": "running", "sg": 1, "t0": now, "at": now, "eta": DURATION}, {}
        if st != "running":
            return None, {}
        el = now - state["t0"]
        if el >= DURATION:
            return {**state, "st": "done", "sg": 4, "p": state["n"], "end": now, "eta": 0}, {}
        p = state["n"] * el // DURATION
        sg = 1 if el < DURATION * 0.4 else 2 if el < DURATION * 0.8 else 3
        if (p, sg) == (state["p"], state["sg"]):
            return None, {}
        return {**state, "p": p, "sg": sg, "at": now, "eta": DURATION - el}, {}
    if act.verb == "cancel":
        if st not in ("queued", "running"):
            raise BadRequest(act.raw)
        return {**state, "st": "failed", "end": now, "err": "Cancelled by you"}, {}
    if act.verb == "retry":
        if st != "failed":
            raise BadRequest(act.raw)
        new = {k: v for k, v in state.items() if k not in ("end", "err", "eta", "at")}
        return {**new, "st": "queued", "sg": 0, "p": 0, "t0": now}, {}
    raise BadRequest(act.raw)


SPEC = Spec(name="job-progress", decide=decide, demo=load_demo("job-progress"))
