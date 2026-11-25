"""Per-method request examples for the Bot API domain `business`, recorded offline (Bot API 10.5).

Business accounts, gifts, stories and emoji status: one small function per method makes the call the
agent note points at. The values are synthetic (a bakery owner who connected the bot, a second account
the same bot manages, made-up gift, story and emoji ids). `run_all()` returns the FakeTransport whose
`calls` `export_payloads.py --only api-business` writes to examples/payloads/api-business.json.

A call that depends on an earlier answer reads it from the scripted result: getBusinessAccountGifts
returns the owned_gift_id values that delete, convert, upgrade and transfer take; getAvailableGifts
returns the gift id sendGift takes; postStory returns the Story whose id editStory, repostStory and
deleteStory take. Calls that spend Stars (transferBusinessAccountStars, upgradeGift, transferGift,
sendGift, giftPremiumSubscription), move or give up gifts (convertGiftToStars, deleteBusinessAccountGift)
or delete (deleteBusinessMessages, deleteStory) are recorded requests, never sent: a bot makes them on
the owner's explicit confirmation of the exact gift, amount or message. A new file is shown as
"attach://<part>"; its bytes travel as a multipart part (references/media-and-files.md#uploading).

Run:  py -3 examples/python/recipes/api_business.py
"""
from __future__ import annotations

import _common as c
from tgkit.transport import FakeTransport

STATUS = "production (Star spending, gift moves and deletions are recorded requests, never sent)"
CONTEXT = "business connection with the right each step names; bot-level gift and emoji status calls need none"

CONN = "business connection"
STEP_CONTEXT = {
    "getBusinessConnection": f"{CONN} id from a business_connection or business_message update; no right named",
    "readBusinessMessage": f"{CONN} with can_read_messages; the chat was active in the last 24 hours",
    "deleteBusinessMessages": f"{CONN} with can_delete_sent_messages (bot's own messages) or "
                              "can_delete_all_messages (any); 1-100 ids from one chat; recorded, not sent",
    "setBusinessAccountName": f"{CONN} with can_edit_name (the method text says can_change_name)",
    "setBusinessAccountUsername": f"{CONN} with can_edit_username (the method text says can_change_username)",
    "setBusinessAccountBio": f"{CONN} with can_edit_bio (the method text says can_change_bio)",
    "setBusinessAccountProfilePhoto": f"{CONN} with can_edit_profile_photo; photo is a new upload",
    "removeBusinessAccountProfilePhoto": f"{CONN} with can_edit_profile_photo",
    "setBusinessAccountGiftSettings": f"{CONN} with can_change_gift_settings",
    "getBusinessAccountStarBalance": f"{CONN} with can_view_gifts_and_stars",
    "transferBusinessAccountStars": f"{CONN} with can_transfer_stars; 1-10000 Stars to the bot; recorded, not sent",
    "getBusinessAccountGifts": f"{CONN} with can_view_gifts_and_stars",
    "deleteBusinessAccountGift": f"{CONN} with can_convert_gifts_to_stars; regular, not limited, not refunded; "
                                 "recorded, not sent",
    "convertGiftToStars": f"{CONN} with can_convert_gifts_to_stars; regular gift; recorded, not sent",
    "upgradeGift": f"{CONN} with can_transfer_and_upgrade_gifts (+ can_transfer_stars if paid); recorded, not sent",
    "transferGift": f"{CONN} with can_transfer_and_upgrade_gifts (+ can_transfer_stars if paid); new owner "
                    "chat active in the last 24 hours; recorded, not sent",
    "getAvailableGifts": "no business connection; any bot",
    "sendGift": "no business connection; spends the bot's Stars (Gift.star_count); recorded, not sent",
    "giftPremiumSubscription": "no business connection; spends 1000, 1500 or 2500 of the bot's Stars; "
                               "recorded, not sent",
    "getUserGifts": "no business connection; any user",
    "getChatGifts": "no business connection; channel (saved and unsaved filters need can_post_messages)",
    "getUniqueGift": "no business connection; name of a unique gift",
    "postStory": f"{CONN} with can_manage_stories; content is a new upload",
    "editStory": f"{CONN} with can_manage_stories; a story the bot posted; content is a new upload",
    "repostStory": f"two {CONN}s of this bot, both with can_manage_stories; source story posted by the bot",
    "deleteStory": f"{CONN} with can_manage_stories; a story the bot posted; recorded, not sent",
    "setUserEmojiStatus": "no business connection; the user granted access via WebApp.requestEmojiStatusAccess",
}

