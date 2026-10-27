# Sponsored Products campaign portfolio audit

Fill requested sections from the validated Amazon Ads MCP report. Mark unsupported sections `N/A` and name the missing field or unresolved ambiguity.

## 1. Scope and provenance

- Identity, advertiser account/profile, region, marketplace, and currency
- Date range and report ID
- Report-field catalog or schema version when exposed
- Exact requested and accepted field IDs
- Returned row count and detected grain
- Aggregation and budget-denominator rules

## 2. Executive findings

Summarize the most material observations. Label each statement as:

- **Observation:** directly calculated or returned by the MCP
- **Hypothesis:** a plausible explanation requiring investigation
- **Recommendation:** a reversible next step tied to evidence

## 3. Portfolio composition

- Unique campaigns after aggregation
- Delivery-status counts, with proxy status disclosed
- Spend and optional attributed sales totals
- Targeting-type mix when supported by a validated field
- Naming-pattern counts only when the user confirms the taxonomy

## 4. Spend concentration

- Top-N campaigns by cost, including campaign ID, name, cost, and portfolio share
- Total cost and top-N share formula
- User-provided threshold and result, or descriptive distribution when no threshold exists

## 5. Budget fill

- Campaign or portfolio fill rates only where window-aligned denominators are available
- Budget type, eligible-day rule, and treatment of budget changes
- `N/A` explanation where historical budget cannot be reconstructed

## 6. Delivery and engagement review

- No-delivery campaigns
- Visible-without-engagement campaigns
- Data-quality anomalies
- Prioritized review table with evidence and diagnostic hypotheses

## 7. Structure and naming

- Observed targeting mix
- Confirmed naming taxonomy analysis
- Normalized duplicate-name groups, retaining campaign IDs

## 8. Recommendations

Provide a short, evidence-linked review queue. State what should be verified before any change and identify risks such as seasonality, learning effects, shared constraints, or recent launches. Do not execute campaign changes.

## 9. Limitations

List missing fields, proxy measures, unresolved account context, schema compromises, threshold sources, and any section marked `N/A`.
