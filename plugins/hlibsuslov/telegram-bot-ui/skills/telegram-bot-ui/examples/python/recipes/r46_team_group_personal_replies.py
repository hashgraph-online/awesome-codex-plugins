"""R46 - The agent in a team group: one shared card, personal replies, nothing private in public.

Everyone sees the shared job card. "My failures" shows each member only the
tests they own (ephemeral reply, 10.3/10.4). The log stays in the operator's
private chat. Strangers in the group and anonymous admins get nothing.

Run:  py -3 examples/python/recipes/r46_team_group_personal_replies.py
"""
from __future__ import annotations

import _common as c
from agent_bridge.demo import OPERATOR, STRANGER, TEAM_GROUP, TEAMMATE, make_bridge
from tgkit.ephemeral import PersonalPanels

OWNERS = {OPERATOR: ["checkout.spec.ts › pays with saved card"],
          TEAMMATE: ["search.spec.ts › filters by price", "search.spec.ts › empty query"]}


def render(user_id: int) -> str:
    mine = OWNERS.get(user_id, [])
    return ("Your failing tests:\n" + "\n".join(f"• {m}" for m in mine)) if mine else "None of the failures are yours."


def group_tap(uid: int, user: int, data: str, mid: int) -> dict:
    return {"update_id": uid, "callback_query": {
        "id": f"4382000000{uid}", "from": {"id": user, "is_bot": False, "first_name": "Member"},
        "message": {"message_id": mid, "date": 0, "chat": {"id": TEAM_GROUP, "type": "supergroup"}},
        "chat_instance": "-5550003", "data": data}}


def run():
    b, t, clock = make_bridge(members={TEAMMATE}, groups={TEAM_GROUP})
    card = b.call("sendMessage", {"chat_id": TEAM_GROUP, "text": "CI #142 failed: 3 of 60 E2E specs.",
                                  "reply_markup": {"inline_keyboard": [[
                                      {"text": "My failures", "callback_data": "ci142:mine"},
                                      {"text": "Send me the log", "callback_data": "ci142:log"}]]}})
    panels = PersonalPanels(b, bot_username="agent_demo_bot", clock=clock)
    b.source.queue.extend([group_tap(980001, OPERATOR, "ci142:mine", card["message_id"]),
                           group_tap(980002, TEAMMATE, "ci142:mine", card["message_id"]),
                           group_tap(980003, STRANGER, "ci142:mine", card["message_id"]),
                           group_tap(980004, TEAMMATE, "ci142:log", card["message_id"])])
    routes = []
    for ev in b.listen():
        cq = {"id": ev["callback_query_id"], "from": {"id": ev["from"]},
              "message": {"message_id": ev["message_id"], "chat": {"id": ev["chat"], "type": "supergroup"}}}
        if ev["data"] == "ci142:mine":
            routes.append(panels.show(cq, render))
        elif ev["data"] == "ci142:log":
            # Logs never go to the group, not even as an ephemeral reply: a private notice
            # and the file in the requester's own chat - only if they're an operator.
            if ev["trust"] == "operator":
                routes.append("sent_privately")
            else:
                b.call("answerCallbackQuery", {"callback_query_id": ev["callback_query_id"], "show_alert": True,
                                               "text": "Logs go to the operator's private chat only."})
                routes.append("refused")
    refused_file = False
    try:
        b.send_file(__file__, chat_id=TEAM_GROUP)
    except PermissionError:
        refused_file = True
    return t, routes, refused_file, b


def main() -> None:
    t, routes, refused_file, b = run()
    c.dump(t, "Team group: shared card, personal replies")
    c.check(routes == ["ephemeral", "ephemeral", "refused"], f"routes {routes}")
    sends = [p for p in t.params_of("sendMessage") if "ephemeral_message_parameters" in p]
    c.check(len(sends) == 2 and all("receiver_user_id" not in p["ephemeral_message_parameters"] for p in sends),
            "10.4 short form: callback_query_id only - shown to the presser")
    c.check("search.spec" not in sends[0]["text"] and "checkout.spec" not in sends[1]["text"],
            "each member sees only their own failures")
    c.check(b.intake.stats["rejected"] == 1, "a group member who isn't on the allowlist gets nothing")
    c.check(refused_file and not t.params_of("sendDocument"), "files never go to the group")
    public = [p for p in t.params_of("sendMessage") if p.get("chat_id") == TEAM_GROUP]
    c.check(len(public) == 1, "the only public message is the shared card")


if __name__ == "__main__":
    main()
