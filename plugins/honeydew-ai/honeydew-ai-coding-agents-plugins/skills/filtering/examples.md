# Filtering Examples

## Metric Value Filters (Post-Aggregation)

### Only groups with more than 10 listings

Call `get_data_from_fields` with:

- `attributes`: `["detailed_listings.neighbourhood_cleansed"]`
- `metrics`: `["detailed_listings.count"]`
- `filters`: `["detailed_listings.count > 10"]`
- `order_by`: `["\"detailed_listings.count\" DESC"]`

### Find duplicate values (count > 1)

Call `get_data_from_fields` with:

- `attributes`: `["detailed_listings.host_name"]`
- `metrics`: `["COUNT(detailed_listings.host_name)"]`
- `filters`: `["COUNT(detailed_listings.host_name) > 1"]`
- `order_by`: `["\"COUNT(detailed_listings.host_name)\" DESC"]`

### High-revenue categories only

Call `get_data_from_fields` with:

- `attributes`: `["orders.category"]`
- `metrics`: `["orders.total_revenue"]`
- `filters`: `["orders.total_revenue > 10000"]`

## Pre-Aggregation Filters

### Combine multiple conditions

Call `get_data_from_fields` with:

- `attributes`: `["detailed_listings.neighbourhood_cleansed"]`
- `metrics`: `["detailed_listings.count"]`
- `filters`: `["detailed_listings.room_type = 'Entire home/apt'", "detailed_listings.price > 50"]`
- `order_by`: `["\"detailed_listings.count\" DESC"]`

### Date range filter

Call `get_data_from_fields` with:

- `attributes`: `["orders.category"]`
- `metrics`: `["orders.total_revenue"]`
- `filters`: `["orders.order_date >= '2024-01-01'", "orders.order_date < '2024-04-01'"]`

### Full-text search filter

Call `get_data_from_fields` with:

- `attributes`: `["detailed_listings.name"]`
- `metrics`: `["detailed_listings.count"]`
- `filters`: `["SEARCH(detailed_listings.name, 'cozy studio', SEARCH_MODE => 'AND')"]`
