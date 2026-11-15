"""R08 - Bot with several conversation topics in the private chat (10.3 + 10.4).

Two AI answers stream in parallel in two topics; Stop in one topic stops only
that one; a 10.4 topic link jumps between them. Also shows the addressing of a
forum supergroup and a channel direct-messages chat - three different fields.

Run:  py -3 examples/python/recipes/r08_multi_topic_bot.py
"""
from __future__ import annotations

import _common as c
from tgkit.generation import Generation, OperationRegistry, State, execute
from tgkit.topics import Address, private_topic_link
from tgkit.transport import FakeTransport

CHAT = 111111111


def topic_message(thread: int, text: str) -> dict:
    return {"message_id": 100 + thread, "chat": {"id": CHAT, "type": "private"}, "message_thread_id": thread,
            "is_topic_message": True, "text": text}


def run(transport: FakeTransport | None = None):
    t = transport or FakeTransport()
    reg = OperationRegistry()
    gens = {}
    for thread, draft in ((11, 50000), (12, 50001)):
        addr = Address.of(topic_message(thread, "question"))
        g = Generation(op_id=f"t{thread}", chat_id=addr.chat_id, draft_id=draft,
                       message_thread_id=addr.message_thread_id)
        reg.add(g)
        gens[thread] = g
        execute(g.start(0.0), t, g, now=0.0)
    for thread, g in gens.items():
        execute(g.on_chunk(f"Answer for topic {thread}. ", 1.5), t, g, now=1.5)
    stop = c.fixture("stopped_message_generation_topic.json")["stopped_message_generation"]   # thread 12
    target = reg.find_for_stop(stop)
    execute(target.on_stop(2.0), t, target, now=2.0)
    try:   # topic 11 is still generating: a second run there is refused
        reg.add(Generation(op_id="dup", chat_id=CHAT, draft_id=50002, message_thread_id=11))
        clash = False
    except RuntimeError:
        clash = True
    execute(gens[11].on_done(3.0), t, gens[11], now=3.0)
    # Cross-link: from topic 11, point the user to the stopped answer in topic 12.
    link = private_topic_link("orders_demo_bot", 12)
    t.call("sendMessage", {**Address.of(topic_message(11, "")).send_params(),
                           "text": "The other answer was stopped — open it to continue:",
                           "reply_markup": {"inline_keyboard": [[{"text": "Go to topic", "url": link}]]}})
    return t, gens, target, link, clash


def main() -> None:
    t, gens, target, link, clash = run()
    c.dump(t, "Two topics, one stopped")
    c.check(target is gens[12], "Stop matched by (chat, thread, draft) - topic 12 only")
    c.check(gens[12].outcome == State.STOPPED and gens[11].outcome == State.COMPLETED, "topics isolated")
    for thread in (11, 12):
        calls = [p for m, p in t.calls if p.get("message_thread_id") == thread]
        c.check(all(f"topic {23 - thread}" not in str(p) for p in calls), f"topic {thread} never shows the other's text")
    c.check(link == "https://t.me/orders_demo_bot/12", "10.4 private topic link")
    c.check(clash, "a second generation in a busy topic is refused (not silently interleaved)")

    forum = Address.of({"chat": {"id": -1001, "type": "supergroup", "is_forum": True},
                        "message_thread_id": 5, "is_topic_message": True})
    dm = Address.of({"chat": {"id": -1002, "type": "supergroup", "is_direct_messages": True},
                     "message_thread_id": 9, "direct_messages_topic": {"topic_id": 222222222}})
    c.check(forum.send_params() == {"chat_id": -1001, "message_thread_id": 5}, "forum topic -> message_thread_id")
    c.check(dm.send_params() == {"chat_id": -1002, "direct_messages_topic_id": 222222222},
            "channel DM topic -> direct_messages_topic_id, never message_thread_id")
    try:
        forum.draft_params()
        c.check(False, "drafts must refuse groups")
    except ValueError:
        c.check(True, "drafts stream to private chats only")


if __name__ == "__main__":
    main()
