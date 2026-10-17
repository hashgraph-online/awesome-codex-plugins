# Context Item Examples

Context items are frontmatter documents: a YAML block followed by a markdown prose body. Examples below show the full document as it would be stored.

---

## Right vs. Wrong — The Semantic Layer Boundary

These are the most common mistakes. Check these before creating anything.

### ❌ Wrong: encoding calculation logic in an instruction

```
---
type: instruction
subtype: instruction
name: revenue-calculation
title: Revenue calculation rule
---
Revenue should be calculated as price multiplied by quantity, minus discounts.
```

**Why wrong:** This is SQL logic. It belongs in a metric.

### ✅ Correct: create a metric instead

Use `create_object`:

```yaml
type: metric
entity: orders
name: net_revenue
display_name: Net Revenue
description: Revenue after discounts
owner: finance-team
datatype: float
sql: SUM(orders.price * orders.quantity - orders.discount_amount)
```

Then, if you want the AI to always prefer this metric, create an instruction that **refers to it by name**:

```
---
type: instruction
subtype: instruction
name: finance/use-net-revenue
title: Use net revenue for revenue questions
labels: [finance]
related_objects:
- name: orders.net_revenue
  type: field
- name: orders.gross_revenue
  type: field
---
Always use `orders.net_revenue` for any revenue-related analysis.
Do not use `orders.gross_revenue` unless the user explicitly requests gross figures.
```

---

### ❌ Wrong: documenting table structure in a knowledge item

```
---
type: instruction
subtype: knowledge
name: orders-schema
title: Orders table schema
---
The orders table has columns: order_id, customer_id, amount, status, created_at...
```

**Why wrong:** Table structure belongs in entities and datasets (see `entity-creation` skill).

---

### ❌ Wrong: encoding a segment definition in an instruction

```
---
type: instruction
subtype: instruction
name: active-customer-definition
title: Active customer definition
---
Active customers are those who have placed an order in the last 90 days.
```

**Why wrong:** This is a filter expression. It belongs as a calculated attribute `is_active` with `sql: orders.last_order_date >= CURRENT_DATE - 90`, so it can be used in queries.

---

## Instruction — Standing Rule

**Scenario:** The finance team always wants net revenue used in reports, not gross.

```
---
type: instruction
subtype: instruction
name: finance/use-net-revenue
title: Always use net revenue
labels: [finance]
related_objects:
- name: orders.net_revenue
  type: field
- name: orders.gross_revenue
  type: field
---
For all revenue analyses, use `orders.net_revenue` (which excludes returns and discounts).
Use `orders.gross_revenue` only when the user explicitly requests gross figures.
Never mix gross and net in the same analysis without labeling which is which.
```

---

## Skill — Analysis Playbook

**Scenario:** The team has a standard procedure for investigating revenue drops.

```
---
type: instruction
subtype: skill
name: finance/revenue-drop-investigation
title: Revenue Drop Investigation Playbook
description: Step-by-step guide for investigating unexpected revenue drops. Covers: isolating the time period, segmenting by product line and geography, comparing acquisition vs. retention contribution, identifying order count vs. average order value decomposition, and ruling out data quality issues. Use when asked to diagnose or explain a revenue decline, shortfall, or anomaly.
labels: [finance, investigation]
---
## Revenue Drop Investigation

1. **Isolate the time period** — compare the drop window to the prior equivalent period (e.g., same week last month, same month last year) using `get_data_from_fields` with `orders.net_revenue` grouped by date.
2. **Segment by product line and geography** — break down the affected period by `orders.product_line` and `orders.region` to identify where the drop is concentrated.
3. **Decompose order count vs. average order value** — check whether the drop is driven by fewer orders (`orders.order_count`) or lower per-order value (`orders.avg_order_value`).
4. **Compare acquisition vs. retention contribution** — split by `customers.is_new` to determine if new or returning customers are driving the change.
5. **Rule out data quality** — verify that total record counts for the period look normal; a sharp drop may indicate a data pipeline issue rather than a business change.
```

