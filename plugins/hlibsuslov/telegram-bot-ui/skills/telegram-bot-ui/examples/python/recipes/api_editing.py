"""Bot API domain `editing`: one request per method, recorded offline (nothing is sent).

Covers editing, deleting and reacting to messages, ephemeral edits and suggested-post decisions.
Run:  py -3 examples/python/recipes/api_editing.py
Written to examples/payloads/api-editing.json by export_payloads.py (--only api-editing).
Ids are synthetic. Deletions are recorded requests only.
"""
from __future__ import annotations

import _common as c
from tgkit.transport import FakeTransport

STATUS = "production (deletions are recorded requests only)"
CONTEXT = "private; group and supergroup with bot admin; channel; business chat; channel direct messages chat"
STEP_CONTEXT = {
    "editMessageText": "any chat the bot sent to, or an inline message (inline_message_id, result True); business messages need business_connection_id",
    "editMessageCaption": "media message the bot sent, or an inline message (inline_message_id, result True)",
    "editMessageMedia": "message the bot sent, or an inline message (file_id or URL only); inside an album the media type is restricted",
    "editMessageLiveLocation": "live location message the bot sent, while its live_period has not expired",
    "stopMessageLiveLocation": "live location message the bot sent, before its live_period expires",
    "editMessageChecklist": "private chat of a connected business account; business_connection_id required",
    "editMessageReplyMarkup": "any chat the bot sent to, or an inline message (inline_message_id, result True)",
    "stopPoll": "poll the bot sent; not available for inline messages",
    "deleteMessage": "supergroup; bot admin with can_delete_messages for others' messages; message younger than 48 hours",
    "deleteMessages": "supergroup; bot admin with can_delete_messages for others' messages; ids younger than 48 hours",
    "setMessageReaction": "group or supergroup; the reaction must be allowed in the chat; one reaction per message",
    "deleteMessageReaction": "supergroup; bot admin with can_delete_messages",
    "deleteAllMessageReactions": "supergroup; bot admin with can_delete_messages",
    "editEphemeralMessageText": "group or supergroup; ephemeral message the bot sent to receiver_user_id",
    "editEphemeralMessageCaption": "group or supergroup; ephemeral media message the bot sent to receiver_user_id",
    "editEphemeralMessageMedia": "group or supergroup; ephemeral media message the bot sent to receiver_user_id",
    "editEphemeralMessageReplyMarkup": "group or supergroup; ephemeral message the bot sent to receiver_user_id",
    "deleteEphemeralMessage": "group or supergroup; ephemeral message the bot sent to receiver_user_id",
    "approveSuggestedPost": "channel direct messages chat; bot admin with can_post_messages in the channel",
    "declineSuggestedPost": "channel direct messages chat; bot admin with can_manage_direct_messages in the channel",
    "sendMessage": "supergroup; bot admin pushing an ephemeral message to a member (setup for the ephemeral edits)",
    "sendPhoto": "supergroup; bot admin pushing an ephemeral photo to a member (setup for the ephemeral media edits)",
}

PRIVATE = 111111111
GROUP = -1001234567890
CHANNEL = -1001987654321
DIRECT_MESSAGES = -1001122334455
BUSINESS_CONNECTION = "BCxyz"
BUSINESS_CHAT = 555555555
MEMBER = 222222222
SPAMMER = 666666666
NOW = 1790000000


def edit_message_text(t: FakeTransport) -> None:
    t.call("editMessageText", {
        "chat_id": PRIVATE, "message_id": 4021,
        "text": "<b>Order #8812</b>\nStatus: out for delivery", "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": True},
        "reply_markup": {"inline_keyboard": [[{"text": "Track", "callback_data": "trk:8812"}]]}})
    t.call("editMessageText", {                      # rich content instead of text
        "chat_id": PRIVATE, "message_id": 4022,
        "rich_message": {"html": "<h2>Order #8812</h2><p>Out for delivery, arriving by 18:00.</p>"}})
    t.call("editMessageText", {                      # inline message: no chat_id, no message_id
        "inline_message_id": "BAAAAJw0AAA8e2Kx", "text": "Margherita: ordered by Taras",
        "reply_markup": {"inline_keyboard": [[{"text": "Track", "callback_data": "trk:8812"}]]}})


