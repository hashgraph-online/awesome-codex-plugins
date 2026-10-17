---
name: context-item-creation
description: Guides you through creating context items — instructions, skills, knowledge pointers, and memory events — that give the AI analyst persistent knowledge about your organization. Covers when to create each type, naming conventions, folder organization, and the hard boundary between context (rules and procedures) and the semantic layer (logic and calculations).
---

## Prerequisites

Before creating context items, ensure you are on the correct workspace and branch. Use `get_session_workspace_and_branch` to check the current session context. For development work, create a branch with `create_workspace_branch` (the session switches automatically). See the `model-exploration` skill for the full workspace/branch tool reference.

---

## Overview

**Context items** are the mechanism for giving the AI analyst persistent, organizational knowledge: standing rules it must always follow, on-demand procedures it can retrieve, external references it can look up, and a historical record of notable events.

Context items belong to the **context layer** — they are consumed by the Honeydew AI analyst at query time to shape its behavior. They are separate from the **semantic layer** (entities, metrics, attributes, relations, domains), which defines your data model and business logic such as metric calculations.

There are four types:

| Type | Subtype | When retrieved | Use for |
|---|---|---|---|
| **Instruction** | `instruction` | Every prompt, automatically | Short standing rules or constraints the model must always respect |
| **Skill** | `skill` | On demand, when relevant | Long-form analysis playbooks and procedural guides |
| **Knowledge** | `knowledge` | On demand, when relevant | Pointers to external content (Confluence, Notion, etc.) |
| **Memory** | `event` | On demand, when relevant | Historical events and decisions that affect data interpretation |

> **Before creating anything, read the critical boundary section below.** Most requests for context items are actually requests to define or document logic — which belongs in the semantic layer, not in context.

---

## THE HARD BOUNDARY: Context vs. Semantic Layer

> **This is the most important rule in this skill. Re-read it every time you are asked to create a context item.**

**Context items are for rules, procedures, and history. They are NOT for logic, calculations, or data definitions.**

If the information describes *how to compute something*, *what a value means mathematically*, or *how data is structured* — it belongs in the **semantic layer** (as a metric, attribute, filter, relationship, or entity definition), not in a context item.

### When to use the Semantic Layer instead

| Request | ❌ Wrong approach | ✅ Correct approach |
|---|---|---|
| "Add a rule that revenue = price × quantity" | Instruction: "revenue is price × quantity" | Calculated attribute or metric with `sql: orders.price * orders.quantity` |
| "Explain how to calculate LTV" | Instruction with formula | Metric with the LTV SQL expression |
| "Document that active customers are those with an order in 90 days" | Instruction with definition | Calculated attribute `is_active` with `sql: orders.last_order_date >= CURRENT_DATE - 90` |
| "Add a rule that we always filter to the current fiscal year" | Instruction with filter logic | Domain filter or global parameter — *unless* the preference is about which existing filter to apply, in which case an instruction referencing the filter by name is fine |
| "Record that the orders table has columns order_id, customer_id..." | Knowledge item | Entity and dataset definition via `entity-creation` skill |
| "Add a note that revenue excludes returns" | Instruction | Metric `sql` with `FILTER (WHERE NOT orders.is_return)`, plus a clear `description` on the metric |

### What context items ARE good for

- **Instructions**: A standing preference that refers to existing semantic objects, not logic. "Always use `orders.net_revenue` rather than `orders.gross_revenue` for revenue questions."
- **Skills**: A multi-step analytical procedure: "To investigate churn, start by segmenting cohorts, then compare retention curves, then identify the inflection point."
- **Knowledge**: A pointer to external policy documents, runbooks, or reference material.
- **Memory/Events**: "On 2024-03-01 we redefined revenue to exclude refunds — historical data was backfilled."

**The test:** Can you express this as a SQL expression or a schema definition? If yes, it belongs in the semantic layer. Context items should reference semantic objects by name, not define or duplicate their logic.

---

## MCP Tools

### create_context_item

Call `create_context_item` with the frontmatter fields as `context_item` parameters and the prose body as `markdown_text`.

### After Creation/Update: Display the UI Link

After a successful `create_context_item` or `update_context_item` call, the response includes a `ui_url` field. **Always display this URL to the user** so they can quickly open the item in the Honeydew application.

### update_context_item

To modify an existing context item:

1. Call `get_context_item` with the item's name to read its current content.
2. Call `update_context_item` with the item's `name` and the updated `context_item` fields and `markdown_text`.

