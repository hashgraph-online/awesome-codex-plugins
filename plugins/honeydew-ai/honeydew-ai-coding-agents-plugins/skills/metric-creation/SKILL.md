---
name: metric-creation
description: Guides you step-by-step through defining a business metric (aggregation) on a Honeydew entity. Covers SQL expression building and pushes to Honeydew via the MCP tools.
---

## Prerequisites

Before creating metrics, ensure you are on the correct workspace and branch. Use `get_session_workspace_and_branch` to check the current session context. For development work, create a branch with `create_workspace_branch` (the session switches automatically). See the `model-exploration` skill for the full workspace/branch tool reference.

---

## Overview

A Honeydew **metric** is a named, reusable aggregation anchored to an entity.
Unlike a calculated attribute (which is per-row), a metric collapses multiple rows into a
single value.
Metrics are **context-sensitive**: they automatically respond to whatever filters and
groupings the consuming BI tool or analyst applies.

**Your job is to build an aggregation function that users can later group by.**

If a user asks for a group by ("sum sales by category"), ignore the group. You're building the aggregation to sum sales by ANYTHING. The user will later use it in a query with their chosen dimensions.

Use a metric when:

- The same aggregation logic is reused across dashboards, teams, or tools
- You need a governed, single source of truth for a KPI (e.g. "revenue", "active users")
- The calculation involves combining other metrics (ratios, deltas)

**Do not** use a metric when the value is per-row (use a calculated attribute instead).

---

## Building the SQL Expression

### Core Rules

- **MUST use an aggregation function** — metrics collapse rows
- **DO NOT use window functions** — only aggregations allowed
- **DO NOT use joins or subqueries** — simple expressions only
- **NEVER use COUNT(\*)** — use the entity's built-in count metric (e.g., `entity.count`) if available,
  or `COUNT(entity.key_field)` on a specific key column.
- **Reuse existing attributes and metrics** — if a calculated attribute or metric already exists (or you just created one),
  reference it by name (e.g., `entity.attribute_name`) rather than repeating its SQL logic in the new metric expression.
  This keeps definitions DRY and ensures changes propagate.
- **Use fully qualified column names** — `entity.attribute`, not just `attribute`

See [reference.md](reference.md) for: aggregation functions, filtered aggregations, date handling, text summarization, data types, metric types, and format strings.

---

## Creation Methods

### create_object (Required)

Always use `create_object` with full YAML to ensure proper datatype and all properties are set.

Call `create_object` with `yaml_text`:

```yaml
type: metric
entity: <entity_name>
name: <snake_case_name>
display_name: <Human Readable Name>
description: |-
  <business description>
owner: <owner_email_or_team>
datatype: float|number|string|date|timestamp
sql: |-
  <aggregation SQL expression>
```

**Required fields:**

- `type: metric`
- `entity` — the entity this metric belongs to
- `name` — snake_case identifier
- `owner` — **CRITICAL: always set to current username** (from workspace context)
- `datatype` — **CRITICAL: always set explicitly** (default to `float` for most metrics, `number` for counts)
- `sql` — the aggregation expression

**Optional fields:**

- `display_name` — human readable name
- `description` — business context
- `format_string` — display format (e.g., `$#,##0.00`)
- `labels` — categorization tags
- `folder` — organizational path

### update_object (for updates)

To modify an existing metric:

1. Use `get_entity` with the entity name to find the metric and its details.
2. Use `search_model` (with `search_mode: EXACT`) to find the metric's `object_key`.
3. Call `update_object` with the full updated YAML (`yaml_text`) and the `object_key`.

> **Minimal diff rule:** When updating, preserve the existing field order and formatting from the current YAML. Only change the fields you need to modify. Objects are versioned in git, so unnecessary reordering or reformatting creates noisy diffs.

### After Creation/Update: Display the UI Link

After a successful `create_object` or `update_object` call, the response includes a `ui_url` field. **Always display this URL to the user** so they can quickly open the object in the Honeydew application.

### delete_object (for deletion)

1. Use `search_model` (with `search_mode: EXACT`) to find the metric's `object_key`.
2. Call `delete_object` with the `object_key`.

---

## Examples

See [examples.md](examples.md) for full worked examples covering: basic, derived, filtered, ratio, count, distinct count, fixed grouping, nested aggregation, text summary, update, and delete.

---

## Discovery Helpers

Use these MCP tools to explore existing metrics:

- `get_entity` — Get entity details including all its metrics, attributes, datasets, and relations
- `get_field` — Get detailed info about a specific metric by entity and field name
- `search_model` — Search for metrics across the model by name (use `search_mode: EXACT` for known names, `OR` for broad discovery)
- `list_entities` — List entities to identify where to anchor new metrics

---

---

## Clarify Ambiguous Requests (BEFORE creating)

Many metric requests are ambiguous. **ALWAYS clarify before implementing:**

| Ambiguous Term       | Possible Interpretations               | Ask User                                                                                       |
| -------------------- | -------------------------------------- | ---------------------------------------------------------------------------------------------- |
| "per day/week/month" | A) Breakdown by period (multiple rows) | "Do you want revenue _for each day_ (fixed grouping) or _average daily revenue_ (single KPI)?" |
|                      | B) Average per period (single value)   |                                                                                                |
| "rate"               | A) Ratio (X / Y)                       | "Is this a ratio (e.g., conversion rate = orders/visits) or velocity (e.g., orders per hour)?" |
|                      | B) Velocity (X per time unit)          |                                                                                                |
| "growth"             | A) Absolute difference                 | "Do you want absolute growth ($100 → $150 = $50) or percentage growth (50%)?"                  |
|                      | B) Percentage change                   |                                                                                                |
| "average"            | A) Simple mean                         | "Simple average or weighted average? If weighted, by what?"                                    |
|                      | B) Weighted mean                       |                                                                                                |

