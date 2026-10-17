---
name: model-exploration
description: Use when exploring Honeydew semantic layer, discovering entities/fields, setting up workspace and branch context, or querying data. For creating metrics use metric-creation skill. For creating attributes use attribute-creation skill.
---

# Instructions

## When To Use This Skill

Before ANY Honeydew work, set up your session and discover the model:

**Step 0: Set workspace and branch**
Use `get_session_workspace_and_branch` to check the current session context. If no workspace/branch is set, use `list_workspaces`, `list_workspace_branches`, and `set_session_workspace_and_branch` to select the right workspace and branch. All subsequent tool calls use this context.

**Step 1: List entities**
Use the `list_entities` MCP tool to see all entities in the model.

**Step 2: Explore entity details**
Use the `get_entity` MCP tool with the relevant entity name to list its attributes, metrics, datasets, and relations.

**Step 3: Search the model**
Use the `search_model` MCP tool to find specific fields, entities, or other objects by name.

---

## Overview

Honeydew is the Semantic Layer for AI and BI. Honeydew enables a shared source of truth for data teams, providing consistency, flexibility, governance and performance.
It provides metrics and attributes over data warehouse tables and views (Snowflake, Databricks, BigQuery) that have relationships defined between them.
Use the Honeydew MCP tools to interact with the model.

## MCP Tools

### Session & Workspace

- `list_workspaces` - List all available workspaces. Returns the workspace name and the data warehouse type (`snowflake`, `databricks`, or `bigquery`). Use the warehouse type to inform SQL dialect choices in semantic model implementation.
- `list_workspace_branches` - List all branches available for a workspace. Requires `workspace_id` (the workspace name).
- `get_session_workspace_and_branch` - Get the workspace and branch set for the current session.
- `set_session_workspace_and_branch` - Set the workspace and branch to use for the current session. All subsequent tool calls use this workspace and branch. Requires `workspace_id`; optional `branch_id` (omit to use the production branch, which is the default).
- `create_workspace_branch` - Create a new branch for an existing workspace. The branch is created from the current state of the workspace's `prod` branch. The session automatically switches to the new branch. Requires `workspace_id` and `branch_name`.

**Typical flow:**

1. `get_session_workspace_and_branch` — check if a workspace/branch is already set
2. If not set: `list_workspaces` → pick a workspace → `set_session_workspace_and_branch`
3. For development work: `create_workspace_branch` (session switches to the new branch automatically)

### Discovery

- `list_entities` - List all entities in the model (names, keys, descriptions)
- `get_entity` - Get detailed info for a specific entity (attributes, metrics, datasets, relations, YAML)
- `get_field` - Get detailed info for a specific field (attribute or metric) within an entity
- `list_domains` - List all domains with their names, descriptions, and entities
- `get_domain` - Get detailed info for a specific domain (entities, filters, parameters, YAML)
- `search_model` - Search across all model objects (entities, attributes, metrics, datasets, dynamic datasets, domains, parameters). Requires `query` and `search_mode`:
  - `OR` — splits by whitespace, returns objects matching any word
  - `AND` — splits by whitespace, returns only objects matching all words
  - `EXACT` — uses the full string as-is, matches name or display name exactly
  - Use `entity.field` syntax to scope to fields within an entity (e.g. `customers.balance` finds `balance` on entities matching `customers`; `customers.` returns all fields of matching entities)

### Agents & Context

Honeydew has two layers: the **semantic layer** (entities, metrics, attributes, relations, domains — the data model and business logic such as metric calculations) and the **context layer** (agents and their associated context items — instructions, skills, knowledge, and memory — that shape how the AI analyst behaves).

- `list_agents` — List all agents with their names, descriptions, domains, and context references
- `get_agent` — Get detailed info for a specific agent (domain, context items, welcome message, sample questions)
- `list_context_items` — List all context items with their types, names, titles, and subtypes
- `get_context_item` — Get detailed info for a specific context item

