# Tables — the flagship capability

> **Read this first for any structured content.** Since Bot API 10.1 introduced
> Rich Messages, a bot can send a **real Telegram table** (the same element the
> user-facing Rich Text Editor produces — see the official blog *"Text Editor,
> Communities & Ephemeral Messages"*). Tables are this skill's **first-priority**
> output: whenever data has rows and columns — comparisons, schedules, prices,
> scores, key/value facts, status lists — reach for a table before anything else.
>
> **Last verified against official docs: 2026-11-15** (Bot API 10.4, 9 Nov
> 2026). Field names of `InputRichBlockTable` and `RichBlockTableCell` are checked
> against the local catalog (`py -3 scripts/tg_api_lookup.py show RichBlockTableCell`).
> See `official-sources.md`.

## When a table is the right call

Reach for a table when the content is **two or more parallel records with shared
attributes**, or **label → value pairs** you want aligned. Examples: a price
list, a match schedule, a feature comparison, quiz results, a config diff, a
leaderboard, an order summary. If the content is genuinely one flat sentence or a
single status line, use the escape hatch (plain/regular message) — see
`format-selection.md`. Everything with structure defaults to a table.

**Do not fake tables.** A monospace `pre` block with hand-aligned spaces is a
*fallback of last resort* (see the bottom of this file), never the default. Real
tables reflow correctly on every client, export cleanly, and stay aligned.

## The three ways to build a table (pick by how the data arrives)

All three are carried inside **one** `InputRichMessage` and sent with
`sendRichMessage` (or streamed with `sendRichMessageDraft`, or replaced with
`editMessageText` + `rich_message`). `InputRichMessage` holds **exactly one** of
`markdown`, `html`, or `blocks`.

| Data source | Build path | Field |
|---|---|---|
| Text the model/author writes naturally | **Rich Markdown** pipe table | `markdown` |
| Server-side template with precise tag control | **Rich HTML** `<table>` | `html` |
| Rows from a DB / API / CMS / AST — programmatic | **Explicit blocks** `InputRichBlockTable` | `blocks` |

Prefer **blocks** when the rows come from data (no string-escaping pitfalls, no
parser ambiguity). Prefer **Rich Markdown** for naturally-authored answers.

### 1. Rich Markdown (GitHub-style pipe table)

The first row is the **header**; the `---` separator row sets per-column
alignment (`:--` left, `:-:` center, `--:` right).

```python
table = (
    "| Team        | Played | Won | Points |\n"
    "|:------------|-------:|----:|-------:|\n"
    "| Alpha       |     10 |   7 |     21 |\n"
    "| Bravo       |     10 |   6 |     19 |\n"
    "| Charlie     |     10 |   4 |     13 |\n"
)
bot.send_rich_message(chat_id=chat_id, markdown=table)   # exact SDK call varies
```

- Header cells render **bold** automatically — do not also bold them by hand.
- Escape a literal `|` inside a cell as `\|`; keep cell text on one line (use
  `<br>`-equivalent only if the project's Rich Markdown supports it — *verify*).
- Numbers → right-aligned columns; labels → left. See alignment note below.

### 2. Rich HTML (`<table>` with real header cells)

Use `<th>` for header cells and `<td>` for body cells — never fake a header with
bold `<td>`. Whitelist tags/attributes exactly as for regular HTML
(`security-and-escaping.md`); escape `< > &` in every dynamic cell value.

```html
<table compact>
  <caption>Standings after round 10</caption>
  <tr><th>Team</th><th>Played</th><th>Won</th><th>Points</th></tr>
  <tr><td>Alpha</td><td align="right">10</td><td align="right">7</td><td align="right">21</td></tr>
  <tr><td>Bravo</td><td align="right">10</td><td align="right">6</td><td align="right">19</td></tr>
</table>
```

Put the string in `InputRichMessage.html`. Official tag set (Bot API page, *Rich HTML
style*, checked 2026-11-15) **[API]**: `<table>` with the flags `bordered`, `striped`,
`compact`; an optional `<caption>`; `<tr>` **directly inside `<table>`** — there is no
`<thead>` or `<tbody>`; `<th>` / `<td>` with `colspan`, `rowspan`, `align`
(`left|center|right`) and `valign` (`top|middle|bottom`).

**Budget:** every table row counts toward the **500-block** Rich Message limit
(together with nested blocks, list items, quotations and details blocks), and a table
has at most **20 columns** **[API]**. A 400-row table leaves almost nothing for the
rest of the message: split long tables or page them, long before the 32,768-character
limit is in sight.

### 3. Explicit `InputRichBlockTable` blocks (programmatic — preferred for data)

Build the table as typed objects — no string escaping, no parser ambiguity. This
is the safest path when rows come from a database, API, or CMS.

```python
# Shape checked against the Bot API 10.4 catalog (2026-11-15):
# InputRichBlockTable{type, cells: Array of Array of RichBlockTableCell,
#   is_bordered?, is_striped?, is_compact?, caption?}
# RichBlockTableCell{text?: RichText, is_header?, colspan?, rowspan?, align, valign}
def cell(text, header=False, align="left"):
    c = {"text": text, "align": align, "valign": "middle"}
    if header:
        c["is_header"] = True    # type True: send true or omit it, never false
    return c

table_block = {
    "type": "table",
    "is_compact": True,                      # 10.3: tighter cells, better on phones
    "cells": [                               # rows are plain arrays of cells
        [cell("Team", header=True),
         cell("Played", header=True, align="right"),
         cell("Points", header=True, align="right")],
        *[
            [cell(t["name"]),
             cell(str(t["played"]), align="right"),
             cell(str(t["points"]), align="right")]
            for t in standings
        ],
    ],
}
params = {"chat_id": chat_id, "rich_message": {"blocks": [table_block]}}
# send with sendRichMessage; check it offline first:
#   py -3 scripts/validate_payload.py --method sendRichMessage params.json
```

- **`is_header: true`** marks header cells; clients render them bold. This is the
  *semantic* header — always use it instead of manual bold.
- **`align` and `valign` are required** on every cell.
- Cell `text` is `RichText`: a plain string, or rich nodes (bold, link, code,
  custom emoji…) — not a list of blocks.

## Cross-cutting table rules (apply in all three paths)

### Header row
Every table gets a header row. Mark it semantically: `is_header: true` (blocks),
`<th>` (Rich HTML), or the first row above `---` (Rich Markdown). Never simulate a
header with bold body cells — it breaks export and screen readers.

### Alignment
Set `align` per column: **numbers/currency/dates right, text left, short flags
center**. Right-aligned numeric columns are the single biggest readability win in
a Telegram table. Vertical alignment (`top`/`middle`/`bottom`) exists on cells if
the content is multi-line *(verify field name)*.

### Spanning (merged cells)
Use `colspan`/`rowspan` (cell field `> 1`) for merged cells — e.g. a group title
across the top — instead of padding with empty cells. *(Verify the exact field
names.)*

### Column cap
There is a per-table **column limit** (official: 20 columns, Rich Message Limits, verified 2026-11-12). If data is wider, transpose it (attributes as rows) or split into
two tables with a shared key column. Never silently drop columns — if you cap,
say so.

### Splitting a long table across messages
A Rich Message holds up to **32,768 characters**, so most tables fit in one. If a
table is genuinely too long:

- **Never split mid-row.** Break only between rows.
- **Repeat the header row** at the top of each continuation part so every part is
  self-describing.
- Keep the header physically with its body (don't strand a header at the end of
  part 1). See `limits-and-splitting.md` for the splitter and part-numbering.
- `tgkit.dataview.rich_table_parts` (or `scripts/data_view.py`) does this split, with the
  summary on part 1 and totals on the last; the ladder before splitting and the catalog of
  business data views: `data-views.md`.

### Escaping cell content
One escaper per format (`security-and-escaping.md`):
- **Rich Markdown cell:** escape `|` → `\|`; escape any Markdown-active chars in
  user text; keep to one logical line.
- **Rich HTML cell:** escape `<`, `>`, `&`; whitelist any inline tags you allow.
- **Blocks:** no escaping needed for plain text — that's the point; only apply the
  matching escaper if a cell embeds inline markdown/HTML.

## Data → table recipes

- **Key/value facts** (order summary, profile, config): two columns, left label
  (header optional or a single "Field | Value" header), values right- or
  left-aligned by type. Consider one header row `Field | Value`.
- **List of records** (standings, prices, schedule): one column per attribute,
  one row per record, numeric columns right-aligned.
- **Comparison** (plan A vs B vs C): first column = feature (row header via a
  leading `is_header` cell per row *(verify row-header support)*), one column per
  option, ✓/✗ or values in cells.
- **Diff / before-after:** three columns — item, before, after — with changed
  cells emphasized (bold inside the cell).

## Fallback ladder when Rich Messages are unavailable

Tables are the goal, but degrade explicitly and logged — never silently
(`errors-and-fallbacks.md`):

1. **Rich table** (`sendRichMessage` + markdown/html/blocks) — the default.
2. If the project's Bot API version is **below 10.1** or the SDK can't reach the
   rich methods (`sdk-compatibility.md`): send a **regular message** with a
   monospace `pre` block containing a space-aligned ASCII table. Compute column
   widths in **UTF-16 code units**; pad with spaces; keep it under 4096 chars and
   split by whole rows if needed.
3. If even that is too wide for small screens: emit a **key/value list**
   (`Label: value` lines grouped per record) instead of a cramped grid.

Always log which rung was used and why. Do not claim "sent a table" when the
fallback shipped a monospace block — report what actually went out.

## Verify before you ship

- Open the official **`InputRichBlockTable`** / **Rich message formatting
  options** page and confirm: the type discriminator, the row/cell field names,
  `is_header`, `align`, `colspan`/`rowspan`, and the real column cap.
- Confirm the project's SDK exposes `sendRichMessage`/`InputRichMessage` (or wrap
  the raw Bot API method — `sdk-compatibility.md`).
- Test render on **mobile and desktop** and after an **export** (see
  `testing-playbook.md`) — a table that looks fine on desktop can wrap badly on a
  narrow phone.

## Compact tables

10.3: `is_compact` (`<table compact>`) shrinks cell padding. Use it for dense numeric tables on
phones (≥ 4 columns, short values); keep the normal padding for 2–3 column tables people read
slowly. It changes spacing only — headers, alignment and the 20-column limit still apply.
