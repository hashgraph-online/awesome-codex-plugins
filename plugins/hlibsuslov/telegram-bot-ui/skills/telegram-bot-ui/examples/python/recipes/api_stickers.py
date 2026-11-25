"""Per-method request examples for the Bot API domain `stickers`, recorded offline (Bot API 10.5).

One small function per method makes the call the agent note points at; the values are synthetic (a
made-up owner, bot username, set names and ids). `run_all()` returns the FakeTransport whose `calls`
`export_payloads.py --only api-stickers` writes to examples/payloads/api-stickers.json. A call that
depends on an earlier answer reads it from the scripted result (uploadStickerFile returns a File whose
file_id createNewStickerSet takes; getStickerSet returns the file_id and custom_emoji_id the edit
methods take). Destructive calls (replaceStickerInSet, deleteStickerFromSet, deleteStickerSet) are
recorded requests, never sent. A new file is shown as "attach://<part>"; its bytes travel as a
multipart part (references/media-and-files.md#uploading).

Run:  py -3 examples/python/recipes/api_stickers.py
"""
from __future__ import annotations

import _common as c
from tgkit.transport import FakeTransport

STATUS = "production (destructive calls are recorded requests, never sent)"
CONTEXT = "any chat for sendSticker; sticker-set methods take no chat, only the set owner's user_id"
STEP_CONTEXT = {
    "sendSticker": "any chat the bot can send to; the sticker is a file_id the bot already has",
    "getStickerSet": "name is the set's short name, not its title",
    "getCustomEmojiStickers": "at most 200 custom emoji ids per call",
    "uploadStickerFile": "owner user_id; sticker_format is static, animated or video",
    "createNewStickerSet": "owner user_id; name ends in _by_<bot_username>; 1-50 initial stickers; "
                           "sticker_type custom_emoji; needs_repainting only for custom emoji sets",
    "addStickerToSet": "set created by the bot; an emoji set holds up to 200 stickers, other sets up to 120",
    "setStickerPositionInSet": "sticker of a set created by the bot; position is zero-based",
    "deleteStickerFromSet": "sticker of a set created by the bot; destructive, recorded not sent",
    "replaceStickerInSet": "owner user_id; old_sticker is a file_id read from getStickerSet; "
                           "destructive, recorded not sent",
    "setStickerEmojiList": "regular or custom emoji sticker of a set created by the bot; 1-20 emoji",
    "setStickerKeywords": "regular or custom emoji sticker of a set created by the bot; "
                          "0-20 keywords, 64 characters in total",
    "setStickerMaskPosition": "mask sticker of a set created by the bot",
    "setStickerSetTitle": "title is 1-64 characters",
    "setStickerSetThumbnail": "regular or mask set; owner user_id; format matches the stickers' format",
    "setCustomEmojiStickerSetThumbnail": "custom emoji set; custom_emoji_id of a sticker in that set",
    "deleteStickerSet": "set created by the bot; destructive, recorded not sent",
}

OWNER = 111111111                       # user_id of the sticker set owner
CHAT = 111111111
BOT = "pizzaplace_bot"
EMOJI_SET = f"pizza_icons_by_{BOT}"     # custom emoji set (name ends in _by_<bot_username>)
STICKER_SET = f"pizza_stickers_by_{BOT}"
MASK_FILE_ID = "CAACAgIAAxkBAAEBpizzaMask0001"


def _sticker(n: int, emoji: str) -> dict:
    """A custom emoji Sticker as getStickerSet returns it (synthetic ids; the 0 prefix is never real)."""
    return {"file_id": f"CAACAgIAAxkBAAEBpizzaIcon{n:04d}", "file_unique_id": f"AgADpizza{n:04d}",
            "type": "custom_emoji", "width": 100, "height": 100, "is_animated": False, "is_video": False,
            "emoji": emoji, "set_name": EMOJI_SET, "custom_emoji_id": f"020000000000000{n}",
            "needs_repainting": True, "file_size": 2048}


EMOJI_SET_RESULT = {"name": EMOJI_SET, "title": "Pizza place icons", "sticker_type": "custom_emoji",
                    "stickers": [_sticker(1, "🏠"), _sticker(2, "🛒")]}


def upload_sticker_file(t: FakeTransport) -> str:
    t.script("uploadStickerFile", {"file_id": "BQACAgIAAxkBAAEBpizzaUpload01", "file_unique_id": "AgADpizzaUp01",
                                   "file_size": 2048})
    uploaded = t.call("uploadStickerFile", {"user_id": OWNER, "sticker": "attach://sticker",
                                            "sticker_format": "static"})
    return uploaded["file_id"]


def create_new_sticker_set(t: FakeTransport, file_id: str) -> None:
    t.call("createNewStickerSet", {
        "user_id": OWNER, "name": EMOJI_SET, "title": "Pizza place icons", "sticker_type": "custom_emoji",
        "needs_repainting": True,
        "stickers": [{"sticker": file_id, "format": "static", "emoji_list": ["🏠"], "keywords": ["home", "pizza"]}]})


