"""leaderboard: top players plus a one-vote-per-user poll. SHARED widget (public_data).

Request: "v:<i>" -> record the vote. Votes are kept server-side in the widget's memo (one per
shared widget, so the key is effectively (widget_id, from.id) as the Guide asks), never in the
shared state that every viewer sees; changing a vote moves it. The answer carries
"my" (the asker's own option) so the widget can remember it.
"""
from __future__ import annotations

from .core import Action, BadRequest, Ctx, Spec, load_demo

def decide(state: dict, act: Action, ctx: Ctx):
    if act.verb != "v":
        raise BadRequest(act.raw)
    poll = state.get("poll")
    if not poll:
        raise BadRequest(act.raw)
    i = act.int_arg(0, len(poll["o"]) - 1)
    if poll.get("cl"):
        return None, {"err": "closed"}
    votes = ctx.memo.setdefault("votes", {})     # user id -> option (the bot's database in production)
    before = votes.get(ctx.user_id)
    if before == i:
        return None, {"my": i}
    opts = [list(o) for o in poll["o"]]
    if before is not None:
        opts[before][1] = max(0, opts[before][1] - 1)
    opts[i][1] += 1
    votes[ctx.user_id] = i
    return {**state, "poll": {**poll, "o": opts}}, {"my": i}


SPEC = Spec(name="leaderboard", decide=decide, demo=load_demo("leaderboard"), field="public_data",
            shared=True, owner_only=False)
