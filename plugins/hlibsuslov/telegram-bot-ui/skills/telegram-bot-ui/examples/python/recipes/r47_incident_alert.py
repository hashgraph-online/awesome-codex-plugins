"""R47 - Incident alert with Acknowledge / Escalate and automatic escalation.

The primary on-call gets a loud alert with two buttons. Acknowledge stops the
clock; Escalate (or 5 minutes of silence) pages the secondary. Only the paged
person's numeric id can acknowledge their page.

Run:  py -3 examples/python/recipes/r47_incident_alert.py
"""
from __future__ import annotations

import _common as c
from agent_bridge.demo import OPERATOR, START, make_bridge, tap

SECONDARY = 444444444
ALERT = "🔴 INC-311 · checkout error rate 18% (threshold 2%) since 03:12 UTC\nRunbook: restart payment-gateway pods"
CHOICES = ["Acknowledge", "Escalate"]


def page(bridge, chat: int, arrivals, ack_window: float = 300):
    rec = bridge.request_answer(ALERT, choices=CHOICES, timeout=ack_window, chat_id=chat,
                                approvers={chat}, allow_text=False)
    bridge.source.queue.extend(arrivals(rec))
    return bridge.wait(rec["rid"])


def incident(bridge, primary_arrivals, secondary_arrivals):
    first = page(bridge, OPERATOR, primary_arrivals)
    if first["status"] == "answered" and first["answer"] == "Acknowledge":
        return {"acked_by": first["by"], "escalated": False}
    second = page(bridge, SECONDARY, secondary_arrivals)
    acked = second["status"] == "answered" and second["answer"] == "Acknowledge"
    if not acked:
        bridge.notify("INC-311 is still unacknowledged after two pages. Calling the phone tree.")
    return {"acked_by": second["by"] if acked else None, "escalated": True}


def run():
    b1, t1, _ = make_bridge(operators={OPERATOR, SECONDARY})
    r1 = incident(b1, lambda rec: [tap(rec, "0", uid=990001, at=START + 40)], lambda rec: [])
    b2, t2, _ = make_bridge(operators={OPERATOR, SECONDARY})
    r2 = incident(b2, lambda rec: [tap(rec, "0", user=SECONDARY, uid=990011, at=START + 30)],   # wrong person
                  lambda rec: [tap(rec, "0", user=SECONDARY, uid=990012, at=rec["created"] + 60)])
    b3, t3, _ = make_bridge(operators={OPERATOR, SECONDARY})
    r3 = incident(b3, lambda rec: [tap(rec, "1", uid=990021, at=START + 20)], lambda rec: [])
    return (t1, r1), (t2, r2), (t3, r3)


def main() -> None:
    (t1, r1), (t2, r2), (t3, r3) = run()
    c.dump(t2, "Incident: no ack from primary -> secondary acknowledges")
    first = t1.params_of("sendMessage")[0]
    c.check("force_reply" not in first["reply_markup"] and "disable_notification" not in first,
            "a loud alert with buttons only (no reply field)")
    c.check(r1 == {"acked_by": OPERATOR, "escalated": False}, "primary acknowledges -> no escalation")
    c.check(r2 == {"acked_by": SECONDARY, "escalated": True},
            "the secondary can't ack the primary's page; after 5 min the secondary is paged and acks")
    pages = [p["chat_id"] for p in t2.params_of("sendMessage")]
    c.check(pages == [OPERATOR, SECONDARY], "escalation pages the next person in their own chat")
    c.check(r3["escalated"] and t3.params_of("sendMessage")[-1]["text"].startswith("INC-311 is still"),
            "Escalate escalates at once; two silent pages end in an explicit fallback, never silence")
    closed = t2.params_of("editMessageText")[0]["reply_markup"]["inline_keyboard"][0][0]
    c.check(closed["disabled"] == {} and "No answer" in closed["text"], "the unanswered page is closed visibly")


if __name__ == "__main__":
    main()
