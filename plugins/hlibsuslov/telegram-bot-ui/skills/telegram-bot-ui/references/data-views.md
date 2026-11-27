---
summary: "Showing numbers and records in a bot: choosing the surface, visual grammar, catalog of business interfaces, splitting long tables, widget data rules; read for tables, leaderboards, KPIs and reports."
verified: "2026-11-23"
bot_api: "10.5"
---

# Data views: tables, leaderboards, progress, KPIs and reports in a bot

## Contents

- [Tools](#tools)
- [1. Pick the surface](#1-pick-the-surface)
- [2. Visual grammar (H, one per bot)](#2-visual-grammar-h-one-per-bot)
- [3. Catalog: interfaces business and commercial bots need](#3-catalog-interfaces-business-and-commercial-bots-need)
- [4. When a table or notification does not fit one message](#4-when-a-table-or-notification-does-not-fit-one-message)
- [5. Widgets for data: rules that are not obvious](#5-widgets-for-data-rules-that-are-not-obvious)

How a bot shows numbers and records so a person gets the answer in one glance: which surface,
which layout, which symbols, and what to do when the data does not fit one message.
Tables in depth: `tables.md`. Limits and the generic splitter: `limits-and-splitting.md`.
Widget runtime and budget: `widgets.md`, `widget-design-system.md`.

Status markers: **API** = Bot API limit, **Guide** = Telegram guidance, **H** = heuristic of this skill.

## Tools

| Piece | What it gives |
|---|---|
| `examples/python/tgkit/dataview.py` | `number`, `money`, `delta`, `progress`, `sparkline`, `status`, `leaderboard`, `kpi_lines`, `rich_table_parts` (default), `table_parts` (`<pre>` fallback), `mono_lines` |
| `py -3 scripts/data_view.py spec.json [--json]` | the same as a CLI: ready parts with their lengths (spec format in the script's docstring) |
| Gallery widgets | `data-table` (sortable page of a report, totals, pages, full report on request), `leaderboard`, `job-progress`, `metrics-dashboard`, `receipt`, `order-tracker`, `schedule-calendar`, `slot-booking`, `price-ticker`, `task-checklist`, `shared-poll`, `rating-feedback` in `examples/widgets/` |

Check what you produce: `scripts/validate_rich.py` for Rich parts, `scripts/build_widget.py --strict`
and `scripts/preview_widget.py` for widgets.

## 1. Pick the surface

| Data | Surface | Why |
|---|---|---|
| 1-5 numbers or one status | regular message: KPI lines (§3.1) | readable in the notification preview |
| Records with shared columns, read once | **Rich Message table** (`tables.md`) | real table, reflows, quotable, exportable |
| Same, but the client or SDK has no Rich Messages | regular message with a `<pre>` grid (`table_parts`) | the fallback rung; log that it was used |
| A number that changes while the person watches (job, order, score, live price) | widget (`job-progress`, `order-tracker`, `leaderboard`) or one regular message edited in place | one bubble, no spam |
| A report the person browses: sort, page, filter | widget `data-table` + "Full report in chat" | the page fits 600 px; the whole report stays text |
| More than ~3 message parts, or for a spreadsheet | file (CSV/XLSX) with a one-screen summary in the caption | nobody reads part 7 of 12 |
| Channel post | Rich Message or regular text; widgets only where `widget-patterns.md` §13 allows | |

Every widget keeps a text alternative: a caption that states the main fact and a fallback keyboard
(Guide). Every table keeps its meaning without colour: status words stay next to the dots.

## 2. Visual grammar (H, one per bot)

- **Numbers.** Group thousands by the user's locale (`1,234` / `1 234`), the same number of decimals
  down a column, right-aligned. One unit per column, in the header ("Sum, €"), not in every cell.
  Money from minor units, never floats; Stars `250 ⭐`, grams as `1.25 GRAM` (`wallet-and-ton.md`).
- **Change.** `▲ 12%` / `▼ 3.5%` / `= 0%`, with the period it compares ("vs yesterday"). Green/red only
  in widgets and only together with the arrow; "down" is not always bad (latency, refunds): say it.
- **Status.** Dot plus word: `🟢 Paid`, `🟡 Pending`, `🔴 Refunded`, `⚪ Cancelled`. Four states at most
  per view; add a legend line when a mark is not self-evident.
- **Ranks.** `🥇 🥈 🥉` then `#4`; ties share a rank; the viewer's own row in bold, and when it is
  below the top, a `⋯` line and their row (`leaderboard`).
- **Progress.** `▰▰▰▰▱▱▱▱▱▱ 40%` (10 cells; `█░` or `●○` as variants, one style per bot). Never 100%
  before the work is done, never 0% once anything is done; show the count next to it (`412 / 1 000`)
  and an ETA only when it is honest.
- **Trend in text.** `▁▂▃▅▇▆▅` sparkline plus the last value; a real chart only in a widget
  (`_kit/chart.js`) or an image.
- **Time.** Absolute in the user's time zone for events (`Today 14:05`), relative for freshness
  (`updated 3 min ago`). Every report says "as of" when the data is not live.
- **Spacing.** Title line, one blank line, the data block, one blank line, the footer (totals,
  legend, next step). No decorative emoji on every line; one accent per title at most.
- **Truncation.** Clip long names with `…` in tables; never clip numbers. A hidden column is said
  ("2 columns hidden: open the full report").
- **States.** Every view has empty ("No orders today yet"), loading (typing or a progress line),
  error (what failed, what to do), and stale (as-of time in grey) states. Zero is a value, not an
  empty state: "0 refunds" is good news.

## 3. Catalog: interfaces business and commercial bots need

Each entry: what it answers, the text form, the Rich or widget form, how it overflows. The
notification around the data (header, sound, lifecycle) follows `message-patterns.md`.

1. **KPI summary / daily digest.** "How are we doing?" Text: 3-6 `Label: **value** ▲ 8%` lines
   (`kpi_lines`) under a dated title; one line of conclusion first ("Revenue up, refunds normal").
   Widget: `metrics-dashboard`. Overflow: never; move the rest to a "Details" button.
2. **Report table** (orders, invoices, payouts, leads, shipments). Rich table, totals row, numeric
   columns right-aligned, compact on phones with 4+ columns. Widget: `data-table` page. Overflow: §4.
3. **Leaderboard / ranking** (sales reps, quiz, referrals, loyalty). Text: top 10 + the viewer.
   Widget: `leaderboard` (shared). Overflow: top N only; "Your place: #57" is the line people want.
4. **Goal progress** (monthly target, fundraising, quota, course completion). Text: title, bar,
   `€8,400 / €12,000`, days left. Several goals: one bar per line with the same width.
5. **Job progress** (export, import, report generation, upload). One message edited in place or the
   `job-progress` widget: stage list `✓ ● ○`, bar, ETA, Cancel. Never one message per percent.
6. **Order or delivery tracker.** Timeline: `✓ Paid 10:02`, `✓ Packed 12:40`, `● On the way`,
   `○ Delivered`; the current step in bold; widget `order-tracker`. Overflow: collapse past steps.
7. **Receipt / invoice.** Items table (name, qty, sum), subtotal, tax, total in bold, status word,
   number and date; widget `receipt`. A receipt is never split: long carts go to a file.
8. **Comparison** (plans, products, offers). Rich table with options as columns and features as
   rows, `✓` / `—`, the recommended column named in the title, not by colour alone.
9. **Price list / catalog.** Rich table or paged list (`63-search-and-long-lists` recipe); price
   right-aligned; "from €9" when it varies. Widget for browsing: `product-card`.
10. **Balance and statement** (wallet, bonus points, prepaid minutes). Balance in the title,
    then transactions newest first: date, description, `+€20.00` / `−€4.50`, running balance.
    Recipes 07, 86. Overflow: last 10 + "Statement for the month" as a file.
11. **Schedule / slots / shifts.** Day headers, `09:00–10:00  Free` rows; widget `schedule-calendar`
    or `slot-booking`. Overflow: one day per page.
12. **Queue position / waiting time.** `You are #4 in line · ~12 min`, edited as it moves; recipe 87.
13. **Alert / incident.** First line: severity mark and what is wrong; then since when, impact,
    one action button. Follow-ups reply to the first alert; the resolution edits it (recipe 47).
14. **Inventory / stock.** Table with item, on hand, reorder level, status (`🔴 Low`); sorted by
    urgency, not by name. Overflow: low-stock rows first, the rest in the file.
15. **Funnel / conversion.** Lines `Visited 1 200 → Cart 310 (26%) → Paid 95 (31%)`, or one bar per
    step of the same width so they compare. Widget only for interaction.
16. **Poll and rating results.** One bar per option with the count and percent; the viewer's choice
    marked; widget `shared-poll` / `rating-feedback`.
17. **Checklist / tasks.** `- [x]` Rich checklist or the `task-checklist` widget; done count in the
    title (`3/7 done`).
18. **Countdown / deadline.** Absolute deadline plus "in 2 h 15 min"; widgets derive the timer from
    a timestamp, never count (`widget-patterns.md` §7).

## 4. When a table or notification does not fit one message

API: a regular message holds "1-4096 characters after entities parsing"; a Rich Message 32 768 characters and
500 blocks (every table row is a block) and 20 table columns. Ladder (H), first that fits wins:

1. **Shrink.** Drop columns the reader does not need for this decision; compact table; shorter labels.
2. **Summary + top N + "Show all".** A notification states the outcome in its first line and shows
   the top 5-10 rows; a button opens the rest (widget page, Rich report, or file).
3. **Split by rows** (`rich_table_parts`, fallback `table_parts`): break only between rows, repeat
   the header on every part, title `Orders (2/3) · continued`, the summary only on part 1, totals
   and legend only on the last part. Send the parts in order; **parts 2..n with
   `disable_notification: true`** so the person gets one ping; the keyboard goes on the last part.
4. **More than ~3 parts: a file** (CSV) with the summary in the caption, or the `data-table` widget
   with paging. Never send 10 messages for one report.

When the report is refreshed, edit the parts in place; if the number of parts changes, edit what
exists, then send or delete the difference, and keep the keyboard on the last part.
Wide data (more than ~5 columns on a phone): transpose (one record per block of `Label: value`
lines) or split by columns with the key column repeated in each table.

## 5. Widgets for data: rules that are not obvious

- State carries one page (≤ ~900 bytes), not the report; the bot keeps the data and answers
  `pg:<n>` by editing `chat_data` (`h_data_table.py`). Sorting a page is local, never a request.
- 600 px height and no scrolling inside a widget (Guide): at most 8 one-line rows a page (the
  `data-table` widget pages by 8) with a header, totals and a pager. On ≤ 280 px drop optional
  columns (`[label, kind, 1]` in `data-table`).
- Controls are real buttons with a visible label: widgets keep `aria-*` but it does nothing
  (`widget-design-system.md`). Arrows are drawn (SVG chevrons centred in a 44 × 36 button), not
  text glyphs, and mirror in RTL.
- `tabular-nums` for numbers, `Intl.NumberFormat` for every number and money value (`K.nf`, `K.money`).
- The whole report always has a text path: "Full report in chat" sends Rich parts (§4), the
  fallback keyboard offers the same.
