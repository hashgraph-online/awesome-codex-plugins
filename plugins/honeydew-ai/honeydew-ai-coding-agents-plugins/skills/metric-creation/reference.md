# Metric Reference

## Aggregation Functions

| Category               | Functions                                                                                                    |
| ---------------------- | ------------------------------------------------------------------------------------------------------------ |
| **Numeric**            | `AVG`, `COUNT`, `MAX`, `MIN`, `MEDIAN`, `SUM`                                                                |
| **Max/min by column**  | `MIN_BY`, `MAX_BY`                                                                                           |
| **Concatenate**        | `LISTAGG`                                                                                                    |
| **Statistics**         | `CORR`, `COVAR_POP`, `COVAR_SAMP`, `MODE`, `STDDEV`, `STDDEV_POP`, `VAR_POP`, `VAR_SAMP`, `KURTOSIS`, `SKEW` |
| **Approximate**        | `APPROX_COUNT_DISTINCT`, `APPROXIMATE_SIMILARITY`, `APPROX_PERCENTILE`                                       |
| **Bitwise**            | `BITAND_AGG`, `BITOR_AGG`, `BITXOR_AGG`                                                                      |
| **Boolean**            | `BOOLAND_AGG`, `BOOLOR_AGG`, `BOOLXOR_AGG`                                                                   |
| **Text summarization** | `AI_SUMMARIZE_AGG`, `AI_AGG`                                                                                 |

## Filtered Aggregations

Apply a filter to any aggregation with `FILTER (WHERE ...)`:

```sql
SUM(orders.price) FILTER (WHERE orders.color = 'red')
```

> For complete filter expression syntax (comparisons, strings, SEARCH, dates, booleans, combined conditions) and date handling functions, see the **filtering** skill.

## Text Summarization

- `AI_SUMMARIZE_AGG(account.churn_reason)` — get a summary of a text column
- `AI_AGG(reservation.reviews, 'Describe common complaints')` — reduce text with a natural language instruction

## Data Types

Every metric has a data type. Choose based on the aggregation result:

| Data Type   | When to use                                                 |
| ----------- | ----------------------------------------------------------- |
| `float`     | **Default for most metrics.** SUM, AVG, ratios, percentages |
| `number`    | Integer results: COUNT, COUNT DISTINCT                      |
| `string`    | Text aggregations: LISTAGG, AI_SUMMARIZE_AGG, AI_AGG        |
| `bool`      | Boolean aggregations: BOOLAND_AGG, BOOLOR_AGG               |
| `date`      | Date aggregations: MIN/MAX on dates                         |
| `timestamp` | Timestamp aggregations                                      |
| `time`      | Time aggregations                                           |

> **Default to `float`** unless the metric is clearly a count (use `number`) or text (use `string`).

## Metric Types

| Type                   | Purpose                            | Example                                |
| ---------------------- | ---------------------------------- | -------------------------------------- |
| **Basic**              | Standard SQL aggregation           | `SUM(orders.amount)`                   |
| **Derived**            | Arithmetic on existing metrics     | `orders.revenue - orders.cost`         |
| **Filtered**           | Aggregation with fixed WHERE       | `SUM(orders.price) FILTER (WHERE ...)` |
| **Fixed Grouping**     | Always grouped by a dimension      | `metric GROUP BY (dim)`                |
| **Nested Aggregation** | Aggregation of grouped aggregation | `AVG(metric GROUP BY (*,dim))`         |

## Format Strings

Use `format_string` to control how metric values display in BI tools. Uses spreadsheet-style format expressions (Excel syntax). See https://customformats.com/ to help build expressions.

| Format      | Renders as | Use for                          |
| ----------- | ---------- | -------------------------------- |
| `#,##0`     | 1,234      | Integer with thousands separator |
| `#,##0.00`  | 1,234.56   | Two decimal places               |
| `$#,##0`    | $1,234     | Currency without decimals        |
| `$#,##0.00` | $1,234.56  | Currency with decimals           |
| `0%`        | 12%        | Percentage without decimals      |
| `0.00%`     | 12.34%     | Percentage with decimals         |
