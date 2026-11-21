"""schedule-calendar: month grid with an agenda per day (private chat).

Requests: "m:<YYYY-MM>" -> edits chat_data (month and its event days);
"d:<YYYY-MM-DD>" -> answer-only data: {"d": date, "ag": [[time, title], ...]}, no state edit.
Events come from the bot's calendar store; the rule below stands in for it so payloads are stable
(months 3, 6, 9 and 12 are empty).
"""
from __future__ import annotations

import calendar
import datetime
import re

from .core import Action, BadRequest, Ctx, Spec, load_demo

TITLES = ["Standup", "Lunch with Anna", "Dentist", "Yoga", "Design review", "Pick up parcel"]
TIMES = ["09:30", "12:00", "15:00", "18:30"]


def events(year: int, month: int) -> list[int]:
    if month % 3 == 0:
        return []
    return [d for d in range(1, calendar.monthrange(year, month)[1] + 1) if (d * 5 + month) % 4 == 0]


def decide(state: dict, act: Action, ctx: Ctx):
    if act.verb == "m":
        if not re.fullmatch(r"\d{4}-\d{2}", act.arg):
            raise BadRequest(act.raw)
        y, m = int(act.arg[:4]), int(act.arg[5:])
        if not (2025 <= y <= 2028 and 1 <= m <= 12):
            raise BadRequest(act.raw)
        if state.get("m") == act.arg:
            return None, {}
        return {**state, "m": act.arg, "ev": events(y, m)}, {}
    if act.verb == "d":
        try:
            day = datetime.date.fromisoformat(act.arg)
        except ValueError:
            raise BadRequest(act.raw) from None
        if act.arg != day.isoformat() or not 2025 <= day.year <= 2028:
            raise BadRequest(act.raw)
        items: list[list[str]] = []
        if day.day in events(day.year, day.month):
            items = sorted([TIMES[(day.day + i) % 4], TITLES[(day.day + i) % 6]] for i in range(1 + day.day % 3))
        return None, {"d": act.arg, "ag": items}
    raise BadRequest(act.raw)


SPEC = Spec(name="schedule-calendar", decide=decide, demo=load_demo("schedule-calendar"))
