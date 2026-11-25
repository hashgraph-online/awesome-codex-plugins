"""Inline mode, guest queries, Mini App answers and HTML widgets: one request per method.

Run:  py -3 examples/python/recipes/api_inline_widgets.py        (offline; nothing is sent)
Written to payloads/api-inline-widgets.json by export_payloads.py. Ids are synthetic. Each call is only
valid where STEP_CONTEXT says: an incoming inline query, a guest message, the server behind a Mini App,
a private chat with widgets. Widgets go to private chats here (production); groups, inline widget results
and forwards are test-server only and stay out of this file. Where a call needs a value an earlier call
returned (a shared widget id, a widget message), FakeTransport.script supplies that result.
"""
from __future__ import annotations

import json

import _common as c
from tgkit.transport import FakeTransport
from tgkit.widgets import check_widget, encode_state

STATUS = "production (widgets in private chats only; inline widget results are test-server only and not used)"
CONTEXT = "inline query, guest message, Mini App backend, private chats with an HTML widget"

STEP_CONTEXT = {
    "answerInlineQuery": "incoming Update.inline_query, from any chat; inline mode enabled (setMySettings supports_inline_queries)",
    "answerGuestQuery": "incoming Update.guest_message with Message.guest_query_id; guest queries allowed (setMySettings supports_guest_queries); one reply",
    "savePreparedInlineMessage": "bot backend for a Mini App user; the returned id goes to Telegram.WebApp.shareMessage",
    "answerWebAppQuery": "bot backend; query_id from verified initData of a Mini App opened from an inline keyboard button, the menu button or the attachment menu",
    "sendWidget": "private chat with the bot (production); groups, inline results and forwards only on the test server",
    "sendSharedWidget": "private chat with the bot (production); a shared widget this bot created",
    "editMessageWidgetData": "widget message sent by the bot (chat_id + message_id) or via the bot (inline_message_id)",
    "answerWidgetQuery": "incoming Update.widget_query or shared_widget_query; exactly once, within 15 seconds",
    "editSharedWidgetData": "shared widget this bot created; at most one edit per second",
}

NOW = 1763191000
OWNER = 111111111          # the user who starts the poll
FRIEND = 222222222         # gets the same poll by widget_id
TEAM_GROUP = -1001234567890
WIDGET_ID = "7770011223344556677"
OPTIONS = ["Pizza", "Sushi", "Salad"]
CAPTION = "Poll: Lunch on Friday?"


def _user(user_id: int, first_name: str) -> dict:
    return {"id": user_id, "is_bot": False, "first_name": first_name}


def _article(result_id: str, title: str, text: str, **fields) -> dict:
    """InlineQueryResultArticle with InputTextMessageContent: the result every answer method takes."""
    return {"type": "article", "id": result_id, "title": title,
            "input_message_content": {"message_text": text}, **fields}


# Incoming updates the answers refer to.
INLINE_QUERY = {"id": "AAEC77001", "from": _user(OWNER, "Olena"), "query": "pizza", "offset": "", "chat_type": "group"}
GUEST_MESSAGE = {"message_id": 5150, "date": NOW, "from": _user(FRIEND, "Taras"),
                 "chat": {"id": TEAM_GROUP, "type": "supergroup", "title": "Team Kyiv"},
                 "text": "@lunchpoll_bot where do we eat on Friday?", "guest_query_id": "gq-5150-77"}
WEB_APP_QUERY_ID = "AAHlunch-order-8812"   # initData.query_id, after the HMAC check on the backend


# --- inline mode -------------------------------------------------------------------------------

def answer_inline_query(t: FakeTransport) -> None:
    keyboard = {"inline_keyboard": [[{"text": "I'm in", "callback_data": "join:napoli"}]]}   # -> inline_message_id
    t.call("answerInlineQuery", {
        "inline_query_id": INLINE_QUERY["id"],
        "results": [_article("napoli", "Napoli, 12:30", "Lunch on Friday: Napoli, 12:30. Who's in?",
                             description="Pizza, 5 min walk", reply_markup=keyboard)],
        "cache_time": 30, "is_personal": True, "next_offset": "",
        "button": {"text": "Set your office", "start_parameter": "inline_office"},
    })


def answer_guest_query(t: FakeTransport) -> dict:
    t.script("answerGuestQuery", {"inline_message_id": "BAAAAGuest5150"})
    return t.call("answerGuestQuery", {
        "guest_query_id": GUEST_MESSAGE["guest_query_id"],
        "result": _article("guest-5150", "Friday lunch", "Friday's pick so far: Sushi (3 votes). Vote with @lunchpoll_bot."),
    })


# --- Mini App answers --------------------------------------------------------------------------

def save_prepared_inline_message(t: FakeTransport) -> dict:
    t.script("savePreparedInlineMessage", {"id": "prep-8812-a", "expiration_date": NOW + 3600})
    return t.call("savePreparedInlineMessage", {
        "user_id": OWNER,
        "result": _article("share-8812", "My lunch order", "I ordered a Margherita for Friday. Join the order?"),
        "allow_user_chats": True, "allow_group_chats": True,
    })