NOW = 1763191000
DAY = 86400
BAKERY = "BCbakery7Qx"                 # the bakery owner's connection
CAFE = "BCcafe2Rk"                     # a second account the same bot manages
OWNER = {"id": 444444444, "is_bot": False, "first_name": "Dana", "last_name": "Koval"}
CAFE_CHAT = 666666666                  # the second account's chat (the source of a repost)
CUSTOMER = 555555555
FAN = 222222222                        # a user who earned a reward
CHANNEL = "@bakery_news"
ALL_RIGHTS = {r: True for r in (
    "can_reply", "can_read_messages", "can_delete_sent_messages", "can_edit_name", "can_edit_bio",
    "can_edit_profile_photo", "can_edit_username", "can_change_gift_settings", "can_view_gifts_and_stars",
    "can_convert_gifts_to_stars", "can_transfer_and_upgrade_gifts", "can_transfer_stars", "can_manage_stories")}


def _sticker(uid: str) -> dict:
    return {"file_id": f"CAACAgIAAx{uid}", "file_unique_id": f"AgAD{uid}", "type": "regular",
            "width": 512, "height": 512, "is_animated": True, "is_video": False}


def _gift(gift_id: str, stars: int, **fields) -> dict:
    """A Gift as getAvailableGifts and OwnedGiftRegular carry it."""
    return {"id": gift_id, "sticker": _sticker(gift_id[-4:]), "star_count": stars, **fields}


def _unique_gift(name: str, number: int) -> dict:
    part = {"sticker": _sticker(name[-4:]), "rarity_per_mille": 12}
    return {"gift_id": "5170145012310081615", "base_name": "Plush Pepe", "name": name, "number": number,
            "model": {"name": "Baker", **part}, "symbol": {"name": "Croissant", **part},
            "backdrop": {"name": "Wheat", "rarity_per_mille": 20, "colors": {
                "center_color": 0xE8C07D, "edge_color": 0xB5893F, "symbol_color": 0x6B4A1A, "text_color": 0xFFFFFF}}}


def _story(chat_id: int, story_id: int) -> dict:
    return {"chat": {"id": chat_id, "type": "private", "first_name": "Dana"}, "id": story_id}


# --- connection and messages -------------------------------------------------------------------

def get_business_connection(t: FakeTransport) -> dict:
    t.script("getBusinessConnection", {"id": BAKERY, "user": OWNER, "user_chat_id": OWNER["id"], "date": NOW - DAY,
                                       "rights": ALL_RIGHTS, "is_enabled": True})
    return t.call("getBusinessConnection", {"business_connection_id": BAKERY})


def read_business_message(t: FakeTransport) -> None:
    t.call("readBusinessMessage", {"business_connection_id": BAKERY, "chat_id": CUSTOMER, "message_id": 5012})


def delete_business_messages(t: FakeTransport) -> None:
    t.call("deleteBusinessMessages", {"business_connection_id": BAKERY, "message_ids": [5013, 5014]})


# --- profile -----------------------------------------------------------------------------------

def set_business_account_name(t: FakeTransport) -> None:
    t.call("setBusinessAccountName", {"business_connection_id": BAKERY, "first_name": "Dana", "last_name": "Bakery"})


def set_business_account_username(t: FakeTransport) -> None:
    t.call("setBusinessAccountUsername", {"business_connection_id": BAKERY, "username": "dana_bakery"})


def set_business_account_bio(t: FakeTransport) -> None:
    t.call("setBusinessAccountBio", {"business_connection_id": BAKERY, "bio": "Sourdough and cardamom buns · daily 8:00-19:00"})


def set_business_account_profile_photo(t: FakeTransport) -> None:
    t.call("setBusinessAccountProfilePhoto", {"business_connection_id": BAKERY,
                                              "photo": {"type": "static", "photo": "attach://avatar"}})


def remove_business_account_profile_photo(t: FakeTransport) -> None:
    t.call("removeBusinessAccountProfilePhoto", {"business_connection_id": BAKERY, "is_public": True})


# --- gifts and Stars of the business account ---------------------------------------------------

def set_business_account_gift_settings(t: FakeTransport) -> None:
    t.call("setBusinessAccountGiftSettings", {
        "business_connection_id": BAKERY, "show_gift_button": True,
        "accepted_gift_types": {"unlimited_gifts": True, "limited_gifts": True, "unique_gifts": True,
                                "premium_subscription": False, "gifts_from_channels": False}})