def add_sticker_to_set(t: FakeTransport) -> None:
    t.call("addStickerToSet", {"user_id": OWNER, "name": EMOJI_SET,
                               "sticker": {"sticker": "attach://cart_icon", "format": "static", "emoji_list": ["🛒"]}})


def get_sticker_set(t: FakeTransport) -> dict:
    t.script("getStickerSet", EMOJI_SET_RESULT)
    return t.call("getStickerSet", {"name": EMOJI_SET})


def get_custom_emoji_stickers(t: FakeTransport, read: dict) -> None:
    t.script("getCustomEmojiStickers", read["stickers"])
    t.call("getCustomEmojiStickers", {"custom_emoji_ids": [s["custom_emoji_id"] for s in read["stickers"]]})


def set_sticker_position_in_set(t: FakeTransport, read: dict) -> None:
    t.call("setStickerPositionInSet", {"sticker": read["stickers"][1]["file_id"], "position": 0})


def set_sticker_emoji_list(t: FakeTransport, read: dict) -> None:
    t.call("setStickerEmojiList", {"sticker": read["stickers"][0]["file_id"], "emoji_list": ["🏠", "🍕"]})


def set_sticker_keywords(t: FakeTransport, read: dict) -> None:
    t.call("setStickerKeywords", {"sticker": read["stickers"][0]["file_id"], "keywords": ["home", "pizza", "menu"]})


def set_sticker_set_title(t: FakeTransport) -> None:
    t.call("setStickerSetTitle", {"name": EMOJI_SET, "title": "Pizza place icons v2"})


def set_custom_emoji_sticker_set_thumbnail(t: FakeTransport, read: dict) -> None:
    t.call("setCustomEmojiStickerSetThumbnail",
           {"name": EMOJI_SET, "custom_emoji_id": read["stickers"][0]["custom_emoji_id"]})


def send_sticker(t: FakeTransport) -> None:
    t.call("sendSticker", {"chat_id": CHAT, "sticker": "CAACAgIAAxkBAAEBpizzaSticker01"})


def replace_sticker_in_set(t: FakeTransport) -> None:
    t.call("replaceStickerInSet", {
        "user_id": OWNER, "name": STICKER_SET, "old_sticker": "CAACAgIAAxkBAAEBpizzaSticker01",
        "sticker": {"sticker": "attach://pizza_slice", "format": "static", "emoji_list": ["🍕"]}})


def delete_sticker_from_set(t: FakeTransport) -> None:
    t.call("deleteStickerFromSet", {"sticker": "CAACAgIAAxkBAAEBpizzaSticker02"})


def set_sticker_mask_position(t: FakeTransport) -> None:
    t.call("setStickerMaskPosition", {"sticker": MASK_FILE_ID,
                                      "mask_position": {"point": "forehead", "x_shift": 0.0, "y_shift": -0.2,
                                                        "scale": 1.5}})


def set_sticker_set_thumbnail(t: FakeTransport) -> None:
    t.call("setStickerSetThumbnail", {"name": STICKER_SET, "user_id": OWNER, "thumbnail": "attach://thumbnail",
                                      "format": "static"})


def delete_sticker_set(t: FakeTransport) -> None:
    t.call("deleteStickerSet", {"name": STICKER_SET})


def run_all() -> FakeTransport:
    t = FakeTransport()
    file_id = upload_sticker_file(t)
    create_new_sticker_set(t, file_id)
    add_sticker_to_set(t)
    read = get_sticker_set(t)
    get_custom_emoji_stickers(t, read)
    set_sticker_position_in_set(t, read)
    set_sticker_emoji_list(t, read)
    set_sticker_keywords(t, read)
    set_sticker_set_title(t)
    set_custom_emoji_sticker_set_thumbnail(t, read)
    send_sticker(t)
    replace_sticker_in_set(t)
    delete_sticker_from_set(t)
    set_sticker_mask_position(t)
    set_sticker_set_thumbnail(t)
    delete_sticker_set(t)
    return t


def main() -> None:
    t = run_all()
    c.dump(t, "Bot API stickers: one request per method")
    c.check(sorted(t.methods()) == sorted(STEP_CONTEXT), "every method of the domain is recorded exactly once")
    c.check(t.params_of("createNewStickerSet")[0]["stickers"][0]["sticker"]
            == "BQACAgIAAxkBAAEBpizzaUpload01", "createNewStickerSet takes the file_id uploadStickerFile returned")
    c.check(all(p["name"].endswith(f"_by_{BOT}") for p in t.params_of("createNewStickerSet")),
            "a set created by the bot ends in _by_<bot_username>")


if __name__ == "__main__":
    main()
