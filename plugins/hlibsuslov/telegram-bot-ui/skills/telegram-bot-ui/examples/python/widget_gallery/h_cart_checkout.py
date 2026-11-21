"""cart-checkout: cart with quantity steppers, delivery option and Checkout (private chat, production).

Requests: "q:<line>:<+1|-1>@rev" changes a line (stale verb: the line index means what the user
saw; one step below 1 removes the line), "dl:<i>" picks the delivery option (absolute),
"checkout" locks the cart and answers with the amount to pay. Once awaiting payment (ph=1)
the cart is read-only. The payment itself is not part of this widget.
"""
from __future__ import annotations

from .core import Action, BadRequest, Ctx, Spec, load_demo

MAX_QTY = 9


def total(state: dict) -> int:
    sub = sum(q * unit for _, _, q, unit in state["it"])
    pc = state.get("pc")
    off = sub * pc[1] // 100 if pc else 0
    return sub - off + state["dm"][state["dl"]][1]


def decide(state: dict, act: Action, ctx: Ctx):
    if state.get("ph") or not state.get("it"):
        raise BadRequest(act.raw)
    if act.verb == "q":
        line, _, step = act.arg.partition(":")
        if not line.isdigit() or step not in ("+1", "-1") or int(line) >= len(state["it"]):
            raise BadRequest(act.raw)
        items = [list(x) for x in state["it"]]
        qty = items[int(line)][2] + int(step)
        if qty > MAX_QTY:
            return None, {"err": "max", "msg": f"At most {MAX_QTY} per item"}
        if qty < 1:
            del items[int(line)]
        else:
            items[int(line)][2] = qty
        return {**state, "it": items}, {}
    if act.verb == "dl":
        i = act.int_arg(0, len(state["dm"]) - 1)
        return (None, {}) if i == state["dl"] else ({**state, "dl": i}, {})
    if act.verb == "checkout":
        return {**state, "ph": 1}, {"msg": f"Pay {total(state) / 100:.2f} {state['cur']} to place the order"}
    raise BadRequest(act.raw)


SPEC = Spec(name="cart-checkout", decide=decide, demo=load_demo("cart-checkout"), stale_verbs=frozenset({"q"}))