---

## Map User Choice → Implementation Pattern

After user clarifies intent, use the correct SQL pattern:

| User Choice             | SQL Pattern                                                    | Example                                                                 |
| ----------------------- | -------------------------------------------------------------- | ----------------------------------------------------------------------- |
| **Breakdown by period** | `AGG(field) GROUP BY (time_field)`                             | `SUM(order_header.order_total) GROUP BY (order_header.order_date)`      |
| **Average per period**  | `AGG(metric GROUP BY (*, time_field))` or `SUM/COUNT DISTINCT` | `AVG(order_header.total_revenue GROUP BY (*, order_header.order_date))` |
| **Ratio**               | `metric_a / NULLIF(metric_b, 0)`                               | `order_count / NULLIF(customer_count, 0)`                               |
| **Velocity (per time)** | `AGG(field) / COUNT(DISTINCT time_field)`                      | `SUM(order_total) / NULLIF(COUNT(DISTINCT order_date), 0)`              |
| **Absolute growth**     | `current - previous`                                           | Requires time comparison logic                                          |
| **Percentage growth**   | `(current - previous) / NULLIF(previous, 0) * 100`             | Requires time comparison logic                                          |

**CRITICAL: "Breakdown by X" or "for each X" = Fixed GROUP BY**

- ✅ `SUM(order_header.order_total) GROUP BY (order_header.order_date)`
- ❌ `SUM(order_header.order_total)` ← requires manual grouping at query time

---

## Additional Grouping Clarifications

When the user's request contains phrases suggesting a specific granularity, **ask before creating**:

| Phrase                                 | Likely Intent                 | Clarifying Question                                                                                   |
| -------------------------------------- | ----------------------------- | ----------------------------------------------------------------------------------------------------- |
| "in an order", "per order", "by order" | Fixed grouping by order_id    | "Should this always be calculated per order (fixed grouping), or flexible to group by any dimension?" |
| "in a day", "per day", "daily"         | Fixed grouping by date        | "Should this always be at daily granularity, or flexible?"                                            |
| "per customer", "by customer"          | Fixed grouping by customer_id | "Should this always be per customer, or flexible?"                                                    |

**Rule:** If the request mentions "per X" or "in an X", clarify whether they want:

1. **Fixed Grouping** — `SUM(entity.field) GROUP BY (entity.x_id)`
2. **Flexible Aggregation** — `SUM(entity.field)` that users can group by anything later

---

## Documentation Lookup

Use the `honeydew-docs` MCP tools to search the Honeydew documentation when:

- You need to understand metric types or advanced aggregation patterns beyond what `reference.md` covers
- The user asks about how metrics behave in BI tools or how context-sensitive aggregation works
- You need guidance on derived metrics, fixed groupings, or metric composition patterns
- The user needs **time intelligence** features — period-over-period comparisons, YTD/MTD/QTD calculations, trailing windows, or time-based growth metrics

Search for topics like: "metrics", "aggregation", "derived metrics", "fixed grouping", "time intelligence", "period over period", "YTD", "trailing window".

---

## Best Practices

- **Use `FILTER (WHERE ...)` for filtered aggregations** — NOT `CASE WHEN`.
  The FILTER syntax is cleaner, more readable, and the native Honeydew pattern.
  - ✅ `SUM(orders.amount) FILTER (WHERE orders.is_promotional)`
  - ✅ `COUNT(truck.truck_id) FILTER (WHERE truck.is_electric)`
  - ❌ `SUM(CASE WHEN orders.is_promotional THEN orders.amount ELSE 0 END)`
  - ❌ `COUNT(CASE WHEN truck.is_electric THEN truck.truck_id END)`
- **Reuse existing objects — don't repeat logic.**
  If you created a calculated attribute (e.g., `orders.net_price`), reference it in your metric (`SUM(orders.net_price)`)
  rather than inlining the attribute's SQL expression.
  Similarly, if a metric already exists, reference it in derived metrics by name (`entity.existing_metric`).
  This keeps definitions DRY and ensures changes propagate automatically.
- **Never use COUNT(\*).** Use the entity's built-in count metric (e.g., `entity.count`) when available.
  Otherwise, use `COUNT(entity.key_field)` on the entity's key column.
- **Name metrics after the business concept**, not the SQL. `gross_margin` is better than `revenue_minus_cogs_divided_by_revenue`.
- **Use Derived metrics for ratios.** Build numerator and denominator as separate metrics first.
- **Use fully qualified column names.** `orders.amount`, not just `amount`.
- **Ignore grouping requests.** Build the aggregation; users add dimensions later.

---

## MANDATORY: Validate After Creating

**After creating ANY metric, you MUST invoke the `validation` skill to test and validate results.**

See `validation` skill for:

- How to execute metrics via `get_data_from_fields`
- Sanity checks (magnitude, sign, consistency)
- When to alert the user about suspicious results
- Cross-validation with related metrics

**Quick validation:**

Call `get_data_from_fields` with:

- `metrics`: `["<entity>.<metric_name>"]`

---

## Common Pitfalls to Avoid

- **Using `COUNT(*)`** — use the entity's built-in count metric if available, or `COUNT(entity.key_field)` on a specific key.
- **Repeating logic that already exists** — if a calculated attribute or metric already exists, reference it by name instead of duplicating its SQL.
- **Using window functions** — only aggregations allowed in metrics.
- **Using joins or subqueries** — simple expressions only.
- **Unqualified column references** — always prefix with entity name.
