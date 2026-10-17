# Attribute Reference

## SQL Reference

| Category                | Functions / Syntax                                                                                 |
| ----------------------- | -------------------------------------------------------------------------------------------------- |
| **Safe division**       | `DIV0(numerator, denominator)`                                                                     |
| **Null-safe equality**  | `IS [NOT] DISTINCT FROM`                                                                           |
| **Math**                | `LOG(base, expr)`                                                                                  |
| **String position**     | `POSITION(substring, string)`                                                                      |
| **Substring**           | `SUBSTRING(str, start_position [, length])`                                                        |
| **Concatenate**         | `\|\|` operator                                                                                    |
| **Regular expressions** | `REGEXP_LIKE(subject, pattern)`                                                                    |
| **Full-text search**    | `SEARCH(field, 'terms', SEARCH_MODE => 'AND')` — Snowflake only, always use `SEARCH_MODE => 'AND'` |
| **Phonetic**            | `SOUNDEX(string)`                                                                                  |
| **Array search**        | `ARRAY_CONTAINS(array, value)`                                                                     |
| **Running total**       | `SUM(x) OVER (ORDER BY … ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`                        |
| **Date truncation**     | `DATE_TRUNC(part, expr)`                                                                           |
| **Date extraction**     | `EXTRACT(part FROM expr)`                                                                          |
| **Date casting**        | Cast between DATE and STRING                                                                       |

## Semi-Structured Data (JSON)

| Function                              | Use                                                                                   |
| ------------------------------------- | ------------------------------------------------------------------------------------- |
| `GET_PATH(field, path)`               | Get elements: `.key` for keys, `[idx]` for arrays                                     |
| `PARSE_JSON(str)`                     | Parse JSON string, then use GET_PATH                                                  |
| `JSON_EXTRACT_PATH_TEXT(field, path)` | Get JSON element as VARCHAR                                                           |
| `PARSE_URL(field)`                    | Returns JSON with `fragment`, `host`, `parameters`, `path`, `port`, `query`, `scheme` |

> JSON values must be cast after extraction: `GET_PATH(field, 'data.users[0].name')::string`

## Geography

| Function              | Use                                          |
| --------------------- | -------------------------------------------- |
| `TO_GEOGRAPHY(field)` | From WKT/EWKT/GeoJSON string (auto-detected) |
| `ST_POINT(lon, lat)`  | From longitude and latitude                  |

## Data Types

Every attribute has a data type. Choose based on the expression result:

| Data Type   | When to use                                                             |
| ----------- | ----------------------------------------------------------------------- |
| `string`    | **Default for text.** Categories, labels, identifiers, parsed JSON text |
| `number`    | Integer values: counts, IDs, ranks                                      |
| `float`     | Decimal values: amounts, ratios, calculated prices                      |
| `bool`      | True/false flags, conditions                                            |
| `date`      | Calendar date (no time component)                                       |
| `timestamp` | Date and time                                                           |
| `time`      | Time of day only                                                        |

## Full YAML Schema

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
format_string: <optional, for numeric or date types>
timegrain: day|week|month|quarter|year # date/timestamp only
labels: []
folder: <optional folder path>
```

## Attribute Types

| Type                   | Purpose                                                  | When to choose                                           |
| ---------------------- | -------------------------------------------------------- | -------------------------------------------------------- |
| **Basic**              | Row-level expression on a single entity                  | Arithmetic, string manipulation, simple conditionals     |
| **Multi-Entity**       | References columns from a related entity via many-to-one | Cross-entity calculations like `quantity × unit_cost`    |
| **Aggregation**        | Summarizes rows from a higher-granularity related entity | "Total line items on this order" from a many-side entity |
| **Grouping / Binning** | Buckets or categorizes a value                           | Revenue tiers, age bands, status labels                  |
| **Window Function**    | Ranking or partitioning without collapsing rows          | `RANK()`, `ROW_NUMBER()`, `LAG()`, `LEAD()`              |
| **Semi-Structured**    | Unpacks JSON or array fields                             | Parsing nested metadata, event properties                |
| **Lookup**             | Tests membership in a reference entity                   | Flag rows whose value appears in a curated list          |

## Time Grain (date/timestamp only)

Sets the finest granularity BI tools use when grouping this date column:

`microsecond` | `millisecond` | `second` | `minute` | `hour` | `day` | `week` | `month` | `quarter` | `year`

## Format Strings

Use `format_string` to control how attribute values display in BI tools.
Applies to numeric and date types.
Uses spreadsheet-style format expressions (Excel syntax).

| Format      | Renders as | Use for                          |
| ----------- | ---------- | -------------------------------- |
| `#,##0`     | 1,234      | Integer with thousands separator |
| `#,##0.00`  | 1,234.56   | Two decimal places               |
| `$#,##0`    | $1,234     | Currency without decimals        |
| `$#,##0.00` | $1,234.56  | Currency with decimals           |
| `0%`        | 12%        | Percentage without decimals      |
| `0.00%`     | 12.34%     | Percentage with decimals         |