### Warehouse Discovery

- `list_databases` - List all databases in the connected data warehouse
- `list_schemas` - List schemas in a specific database
- `list_tables` - List tables in the connected data warehouse (requires `database` and `schema` parameters)
- `get_table_info` - Get column-level details for a specific warehouse table

### Query Execution

- `get_data_from_fields` - Execute a query from field parameters and return data (supports `limit` and `offset` for pagination)
- `get_sql_from_fields` - Generate SQL from field parameters without executing

### AI-Powered Queries

- `ask_deep_analysis_question` - Natural language question (simple or complex) → agentic analysis and results

## Example Usage

### Query API Decision Flow

```
User Request
    │
    ├─► Exact field names known? Want structured query?
    │       └─► YES → get_data_from_fields (deterministic, structured)
    │
    └─► Plain English / natural language / "why" / investigation?
            └─► ask_deep_analysis_question (any complexity)
```

| Tool                         | Use When                                    | Example Request                                       |
| ---------------------------- | ------------------------------------------- | ----------------------------------------------------- |
| `get_data_from_fields`       | Known fields, programmatic                  | "Get total_revenue by month for 2021"                 |
| `ask_deep_analysis_question` | Plain English questions, trends, root cause | "Show me revenue by city last 2 years"                |
| `ask_deep_analysis_question` | Complex analysis, "why", multi-step         | "Find revenue drops and find contributing factors"    |

---

### get_data_from_fields (Primary - Known Fields)

Call `get_data_from_fields` with field parameters:

- `attributes`: `["order_header.order_year_month"]`
- `metrics`: `["order_header.total_revenue"]`
- `filters`: `["order_header.order_year_month LIKE '2021%'"]`
- `order_by`: `["\"order_header.order_year_month\" ASC"]` — field references must be wrapped in double quotes, like SQL identifiers
- `domain`: `"my_domain"` (optional)
- `limit`: max rows to return (default: 100)
- `offset`: rows to skip (for pagination)

---

### get_sql_from_fields (SQL Preview)

Same field parameters as `get_data_from_fields`, but returns the generated SQL without executing it.

---

### ask_deep_analysis_question (Natural Language Queries)

Call with:

- `question`: `"Show me revenue by city for the last 2 years"` (simple) or `"Look at last 5 years, identify revenue drops and find contributing factors"` (complex)
- `conversation_id`: `"conv_123"` (optional, for follow-up questions)

**Returns:** markdown analysis report, data, suggested follow-up questions, conversation_id

---

### Discovery Examples

- Use `list_entities` to list all entities
- Use `get_entity` with an entity name to see its attributes, metrics, datasets, and relations
- Use `get_field` with entity name and field name to get detailed info about a specific field
- Use `list_domains` to list all domains
- Use `get_domain` with a domain name to see its entities, filters, parameters, and YAML definition
- Use `search_model` with a query string and `search_mode` (`OR`, `AND`, or `EXACT`) to find any model object by name. Use `EXACT` when you know the precise name; use `OR` or `AND` for broad discovery

## Documentation Lookup

Use the `honeydew-docs` MCP tools to search the Honeydew documentation when:

- The user asks conceptual questions ("what is an entity?", "how do metrics work?", "what is a semantic layer?")
- You need to explain Honeydew concepts, architecture, or terminology
- The user is new to Honeydew and needs orientation on capabilities
- You need to understand how a feature works beyond what the MCP tool descriptions provide
- The user asks about advanced modeling concepts or patterns
- The user asks about integrations, setup, or configuration

Search for topics like: "entities", "metrics", "attributes", "domains", "relations", "semantic layer", "governance", or any Honeydew-specific concept.

---

## Best Practices

1. Use `get_entity` to explore fields on a specific entity
2. Reference fields using `entity.field_name` syntax
3. Use discovery tools before any creation tasks
4. For creating entities, metrics, attributes, or relations - use the specialized skills listed above
