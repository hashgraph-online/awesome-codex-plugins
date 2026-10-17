---
name: filtering
description: Use when the user needs to filter data — whether in a structured query, a metric aggregation, or an attribute expression. Covers filter syntax, date handling, and best practices.
---

## Overview

Filtering restricts which rows contribute to a result. The same expression language applies across three contexts in Honeydew:

| Context                  | Where it appears                                          | When it runs       |
| ------------------------ | --------------------------------------------------------- | ------------------ |
| **Structured query**     | `filters` parameter in `get_data_from_fields` / `get_sql_from_fields` | Pre-aggregation    |
| **Metric aggregation**   | `FILTER (WHERE ...)` on an aggregation                    | During aggregation |
| **Attribute expression** | `CASE WHEN ... END` in attribute SQL                      | Per-row evaluation |
| **Metric value filter**  | Metric expression in `filters` parameter                  | Post-aggregation   |

---

## Filter Expression Syntax

### Comparisons

```sql
entity.field = 'value'
entity.field > 100
entity.field >= 3 AND entity.field < 10
```

Operators: `=`, `<`, `>`, `>=`, `<=`, `!=`

You can compare an attribute to a constant or to another attribute. Cast mismatching types when comparing (e.g., `entity.field::DATE`).

### Strings

```sql
entity.field = 'exact value'
entity.field IN ('val1', 'val2', 'val3')
entity.field ILIKE '%keyword%'
```

- `ILIKE` is case-insensitive pattern matching (`%` = any characters, `_` = one character)

### Full-Text Search (Snowflake only)

Use `SEARCH` when you don't know exact values and need to find possible matches.

```sql
-- Single search — always use SEARCH_MODE => 'AND'
SEARCH(entity.field, 'search terms', SEARCH_MODE => 'AND')

-- Multiple alternatives — use OR between SEARCH calls
SEARCH(entity.field, 'term1', SEARCH_MODE => 'AND') OR SEARCH(entity.field, 'term2', SEARCH_MODE => 'AND')
```

**Always use `SEARCH_MODE => 'AND'`.**

### NULL Checks

```sql
entity.field IS NULL
entity.field IS NOT NULL
```

### Booleans

```sql
entity.flag = true
entity.flag = false
```

### Date Comparisons

```sql
YEAR(entity.date_field) = 2023
entity.date_field >= '2024-01-01'
entity.date_field BETWEEN '2024-02-05'::DATE AND '2024-02-10'::DATE
```

### Combining Conditions

```sql
entity.price > 50 AND entity.room_type = 'Private room'
entity.status = 'active' OR entity.status = 'pending'
```

Use `AND` / `OR` to combine conditions. Use parentheses to control precedence.

### Type Casting

Cast when types don't match:

```sql
entity.string_field::DATE
entity.number_field::VARCHAR
'2024-01-01'::DATE
DATE('2024-01-01')
```

---

## Filtering Contexts

### 1. Structured Query Filters

Pass filters as a list of expressions in the `filters` parameter of `get_data_from_fields` or `get_sql_from_fields`. Filters are applied **before** aggregation (equivalent to SQL `WHERE`):

Call `get_data_from_fields` with:

- `attributes`: `["detailed_listings.neighbourhood_cleansed"]`
- `metrics`: `["detailed_listings.count"]`
- `filters`: `["detailed_listings.room_type = 'Entire home/apt'", "detailed_listings.price > 50"]`

Each entry in the `filters` list is ANDed together.

### 2. Metric Aggregation Filters

Inside a metric's SQL, use `FILTER (WHERE ...)` to restrict which rows feed the aggregation:

```sql
SUM(orders.price) FILTER (WHERE orders.color = 'red')
COUNT(orders.id) FILTER (WHERE orders.status = 'completed')
```

**Use `FILTER (WHERE ...)`, not `CASE WHEN`**, for filtered aggregations in metrics.

### 3. Attribute Expression Filters

In attribute SQL, use `CASE WHEN` for conditional per-row logic:

```sql
CASE
  WHEN orders.amount > 1000 THEN 'high'
  WHEN orders.amount > 100 THEN 'medium'
  ELSE 'low'
END
```

### 4. Filtering by Metric Values

You can filter on aggregated metric values — the equivalent of SQL's `HAVING` clause. Use the metric expression (named or ad-hoc) in the `filters` parameter of a structured query. These filters are applied **after** aggregation.

This works with both named metrics (e.g., `entity.metric_name > 10`) and ad-hoc aggregations (e.g., `COUNT(entity.field) > 1`).

> For examples — including duplicate detection, minimum group size, and revenue thresholds — see `examples.md`.

---

## Date Handling

### Date Functions

| Function       | Use                                                  |
| -------------- | ---------------------------------------------------- |
| `CURRENT_DATE` | Reference today                                      |
| `DATE_TRUNC`   | Get boundaries: `DATE_TRUNC(month, CURRENT_DATE())`  |
| `INTERVAL`     | Relative time: `CURRENT_DATE() - INTERVAL '1 month'` |
| Cast strings   | `DATE('2024-01-01')` or `'2024-01-01'::DATE`         |

### Example — Last Month Filter

```sql
DATE_TRUNC(month, order.order_date) = DATE_TRUNC(month, CURRENT_DATE() - INTERVAL '1 month')
```

> Do NOT use interval calculation when asked about specific dates (e.g., "November 2024"). Use explicit date values instead.

---

## Best Practices

- **Discover available values if needed** — if you're unsure what values a field contains, check its distinct values by querying it as an attribute with a COUNT metric (see the **query** skill's "Getting Distinct Values" tip)
- **Use `SEARCH` when values are unknown** — avoids hard-coding exact strings
- **Use `ILIKE` for pattern matching** — case-insensitive, good for partial matches
- **Cast types explicitly** — prevents silent type coercion errors
- **Use `FILTER (WHERE ...)` in metrics**, not `CASE WHEN` — cleaner, standard SQL
- **Use `CASE WHEN` in attributes** — for per-row conditional logic
- **Prefer `IN (...)` over multiple OR** — cleaner for known value lists
- **Use date functions for relative dates** — `CURRENT_DATE`, `DATE_TRUNC`, `INTERVAL`
- **Use explicit dates for specific periods** — don't compute "November 2024" via interval math
