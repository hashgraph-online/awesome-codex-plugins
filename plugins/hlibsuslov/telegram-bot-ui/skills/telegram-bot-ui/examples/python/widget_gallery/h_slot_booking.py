"""slot-booking: appointment picker (private chat, production).

Requests: "pick:<day>:<HHMM>@rev" selects a slot (stale verb: the slot may be taken meanwhile; a
taken slot is refused with a message), "book" confirms the selection, "cancel" frees the booking.
chat_data carries the free slots of the next seven days as hex bitmasks (bit i = slot i is free,
slot i starts at 09:00 + 30 min * i). The day strip in the widget is local UI.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .core import Action, BadRequest, Ctx, Spec, load_demo

SLOTS, DAYS = 18, 7


def parse_slot(raw: str) -> tuple[int, int]:
    """'<day>:<HHMM>' -> (day, slot index); anything off the 09:00-17:30 half-hour grid is invalid."""
    day, _, hhmm = raw.partition(":")
    if not (day.isdigit() and hhmm.isdigit() and len(hhmm) == 4):
        raise BadRequest(raw)
    minutes = int(hhmm[:2]) * 60 + int(hhmm[2:])
    idx, rest = divmod(minutes - 540, 30)
    if not (0 <= int(day) < DAYS and 0 <= idx < SLOTS and rest == 0):
        raise BadRequest(raw)
    return int(day), idx


def is_free(state: dict, day: int, idx: int) -> bool:
    return bool(int(state["m"][day], 16) >> idx & 1)


def with_bit(state: dict, day: int, idx: int, free: bool) -> list[str]:
    masks = list(state["m"])
    value = int(masks[day], 16)
    masks[day] = format(value | 1 << idx if free else value & ~(1 << idx), "x")
    return masks


def label(state: dict, raw: str) -> str:
    day, idx = parse_slot(raw)
    when = datetime.fromtimestamp(state["d0"], timezone.utc) + timedelta(days=day, minutes=540 + 30 * idx)
    return when.strftime("%a %d %b, %H:%M")


def decide(state: dict, act: Action, ctx: Ctx):
    if act.verb == "pick":
        if state.get("bk"):
            raise BadRequest(act.raw)
        day, idx = parse_slot(act.arg)
        if not is_free(state, day, idx):
            return None, {"err": "taken", "msg": "That slot was just taken. Pick another time."}
        return {**state, "sel": act.arg}, {}
    if act.verb == "book":
        sel = state.get("sel")
        if not sel or state.get("bk"):
            raise BadRequest(act.raw)
        day, idx = parse_slot(sel)
        if not is_free(state, day, idx):
            return {**state, "sel": ""}, {"err": "taken", "msg": "That slot was just taken. Pick another time."}
        return ({**state, "m": with_bit(state, day, idx, False), "sel": "", "bk": sel},
                {"msg": f"Booked for {label(state, sel)}"})
    if act.verb == "cancel":
        bk = state.get("bk")
        if not bk:
            raise BadRequest(act.raw)
        day, idx = parse_slot(bk)
        return {**state, "m": with_bit(state, day, idx, True), "bk": ""}, {"msg": "Booking cancelled"}
    raise BadRequest(act.raw)


SPEC = Spec(name="slot-booking", decide=decide, demo=load_demo("slot-booking"),
            stale_verbs=frozenset({"pick"}))
