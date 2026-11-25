"""Forum topics: one request per method (topics in forum supergroups, the 'General' topic, topic icons).

Run:  py -3 examples/python/recipes/api_forums.py        (offline; nothing is sent)
Written to payloads/api-forums.json by export_payloads.py. Ids are synthetic. A call that depends on
an earlier answer reads it from the scripted result: getForumTopicIconStickers returns the stickers
whose custom_emoji_id createForumTopic takes, and createForumTopic returns the ForumTopic whose
message_thread_id every later topic call takes. deleteForumTopic removes the topic with all its
messages, so it is a recorded request only, sent on a human admin's decision.
"""
from __future__ import annotations

import _common as c
from tgkit.transport import FakeTransport

STATUS = "production (deleteForumTopic is a recorded request, never sent)"
CONTEXT = ("forum supergroup where the bot is an administrator; createForumTopic, editForumTopic, "
           "deleteForumTopic and unpinAllForumTopicMessages also take a private chat with a user")

MANAGE = "bot admin with can_manage_topics"
STEP_CONTEXT = {
    "getForumTopicIconStickers": "no chat; no rights; any bot",
    "createForumTopic": f"forum supergroup, {MANAGE}; or a private chat with a user (no right named)",
    "editForumTopic": f"forum supergroup, {MANAGE} unless the bot created the topic; "
                      "or a private chat with a user (no right named)",
    "unpinAllForumTopicMessages": "forum supergroup, bot admin with can_pin_messages; "
                                  "or a private chat with a user (no right named)",
    "closeForumTopic": f"forum supergroup; {MANAGE} unless the bot created the topic",
    "reopenForumTopic": f"forum supergroup; {MANAGE} unless the bot created the topic",
    "deleteForumTopic": "forum supergroup, bot admin with can_delete_messages; or a private chat with a user "
                        "(no right named); destructive, recorded not sent",
    "editGeneralForumTopic": f"forum supergroup; {MANAGE}",
    "closeGeneralForumTopic": f"forum supergroup; {MANAGE}",
    "hideGeneralForumTopic": f"forum supergroup; {MANAGE}; also closes General if it was open",
    "unhideGeneralForumTopic": f"forum supergroup; {MANAGE}",
    "reopenGeneralForumTopic": f"forum supergroup; {MANAGE}; also unhides General if it was hidden",
    "unpinAllGeneralForumTopicMessages": "forum supergroup; bot admin with can_pin_messages",
}

FORUM = -1001234567890                  # a supergroup with Chat.is_forum
TICKET_COLOR = 7322096                  # 0x6FB9F0, one of the six allowed icon colors


def _icon_sticker(n: int, emoji: str) -> dict:
    """A custom emoji Sticker as getForumTopicIconStickers returns it (synthetic ids)."""
    return {"file_id": f"CAACAgIAAxkBAAEBtopicIcon{n:04d}", "file_unique_id": f"AgADtopic{n:04d}",
            "type": "custom_emoji", "width": 100, "height": 100, "is_animated": False, "is_video": False,
            "emoji": emoji, "custom_emoji_id": f"030000000000000{n}"}


ICON_STICKERS = [_icon_sticker(1, "📝"), _icon_sticker(2, "✅"), _icon_sticker(3, "🔥")]


# --- topic icons -------------------------------------------------------------------------------

def get_forum_topic_icon_stickers(t: FakeTransport) -> list[dict]:
    t.script("getForumTopicIconStickers", ICON_STICKERS)
    return t.call("getForumTopicIconStickers", {})


# --- topics ------------------------------------------------------------------------------------

def create_forum_topic(t: FakeTransport, icon: dict) -> dict:
    params = {"chat_id": FORUM, "name": "Ticket #1042: refund for order 318", "icon_color": TICKET_COLOR,
              "icon_custom_emoji_id": icon["custom_emoji_id"]}
    t.script("createForumTopic", {"message_thread_id": 42, "name": params["name"], "icon_color": TICKET_COLOR,
                                  "icon_custom_emoji_id": icon["custom_emoji_id"]})
    return t.call("createForumTopic", params)


def edit_forum_topic(t: FakeTransport, topic: dict, icon: dict) -> None:
    t.call("editForumTopic", {"chat_id": FORUM, "message_thread_id": topic["message_thread_id"],
                              "name": "Ticket #1042: refund sent", "icon_custom_emoji_id": icon["custom_emoji_id"]})


def unpin_all_forum_topic_messages(t: FakeTransport, topic: dict) -> None:
    t.call("unpinAllForumTopicMessages", {"chat_id": FORUM, "message_thread_id": topic["message_thread_id"]})


def close_forum_topic(t: FakeTransport, topic: dict) -> None:
    t.call("closeForumTopic", {"chat_id": FORUM, "message_thread_id": topic["message_thread_id"]})


def reopen_forum_topic(t: FakeTransport, topic: dict) -> None:
    t.call("reopenForumTopic", {"chat_id": FORUM, "message_thread_id": topic["message_thread_id"]})


def delete_forum_topic(t: FakeTransport, topic: dict) -> None:
    t.call("deleteForumTopic", {"chat_id": FORUM, "message_thread_id": topic["message_thread_id"]})


# --- the 'General' topic (addressed by chat_id alone) --------------------------------------------

def edit_general_forum_topic(t: FakeTransport) -> None:
    t.call("editGeneralForumTopic", {"chat_id": FORUM, "name": "Lobby"})


def close_general_forum_topic(t: FakeTransport) -> None:
    t.call("closeGeneralForumTopic", {"chat_id": FORUM})


def hide_general_forum_topic(t: FakeTransport) -> None:
    t.call("hideGeneralForumTopic", {"chat_id": FORUM})


def unhide_general_forum_topic(t: FakeTransport) -> None:
    t.call("unhideGeneralForumTopic", {"chat_id": FORUM})


def reopen_general_forum_topic(t: FakeTransport) -> None:
    t.call("reopenGeneralForumTopic", {"chat_id": FORUM})


def unpin_all_general_forum_topic_messages(t: FakeTransport) -> None:
    t.call("unpinAllGeneralForumTopicMessages", {"chat_id": FORUM})


def run_all() -> FakeTransport:
    t = FakeTransport()
    stickers = get_forum_topic_icon_stickers(t)
    allowed = {s["custom_emoji_id"] for s in stickers}
    new_icon, done_icon = stickers[0], stickers[1]
    topic = create_forum_topic(t, new_icon)
    c.check(t.params_of("createForumTopic")[0]["icon_custom_emoji_id"] in allowed,
            "createForumTopic takes a custom_emoji_id from getForumTopicIconStickers")
    edit_forum_topic(t, topic, done_icon)
    unpin_all_forum_topic_messages(t, topic)
    close_forum_topic(t, topic)
    reopen_forum_topic(t, topic)
    delete_forum_topic(t, topic)
    threaded = [p for m, p in t.calls if "message_thread_id" in p]
    c.check(len(threaded) == 5 and all(p["message_thread_id"] == topic["message_thread_id"] for p in threaded),
            "every topic call takes the message_thread_id createForumTopic returned")
    for fn in (edit_general_forum_topic, close_general_forum_topic, hide_general_forum_topic,
               unhide_general_forum_topic, reopen_general_forum_topic, unpin_all_general_forum_topic_messages):
        fn(t)
    c.check(sorted(t.methods()) == sorted(STEP_CONTEXT), "every forums method is called exactly once")
    return t


if __name__ == "__main__":
    c.dump(run_all(), "Forum topics")
