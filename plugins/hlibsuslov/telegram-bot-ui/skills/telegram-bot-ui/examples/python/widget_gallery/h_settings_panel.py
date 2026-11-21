"""settings-panel: toggles, digest time and language for one user (private chat).

Requests, all absolute (so no revision is needed): "tg:<i>:<0|1>" sets toggle i, "dt:<0|1|2>" sets the
digest time, "lg:<code>" sets the language (one of the codes in state). The widget is optimistic:
it flips the control at once and rolls back if the answer is an error.
"""
from __future__ import annotations

from .core import Action, BadRequest, Ctx, Spec, load_demo


def decide(state: dict, act: Action, ctx: Ctx):
    if "n" not in state:
        raise BadRequest(act.raw)
    if act.verb == "tg":
        key, _, val = act.arg.partition(":")
        if not key.isdigit() or int(key) >= len(state["n"]) or val not in ("0", "1"):
            raise BadRequest(act.raw)
        i, on = int(key), int(val)
        flags = (state["f"] & ~(1 << i)) | (on << i)
        return (None if flags == state["f"] else {**state, "f": flags}), {}
    if act.verb == "dt":
        j = act.int_arg(0, len(state["dl"]) - 1)
        return (None if j == state["dg"] else {**state, "dg": j}), {}
    if act.verb == "lg":
        if act.arg not in [c for c, _ in state["ll"]]:
            raise BadRequest(act.raw)
        return (None if act.arg == state["lg"] else {**state, "lg": act.arg}), {}
    raise BadRequest(act.raw)


SPEC = Spec(name="settings-panel", decide=decide, demo=load_demo("settings-panel"))