> **Minimal diff rule:** Only change the fields you need to modify. Context items are versioned in git, so unnecessary reformatting creates noisy diffs.

### delete_context_item

Call `delete_context_item` with the item's `name`.

| Task | Tool |
|---|---|
| Create | `create_context_item` |
| Update | `update_context_item` |
| Delete | `delete_context_item` |
| Get one | `get_context_item` |
| List all | `list_context_items` |

---

## Naming and Organization

### Name format

Names use `folder/item-name` with lowercase kebab-case and `/` as a hierarchy separator:

```
finance/use-net-revenue
customer/churn-analysis-playbook
confluence/data-governance-policy
finance/revenue-redefinition-2024
```

A flat name (no folder) is fine when the item is genuinely cross-cutting:

```
root-cause-analysis
gdpr-compliance-rollout
```

### Why folders matter — agent scoping

When configuring an AI agent, context items are referenced using **glob patterns**. Folders let you include a coherent group of items with a single pattern:

- `finance/*` — all finance-specific rules and skills
- `customer/*` — all customer analysis guidelines
- `*/churn-*` — all churn-related items regardless of team folder
- `menu/**` — all items under `menu/` including subfolders (e.g. `menu/drinks/latte-art`)
- `**` — all context items across all folders and subfolders (use sparingly; typically for a catch-all agent)

**Organize by the team or domain that owns the context**, not by the item type. Items of different types (instruction + skill + knowledge) for the same domain belong in the same folder:

```
finance/use-net-revenue         ← instruction
finance/variance-analysis       ← skill
finance/accounting-policy       ← knowledge
finance/revenue-redefinition    ← memory
```

This way, an agent configured with `finance/*` automatically gets all finance context.

### Naming best practices

- Use the folder to reflect ownership, not to repeat the item type. `finance/use-net-revenue` is good. `instructions/use-net-revenue` is redundant.
- Name after the concept or rule, not the implementation. `exclude-canceled-orders` is better than `filter-status-not-canceled`.
- For memory events, name after the event itself, not a generic label. `revenue-redefinition` or `gdpr-rollout` beats `data-change-3`.

---

## Frontmatter format

Context items are stored as frontmatter documents: a YAML block between `---` delimiters, followed by a markdown prose body. When calling `create_context_item`, pass the YAML fields as `context_item` parameters and the prose body as the `markdown_text` parameter.

The `description` field is the **retrieval signal** — the model reads it to decide whether to fetch an on-demand item. It is **used for skills, knowledge, and memory events**. Do not add `description` to instructions; their only content is the prose body.

See [examples.md](examples.md) for what the full frontmatter documents look like.

---

## Type Reference

### Instruction — standing rule (always on)

**Use when:** There is a standing preference, constraint, or fact that the model must respect in every conversation. These are injected into every prompt automatically.

**Keep instructions concise.** They are never filtered out, so verbose instructions bloat every prompt. If the content is more than a short paragraph, turn it into a skill instead.

**Parameters:**
- `type`: `instruction`
- `subtype`: `instruction`
- `name`: `folder/rule-name`
- `title`: short human label
- prose body: **the rule text** — what the model must do or avoid
- `related_objects`: *(optional)* only the fields or entities directly named or constrained by this instruction — not downstream consumers, not lineage, not entities that happen to join to a relevant one; use an entity reference instead of a field list when the instruction applies to most fields of that entity
- `labels`: optional tags for grouping
- `owner`: *(optional)* defaults to the caller; only set if a different team or person should be listed

**Good instruction topics:**
- Metric selection preferences ("always use net_revenue")
- Domain-specific constraints ("exclude test accounts from all analyses")
- Terminology corrections ("what users call 'bookings' maps to the `orders.gmv` metric")

### Skill — on-demand playbook

**Use when:** There is a multi-step analysis procedure the model should follow when asked about a specific topic. Skills are retrieved when the model judges them relevant based on the description.

**Write a rich, keyword-dense `description`** — this is what the model reads to decide whether to retrieve the skill. A weak description means the skill will be missed.

**Parameters:**
- `type`: `instruction`
- `subtype`: `skill`
- `name`: `topic-or-folder/topic`
- `title`: short human label
- `description`: **required** — precise, keyword-rich description of when to use this skill and what it covers (this is the retrieval signal)
- prose body: **the playbook** — step-by-step guide written in markdown (goes after the closing `---`)
- `labels`: optional tags for grouping
- `owner`: *(optional)* defaults to the caller

