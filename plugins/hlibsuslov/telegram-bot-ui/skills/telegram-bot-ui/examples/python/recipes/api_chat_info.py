"""Chat info: one request per method (chat settings, pins, members read-out, boosts, verification, user profile reads).

Run:  py -3 examples/python/recipes/api_chat_info.py        (offline; nothing is sent)
Written to payloads/api-chat-info.json by export_payloads.py. Ids, names and file ids are synthetic.
leaveChat, removeChatVerification and removeUserVerification are recorded requests only: a bot sends
them on a human operator's decision, with the reason logged. Where a call needs a value an earlier call
returned (the bot's own rights, the pinned message, can_set_sticker_set), FakeTransport.script supplies
that result. A new file is shown as "attach://<part>"; its bytes travel as a multipart part
(references/media-and-files.md#uploading).
"""
from __future__ import annotations

import _common as c
from tgkit.transport import FakeTransport

STATUS = "production (leaveChat and verification removals are recorded requests, never sent)"
CONTEXT = ("supergroup, group and channel where the bot is an administrator; user reads by user_id; "
           "verification calls only for a bot that represents an organization")

CHANGE_INFO = "bot admin with can_change_info (the method says only 'appropriate administrator rights')"
PIN_RIGHTS = "groups: bot admin with can_pin_messages; channels: can_edit_messages; private chats: no rights"
ORGANIZATION = "bot that represents a verifying organization"
STEP_CONTEXT = {
    "getChat": "any chat the bot can see; @username only for supergroups and channels",
    "getChatMember": "group, supergroup or channel; other users guaranteed only when the bot is an administrator",
    "getChatAdministrators": "group, supergroup or channel; return_bots lists other bot admins too",
    "getChatMemberCount": "group, supergroup or channel",
    "setChatTitle": f"group, supergroup or channel (not private); {CHANGE_INFO}",
    "setChatDescription": f"group, supergroup or channel; {CHANGE_INFO}",
    "setChatPhoto": f"group, supergroup or channel (not private); {CHANGE_INFO}; multipart/form-data upload",
    "deleteChatPhoto": f"group, supergroup or channel (not private); {CHANGE_INFO}",
    "pinChatMessage": PIN_RIGHTS,
    "unpinChatMessage": PIN_RIGHTS,
    "unpinAllChatMessages": f"{PIN_RIGHTS}; clears every pin in the chat",
    "setChatStickerSet": "supergroup; bot admin, ChatFullInfo.can_set_sticker_set is true",
    "deleteChatStickerSet": "supergroup; bot admin, ChatFullInfo.can_set_sticker_set is true",
    "getUserChatBoosts": "chat where the bot is an administrator (can_manage_chat: get boost list)",
    "verifyChat": f"bot, supergroup or channel (not a channel direct messages chat); {ORGANIZATION}",
    "verifyUser": ORGANIZATION,
    "removeChatVerification": f"chat verified by this organization; {ORGANIZATION}; recorded, not sent",
    "removeUserVerification": f"user verified by this organization; {ORGANIZATION}; recorded, not sent",
    "leaveChat": "group, supergroup or channel (not a channel direct messages chat); recorded, not sent",
    "getUserProfilePhotos": "any user_id; limit 1-100",
    "getUserProfileAudios": "any user_id; limit 1-100",
    "getUserPersonalChatMessages": "user with a personal chat on their profile; limit 1-20",
    "getChatShareThemeBackdrops": "no parameters; one list for every chat",
}

SUPERGROUP = -1001234567890
OLD_SUPERGROUP = -1001555666777
CHANNEL = -1009876543210
UNKNOWN_GROUP = -1001999888777
NOW = 1763191000
DAY = 86400
BOT = {"id": 777000111, "is_bot": True, "first_name": "Community Guard", "username": "community_guard_bot"}
OWNER = {"id": 333333333, "is_bot": False, "first_name": "Iryna"}
MODERATOR = {"id": 555555555, "is_bot": False, "first_name": "Andrii"}
MEMBER = {"id": 222222222, "is_bot": False, "first_name": "Olena"}
PERSONAL_CHANNEL = {"id": -1004445556667, "type": "channel", "title": "Olena cooks"}
RULES_POST = 4210
STICKER_SET = "foodies_of_kyiv_by_community_guard_bot"

RIGHTS_OFF = {"is_anonymous": False, "can_manage_chat": True, "can_delete_messages": False,
              "can_manage_video_chats": False, "can_restrict_members": False, "can_promote_members": False,
              "can_change_info": False, "can_invite_users": False, "can_post_stories": False,
              "can_edit_stories": False, "can_delete_stories": False, "can_send_welcome_messages": False}


