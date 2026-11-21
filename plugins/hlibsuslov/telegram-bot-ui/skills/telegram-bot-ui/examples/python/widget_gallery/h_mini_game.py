"""mini-game: "Stop the beat", a five-round timing game played locally (private chat).

Request: "score:<0-500>" sent once when the round set ends. The score is client-reported, fine for a
casual game; a bot that ranks for prizes needs its own plausibility checks. Only a new best edits
state (best and rank); a lower score is answered with a message and leaves state alone.
"""
from __future__ import annotations

from .core import Action, BadRequest, Ctx, Spec, load_demo

MAX_SCORE = 500
PLAYERS = 2380


def rank_for(score: int) -> int:
    """Stand-in for a leaderboard lookup: monotonic, 1 for a perfect score."""
    return 1 + (MAX_SCORE - score) ** 2 // 484


def decide(state: dict, act: Action, ctx: Ctx):
    if act.verb != "score":
        raise BadRequest(act.raw)
    score = act.int_arg(0, MAX_SCORE)
    best = state.get("b", 0)
    if score <= best:
        return None, {"msg": f"Not a new best. Your best is {best}"}
    return {**state, "b": score, "k": rank_for(score), "n": PLAYERS}, {"msg": f"New best: {score}"}


SPEC = Spec(name="mini-game", decide=decide, demo=load_demo("mini-game"))