def edit_message_caption(t: FakeTransport) -> None:
    t.call("editMessageCaption", {
        "chat_id": CHANNEL, "message_id": 312,
        "caption": "<b>Margherita</b>: now 8.90 EUR", "parse_mode": "HTML", "show_caption_above_media": True})


def edit_message_media(t: FakeTransport) -> None:
    t.call("editMessageMedia", {
        "chat_id": CHANNEL, "message_id": 312,
        "media": {"type": "photo", "media": "AgACAgIAAxkBAAID", "caption": "Updated price: 8.90 EUR"},
        "reply_markup": {"inline_keyboard": [[{"text": "Order", "callback_data": "ord:margherita"}]]}})


def edit_message_live_location(t: FakeTransport) -> None:
    t.call("editMessageLiveLocation", {
        "chat_id": PRIVATE, "message_id": 4180, "latitude": 50.4501, "longitude": 30.5234,
        "live_period": 7200, "horizontal_accuracy": 25.5, "heading": 90, "proximity_alert_radius": 100})


def stop_message_live_location(t: FakeTransport) -> None:
    t.call("stopMessageLiveLocation", {"chat_id": PRIVATE, "message_id": 4180})


def edit_message_checklist(t: FakeTransport) -> None:
    t.call("editMessageChecklist", {
        "business_connection_id": BUSINESS_CONNECTION, "chat_id": BUSINESS_CHAT, "message_id": 77,
        "checklist": {"title": "Before your appointment", "others_can_mark_tasks_as_done": True,
                      "tasks": [{"id": 1, "text": "Bring your passport"},
                                {"id": 2, "text": "Arrive 10 minutes early"},
                                {"id": 3, "text": "Sign the consent form"}]}})


def edit_message_reply_markup(t: FakeTransport) -> None:
    t.call("editMessageReplyMarkup", {
        "chat_id": GROUP, "message_id": 905,
        "reply_markup": {"inline_keyboard": [[{"text": "Approved by Dan", "callback_data": "noop"}]]}})


def stop_poll(t: FakeTransport) -> None:
    t.script("stopPoll", {"id": "5432109876", "question": "Friday release?", "is_closed": True,
                          "options": [{"text": "Yes", "voter_count": 7}, {"text": "No", "voter_count": 2}]})
    t.call("stopPoll", {"chat_id": CHANNEL, "message_id": 640})


def delete_message(t: FakeTransport) -> None:
    t.call("deleteMessage", {"chat_id": GROUP, "message_id": 905})


def delete_messages(t: FakeTransport) -> None:
    t.call("deleteMessages", {"chat_id": GROUP, "message_ids": [906, 907, 908]})


def set_message_reaction(t: FakeTransport) -> None:
    t.call("setMessageReaction", {
        "chat_id": GROUP, "message_id": 910, "reaction": [{"type": "emoji", "emoji": "👍"}]})


def delete_message_reaction(t: FakeTransport) -> None:
    t.call("deleteMessageReaction", {"chat_id": GROUP, "message_id": 910, "user_id": SPAMMER})


def delete_all_message_reactions(t: FakeTransport) -> None:
    t.call("deleteAllMessageReactions", {"chat_id": GROUP, "user_id": SPAMMER})