def _admin(user: dict, **rights) -> dict:
    """A ChatMemberAdministrator, required flags filled."""
    return {"status": "administrator", "user": user, "can_be_edited": False, **RIGHTS_OFF, **rights}


def has_right(member: dict, right: str) -> bool:
    """A creator holds every right but carries no can_* flags; an administrator carries each flag."""
    return member["status"] == "creator" or bool(member.get(right))


# --- reading the chat ------------------------------------------------------------------------------

def get_chat(t: FakeTransport) -> dict:
    t.script("getChat", {
        "id": SUPERGROUP, "type": "supergroup", "title": "Foodies of Kyiv", "accent_color_id": 2,
        "max_reaction_count": 11, "accepted_gift_types": {"unlimited_gifts": True, "limited_gifts": True,
                                                         "unique_gifts": True, "premium_subscription": True,
                                                         "gifts_from_channels": True},
        "description": "Recipes and restaurant tips", "can_set_sticker_set": True,
        "pinned_message": {"message_id": 4100, "date": NOW - 30 * DAY,
                           "chat": {"id": SUPERGROUP, "type": "supergroup", "title": "Foodies of Kyiv"},
                           "text": "Rules (2025)"},
    })
    return t.call("getChat", {"chat_id": SUPERGROUP})


def get_chat_member(t: FakeTransport) -> dict:
    t.script("getChatMember", _admin(BOT, can_change_info=True, can_pin_messages=True, can_invite_users=True))
    return t.call("getChatMember", {"chat_id": SUPERGROUP, "user_id": BOT["id"]})


def get_chat_administrators(t: FakeTransport) -> list:
    t.script("getChatAdministrators", [
        {"status": "creator", "user": OWNER, "is_anonymous": False},
        _admin(BOT, can_change_info=True, can_pin_messages=True, can_invite_users=True),
        _admin(MODERATOR, can_delete_messages=True, can_restrict_members=True, can_pin_messages=True),
    ])
    return t.call("getChatAdministrators", {"chat_id": SUPERGROUP, "return_bots": True})


def get_chat_member_count(t: FakeTransport) -> int:
    t.script("getChatMemberCount", 1342)
    return t.call("getChatMemberCount", {"chat_id": SUPERGROUP})


# --- chat settings ---------------------------------------------------------------------------------

def set_chat_title(t: FakeTransport) -> bool:
    return t.call("setChatTitle", {"chat_id": SUPERGROUP, "title": "Foodies of Kyiv: Spring Fest"})


def set_chat_description(t: FakeTransport) -> bool:
    return t.call("setChatDescription", {"chat_id": SUPERGROUP,
                                         "description": "Recipes, restaurant tips and the Spring Fest schedule"})


def set_chat_photo(t: FakeTransport) -> bool:
    return t.call("setChatPhoto", {"chat_id": SUPERGROUP, "photo": "attach://chat_photo"})


def delete_chat_photo(t: FakeTransport) -> bool:
    return t.call("deleteChatPhoto", {"chat_id": CHANNEL})


def set_chat_sticker_set(t: FakeTransport) -> bool:
    return t.call("setChatStickerSet", {"chat_id": SUPERGROUP, "sticker_set_name": STICKER_SET})


def delete_chat_sticker_set(t: FakeTransport) -> bool:
    return t.call("deleteChatStickerSet", {"chat_id": OLD_SUPERGROUP})


# --- pins ------------------------------------------------------------------------------------------

def pin_chat_message(t: FakeTransport) -> bool:
    return t.call("pinChatMessage", {"chat_id": SUPERGROUP, "message_id": RULES_POST, "disable_notification": True})


def unpin_chat_message(t: FakeTransport, old_pin_id: int) -> bool:
    return t.call("unpinChatMessage", {"chat_id": SUPERGROUP, "message_id": old_pin_id})


def unpin_all_chat_messages(t: FakeTransport) -> bool:
    return t.call("unpinAllChatMessages", {"chat_id": MEMBER["id"]})


# --- boosts and user profile reads -----------------------------------------------------------------

def get_user_chat_boosts(t: FakeTransport) -> dict:
    t.script("getUserChatBoosts", {"boosts": [{
        "boost_id": "boost-7f3a", "add_date": NOW - 10 * DAY, "expiration_date": NOW + 20 * DAY,
        "source": {"source": "premium", "user": MEMBER}}]})
    return t.call("getUserChatBoosts", {"chat_id": CHANNEL, "user_id": MEMBER["id"]})


def get_user_profile_photos(t: FakeTransport) -> dict:
    t.script("getUserProfilePhotos", {"total_count": 3, "photos": [[
        {"file_id": "AgACAgIAAxkBAAEBolenaSmall", "file_unique_id": "AQADolenaS", "width": 160, "height": 160},
        {"file_id": "AgACAgIAAxkBAAEBolenaBig", "file_unique_id": "AQADolenaB", "width": 640, "height": 640}]]})
    return t.call("getUserProfilePhotos", {"user_id": MEMBER["id"], "offset": 0, "limit": 1})


