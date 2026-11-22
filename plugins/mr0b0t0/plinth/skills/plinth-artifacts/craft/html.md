# Craft: pages and dashboards (type html)

How to make an HTML page or a dashboard read well and look finished. The page contract in
SKILL.md still holds: a real title, both color schemes, phone width, pinned allowlisted scripts,
no requests to other hosts.

## Plan before you build

- Name the reader and the decision the page helps them make. Write the finding in one sentence
  with its number ("Signups doubled after the March launch, to 4,210 a week"). That sentence goes
  under the title, before anything else.
- **Summary before detail.** The headline numbers first, then the one chart that carries the
  finding, then the breakdowns, then the table people look things up in. Someone who reads only
  the first screen should leave with the answer.
- **Size it to the ask.** One question gets one chart and a sentence, not a dashboard. Leave out
  sections nobody asked for and offer them in your reply.

## Every number from a dataset

- Put the rows the page draws inside the page, in a `<script type="application/json">` block, and
  draw every figure, chart and table from them in code. Totals, shares and changes are computed
  from those rows, never typed in by hand, so the page and its data cannot disagree.
- Use only data the person gave you or you read from a source. Never invent a figure, a trend or
  sample rows to fill a chart. When data is missing, the page says so where the figure would be,
  and your reply says so too.
- Say where the numbers come from and how fresh they are, in a line under the title or at the foot
  ("Source: billing export, 18 Nov 2026"), with a link when there is one.
- Label units everywhere (EUR, %, hours) and name the period once (calendar or fiscal, and the
  time zone when it matters).

## KPIs

- A KPI tile is a short label, the value large, and its comparison with a sign and the period it
  compares with ("+12% vs October"). A color for up or down is fine next to the sign, never instead
  of it.
- Three to five tiles in a row that wraps to two columns at phone width. Use tabular figures
  (`font-variant-numeric: tabular-nums`) and round to what the reader needs (1.2 M, not
  1,203,447.33).

## Charts

- **Pick the chart by the question.** Change over time is a line. Comparing items is a bar chart,
  sorted by value. Parts that add up to a whole are a stacked bar (a pie only for two or three
  parts). A distribution is a histogram, two measures of the same items a scatter. Values people
  look up one by one are a table, not a chart.
- **Title the chart with what it shows or its finding**, not a field name.
- Bars start at zero. Label lines and bars directly where they fit, and keep a legend only for more
  than about four series.
- **One accent color** for what matters, muted greys for context. At most about six series
  colors, told apart by lightness as well as hue, and the same series in the same color on every
  chart of the page.
- Every chart that plots values shows the exact value on hover and on tap, in a tooltip that stays
  inside the page. Axis and tick labels are at least 12 px.
- **Charts follow the theme.** Read their colors from your CSS custom properties and draw again
  when `matchMedia("(prefers-color-scheme: dark)")` changes: canvas libraries such as Chart.js and
  Plotly do not read CSS variables on their own.
- **Size charts from their container** (`clientWidth`, a `ResizeObserver`), never a fixed pixel
  width, and draw again on resize. At phone width use fewer ticks, put the legend under the chart
  and shorten the labels.

## Tables

- Numbers right-aligned in tabular figures, text left-aligned, units in the header, rows sorted by
  what readers scan for (newest first for dated rows, largest first for amounts).
- A long or wide table gets a sticky header and a scroll box of its own.

## Layout and look

- One column of content up to about 1,100 px wide, centred; cards in a grid that falls to one
  column on a phone.
- Four or five type sizes for the whole page. Body text 15 to 16 px, line height 1.4 to 1.6 for
  prose.
- Text has 4.5:1 contrast against its background in both themes (3:1 for text 24 px and up, chart
  marks, icons and control borders).
- Real controls: `<button>`, `<a href>`, `<input>` with a `<label>`, touch targets of at least 44 px
  and a visible focus ring.
- Give the parts people will talk about (cards, charts, sections) an element of their own with an
  `id`, so a comment pins to them. For points inside a canvas chart, see "Comments from the page"
  in SKILL.md.
- Loading, empty and error states say what happened, never a blank box.
- When the person has a design system, read it first and build with its tokens ("Design systems"
  in SKILL.md).

## Handing over

- If you can open the page, check a figure or two against the data, and look at it 360 px wide and
  in dark mode.
- In your reply: what the page shows, what you assumed (periods, currency, what you left out), and
  where the data came from. After an update, give the old and the new value of every headline
  figure that changed, above all the ones nobody asked about.
