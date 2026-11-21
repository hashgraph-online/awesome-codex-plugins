"""quiz: multiple-choice quiz in a private chat.

Requests: "a:<qid>:<i>@rev" -> check the answer, reveal the correct option and the explanation in the
new state (a stale verb); "next@rev" -> next question or the result; "restart" -> new round.
The correct answer lives only here: chat_data never carries it before the user has answered.
"""
from __future__ import annotations

from .core import Action, BadRequest, Ctx, Spec, load_demo

BANK = [
    ("Which planet has the shortest year?", ["Mercury", "Venus", "Mars", "Jupiter"], 0,
     "Mercury orbits the Sun in about 88 days."),
    ("What is the capital of Australia?", ["Sydney", "Melbourne", "Canberra", "Perth"], 2,
     "Canberra was built as a compromise between Sydney and Melbourne."),
    ("How many bits are in a byte?", ["4", "8", "16", "32"], 1, "A byte is 8 bits."),
    ("Which gas do plants absorb for photosynthesis?", ["Oxygen", "Nitrogen", "Carbon dioxide", "Helium"], 2,
     "Plants turn CO2 and water into sugar and oxygen."),
    ("Who painted the Mona Lisa?", ["Michelangelo", "Leonardo da Vinci", "Raphael", "Titian"], 1,
     "Leonardo painted it in the early 1500s."),
]


def question(i: int, score: int) -> dict:
    t, o, _, _ = BANK[i]
    return {"q": i, "n": len(BANK), "t": t, "o": o, "sel": -1, "sc": score}


def decide(state: dict, act: Action, ctx: Ctx):
    if act.verb == "restart":
        return question(0, 0), {}
    if state.get("fin"):
        raise BadRequest(act.raw)
    q, score = state["q"], state["sc"]
    if act.verb == "a":
        qid, _, pick = act.arg.partition(":")
        try:
            qid, pick = int(qid), int(pick)
        except ValueError:
            raise BadRequest(act.raw) from None
        if qid != q or not 0 <= pick < 4 or state["sel"] >= 0:
            raise BadRequest(act.raw)
        _, _, right, why = BANK[q]
        return {**state, "sel": pick, "ok": right, "ex": why, "sc": score + (pick == right)}, {}
    if act.verb == "next":
        if state["sel"] < 0:
            raise BadRequest(act.raw)
        if q + 1 >= len(BANK):
            return {"fin": 1, "n": len(BANK), "sc": score}, {}
        return question(q + 1, score), {}
    raise BadRequest(act.raw)


SPEC = Spec(name="quiz", decide=decide, demo=load_demo("quiz"), stale_verbs=frozenset({"a", "next"}))
