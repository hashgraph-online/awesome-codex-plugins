# 71 — Icons for a new bot from zero (no ids yet, capture path)

Registry rows: none of its own — `MessageEntity.custom_emoji_id`, `getCustomEmojiStickers`,
9.4 button icons. Verified 2026-11-15, Bot API 10.4. Background: `references/emoji-packs.md`
(capture), `references/custom-emoji.md`.

1. **Request and visible result.** “New bot; we want premium icons but have no ids.” — Day 1
   ships with Unicode fallbacks; after the owner sends one message with the chosen emoji,
   the captured slots switch to custom icons; slots not captured show their label only.
2. **Why the new features.** Received messages expose `custom_emoji` entities with
   `custom_emoji_id`; `getCustomEmojiStickers` confirms them (≤ 200 ids per call). No ids
   have to be typed or guessed.
3. **Requirements.** The owner needs Premium to send custom emoji; the bot needs an
   eligibility route to use them. Offsets are UTF-16 code units (API).
4. **Payload.** `examples/payloads/r71-icons-from-zero.json`. Key part:
   ```json
   {"method": "getCustomEmojiStickers", "params": {"custom_emoji_ids": ["<captured id>", "…"]}}
   ```
5. **Code.** `examples/python/recipes/r71_icons_from_zero.py` (`day_one_icons`,
   `owner_capture_message`, `run`), `tgkit/icons.py` (`ids_from_message`, `verify_ids`),
   `scripts/emoji_packs.py capture [--update saved.json]`.
6. **Sequence and state.** slots with `fallback` only → screens in Unicode → owner sends the
   emoji → `ids_from_message` → `verify_ids` → store `{id, fallback: sticker.emoji, set}`
   per captured slot → new `IconSystem` map; uncovered slots keep no `id`.
7. **Result.** Mock-up: day 1 `➕ New list`; after capture `[icon] New list`, and `Help`
   (label only — the help emoji was not captured).
8. **Typical mistake, limits, alternative.** Filling the missing slot with an id that "looks
   right"; computing offsets in Python characters; leaving a Unicode emoji next to custom
   icons on one keyboard. Alternative: resolve the whole pack with `getStickerSet(name)`.
9. **Run and verify.** `py -3 examples/python/recipes/r71_icons_from_zero.py` ·
   `py -3 scripts/emoji_packs.py capture` · tests in `tests/test_emoji_icons.py`. Evidence:
   offline contract; synthetic ids.
10. **Adapt.** Add a hidden owner-only command that logs `ids_from_message(update)`; persist
    the map; run `emoji_packs.py verify` on deploy. Related: 70, 74.
