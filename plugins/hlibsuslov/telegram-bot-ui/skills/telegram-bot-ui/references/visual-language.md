# Visual language: icons, emoji and text structure

> Status: **Heuristic** (this skill's design system) unless marked **API**. Verified against
> Bot API 10.4 on 2026-11-12. Tools: `scripts/audit_icons.py`, `scripts/audit_copy.py`,
> `examples/python/icons/build_icon_map.py`, `examples/python/tgkit/icons.py`.
> Worked example: `case-study-btc-tracker.md`.

A professional bot looks like **one product**: the same symbol always means the same thing, icons
come from one drawing style, every screen has the same anatomy, and decoration never competes
with information.

## 1. Choose one icon system per bot

| System | When | Cost |
|---|---|---|
| **None** (words only) | utilities, admin bots, dense data | zero; always accessible |
| **Unicode emoji** | most bots; no eligibility needed | renders differently per platform; easy to overuse |
| **Custom emoji ("premium icons")** | a branded bot whose owner has Premium or Fragment usernames | eligibility (**API**: buttons/text only for Fragment-username bots, or messages the bot sends directly to private/group/supergroup chats while the owner has Premium); ids must be real |

Rules:
- **One family per bot.** A family = one designer's style: same grid, stroke weight, fill
  (outline vs solid), corner radius, color treatment, static vs animated. Packs that imitate
  different platforms (iOS, Android, Unigram, macOS) are different families even when they draw
  the same objects.
- **Static on buttons.** Animated custom emoji on controls pull the eye from the label; keep
  animation for one hero moment (a success screen, `<tg-thinking>` with the AIActions set the
  Bot API recommends).
- **Same id in text and on buttons.** If buttons use custom emoji, screen titles use
  `<tg-emoji emoji-id="…">` with the same id (`IconSystem.title`) — not a Unicode look-alike.
- **Degrade together.** When eligibility is lost, switch *every* icon to its Unicode fallback (or
  every one to label-only) — never a mix (`IconSystem(enabled=False)`); keep a kill switch.
- **No double icons.** A button with `icon_custom_emoji_id` has no emoji in its label.
- **Not every button needs an icon.** Back/Next/Cancel and list items are often clearer as words.
  An uncovered slot stays label-only rather than borrowing a foreign style.

## 2. Picking premium icons (process)

1. **List the slots** the bot needs, by meaning: `home, wallets/list, add, search, settings,
   notifications, mute, language, rename, delete, back, confirm/done, warning, error, help, share,
   copy, refresh, stats`. Keep 8–15; more slots = more drift.
2. **Shortlist 1–2 families** whose base pack covers ≥ 70 % of the slots. Look at them in the
   chat on light and dark themes, at button size, next to each other.
3. **Resolve ids, never guess** (**API**): `getStickerSet(name)` → `stickers[].custom_emoji_id`
   + `emoji` (the Unicode equivalent = your fallback); `getCustomEmojiStickers(ids)` (≤ 200) →
   `set_name`, `is_animated`, `is_video` for ids someone gave you.
   `build_icon_map.py --set <name> --slots slots.json` does the mapping and lists uncovered slots.
4. **Fill gaps** from the same family's sibling pack (e.g. the iOS and macOS packs of one author),
   otherwise leave the slot label-only.
5. **Record the map** (slot → id, set, fallback, animated) in one module; run
   `scripts/audit_icons.py` in CI. Re-resolve after a pack update.
6. **Check meaning, not just looks:** one id = one meaning; `delete` and `close` must not share
   an id; the warning symbol is never a decoration.

Automated version of this process (slot vocabulary of 240 meanings, verified pack catalog,
resolve/suggest/verify/apply CLI, agent decision path): `emoji-packs.md`. Posts and long
texts: `emoji-in-posts.md`.

### IconSystem v2 in one paragraph

`IconSystem(icons, vocabulary=load_vocabulary(), eligibility=Eligibility(...))` — handlers
call `button`, `title`/`text` (HTML), `md2`, `rich`/`rich_label` (Rich Messages) and
`composer()` (entities with UTF-16 offsets) by **slot**; `send(transport, method, params,
SendContext(...))` decides per message, converts any Unicode emoji the handler wrote, and
strips everything when the message is not eligible or Telegram refuses it (one retry, kill
switch). While icons are on, a slot without an id renders **label-only**, so a keyboard never
mixes custom icons with Unicode stand-ins.

### Density and discipline (Heuristic)

- Buttons: one icon per button, a whole group or none; static only.
- Screen text: ≤ 3 custom emoji, ≤ 1 per line; posts ≤ 8, ≤ 1 per line
  (`density_warnings`, `audit_icons.py --payload`).
- Adaptive (`needs_repainting`) icons follow the text colour; do not mix them with
  fixed-colour icons on one bot (`audit_icons.py` warns).
- Widgets cannot show custom emoji by id (Widgets guide): draw the same family in inline SVG
  (`emoji-packs.md#widgets-and-custom-emoji`).

## 3. Unicode emoji discipline (applies to fallbacks too)

- **Signal, not ornament:** an emoji earns its place when it lets the eye find something —
  a section, a status, an action. ≤ 1 per line, ≤ 1 per heading; none on every bullet.
- **Status vocabulary is reserved:** ✅ done · ⚠️ needs attention · ❌ failed · ⏳ in progress.
  Don't use ✅ as a "Confirmations" settings icon and as "success" in the same bot.
- **One symbol per meaning, everywhere:** same key → same leading symbol in every language
  (`audit_copy.py` checks), same meaning → same symbol in text and on buttons (🔍 vs 🔎, 🔙 vs ←
  are two symbols).
- **Arrows:** pick one navigation pair (← / →) and use it for Back/Previous/Next everywhere.
- **Flags are not languages:** show language names ("Українська"), flags only as an extra.

## 4. Screen anatomy (regular messages)

```
<b>[icon] Title</b>                ← one line, bold, the screen's name or the event
Context line                       ← what this is / for which object (name, count, page)
                                   ← blank line
Body                               ← facts: short lines "Label: <b>value</b>", a list, or a table
<code>copyable value</code>        ← addresses, ids, paths, codes (tap-to-copy on clients)
                                   ← blank line
<i>Hint or consequence</i>         ← one sentence; for destructive actions say what is lost
```
+ keyboard: one primary forward action, secondary actions neutral, Back last.

Patterns:
- **Steps:** "Step 2 of 3 · Wallet name" in the title; keep earlier answers visible.
- **Lists:** "Total: **42** · Page **2/9**" on its own line; paginate before 8–10 rows.
- **Numbers:** right-align in tables, `tabular-nums` in widgets; units after the value
  ("0.0125 BTC", "≈ $1,215.63"); one decimal convention per locale (`Intl` in widgets).
- **Copyable values:** `<code>` in text, a `copy_text` button for the one value people copy.
- **Times:** `date_time` entities / `<tg-time>` (9.5+) so each reader sees their timezone.
- **Empty states** say what will appear and offer the action that fills them.
- **Errors** say what happened and what to do, never a stack trace or "Error 400".
- **Rich vs regular:** use Rich Messages when the body needs headings, tables or long text;
  keep menus and prompts as regular messages (`format-selection.md`).

## 5. Buttons: label, color, icon

Label first (verb + object, ≤ ~24 chars in the longest locale) → layout → `style` (one primary,
`danger` only before a confirmation, success for commit) → icon. Pair meaning with color:
a `danger` button keeps the delete icon; a `success` button gets the done/confirm icon, not a
decorative one. Toggle buttons show **state in words** ("Incoming: On"), the icon stays the
slot's icon — don't swap icons to encode state.

## 6. Audit checklist

- [ ] `audit_icons.py`: one family, static, no shared ids, fallbacks present, no fixture ids;
      `audit_icons.py --payload`: no double icons, no mixed keyboards, density in budget.
- [ ] `audit_copy.py`: placeholders and leading symbols equal across languages; no over-long labels.
- [ ] `validate_keyboard.py`: one action per button, ≤ 1 primary, no emoji-only labels.
- [ ] Screens follow the anatomy; status symbols used only for status.
- [ ] Looks right with custom emoji **off** (Unicode fallback) and on light/dark themes.
