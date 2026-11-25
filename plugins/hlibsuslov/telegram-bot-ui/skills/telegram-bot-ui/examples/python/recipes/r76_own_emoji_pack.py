"""R76 - The bot builds its own custom emoji pack, then uses it.

The owner (a user_id) hands the bot three icon images. The bot checks the set name and the images,
uploads each image (uploadStickerFile), creates a custom emoji set with the first
(createNewStickerSet, sticker_type "custom_emoji"), adds the others (addStickerToSet) and READS THE SET
BACK with getStickerSet: createNewStickerSet answers only True, so every custom_emoji_id and the Unicode
fallback (Sticker.emoji) come from that read. The thumbnail is set from one of those ids
(setCustomEmojiStickerSetThumbnail) and the ids go into messages. Using custom emoji in text is a
separate eligibility question: a bot without a route sends the Unicode fallback.

Run:  py -3 examples/python/recipes/r76_own_emoji_pack.py
"""
from __future__ import annotations

import re
import struct

import _common as c
from icons.emoji_demo import VOCAB
from tgkit.errors import OutcomeUnknown
from tgkit.icons import Eligibility, IconSystem, SendContext, resolve_icon_map
from tgkit.transport import FakeTransport

OWNER = 111111111                   # user_id of the set owner: the person who made the icons
BOT_USERNAME = "pizzaplace_bot"
TITLE = "Pizza place icons"         # 1-64 characters
ICONS = [("home", "🏠"), ("cart", "🛒"), ("done", "✅")]    # slot, Unicode emoji of the sticker
MAX_EMOJI_SET = 200                 # addStickerToSet: an emoji set holds up to 200 stickers
EMOJI_PX = 100                      # stickers page: emoji images are exactly 100x100 px (PNG or WEBP)


class PackFull(Exception):
    pass


def valid_set_name(name: str, bot_username: str) -> bool:
    """createNewStickerSet name: English letters, digits and underscores, begins with a letter, no
    consecutive underscores, ends in _by_<bot_username> (case insensitive), 1-64 characters."""
    return (re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", name) is not None and "__" not in name and len(name) <= 64
            and name.lower().endswith(f"_by_{bot_username.lower()}"))


def set_name(base: str, bot_username: str) -> str:
    name = f"{base}_by_{bot_username}"
    if not valid_set_name(name, bot_username):
        raise ValueError(f"not a valid sticker set name: {name!r}")
    return name


def png_header(width: int, height: int) -> bytes:
    """The first 24 bytes of a PNG (signature and IHDR size): enough for the size check offline."""
    return b"\x89PNG\r\n\x1a\n" + struct.pack(">I4sII", 13, b"IHDR", width, height)


