# Content-shape detection — recognizing what the text wants to be

Heuristics of this skill (first written 2026-08-05, reviewed 2026-11-15). Surface choice
(message, rich document, keyboard, widget, Mini App): `format-selection.md`.

> **This is the skill's proactive core.** Every other reference tells you *how*
> to build a thing once you've decided to. This one tells you **when to decide,
> without being asked** — how to look at a blob of bot text and see that it is
> secretly a table, a checklist, a heading tree, or a collapsible block.
>
> Run this pass on **every** piece of user-visible text you write, generate,
> review, or migrate. Detection is not a favour you do when the user says
> "format this" — it is part of producing the text at all.

## The rule

**Text is never "just text". It has a shape.** Your job is to find the shape and
render it, or — when the change is bigger than the user asked for — to *name the
shape out loud and offer it*.

Silence is a failure mode. If you shipped a wall of `Label: value` lines and
never mentioned that it is a 2-column table, you did half the job.

---

## Step 1 — Read the content for shape signals

Scan the text for these. Each signal points at one target format.

### → TABLE (highest priority — check this first)

Any **one** of these is enough to make a table the leading candidate:

| Signal | What it looks like |
|---|---|
| **Repeated records, shared attributes** | 2+ items that each carry the same fields (name + price + status) |
| **`Label: value` run** | 2+ consecutive lines of `Something: something` |
| **Parallel prose comparison** | "Basic costs €5, Pro costs €12, Team costs €30" |
| **Aligned monospace grid** | existing `<pre>` with hand-padded spaces, `\t`, or `|` |
| **Repeated separator** | 2+ lines split by the same ` — `, ` – `, ` / `, ` \| ` |
| **Numeric column** | the same unit/currency/date repeating down a list |
| **Enumerated attributes per item** | a bulleted list where every bullet has sub-bullets with the *same* labels |
| **Before/after or diff** | "was X, now Y" repeated |
| **Ranking / leaderboard / scores** | positions with values |
| **Schedule / timetable** | times paired with events |

**The two-axis test (use this when unsure).** A table is right when the data has
**two axes**: records (rows) × attributes (columns). Ask:

1. Can I name the **rows**? ("each plan", "each match", "each order line")
2. Can I name the **columns**? ("price", "status", "date")
3. Do **most** cells at those intersections have a value?

Three yeses → table. If only one axis exists, it is a **list**, not a table. If
most intersections are empty, it is a **key/value list per record**, not a grid.

**Minimum size.** 2 records × 2 attributes is a table. 1 record × N attributes is
a 2-column `Field | Value` table *only if* N ≥ 3 — below that, plain lines read
better.

**Maximum width.** Over 20 columns is impossible (hard API cap). Over ~4 columns
is usually unreadable on a phone — transpose or split, and say so.

### → LIST (one axis only)

Sequential or unordered items with **no shared sub-attributes**: steps,
options, features, warnings. Signals: lines starting `-`, `*`, `1.`, `•`; prose
with "first… then… finally"; comma-separated enumerations longer than ~3 items.

Use an **ordered** list when order is meaningful (steps, ranking), **unordered**
otherwise.

### → CHECKLIST (`- [ ]` / `has_checkbox`)

A list whose items are **things the user does or completes**: onboarding steps,
requirements, document lists, "what you need before starting". Signals:
imperative verbs per item, "required", "make sure", "you need to".

### → HEADINGS (section tree)

The text has **2+ topics** that a reader would want to jump between. Signals: a
bolded line acting as a title, "Part 1"/"Step 2", a topic shift mid-message, any
message over ~15 lines covering more than one subject.

**A bold paragraph used as a title is always a defect** → convert to a real
heading block (`InputRichBlockSectionHeading`, `#`, `<h2>`).

### → DETAILS (collapsible)

Content that **most users don't need but some do**: terms, full changelog,
methodology, raw error trace, "advanced settings". Signals: the text says "if you
want more detail…", or a long tail of secondary information after the answer.
Especially valuable past the ~8,000-character "Show More" threshold.

### → BLOCKQUOTE / PULLQUOTE

Quoted user input, a cited rule, a policy excerpt, an echoed message being
replied to. Long quotes → expandable. A `<aside>` pull quote is for emphasis of a
key line, not for ordinary quoting.

### → CODE BLOCK

Anything the user might **copy verbatim**: IDs, tokens, commands, JSON, config,
addresses. Always set the language when it has one. Consider a `copy_text` button
instead when the value is short and copying is the whole point.

### → MATH

Any formula currently written as `x^2` or Unicode fractions → real math
(`$…$` inline, `$$…$$` block).

### → MEDIA BLOCK

The text describes something visual and a file is available. 2+ related images →
collage or slideshow rather than sequential sends.

---

## Step 2 — Apply the escape hatch honestly

**Do not format things that don't need it.** Over-formatting is as much a defect
as under-formatting, and it is the more embarrassing one.

Leave as plain/regular text:

- one-line statuses, confirmations, errors ("Saved", "Code sent")
- short prompts that exist to introduce a keyboard
- anything under ~2 lines with no repetition
- transactional notifications the user reads in a notification banner

