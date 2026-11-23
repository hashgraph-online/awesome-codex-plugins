# Emoji packs: choosing, resolving and applying a premium icon family

> Status labels: **API** = Bot API requirement, **Official** = recommendation in Telegram's
> docs, **Heuristic** = design rule of this skill. Checked 2026-11-15 against Bot API 10.4
> (2026-11-09, the latest version on that date). Tools: `scripts/emoji_packs.py`,
> `scripts/audit_icons.py`, `examples/python/tgkit/icons.py`. Data: `data/emoji/slots.json`
> (240 slots), `data/emoji/packs.json` (curated public sets, metadata only).
> Recipes: 70–75 (`recipes/70-restyle-to-premium.md` … `recipes/75-migrate-pack.md`).

## The agent's decision path (follow it unprompted)

Use it whenever you build or restyle a bot, or compose a post, and icons/emoji are involved.

1. **Eligibility — one precise question or a config read.** Look for config first
   (`TG_FRAGMENT_USERNAMES`, `TG_OWNER_PREMIUM` or similar). If absent, ask exactly:
   *"Does this bot have extra usernames bought on Fragment, or does the bot's owner have
   Telegram Premium? And will it post to channels?"* Map the answer to
   `Eligibility(fragment_usernames=…, owner_premium=…)` (**API** rule: `custom-emoji.md`).
   Neither → stop here, use Unicode with `visual-language.md` discipline, say why.
2. **Existing icon map?** Search the project for `icon_custom_emoji_id`, `tg-emoji`,
   `tg://emoji`, `custom_emoji`, an `icon-map.json`, a bot-ui `emoji/library.json` (the user's
   own packs and icon map from the Studio; read it with `bot-ui emoji brief`) or an
   `IconSystem(`. If one exists, run
   `py -3 scripts/audit_icons.py MAP` and keep its family unless the user asks to change it
   (then recipe 75).
3. **Slots.** Derive the needed slots from the existing texts and keyboards:
   `py -3 scripts/emoji_packs.py suggest --from <payload-or-texts>` (it maps every Unicode
   emoji to a slot of `data/emoji/slots.json`), or list them by meaning for a new bot. Keep
   8–15 button slots (**Heuristic**).
4. **Propose ONE family by archetype and tone.** `suggest --archetype monitoring --tone
   native` ranks `data/emoji/packs.json`. Without saved `getStickerSet` results the ranking
   is metadata-only and says so. Present the top pick with its link and one alternative;
   the user looks at both in a chat (light and dark theme) before you resolve.
5. **Resolve real ids.** `TELEGRAM_LIVE=1 TELEGRAM_TEST_BOT_TOKEN=… py -3 scripts/emoji_packs.py
   resolve --set <primary> --set <sibling> --slots a,b,c --out icon-map.json` (read-only
   `getStickerSet`). Offline: `--sticker-set saved.json`. No token available → give the user
   the capture path (below) and ship with fallbacks only. **Never invent an id.**
6. **Apply through `IconSystem`.** Handlers ask for slots (`icons.button("Cart", "cart")`,
   `icons.title(...)`, `icons.rich(...)`); every request passes `IconSystem.send(transport,
   method, params, SendContext(...))` or `prepare(...)`. For an existing bot that already
   writes Unicode emoji, `prepare` converts them (`apply`); nothing else changes.
7. **Audit.** `audit_icons.py icon-map.json` (one family, static vs animated, adaptive vs
   fixed colour, no shared ids, fallbacks) and `audit_icons.py --payload FILE` (no double
   icons, no mixed keyboards, density).
8. **Fallback verified.** Run the same screens with `Eligibility()` (nothing) and check they
   read correctly with Unicode only; check the channel copy when the bot posts to channels.

## Choosing a pack

| Signal | Prefer | Avoid |
|---|---|---|
| Utility, monitoring, finance, support | static app-style glyphs (`tgmacicons` + `tgiosicons`, `TgAndroidIcons`, `UnigramIcons` + `EmojiStatus`) | animated sets on buttons |
| AI assistant | the bot's family for UI; `AIActions` only inside `<tg-thinking>` (**Official**: InputRichBlockThinking links it) | AIActions as the general family |
| Games, playful bots | one animated set for a hero moment (`DMJUnigramAnimationEmoji`, `UI_icons`) | animation on every control |
| Channel / editorial | a set whose marks fit headlines and sections (`NewsEmoji`) — needs the Fragment route | bot keyboards from an editorial set |
| Coins next to tickers | `cryptoicons` as inline content marks | logos as UI icons (trademarks) |

