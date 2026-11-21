"""Mini-recipes for the specialized 10.3/10.4 changes (one function per row group).

Run:  py -3 examples/python/recipes/mini_recipes.py           (offline; destructive calls dry-run)
Each function: request or incoming fixture -> handling -> checks. See
recipes/mini-recipes.md for the when/why/limits of each.
"""
from __future__ import annotations

import re

import _common as c
from tgkit.ephemeral import ephemeral_params, migrate_ephemeral_10_2
from tgkit.errors import TelegramError
from tgkit.text import entity_for
from tgkit.transport import FakeTransport, TelegramErrorResponse

GROUP = -1001234567890


def m01_welcome_right(t: FakeTransport) -> None:
    """10.3 can_send_welcome_messages: grant it (dry-run), detect it, use it."""
    plan = {"chat_id": GROUP, "user_id": 999000111, "can_send_welcome_messages": True, "can_invite_users": True}
    print("   dry-run promoteChatMember", plan)          # a rights change: run only on request
    upd = c.fixture("chat_member_admin_welcome.json")["my_chat_member"]
    rights = upd["new_chat_member"]
    can_welcome = rights.get("status") == "administrator" and rights.get("can_send_welcome_messages") is True
    c.check(can_welcome, "bot detects the welcome right from my_chat_member")
    # An administrator bot may send an ephemeral message to any non-bot member;
    # a welcome is shown only to the newcomer, the group isn't spammed.
    t.call("sendMessage", {"chat_id": GROUP, "text": "Welcome! Pin your lunch preferences with /prefs.",
                           "ephemeral_message_parameters": {"receiver_user_id": 222222222}})


def m02_community_join(t: FakeTransport) -> None:
    msg = c.fixture("message_community_chat_joined.json")["message"]
    community = msg["community_chat_joined"]["community"]
    c.check(isinstance(community["id"], int) and community["id"] > 2 ** 32, "community id needs 64-bit storage")
    t.call("sendMessage", {"chat_id": msg["chat"]["id"], "text": f"Welcome from {community['name']}!",
                           "ephemeral_message_parameters": {"receiver_user_id": msg["from"]["id"]}})


def m03_unique_gift_text(t: FakeTransport) -> None:
    bm = c.fixture("message_unique_gift_info.json")["business_message"]
    info = bm["unique_gift"]
    note = info.get("text")
    shown = note if not info.get("is_private") else None    # private: receiver only
    c.check(note == "Happy birthday, Dan!" and shown is None,
            "gift note read with entities; is_private keeps it out of any public repost")
    t.call("sendMessage", {"business_connection_id": bm["business_connection_id"], "chat_id": bm["chat"]["id"],
                           "text": note, "entities": info.get("entities", [])})   # back to the receiver only


def m04_get_unique_gift(t: FakeTransport) -> None:
    t.script("getUniqueGift", {"gift_id": "5000", "base_name": "Plush Pepe", "name": "PlushPepe-17", "number": 17},
             TelegramErrorResponse(400, "Bad Request: gift not found"))
    gift = t.call("getUniqueGift", {"name": "PlushPepe-17"})
    c.check(gift["number"] == 17, "getUniqueGift by name")
    try:
        t.call("getUniqueGift", {"name": "NoSuchGift-1"})
    except TelegramError as err:
        c.check(err.category == "validation", "unknown name -> validation error, shown as 'gift not found'")


def m05_delete_business_gift(t: FakeTransport, *, execute: bool = False) -> dict:
    """DESTRUCTIVE: deletes a regular gift of a managed business account and the
    Stars are NOT received. Preconditions: business bot right
    can_convert_gifts_to_stars; regular (not unique) gift; not limited
    (Gift.total_count omitted); not refunded. Default: dry-run."""
    owned = {"type": "regular", "owned_gift_id": "OG-15", "gift": {"id": "g1", "star_count": 15}, "convert_star_count": 10}
    rights = {"can_convert_gifts_to_stars": True}
    problems = []
    if not rights.get("can_convert_gifts_to_stars"):
        problems.append("missing can_convert_gifts_to_stars")
    if owned["type"] != "regular":
        problems.append("only regular gifts")
    if "total_count" in owned["gift"]:
        problems.append("limited gifts can't be deleted")
    if owned.get("was_refunded"):
        problems.append("refunded gift")
    plan = {"method": "deleteBusinessAccountGift",
            "params": {"business_connection_id": "BCxyz", "owned_gift_id": owned["owned_gift_id"]},
            "consequence": f"gift removed; {owned.get('convert_star_count', 0)} Stars NOT received; irreversible",
            "problems": problems}
    if execute and not problems:
        t.call(plan["method"], plan["params"])
    c.check(not execute and "deleteBusinessAccountGift" not in t.methods(), "dry-run by default: nothing deleted")
    return plan