def get_business_account_star_balance(t: FakeTransport) -> dict:
    t.script("getBusinessAccountStarBalance", {"amount": 420})
    return t.call("getBusinessAccountStarBalance", {"business_connection_id": BAKERY})


def transfer_business_account_stars(t: FakeTransport, balance: dict) -> None:
    t.call("transferBusinessAccountStars", {"business_connection_id": BAKERY, "star_count": min(balance["amount"], 400)})


OWNED = {"total_count": 4, "next_offset": "", "gifts": [
    {"type": "regular", "owned_gift_id": "og_1181", "gift": _gift("5168043875654172773", 15),
     "send_date": NOW - 9 * DAY, "is_saved": False},
    {"type": "regular", "owned_gift_id": "og_1182", "gift": _gift("5170233102089322756", 50),
     "send_date": NOW - 7 * DAY, "is_saved": False, "convert_star_count": 40},
    {"type": "regular", "owned_gift_id": "og_1190", "send_date": NOW - 3 * DAY, "is_saved": True,
     "gift": _gift("5170145012310081615", 350, upgrade_star_count=250, total_count=50000, remaining_count=1200),
     "can_be_upgraded": True, "prepaid_upgrade_star_count": 250},
    {"type": "unique", "owned_gift_id": "og_1201", "gift": _unique_gift("PlushPepe-1234", 1234),
     "send_date": NOW - 2 * DAY, "is_saved": True, "can_be_transferred": True, "transfer_star_count": 25,
     "next_transfer_date": NOW - DAY},
]}


def get_business_account_gifts(t: FakeTransport) -> dict:
    t.script("getBusinessAccountGifts", OWNED)
    return t.call("getBusinessAccountGifts", {"business_connection_id": BAKERY, "exclude_from_blockchain": True,
                                              "sort_by_price": True, "offset": "", "limit": 50})


def delete_business_account_gift(t: FakeTransport, owned: dict) -> None:
    gift = next(g for g in owned["gifts"] if g["type"] == "regular" and "total_count" not in g["gift"]
                and "convert_star_count" not in g)
    t.call("deleteBusinessAccountGift", {"business_connection_id": BAKERY, "owned_gift_id": gift["owned_gift_id"]})


def convert_gift_to_stars(t: FakeTransport, owned: dict) -> None:
    gift = next(g for g in owned["gifts"] if g.get("convert_star_count"))
    t.call("convertGiftToStars", {"business_connection_id": BAKERY, "owned_gift_id": gift["owned_gift_id"]})


def upgrade_gift(t: FakeTransport, owned: dict) -> None:
    gift = next(g for g in owned["gifts"] if g.get("can_be_upgraded"))
    prepaid = gift.get("prepaid_upgrade_star_count", 0) > 0
    t.call("upgradeGift", {"business_connection_id": BAKERY, "owned_gift_id": gift["owned_gift_id"],
                           "keep_original_details": True,
                           "star_count": 0 if prepaid else gift["gift"]["upgrade_star_count"]})


def transfer_gift(t: FakeTransport, owned: dict) -> None:
    gift = next(g for g in owned["gifts"] if g.get("can_be_transferred") and g["next_transfer_date"] <= NOW)
    t.call("transferGift", {"business_connection_id": BAKERY, "owned_gift_id": gift["owned_gift_id"],
                            "new_owner_chat_id": CUSTOMER, "star_count": gift["transfer_star_count"]})


# --- gifts the bot sends and reads -------------------------------------------------------------

def get_available_gifts(t: FakeTransport) -> dict:
    t.script("getAvailableGifts", {"gifts": [
        _gift("5170145012310081615", 15),
        _gift("5168103777563050263", 25, upgrade_star_count=25),
        _gift("5170250947678437525", 100, total_count=100000, remaining_count=4210,
              personal_total_count=10, personal_remaining_count=10),
    ]})
    return t.call("getAvailableGifts", {})


def send_gift(t: FakeTransport, gifts: dict) -> None:
    gift = next(g for g in gifts["gifts"] if "upgrade_star_count" in g and "total_count" not in g)
    t.script("sendGift", True)
    t.call("sendGift", {"user_id": FAN, "gift_id": gift["id"], "pay_for_upgrade": False,
                        "text": "Thank you for a year with us!", "text_entities": [
                            {"type": "bold", "offset": 0, "length": 9}]})


