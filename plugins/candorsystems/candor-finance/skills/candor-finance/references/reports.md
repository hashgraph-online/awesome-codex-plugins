> The calls below are Candor MCP tool calls. Replace placeholders such as `TRANSACTION_ID` with values from earlier responses; where an `input` names an operation instead of showing an object, `candor_schema` lists its fields.

# Reports

A report is a page you save for the person in Candor. They open it on the
Reports tab, on the web and in the app, labelled as written by you, instead
of a page left behind in a chat. Use one when your answer is something they
will come back to or want to explore, whether or not they asked for a page:
a dashboard of what they watch (live), a projection with controls they can
change, or a review of a period to keep (snapshot). Link it in your answer.
A one-off answer belongs in the chat; a follow-up belongs in a note.

- **Live** reads Candor's figures each time they open it. Compute relative
  dates in the page (this month, the last 90 days).
- **Snapshot** freezes the figures at the save, for a review of what
  happened. List every read the page makes in `reads`, each as its name and
  arguments (`{ "name": "get", "arguments": { "operation": "goals.list" } }`),
  with fixed dates; Candor runs them as part of the save and the page gets
  those stored results.

## The page

One complete HTML document, from a doctype to `</html>`, up to 500 KB. It
runs in a sandbox with no network, so inline every script, style, and image;
a library you need (D3, say) goes inline too. Candor adds a runtime before
your code:

Start from the starting page below and change what the person asked for.

- `candor.query(arguments)`, `candor.get(arguments)`,
  `candor.snapshot(arguments)`, `candor.changes(arguments)`, and
  `candor.visualize(arguments)` read exactly what the matching Candor read
  returns to you: a dataset query, a read operation such as goals.list, a
  multi-dataset snapshot, a period comparison, or a dashboard panel. Each
  takes that read's own arguments, without a reason, and returns the same
  result, so build the page against results you have already seen in this
  conversation: rows are under `result.data.page`, and panels under
  `result.panels`. `candor.callServerTool` returns the raw MCP result, with
  that same envelope in `structuredContent`.
- `candor.watch("query", arguments, onResult)` (or "get", "visualize", and
  so on) calls `onResult` with the first result and again whenever the
  figures change. Use it in live pages that should move with the data.
- `candor.money(text)` turns an amount as Candor writes it ("USD -1,234.56")
  into a number for a chart. Keep the original text for anything you print.
- `candor.render(element, result)` draws a `candor.visualize` result with the
  dashboard's own panels. A panel brings its own surface and heading, so put
  it straight in the page or beside a section, never inside one.
- `candor.chart(element, spec)` draws a chart with Candor's chart library
  (below).
- Link to Candor wherever a figure has detail behind it, with a plain link by
  path or `view_url`: `/transactions?q=Whole%20Foods`,
  `/transactions?category=Dining`, `/budget`, `/recurring`, `/goals`,
  `/accounts`, another report at `/reports/<report_key>`. They open in place.
  A link outside Candor asks the person first, and `#section` links scroll the
  page. `candor.openLink(url)` does the same from a script. Never set
  `location` yourself: Candor stops a page that navigates away.

Never type an amount the reads can supply; read it, so the page cannot drift
from the records. Figures you worked out yourself (a projection, a what-if)
can sit in the page; say they are yours and state the assumptions.

## Looking like Candor

Write plain semantic HTML and Candor styles it like the dashboard, in its font
and colors, with no classes. Candor shows the report's title and who wrote it
above the page, so write neither. In order:

- One `<p>` first, plain text on what the page shows. Candor shows it as the
  page's caption.
- A `<dl>` of at most four terms: each `<dt>` a label, its `<dd>` the figure,
  an optional second `<dd>` a short note. This is the panel the page opens on,
  as every Candor page does. The first term leads, large, so put the number
  the page is about first. Leave a figure empty until its read lands: it holds
  its place, cents step back, and a value that changes later tints as the
  dashboard's do.
- A `<section>` with an `<h2>` is a panel for a chart or table. A `<div>` of
  sections sets them side by side, matched in height.