def m06_share_theme(t: FakeTransport) -> str:
    chat = c.fixture("get_chat_result_wallet_theme.json")["result"]
    backdrops = c.fixture("get_chat_share_theme_backdrops_result.json")["result"]["backdrops"]
    theme = chat.get("share_theme")
    if theme is None:
        desc = "default share screen"
    elif theme["type"] == "emoji":
        emojis = [e["emoji"] if e["type"] == "emoji" else f"<custom {e['custom_emoji_id']}>" for e in theme["emojis"]]
        bd = next((b for b in backdrops if b["id"] == theme.get("background_backdrop_id")), None)
        desc = f"emoji {' '.join(emojis)} on {bd['name'] if bd else 'default background'}"
    else:
        desc = f"unique gift {theme['gift']['name']}"
    c.check(desc.startswith("emoji 🍕 <custom 5368324170671202286> on Midnight"),
            "share theme resolved (EmojiType union + getChatShareThemeBackdrops)")
    return desc


SECONDARY = ("agent", "ai", "app", "game", "gay")


def m07_managed_bot_username(t: FakeTransport, suggested: str = "pizzaplace_ai") -> None:
    ok_regular = suggested.lower().endswith("bot")
    ok_secondary = suggested.lower().endswith(SECONDARY)
    c.check(ok_regular or ok_secondary, "suggested username ends with bot or a Premium suffix")
    t.call("sendMessage", {"chat_id": 111111111, "text": "Create your shop's assistant bot:",
                           "reply_markup": {"keyboard": [[{"text": "Create bot", "request_managed_bot": {
                               "request_id": 1, "suggested_name": "Pizza Agent", "suggested_username": suggested}}]],
                               "resize_keyboard": True, "one_time_keyboard": True}})
    created = {"bot": {"id": 888000111, "is_bot": True, "first_name": "Pizza Agent", "username": "pizzaplace_bot"}}
    c.check(created["bot"]["username"].endswith("bot"),
            "a Premium suffix becomes a SECONDARY username; the bot still gets a regular ...bot username")


def m08_verification_description(t: FakeTransport) -> None:
    text = "Official partner — see terms"
    ents = [entity_for(text, "terms", "text_link", url="https://example.com/partner-terms")]
    c.check(len(text) <= 70 and all(e["type"] == "text_link" for e in ents), "0-70 chars, only text_link entities")
    t.call("verifyChat", {"chat_id": GROUP, "custom_description": text, "custom_description_entities": ents})
    bad = [{"type": "bold", "offset": 0, "length": 8}]
    c.check(any(e["type"] != "text_link" for e in bad), "a bold entity would be rejected - validate before calling")


def m09_paid_messages_waived(t: FakeTransport) -> None:
    bm = c.fixture("message_paid_messages_waived.json")["business_message"]
    waived = "paid_messages_waived" in bm      # an EMPTY object: test presence, not truthiness
    c.check(waived and bm["paid_messages_waived"] == {}, "presence of {} is the signal: an empty dict is falsy in Python (test the key)")


def _utf16_slice(text: str, offset: int, length: int) -> str:
    return text.encode("utf-16-le")[2 * offset:2 * (offset + length)].decode("utf-16-le")