def send_ephemeral(t: FakeTransport, method: str, params: dict, ephemeral_message_id: int) -> int:
    """The edits need the id of the sent message: Message.message_id is 0, the id is ephemeral_message_id."""
    t.script(method, {"message_id": 0, "date": NOW, "chat": {"id": GROUP, "type": "supergroup"},
                      "receiver_user": {"id": MEMBER, "is_bot": False, "first_name": "Taras"},
                      "ephemeral_message_id": ephemeral_message_id})
    sent = t.call(method, {"chat_id": GROUP, "ephemeral_message_parameters": {"receiver_user_id": MEMBER}, **params})
    return sent["ephemeral_message_id"]


def edit_ephemeral_message_text(t: FakeTransport, ephemeral_message_id: int) -> None:
    t.call("editEphemeralMessageText", {
        "chat_id": GROUP, "receiver_user_id": MEMBER, "ephemeral_message_id": ephemeral_message_id,
        "text": "Your open orders: 1",
        "reply_markup": {"inline_keyboard": [[{"text": "Open", "callback_data": "orders:open"}]]}})


def edit_ephemeral_message_caption(t: FakeTransport, ephemeral_message_id: int) -> None:
    t.call("editEphemeralMessageCaption", {
        "chat_id": GROUP, "receiver_user_id": MEMBER, "ephemeral_message_id": ephemeral_message_id,
        "caption": "Your order #8812: out for delivery", "show_caption_above_media": True})


def edit_ephemeral_message_media(t: FakeTransport, ephemeral_message_id: int) -> None:
    t.call("editEphemeralMessageMedia", {
        "chat_id": GROUP, "receiver_user_id": MEMBER, "ephemeral_message_id": ephemeral_message_id,
        "media": {"type": "photo", "media": "AgACAgIAAxkBAAID", "caption": "Your order #8812"}})


def edit_ephemeral_message_reply_markup(t: FakeTransport, ephemeral_message_id: int) -> None:
    t.call("editEphemeralMessageReplyMarkup", {
        "chat_id": GROUP, "receiver_user_id": MEMBER, "ephemeral_message_id": ephemeral_message_id,
        "reply_markup": {"inline_keyboard": [[{"text": "Track", "callback_data": "trk:8812"}]]}})


def delete_ephemeral_message(t: FakeTransport, ephemeral_message_id: int) -> None:
    t.call("deleteEphemeralMessage", {
        "chat_id": GROUP, "receiver_user_id": MEMBER, "ephemeral_message_id": ephemeral_message_id})


def approve_suggested_post(t: FakeTransport) -> None:
    t.call("approveSuggestedPost", {"chat_id": DIRECT_MESSAGES, "message_id": 52, "send_date": NOW + 86400})


def decline_suggested_post(t: FakeTransport) -> None:
    t.call("declineSuggestedPost", {
        "chat_id": DIRECT_MESSAGES, "message_id": 53, "comment": "Duplicates Monday's post"})


def run_all() -> FakeTransport:
    t = FakeTransport()
    edit_message_text(t)
    edit_message_caption(t)
    edit_message_media(t)
    edit_message_live_location(t)
    stop_message_live_location(t)
    edit_message_checklist(t)
    edit_message_reply_markup(t)
    stop_poll(t)
    delete_message(t)
    delete_messages(t)
    set_message_reaction(t)
    delete_message_reaction(t)
    delete_all_message_reactions(t)
    text_id = send_ephemeral(t, "sendMessage", {
        "text": "Your open orders: 2",
        "reply_markup": {"inline_keyboard": [[{"text": "Open", "callback_data": "orders:open"}]]}}, 41)
    photo_id = send_ephemeral(t, "sendPhoto", {"photo": "AgACAgIAAxkBAAID", "caption": "Your order #8812"}, 42)
    edit_ephemeral_message_text(t, text_id)
    edit_ephemeral_message_caption(t, photo_id)
    edit_ephemeral_message_media(t, photo_id)
    edit_ephemeral_message_reply_markup(t, text_id)
    delete_ephemeral_message(t, text_id)
    approve_suggested_post(t)
    decline_suggested_post(t)
    return t


if __name__ == "__main__":
    c.dump(run_all(), "editing")