---

## Skill — Domain Playbook

**Scenario:** Customer success has a procedure for churn root-cause analysis.

```
---
type: instruction
subtype: skill
name: customer/churn-investigation
title: Customer Churn Investigation Playbook
description: Procedure for diagnosing elevated customer churn. Covers cohort isolation by signup month, retention curve comparison across cohorts, engagement signal correlation (logins, feature usage), and identification of the lifecycle stage where drop-off occurs. Use when asked to investigate, explain, or predict customer churn or retention changes.
labels: [customer, churn]
---
## Churn Investigation Playbook

1. **Isolate the cohort** — group customers by `customers.signup_month` and compute `customers.churn_rate` per cohort to identify whether churn is elevated for a specific signup period or broadly across all cohorts.
2. **Compare retention curves** — plot `customers.retention_rate` over months-since-signup for the elevated cohort vs. healthy cohorts to find the lifecycle stage where drop-off occurs.
3. **Check engagement signals** — compare `customers.avg_monthly_logins` and `customers.feature_adoption_score` between churned and retained customers in the same cohort.
4. **Identify product or plan correlation** — break down churn by `customers.plan_tier` and `customers.primary_use_case` to find if a specific segment is disproportionately affected.
5. **Check for external events** — consult memory items for any changes around the cohort's signup date (pricing changes, product updates, support issues) that might explain the pattern.
```

---

## Knowledge — External Document

**Scenario:** The data governance team has a Confluence page defining metric ownership rules.

```
---
type: instruction
subtype: knowledge
name: confluence/data-governance-policy
title: Data Governance Policy
description: Official data governance policy covering metric ownership rules, definition change approval process, PII handling requirements, and data quality SLAs. Retrieve when the user asks about who owns a metric, how to request a metric change, or data quality standards.
external_source:
  tool: confluence
  resource_id: confluence://Data-Governance-Policy
labels: [governance]
---
```

No body needed — the content is fetched from the external source at retrieval time.

---

## Memory / Event — Point-in-Time Change

**Scenario:** On March 1, 2024, the revenue metric was redefined to exclude refunds.

```
---
type: memory
subtype: event
name: finance/revenue-redefinition-2024
title: Revenue metric redefined to exclude refunds
from_date: 2024-03-01
labels: [finance, metric-change]
related_objects:
- name: orders.net_revenue
  type: field
- name: orders.gross_revenue
  type: field
---
The revenue metric was redefined to exclude refund transactions. Historical data was backfilled to 2020-01-01. Any trend analysis crossing March 2024 is consistent; data before 2020 retains the old definition and is not comparable.
```

---

## Memory / Event — Duration Event

**Scenario:** A migration ran for two weeks and caused incomplete order data during that window.

```
---
type: memory
subtype: event
name: eng/orders-migration-data-gap
title: Orders table migration — incomplete data window
from_date: 2024-07-10
to_date: 2024-07-24
labels: [data-quality, migration]
related_objects:
- name: orders
  type: entity
- name: orders.order_count
  type: field
- name: orders.net_revenue
  type: field
---
During the orders table migration, approximately 8% of order records were dropped due to a join key mismatch. Order counts and revenue metrics for July 10–24, 2024 are understated. The gap was not backfilled. Flag this period as unreliable in any trend analysis.
```

---

## Organization Example — Finance Domain Agent

All four types of context item organized under a `finance/` folder, so a finance agent can reference them with `finance/*`:

```
finance/use-net-revenue            ← instruction: always use net_revenue
finance/revenue-drop-investigation ← skill: investigation playbook
finance/variance-analysis          ← skill: variance analysis procedure
finance/accounting-policy          ← knowledge: Confluence → accounting standards doc
finance/revenue-redefinition-2024  ← memory: metric definition change event
finance/orders-migration-gap       ← memory: data quality event
```

An agent configured with context glob `finance/*` automatically loads all of these. Adding a new finance item to the folder extends the agent without any configuration change.
