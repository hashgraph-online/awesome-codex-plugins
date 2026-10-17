# Metric Examples

## Basic — revenue metric

Call `create_object` with yaml_text:

```yaml
type: metric
entity: order_lines
name: revenue
display_name: Revenue
description: Total revenue from order line items
owner: data-team
datatype: float
sql: SUM(order_lines.price * order_lines.quantity)
```

## Derived — profit metric (price minus cost)

Call `create_object` with yaml_text:

```yaml
type: metric
entity: order_lines
name: profit
display_name: Profit
description: Revenue minus cost
owner: data-team
datatype: float
sql: SUM(order_lines.price - order_lines.order_cost)
```

## Filtered — promotional revenue only

Call `create_object` with yaml_text:

```yaml
type: metric
entity: order_lines
name: promo_revenue
display_name: Promotional Revenue
description: Revenue from promotional items only
owner: data-team
datatype: float
sql: order_lines.revenue FILTER (WHERE parts.type LIKE 'PROMO%')
```

## Ratio — promo revenue percentage

Call `create_object` with yaml_text:

```yaml
type: metric
entity: order_lines
name: promo_revenue_pct
display_name: Promo Revenue %
description: Percentage of revenue from promotions
owner: data-team
datatype: float
sql: 100 * order_lines.promo_revenue / order_lines.revenue
```

## Count — order count (never use COUNT(\*))

Call `create_object` with yaml_text:

```yaml
type: metric
entity: orders
name: order_count
display_name: Order Count
description: Total number of orders
owner: data-team
datatype: number
sql: COUNT(orders.order_id)
```

## Distinct count

Call `create_object` with yaml_text:

```yaml
type: metric
entity: orders
name: unique_customers
display_name: Unique Customers
description: Count of distinct customers
owner: data-team
datatype: number
sql: COUNT(DISTINCT orders.customer_id)
```

## Fixed Grouping — daily revenue share

Call `create_object` with yaml_text:

```yaml
type: metric
entity: order_lines
name: daily_revenue_share
display_name: Daily Revenue Share
description: Revenue share within each day
owner: data-team
datatype: float
sql: order_lines.revenue / order_lines.revenue GROUP BY (orders.order_date)
```

## Nested Aggregation — average daily revenue

Call `create_object` with yaml_text:

```yaml
type: metric
entity: order_lines
name: avg_daily_revenue
display_name: Average Daily Revenue
description: Average revenue per day
owner: data-team
datatype: float
sql: AVG(order_lines.revenue GROUP BY (*, orders.order_date))
```

## Text summary — churn reasons

Call `create_object` with yaml_text:

```yaml
type: metric
entity: accounts
name: churn_summary
display_name: Churn Summary
description: AI-generated summary of churn reasons
owner: data-team
datatype: string
sql: AI_SUMMARIZE_AGG(accounts.churn_reason)
```

## Update existing metric

1. Use `get_entity` or `search_model` to find the metric's `object_key`.
2. Call `update_object` with `object_key` and yaml_text:

```yaml
type: metric
entity: order_lines
name: revenue
display_name: Revenue
description: Total revenue with discount applied
owner: data-team
datatype: float
sql: SUM(order_lines.price * (1 - order_lines.discount) * order_lines.quantity)
```

## Delete metric

1. Use `search_model` to find the metric's `object_key`.
2. Call `delete_object` with that `object_key`.
