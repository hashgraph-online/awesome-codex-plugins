# Portable output formats

Choose the format from the user's request and the capabilities currently
available in the host. The analysis contract is independent of the rendering
tool.

## Format selection

| Format | Use when | Minimum content |
|---|---|---|
| Markdown | Fast review, discussion, or no format specified | Concise findings, tables, recommendations, data-quality note |
| Document | Client, executive, or archival narrative | Executive summary, numbered tables/figures, caveats, methodology |
| Spreadsheet | BI handoff, filtering, or detailed reconciliation | Typed tables, data dictionary, formulas or derived-field definitions, notes |
| Dashboard | Interactive exploration materially improves the decision | Bounded embedded dataset, filters, accessible charts, methodology |

Do not hard-code a document, spreadsheet, visualization, or filesystem API.
Use the corresponding capability exposed by the current client. If the host
cannot create the requested artifact, provide the structured content and state
the limitation. Every save waits for the approval step in SKILL.md step 8: show
the destination, the contents, and whether buyer data is included, then get an
explicit yes.

## Audience adjustments

- **Internal operator:** lead with product priorities and concrete next checks;
  raw codes are appropriate.
- **Client:** lead with scope and outcomes; spell out codes, keep caveats near
  claims, and frame actions as recommendations.
- **Executive:** lead with material changes, high-impact products, and the top
  decisions; move detail after the summary.
- **Data handoff:** minimize narrative and expand schemas, definitions,
  provenance, and quality fields.

The numbers and definitions do not change with audience.

## Spreadsheet guidance

Use only tabs supported by the available data:

- `Summary`
- `Product_detail`
- `Reasons`
- `Dispositions_status`
- `Trend`
- `Fulfillment_centers`
- `Comments_redacted`
- `Prior_comparison`
- `Reimbursement_review`
- `Data_quality`
- `Data_dictionary`

Use stable column names, real numeric cells, explicit rate-method columns, and
source/join fields. Do not include sensitive raw comments, addresses, order IDs,
or document URLs unless they are necessary and the user approved them at the
save step.

## Document guidance

- Match the report-template order.
- Put units, denominators, date basis, and rate method beside the metric.
- Place charts next to the finding they support.
- Use captions and accessible color choices; do not rely on color alone.
- Keep detailed methodology and data quality available even when the executive
  section is short.

## Dashboard guidance

- Use normalized or aggregate data, not the raw report.
- Bound the embedded payload and long product tables.
- Provide accessible labels, table alternatives, and visible filter state.
- Define every metric and expose the rate method in labels or tooltips.
- Avoid runtime access to SP-API credentials or signed document URLs.
- Prefer a spreadsheet when the user needs complete row-level data rather than
  exploration.

Useful views include product return volume, rate versus denominator size,
reason or disposition distributions, and time trends. Include a view only when
the source supports it.

## Rerendering

When account, marketplace, channel, date window, source revision, and analytical
definitions are unchanged, reuse the validated normalized data and aggregates
for another format. State that the figures use the same analysis snapshot.

Reacquire or reparse when any scope field or source data changed. Do not claim
that two outputs match merely because their file names or nominal windows do.
