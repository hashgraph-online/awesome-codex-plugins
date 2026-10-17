---
name: domain-creation
description: Guides you through creating a Honeydew domain — a governance object that scopes entity/field visibility and applies mandatory filters — ideal for setting up contexts for deep analysis.
---

## Prerequisites

Before creating domains, ensure you are on the correct workspace and branch. Use `get_session_workspace_and_branch` to check the current session context. For development work, create a branch with `create_workspace_branch` (the session switches automatically). See the `model-exploration` skill for the full workspace/branch tool reference.

---

## Overview

A Honeydew **domain** is a lightweight governance object that defines a scoped business context over the semantic model.

Domains control:

- **Which entities** are visible (and optionally which fields within them via field selectors)
- **Semantic filters** (`filters`) — applied to every query in the domain, for governance and access control
- **Source filters** (`source_filters`) — applied early at the source level, for performance optimization

Domains are the primary mechanism for creating focused, governed views of the model for specific teams, use cases, or analysis contexts.

> This skill focuses on domain creation and management.
> Use `entity-creation` to create entities and `attribute-creation` / `metric-creation` to add fields before scoping them into a domain.
> To expose a domain for AI analysis, create an agent referencing it using `create_agent` (MCP agent tools) or the Honeydew Studio agent builder.

---

## Creation Method

### create_object with YAML

Domains are created using `create_object` with domain YAML. There is no specialized `create_domain` tool.

Parameters:

- `yaml_text` — YAML defining the domain

Required permission: Editor or higher.

### Update: update_object

1. Use `search_model` (with `search_mode: EXACT`) to find the domain's `object_key`.
2. Call `update_object` with the full updated YAML (`yaml_text`) and the `object_key`.

> **Minimal diff rule:** When updating, preserve the existing field order and formatting from the current YAML. Only change the fields you need to modify.

### Delete: delete_object

1. Use `search_model` (with `search_mode: EXACT`) to find the domain's `object_key`.
2. Call `delete_object` with that `object_key`.

### After Creation/Update: Display the UI Link

After a successful `create_object` or `update_object` call, the response includes a `ui_url` field. **Always display this URL to the user** so they can quickly open the object in the Honeydew application.

---

## Decision Flow

```text
Need to create a domain?
    │
    ├─► Which entities should be included?
    │       └─► Use list_entities / search_model (OR mode) to discover available entities
    │
    ├─► Should all fields be visible, or only a subset?
    │       ├─► All fields → omit fields for that entity
    │       └─► Subset → use field selectors (supports wildcards and exclusions)
    │
    ├─► Are governance/access filters needed (apply to ALL queries)?
    │       └─► Use filters (semantic) with name + sql
    │
    └─► Are performance/source-level filters needed (apply only when entity is queried)?
            └─► Use source_filters with name + sql
```

---

## Examples

See [examples.md](examples.md) for full worked examples covering: basic entity selection, semantic filters, source filters, field selectors, deep analysis context and update/delete.

---

## Discovery Helpers

Use these MCP tools before creating domains:

- `list_entities` — List all entities in the model to decide which to include
- `get_entity` — Get detailed info for a specific entity (attributes, metrics, relations)
- `list_domains` — List all existing domains in the model
- `get_domain` — Get detailed info for a specific domain (entities, filters, parameters)
- `search_model` — Search for entities, fields, domains, or other objects by name (use `search_mode: EXACT` for known names, `OR` for broad discovery)
- `get_field` — Get detailed info about a specific field (attribute or metric)

---

See [reference.md](reference.md) for: full YAML schema, entity selection syntax, field selectors, filter types and syntax, and parameter overrides.

---

## Documentation Lookup

Use the `honeydew-docs` MCP tools to search the Honeydew documentation when:

- You need to understand governance concepts, domain design patterns, or access control strategies
- The user asks about the difference between semantic filters and source filters, or when to use each
- You need guidance on advanced modeling configurations like parameter overrides or complex field selectors
- The user asks about how domains interact with BI tools, queries, or the deep analysis API
- The user needs advanced modeling patterns for governance or multi-tenant access control

Search for topics like: "domains", "governance", "filters", "field selectors", "access control", "source filters".

---

## Best Practices

- **Name domains after the business context**, not technical details. `sales_analytics` is better than `filtered_orders_v2`.
- **Start broad, then narrow.** Include all relevant entities first, then add filters and field selectors as governance requirements emerge.
- **Always set `owner`** to identify the responsible team or person for governance and accountability.
- **Prefer semantic filters (`filters`) over source filters** for governance rules. Source filters apply before computation and can change calculated values.
- **Use source filters for performance** — they're ideal for partition pruning on large datasets.
- **Use `description`** to document the domain's purpose and intended audience clearly.
- **Keep domains focused.** A domain for "Sales Team" should only include entities and fields relevant to sales analysis.
- **Use field selectors sparingly.** Only restrict fields when there's a clear governance need (e.g. hiding PII from certain teams).
- **All filter `sql` references must be fully qualified.** Always use `entity.field` notation — unqualified references fail validation.

---

## MANDATORY: Validate After Creating

**After creating ANY domain, you MUST invoke the `validation` skill to test and validate that it works correctly.**

See `validation` skill for the full domain validation workflow.

### Validation steps:

1. **Verify domain exists** using `search_model` (with `search_mode: EXACT`) to find the new domain by name.

2. **Test with a query** — use `get_data_from_fields` with the `domain` parameter:

- `metrics`: `["<entity>.count"]`
- `domain`: `"<domain_name>"`

This verifies that the domain settings (e.g. filter) apply.
