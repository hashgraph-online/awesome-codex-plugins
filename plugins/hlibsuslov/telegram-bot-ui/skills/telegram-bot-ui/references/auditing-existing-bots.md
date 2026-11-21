# Auditing an existing bot (analyze → diagnose → propose)

Heuristics of this skill (first written 2026-08-05, reviewed against Bot API 10.4 on
2026-11-15). Version gates: `ui-changelog.md`; every 10.3/10.4 item: `bot-api-10.3-10.4.md`.

> **Most work on this skill is not greenfield.** There is already a bot, already
> a repo, already hundreds of strings someone wrote under time pressure. The
> agent's job is to *understand what exists* and make it better — not to design
> a hypothetical bot from scratch.
>
> `project-adaptation.md` tells you how to **find** the interface in an unknown
> repo. This file tells you what to **do with what you found**: how to inventory
> the text, diagnose it, and put concrete proposals in front of the user.

Use this whenever the input is an existing bot: a repo, a directory, a single
handler file, or **even a pasted snippet of code or message text**. The pipeline
scales down — a 20-line snippet gets the same passes, just faster.

---

## Pass 0 — Establish scope and constraints

Before reading code, know what you're allowed to change. If the user hasn't
said, assume the **conservative** answer and state the assumption:

- **Behaviour is frozen** unless told otherwise: `callback_data`, routing,
  handler names, deep links, i18n keys stay as they are.
- **Wording is in scope** when the user asks for UX/text work.
- **Structure (keyboards, navigation)** is in scope only if named.

Also determine the **hard ceiling**: the Bot API version the installed SDK
supports (`project-adaptation.md` step 2). An audit that recommends tables to a
bot on Bot API 9.6 is a wasted audit — Rich Messages need **10.1+** (and
`blocks` needs **10.2+**).

---

## Pass 1 — Build the text inventory

Extract **every user-visible string** into one list. This artifact is the whole
foundation; do not skip it and do not work from memory.

Where strings hide (search all of these — see `project-adaptation.md` for SDK
patterns):

- literals passed to `sendMessage` / `reply` / `answer` / `edit_text`
- i18n catalogs (`.ftl`, `.po`, `.json`, `.yaml`) — often the *real* source
- template files and f-strings / template literals
- button labels inside keyboard builders
- `BotCommand` descriptions, menu button text, `input_field_placeholder`
- `answerCallbackQuery` toast text
- error strings in `except` / `catch` blocks (**routinely the worst text in any
  bot** — written last, never reviewed)
- empty-state text ("nothing found", "no items yet")
- captions on media sends

Record per entry:

| Field | Why it matters |
|---|---|
| Location (`file:line`) | so a proposal is actionable |
| Screen/state it belongs to | groups related text |
| Class | menu / prompt / confirmation / result / error / empty / notification |
| Current format | plain / HTML / MarkdownV2 / entities / rich |
| Localized? | key present, or hardcoded |
| Length | flags 4096 / 1024 caption risk |
| Dynamic parts | user data interpolated → escaping risk |

**Deduplicate as you go.** The same sentence appearing in 5 places is itself a
finding.

---

## Pass 2 — Diagnose each entry

Run every string through these five checks. Most defects are one of these.

### 1. Shape — is it rendered as what it actually is?
Apply `content-shape-detection.md` in full. The recurring finds in real bots:

- `Label: value` runs that should be tables
- `<pre>` grids padded with spaces (breaks on phones) that should be tables
- bold paragraphs used as headings
- prose comparisons that should be tables
- long option lists that should be lists or keyboards
- AI answers flattened to plain text, losing all structure

