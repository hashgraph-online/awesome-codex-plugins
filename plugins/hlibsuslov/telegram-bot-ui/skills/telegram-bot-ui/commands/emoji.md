# emoji: one premium emoji pack, applied everywhere eligible

**When:** premium or custom emoji in buttons, texts or posts; move to another pack.

## Read

- Eligibility and ids: `references/custom-emoji.md`.
- The decision path, choosing, resolving, applying, migrating, widgets:
  `references/emoji-packs.md` ("The agent's decision path" first).
- Posts and long texts: `references/emoji-in-posts.md`.
- One icon system per bot: `references/visual-language.md` §1-3.

## Steps

1. Check eligibility (Fragment usernames, or owner Premium outside channels). If ineligible, say
   so and keep Unicode fallbacks: Telegram strips the emoji silently and returns no error.
2. `tgui.py emoji library pick --needs <slots>` (the ~490-pack library: one family ranked by real
   coverage, theme-adaptive, static; only slot emoji leave the machine) → `emoji apply`; offline:
   `emoji suggest` → `emoji resolve`. Ids come from a real pack, never invented; `emoji verify`
   against a sent message read back. One icon by meaning: `emoji library search <words>`. By look:
   `emoji library facets --use <bot kind> --style … --theme both` (tags with confidence; style
   tags are the least reliable, so show the pack before you rely on one).
3. All icons of a message or none; one pack family per bot (`tgui.py check icons`).
4. **Double check, required:** `bot-ui emoji review --out icon-review.html` (or `audit_icons.py`
   without a project), open the sheet and look at every row: the picture says what the label says
   (`ICON_MEANING_MISMATCH`), it is static (`BUTTON_EMOJI_ANIMATED`), it matches its neighbours
   in fill, weight and colour. Fix or drop every red row; a slot no pack says well stays label-only.

## Without scripts

Use only ids from `data/emoji/packs.json`; if the pack isn't there, ask for a sticker-set link.

## Done

One family, every id resolved, Unicode fallback kept, eligibility stated, the review sheet
looked at and clean.

## Next

`improve` the screens whose icons changed, or `post` for channel use (needs Fragment).
