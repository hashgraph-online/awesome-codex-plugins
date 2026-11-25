"""Per-method requests for the Bot API domain `messages`: sending text, media, polls and chat actions,
forwarding and copying, and downloading a file. One function per method, synthetic ids, offline.

Run:  py -3 examples/python/recipes/api_messages.py
Written to examples/payloads/api-messages.json by `export_payloads.py --only api-messages`.
A call that needs a value returned by an earlier one (the album's message ids, a file_id) reads the
scripted result of that call. Notes that point here: data/bot-api/agent-notes/messages.json.
"""
from __future__ import annotations

import _common as c
from tgkit.transport import FakeTransport

STATUS = "production"
CONTEXT = "private, supergroup and channel chats; a step that needs a chat type, a right or a business account carries _context"
STEP_CONTEXT = {
    "sendMessageDraft": "private chat only (chat_id is the target private chat)",
    "sendChatAction": "private chat or supergroup; channel chats and channel direct messages chats aren't supported",
    "sendPaidMedia": "channel; bot admin with can_post_messages; the Star proceeds are credited to the channel's balance",
    "sendMediaGroup": "channel; bot admin with can_post_messages",
    "sendPoll": "supergroup; a non-admin member needs can_send_polls (ChatPermissions)",
    "sendChecklist": "business chat: business_connection_id of a connected business account; bot right can_reply",
}

PRIVATE = 111111111
GROUP = -1001234567890
CHANNEL = -1009876543210
BUSINESS_CHAT = 555555555
TOPIC = 77


def _message(chat_id: int, message_id: int, **content) -> dict:
    return {"message_id": message_id, "date": 1763450000, "chat": {"id": chat_id}, **content}


def send_message(t: FakeTransport) -> None:
    t.call("sendMessage", {
        "chat_id": GROUP, "message_thread_id": TOPIC,
        "text": "<b>Deploy finished</b>: https://example.com/r/812",
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": True},
        "reply_parameters": {"message_id": 4021},
        "reply_markup": {"inline_keyboard": [[{"text": "Open run", "url": "https://example.com/r/812"}]]},
    })


def send_message_draft(t: FakeTransport) -> None:
    """Two updates of one draft animate; the finished answer goes out with sendMessage."""
    draft = {"chat_id": PRIVATE, "draft_id": 9001, "can_stop": True, "keep_on_stop": True}
    t.call("sendMessageDraft", {**draft, "text": "Checking the three failing jobs"})
    t.call("sendMessageDraft", {**draft, "text": "Checking the three failing jobs. Two fail on the same migration"})


def send_media_group(t: FakeTransport) -> list[dict]:
    """An album of 3 photos; the caption sits on the first item."""
    t.script("sendMediaGroup", [_message(CHANNEL, 5201), _message(CHANNEL, 5202), _message(CHANNEL, 5203)])
    media = [
        {"type": "photo", "media": "AgACAgIAAxkBAAIBa2Zx0001", "caption": "<b>Kyiv at night</b>", "parse_mode": "HTML"},
        {"type": "photo", "media": "AgACAgIAAxkBAAIBa2Zx0002"},
        {"type": "photo", "media": "AgACAgIAAxkBAAIBa2Zx0003"},
    ]
    c.check(2 <= len(media) <= 10, "an album has 2-10 items")
    return t.call("sendMediaGroup", {"chat_id": CHANNEL, "media": media, "disable_notification": True})


def forward_message(t: FakeTransport) -> None:
    t.call("forwardMessage", {"chat_id": GROUP, "from_chat_id": CHANNEL, "message_id": 5201, "disable_notification": True})


def forward_messages(t: FakeTransport, album: list[dict]) -> None:
    ids = [m["message_id"] for m in album]
    c.check(ids == sorted(set(ids)) and 1 <= len(ids) <= 100, "1-100 ids in strictly increasing order")
    t.call("forwardMessages", {"chat_id": GROUP, "from_chat_id": CHANNEL, "message_ids": ids})


