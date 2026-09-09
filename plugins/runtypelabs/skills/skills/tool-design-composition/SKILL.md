---
name: tool-design-composition
description: 'Compose and expose agent toolsets: task-level operations, batching, discovery, dry runs, and versioning.'
user-invocable: true
argument-hint: '[tool set to organize or extend]'
---

# Tool Composition and Discovery Design

Tools should compose like Unix pipes, not like a chain of command. That needs three
properties across the set: consistent shapes so one output feeds the next input, batch
support so the agent does not loop one item at a time, and multiple abstraction levels
so the agent can pick the granularity the task needs. It also needs the agent to be
able to find the right tool without trial and error.

## Procedure

1. **Map the current set**: every tool, its type, and the sequences agents actually run
   (from traces, not from intent).
2. **Find bundle candidates**: sequences repeated across runs with no branching between
   steps.
3. **Find batch candidates**: the same tool called in a loop over a list.
4. **Find ladder gaps**: capabilities with only a raw low-level tool and no intent-level
   tool, or the reverse.
5. **Add preview modes** to every destructive or costly command.
6. **Design discovery**: dependency hints in descriptions, a registry or search tool
   once the set is large, layered schema exploration for data sources.
7. **Prune**: merge near-duplicates and retire tools with no traffic. Fewer,
   better-described tools beat many similar ones.

## Rules with examples

### Offer the capability at more than one altitude (Abstraction Ladder)

```text
low   execute_query(sql)                       full control, expert use
mid   search_records(table, filters)           structured, safe
high  find_customers_like(description)         intent-level, does the work
```

Each rung has a stated use case; higher rungs call lower ones internally; descriptions
say when to use which. Do not ship only the low rung and expect the agent to compose
it correctly every time.

### Bundle the sequence the agent always runs (Task Bundle)

`search_users` then `open_dm` then `send_message` becomes `dm_user(name, message)`.
Name the bundle after the task, not the steps. Handle intermediate failures inside the
bundle and return a composite result that reports each step. Keep the atomic tools
available for edge cases, and say in the bundle's description that it replaces the
sequence.

### Accept lists (Batch Operation)

Any tool the agent calls per item over a list gets a batch form: an array input, a
documented maximum batch size, per-item results with status, and a partial-success
report (see `tool-design-output`). Batch the upstream calls internally where the API
allows. Decide up front whether a batch is all-or-nothing or partial, and say which.

### Explore before executing (Operation Mode)

Give commands a `mode` parameter that defaults to the safest option:

```text
explore   list what the tool could do here, read-only
preview   show exactly what would change, no side effects
dry_run   validate inputs without executing
execute   perform the action
```

Return the same result structure in every mode so the agent can compare a preview to
the real run. A `schema` mode that returns the upstream's complex input shape is useful
when the shape cannot be expressed in the tool interface.

### Make the sequence explicit when it matters (Tool Chain)

For multi-step processes with a fixed order, define the chain as ordered steps with
data passing between them and checkpoints for resume. A chain is a specification the
agent follows, or a single orchestrated tool that runs it; either way the order is not
left to inference.

### Fan out, then merge (Scatter-Gather Tool)

A tool that consults several sources queries them in parallel, merges the results into
one canonical shape, and reports per-source status so a failed source degrades the
result rather than failing it.

## Discovery: how the agent finds the right tool

### Say what to call first (Dependency Hint)

Descriptions and parameter docs name prerequisites ("`userId`: if you only have an
email, call `search_users` first"), follow-ups ("after this, `get_user` verifies the
change"), and alternatives ("if this fails, try `send_email`"). Repeat the hint in the
error the tool returns when the prerequisite is missing.

### Catalog the set when it is large (Tool Registry, Capability Matching)

Past roughly twenty tools, the model can no longer hold every definition in context.
Provide a `list_available_tools(category)` registry with name, description, category,
and auth requirements, and a `find_tool_by_intent(intent)` search that ranks tools by
semantic match with confidence and usage examples. Keep the must-use tools always
loaded and let the long tail be discovered.

### Reveal structure in layers (Schema Explorer)

For data sources, do not dump the full schema. Layer it: `list_tables()`, then
`describe_table(name)`, then `sample_rows(table, limit)`, then `get_query_hints(table)`.
Each layer's description names the next.

### Check before relying (Health Check)

A fast (sub-second) `check_service_health(service)` returns healthy, degraded, or
unavailable with specific reasons, so the agent does not spend turns on a dead backend.
Cache the status briefly.

## Across the system

- **Tool Gateway**: one entry point routes to many backends and aggregates discovery,
  so the agent sees one consistent set.
- **Tool Adapter**: wrap a legacy or awkward API in a clean tool: LLM-friendly
  description, constrained inputs, shaped output. The adapter hides the legacy shape
  entirely.
- **Canonical Tool Model**: shared `User`, `Task`, `Event` shapes and field names across
  every tool, mapped to and from each backend.
- **Tool Versioning**: version in the name (`send_email_v2`) or metadata, run versions in
  parallel during migration, and deprecate with a migration note in the old tool's
  description.

## Anti-patterns

- Thirty atomic tools and no bundle for the sequence 80% of runs perform.
- `delete_files` with no preview mode.
- Two tools that differ only in one optional parameter.
- A registry that lists tools without their auth requirements or categories.
- A composite tool built before any trace showed the sequence being used.
- A migration that changes a tool's behavior in place instead of versioning it.

## On Runtype

- **Tool count and residency.** A dispatch carries at most 50 runtime tools. At 20
  the platform partitions them into a hot set plus a `tool_search` meta-tool. Pin the
  must-use tools with `config.tools.toolSearch.alwaysLoaded` (or `alwaysLoaded: true`
  on the tool), raise or lower the cut with `toolSearch.threshold`, or set
  `toolSearch.enabled: false` to force every tool into context. Descriptions drive
  both model choice and search ranking.
- **Task bundle and tool chain.** A flow is the platform's explicit chain: fixed step
  order, data passing, per-step error handling. Expose it as one tool
  (`toolType: "flow"`) when the agent should run the whole sequence as a single call.
- **Abstraction ladder.** Built-in and Orthogonal catalog tools are the low rung,
  `custom` and `external` tools the middle, flows and subagents the top. Subagents
  have their own caps; read `get_platform_documentation(topic="subagent-delegation")`.
- **Operation mode.** A `tool-call` flow step runs a catalog tool deterministically
  with no approval gate, so a preview mode must be a distinct tool or a `mode`
  parameter; do not rely on the gate to make a step safe.
- **Registry and discovery.** `list_tools` covers saved tools,
  `discover_mcp_server_tools` an MCP server, and
  `get_platform_documentation(topic="builtin-tools")` the catalog. A `tool-call` step
  that names a catalog id nobody answers to is rejected as
  `TOOL_CALL_STEP_UNKNOWN_CATALOG_TOOL`.
- **Versioning.** Agents and flows are versioned (`publish_agent_version`,
  `publish_flow_version`); a tool behavior change ships behind a new published version
  rather than in place.
