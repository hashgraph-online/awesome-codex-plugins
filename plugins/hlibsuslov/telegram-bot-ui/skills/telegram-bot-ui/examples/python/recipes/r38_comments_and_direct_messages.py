"""R38 - The audience side of a channel: comment threads and direct messages.

Comments: every channel post is auto-forwarded into the linked discussion
group (`is_automatic_forward`, `forward_origin.message_id` = the channel post).
Replies to that copy form the post's comment thread. The bot opens each thread
with one silent pinned-style note, answers questions and removes spam.

Direct messages: a channel's direct-messages chat is a supergroup with
`is_direct_messages`; every reply needs `direct_messages_topic_id`. Suggested
posts arrive there with `suggested_post_info`; the bot approves (needs
can_post_messages; `send_date` <= 30 days ahead) or declines with a comment
(needs can_manage_direct_messages; 0-128 chars). Ephemeral replies and polls are
not available in channel DM chats.

Run:  py -3 examples/python/recipes/r38_comments_and_direct_messages.py
"""
from __future__ import annotations

import re
from typing import Any

import _common as c
from tgkit.errors import call_with_policy
from tgkit.publish import LIMITS
from tgkit.transport import FakeTransport

CHANNEL, GROUP = -1001500000001, -1001500000101
SPAM = re.compile(r"airdrop|t\.me/\+|followers", re.I)


class ChannelAudience:
    def __init__(self, transport: Any, channel_id: int):
        self.t, self.channel = transport, channel_id
        info = call_with_policy(transport, "getChat", {"chat_id": channel_id})
        self.group = info.get("linked_chat_id")      # None: comments are off for this channel
        self.threads: dict[int, int] = {}            # group message id of the auto-forward -> channel post id

    # -- comments ------------------------------------------------------------
    def on_group_message(self, m: dict[str, Any]) -> str:
        if m["chat"]["id"] != self.group:
            return "ignored"
        origin = m.get("forward_origin") or {}
        if m.get("is_automatic_forward") and origin.get("type") == "channel" and origin["chat"]["id"] == self.channel:
            self.threads[m["message_id"]] = origin["message_id"]
            self.t.call("sendMessage", {"chat_id": self.group, "reply_parameters": {"message_id": m["message_id"]},
                                        "text": "Comments are open. Be kind; links to other channels are removed.",
                                        "disable_notification": True})
            return "thread_opened"
        thread_root = (m.get("reply_to_message") or {}).get("message_id")
        if thread_root not in self.threads:
            return "ignored"
        if SPAM.search(m.get("text", "")):
            self.t.call("deleteMessage", {"chat_id": self.group, "message_id": m["message_id"]})
            return "removed"
        if m.get("text", "").rstrip().endswith("?"):
            self.t.call("sendMessage", {"chat_id": self.group, "reply_parameters": {"message_id": m["message_id"]},
                                        "text": "Thanks for asking - an editor will answer in this thread today."})
            return "acknowledged"
        return "kept"

    # -- direct messages -----------------------------------------------------
    def on_dm_message(self, m: dict[str, Any]) -> str:
        if not m["chat"].get("is_direct_messages"):
            return "ignored"
        topic = m["direct_messages_topic"]["topic_id"]
        info = m.get("suggested_post_info")
        if info and info["state"] == "pending":
            if SPAM.search(m.get("text", "")):
                comment = "Sorry, we don't publish ads for this kind of service."
                assert len(comment) <= LIMITS["decline_comment"]
                self.t.call("declineSuggestedPost", {"chat_id": m["chat"]["id"], "message_id": m["message_id"],
                                                     "comment": comment})
                return "suggestion_declined"
            params = {"chat_id": m["chat"]["id"], "message_id": m["message_id"]}
            if "send_date" not in info:
                params["send_date"] = m["date"] + 3600       # publish in an hour if the author set no date
            self.t.call("approveSuggestedPost", params)
            return "suggestion_approved"
        self.t.call("sendMessage", {"chat_id": m["chat"]["id"], "direct_messages_topic_id": topic,
                                    "text": "Thanks! The editors read every message and reply here within a day."})
        return "dm_answered"


def run(transport: FakeTransport | None = None):
    t = transport or FakeTransport().script("getChat", {"id": CHANNEL, "type": "channel", "title": "City News",
                                                        "linked_chat_id": GROUP})
    aud = ChannelAudience(t, CHANNEL)
    routes = []
    for u in c.fixture("r38_channel_audience_updates.json"):
        m = u["message"]
        routes.append(aud.on_dm_message(m) if m["chat"].get("is_direct_messages") else aud.on_group_message(m))
    return t, routes, aud


def main() -> None:
    t, routes, aud = run()
    c.dump(t, "Comments and direct messages")
    c.check(routes == ["thread_opened", "acknowledged", "removed", "dm_answered", "suggestion_approved",
                       "suggestion_declined"], f"routes {routes}")
    c.check(aud.threads == {9001: 5101}, "group copy 9001 is the thread of channel post 5101")
    first = t.params_of("sendMessage")[0]
    c.check(first["reply_parameters"] == {"message_id": 9001} and first["disable_notification"] is True,
            "the thread note is a silent reply to the auto-forwarded copy")
    c.check(t.params_of("deleteMessage") == [{"chat_id": GROUP, "message_id": 9003}], "spam comment removed")
    dm = t.params_of("sendMessage")[2]
    c.check(dm["direct_messages_topic_id"] == 77 and "message_thread_id" not in dm,
            "DM reply uses direct_messages_topic_id, not message_thread_id")
    c.check(t.params_of("approveSuggestedPost") == [{"chat_id": -1001500000201, "message_id": 3002}],
            "author-chosen send_date kept (no send_date passed)")
    c.check(len(t.params_of("declineSuggestedPost")[0]["comment"]) <= 128, "decline comment within 0-128")


if __name__ == "__main__":
    main()
