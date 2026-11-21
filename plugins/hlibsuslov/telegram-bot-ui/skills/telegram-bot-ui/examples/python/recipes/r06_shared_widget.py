"""R06 - Shared widget: one poll, many messages, one public state with revisions.

Production part: create once with is_shared, re-send with sendSharedWidget to
private chats, count votes on (widget_id, from.id), coalesce edits to <= 1/s.
TEST-SERVER-ONLY part (marked): forwards (shared_widget_query), inline results
(InputSharedWidgetMessageContent), groups.

Run:  py -3 examples/python/recipes/r06_shared_widget.py
"""
from __future__ import annotations

import json

import _common as c
from tgkit.errors import TelegramError
from tgkit.router import Router
from tgkit.transport import FakeTransport
from tgkit.widgets import SharedWidgetWriter, check_widget, encode_state

ADMIN_CHAT = 555555555


class Poll:
    def __init__(self, question: str, options: list[str]):
        self.q, self.opts = question, options
        self.votes: dict[int, int] = {}       # from.id -> option (one vote per user)
        self.revision = 0

    def public(self) -> dict:
        counts = [0] * len(self.opts)
        for o in self.votes.values():
            counts[o] += 1
        return {"q": self.q, "opts": self.opts, "v": counts, "closed": False, "r": self.revision}

    def vote(self, user_id: int, option: int) -> None:
        if not 0 <= option < len(self.opts):
            raise ValueError("bad option")
        self.votes[user_id] = option
        self.revision += 1


def run(transport: FakeTransport | None = None):
    t = transport or FakeTransport()
    poll = Poll("Lunch on Friday?", ["Pizza", "Sushi", "Salad"])
    html = c.widget_html("shared-poll.html")
    assert check_widget(html, caption="Poll: Lunch on Friday?", public_data=encode_state(poll.public())).ok
    # 1) The first send creates the shared widget; read its id from the result.
    first = t.call("sendWidget", {"chat_id": ADMIN_CHAT, "html": html, "public_data": encode_state(poll.public()),
                                  "caption": "Poll: Lunch on Friday?", "is_shared": True, "allow_queries": True})
    widget_id = first["widget"]["id"]
    # 2) Re-send the same widget to people (production: private chats only).
    for user in (111111111, 222222222):
        t.call("sendSharedWidget", {"chat_id": user, "widget_id": widget_id,
                                    "caption": "Poll: Lunch on Friday? Tap to vote.",
                                    "chat_data": encode_state({"u": user})})
    writer = SharedWidgetWriter(t, widget_id)
    clock = [10.0]
    router = Router()

    def on_vote(q: dict) -> None:
        if q.get("widget_id") != widget_id:                 # computed by the server: can't be forged
            t.call("answerWidgetQuery", {"widget_query_id": q["id"], "data": '{"ok":false,"err":"unknown"}'})
            return
        try:
            poll.vote(q["from"]["id"], int(q["data"].split(":", 1)[1]))
        except (ValueError, IndexError):
            t.call("answerWidgetQuery", {"widget_query_id": q["id"], "data": '{"ok":false,"err":"bad"}'})
            return
        state = poll.public()
        # Answer first with the new state (the voter sees it at once) ...
        t.call("answerWidgetQuery", {"widget_query_id": q["id"],
                                     "data": json.dumps({"ok": True, "s": state, "r": state["r"]}, separators=(",", ":"))})
        # ... then write the shared state, at most once per second for everyone.
        writer.submit(encode_state(state), clock[0])

    router.on("widget_query")(on_vote)
    router.on("shared_widget_query")(on_vote)               # forwards: TEST SERVER ONLY today
    router.dispatch(_with_widget(c.fixture("widget_query_vote.json"), widget_id))
    clock[0] = 10.4
    router.dispatch(_with_widget(c.fixture("shared_widget_query_vote.json"), widget_id))   # coalesced
    clock[0] = 10.7
    router.dispatch(_with_widget(c.fixture("widget_query_inline_vote.json"), widget_id))   # B changes vote
    clock[0] = 11.2
    writer.flush(clock[0])                                  # the timer tick
    # 3) TEST SERVER ONLY: offer the same widget as an inline result.
    inline_result = {"inline_query_id": "iq-1", "results": [{
        "type": "article", "id": "poll", "title": "Lunch poll", "description": "Live results",
        "input_message_content": {"widget_id": widget_id, "caption": "Poll: Lunch on Friday?"}},   # InputSharedWidgetMessageContent
        {"type": "article", "id": "fresh", "title": "New poll", "description": "A separate poll per send",
         "input_message_content": {"html": html, "public_data": encode_state(Poll("Lunch on Friday?", poll.opts).public()),
                                   "caption": "Poll: Lunch on Friday?", "allow_queries": True,
                                   "is_shared": True}}]}                                       # InputWidgetMessageContent
    # 4) Copying a widget is refused - re-send by id instead.
    t.script("copyMessage", c.fixture("copy_widget_error.json"))
    try:
        t.call("copyMessage", {"chat_id": 333333333, "from_chat_id": ADMIN_CHAT, "message_id": first["message_id"]})
    except TelegramError as err:
        assert err.category == "validation"
        t.call("sendSharedWidget", {"chat_id": 333333333, "widget_id": widget_id, "caption": "Poll: Lunch on Friday?"})
    # 5) Someone replies to a forwarded copy: ExternalReplyInfo.widget identifies it.
    reply = c.fixture("message_reply_to_widget_external.json")["message"]
    recognised = reply["external_reply"]["widget"].get("id")
    return t, poll, writer, widget_id, inline_result, recognised


def _with_widget(update: dict, widget_id: str) -> dict:
    update = {k: v for k, v in update.items() if not k.startswith("_")}
    kind = next(k for k in update if k != "update_id")
    update[kind] = {**update[kind], "widget_id": widget_id}
    return update


def main() -> None:
    t, poll, writer, widget_id, inline_result, recognised = run()
    c.dump(t, "Shared widget")
    c.check(poll.public()["v"] == [0, 2, 0], "one vote per user; a changed vote replaces the old one")
    c.check(writer.writes == 2, "3 votes in 1.2 s -> 2 shared edits (coalesced to <= 1/s)")
    last = json.loads(t.params_of("editSharedWidgetData")[-1]["public_data"])
    c.check(last["r"] == 3, "the last pushed state is the newest revision")
    c.check(len(t.params_of("answerWidgetQuery")) == 3, "every vote answered")
    c.check(t.methods().count("sendSharedWidget") == 3, "re-sent by widget_id, including after copyMessage was refused")
    c.check(inline_result["results"][0]["input_message_content"]["widget_id"] == widget_id,
            "inline result references the existing shared widget (test server only)")
    c.check("html" in inline_result["results"][1]["input_message_content"],
            "InputWidgetMessageContent: each send creates its own shared widget (id known only from later queries)")
    c.check(recognised == "7770011223344556677", "reply to a widget recognised via external_reply.widget")
    rep = check_widget(c.widget_html("shared-poll.html"), caption="Poll", context="group")
    c.check(not rep.ok and "test-server only" in rep.errors[0], "a group widget is refused for production")
    c.check(check_widget(c.widget_html("shared-poll.html"), caption="Poll", context="group",
                         environment="test").ok, "the same widget is valid on the test server")


if __name__ == "__main__":
    main()
