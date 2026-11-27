---
summary: "Rewriting message texts, titles, captions and button labels safely: keep facts and placeholders, body rules, tone, emoji, errors, empty states; read before editing any bot copy."
verified: "2026-11-23"
bot_api: "10.5"
---

# Microcopy: message texts, titles, captions, button labels

Text is the bot's primary interface. This is the first layer to fix and the one
that most often makes color and emoji unnecessary.

## Rewriting an existing text — the safe procedure

1. **Identify what the text must accomplish** (inform / ask / confirm / warn /
   celebrate) and who reads it.
2. **Keep every fact.** Prices, deadlines, legal wording, IDs, and links survive
   verbatim unless the user asked otherwise.
3. **Keep the placeholders.** `{name}`, `%s`, `{{count}}`, ICU plurals, Fluent
   selectors — same names, same count. Never reorder positional placeholders.
4. **Edit the catalog, not the call site.** If the project has i18n, change the
   translation entry; don't inline a literal at the send site.
5. **Update every locale or none.** A rewritten English string with stale
   translations is a regression — if you can't translate, flag the locales that
   need it (`localization-and-rtl.md`).
6. **Re-check escaping** for the parse mode in use: new punctuation can break
   MarkdownV2, and copied text can carry raw `<`/`&`
   (`security-and-escaping.md`).
7. **Re-check length** against the message/caption limits and the chosen layout
   (`limits-and-splitting.md`).

## Message body rules

- **One screen, one job.** If a message asks two questions, it is two screens.
- **Front-load the point.** First line = what this is or what happened. Users
  read one line in a notification preview.
- **Short lines, few of them.** Under a keyboard, 1–3 short paragraphs. Long
  reference content belongs in a table, a collapsible block, or a separate
  message (`format-selection.md`).
- **Structured data becomes a table**, not a monospace grid or bullet soup
  (`tables.md`).
- **Formatting is emphasis, not decoration.** Bold the one thing that matters;
  a message where everything is bold has no emphasis at all.
- **No raw internals.** Stack traces, SQL, enum names, and HTTP codes are not
  user-facing — log them, show a human sentence plus a support route.
- **Write dates and times for the reader.** Prefer the `date_time` entity so the
  client renders in the user's locale and timezone
  (`navigation-and-flows.md`); otherwise state the timezone explicitly.

## Titles and captions

- A title is a **noun phrase** naming the screen ("Order #1042", "Your plan"),
  not a sentence.
- Keep titles stable across states — the same screen shouldn't rename itself
  after a refresh.
- Media captions have a **smaller limit than message text** — check the current
  numbers in the docs, keep captions to the essential line, and move detail into
  a following message (`limits-and-splitting.md`, `rich-media.md`).

## Button labels

- **Verb + object**: "Add to cart", "Send report", "Confirm order". A label that
  is only a noun ("Report") leaves the user guessing what happens.
- **Say the outcome, not the mechanism.** "Get the PDF" beats "Generate file".
- **Match the destination.** A button labelled "Settings" must lead to a screen
  titled "Settings" — same word, both places.
- **Short enough not to truncate**: aim for ≤ ~20 characters for a full-width
  button, fewer when the row holds 2–3 buttons. Verify with the **longest
  translation**, not English.
- **Unique within a keyboard.** Two buttons with the same label are a bug even
  if their payloads differ.
- **One label per action, bot-wide.** Not "Cancel" here and "Abort" there.
- **Never emoji-only.** `🔙` alone is unreadable to screen readers and
  ambiguous; use "← Back".
- **Front-load the distinguishing word** in a list: "Order #1042 — 3 items"
  reads better than "You have an order numbered 1042".
- **Destructive labels name the object**: "Delete this draft", not "Delete".

## Emoji in text and labels

- **Budget:** at most one emoji per button, and roughly one per message screen.
  Emoji are punctuation, not paragraph markers.
- **Position:** leading emoji work as icons (`✅ Confirm`); trailing emoji read
  as tone. Pick one convention per bot and record it.
- **Use a fixed vocabulary** where an emoji means a state: ✅ done, ⏳ pending,
  ❌ failed, ⚠️ warning. Never reuse a state emoji decoratively.
