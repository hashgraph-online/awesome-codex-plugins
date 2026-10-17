---
name: attribute-creation
description: Guides you step-by-step through defining a calculated attribute (dimension) on a Honeydew entity. Covers SQL expression building and pushes to Honeydew via the MCP tools.
---

## Prerequisites

Before creating attributes, ensure you are on the correct workspace and branch. Use `get_session_workspace_and_branch` to check the current session context. For development work, create a branch with `create_workspace_branch` (the session switches automatically). See the `model-exploration` skill for the full workspace/branch tool reference.

---

## Overview

A Honeydew **calculated attribute** is a virtual, per-row column defined on an entity — analogous to an expression in a SQL `SELECT` clause.
It is evaluated once per row, not aggregated. In BI tools it surfaces as a **dimension** users can group, filter, and slice by.

Use a calculated attribute when:

- You need a reusable, governed column that doesn't exist verbatim in the source table (e.g. `net_price`, `customer_tier`, `order_month`)
- The value should be consistent everywhere it's consumed, not recalculated ad-hoc in each dashboard
- You want to expose a clean, business-friendly label for a raw or encoded column

Do **not** use a calculated attribute for aggregations across rows — use a metric instead.

---

## Building the SQL Expression

### Core Rules

- **Use simple expressions** — easy to understand
- **Use the SQL dialect of the connected data warehouse** (Snowflake, Databricks, or BigQuery)
- **Use `entity.field` format** for all attribute/metric references
- **No joins or subqueries** — simple expressions only (window functions allowed)
- **Use fully qualified column names** — `orders.amount`, not just `amount`
- **Prefer ILIKE over LIKE** for case-insensitive matching

See [reference.md](reference.md) for: SQL functions, JSON/semi-structured data, geography, data types, full YAML schema, attribute types, time grain, and format strings.

---

## Creation Methods

### Primary: create_object with YAML

Call `create_object` with `yaml_text`:

```yaml
type: calculated_attribute
entity: <entity_name>
name: <snake_case_name>
display_name: <Human Readable Name>
description: |-
  <business description>
owner: <owner_email_or_team>
datatype: string|number|float|bool|date|timestamp|time
sql: |-
  <SQL expression>
folder: <optional folder path>
```

**Required fields:**

- `type: calculated_attribute`
- `entity` — the entity this attribute belongs to
- `name` — snake_case identifier
- `owner` — **CRITICAL: always set** (email or team name)
- `datatype` — **CRITICAL: always set explicitly**
- `sql` — the expression

### Update: update_object

1. Use `get_entity` or `search_model` (with `search_mode: EXACT`) to find the attribute's `object_key`.
2. Call `update_object` with the full updated YAML (`yaml_text`) and the `object_key`.

> **Minimal diff rule:** When updating, preserve the existing field order and formatting from the current YAML. Only change the fields you need to modify. Objects are versioned in git, so unnecessary reordering or reformatting creates noisy diffs.

### After Creation/Update: Display the UI Link

After a successful `create_object` or `update_object` call, the response includes a `ui_url` field. **Always display this URL to the user** so they can quickly open the object in the Honeydew application.

### Delete: delete_object

1. Use `search_model` (with `search_mode: EXACT`) to find the attribute's `object_key`.
2. Call `delete_object` with that `object_key`.

---

## Examples

See [examples.md](examples.md) for full worked examples covering: basic, boolean flag, grouping/binning, multi-entity, date truncation, window function, running total, semi-structured JSON, safe division, update, and delete.

---

## Discovery Helpers

Use these MCP tools to explore existing attributes:

- `get_entity` — Get entity details including all attributes (filter by `__typename` for `CalcAttribute` or `DataSetAttribute`)
- `get_field` — Get detailed info about a specific attribute by entity and field name
- `search_model` — Search for attributes across the model by name (use `search_mode: EXACT` for known names, `OR` for broad discovery)
- `list_entities` — List entities to identify where to anchor new attributes

---

## Documentation Lookup

Use the `honeydew-docs` MCP tools to search the Honeydew documentation when:

- You need warehouse-specific SQL function details not covered in `reference.md` (Snowflake, Databricks, BigQuery differences)
- The user asks about advanced attribute types (multi-entity, aggregation) or when to use each
- You need guidance on time grain configuration, format strings, or data type nuances
- The user needs advanced modeling patterns for calculated attributes (e.g., complex bucketing, conditional logic, semi-structured data extraction)

Search for topics like: "calculated attributes", "attribute types", "multi-entity attribute", "aggregation attribute", "time grain", "format strings", "advanced modeling".

---

## Best Practices

- **Reuse existing attributes — don't repeat logic.**
  If a calculated attribute already exists on the entity (or you just created one), reference it by name
  (`entity.attribute_name`) rather than inlining its SQL expression. This keeps definitions DRY and ensures changes propagate.
- **Qualify every column reference** with the entity name: `orders.amount`, not `amount`.
- **Set timegrain** on every date/timestamp attribute.
- **Hide raw / intermediate columns** so they don't clutter BI tool field pickers.
- **Use folder** to group related attributes.
- **Prefer Multi-Entity over duplicating columns.** Reference related entities rather than copying definitions.
- **Use DIV0 for division** to avoid divide-by-zero errors.
- **Use ILIKE over LIKE** for case-insensitive string matching.

---

## MANDATORY: Validate After Creating

**After creating ANY attribute, you MUST invoke the `validation` skill to test and validate results.**

See `validation` skill for:

- How to execute attributes via `get_data_from_fields` (attributes go in the attributes parameter)
- Type-specific sanity checks (booleans, dates, buckets, etc.)
- When to alert the user about suspicious results

**Quick validation — check distinct values:**

Call `get_data_from_fields` with:

- `attributes`: `["<entity>.<attribute_name>"]`
- `metrics`: `["COUNT(<entity>.<attribute_name>)"]` — forces aggregation, returning one row per distinct value

This lets you quickly inspect all distinct output values and their frequencies to confirm the attribute logic is correct (see the **query** skill's "Getting Distinct Values" tip for more details).

---

## Common Pitfalls to Avoid

- **Unqualified column references.** `amount` will fail — write `orders.amount`.
- **Using Aggregation attribute when a metric is better.** If it's a reusable KPI, use a metric.
- **Aggregating from same-grain or higher-grain entity.** Only aggregate from higher-granularity (many-side) entities.