Rules (**Heuristic**): one family per bot; siblings (same author or explicitly paired sets)
may fill gaps; static on buttons; adaptive (`needs_repainting`) and fixed-colour icons do
not mix; an uncovered slot is label-only, never a look-alike from another family.

**API facts used for the choice:** `Sticker.is_animated`, `is_video` (animation),
`needs_repainting` ("must be repainted to a text color in messages" — adaptive), `emoji`
(the Unicode equivalent and recommended fallback), `set_name`, `custom_emoji_id`.

## The catalog

`data/emoji/packs.json` lists only sets whose existence was checked on 2026-11-15 by opening
`https://t.me/addemoji/<name>` (an existing set shows "Add emoji set <title>"). It carries no
ids, and `animation` / `adaptive` stay `null` until a resolve reads the stickers; style words
come from the set titles. Re-check before relying on a set — authors can rename or remove
sets, which `emoji_packs.py verify` detects.

## Adding your own or a purchased pack

1. Get the set's short name (the part after `t.me/addemoji/`). A set you or your designer
   created with @Stickers works the same way as a public one.
2. Resolve it: `emoji_packs.py resolve --set <name> --slots …` (or save the `getStickerSet`
   JSON once and resolve offline). Check `uncovered`, `conflicts` and `per_set`.
3. Optional: add an entry to your project's copy of `packs.json` (same fields) so `suggest`
   knows its archetypes and tone.
4. If the pack came from an author or marketplace, keep their licence terms with the map.
5. In a bot-ui project the user can do steps 1-2 without the CLI: the Studio's Emoji page imports
   a pack from its link, shows every emoji, and saves the chosen meanings to `emoji/library.json`.

## Capture path (no token, or the owner picks emoji by hand)

`py -3 scripts/emoji_packs.py capture` prints the steps and a stdlib handler: the owner sends
one message with the chosen emoji to the bot; the bot reads `message.entities` of type
`custom_emoji` (offsets in UTF-16 code units, **API**) and stores `custom_emoji_id`; then
`verify` confirms each id with `getCustomEmojiStickers` (≤ 200 per call, **API**). With a
saved update: `capture --update saved.json` suggests a slot per emoji. Recipe 71.

## Migrating to another pack

Handlers name slots, so a migration is data: resolve the new family for the slots in use,
require full coverage (or decide label-only on purpose), `verify`, audit, swap the map.
Recipe 75.

## Widgets and custom emoji

**Official** (Telegram Widgets guide, checked 2026-11-15): widget HTML loads images only as
`data:` URLs or inline SVG; external images are never loaded; colour emoji render as text.
The guide documents no way to show a custom emoji by id, so **HTML widgets cannot use
`custom_emoji_id`**. To keep one visual family:

- put the widget's icons in inline SVG drawn in the same style (stroke weight, corner
  radius, fill) as the chosen pack, coloured with `currentColor` / theme variables;
- keep the custom emoji on the message's caption and buttons around the widget;
- never paste sticker image files into a widget (licensing, below).

```html
<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="none"
     stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M5 12l4 4 10-10"/></svg>
```

## Licensing

Custom emoji sets belong to their authors. Using a set by id in your bot's messages is the
use Telegram built; the artwork stays on Telegram's servers. This skill references public
sets by name and resolves ids at the user's request; it never bundles, downloads or
redistributes sticker files. Credit the author when a set defines your bot's look; ask
before building a commercial brand on someone's set; brand logos remain trademarks of their
owners. This is a practical position, not legal advice.

## Checklist

- [ ] Eligibility route named (Fragment / owner Premium / neither) and channels addressed.
- [ ] One family; siblings only for gaps; uncovered slots label-only.
- [ ] Every id from `getStickerSet`, `getCustomEmojiStickers` or a received entity.
- [ ] `audit_icons.py` clean on the map and on a payload of real screens.
- [ ] Screens checked with icons off.
