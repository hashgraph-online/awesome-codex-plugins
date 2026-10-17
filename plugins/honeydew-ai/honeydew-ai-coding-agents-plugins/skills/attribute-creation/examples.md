# Attribute Examples

## Basic — net price after discount

Call `create_object` with yaml_text:

```yaml
type: calculated_attribute
entity: orders
name: net_price
display_name: Net Price
description: Order amount after applying discount
owner: data-team
datatype: float
sql: |-
  orders.amount * (1 - orders.discount_rate)
```

## Boolean flag — high spender

Call `create_object` with yaml_text:

```yaml
type: calculated_attribute
entity: users
name: is_high_spender
display_name: Is High Spender
description: Indicates if user has spent more than $1000 in total
owner: data-team
datatype: bool
sql: |-
  CASE WHEN users.total_spent > 1000 THEN TRUE ELSE FALSE END
```

## Grouping / Binning — order size tier

Call `create_object` with yaml_text:

```yaml
type: calculated_attribute
entity: orders
name: order_size_tier
display_name: Order Size Tier
description: Categorizes orders by amount
owner: data-team
datatype: string
sql: |-
  CASE
    WHEN orders.amount < 100 THEN 'Small'
    WHEN orders.amount < 1000 THEN 'Medium'
    ELSE 'Large'
  END
```

## Multi-Entity — extended cost using product price

Call `create_object` with yaml_text:

```yaml
type: calculated_attribute
entity: line_items
name: extended_cost
display_name: Extended Cost
description: Line item quantity times product unit cost
owner: data-team
datatype: float
sql: |-
  line_items.quantity * products.unit_cost
```

## Date truncation — order month

Call `create_object` with yaml_text:

```yaml
type: calculated_attribute
entity: orders
name: order_month
display_name: Order Month
description: Calendar month of the order
owner: data-team
datatype: date
sql: |-
  DATE_TRUNC('month', orders.order_date)
timegrain: month
```

## Window Function — customer revenue rank

Call `create_object` with yaml_text:

```yaml
type: calculated_attribute
entity: customers
name: revenue_rank
display_name: Revenue Rank
description: Customer rank by total revenue within region
owner: data-team
datatype: number
sql: |-
  RANK() OVER (PARTITION BY customers.region ORDER BY customers.total_revenue DESC)
```

## Running total — cumulative revenue

Call `create_object` with yaml_text:

```yaml
type: calculated_attribute
entity: orders
name: cumulative_revenue
display_name: Cumulative Revenue
description: Running total of order amounts
owner: data-team
datatype: float
sql: |-
  SUM(orders.amount) OVER (
    ORDER BY orders.order_date ROWS
    BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  )
```

## Semi-Structured — shipping city from JSON

Call `create_object` with yaml_text:

```yaml
type: calculated_attribute
entity: orders
name: shipping_city
display_name: Shipping City
description: City extracted from shipping JSON metadata
owner: data-team
datatype: string
sql: |-
  GET_PATH(orders.metadata, 'shipping.city')::string
```

## Safe division — conversion rate

Call `create_object` with yaml_text:

```yaml
type: calculated_attribute
entity: campaigns
name: conversion_rate
display_name: Conversion Rate
description: Conversions divided by impressions (safe division)
owner: data-team
datatype: float
sql: |-
  DIV0(campaigns.conversions, campaigns.impressions)
```

## Update existing attribute

1. Use `get_entity` or `search_model` to find the attribute's `object_key`.
2. Call `update_object` with `object_key` and yaml_text:

```yaml
type: calculated_attribute
entity: orders
name: net_price
display_name: Net Price
description: Order amount after discount and fees
owner: data-team
datatype: float
sql: |-
  orders.amount * (1 - orders.discount_rate) - orders.fees
```

## Delete attribute

1. Use `search_model` to find the attribute's `object_key`.
2. Call `delete_object` with that `object_key`.
