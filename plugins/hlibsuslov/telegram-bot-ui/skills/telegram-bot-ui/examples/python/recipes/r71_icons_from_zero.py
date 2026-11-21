"""R71 - Icons for a NEW bot from zero: no ids yet, capture them from the owner, then switch on.

Day 1 the bot ships with slots that have only a Unicode fallback (no `id`), so every
screen is plain Unicode and nothing needs to change later. The owner (Premium) sends one
message with the chosen pack's emoji to the bot; the bot reads the custom_emoji entities
(UTF-16 offsets), verifies the ids with getCustomEmojiStickers and stores the map. A slot
the owner did not send stays unset - it is never filled with a guessed id.

Run:  py -3 examples/python/recipes/r71_icons_from_zero.py
"""
from __future__ import annotations

import _common as c
from icons.emoji_demo import VOCAB, fixture_set, sticker_lookup
from tgkit.icons import Eligibility, IconSystem, SendContext, ids_from_message, verify_ids
from tgkit.transport import FakeTransport

OWNER = 111111111
SLOTS = ["home", "add", "search", "settings", "done", "help"]


def home_screen(icons: IconSystem) -> dict:
    return {"chat_id": OWNER, "parse_mode": "HTML", "text": icons.title("home", "Your lists") + "\nNo lists yet.",
            "reply_markup": {"inline_keyboard": [[icons.button("New list", "add", style="primary", callback_data="add")],
                                                 [icons.button("Search", "search", callback_data="search"),
                                                  icons.button("Settings", "settings", callback_data="settings")],
                                                 [icons.button("Help", "help", callback_data="help")]]}}


def day_one_icons() -> IconSystem:
    """Slots with fallbacks only: the vocabulary's first Unicode choice, no ids."""
    return IconSystem({s: {"fallback": VOCAB[s]["unicode"][0]} for s in SLOTS}, vocabulary=VOCAB,
                      eligibility=Eligibility(owner_premium=True))


def owner_capture_message() -> dict:
    """What arrives when the owner sends 'home 🏠 add ➕ search 🔍 settings ⚙️ done ✅'
    picked from the pack (ids from the fixture pack; real ones come from the real update)."""
    st = {s["emoji"]: s["custom_emoji_id"] for s in fixture_set("demo_line_icons")["stickers"]}
    text, ents = "", []
    for word, emoji in (("home", "🏠"), ("add", "➕"), ("search", "🔍"), ("settings", "⚙️"), ("done", "✅")):
        text += f"{word} "
        ents.append({"type": "custom_emoji", "offset": len(text.encode("utf-16-le")) // 2,
                     "length": len(emoji.encode("utf-16-le")) // 2, "custom_emoji_id": st[emoji]})
        text += emoji + " "
    return {"message": {"message_id": 5, "chat": {"id": OWNER, "type": "private"}, "text": text.strip(), "entities": ents}}


def run():
    t = FakeTransport().script("getCustomEmojiStickers", sticker_lookup(["demo_line_icons"]))
    icons = day_one_icons()
    icons.send(t, "sendMessage", home_screen(icons), SendContext("private"))         # day 1: Unicode
    captured = ids_from_message(owner_capture_message(), VOCAB)
    found, missing = verify_ids(t, [x["id"] for x in captured])
    upgraded = dict(icons.icons)
    for x in captured:
        s = found.get(x["id"])
        if s and x["suggested_slot"] in upgraded:
            upgraded[x["suggested_slot"]] = {"id": x["id"], "fallback": s["emoji"], "set": s["set_name"],
                                             "animated": bool(s["is_animated"] or s["is_video"])}
    icons2 = IconSystem(upgraded, vocabulary=VOCAB, eligibility=icons.eligibility)
    icons2.send(t, "sendMessage", home_screen(icons2), SendContext("private"))       # after capture
    return t, captured, missing, icons2


def main() -> None:
    t, captured, missing, icons = run()
    c.dump(t, "Icons from zero (capture path)")
    first = t.params_of("sendMessage")[0]
    c.check("icon_custom_emoji_id" not in str(first) and first["reply_markup"]["inline_keyboard"][0][0]["text"] == "➕ New list",
            "day 1: no ids at all -> Unicode fallbacks, no placeholder ids")
    c.check([x["emoji"] for x in captured] == ["🏠", "➕", "🔍", "⚙️", "✅"] and not missing,
            "ids read from custom_emoji entities with UTF-16 offsets and verified")
    c.check(t.params_of("getCustomEmojiStickers")[0]["custom_emoji_ids"] == [x["id"] for x in captured],
            "verification is one getCustomEmojiStickers call (<= 200 ids)")
    second = t.params_of("sendMessage")[1]["reply_markup"]["inline_keyboard"]
    c.check(second[0][0].get("icon_custom_emoji_id") and second[0][0]["text"] == "New list", "captured slots switch to icons")
    c.check("id" not in icons.icons["help"] and second[2][0] == {"text": "Help", "callback_data": "help"},
            "'help' was not captured: it stays unset (never a guessed id) and goes label-only, not a Unicode look-alike")


if __name__ == "__main__":
    main()
