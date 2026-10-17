---
name: validation
description: Use after creating or modifying ANY Honeydew object (metric, attribute, entity, domain). Provides type-specific validation logic to ensure objects work correctly and return sensible results.
---

## Overview

**This skill is MANDATORY after creating or modifying any Honeydew object.**

Validation ensures:

- The object compiles and executes without errors
- Results are returned (not NULL or empty)
- Values make business sense
- Related objects are consistent with each other

---

## Validation by Object Type

### Metrics

**Step 1: Execute the metric**

Call `get_data_from_fields` with:

- `metrics`: `["<entity>.<metric_name>"]`

If the tool call fails (API error, permission denied, timeout), report the error to the user before proceeding. Do not confuse a tool error with suspicious data.

**Step 2: Sanity checks**

| Check           | What to Look For                      | Action if Failed                                      |
| --------------- | ------------------------------------- | ----------------------------------------------------- |
| Returns data    | Not NULL, not empty                   | Check SQL syntax, entity references                   |
| Magnitude       | Reasonable for business context       | Verify calculation logic                              |
| Sign            | Positive for revenue/counts (usually) | Check for inverted logic                              |
| Related metrics | Parts sum to whole                    | Query related metrics together and verify consistency |
| Ratios          | Between 0-100% (usually)              | Check numerator and denominator metrics independently |

**Step 3: Cross-validation**

If the new metric is a filtered subset of an existing metric, or a ratio of existing metrics, query them together to verify consistency:

- For filtered metrics: query the filtered metric alongside the unfiltered total — the filtered value should be less than or equal to the total.
- For ratio/derived metrics: query the numerator and denominator independently to confirm they return sensible values before checking the ratio.

Call `get_data_from_fields` with both metrics:

- `metrics`: `["<entity>.<filtered_metric>", "<entity>.<total_metric>"]`

**Alert user if:**

- Metric returns $0 or NULL unexpectedly
- Revenue/count is negative
- Ratio exceeds 100% or is negative (unless expected)
- Magnitude seems off by orders of magnitude

---

### Attributes

**Step 1: Execute the attribute**

If the attribute references a related entity (multi-entity attribute), first verify the relation exists using `get_entity` on the source entity.
If the relation is missing, report that before attempting to query the attribute.

Sample rows — call `get_data_from_fields` with:

- `attributes`: `["<entity>.<attribute_name>"]`

For boolean attributes, check distribution — call `get_data_from_fields` with:

- `attributes`: `["<entity>.<boolean_attribute>"]`
- `metrics`: `["<entity>.count"]`

**Step 2: Sanity checks by attribute type**

| Attribute Type      | Valid Range              | Red Flags                           |
| ------------------- | ------------------------ | ----------------------------------- |
| **Age/Duration**    | 0 to reasonable max      | Negative values, >150 years         |
| **Boolean**         | TRUE/FALSE mix           | All TRUE or all FALSE               |
| **Percentage**      | 0-100 (usually)          | Negative, >100 (unless growth rate) |
| **Date**            | Past to near future      | Year 1900, year 2099, all NULLs     |
| **Category/Bucket** | Expected labels          | 95%+ in "Unknown" or NULL           |
| **Rank**            | Starts at 1, consecutive | Starts at 0, gaps, all same value   |
| **Running total**   | Monotonically increasing | Decreases, resets unexpectedly      |
| **Any type**        | Mix of values            | >50% NULLs warrants investigation   |

**Alert user if:**

- All values are NULL or >50% NULLs
- Boolean is 100% one value
- Dates are invalid or in wrong century
- Buckets are mostly "Unknown"

---

### Entities

**Step 1: Verify entity was created**

Use `list_entities` and filter results for the new entity name.

**Step 2: Verify data flows**

Call `get_data_from_fields` with:

- `metrics`: `["<entity>.count"]`

Also call with a list of attributes to verify they are accessible:

- `attributes`: `["<entity>.<attribute1>", "<entity>.<attribute2>", "<entity>.<attribute3>"]`

**Step 3: Sanity checks**

| Check                 | What to Look For                 | Action if Failed             |
| --------------------- | -------------------------------- | ---------------------------- |
| Entity exists         | Shows in `list_entities` results | Check `create_entity` call   |
| Has rows              | Count > 0                        | Verify source table path     |
| Key is unique         | Count = count distinct of key    | Fix key or add composite key |
| Attributes accessible | Can query attributes             | Check dataset definition     |

**Alert user if:**

- Entity not found after creation
- Zero rows returned
- Key column has duplicates (for non-fact tables)

#### Validating Relations (part of entity validation)

