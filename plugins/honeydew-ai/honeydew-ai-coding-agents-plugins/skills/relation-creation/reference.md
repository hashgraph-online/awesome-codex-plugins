# Relation Reference

## YAML Schema

```yaml
relations:
  - target_entity: <target_entity_name>
    rel_type: many-to-one|one-to-many
    rel_join_type: left|inner|right|outer   # default: left
    cross_filtering: both|many-to-one|one-to-many|none   # default: both
    connection:
      - src_field: <source_entity_field>
        target_field: <target_entity_field>
    # OR use connection_expr instead of connection:
    connection_expr:
      sql: |-
        <custom SQL join expression>
```

## Direction (rel_type)

| Value | Meaning | When to use |
|---|---|---|
| `many-to-one` | Many rows on source join to one row on target | Source holds the FK (e.g. orders → customers) |
| `one-to-many` | One row on source joins to many rows on target | Inverse perspective — rarely needed directly |

> Always define the relation on the entity that holds the foreign key, using `many-to-one`.

## Join Type (rel_join_type)

| Value | Behaviour | Default |
|---|---|---|
| `left` | All source rows kept, nulls for unmatched target | Yes |
| `inner` | Only rows with a match on both sides | — |
| `right` | All target rows kept, nulls for unmatched source | — |
| `outer` | All rows from both sides kept | — |

## Cross-Filtering (cross_filtering)

Controls how filters propagate between the two entities in BI queries:

| Value | Filter propagates | Performance |
|---|---|---|
| `both` | In both directions (default) | Standard |
| `one-to-many` | From "one" side to "many" side only | Standard |
| `many-to-one` | From "many" side to "one" side only | Higher cost |
| `none` | No propagation | Fastest |

> `many-to-one` cross-filtering is expensive — use `none` or `one-to-many` for large entities where bidirectional filtering is not required.

## Connection Methods

| Method | When to use |
|---|---|
| `connection` (field-based) | Simple equality joins on one or more columns. Must include all columns of the "one" side's key. |
| `connection_expr` (SQL expression) | Complex joins: range conditions, SCD Type 2, filtered joins, alternative keys, multi-entity references. |

> Honeydew does not validate cardinality for `connection_expr` joins — you are responsible for ensuring correct many-to-one semantics.
