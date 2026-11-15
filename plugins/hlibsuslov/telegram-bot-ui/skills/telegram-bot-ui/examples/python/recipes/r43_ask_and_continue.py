"""R43 - "Ask the operator and continue" during a coding task.

The agent hits a decision it shouldn't make alone, asks with quick choices plus
a reply field, keeps a default, reminds once, and continues either way.

Run:  py -3 examples/python/recipes/r43_ask_and_continue.py
"""
from __future__ import annotations

import _common as c
from agent_bridge.demo import START, make_bridge, reply, tap

QUESTION = ("The payments tests are flaky (3 of 20 runs fail on a timeout). "
            "How should I proceed with the refactor?")
CHOICES = ["Skip them for now", "Fix the flakiness first", "Stop and wait for me"]


def coding_task(bridge, arrivals):
    """arrivals(rec) -> updates that arrive while the agent waits."""
    rec = bridge.request_answer(QUESTION, choices=CHOICES, timeout=900, default=CHOICES[0])
    bridge.source.queue.extend(arrivals(rec))
    res = bridge.wait(rec["rid"], remind_after=600)
    plan = {CHOICES[0]: "continue_without_payments_tests", CHOICES[1]: "fix_flaky_tests",
            CHOICES[2]: "pause"}.get(res["answer"], "follow_operator_note")
    return res, plan


def run():
    b1, t1, _ = make_bridge()
    r1, p1 = coding_task(b1, lambda rec: [tap(rec, "1", uid=960001, at=START + 120)])
    b2, t2, _ = make_bridge()
    r2, p2 = coding_task(b2, lambda rec: [reply(rec, "Skip them, but open an issue with the failing seeds.",
                                                 uid=960011, at=START + 700)])
    b3, t3, _ = make_bridge()
    r3, p3 = coding_task(b3, lambda rec: [])
    return t1, t2, t3, (r1, p1), (r2, p2), (r3, p3)


def main() -> None:
    t1, t2, t3, (r1, p1), (r2, p2), (r3, p3) = run()
    c.dump(t3, "Ask and continue (no answer -> default)")
    first = t1.params_of("sendMessage")[0]
    c.check(first["reply_markup"]["force_reply"] is True and len(first["reply_markup"]["inline_keyboard"]) == 3,
            "quick choices AND a reply field in one message (10.3 force_reply on inline keyboards)")
    c.check("continue with: Skip them for now" in first["text"], "the default is stated up front")
    c.check((r1["via"], p1) == ("button", "fix_flaky_tests"), "a tap answers in one step")
    c.check(r2["via"] == "text" and r2["content_is_untrusted_data"] and p2 == "follow_operator_note",
            "a typed answer reaches the agent as data (it decides what to do with it)")
    reminders = [m for m in t2.params_of("sendMessage") if m["text"].startswith("Reminder")]
    c.check(len(reminders) == 1 and reminders[0]["reply_parameters"]["message_id"] == 1001,
            "one reminder at 10 min, as a reply to the question")
    c.check((r3["status"], r3["answer"], p3) == ("timeout", CHOICES[0], "continue_without_payments_tests"),
            "no answer in 15 min: the stated default, flagged used_default")
    last = t3.params_of("editMessageText")[-1]
    c.check(last["reply_markup"]["inline_keyboard"][0][0] == {"text": "No answer — continued with: Skip them for now",
                                                               "disabled": {}} and last["reply_markup"]["force_reply"],
            "the question closes with a disabled result button (force_reply kept: it can't change in an edit)")


if __name__ == "__main__":
    main()