A menu screen is **a short prompt plus buttons**, never an essay and never a
table. If a screen's job is to route the user, formatting the prompt is noise.

**The honest question:** *does the structure help the reader do something faster?*
If you can't name the reader's gain, don't add the structure.

---

## Step 3 — Decide: act, offer, or ask

This is the part agents get wrong. Match the response to the scope of the change.

| Situation | What to do |
|---|---|
| You are **authoring new text** and the shape is clear | **Just build it right.** Don't ask permission to use a heading. |
| You are **already editing that exact message** for another reason | **Do it**, and mention it in one line in your report. |
| The change touches text you **weren't asked to touch** | **Offer.** Name the file/message, the shape you spotted, and the gain. |
| The shape is clear but the **data source isn't** (columns exist only if you can get the fields) | **Ask**, with your proposed columns listed. |
| Restructuring would change **what the message says**, not just how it looks | **Ask.** Content decisions are the user's. |
| The bot's **Bot API version can't do it** | Say so, propose the fallback, don't silently degrade. |

### How to offer (wording that works)

Bad: *"I could improve the formatting."* — vague, unactionable, gets ignored.

Good — **name the message, the shape, and the win**:

> `handlers/orders.py:88` — the order summary sends 6 `Label: value` lines. That's
> a 2-column table (`Field | Value`), right-aligned amounts. Want me to convert
> it? Same strings, same handler.

> `/stats` sends a `<pre>` grid padded with spaces — it breaks on narrow phones.
> It's a real 4-column table (player × games/wins/points). Convert?

> The plan comparison in `texts/pricing.py` is prose ("Basic costs…, Pro
> costs…"). As a 3-column table it's scannable in one glance. Shall I?

Always state: **what stays untouched** (callback_data, handlers, i18n keys). The
main reason users decline a formatting offer is fear that it breaks routing.

### Batch your offers

If you found 12 candidates, do **not** ask 12 questions. Group them:

> Found 12 messages with table-shaped content. 3 are high-value (order summary,
> `/stats`, plan comparison), 9 are 2-line key/value pairs where a table would be
> overkill. Want me to do the 3?

Rank by reader gain, recommend a subset, let the user say "all" or "just those".

---

## Step 4 — Proactively surface the *other* wins too

While you have the text open, these are worth flagging in the same breath. They
cost the user nothing to hear and are usually invisible to them:

- **A message over 4096 chars** that will fail to send (or over 1024 in a
  caption) → needs splitting or a Rich Message.
- **An unescaped user value** interpolated into HTML/MarkdownV2 → a live
  `can't parse entities` bug (`security-and-escaping.md`).
- **A long operation with no feedback** → the bot looks frozen
  (`dynamic-feedback-and-streaming.md`).
- **A hardcoded string next to i18n'd siblings** → a localization hole.
- **A dead end with no back button** (`navigation-and-flows.md`).
- **The same action labelled differently on two screens**
  (`consistency-and-review.md`).
- **A destructive action with no confirmation step**.
- **A structured AI answer flattened into plain text** — the single biggest
  missed opportunity now that Rich Messages exist.

Report these as observations with a one-line fix each, not as a lecture.

---

## Worked detection examples

**Input:**
```
Your order #4821
Status: shipped
Items: 3
Total: €47.50
Delivery: 12 Aug
```
**Detected:** 4 consecutive `Label: value` lines → key/value table (2 cols,
`Field | Value`, values left, amount right). 1 record × 4 attributes ≥ 3 → table
justified. Header optional. **Action:** authoring new → just build it.

---

**Input:**
```
Basic — €5/mo, 10 projects, email support.
Pro — €12/mo, unlimited projects, priority support.
Team — €30/mo, unlimited projects, dedicated manager.
```
**Detected:** 3 records × 4 shared attributes (plan, price, projects, support),
repeated ` — ` separator, repeating currency → **4-column table**, price
right-aligned, plan column `is_header` per row. **Action:** if this text wasn't
in scope → offer.

---

**Input:**
```
Done ✅
```
**Detected:** nothing. 1 line, no repetition, no axes. **Action:** leave it.
Formatting this would be noise.

---

**Input:**
```
To register you need your passport, then fill the form,
then pay the fee, then wait for confirmation.
```
**Detected:** one axis (sequence), imperative verbs, "then" chain → **ordered
list**, or a **checklist** if the user tracks progress. Not a table — there are
no shared attributes per step. **Action:** build the list; mention checklist as
an option if the bot tracks state.

---

## Anti-patterns

- **Asking permission to do the obvious.** Don't ask whether a heading may be a
  heading while you're already writing the message.
- **Formatting for its own sake.** A table with one row. A heading over a
  two-line message. Bold on every second word.
- **Silently restructuring text you weren't asked to touch** — offer first.
- **Offering without specifics** ("I could improve this") — name message, shape,
  gain.
- **Ignoring the escape hatch** because "tables are the priority". Priority means
  *when structure exists*, not always.
- **Detecting only in new text.** Existing bots are where the wins are —
  `auditing-existing-bots.md`.