def m10_sensitive_entities(t: FakeTransport) -> None:
    m = c.fixture("message_entities_ton_bank.json")["message"]
    text = m["text"]
    masked = text
    for e in m["entities"]:
        if e["type"] == "bank_card_number":
            raw = _utf16_slice(text, e["offset"], e["length"])
            masked = masked.replace(raw, "•••• " + raw[-4:])
    c.check("4242 4242 4242 4242" not in masked and masked.endswith("•••• 4242"), "card number masked before logging")
    addr = next(e for e in m["entities"] if e["type"] == "ton_address")
    t.call("sendMessage", {"chat_id": m["chat"]["id"], "text": "Copy the address:",
                           "reply_markup": {"inline_keyboard": [[{"text": "Copy TON address", "copy_text": {
                               "text": _utf16_slice(text, addr["offset"], addr["length"])}}]]}})


def m11_area_position_rename() -> None:
    before = "from sdk.types import StoryAreaPosition as AreaPosition  # SDK < Bot API 10.4"
    after = "from sdk.types import AreaPosition                      # SDK >= 10.4"
    c.check("AreaPosition" in before and "StoryAreaPosition" not in after,
            "type renamed, JSON fields unchanged - alias the old name until the SDK upgrade")


def m12_ephemeral_media_edit(t: FakeTransport) -> None:
    base = {"chat_id": GROUP, "receiver_user_id": 111111111, "ephemeral_message_id": 5}
    # 10.3: a NEW file may be uploaded (multipart/form-data, attach://receipt).
    t.call("editEphemeralMessageMedia", {**base, "media": {"type": "photo", "media": "attach://receipt",
                                                           "caption": "Your receipt"}})
    t.call("editEphemeralMessageCaption", {**base, "caption": "Your receipt (updated)", "show_caption_above_media": True})
    t.call("editEphemeralMessageText", {**base, "rich_message": {"markdown": "**Paid** — $9.50"}})
    c.check(t.methods()[-3:] == ["editEphemeralMessageMedia", "editEphemeralMessageCaption", "editEphemeralMessageText"],
            "ephemeral media upload, caption above media, rich text edit")
    # 10.3: sendRichMessage accepts ephemeral_message_parameters too.
    cq = c.fixture("callback_card_user_a.json")["callback_query"]
    t.call("sendRichMessage", {**ephemeral_params(cq), "rich_message": {"blocks": [
        {"type": "heading", "size": 3, "text": "Your order"},
        {"type": "table", "is_compact": True, "cells": [[{"text": "Margherita", "align": "left", "valign": "middle"},
                                                         {"text": "$9.50", "align": "right", "valign": "middle"}]]}]}})
    t.call("answerCallbackQuery", {"callback_query_id": cq["id"]})
    # 10.2 -> 10.3 migration: top-level receiver_user_id / callback_query_id moved.
    old = {"chat_id": GROUP, "text": "Hi", "receiver_user_id": 111111111, "callback_query_id": "q1"}
    c.check(migrate_ephemeral_10_2(old) == {"chat_id": GROUP, "text": "Hi", "ephemeral_message_parameters": {
        "receiver_user_id": 111111111, "callback_query_id": "q1"}}, "10.2 parameters migrated into EphemeralMessageParameters")


def m13_widget_permission(chat_permissions: dict) -> bool:
    """10.4: can_send_other_messages now also covers widgets (groups: test server)."""
    return chat_permissions.get("can_send_other_messages", False)


def m14_received_widget() -> None:
    msg = c.fixture("message_with_widget.json")["message"]
    c.check("widget" in msg and msg.get("caption"), "Message.widget parsed; caption is the readable fallback")


def run_all():
    t = FakeTransport()
    for fn in (m01_welcome_right, m02_community_join, m03_unique_gift_text, m04_get_unique_gift,
               m05_delete_business_gift, m06_share_theme, m07_managed_bot_username,
               m08_verification_description, m09_paid_messages_waived, m10_sensitive_entities, m12_ephemeral_media_edit):
        print(f"-- {fn.__name__}")
        fn(t)
    print("-- m11_area_position_rename")
    m11_area_position_rename()
    c.check(m13_widget_permission({"can_send_messages": True}) is False, "no can_send_other_messages -> no widgets")
    m14_received_widget()
    return t


if __name__ == "__main__":
    c.dump(run_all(), "Mini-recipes")