- Tables, lists, and links work as they do anywhere.

Optional refinements: `class="num"` on number cells, `up` and `down` for money
in and out, `<p class="note">` for a caveat, `<p class="source">` for a closing
line on what the page reads, and `<div class="bars">` of `bar-label`,
`bar-track` holding `bar-fill` (its width the share), and `bar-value` for a
ranked list.

Add your own styles only for layout the blocks do not cover, and leave colors,
fonts, and the page background to Candor. Keep widths fluid (the page is as
wide as the person's window, down to a phone) and give a chart a fixed pixel
height.

A save is refused when the page cannot work in its sandbox: anything loaded by
address, network calls, code that navigates the page, `vh` units, or a script
that does not parse. The refusal says what to fix. A saved page's warnings say
what would make it read better, and `reports.get` shows `page_error` when the
page threw for the person.

## A starting point

```html
<!doctype html>
<html><head><title>Spending this month</title></head>
<body><main>
  <p>Where the money went so far, against the budget.</p>
  <dl>
    <div><dt>Spent</dt><dd id="spent"></dd></div>
    <div><dt>Budget left</dt><dd id="left"></dd></div>
  </dl>
  <section><h2>By category</h2><div id="chart"></div></section>
  <p class="source">Reads Candor's budget each time you open it.</p>
</main>
<script>
  candor.watch("get", { operation: "budget.status" }, (result) => {
    const budget = result.data;
    // Fill #spent and #left from the amounts budget.status returned, then
    // draw its lines with candor.chart (below).
  });
</script>
</body></html>
```

## Charts

Draw every chart with `candor.chart`, even when the person names a library:
it is already on the page, needs nothing copied in, and looks like Candor. Do
not hand-draw bars in SVG or CSS, and do not look for a copy of the library.

`candor.chart(element, spec)` draws bar, line, and area charts, mixed in
one chart, with the dashboard's conventions: a hairline grid, rounded bars,
a tooltip on every mark, and Candor's colors.

- `data`: rows of plain numbers; `x`: the key each row is placed by.
- `series`: each `{ key, label, kind, color, stack, axis, dashed }`. `kind`
  is bar, line, or area (the chart's `type` by default). `color` is a token,
  chart-1 to chart-8, flow-in, flow-out, or muted, or any CSS color. Series
  with the same `stack` stack. `axis: "right"` uses a second axis.
- `y` and `y2`: `{ format: "money" | "percent" | "number", currency, hide,
  zero }`. Axes and tooltips read as money unless `format` says otherwise.
- `layout: "vertical"` draws horizontal bars with categories down the side.
  Bars for named things turn that way on their own on a phone.
- `referenceLines`: `[{ y, label }]` or `[{ x, label }]`, such as a budget.
- `height` in pixels (280 by default), `legend`, `smooth`.

Spending by month, stacked by category, against a monthly budget:

```js
candor.chart(document.getElementById("months"), {
  type: "bar",
  data: months, // [{ month: "Aug", groceries: 612, dining: 240, shopping: 180 }, ...]
  x: "month",
  series: [
    { key: "groceries", label: "Groceries", stack: "spend", color: "chart-2" },
    { key: "dining", label: "Dining", stack: "spend", color: "chart-6" },
    { key: "shopping", label: "Shopping", stack: "spend", color: "chart-3" },
  ],
  y: { format: "money" },
  referenceLines: [{ y: 1200, label: "Budget" }],
});
```

Income and spending as bars, with the savings rate as a line on its own
axis:

```js
candor.chart(document.getElementById("flow"), {
  data: cashflow, // [{ month: "Aug", income: 6210, spending: 5720, rate: 0.08 }, ...]
  x: "month",
  series: [
    { key: "income", label: "Income", kind: "bar", color: "flow-in" },
    { key: "spending", label: "Spending", kind: "bar", color: "flow-out" },
    { key: "rate", label: "Savings rate", kind: "line", axis: "right", color: "chart-1" },
  ],
  y: { format: "money" },
  y2: { format: "percent" },
});
```

Top merchants as horizontal bars:

```js
candor.chart(document.getElementById("merchants"), {
  layout: "vertical",
  data: merchants, // [{ name: "Trader Joe's", spent: 412 }, ...]
  x: "name",
  series: [{ key: "spent", label: "Spent", color: "chart-1" }],
  y: { format: "money" },
  height: 40 * merchants.length + 40,
});
```

A projection with a range, as an area and two lines:

```js
candor.chart(document.getElementById("projection"), {
  type: "area",
  data: years, // [{ year: 2027, low: 41000, likely: 48000, high: 55000 }, ...]
  x: "year",
  series: [
    { key: "high", label: "Strong markets", color: "chart-4" },
    { key: "likely", label: "Likely", kind: "line", color: "chart-1" },
    { key: "low", label: "Weak markets", kind: "line", dashed: true, color: "muted" },
  ],
  y: { format: "money", zero: false },
});
```

For anything the spec does not cover, `candor.React`, `candor.Recharts`, and
`candor.ui.ChartContainer` are Candor's own chart library, and
`candor.mount(element, node)` draws a React element:

```js
const { createElement: h } = candor.React;
const { ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, Tooltip } =
  candor.Recharts;
candor.mount(
  document.getElementById("scatter"),
  h(candor.ui.ChartContainer, { config: {}, style: { height: 300 } },
    h(ResponsiveContainer, { initialDimension: { width: 320, height: 300 } },
      h(ScatterChart, null,
        h(XAxis, { dataKey: "day", name: "Day of month" }),
        h(YAxis, { dataKey: "amount", name: "Amount" }),
        h(Tooltip, null),
        h(Scatter, { data: purchases, fill: "currentColor" }))))
);
```

## Preview

`reports.preview` takes the same body as `reports.save`, draws the page in its
real sandbox with the person's figures, and saves nothing. You get pictures of
it at desktop and phone widths, what its code threw, reads that failed,
addresses the sandbox refused, whether it scrolls sideways on a phone, and its
text as drawn. It takes a few seconds, so use it when you built or changed a
page and want to see it, then fix what you find and save.

## Save

```text
candor_write({
  "operation": "reports.save",
  "reason": "Keep the person's spending page",
  "input": {
    "report_key": "monthly-spending",
    "title": "Spending this month",
    "summary": "Where the money went this month by category, against the budget.",
    "mode": "live",
    "html": "<!doctype html><html><head><title>Spending this month</title></head><body><main class=\"report\"><h1>Spending this month</h1><div id=\"spending\"></div></main><script>candor.watch(\"visualize\", { panel: \"spending\", preset: \"1m\" }, (result) => candor.render(document.getElementById(\"spending\"), result));</script></body></html>"
  }
})
```

Saving the same `report_key` again adds a revision and keeps the earlier
ones; reuse the key when you update a report. The `summary` is what you and
later runs read instead of the page, so say what it shows and what it
concluded. The opening lists every saved report; check it before you make a
new one that repeats an old one. Pass the returned link to the person in one
line.

## Read, archive, restore

```text
candor_get({
  "operation": "reports.list",
  "reason": "See which reports exist"
})
candor_get({
  "operation": "reports.get",
  "reason": "Read the saved report",
  "args": {
    "report_key": "REPORT_KEY"
  }
})
candor_write({
  "operation": "reports.archive",
  "reason": "The person no longer needs it",
  "args": {
    "report_key": "REPORT_KEY"
  }
})
candor_write({
  "operation": "reports.restore",
  "reason": "The person wants it back",
  "args": {
    "report_key": "REPORT_KEY"
  }
})
candor_write({
  "operation": "reports.pin",
  "reason": "The person wants it in the sidebar",
  "args": {
    "report_key": "REPORT_KEY"
  }
})
candor_write({
  "operation": "reports.unpin",
  "reason": "The person no longer needs it there",
  "args": {
    "report_key": "REPORT_KEY"
  }
})
```

`reports get` returns the page source only with `include_html`. A report
marked `blocked` tried to leave its page and was stopped; read its source,
remove whatever navigates away, and save a new revision.
