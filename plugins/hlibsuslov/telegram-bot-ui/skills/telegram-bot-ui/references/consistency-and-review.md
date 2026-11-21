# Consistency between screens and states, and the final review

A bot feels "designed" when the same thing looks and is named the same
everywhere. Most UX complaints about bots are consistency failures, not missing
features.

## The consistency inventory

Build these tables from the codebase before and after your change. Each row that
differs without a reason is a defect.

**1. Action vocabulary** — one label per action, bot-wide.

| Action | Labels found | Chosen label |
|---|---|---|
| return one level up | "Back", "⬅️", "Назад", "Return" | "← Back" |
| abandon a wizard | "Cancel", "Abort", "Stop" | "Cancel" |

**2. Navigation slots** — position and presence of Back/Home per screen.

**3. `callback_data` scheme** — prefix per screen, id format, verbs.

**4. Emphasis** — which screens use `primary` / `success` / `danger`, and
whether the meaning is the same everywhere.

**5. Emoji vocabulary** — which emoji marks which state, and whether the bot
mixes Unicode and custom emoji.

**6. Message shape** — title line style, use of bold, paragraph length,
where the keyboard sits relative to content.

**7. i18n coverage** — strings present in every locale, including button labels
and command descriptions.

## State consistency

The same screen renders differently across states — each variant must exist and
agree with the others:

| State | Must exist? | Common failure |
|---|---|---|
| Empty | Yes for every list/result screen | Renders an empty table or nothing |
| Loading / in progress | If work takes >1–2 s | Silence; user taps twice |
| Partial / degraded | If data can be incomplete | Presents partial data as complete |
| Error | Yes | Raw exception text or no message at all |
| Success | Yes | Nothing changes on screen after the tap |
| Stale (old message, changed data) | Yes | Old buttons act on data that moved |
| No permission | Where access varies | Button exists but errors on tap |

Rules:

- A tap must **always** produce feedback: an edited screen, a toast, or an
  alert (`inline-keyboards.md`).
- After a state change, **the screen must show the new state** — don't leave a
  toggle labelled "on" after switching it off.
- A stale message's buttons must be **re-validated server-side**; never trust
  that the visible screen matches the database.
- Keep the **same keyboard skeleton** across a screen's states so the layout
  doesn't jump — swap labels, not structure, where possible.

## Cross-surface consistency

The Telegram-side chrome must agree with the in-message UI:

- Command descriptions use the same verbs as the buttons that do the same thing.
- The menu button's destination matches what the main menu offers.
- Deep links land on screens that exist and are titled as the link promised.
- If a Mini App exists, its entry point is named identically wherever it appears.

## Final review checklist (run before reporting done)

**Behaviour preserved**
- [ ] Every existing `callback_data`, URL, deep link, and payload unchanged
      (or every consumer updated in the same change, and called out).
- [ ] Handlers/routers untouched by purely visual edits.
- [ ] Reply-keyboard label changes reflected in the matchers.

**Buttons**
- [ ] Exactly one action field per inline button; ≤1 non-text field on reply
      buttons.
- [ ] `callback_data` ≤ 64 bytes.
- [ ] `style` only `primary` / `success` / `danger`, assigned by meaning.
- [ ] ≤1 `primary` per screen; `danger` only for real destruction, with a
      confirmation step.
- [ ] Every label readable and unambiguous with no color and no emoji.
- [ ] No duplicate labels within one keyboard.

**Custom emoji**
- [ ] Eligibility route established (Fragment usernames / owner Premium /
      neither) and stated.
- [ ] No invented `custom_emoji_id`; each came from an entity, `getStickerSet`,
      or `getCustomEmojiStickers`.
- [ ] Unicode fallbacks present for text entities; buttons legible without the
      icon.

**Text**
- [ ] Facts, placeholders, and links preserved; i18n catalogs updated.
- [ ] Errors/empty/confirm/success screens follow the shapes in
      `microcopy-and-labels.md`.
- [ ] Escaping correct for the parse mode; nothing over the length limits.

**Navigation**
- [ ] Screen map has no dead ends or orphans.
- [ ] Back/Home consistent in label and position.
- [ ] Wizard steps show progress and offer Back + Cancel.

**Compatibility**
- [ ] SDK support for every new field verified, or a documented raw-payload
      path used (`sdk-compatibility.md`).
- [ ] Behaviour on clients that ignore `style` / `icon_custom_emoji_id` checked.
- [ ] Fallback path explicit and logged (`errors-and-fallbacks.md`).

**Verification**
- [ ] Keyboard payloads validated (`scripts/validate_keyboard.py` or the
      project's own tests).
- [ ] Project lint / typecheck / tests run and green.
- [ ] Screens exercised manually or in a harness (`testing-playbook.md`).
- [ ] Report lists what changed, what was left alone and why, and anything that
      still needs the bot owner's input (IDs, Premium status, copy decisions).