**Good skill topics:**
- Root cause analysis procedures
- Customer cohort or churn investigation workflows
- Reporting preparation checklists
- Domain-specific investigation playbooks

### Knowledge — external source pointer

**Use when:** There is an external document (Confluence page, Notion database, runbook, policy) that the model should consult when answering relevant questions. The model fetches the content via an MCP server at retrieval time.

**Write a precise `description`** that includes the topics the document covers — this is the retrieval signal.

**Parameters:**
- `type`: `instruction`
- `subtype`: `knowledge`
- `name`: `source-folder/document-name`
- `title`: short human label
- `description`: **required** — what topics this document covers (used for retrieval)
- `external_source.tool`: the MCP server name (e.g. `confluence`, `notion`)
- `external_source.resource_id`: the URI within that server (e.g. `confluence://Page-Title`)
- prose body: typically omit — the content is fetched from the external source at runtime
- `labels`: optional tags for grouping
- `owner`: *(optional)* defaults to the caller

### Memory / Event — historical record

**Use when:** Something happened that affects how data should be interpreted: a metric was redefined, a process changed, a data migration occurred, a business event shifted baseline numbers.

Memory items are retrieved on demand when the model judges them relevant to the current question.

**Parameters:**
- `type`: `memory`
- `subtype`: `event`
- `name`: `domain/event-name`
- `title`: short human label
- `description`: **required** — what this event is about (used for retrieval)
- prose body: **what happened and why it matters** for data interpretation
- `from_date`: when the event occurred (point-in-time) or when it started (if a duration)
- `to_date`: *(optional)* end date for events spanning a period
- `related_objects`: *(optional)* only the fields or entities directly changed or affected by this event — not downstream consumers, not lineage, not entities that happen to join to a relevant one; use an entity reference instead of a field list when the event affects most fields of that entity
- `labels`: optional tags for grouping
- `owner`: *(optional)* defaults to the caller

**Good memory topics:**
- Metric or definition changes with a specific effective date
- ETL migrations or data backfills
- Significant business events (acquisitions, product launches) that cause discontinuities in data
- Changes in how data is collected or tagged

---

## Examples

See [examples.md](examples.md) for full worked examples of each type, plus right-vs-wrong comparisons.

---

## Discovery Helpers

- `list_context_items` — see all existing items (avoid duplicates)
- `get_context_item` — read a specific item's current content before updating
- `list_agents` / `get_agent` — see which agents reference which context globs, to understand the scoping impact of adding a new item

---

## Documentation Lookup

Use the `honeydew-docs` MCP tools to search the Honeydew documentation when:

- You need to understand how context items interact with agents or how retrieval works
- The user asks about agent configuration, glob patterns, or context scoping
- You need guidance on memory subtypes or advanced context item options

Search for topics like: "context items", "instructions", "agent context", "memory events", "skills".

---

## Best Practices

1. **Semantic layer first.** If the request is about logic, calculations, definitions, or data structure — build it in the semantic layer. Context items reference semantic objects; they do not replace them.

2. **Instructions must be short.** They're injected into every prompt. If it doesn't fit in 2–3 sentences, turn it into a skill.

3. **Skill descriptions are the retrieval key.** Write rich, specific, keyword-heavy descriptions. "Guide for root cause analysis of revenue drops, covering cohort isolation, period-over-period comparison, and funnel decomposition" is far better than "revenue analysis".

4. **Folder by domain, not by type.** `finance/` should contain instructions, skills, knowledge, and events all related to finance. This makes agent glob patterns meaningful.

5. **Check for duplicates before creating.** Run `list_context_items` first. Overlapping or contradictory instructions are worse than none.

6. **Use labels for cross-cutting concerns.** Labels like `pii`, `finance`, or `deprecated` enable filtering that cuts across folder hierarchy.

---

## MANDATORY: Confirm You Are Not Duplicating Semantic Layer Logic

Before creating any context item, verify:

1. **Does this describe a calculation or data definition?** → Build it as a metric, attribute, or filter instead.
2. **Does this duplicate something already in the semantic layer?** → Update the semantic object's `description` field instead of adding context.
3. **Is this a preference that references an existing metric by name?** → Good candidate for an instruction.

If you are unsure, ask the user: *"Should I add this as a rule for the AI analyst, or should I encode it directly in the semantic layer as a metric/attribute?"*