def get_user_profile_audios(t: FakeTransport) -> dict:
    t.script("getUserProfileAudios", {"total_count": 1, "audios": [{
        "file_id": "CQACAgIAAxkBAAEBolenaAudio", "file_unique_id": "AgADolenaA", "duration": 184,
        "performer": "Olena", "title": "Kitchen playlist"}]})
    return t.call("getUserProfileAudios", {"user_id": MEMBER["id"], "offset": 0, "limit": 5})


def get_user_personal_chat_messages(t: FakeTransport) -> list:
    t.script("getUserPersonalChatMessages", [
        {"message_id": 88, "date": NOW - DAY, "chat": PERSONAL_CHANNEL, "text": "Borscht, my way"},
        {"message_id": 87, "date": NOW - 3 * DAY, "chat": PERSONAL_CHANNEL, "text": "Market haul"}])
    return t.call("getUserPersonalChatMessages", {"user_id": MEMBER["id"], "limit": 3})


def get_chat_share_theme_backdrops(t: FakeTransport) -> dict:
    t.script("getChatShareThemeBackdrops", c.fixture("get_chat_share_theme_backdrops_result.json")["result"])
    return t.call("getChatShareThemeBackdrops", {})


# --- verification (organization bots only) ---------------------------------------------------------

def verify_chat(t: FakeTransport) -> bool:
    text = "Official channel of Kyiv Food Fest"
    link = "Kyiv Food Fest"
    entities = [{"type": "text_link", "offset": text.index(link), "length": len(link),
                 "url": "https://example.com/food-fest"}]
    c.check(len(text) <= 70 and all(e["type"] == "text_link" for e in entities),
            "verifyChat: custom_description 0-70 characters, only text_link entities")
    return t.call("verifyChat", {"chat_id": CHANNEL, "custom_description": text,
                                 "custom_description_entities": entities})


def verify_user(t: FakeTransport) -> bool:
    text = "Accredited food guide, Kyiv Food Fest 2026"
    c.check(len(text) <= 70, "verifyUser: custom_description 0-70 characters")
    return t.call("verifyUser", {"user_id": MODERATOR["id"], "custom_description": text})


def remove_chat_verification(t: FakeTransport) -> bool:
    return t.call("removeChatVerification", {"chat_id": CHANNEL})


def remove_user_verification(t: FakeTransport) -> bool:
    return t.call("removeUserVerification", {"user_id": MODERATOR["id"]})


def leave_chat(t: FakeTransport) -> bool:
    return t.call("leaveChat", {"chat_id": UNKNOWN_GROUP})


def run_all() -> FakeTransport:
    t = FakeTransport()
    chat = get_chat(t)
    me = get_chat_member(t)
    c.check(has_right(me, "can_change_info") and has_right(me, "can_pin_messages"),
            "getChatMember(bot id) confirms can_change_info and can_pin_messages before acting")
    admins = get_chat_administrators(t)
    c.check(has_right(admins[0], "can_pin_messages") and "can_pin_messages" not in admins[0],
            "a creator item carries no can_* flags yet holds every right")
    c.check(isinstance(get_chat_member_count(t), int), "getChatMemberCount returns a plain Integer")
    set_chat_title(t)
    set_chat_description(t)
    set_chat_photo(t)
    delete_chat_photo(t)
    c.check(chat.get("can_set_sticker_set") is True, "getChat says the bot can change the group sticker set")
    set_chat_sticker_set(t)
    delete_chat_sticker_set(t)
    pin_chat_message(t)
    unpin_chat_message(t, chat["pinned_message"]["message_id"])
    unpin_all_chat_messages(t)
    boosts = get_user_chat_boosts(t)
    c.check(any(b["expiration_date"] > NOW for b in boosts["boosts"]), "an active boost: expiration_date in the future")
    photos = get_user_profile_photos(t)
    c.check(photos["total_count"] >= len(photos["photos"]), "page profile photos with offset against total_count")
    get_user_profile_audios(t)
    get_user_personal_chat_messages(t)
    backdrops = get_chat_share_theme_backdrops(t)
    c.check(backdrops["backdrops"][0]["colors"]["center_color"] >= 0, "backdrops resolve to RGB colors")
    for fn in (verify_chat, verify_user, remove_chat_verification, remove_user_verification, leave_chat):
        fn(t)
    c.check(sorted(t.methods()) == sorted(STEP_CONTEXT), "every chat-info method is called exactly once")
    return t


if __name__ == "__main__":
    c.dump(run_all(), "Chat info")