def emoji_png_ok(data: bytes) -> bool:
    return data[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", data[16:24]) == (EMOJI_PX, EMOJI_PX)


def input_sticker(file_id: str, emoji: str) -> dict:
    return {"sticker": file_id, "format": "static", "emoji_list": [emoji]}


def _server_set(t: FakeTransport, name: str):
    """What getStickerSet answers for the set the calls so far built (synthetic ids: the 0 prefix is never real)."""
    def respond(method: str, params: dict) -> dict:
        stickers = []
        for m, p in t.calls:
            if p.get("name") != name or m not in ("createNewStickerSet", "addStickerToSet"):
                continue
            for item in p["stickers"] if m == "createNewStickerSet" else [p["sticker"]]:
                n = len(stickers) + 1
                stickers.append({"file_id": f"CAACAgIAAxkBAAEBpizzaOwn{n:04d}", "file_unique_id": f"AgADpizzaOwn{n:04d}",
                                 "type": "custom_emoji", "width": EMOJI_PX, "height": EMOJI_PX, "is_animated": False,
                                 "is_video": False, "emoji": item["emoji_list"][0], "set_name": name,
                                 "custom_emoji_id": f"03000000000000{n:02d}", "needs_repainting": True})
        return {"name": name, "title": TITLE, "sticker_type": "custom_emoji", "stickers": stickers}
    return respond


def create_pack(t: FakeTransport, name: str, file_id: str, emoji: str) -> None:
    """createNewStickerSet. If the answer is lost the set may exist: read it before creating again."""
    try:
        t.call("createNewStickerSet", {"user_id": OWNER, "name": name, "title": TITLE, "sticker_type": "custom_emoji",
                                       "needs_repainting": True, "stickers": [input_sticker(file_id, emoji)]})
    except OutcomeUnknown:
        t.call("getStickerSet", {"name": name})       # an error here is not guessed around: it reaches the operator


def add_icon(t: FakeTransport, name: str, file_id: str, emoji: str) -> None:
    """Add one more icon later: read the set first and refuse at the documented capacity."""
    if len(t.call("getStickerSet", {"name": name})["stickers"]) >= MAX_EMOJI_SET:
        raise PackFull(f"{name} already holds {MAX_EMOJI_SET} stickers")
    t.call("addStickerToSet", {"user_id": OWNER, "name": name, "sticker": input_sticker(file_id, emoji)})


def menu_card(icons: IconSystem) -> dict:
    return {"chat_id": OWNER, "parse_mode": "HTML",
            "text": icons.title("home", "Pizza place") + f"\n{icons.text('cart')} Cart: 2 pizzas"
                    f"\n{icons.text('done')} Order confirmed"}


def run(t: FakeTransport | None = None, *, owner_premium: bool = True):
    t = t or FakeTransport()
    name = set_name("pizza_icons", BOT_USERNAME)
    t.script("uploadStickerFile", *[{"file_id": f"BQACAgIAAxkBAAEBpizzaUp{n:03d}", "file_unique_id": f"AgADpizzaUp{n:03d}",
                                     "file_size": 1800} for n in range(1, len(ICONS) + 1)])
    t.script("getStickerSet", _server_set(t, name), _server_set(t, name))
    uploads = [t.call("uploadStickerFile", {"user_id": OWNER, "sticker": f"attach://{slot}_png",
                                            "sticker_format": "static"})["file_id"] for slot, _ in ICONS]
    create_pack(t, name, uploads[0], ICONS[0][1])
    for file_id, (_, emoji) in zip(uploads[1:], ICONS[1:]):
        t.call("addStickerToSet", {"user_id": OWNER, "name": name, "sticker": input_sticker(file_id, emoji)})
    read = t.call("getStickerSet", {"name": name})
    t.call("setCustomEmojiStickerSetThumbnail", {"name": name, "custom_emoji_id": read["stickers"][0]["custom_emoji_id"]})
    icon_map, report = resolve_icon_map([read], VOCAB, [slot for slot, _ in ICONS], family=name)
    icons = IconSystem(icon_map["icons"], vocabulary=VOCAB, eligibility=Eligibility(owner_premium=owner_premium))
    icons.send(t, "sendMessage", menu_card(icons), SendContext("private"))
    return t, read, icon_map, report


def _refused(base: str) -> bool:
    try:
        set_name(base, BOT_USERNAME)
    except ValueError:
        return True
    return False


def main() -> None:
    t, read, icon_map, report = run()
    c.dump(t, "Own custom emoji pack")
    name = set_name("pizza_icons", BOT_USERNAME)
    create = t.params_of("createNewStickerSet")[0]
    c.check(create["sticker_type"] == "custom_emoji" and create["name"] == name and len(create["stickers"]) == 1
            and len(t.params_of("addStickerToSet")) == len(ICONS) - 1,
            "one custom emoji set: the first icon creates it, the others are added")
    c.check(t.methods().index("getStickerSet") > t.methods().index("addStickerToSet") and report["coverage"] == 1.0,
            "the set is read back after the last add and covers every slot")
    ids = {s["custom_emoji_id"] for s in read["stickers"]}
    used = set(re.findall(r'emoji-id="(\d+)"', t.params_of("sendMessage")[0]["text"]))
    c.check(used == ids and used.isdisjoint(s["file_id"] for s in read["stickers"]),
            "messages use the custom_emoji_ids from getStickerSet, never a file_id or an id from a request")
    c.check(t.params_of("setCustomEmojiStickerSetThumbnail")[0]["custom_emoji_id"] in ids,
            "the thumbnail is one custom_emoji_id of the set")

    c.check(all(_refused(b) for b in ("1pizza", "pizza_", "pizza-icons", "x" * 60)) and not _refused("pizza_icons")
            and not valid_set_name("pizza_icons", BOT_USERNAME) and not valid_set_name("pizza_icons_by_otherbot", BOT_USERNAME)
            and valid_set_name("Pizza_Icons_by_PizzaPlace_Bot", BOT_USERNAME),
            "a name the catalog's rules forbid never reaches a request; the bot username suffix is case insensitive")
    c.check(emoji_png_ok(png_header(100, 100)) and not emoji_png_ok(png_header(512, 512)),
            "an emoji image that is not 100x100 px is refused before the upload")

    lost = FakeTransport().script("createNewStickerSet", "TIMEOUT")
    run(lost)
    c.check(lost.methods().count("createNewStickerSet") == 1
            and lost.methods().index("getStickerSet") == lost.methods().index("createNewStickerSet") + 1,
            "a lost answer on create: the set is read, not created a second time")

    text = run(owner_premium=False)[0].params_of("sendMessage")[0]["text"]
    c.check("<tg-emoji" not in text and "🛒" in text,
            "a bot without a route sends the Unicode fallback from Sticker.emoji: every icon of the message or none")

    full = FakeTransport()
    full.script("getStickerSet", {"name": name, "title": TITLE, "sticker_type": "custom_emoji",
                                  "stickers": [{"custom_emoji_id": f"{i:016d}"} for i in range(MAX_EMOJI_SET)]})
    try:
        add_icon(full, name, "BQACAgIAAxkBAAEBpizzaUp999", "➕")
    except PackFull:
        c.check("addStickerToSet" not in full.methods(), "a full emoji set (200 stickers) is refused before addStickerToSet")
    else:
        raise AssertionError("a full set must be refused")


if __name__ == "__main__":
    main()
