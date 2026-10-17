# Entity Reference

## YAML Schemas

### Entity definition

```yaml
type: entity
name: <snake_case_name>
display_name: <Human Readable Name>
description: |-
  <business description>
owner: <owner_email_or_team> # REQUIRED - set for governance
labels: []
keys:
  - <key_attribute_name>
key_dataset: <source_dataset_name>
is_time_spine: false
```

### Dataset definition

```yaml
type: dataset
entity: <entity_name>
name: <dataset_name>
display_name: <Human Readable Name>
description: |-
  <description>
dataset_type: table|sql|entity
sql: <table_name or SQL query or base_entity_name>
attributes:
  - column: <source_column_name>
    name: <attribute_name>
    display_name: <Human Readable Name>
    datatype: bool|date|float|number|string|time|timestamp
    timegrain: hour|day|week|month|quarter|year # date/timestamp only
```

## Source Types

| Type                      | When to use                                                       | `dataset_type` value |
| ------------------------- | ----------------------------------------------------------------- | -------------------- |
| **Physical table / view** | Entity maps directly to a data warehouse table or view            | `table`              |
| **Custom SQL**            | Entity defined by a SQL query — filters, unions, light transforms | `sql`                |
| **Virtual entity**        | No physical backing — granularity derived from another entity     | `entity`             |

> Prefer physical tables over custom SQL. Custom SQL limits Honeydew's ability to push filters and column selections down to the warehouse.

## Granularity Key Rules

The key uniquely identifies a single row. It must be:

- **Unique** — no duplicate values
- **Non-null** — no missing values
- **Stable** — does not change over time

Composite keys (multiple columns) are supported for physical entities.
Virtual entities support single-attribute keys only — use `HASH()` to combine columns if needed.
