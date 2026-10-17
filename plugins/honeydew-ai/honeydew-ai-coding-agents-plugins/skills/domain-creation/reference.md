# Domain Reference

## Full YAML Schema

```yaml
type: domain
name: <snake_case_name>
display_name: <Human Readable Name>
description: |-
  <business description — include purpose and intended audience>
owner: <owner_email_or_team>
labels: []
entities:
  - name: <entity_name>
    fields:                   # optional — omit to include all fields
      - <field_selector>
      - ...
filters:                      # optional — semantic filters on every query
  - name: <filter_name>
    sql: <entity.field expression>
    display_name: <optional display name>
    description: <optional description>
source_filters:               # optional — source-level filters
  - name: <filter_name>
    sql: <entity.field expression>
    display_name: <optional display name>
    description: <optional description>
parameters:                   # optional — override global parameter defaults
  - name: <global_parameter_name>
    value: <value>
```

## Entity Selection

Each entry in the `entities` list specifies an entity to include in the domain using the `name` field:

```yaml
entities:
  - name: orders
  - name: customers
  - name: products
```

Omitting an entity from the list makes it invisible within the domain. All entities needed for joins should be included.

## Field Selectors

The `fields` list controls which attributes and metrics are visible for an entity within the domain. If omitted, all fields are visible. Selectors are string patterns evaluated **in the order they are listed** — the last matching selector determines inclusion.

**Selector syntax:**

| Pattern | Meaning |
|---------|---------|
| `*` | Include all fields |
| `field_name` | Include a specific field |
| `-field_name` | Exclude a specific field |
| `pattern*`, `*pattern`, `*mid*` | Include fields matching wildcard |
| `-pattern*`, `-*pattern`, `-*mid*` | Exclude fields matching wildcard |

**Examples:**

```yaml
entities:
  # Include all fields (default behavior)
  - name: customers

  # Include only specific fields
  - name: orders
    fields:
      - order_id
      - order_date
      - order_total

  # Include all fields except specific ones
  - name: employees
    fields:
      - "*"
      - -salary
      - -ssn

  # Include fields matching a pattern
  - name: products
    fields:
      - product_*

  # Complex: all fields, exclude internal, re-include one
  - name: transactions
    fields:
      - "*"
      - -internal_*
      - internal_status
```

> **Important:** Never exclude key columns or foreign key columns — this breaks joins and queries. Always keep them visible.

## Filters

Domains support two types of filters. Both use structured objects with `name` and `sql` fields.

### Semantic Filters (`filters`)

Semantic filters apply to **every query** in the domain, regardless of which entities the query references. They may introduce additional JOINs.

```yaml
filters:
  - name: ground_shipping
    sql: lineitem.l_shipmode in ('MAIL', 'RAIL', 'TRUCK')
    display_name: Ground Shipping Only
    description: Only include shipments via ground transportation
```

**Use semantic filters for:** governance rules, access control, tenant isolation, business logic that must always apply.

**Caveat:** Semantic filters can slow queries by introducing extra JOINs. For example, a filter on `lineitem.shipmode` will cause a JOIN to `lineitem` even in queries that don't otherwise reference it.


### Source Filters (`source_filters`)

Source filters are applied **early, at the source level** — only when the source entity is actually part of the query. They do not introduce extra JOINs.

```yaml
source_filters:
  - name: recent_shipments
    sql: lineitem.l_shipdate >= '1994-01-01' and lineitem.l_shipdate < '1995-01-01'
```

**Use source filters for:** performance optimization on partitioned data, removing duplicate data, conditional filtering.

> **Caution:** Source filters apply before any computation, which can change the values of calculated attributes. When in doubt, use a semantic filter instead.

### Choosing Between Filter Types

| Aspect | Semantic (`filters`) | Source (`source_filters`) |
|--------|---------------------|--------------------------|
| **Scope** | Every query in the domain | Only when source entity is queried |
| **Timing** | After semantic resolution, may add JOINs | Early, directly on source tables |
| **Purpose** | Governance & access control | Performance optimization, deduplication |
| **Caveats** | Can slow queries via extra JOINs | May alter computed values |
| **Best use** | Consistent rules (tenant, access filters) | Large/partitioned data |

### Filter SQL Syntax

Both filter types use the same expression syntax in the `sql` field. All field references must be fully qualified (`entity.field`).

See the `filtering` skill for the full filter expression reference, including comparisons, IN lists, pattern matching, date filters, NULL checks, and combining conditions.
