"""R03 - Multi-step form: inline keyboard + force_reply, disabled Submit,
validation, Back, stale taps, and a double Submit that doesn't duplicate.

Run:  py -3 examples/python/recipes/r03_multi_step_form.py
"""
from __future__ import annotations

import re

import _common as c
from tgkit.forms import FormRunner, FormSession, Step
from tgkit.transport import FakeTransport

USER = CHAT = 111111111


def steps() -> list[Step]:
    return [
        Step("size", "Choose a pizza size or type it.", lambda v: None if v in ("S", "M", "L") else "Choose S, M or L.",
             options=["S", "M", "L"]),
        Step("phone", "Send a phone number for the courier.",
             lambda v: None if re.fullmatch(r"\+?\d[\d ]{6,14}", v) else "That doesn't look like a phone number."),
        Step("time", "When should we deliver?", lambda v: None, options=["ASAP", "In 1 hour"]),
    ]


def cq(data: str, message_id: int, qid: str = "q") -> dict:
    return {"id": qid, "from": {"id": USER, "is_bot": False, "first_name": "Alice"},
            "message": {"message_id": message_id, "chat": {"id": CHAT, "type": "private"}}, "data": data}


def run(transport: FakeTransport | None = None):
    t = transport or FakeTransport()
    created: list[str] = []

    def submit(s: FormSession) -> str:
        created.append(s.form_id)          # the order service is idempotent by form_id too
        return "ORD-1042"

    runner = FormRunner(t, submit)
    s = FormSession(form_id="F7", user_id=USER, chat_id=CHAT, steps=steps())
    runner.start(s)
    first = s.prompt_message_id
    outcomes = [
        runner.on_callback(cq("f:F7:0:o:2", first)),                      # tap "L"
        runner.on_text(CHAT, USER, "call me", reply_to=s.prompt_message_id),  # invalid phone
        runner.on_callback(cq("f:F7:0:o:0", first)),                      # stale: old step's button
        runner.on_text(CHAT, USER, "+380 44 123 4567", reply_to=s.prompt_message_id),
        runner.on_callback(cq("f:F7:2:back", s.prompt_message_id)),       # Back keeps answers
        runner.on_text(CHAT, USER, "+380 44 765 4321", reply_to=s.prompt_message_id),
        runner.on_callback(cq("f:F7:2:o:1", s.prompt_message_id)),        # "In 1 hour"
        runner.on_callback(cq("f:F7:submit", s.prompt_message_id, "q1")),
        runner.on_callback(cq("f:F7:submit", s.prompt_message_id, "q2")),  # double tap / retry
    ]
    return t, s, outcomes, created


def main() -> None:
    t, s, outcomes, created = run()
    c.dump(t, "Multi-step form")
    c.check(outcomes == ["accepted", "invalid", "stale", "accepted", "back", "accepted", "accepted",
                         "submitted", "duplicate"], f"flow outcomes {outcomes}")
    sends = t.params_of("sendMessage")
    c.check(all(m["reply_markup"].get("force_reply") is True for m in sends),
            "every step has an inline keyboard AND the reply UI (InlineKeyboardMarkup.force_reply)")
    c.check(all(e["reply_markup"].get("force_reply") is True
                for e in t.params_of("editMessageReplyMarkup") + t.params_of("editMessageText")),
            "edits repeat force_reply: the field can't be changed by an edit")
    submit_before = sends[-2]["reply_markup"]["inline_keyboard"][-1][0]
    c.check("disabled" in submit_before and "callback_data" not in submit_before,
            "Submit shown disabled until all answers are valid")
    c.check(created == ["F7"], "one order despite two Submit taps")
    c.check(s.answers == {"size": "L", "phone": "+380 44 765 4321", "time": "In 1 hour"},
            "Back kept earlier answers; the corrected phone replaced the old one")


if __name__ == "__main__":
    main()
