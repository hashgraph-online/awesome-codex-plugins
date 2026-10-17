---
name: entity-creation
description: Guides you through defining a new Honeydew entity from a data warehouse source — covering source type, granularity key, and initial attribute mapping — then pushes to Honeydew via the MCP tools.
---

## Prerequisites

Before creating entities, ensure you are on the correct workspace and branch. Use `get_session_workspace_and_branch` to check the current session context. For development work, create a branch with `create_workspace_branch` (the session switches automatically). See the `model-exploration` skill for the full workspace/branch tool reference.

---

## Overview

A Honeydew **entity** is the foundational modeling object — a named, governed representation of a business concept at a specific granularity. Every metric and calculated attribute is anchored to an entity. An entity maps to a data warehouse (Snowflake, Databricks, or BigQuery) table, view, custom SQL query, or a virtual derivation from the semantic model.

When creating an entity you are answering three questions:

1. **What is this?** — the business concept (orders, customers, products, locations)
2. **What makes a row unique?** — the granularity key (primary key column(s))
3. **What columns should be exposed?** — the initial attribute mapping from source columns

> This skill focuses on the entity shell: source, key, and attribute mapping.
> Use `attribute-creation` to add calculated attributes and `relation-creation` to wire up joins afterwards.

---

## Creation Methods

### Quick Import: import_tables

Use `import_tables` to quickly import one or more data warehouse tables into the semantic model.
Each table becomes an entity with its columns automatically mapped as attributes. This is the fastest way to bootstrap entities when you don't need custom YAML.

Parameters:

- `tables` — List of fully qualified table names in the format `<database>.<schema>.<table>`

Best for: bulk imports, quick prototyping, or when the default column-to-attribute mapping is sufficient.

### Primary: create_entity (Recommended)

Unlike metrics and attributes, entity creation always requires YAML — there is no simplified single-expression API. `create_entity` is the preferred MCP tool because it creates both the entity and its dataset in a **single operation**.

Parameters:

- `entity_yaml` — YAML defining the entity
- `dataset_yaml` — YAML defining the dataset

Required permission: Editor or higher.

### Alternative: create_object (Generic)

Use `create_object` only when creating an entity or dataset independently (e.g. adding a second dataset to an existing entity). Requires a separate call per object.

Parameters:

- `yaml_text` — YAML defining the object

### After Creation: Display the UI Link

After a successful `create_entity` or `create_object` call, the response includes a `ui_url` field. **Always display this URL to the user** so they can quickly open the object in the Honeydew application.

---

## Decision Flow

```
Need to create an entity?
    │
    ├─► Quick import from warehouse table(s)? Default mapping is fine?
    │       └─► Use import_tables ✓ (fastest)
    │
    ├─► New entity + dataset together (most common)?
    │       └─► Use create_entity ✓ (full control)
    │
    ├─► Adding a second dataset to existing entity?
    │       └─► Use create_object with dataset YAML only
    │
    └─► Updating an existing entity or dataset?
            └─► Use update_object with YAML + object_key
                (preserve existing field order — minimal diff)
```

---

## Examples

See [examples.md](examples.md) for full worked examples covering: physical table, custom SQL, virtual entity, time spine, update, and delete.

---

## Discovery Helpers

Use these MCP tools before creating entities:

- `list_entities` — List all entities in the model
- `get_entity` — Get detailed info for a specific entity (attributes, metrics, datasets, relations)
- `search_model` — Search for entities, fields, or other objects by name (use `search_mode: EXACT` for known names, `OR` for broad discovery)
- `list_databases` — List all databases in the connected data warehouse
- `list_schemas` — List schemas in a specific database
- `list_tables` — List warehouse tables (requires `database` and `schema` parameters)
- `get_table_info` — Get column details for a specific warehouse table

---

See [reference.md](reference.md) for: YAML schemas (entity + dataset), source types, and granularity key rules.

---

## Documentation Lookup

Use the `honeydew-docs` MCP tools to search the Honeydew documentation when:

- You need to understand entity source types (physical table, custom SQL, virtual entity) in more depth
- The user asks about granularity design, entity modeling patterns, or best practices
- You need guidance on advanced modeling configurations like time spines, composite keys, or multi-dataset entities
- The user asks about entity governance, ownership, or lifecycle
- The user needs advanced modeling patterns (e.g., slowly changing dimensions, snapshot entities, incremental models)

Search for topics like: "entities", "source types", "granularity", "time spine", "virtual entity", "custom SQL source".

---

## Best Practices

- **Always set `owner`** to identify the responsible team or person for governance and accountability.
- **One entity = one granularity.** Never mix row-level grains. If a table has order-level and line-item-level rows, model them as two separate entities.
- **Name entities after the business concept, not the table.** `orders` is better than `fact_orders` or `fct_orders_v2`.
- **Always expose foreign key columns as attributes.** FK columns (e.g. `customer_id` on orders) are required for Honeydew to resolve relations.
- **Set `timegrain` on every date/timestamp source column.** Omitting it leads to unexpected aggregation behavior in BI tools.
- **Prefer absolute table paths** (`DB.SCHEMA.TABLE`) to avoid ambiguity across environments.
- **Convention:** entity = `orders`, dataset = `orders_source`. Keeping names distinct prevents confusion in YAML.

---

## MANDATORY: Validate After Creating

**After creating ANY entity, you MUST invoke the `validation` skill to test and validate.**

See `validation` skill for:

- How to verify entity exists via `list_entities`
- How to verify data flows via `get_data_from_fields`
- Sanity checks (row count, key uniqueness)
- When to alert the user about issues

**Quick validation:**

1. Verify entity exists using `list_entities`, filter for the new entity name.
2. Verify data flows using `get_data_from_fields` with:

- `metrics`: `["<entity>.count"]`

---

## Common Pitfalls to Avoid

- **Non-unique or nullable keys.** Honeydew assumes keys are unique and non-null. Duplicates cause silent incorrect join results. Validate before modeling.
- **Using custom SQL when a physical table would do.** Custom SQL blocks filter pushdown. Use a domain-level filter instead and keep the entity on the physical table.
- **Skipping the key column in the attribute list.** The key column must be in the dataset attributes list or Honeydew cannot resolve it.
- **Composite keys on virtual entities.** Use `HASH()` to create a single synthetic key attribute instead.
- **Forgetting `is_time_spine` on your date dimension.** Time-aware metrics will not function without a designated time spine entity.
