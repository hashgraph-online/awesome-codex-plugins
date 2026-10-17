# Domain Examples

## Basic — entity selection only

Call `create_object` with yaml_text:

```yaml
type: domain
name: sales_analytics
display_name: Sales Analytics
description: |-
  Domain for the sales team. Includes orders, customers, and products
  for revenue analysis and customer segmentation.
owner: sales-team
entities:
  - name: orders
  - name: customers
  - name: products
```

## Domain with semantic filters

Semantic filters apply to every query in the domain, even if the filtered entity isn't directly referenced.

Call `create_object` with yaml_text:

```yaml
type: domain
name: completed_orders
display_name: Completed Orders
description: |-
  Scoped to completed orders only. Used by the fulfillment team
  to analyze shipped and delivered orders.
owner: fulfillment-team
entities:
  - name: orders
  - name: customers
  - name: line_items
filters:
  - name: completed_only
    sql: orders.status = 'completed'
    description: Only include completed orders
```

## Domain with source filters

Source filters apply early at the source level — only when the entity is part of the query. Use for performance optimization on partitioned data.

Call `create_object` with yaml_text:

```yaml
type: domain
name: recent_orders
display_name: Recent Orders
description: |-
  Performance-optimized domain. Source filter limits orders to recent
  data to leverage date partitioning.
owner: data-team
entities:
  - name: orders
  - name: customers
  - name: line_items
source_filters:
  - name: recent_data
    sql: orders.order_date >= '2024-01-01'
    description: Limit to recent orders for partition pruning
```

## Domain with field selectors

Field selectors support wildcards and exclusion patterns, evaluated in order.

Call `create_object` with yaml_text:

```yaml
type: domain
name: marketing_view
display_name: Marketing View
description: |-
  Restricted view for marketing team. Hides PII fields
  from customers. Exposes only product category fields.
owner: marketing-team
entities:
  - name: customers
    fields:
      - "*"
      - -ssn
      - -phone_number
      - -email
  - name: orders
  - name: products
    fields:
      - product_id
      - category
      - subcategory
```

## Domain for deep analysis context

Creating a focused domain to use with `ask_deep_analysis_question`.

Call `create_object` with yaml_text:

```yaml
type: domain
name: revenue_analysis
display_name: Revenue Analysis
description: |-
  Focused domain for revenue deep-dives. Semantic filter ensures
  only completed orders are included in all analysis.
owner: finance-team
entities:
  - name: orders
  - name: customers
  - name: products
  - name: line_items
filters:
  - name: completed_orders
    sql: orders.status = 'completed'
source_filters:
  - name: recent_data
    sql: orders.order_date >= '2024-01-01'
    description: Partition pruning for performance
```

Then use the domain for analysis:

```python
ask_deep_analysis_question(
  question="What were the top revenue drivers? Break down by product category and customer segment.",
  domain="revenue_analysis"
)
```

## Domain with parameter-based filter

Call `create_object` with yaml_text:

```yaml
type: domain
name: tenant_scoped
display_name: Tenant Scoped
description: |-
  Multi-tenant domain. Filters all data to the current user's tenant
  via the $TENANT parameter.
owner: platform-team
entities:
  - name: orders
  - name: customers
  - name: products
filters:
  - name: tenant_filter
    sql: dim_tenant.tenant_id = $TENANT
parameters:
  - name: TENANT
    value: "default"
```

## Update existing domain

1. Use `search_model` to find the domain's `object_key`.
2. Call `update_object` with `object_key` and yaml_text:

```yaml
type: domain
name: sales_analytics
display_name: Sales Analytics
description: |-
  Domain for the sales team. Updated to include line items
  and campaign data for deeper analysis.
owner: sales-team
entities:
  - name: orders
  - name: customers
  - name: products
  - name: line_items
  - name: campaigns
```

## Delete domain

1. Use `search_model` to find the domain's `object_key`.
2. Call `delete_object` with that `object_key`.
