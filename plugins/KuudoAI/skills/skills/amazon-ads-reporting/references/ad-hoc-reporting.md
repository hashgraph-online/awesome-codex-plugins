# Ad-hoc unified/v1 reporting

Use this path when the user specifies metrics, dimensions, or filters instead of a named report in [the report catalog](report-catalog.md). A casual name that uniquely matches a catalog row still uses the catalog template.

## Define the grain first

Resolve these before selecting metrics:

- advertiser account and marketplace scope;
- reporting period and time grain;
- ad product, if the result should be product-specific;
- level-of-detail dimensions such as campaign, ad group, target, audience, placement, or product;
- requested metrics and attribution semantics;
- desired output format.

Ask only for information that changes the request. If a phrase has multiple material interpretations—such as “sales,” “conversion rate,” or “keyword”—show the alternatives and let the user choose.

## Discover fields from the current catalog

Query the live reporting-field catalog rather than relying on memorized names. Search by business concept, inspect the candidate field’s definition and type, and filter candidates against the dimensions already chosen.

Some Amazon Ads integrations expose field-catalog or field-validation operations; discover the available schema and use them when present. When the integration has none, Amazon's Reporting API v1 Dimensions and Metrics documentation is the catalog, and CreateReport validates the list itself: a bad list gets a 400 that names each problem (for example `400005` unknown field, `400004` incompatible fields, `400006` missing required field) and creates no report.

Prefer fields whose documented attribution window and grain match the request. Similar-looking metrics can differ by click/view attribution, promoted/halo products, new-to-brand scope, or denominator.

## Assemble a valid field list

A request needs:

| Requirement | Decision |
|---|---|
| Time | Exactly one supported time dimension, such as daily, weekly, monthly, or summary/date-range grain |
| Level of detail | At least one supported grouping dimension |
| Metrics | At least one compatible metric |
| Currency | Include the catalog-required currency dimension for monetary metrics |

Include stable identifiers beside display names when the result will be joined, persisted, or acted on. Add `adProduct.value` as a field or filter when product identity matters.

Filters use the canonical singular `query.filter` shape. A single predicate is wrapped in `on`; composite filters use the boolean structure supported by the current schema. Validate operator names and value types against that schema.

## Validate, split, and revalidate

Validate the complete field list before submission. Treat these outcomes distinctly:

- **Unknown field:** inspect current alternatives and confirm semantic equivalence before substituting.
- **Missing requirement:** add the required time, level-of-detail, metric, or supporting field.
- **Incompatible pair:** remove a field or split the request into compatible reports.
- **Unsupported filter:** revise the filter without changing the requested business scope.

After any correction, validate the complete list again. If a split is required, state the grain of each report, the join keys, and whether the join repeats a coarser metric across finer rows. Do not describe such a result as additive unless aggregation remains valid.

## Build and deliver

Start from the canonical body shape in [request and delivery workflow](workflow.md). Fill the resolved advertiser account and dates, include only validated fields and filters, and follow the same approval, submission, retrieval, and download rules as a catalog template.

Alongside the JSON, state:

- the selected grain and attribution interpretation;
- any derived metric formula, including zero-denominator handling;
- fields omitted or substituted;
- compatibility-driven report splits and join behavior;
- whether an empty result would be a valid outcome for the selected scope.

Promote a recurring ad-hoc request into the catalog only when its field set and caveats are stable. Add a canonical template, a focused mapping reference, a catalog row, and regression coverage together.
