> The calls below are Candor MCP tool calls. Replace placeholders such as `TRANSACTION_ID` with values from earlier responses; where an `input` names an operation instead of showing an object, `candor_schema` lists its fields.

# Reading records

## Choose the read

- One known object or published read, such as
  `candor_get({"operation":"transactions.get","reason":"Read the transaction in question","args":{"transaction_id":"TRANSACTION_ID"}})`, `candor_get({"operation":"recurring.list","reason":"Read the recurring bills and income"})`,
  `candor_get({"operation":"goals.list","reason":"Read the saved goals"})`, `candor_get({"operation":"budget.status","reason":"Read this month's budget","args":{"period":"YYYY-MM"}})`.
- Rows from a dataset with filters: `candor_query({"dataset":"DATASET","reason":"Read the rows the question needs"})` with its
  filters. Check fields and filters first with `candor_schema({"dataset":"DATASET","reason":"Check the dataset's fields and filters"})`.
- Several datasets together for local analysis:
  `candor_snapshot({"datasets":["transactions","accounts"],"reason":"Build a local snapshot for analysis"})`.
- Period comparisons: `candor_changes({"reason":"Compare this month with last month"})`, which states both ranges and
  withholds totals when history is incomplete.
- An unfamiliar call: `candor_schema({"operation":"OPERATION_ID"})` returns its exact
  arguments.

## Pages and totals

- Every bounded read returns its rows, calculations, and pagination together
  under `data.page`. The calculations cover exactly the rows on that page.
- Continue only through the call in `next_actions`; replay it exactly. A
  cursor is bound to the filters that issued it.
- Before you state a total for a period, follow every continuation for it, or
  say the total covers only what you read.
- Keep raw pages out of your reply. As pages arrive, carry forward only
  counts, totals, and the few records you need next. If you can run code,
  save the pages and analyze them there.

## Coverage

- `financial_position.coverage` on the opening, and `candor_get({"operation":"coverage.get","reason":"Check which accounts and dates the records cover"})`,
  say which accounts report, from when, and how fresh. Observed first and last
  transactions are not the coverage boundary.
- A missing record is uncertainty, not hidden spending, income, or a
  preference.
- When a connected bank's sync is old for the question, `candor_connections({"operation":"sync.refresh","reason":"Refresh balances that are too old for the question"})` asks for new
  data; connecting new ones happens on the web. An account kept by hand has
  nothing to refresh: it is current through its `records_through` date, and
  newer records come from the person's next statement or export.
- A partial result carries a warning and its scope. Keep that limit in the
  answer instead of treating omitted records as zero.

## Visuals

`candor_visualize({"reason":"Show the overview"})`, `candor_visualize({"panel":"goals","reason":"Show the person their goals"})`,
`candor_visualize({"panel":"budget-status","period":"YYYY-MM","reason":"Show this month's budget"})`, `candor_visualize({"panel":"coming-up","reason":"Show upcoming bills"})`,
`candor_visualize({"panel":"cash-flow","reason":"Show cash flow"})`, `candor_visualize({"panel":"holdings","reason":"Show investment holdings"})`, and
`candor_visualize({"panel":"investments","reason":"Show investments over time"})` return a panel
as text context, structured data, and a View in Candor link. Hosts with MCP
Apps also draw it. Read the panel text before discussing it, pass the link
through, and never recalculate its values.

## Links

Use the `view_url` values Candor returns. A response URL opens the related
view; a record URL selects that record. Never build URLs from ids.
