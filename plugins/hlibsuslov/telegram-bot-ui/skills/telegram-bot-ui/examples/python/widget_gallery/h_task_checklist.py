"""task-checklist: kanban-lite checklist in a private chat.

Request: "t:<id>@rev" -> cycle the task's status To do -> Doing -> Done -> To do. A stale verb:
the widget sends the revision it drew, so a tap on an outdated list is refused with the fresh state.
"""
from __future__ import annotations

from .core import Action, BadRequest, Ctx, Spec, load_demo


def decide(state: dict, act: Action, ctx: Ctx):
    if act.verb != "t":
        raise BadRequest(act.raw)
    tid = act.int_arg(0, 999)
    tasks = [list(t) for t in state.get("t", [])]
    for t in tasks:
        if t[0] == tid:
            t[2] = (t[2] + 1) % 3
            return {**state, "t": tasks}, {}
    raise BadRequest(act.raw)


SPEC = Spec(name="task-checklist", decide=decide, demo=load_demo("task-checklist"), stale_verbs=frozenset({"t"}))
