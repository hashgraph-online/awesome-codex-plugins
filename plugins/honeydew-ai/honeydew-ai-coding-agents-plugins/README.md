# Honeydew AI Plugins for Coding Agents

Skills and tools powered by the [Honeydew MCP](https://honeydew.ai/docs/integration/mcp) that help coding agents build semantic models and analyze data through natural conversation.

## Example Use Cases

**Query your data** — Ask "Show me revenue by region for last quarter." Your coding agent discovers the right entities and metrics, runs the query through the semantic layer, and returns the results.

**Build a semantic model** — Ask "I added a new orders table — create an entity with revenue and order count metrics." Your coding agent imports the table, defines attributes and metrics following your naming conventions, and validates the result.

**Investigate anomalies** — Ask "Why did churn spike last month?" Your coding agent runs a multi-step deep analysis, explores correlations across your model, and surfaces the key drivers with supporting data.

## Prerequisites

- A coding agent that supports plugins/skills (e.g., [Claude Code](https://docs.anthropic.com/en/docs/claude-code), [Codex](https://developers.openai.com/codex/cli), [Cursor](https://cursor.com), or any agent with MCP support)
- A Honeydew AI workspace with the [Honeydew MCP server](https://honeydew.ai/docs/integration/mcp) configured

## Installation

### Claude Code

Add this marketplace to Claude Code:

```
/plugin marketplace add honeydew-ai/honeydew-ai-coding-agents-plugins
```

Then install the plugin:

```
/plugin install honeydew-ai@honeydew-ai-coding-agents-plugins
```

### Codex

Add this marketplace to Codex:

```
codex plugin marketplace add honeydew-ai/honeydew-ai-coding-agents-plugins
```

Then open the plugin directory and install the plugin:

```
codex
/plugins
```

If the marketplace was already added before this repo exposed the Codex wrapper path, refresh it first:

```
codex plugin marketplace upgrade honeydew-ai-coding-agents-plugins
```

### Cursor

1. Go to Cursor Settings -> Rules, Skills, Subagents and click on **+New** next to Rules.
2. Select **Add from GitHub** and enter the URL of this repository.

### Other Coding Agents

For coding agents that support MCP, configure the [Honeydew MCP server](https://honeydew.ai/docs/integration/mcp) and use the skill files in this repository as prompts or instructions. The skills are written as agent-agnostic markdown documentation that any coding agent can consume.

## Available Skills

The `honeydew-ai` plugin includes 10 skills:

| Skill | Description |
|-------|-------------|
| **model-exploration** | Explore the semantic model — list entities, search fields, inspect relationships, and discover warehouse tables |
| **entity-creation** | Create entities — the foundational business concepts built from data warehouse tables |
| **relation-creation** | Define relationships between entities with join types, cardinality, and complex join conditions |
| **attribute-creation** | Create calculated attributes (dimensions) — per-row virtual columns defined with SQL expressions |
| **metric-creation** | Create metrics (KPIs) — reusable aggregations like totals, averages, ratios, and growth rates |
| **context-item-creation** | Create context items — instructions, skills, knowledge pointers, and memory events that give the AI analyst persistent knowledge about your organization |
| **domain-creation** | Create domains — curated subsets of the semantic model exposed to specific teams or use cases |
| **validation** | Mandatory post-creation validation — type-specific sanity checks, cross-validation, and error handling |
| **query** | Query data using structured YAML perspectives, natural language questions, or multi-step deep analysis |
| **filtering** | Advanced filtering syntax — comparisons, string matching, date handling, nulls, and full-text search |

## Supported Data Warehouses

- Snowflake
- Databricks
- BigQuery

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.