Relations are not standalone objects — they are defined within an entity's YAML. Validate them as part of the entity that contains them.

**Step 1: Verify relation exists**

Use `get_entity` on the source entity and check its relations list for the new relation.

**Step 2: Test the join works**

Call `get_data_from_fields` with a cross-entity query:

- `attributes`: `["<target_entity>.<attribute>"]`
- `metrics`: `["<source_entity>.<metric>"]`

**Step 3: Sanity checks**

| Check            | What to Look For              | Action if Failed                                |
| ---------------- | ----------------------------- | ----------------------------------------------- |
| Relation exists  | Shows in `get_entity` results | Check `update_object` call                      |
| Join works       | Cross-entity query succeeds   | Verify join keys match                          |
| No fan-out       | Counts don't explode          | Check cardinality (many-to-one vs many-to-many) |
| NULLs reasonable | Some NULLs OK for left join   | Too many NULLs = bad join key                   |

**Alert user if:**

- Relation not found on the entity
- Cross-entity query fails
- Row count explodes (indicates wrong cardinality)
- All joined values are NULL (bad join condition)

---

### Domains

**Step 1: Verify domain exists**

Use `search_model` (with `search_mode: EXACT`) to find the new domain by name.

**Step 2: Test with a scoped query**

Call `get_data_from_fields` with the `domain` parameter to verify entities are accessible and filters apply:

- `metrics`: `["<entity>.count"]`
- `domain`: `"<domain_name>"`

**Step 3: Verify filters apply**

If the domain has semantic or source filters, compare results with and without the domain to confirm filters reduce the data as expected:

- Query a metric **with** the domain set — note the result.
- Query the same metric **without** the domain — note the result.
- The domain-scoped result should be less than or equal to the unscoped result (for filters that restrict rows).

**Step 4: Sanity checks**

| Check                | What to Look For                            | Action if Failed                              |
| -------------------- | ------------------------------------------- | --------------------------------------------- |
| Domain exists        | Found via `search_model`                    | Check `create_object` call and YAML syntax    |
| Entities accessible  | Scoped query returns data                   | Verify entity names match existing entities   |
| Filters apply        | Scoped count <= unscoped count              | Check filter SQL and entity.field references  |
| Field selectors work | Excluded fields not returned in query       | Verify selector patterns and order            |
| No errors            | Query executes without compilation errors   | Check filter SQL syntax, fully qualified refs |

**Alert user if:**

- Domain not found after creation
- Scoped query returns an error (likely bad filter SQL or missing entity)
- Filters have no effect (scoped count equals unscoped count when a filter is expected to reduce rows)
- Excluded fields are still accessible (field selector not applied correctly)

---

## Validating Updates (update_object)

When modifying an existing object, compare before and after:

1. **Before altering**, query the object and note the current result.
2. **After altering**, query again and compare.
3. Report the difference to the user: "The metric `revenue` changed from `$1,234,567` to `$1,198,432` after applying the discount logic."

This confirms the change had the intended effect and helps catch unintended regressions.

---

## Error Handling

If a tool call fails, distinguish between:

| Situation                      | Meaning                                             | Action                                                                                                             |
| ------------------------------ | --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Tool returns an error          | API error, permission denied, timeout, invalid YAML | Report the error message to the user. Do not treat as a validation failure — the object may not have been created. |
| Tool returns empty/NULL data   | Object was created but returns no results           | Proceed with sanity checks — likely a data or SQL issue.                                                           |
| Tool returns unexpected values | Object works but results look wrong                 | Report findings and ask user before attempting a fix.                                                              |

---

## Alerting Guidelines

When results seem wrong, report to the user with:

1. **The actual value** returned by the query
2. **Why it looks suspicious** (e.g., negative revenue, 100% NULL, row count doubled)
3. **A suggested next step** (e.g., "Should I check the SQL expression?" or "Should I verify the join keys?")

Do not silently fix issues — always surface findings and ask before making changes.

---

## Quick Reference

| Object    | Execute With                                  | Key Checks                          |
| --------- | --------------------------------------------- | ----------------------------------- |
| Metric    | `get_data_from_fields` with metrics list      | Value, magnitude, sign, consistency |
| Attribute | `get_data_from_fields` with attributes list   | Range, distribution, NULLs          |
| Entity    | `list_entities` + `get_data_from_fields`      | Exists, has rows, key unique        |
| Relation  | `get_entity` + cross-entity field query       | Exists, joins work, no fan-out (validated as part of entity) |
| Domain    | `search_model` + `get_data_from_fields` with domain | Exists, filters apply, fields scoped |
