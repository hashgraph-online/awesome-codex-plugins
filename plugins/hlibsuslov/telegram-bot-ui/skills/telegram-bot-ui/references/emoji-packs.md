---
summary: "Choosing, resolving and applying a premium emoji pack: decision path, catalog, own packs, capture path, migration, widgets, licensing; read when restyling a bot or post with an icon family."
verified: "2026-11-25"
bot_api: "10.4"
---

# Emoji packs: choosing, resolving and applying a premium icon family

> Status labels: **API** = Bot API requirement, **Official** = recommendation in Telegram's
> docs, **Heuristic** = design rule of this skill. Checked 2026-11-15 against Bot API 10.4
> (2026-11-09, the latest version on that date). Tools: `scripts/emoji_packs.py`,
> `scripts/audit_icons.py`, `examples/python/tgkit/icons.py`. Data: `data/emoji/slots.json`
> (240 slots), `data/emoji/packs.json` (curated public sets, metadata only).
> Recipes: 70–75 (`recipes/70-restyle-to-premium.md` … `recipes/75-migrate-pack.md`).

## Contents

- [The agent's decision path (follow it unprompted)](#the-agents-decision-path-follow-it-unprompted)
- [The icon plan: packs and button icons, stage by stage](#the-icon-plan-packs-and-button-icons-stage-by-stage)
- [Choosing a pack](#choosing-a-pack)
- [The catalog](#the-catalog)
- [The library contract, offline export and profile picking](#the-library-contract-offline-export-and-profile-picking)
- [Adding your own or a purchased pack](#adding-your-own-or-a-purchased-pack)
- [Capture path (no token, or the owner picks emoji by hand)](#capture-path-no-token-or-the-owner-picks-emoji-by-hand)
- [Migrating to another pack](#migrating-to-another-pack)
- [Widgets and custom emoji](#widgets-and-custom-emoji)
- [Licensing](#licensing)
- [Checklist](#checklist)

## The agent's decision path (follow it unprompted)

Use it whenever you build or restyle a bot, or compose a post, and icons/emoji are involved.
A logo, clip, GIF or banner to show in a post or welcome is a different job: offer an emoji mosaic
(`references/emoji-mosaic.md`), not an icon family.

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
4. **Propose ONE family with real coverage.** For buttons and titles you choose yourself, run the icon
   plan (next section): it does this step per slot, with alternatives, scores and a record. For a
   quick whole-pack ranking, when the network is allowed:
   `py -3 scripts/emoji_packs.py library pick --needs home,back,settings,… --out pick.json`
   (MCP: `emoji_pick_family`). It searches the telegram-bot-ui emoji library
   (telegram-bot-ui.hlixli.com/emoji, ~490 packs with real ids; only the slot emoji and pack
   names are sent, no token), fetches the top candidates in full and ranks whole packs by
   slots covered by their own fallback emoji, then theme-adaptive share (`--theme both`),
   then static share (`--motion static` on buttons). Its `map` is an icon map from ONE pack
   with `missing` slots listed: keep those label-only. `library search <words or emoji>`
   finds a single icon or a pack by meaning. Offline or `BOT_UI_EMOJI_RESOLVER=off`:
   `suggest --archetype monitoring --tone native` ranks the small curated
   `data/emoji/packs.json` by metadata only and says so. Present the top pick with its link
   and one alternative; the user looks at both in a chat (light and dark theme) before you
   apply them.
   **Pick by tags** when the look matters as much as coverage: every pack and emoji of the
   library carries faceted tags with a confidence (style, colour, palette, theme fit, motion,
   topic, mood, interface role, bot category, compatible packs), built from Telegram data,
   pixel measurement and the pictures' descriptions (taxonomy: `/api/emoji-facets`).
   `emoji_packs.py library facets --use support --style outline --theme both` ranks packs by
   tags; `library pick --needs … --profile <style profile>` (or `--style/--color/--mood/--topic/
   --use`) adds the brief to coverage; `--require motion:static` is a hard filter, while `--motion
   static` and `--theme` are preferences; `library pick --profile <style profile>` without `--needs`
   ranks whole packs for the bot and explains each in one line (next section). MCP:
   `emoji_rank_by_tags`, `emoji_pick_family`. Measured
   accuracy (blind gold set, held-out half, 2026-11-25): topic 0.95, theme fit 0.80, interface role
   0.89, colour 0.86 hit rate; **style is the weakest tag (about 0.35 recall)**, so show the user
   the pack before relying on a style tag. Library search takes the same filters:
   `settings style:outline fit:adaptive`.
5. **Resolve real ids** (when the library pick was not used, or to re-check its map against
   Telegram). `TELEGRAM_LIVE=1 TELEGRAM_TEST_BOT_TOKEN=… py -3 scripts/emoji_packs.py
   resolve --set <primary> --set <sibling> --slots a,b,c --out icon-map.json` (read-only
   `getStickerSet`). Offline: `--sticker-set saved.json`. No token available → give the user
   the capture path (below) and ship with fallbacks only. **Never invent an id.**
6. **Apply through `IconSystem`.** Handlers ask for slots (`icons.button("Cart", "cart")`,
   `icons.title(...)`, `icons.rich(...)`); every request passes `IconSystem.send(transport,
   method, params, SendContext(...))` or `prepare(...)`. For an existing bot that already
   writes Unicode emoji, `prepare` converts them (`apply`); nothing else changes.
7. **Double check, then audit.** In a bot-ui project `bot-ui emoji review --out icon-review.html`:
   look at each button icon next to its label (meaning, static, family; red rows are
   `ICON_MEANING_MISMATCH` or animated). A slot the main pack cannot say well takes a static icon of
   the same style from another pack or stays label-only, never a wrong meaning from the main pack.
   `audit_icons.py icon-map.json` (one family, static vs animated, adaptive vs
   fixed colour, no shared ids, fallbacks) and `audit_icons.py --payload FILE` (no double
   icons, no mixed keyboards, density).
8. **Fallback verified.** Run the same screens with `Eligibility()` (nothing) and check they
   read correctly with Unicode only; check the channel copy when the bot posts to channels.

## The icon plan: packs and button icons, stage by stage

Run this whenever you choose custom emoji for a bot's buttons or titles yourself (a restyle, a new
bot, "make the buttons nicer"). It replaces guessing with a measured choice the user can audit. A
person's own choice is never overridden: slots they picked are locks. **[Heuristic]** over the
**[API]** facts below.

Tools: in a bot-ui project `bot-ui emoji plan` (writes `emoji/icon-plan.json` and `icon-plan.html`),
`bot-ui emoji verdict`, `bot-ui emoji apply-plan`; without a project `emoji_packs.py library plan
--needs … | --places places.json --route … --sheet plan.html`; MCP `emoji_plan_icons`. Module:
`scripts/emoji_plan.py`. Network: only the library's search words and pack names leave the machine.

**Stage 0 - should there be icons at all.** Read the route (`capabilities.customEmoji`: `fragment`,
`owner_premium`, `none`) and where the bot speaks.
- `none` → STOP: keep words (and Unicode only where `visual-language.md` allows). Telegram strips
  custom emoji silently.
- `owner_premium` and a channel screen → icons there need Fragment; plan the channel copy without.
- Fewer than 3 slots across the bot → icons rarely pay off; propose label-only and stop unless asked.

**Stage 1 - inventory.** Every keyboard button and every title that opens with an emoji becomes a
place; its label words (every locale, `slots.json` `words`) decide the meaning, a leading emoji only
breaks a tie. Rules: a keyboard is all icons or none; Back, Forward and Close stay words (the plan's
`controls` switch adds them only when the family draws them everywhere); a label that says no known
meaning is `unmatched`: give it no icon. STOP if nothing matched: the bot needs words, not icons.

**Stage 2 - style brief.** From the style profile (`brand.icon_style`, accent, traits, archetype); without
one, the Mini App kit's own icons: `style outline, palette monochrome, fit adaptive, topic interface`,
so the bot and its Mini App read as one identity (stroke 1.8, one colour, right in both themes).

**Stage 3 - packs.** The library is searched for each slot's emoji (static hits vote) and ranked by tags;
the top packs are fetched whole. Each pack scores: weighted static coverage (buttons 1, titles 0.5) 0.45,
facet fit to the brief 0.2, theme safety 0.15, legibility 0.1, meaning quality 0.1. The best is the
**main pack**; its library-rated siblings with similarity ≥ 0.8 (`compatible`) form the family pool.
Animated and video emoji never enter (`BUTTON_EMOJI_ANIMATED`).

**Stage 4 - candidates per slot.** Every static emoji of the pool that says the slot is scored 0..1:

| Part | Weight | Measured as |
|---|---|---|
| meaning | 0.40 | the fallback is the slot's first emoji (1.0) or a later equivalent (-0.12 each); +0.1 when tagged with the slot's interface role; -0.15 decoration; -0.2 when it is another needed slot's first emoji |
| family | 0.20 | 1.0 in the main pack, the library's similarity for a sibling |
| style | 0.15 | the emoji's (else the pack's) style tag against the brief |
| theme | 0.10 | adaptive 1.0; fixed colours that read on both 0.75; one theme only 0.3 |
| legibility | 0.15 | at 20 px: -0.35 for 3d / glossy / realistic / gradient / neon / pixel detail, -0.3 a face or character, -0.15 many colours; the pack's look: hairline strokes, photo or gradient fill, glow, three-quarter view |

A candidate needs meaning ≥ 0.6 and legibility ≥ 0.4.

**Stage 5 - assembly.** For each slot (locks first, then buttons by how often they appear): the main
pack's best candidate, unless a sibling says the meaning 0.2 better or scores 0.12 higher; one emoji
one meaning (an id taken by a slot is gone for the rest); nothing good enough → **label-only, never a
wrong meaning to stay in one pack**. Then a keyboard whose content buttons are not all covered goes
label-only. More than two packs in use is flagged.

**Stage 6 - look at it (required).** Open the review sheet. Each row shows the choice at button size
(20 px) and 40 px on a light and a dark tile next to its label, up to three alternatives, the score
breakdown and the reasons. For every chosen slot decide and record:
`bot-ui emoji verdict --slot <slot> --ok` (it says the label, reads at 20 px on both tiles, matches its
neighbours in fill, weight and colour), `--alt N` (take alternative N, look again, then `--ok`) or
`--reject "<why>"` (the slot goes label-only). Style tags are the library's weakest (recall about 0.35):
the picture decides, not the tag.

**Stage 7 - record and apply.** `emoji/icon-plan.json` keeps the brief, the gate, the pack ranking, the
family, per slot the choice, alternatives, scores, reasons and verdict: commit it, so a later restyle
and the user see why. `bot-ui emoji apply-plan` writes only `--ok` slots into the icon map (marked
`by: plan`, with the reason) and never touches a person's slot; then `bot-ui emoji import <pack>` for
previews.

**Stage 8 - validate.** `bot-ui validate` (`BUTTON_EMOJI_ANIMATED`, `ICON_MEANING_MISMATCH`,
`CUSTOM_EMOJI_UNKNOWN`), `bot-ui emoji review` on the placed icons, `audit_icons.py emoji/library.json`;
then send one screen from the real bot and read it back: an ineligible bot gets no error, only missing
icons.

## Choosing a pack

| Signal | Prefer | Avoid |
|---|---|---|
| Utility, monitoring, finance, support | static app-style glyphs (`tgmacicons` + `tgiosicons`, `TgAndroidIcons`, `UnigramIcons` + `EmojiStatus`) | animated sets on buttons |
| AI assistant | the bot's family for UI; `AIActions` only inside `<tg-thinking>` (**Official**: InputRichBlockThinking links it) | AIActions as the general family |
| Games, playful bots | a static set for the controls; one animated emoji for a hero moment in text at most (`DMJUnigramAnimationEmoji`, `UI_icons`) | animation on any control |
| Channel / editorial | a set whose marks fit headlines and sections (`NewsEmoji`) — needs the Fragment route | bot keyboards from an editorial set |
| Coins next to tickers | `cryptoicons` as inline content marks | logos as UI icons (trademarks) |

Rules (**Heuristic**): one family per bot; siblings (same author, explicitly paired sets, or packs the
library rates at least 0.8 similar) may fill gaps; static only on buttons (an animated or video emoji on any button is the error
`BUTTON_EMOJI_ANIMATED`; the pick takes a pack's static entry for a slot when it has one) and
static by default in text (`CUSTOM_EMOJI_ANIMATED` warns); adaptive (`needs_repainting`) and
fixed-colour icons do not mix; an uncovered slot is label-only, never a look-alike from another
family; the bot's family matches the Mini App's line icons in weight and fill.

**API facts used for the choice:** `Sticker.is_animated`, `is_video` (animation),
`needs_repainting` ("must be repainted to a text color in messages" — adaptive), `emoji`
(the Unicode equivalent and recommended fallback), `set_name`, `custom_emoji_id`.

## The catalog

`data/emoji/packs.json` lists only sets whose existence was checked on 2026-11-15 by opening
`https://t.me/addemoji/<name>` (an existing set shows "Add emoji set <title>"). It carries no
ids, and `animation` / `adaptive` stay `null` until a resolve reads the stickers; style words
come from the set titles. Re-check before relying on a set — authors can rename or remove
sets, which `emoji_packs.py verify` detects.

## The library contract, offline export and profile picking

- **Contract.** `data/emoji/library-contract.json` is a dated copy of the component schemas of
  the library's OpenAPI 3.1 document (`/api/emoji-openapi.json`), the tag taxonomy version the
  skill understands and the pack threshold. `LibraryClient` (`emoji_packs.py`) checks every
  answer (search, pack, facets) and every export line against it before reading a field: a
  changed shape fails with `CONTRACT_MISMATCH` naming the field, a taxonomy the skill does not
  know with `TAXONOMY_UNSUPPORTED` (facet values may be renamed between versions). An error
  answer keeps its own `error.code` (`PACK_NOT_FOUND`, `RATE_LIMITED`, ...). `library contract`
  shows the copy; `library contract --openapi saved.json --facets-file facets.json` refreshes it.
- **Offline.** `--library-file emoji-library.ndjson.gz` (the site's `/emoji-library.ndjson.gz`,
  one line per pack: tags, look, description in en/ru/uk, compatible packs, emoji ids with tag
  codes) replaces the network for `library facets` and `library pick --profile`, with the same
  result as online. The export has no fallback emoji and no search, so `pick --needs` (an icon
  map with real coverage) and `library search` stay online.
- **Profile picking.** `library pick --profile <style-profile.json> [--library-file …]` reads
  `brand.icon_style`, `traits` and `bot.archetype` as tags and compares `brand.accent` with each
  pack's measured colours and palette (same family, a neighbour on the colour wheel, a neutral
  colour; an adaptive pack takes the text colour and suits any accent). It prints one line per
  pack: coverage (emoji, meanings, interface roles), style, topic, colour and what the pack is
  for; the JSON adds the description (what, for, not_for) in the profile's primary locale
  (`--lang` overrides). An explicit `--color`/`--palette` replaces the accent comparison. Then
  run `pick --needs …` online with the chosen style to get the icon map.

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
