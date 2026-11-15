"""metrics-dashboard: service health card for a monitoring bot (private chat, production).

Requests: "sync" (background and the Refresh tap) -> current state in the answer;
"p:<1h|24h|7d>" -> the bot recomputes the series for that period, edits chat_data, answers.
The full time series lives in the bot's metrics store; chat_data carries <= 24 points.
"""
from __future__ import annotations

from .core import Action, BadRequest, Ctx, Spec, load_demo

PERIODS = {"1h": 12, "24h": 24, "7d": 14}   # points per period, sized to fit 1024 bytes


def series(period: str, salt: int) -> tuple[list[int], list[int]]:
    """Stand-in for a metrics query: deterministic, so tests and payloads are stable."""
    n = PERIODS[period]
    lat = [170 + (i * 37 + salt) % 45 for i in range(n)]
    err = [1 + (i * 11 + salt) % 9 for i in range(n)]
    return lat, err


def decide(state: dict, act: Action, ctx: Ctx):
    if act.verb == "sync":
        return None, {}
    if act.verb == "p":
        if act.arg not in PERIODS:
            raise BadRequest(act.raw)
        if state.get("p") == act.arg:
            return None, {}
        lat, err = series(act.arg, len(act.arg))
        return {**state, "p": act.arg, "lat": lat, "err": err, "at": int(ctx.now)}, {}
    raise BadRequest(act.raw)


SPEC = Spec(name="metrics-dashboard", decide=decide, demo=load_demo("metrics-dashboard"))