def answer_web_app_query(t: FakeTransport) -> dict:
    keyboard = {"inline_keyboard": [[{"text": "Order the same", "callback_data": "same:8812"}]]}
    t.script("answerWebAppQuery", {"inline_message_id": "BAAAAWebApp8812"})
    return t.call("answerWebAppQuery", {
        "web_app_query_id": WEB_APP_QUERY_ID,
        "result": _article("ord-8812", "Order 8812", "Order 8812: 1 Margherita, Friday 12:30", reply_markup=keyboard),
    })


# --- widgets -----------------------------------------------------------------------------------

def _poll_state(votes: list[int], revision: int) -> str:
    return encode_state({"q": "Lunch on Friday?", "opts": OPTIONS, "v": votes, "closed": False, "r": revision})


def _widget_message(message_id: int, chat_id: int, first_name: str, widget: dict) -> dict:
    """The Message Telegram returns for sendWidget / sendSharedWidget."""
    return {"message_id": message_id, "date": NOW, "chat": {"id": chat_id, "type": "private", "first_name": first_name},
            "caption": CAPTION, "widget": widget}


def send_widget(t: FakeTransport, html: str) -> dict:
    params = {
        "chat_id": OWNER, "html": html, "public_data": _poll_state([0, 0, 0], 0),
        "chat_data": encode_state({"u": OWNER}), "caption": CAPTION,
        "allow_queries": True, "is_shared": True,
        "reply_markup": {"inline_keyboard": [[{"text": "Vote in chat", "callback_data": "poll:vote"}]]},
    }
    t.script("sendWidget", _widget_message(4300, OWNER, "Olena", {
        "id": WIDGET_ID, "html": html, "public_data": params["public_data"], "chat_data": params["chat_data"]}))
    return t.call("sendWidget", params)


def send_shared_widget(t: FakeTransport, widget: dict) -> dict:
    params = {"chat_id": FRIEND, "widget_id": widget["id"], "chat_data": encode_state({"u": FRIEND}),
              "caption": CAPTION + " Tap to vote."}
    t.script("sendSharedWidget", _widget_message(4301, FRIEND, "Taras", {**widget, "chat_data": params["chat_data"]}))
    return t.call("sendSharedWidget", params)


def edit_message_widget_data(t: FakeTransport, query: dict) -> None:
    t.call("editMessageWidgetData", {"chat_id": query["chat"]["id"], "message_id": query["message_id"],
                                     "chat_data": encode_state({"u": query["from"]["id"], "my": 1})})


def answer_widget_query(t: FakeTransport, query: dict, revision: int) -> None:
    t.call("answerWidgetQuery", {"widget_query_id": query["id"],
                                 "data": json.dumps({"ok": True, "r": revision}, separators=(",", ":"))})


def edit_shared_widget_data(t: FakeTransport, widget_id: str, votes: list[int], revision: int) -> None:
    t.call("editSharedWidgetData", {"widget_id": widget_id, "public_data": _poll_state(votes, revision),
                                    "cache_time": 10})


def _vote_query(message: dict, widget_id: str) -> dict:
    """Update.widget_query as the friend's copy sends it: vote for option 1."""
    return {"id": "8123456789012377001", "from": _user(FRIEND, "Taras"), "chat": message["chat"],
            "message_id": message["message_id"], "chat_instance": "901234567890177001",
            "type": {"type": "data"}, "data": "vote:1", "widget_id": widget_id}


def run_all() -> FakeTransport:
    t = FakeTransport()
    answer_inline_query(t)
    sent = answer_guest_query(t)
    c.check(sent["inline_message_id"], "answerGuestQuery returns SentGuestMessage with inline_message_id")
    prepared = save_prepared_inline_message(t)
    c.check(prepared["id"] and prepared["expiration_date"] > NOW,
            "savePreparedInlineMessage returns the id the Mini App passes to shareMessage, with an expiry")
    posted = answer_web_app_query(t)
    c.check(posted["inline_message_id"], "a result with an inline keyboard comes back with inline_message_id")

    html = c.widget_html("shared-poll.html")
    c.check(check_widget(html, caption=CAPTION, public_data=_poll_state([0, 0, 0], 0)).ok,
            "the widget fits the size limits for a private chat in production")
    first = send_widget(t, html)
    widget_id = first["widget"]["id"]
    c.check(widget_id == WIDGET_ID, "sendWidget with is_shared returns Message.widget.id for sendSharedWidget")
    copy = send_shared_widget(t, first["widget"])
    c.check(copy["widget"]["id"] == widget_id, "every copy carries the same shared widget id")
    query = _vote_query(copy, widget_id)
    edit_message_widget_data(t, query)
    answer_widget_query(t, query, revision=1)
    edit_shared_widget_data(t, widget_id, votes=[0, 1, 0], revision=1)
    c.check(sorted(t.methods()) == sorted(STEP_CONTEXT), "every inline-widgets method is called exactly once")
    return t


if __name__ == "__main__":
    c.dump(run_all(), "Inline mode, guest queries, Mini App answers and widgets")