### 2. Clarity — does the reader know what happened and what's next?
- Does the message state the **outcome** ("Saved" vs "Done")?
- Is there a **next step** where one is needed?
- Jargon, internal terms, database field names leaking into user text?
- Button labels that are nouns where a verb is meant ("Settings" vs "Change
  language")?

### 3. Consistency — does it match its siblings?
- The same action named differently on different screens.
- Mixed tone (formal on one screen, chatty on the next).
- Mixed emoji conventions — some screens loaded, some bare.
- Different date/number/currency formats across messages.
- Some screens have Back, others dead-end.

### 4. Safety — will it break or leak?
- User data interpolated into HTML/MarkdownV2 **without the matching escaper** →
  live `can't parse entities` bug (`security-and-escaping.md`).
- One universal escaper used for both formats — always wrong.
- Messages that can exceed **4096** (or **1024** in a caption).
- AI output passed straight through as HTML.

### 5. Localization — will it survive translation?
- Hardcoded string where siblings use i18n.
- Sentence assembled by concatenating fragments (unlocalizable).
- Button label that will truncate in German/Finnish.
- Hardcoded plural rules, dates, or currency.

---

### 6. Newer capabilities — what would the current Bot API do better?
Apply the initiative rule from `SKILL.md` to what you found, within the version ceiling
from Pass 0: a long AI wait with no Stop (`streaming-and-editing.md`); a form without
disabled Submit or `force_reply` (recipe 03); personal data answered publicly in a group
(`ephemeral-and-personal.md`); a status that is re-sent instead of one live card
(`widgets.md`, private chats); mixed or missing icons (`emoji-packs.md`). Report them as
proposals with the gain for the reader, not as defects.

## Pass 3 — Rank by reader gain

Never present a flat list of 60 findings. Rank into three tiers:

- **Bugs** — it is broken *right now*: parse errors, oversized messages, dead
  ends, unescaped input, missing feedback on long operations. Fix these first;
  they usually need no permission because they aren't taste.
- **High-value UX** — the reader visibly gains: a `<pre>` grid becoming a real
  table, an error message that finally says what to do, a destructive action
  getting a confirmation.
- **Polish** — tone, emoji consistency, minor wording. Batch these; never lead
  with them.

A finding that you cannot express as *"the reader gains X"* is not a finding.
Drop it.

---

## Pass 4 — Report, then propose

Output in this order:

1. **What the bot is** — screens, SDK, Bot API ceiling, format(s) in use,
   localization state. Three or four lines.
2. **Inventory scale** — "84 user-visible strings across 11 screens, 6 hardcoded
   outside i18n".
3. **Findings by tier** — each with `file:line`, the defect in one sentence, and
   the proposed fix in one sentence.
4. **Proposals grouped into decisions** — see below.
5. **What you deliberately left alone**, and why.

### Group findings into decisions, not questions

The user should face **a few decisions**, not sixty. Group by theme:

> **1. Structured content → real tables (6 messages).** Order summary, `/stats`,
> plan comparison, `/history`, invoice, admin report. All currently `Label:`
> lines or `<pre>` grids. Needs Bot API 10.1+ — your SDK is on 10.2, so it's
> reachable. Handlers and `callback_data` untouched.
>
> **2. Error messages (11 messages).** Currently "Error" / "Something went
> wrong". Proposal: state what failed and the one action that fixes it.
>
> **3. Escaping bug (3 places).** User names interpolated into MarkdownV2
> unescaped — any user with `_` in their name breaks the message today.
>
> Recommend: 3 first (it's a live bug), then 1, then 2. Say which you want.

### Then ask the questions only the user can answer

Ask these — do not guess them silently. Keep to what actually changes the work:

- **Tone** — formal or casual? (Show two rewrites of the *same* real message
  from their bot rather than asking in the abstract.)
- **Emoji** — in button labels, in body text, or nowhere?
- **Audience** — who uses this bot, and how technical are they?
- **Length** — terse notifications, or explain-as-you-go?
- **Scope** — may `callback_data` / i18n keys change, or are they frozen?
- **Locales** — which are live? (Decides how hard the layout budget is.)

Show, don't ask abstractly. One concrete before/after beats a paragraph of
questions about preferences.

---

## The "rework it" pipeline

When the user says *"переработай"* / *"rework this bot's text"* / *"improve all
the messages"* — that is a request for **the full pipeline**, not a few edits:

1. **Passes 0–3** in full. Do not start rewriting message #1 before the inventory
   is complete — you'll produce inconsistency, which is the exact defect you're
   there to fix.
2. **Establish the voice first.** Rewrite 2–3 representative messages, show them,
   get agreement on tone/length/emoji. Everything else follows this decision.
3. **Build a wording contract** from the agreed samples: how the bot addresses
   the user, how errors open, how confirmations read, verb forms on buttons,
   emoji policy, date/number formats. Write it down — it's what keeps message #57
   consistent with message #3.
4. **Rewrite in screen order**, not file order, so each screen reads as a unit.
5. **Re-run consistency** across the whole set at the end
   (`consistency-and-review.md`) — cross-screen defects only appear once
   everything is rewritten.
6. **Preserve every key**: i18n keys, `callback_data`, routing. If a key's text
   changes meaning enough that the key name is now wrong, flag it — don't
   silently rename.
7. **Report as a diff summary** per screen, plus what you left alone.

For a bot with live translations, rewriting the source locale **orphans every
translation**. Say this out loud before starting and agree on the plan (retranslate
/ mark stale / keep both) — discovering it afterwards is a bad surprise.

---

## Auditing a pasted snippet (the small case)

Same passes, one minute:

1. Name the format and SDK you can infer.
2. Run shape detection on the strings.
3. Point out any live bug (escaping, length, missing feedback).
4. Show the rewritten snippet.
5. Say what you assumed, since you can't see the rest of the bot.

Don't demand the whole repo before helping. Work with what's pasted, state the
assumptions, and offer to check the rest.

---

## Anti-patterns

- **Rewriting before inventorying** — guarantees inconsistency.
- **Presenting 60 flat findings** — the user disengages and nothing ships.
- **Findings with no `file:line`** — unactionable.
- **Changing `callback_data` "while we're in here"** — breaks routing silently.
- **Asking abstract taste questions** instead of showing two concrete rewrites.
- **Only auditing the happy path** — error and empty states are where the bad
  text lives.
- **Recommending Rich Messages without checking the SDK's Bot API version.**
- **Treating an audit as a rewrite mandate** — audit reports findings; rewriting
  is a separate, agreed step.