def copy_message(t: FakeTransport) -> None:
    t.call("copyMessage", {"chat_id": GROUP, "message_thread_id": TOPIC, "from_chat_id": CHANNEL, "message_id": 5201,
                           "caption": "Weekly digest #12", "show_caption_above_media": True})


def copy_messages(t: FakeTransport, album: list[dict]) -> None:
    ids = [m["message_id"] for m in album]
    t.call("copyMessages", {"chat_id": PRIVATE, "from_chat_id": CHANNEL, "message_ids": ids, "remove_caption": True})


def send_photo(t: FakeTransport) -> None:
    t.call("sendPhoto", {"chat_id": PRIVATE, "photo": "AgACAgIAAxkBAAIBcGZx0101",
                         "caption": "<b>Build graph</b> for run 812", "parse_mode": "HTML",
                         "show_caption_above_media": True})


def send_audio(t: FakeTransport) -> None:
    t.call("sendAudio", {"chat_id": PRIVATE, "audio": "CQACAgIAAxkBAAIBdGZx0201", "caption": "Episode 12",
                         "performer": "Dev Notes", "title": "Episode 12: Migrations", "duration": 1894})


def send_document(t: FakeTransport) -> dict:
    """A stored file_id is re-sent; the result carries the document the bot can fetch again with getFile."""
    t.script("sendDocument", _message(PRIVATE, 6001, document={
        "file_id": "BQACAgIAAxkBAAICdGZx0301", "file_unique_id": "AgADjQ", "file_name": "report-812.pdf",
        "mime_type": "application/pdf", "file_size": 48213}))
    return t.call("sendDocument", {"chat_id": PRIVATE, "document": "BQACAgIAAxkBAAICdGZx0301",
                                   "caption": "Test report, run 812"})


def send_video(t: FakeTransport) -> None:
    t.call("sendVideo", {"chat_id": PRIVATE, "video": "BAACAgIAAxkBAAICeGZx0401", "cover": "AgACAgIAAxkBAAIBcGZx0402",
                         "start_timestamp": 5, "duration": 42, "width": 1280, "height": 720,
                         "caption": "Demo of the new onboarding"})


def send_animation(t: FakeTransport) -> None:
    t.call("sendAnimation", {"chat_id": GROUP, "animation": "CgACAgIAAxkBAAICfGZx0501", "duration": 3,
                             "width": 480, "height": 270, "caption": "Shipped"})


def send_voice(t: FakeTransport) -> None:
    t.call("sendVoice", {"chat_id": PRIVATE, "voice": "AwACAgIAAxkBAAICgGZx0601", "duration": 14,
                         "caption": "Short summary"})


def send_video_note(t: FakeTransport) -> None:
    t.call("sendVideoNote", {"chat_id": PRIVATE, "video_note": "DQACAgIAAxkBAAICimZx0701", "duration": 12,
                             "length": 384})


def send_live_photo(t: FakeTransport) -> None:
    """Both parts are file_ids; a live photo can't be sent by URL."""
    t.call("sendLivePhoto", {"chat_id": PRIVATE, "live_photo": "BAACAgIAAxkBAAICkGZx0801",
                             "photo": "AgACAgIAAxkBAAIBcGZx0802", "caption": "Morning in Kyiv"})


def send_paid_media(t: FakeTransport) -> None:
    t.call("sendPaidMedia", {
        "chat_id": CHANNEL, "star_count": 50, "payload": "album:kyiv-night",
        "media": [{"type": "photo", "media": "AgACAgIAAxkBAAIBcGZx0901"},
                  {"type": "video", "media": "BAACAgIAAxkBAAICeGZx0902", "duration": 42, "width": 1280, "height": 720}],
        "caption": "Kyiv at night: 1 photo, 1 video"})


