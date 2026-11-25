# 76 — The bot builds its own custom emoji pack and uses it

Registry rows: none of its own. Verified 2026-11-25 against the Bot API 10.5 catalog (snapshot 2026-11-22).
Labels: **API** = catalog text (`tgui.py lookup show <Symbol>`), **Official** = another core.telegram.org page,
**Heuristic** = design rule of this skill, **Unverified** = the sources do not say. Background:
`references/custom-emoji.md#getting-a-real-custom_emoji_id--never-invent-one`,
`references/emoji-packs.md#adding-your-own-or-a-purchased-pack`.

1. **Request and visible result.** “Make an emoji pack of our own for the bot's icons, from the PNGs our designer sent.”
   — A custom emoji set `pizza_icons_by_pizzaplace_bot` owned by the designer (a `user_id`) with three icons (home,
   cart, done) and a thumbnail; the bot's cards then start their lines with those icons.
2. **Why these methods.** The bot creates and fills the set itself instead of borrowing a public one:
   `createNewStickerSet` with `sticker_type` `custom_emoji` (6.2) and `needs_repainting` for solid-colour icons that
   take the text colour (6.6), `uploadStickerFile`, `addStickerToSet`, `setCustomEmojiStickerSetThumbnail` (6.6),
   and `getStickerSet` to read the ids back. Per-method notes: `tgui.py lookup card createNewStickerSet`.
3. **Requirements.** The owner's `user_id`. The set name ends in `_by_<bot_username>`, letters, digits and
   underscores only, begins with a letter, no consecutive underscores, 1-64 characters (**API**). 1-50 initial
   stickers; an emoji set holds up to 200 (**API**). Static emoji images are exactly 100x100 px, PNG or WEBP
   (**Official**, https://core.telegram.org/stickers). Using the icons in text is a separate rule: Fragment
   usernames, or owner Premium in messages the bot sends directly to private, group and supergroup chats
   (**Official**, Bot API formatting options; recipe 73). **Unverified:** whether the owner must have started the
   bot, and any other condition on creating a set.
4. **Payload.** `examples/payloads/r76-own-emoji-pack.json`; every method on its own:
   `examples/payloads/api-stickers.json`.
5. **Code.** `examples/python/recipes/r76_own_emoji_pack.py` (`valid_set_name`, `emoji_png_ok`, `create_pack`,
   `add_icon`, `run`), `examples/python/tgkit/icons.py` (`resolve_icon_map`, `IconSystem`).
6. **Sequence and state.** Validate the name and each image → `uploadStickerFile` per image (`sticker_format`
   `static`) → `createNewStickerSet` with the first icon → `addStickerToSet`, one call per further icon →
   `getStickerSet` → keep per slot `custom_emoji_id`, `emoji` (the Unicode fallback) and `file_id` →
   `setCustomEmojiStickerSetThumbnail` with one of those `custom_emoji_id` values → messages with
   `<tg-emoji emoji-id="…">fallback</tg-emoji>`. `createNewStickerSet` returns only `True` (**API**), so no id is
   taken from a request or an upload.
7. **Result.** Mock-up: `[home icon] Pizza place / [cart icon] Cart: 2 pizzas / [done icon] Order confirmed`. A bot
   without a route sends the same card with 🏠 🛒 ✅.
8. **Typical mistake, limits, alternative.** A name without the suffix, with a double underscore or starting with a
   digit breaks the documented rules: validate before the call. A `file_id` is not a `custom_emoji_id`. After a lost
   answer on create, read the set before creating it again (**Heuristic**; the error for a missing set is
   **Unverified**, so a failed read goes to the operator). A full set (200) is refused before `addStickerToSet`; an
   identical sticker added twice leaves the set unchanged (**API**). Where a custom emoji cannot be displayed
   the fallback `emoji` is shown (**Official**). For users, the stickers page says everyone can create custom
   emoji while adding and using custom sets is currently a Telegram Premium feature (**Official**). Alternative: the
   @Stickers mini app creates and manages emoji packs without code (**Official**); an existing public pack is
   recipes 70 and 71. The recipe never calls `deleteStickerSet`.
9. **Run and verify.** `py -3 examples/python/recipes/r76_own_emoji_pack.py` ·
   `py -3 examples/python/icons/export_emoji_payloads.py --check` ·
   `py -3 scripts/validate_payload.py examples/payloads/r76-own-emoji-pack.json` · tests in
   `tests/test_emoji_tools.py`. Evidence: offline contract; synthetic ids (leading 0), no live bot.
10. **Adapt.** Keep the slot map in one file and rebuild it from `getStickerSet` after every change, never by hand.
    Add icons later with `add_icon`; rename with `setStickerSetTitle`. Related: 70, 71, 73, 75.
