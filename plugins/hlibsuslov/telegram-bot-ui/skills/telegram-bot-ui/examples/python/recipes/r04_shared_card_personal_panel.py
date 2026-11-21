"""R04 - Shared card + personal panel in a group (ephemeral, Bot API 10.3/10.4).

Two members tap "My order" on one shared card. Each sees only their own panel;
a crafted callback can't read someone else's; failures never go public.

Run:  py -3 examples/python/recipes/r04_shared_card_personal_panel.py
"""
from __future__ import annotations

import _common as c
from tgkit.ephemeral import AudienceViolation, PersonalPanels, ephemeral_params, guard_audience
from tgkit.transport import FakeTransport, TelegramErrorResponse

ORDERS = {111111111: "Margherita, no olives — $9.50", 222222222: "Pepperoni + lemonade — $12.00"}


def render(user_id: int) -> str:
    return f"Your order: {ORDERS.get(user_id, 'nothing yet')}"


def run(transport: FakeTransport | None = None):
    t = transport or FakeTransport()
    clock = [0.0]
    panels = PersonalPanels(t, bot_username="orders_demo_bot", clock=lambda: clock[0])
    a = c.fixture("callback_card_user_a.json")["callback_query"]
    b = c.fixture("callback_card_user_b.json")["callback_query"]
    routes = [panels.show(a, render), panels.show(b, render, api="10.3")]
    owner = c.fixture("callback_panel_owner.json")["callback_query"]
    crafted = c.fixture("callback_panel_crafted.json")["callback_query"]
    routes.append(panels.on_panel_button(owner, render))
    routes.append(panels.on_panel_button(crafted, render))
    clock[0] = 1000.0
    routes.append(panels.on_panel_button(owner, render))        # past the TTL
    return t, routes, panels


def main() -> None:
    t, routes, panels = run()
    c.dump(t, "Shared card + personal panels")
    c.check(routes == ["ephemeral", "ephemeral", "edited", "stale", "expired"], f"routes {routes}")
    sends = t.params_of("sendMessage")
    c.check("chat_id" not in sends[0] and "receiver_user_id" not in sends[0]["ephemeral_message_parameters"],
            "10.4 form: callback_query_id only, chat_id omitted")
    c.check(sends[1]["ephemeral_message_parameters"]["receiver_user_id"] == 222222222 and sends[1]["chat_id"] < 0,
            "10.3 form: receiver = presser, chat_id required")
    c.check("Pepperoni" not in sends[0]["text"] and "Margherita" not in sends[1]["text"],
            "neither user receives the other's data")
    answers = t.params_of("answerCallbackQuery")
    c.check(len(answers) == 5, "5 callback events -> 5 answers (an ephemeral reply doesn't replace answerCallbackQuery)")

    # Failure paths keep the audience.
    t2 = FakeTransport().script("sendMessage", TelegramErrorResponse(400, "Bad Request: EPHEMERAL_REPLY_UNAVAILABLE"))
    p2 = PersonalPanels(t2, bot_username="orders_demo_bot")
    a = c.fixture("callback_card_user_a.json")["callback_query"]
    c.check(p2.show(a, render) == "alert", "short content falls back to a private alert")
    t3 = FakeTransport().script("sendMessage", TelegramErrorResponse(403, "Forbidden: not enough rights"))
    p3 = PersonalPanels(t3, bot_username="orders_demo_bot")
    c.check(p3.show(a, lambda u: "x" * 500) == "deep_link", "long content falls back to a t.me/<bot>?start link")
    token = next(iter(p3.start_tokens))
    c.check(not p3.redeem_start(222222222, f"panel_{token}") and p3.redeem_start(111111111, f"panel_{token}"),
            "only the owner can redeem the deep link")
    for tr in (t2, t3):
        c.check(not any(m == "sendMessage" and "ephemeral_message_parameters" not in p for m, p in tr.calls),
                "no public sendMessage on any failure path")
    try:
        guard_audience("sendMessage", {"chat_id": -1001234567890, "text": render(111111111)},
                       personal=True, owner_id=111111111)
        c.check(False, "guard must refuse")
    except AudienceViolation:
        c.check(True, "guard refuses a public send of personal content")
    try:
        ephemeral_params(c.fixture("callback_channel_dm.json")["callback_query"])
        c.check(False, "must refuse channel DM chats")
    except AudienceViolation:
        c.check(True, "no ephemeral callback replies in channel direct-messages chats")
    inline = ephemeral_params(c.fixture("callback_inline_message.json")["callback_query"])
    c.check(inline == {"ephemeral_message_parameters": {"callback_query_id": "4382000000000000005"}},
            "callback from an inline message: 10.4 form works without chat_id")
    replaced = ephemeral_params(c.fixture("callback_card_user_a.json")["callback_query"], replace_original=True)
    c.check(replaced["ephemeral_message_parameters"]["replace_callback_query_message"] is True,
            "personal view shown in place of the card, for the presser only")


if __name__ == "__main__":
    main()