def gift_premium_subscription(t: FakeTransport) -> None:
    t.call("giftPremiumSubscription", {"user_id": FAN, "month_count": 3, "star_count": 1000,
                                       "text": "Three months of Premium from the bakery"})


def get_user_gifts(t: FakeTransport) -> dict:
    t.script("getUserGifts", {"total_count": 1, "next_offset": "", "gifts": [
        {"type": "unique", "gift": _unique_gift("PlushPepe-1234", 1234), "send_date": NOW - DAY}]})
    return t.call("getUserGifts", {"user_id": FAN, "exclude_unlimited": True, "sort_by_price": True, "limit": 20})


def get_chat_gifts(t: FakeTransport) -> None:
    t.script("getChatGifts", {"total_count": 0, "gifts": []})
    t.call("getChatGifts", {"chat_id": CHANNEL, "exclude_unique": False, "offset": "", "limit": 20})


def get_unique_gift(t: FakeTransport, user_gifts: dict) -> dict:
    name = next(g["gift"]["name"] for g in user_gifts["gifts"] if g["type"] == "unique")
    t.script("getUniqueGift", _unique_gift(name, 1234))
    return t.call("getUniqueGift", {"name": name})


# --- stories -----------------------------------------------------------------------------------

def post_story(t: FakeTransport) -> dict:
    t.script("postStory", _story(OWNER["id"], 41))
    return t.call("postStory", {
        "business_connection_id": BAKERY, "content": {"type": "photo", "photo": "attach://story1"},
        "active_period": DAY, "caption": "New autumn menu is here",
        "areas": [{"position": {"x_percentage": 50, "y_percentage": 85, "width_percentage": 60,
                                "height_percentage": 8, "rotation_angle": 0, "corner_radius_percentage": 4},
                   "type": {"type": "link", "url": "https://example.com/menu"}}],
        "post_to_chat_page": True})


def edit_story(t: FakeTransport, story: dict) -> None:
    t.script("editStory", story)
    t.call("editStory", {"business_connection_id": BAKERY, "story_id": story["id"],
                         "content": {"type": "photo", "photo": "attach://story1v2"},
                         "caption": "New autumn menu: now with pumpkin buns"})


def repost_story(t: FakeTransport, story: dict) -> None:
    t.script("repostStory", _story(CAFE_CHAT, 7))
    t.call("repostStory", {"business_connection_id": CAFE, "from_chat_id": story["chat"]["id"],
                           "from_story_id": story["id"], "active_period": 12 * 3600})


def delete_story(t: FakeTransport, story: dict) -> None:
    t.call("deleteStory", {"business_connection_id": BAKERY, "story_id": story["id"]})


# --- emoji status ------------------------------------------------------------------------------

def set_user_emoji_status(t: FakeTransport) -> None:
    t.call("setUserEmojiStatus", {"user_id": FAN, "emoji_status_custom_emoji_id": "5368324170671202286",
                                  "emoji_status_expiration_date": NOW + 30 * DAY})


def run_all() -> FakeTransport:
    t = FakeTransport()
    conn = get_business_connection(t)
    c.check(conn["is_enabled"] and conn["rights"].get("can_read_messages"),
            "getBusinessConnection returns the rights the following calls depend on")
    for fn in (read_business_message, delete_business_messages, set_business_account_name,
               set_business_account_username, set_business_account_bio, set_business_account_profile_photo,
               remove_business_account_profile_photo, set_business_account_gift_settings):
        fn(t)
    balance = get_business_account_star_balance(t)
    transfer_business_account_stars(t, balance)
    owned = get_business_account_gifts(t)
    c.check(all(g.get("owned_gift_id") for g in owned["gifts"]),
            "getBusinessAccountGifts returns the owned_gift_id each gift call takes")
    for fn in (delete_business_account_gift, convert_gift_to_stars, upgrade_gift, transfer_gift):
        fn(t, owned)
    send_gift(t, get_available_gifts(t))
    gift_premium_subscription(t)
    user_gifts = get_user_gifts(t)
    get_chat_gifts(t)
    get_unique_gift(t, user_gifts)
    story = post_story(t)
    c.check(story["id"] == 41, "postStory returns the Story whose id editStory, repostStory and deleteStory take")
    edit_story(t, story)
    repost_story(t, story)
    delete_story(t, story)
    set_user_emoji_status(t)
    c.check(sorted(t.methods()) == sorted(STEP_CONTEXT), "every business method is called exactly once")
    return t


if __name__ == "__main__":
    c.dump(run_all(), "Business accounts, gifts, stories, emoji status")
