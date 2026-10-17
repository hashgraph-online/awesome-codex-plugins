# Entity Examples

## Physical table — orders entity

Call `create_entity` with:

**entity_yaml:**

```yaml
type: entity
name: orders
display_name: Orders
description: |-
  One row per customer order. Granularity is the unique order ID.
owner: data-team
keys:
  - order_id
key_dataset: orders_source
```

**dataset_yaml:**

```yaml
type: dataset
entity: orders
name: orders_source
dataset_type: table
sql: ANALYTICS.PUBLIC.ORDERS
attributes:
  - column: ORDER_ID
    name: order_id
    display_name: Order ID
    datatype: number
  - column: ORDER_DATE
    name: order_date
    display_name: Order Date
    datatype: date
    timegrain: day
  - column: ORDER_TOTAL
    name: order_total
    display_name: Order Total
    datatype: float
  - column: STATUS
    name: status
    display_name: Status
    datatype: string
  - column: CUSTOMER_ID
    name: customer_id
    display_name: Customer ID
    datatype: number
```

## Custom SQL — filtered entity (active customers only)

Call `create_entity` with:

**entity_yaml:**

```yaml
type: entity
name: active_customers
display_name: Active Customers
description: |-
  Customers who have placed at least one order in the last 12 months.
owner: data-team
keys:
  - customer_id
key_dataset: active_customers_source
```

**dataset_yaml:**

```yaml
type: dataset
entity: active_customers
name: active_customers_source
dataset_type: sql
sql: |-
  SELECT *
  FROM ANALYTICS.PUBLIC.CUSTOMERS
  WHERE CUSTOMER_ID IN (
    SELECT DISTINCT CUSTOMER_ID
    FROM ANALYTICS.PUBLIC.ORDERS
    WHERE ORDER_DATE >= DATEADD('year', -1, CURRENT_DATE)
  )
attributes:
  - column: CUSTOMER_ID
    name: customer_id
    display_name: Customer ID
    datatype: number
  - column: CUSTOMER_NAME
    name: customer_name
    display_name: Customer Name
    datatype: string
```

## Virtual entity — market segment derived from customers

Call `create_entity` with:

**entity_yaml:**

```yaml
type: entity
name: market_segments
display_name: Market Segments
description: |-
  Unique market segments extracted from the customers entity.
  Virtual — no physical table backing.
keys:
  - market_segment
key_dataset: market_segments_source
```

**dataset_yaml:**

```yaml
type: dataset
entity: market_segments
name: market_segments_source
dataset_type: entity
sql: customers
attributes:
  - column: market_segment
    name: market_segment
    display_name: Market Segment
    datatype: string
```

## Time spine — date dimension

Call `create_entity` with:

**entity_yaml:**

```yaml
type: entity
name: dates
display_name: Dates
description: |-
  Calendar date dimension. Used as the time spine for all time-aware metrics.
keys:
  - date_day
key_dataset: dates_source
is_time_spine: true
```

**dataset_yaml:**

```yaml
type: dataset
entity: dates
name: dates_source
dataset_type: table
sql: ANALYTICS.PUBLIC.DIM_DATE
attributes:
  - column: DATE_DAY
    name: date_day
    display_name: Date
    datatype: date
    timegrain: day
  - column: WEEK_START
    name: week_start
    display_name: Week Start
    datatype: date
    timegrain: week
  - column: MONTH_START
    name: month_start
    display_name: Month Start
    datatype: date
    timegrain: month
```

## Update existing entity

Call `update_object` with:

- `yaml_text`: the updated entity YAML
- `object_key`: the entity's object key (find via `list_entities` or `search_model`)

## Delete entity

Call `delete_object` with:

- `object_key`: the entity's object key