def send_location(t: FakeTransport) -> None:
    """A live location: live_period, heading and proximity_alert_radius belong together."""
    t.call("sendLocation", {"chat_id": PRIVATE, "latitude": 50.4501, "longitude": 30.5234, "horizontal_accuracy": 25.0,
                            "live_period": 900, "heading": 90, "proximity_alert_radius": 150})


def send_venue(t: FakeTransport) -> None:
    t.call("sendVenue", {"chat_id": PRIVATE, "latitude": 50.4476, "longitude": 30.5225, "title": "Pizza Place",
                         "address": "12 Khreshchatyk St, Kyiv"})


def send_contact(t: FakeTransport) -> None:
    vcard = "BEGIN:VCARD\nVERSION:3.0\nFN:Ihor Savchenko\nTEL;TYPE=CELL:+15555550123\nEND:VCARD"
    c.check(len(vcard.encode("utf-8")) <= 2048, "vcard is at most 2048 bytes")
    t.call("sendContact", {"chat_id": PRIVATE, "phone_number": "+15555550123", "first_name": "Ihor",
                           "last_name": "Savchenko", "vcard": vcard})


def send_poll(t: FakeTransport) -> None:
    """A quiz: correct_option_ids is required; open_period and close_date are mutually exclusive."""
    correct = [1]
    c.check(correct == sorted(set(correct)), "correct_option_ids are increasing 0-based ids")
    t.call("sendPoll", {"chat_id": GROUP, "question": "Which of these is prime?",
                        "options": [{"text": "9"}, {"text": "11"}, {"text": "15"}],
                        "type": "quiz", "correct_option_ids": correct, "is_anonymous": False,
                        "explanation": "9 = 3x3 and 15 = 3x5.", "open_period": 600})


def send_checklist(t: FakeTransport) -> None:
    t.call("sendChecklist", {
        "business_connection_id": "BCxyz", "chat_id": BUSINESS_CHAT,
        "checklist": {"title": "Before your appointment", "others_can_mark_tasks_as_done": True,
                      "tasks": [{"id": 1, "text": "Bring your passport"}, {"id": 2, "text": "Arrive 10 minutes early"}]}})


def send_dice(t: FakeTransport) -> None:
    t.script("sendDice", _message(GROUP, 6101, dice={"emoji": "🎯", "value": 6}))
    sent = t.call("sendDice", {"chat_id": GROUP, "emoji": "🎯", "reply_parameters": {"message_id": 4021}})
    c.check(1 <= sent["dice"]["value"] <= 6, "the value is Telegram's: read Message.dice.value, 1-6 for the dart")


def send_chat_action(t: FakeTransport) -> None:
    t.call("sendChatAction", {"chat_id": PRIVATE, "action": "typing"})


def get_file(t: FakeTransport, document_message: dict) -> None:
    doc = document_message["document"]
    t.script("getFile", {"file_id": doc["file_id"], "file_unique_id": doc["file_unique_id"],
                         "file_size": doc["file_size"], "file_path": "documents/file_3.pdf"})
    info = t.call("getFile", {"file_id": doc["file_id"]})
    c.check(info["file_size"] <= 20 * 1024 * 1024, "within the 20 MB download limit")


def run_all() -> FakeTransport:
    t = FakeTransport()
    send_message(t)
    send_message_draft(t)
    album = send_media_group(t)
    forward_message(t)
    forward_messages(t, album)
    copy_message(t)
    copy_messages(t, album)
    send_photo(t)
    send_audio(t)
    document = send_document(t)
    send_video(t)
    send_animation(t)
    send_voice(t)
    send_video_note(t)
    send_live_photo(t)
    send_paid_media(t)
    send_location(t)
    send_venue(t)
    send_contact(t)
    send_poll(t)
    send_checklist(t)
    send_dice(t)
    send_chat_action(t)
    get_file(t, document)
    return t


if __name__ == "__main__":
    c.dump(run_all(), "API messages")
