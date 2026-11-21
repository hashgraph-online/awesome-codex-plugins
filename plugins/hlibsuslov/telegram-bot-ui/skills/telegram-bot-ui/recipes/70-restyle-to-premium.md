# 70 — Restyle an existing bot from Unicode emoji to one premium pack

Registry rows: none of its own — Bot API 9.4 `icon_custom_emoji_id`, 6.2 custom emoji
entities. Verified 2026-11-15, Bot API 10.4. Background: `references/emoji-packs.md`,
`references/custom-emoji.md`, `references/visual-language.md`.

1. **Request and visible result.** “Make our bot look premium — same screens, nicer icons.”
   — Every keyboard label that started with a Unicode emoji now shows a custom icon from one
   family and no emoji in the label; screen titles use the same icon via `<tg-emoji>`; code
   blocks and links are untouched.
2. **Why the new features.** Since 9.4 buttons carry `icon_custom_emoji_id`, and since 9.4
   the owner-Premium route allows custom emoji in messages the bot sends directly to
   private/group/supergroup chats. Before: Unicode that renders differently per platform.
3. **Requirements.** Fragment usernames, or owner Premium for private/group/supergroup
   messages sent directly by the bot (API). Ids come only from `getStickerSet` /
   `getCustomEmojiStickers` / received entities. Fallback: the original Unicode screens.
4. **Payload.** `examples/payloads/r70-restyle-to-premium.json`. Key part:
   ```json
   {"text": "Settings", "callback_data": "settings", "icon_custom_emoji_id": "<id from getStickerSet>"}
   ```
5. **Code.** `examples/python/recipes/r70_restyle_to_premium.py` (`SCREENS`, `run`),
   `examples/python/tgkit/icons.py` (`slots_in`, `resolve_icon_map`, `IconSystem.send`),
   `scripts/emoji_packs.py suggest|resolve|apply`.
6. **Sequence and state.** `slots_in(screens)` → `suggest` a family → `resolve` primary set +
   sibling → store the map → every send goes through `IconSystem.send(..., SendContext)`,
   which applies the map to the whole request or strips it (all-or-nothing per message).
7. **Result.** Mock-up (not a client screenshot): `[icon] Main menu / [icon]Wallets
   [icon]Search / [icon]Notifications [icon]Settings / [icon]Help`.
8. **Typical mistake, limits, alternative.** Keeping `💼` in a label that also has an icon
   (double icon); mixing two families to fill gaps; replacing emoji inside `<code>` or links
   (not allowed by the API nesting rules); `parse_mode: Markdown` (legacy cannot express
   custom emoji). Alternative: stay with Unicode and apply `visual-language.md` discipline.
9. **Run and verify.** `py -3 examples/python/recipes/r70_restyle_to_premium.py` ·
   `py -3 scripts/audit_icons.py --payload examples/payloads/r70-restyle-to-premium.json` ·
   tests in `tests/test_emoji_icons.py`. Evidence: offline contract with synthetic fixture
   ids; not rendered in Telegram.
10. **Adapt.** Put `IconSystem.send` (or `prepare`) at the single place your bot calls the
    Bot API; resolve a real pack with `TELEGRAM_LIVE=1 … emoji_packs.py resolve --set NAME`;
    keep the map in config. Related: 71, 75, `recipes/09-tracker-bot.md`.