- **Never encode meaning only in an emoji** — the word must carry it alone.
- **Skip emoji entirely** in errors that involve money, legal terms, or data
  loss; they undercut the message.
- Custom emoji have their own eligibility and fallback rules
  (`custom-emoji.md`), and mixing them with Unicode emoji on one control set
  needs a deliberate reason.

## Tone

- Address the user directly, present tense, active voice.
- Neutral and plain by default; match the project's existing register if it has
  one (check other strings before inventing a voice).
- Don't apologize repeatedly, don't scold, don't exclaim. One "!" per screen at
  most.
- Formality is language-specific: German and Russian bots must decide between
  formal/informal address and hold it consistently across **all** strings.

## Errors, empty states, confirmations

**Error** = what happened + why (if useful) + what to do next.

> ❌ Payment failed — the card was declined by the bank.
> Try another card or contact support.
> `[ Try again ]  [ Contact support ]`

**Empty state** = what would be here + the action that fills it.

> No orders yet. Your orders will appear here after your first purchase.
> `[ Browse catalog ]` *(primary)*

**Confirmation of a destructive action** = name the object, name the
consequence, state reversibility.

> Delete "Project Alpha"? All 42 tasks will be removed. This can't be undone.
> `[ Yes, delete it ]` *(danger)* / `[ ← Keep it ]`

**Success** = what happened + what's next, in one line. Don't celebrate longer
than the action deserved.

**Stale screen** (an old button after a restart, a release or a state change) = it is out of
date + what is still saved + one fresh entry. Answer the callback with the first two as a
toast, then show the current screen; never a spinner, never a silent no-op.

> toast: "This menu is out of date. Your order and bonus card are saved."
> then the current menu with its one `primary` action

**Notification** (the bot speaks first) = the event and whether the reader must act, in the
first line (≤ ~80 visible chars: previews cut there), then one fact per line. Bold the values
people check, `<code>` the values they copy, no greeting or sign-off. Silent
(`disable_notification`) unless someone must act now. When it is handled, **edit the same
message** into its outcome line and remove the buttons, so old alerts don't keep live actions.
A failure inside a status card replaces its own line (⚠️ + next step) and keeps the card's shape.
The header formula, body blocks and one pattern per notification type: `message-patterns.md`.

> **☕ Order #1042 is ready**, pick it up by 13:10
> Khreshchatyk St 22, counter 2
> Pickup code: `7731`
> `[ I've picked it up ]` → edited later to "Picked up at 12:58."

**Blocker** (something the reader asked for can't continue) = cause + impact + the next action,
sent at once, not at the end of a long run.

## Before/after

| Before | After | Why |
|---|---|---|
| "Error 500. Something went wrong. Please try again later or contact the administrator if the problem persists." | "Couldn't load your orders. Try again in a minute." + `[ Try again ]` | States the failed thing, gives an action, drops the internals |
| `[Submit]` | `[ Send application ]` | Verb + object; says what is sent |
| "You have no items." | "No saved items yet — tap ★ on any product to save it." | Explains how to leave the empty state |
| "❗️❗️ATTENTION❗️❗️ Your subscription 🔥EXPIRES🔥 tomorrow!!!" | "⚠️ Your subscription ends tomorrow (23 Aug). Renew to keep access." + `[ Renew ]` *(primary)* | One emoji, one fact, one action |
| `[✅][❌]` | `[ ✅ Confirm ] [ ❌ Cancel ]` | Emoji reinforce words instead of replacing them |

## Checklist

- [ ] Every facts/placeholders/links preserved through the rewrite.
- [ ] Strings changed in the i18n catalog, all locales accounted for.
- [ ] First line states the point; one job per screen.
- [ ] Labels are verb+object, unique, ≤ ~20 chars in the longest locale.
- [ ] The same action uses the same label everywhere.
- [ ] Emoji budget respected; no meaning carried by emoji alone.
- [ ] Errors, empty states, confirmations, stale screens and notifications follow the shapes above.
- [ ] No bare "OK", "Yes", "Submit": each label names its outcome (`validate_keyboard.py` warns).
- [ ] Escaping re-verified for the parse mode after the edit.
