---
name: tool-design-composition
description: 'Compose and expose agent toolsets: task-level operations, batching, discovery, dry runs, and versioning.'
user-invocable: true
argument-hint: '[tool set to organize or extend]'
---

# Tool Composition and Discovery Design

A composable tool set has four properties: consistent input and output shapes, so one
tool's output feeds the next tool's input; batch support, so the agent does not loop one
item at a time; more than one abstraction level, so the agent picks the granularity the
task needs; and discoverability, so the agent finds the right tool without trial and
error.

## Procedure

1. **Map the current set**: every tool, its type, and the sequences agents actually run
   (from traces, not from intent).
2. **Find bundle candidates** (Task Bundle): sequences repeated across runs with no
   branching between steps.
3. **Find batch candidates** (Batch Operation): the same tool called in a loop over a
   list.
4. **Find ladder gaps** (Abstraction Ladder): capabilities with only a raw low-level tool
   and no intent-level tool, or the reverse.
5. **Add a `mode` parameter** (Operation Mode) that defaults to `preview` on every
   destructive or costly command.
6. **Design discovery** (Dependency Hint, Tool Registry, Schema Explorer): hints in
   descriptions, a registry or search tool once the set is large, and layered schema
   exploration for data sources.
7. **Prune**: merge near-duplicates and retire tools with no traffic. Fewer,
   better-described tools beat many similar ones.
8. **Verify**: run each new tool on its own, then run the agent and read its trace to
   confirm it picks the new bundle, batch form, or preview mode instead of the old
   sequence.

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

Past roughly twenty tools, tool-selection accuracy drops and every definition costs
context tokens.
Provide a `list_available_tools(category)` registry with name, description, category,
and auth requirements, and a `find_tool_by_intent(intent)` search that ranks tools by
semantic match with confidence and usage examples. Where your runtime can defer tools,
keep the must-use tools always loaded and let the long tail be discovered.

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

- **Tool count and residency.** A dispatch carries at most 50 runtime tools. Tool search
  is on by default for multi-turn agents: at 20 or more tools, Runtype keeps a hot set
  loaded and defers the inline runtime tools behind a `tool_search` tool that the model
  calls to load more. Saved, built-in, and MCP tools stay loaded. Set
  `tools.toolSearch.enabled: false` to send every tool on every request. Single-turn
  agents and flow prompt steps always send every tool, so keep those sets small or split
  them across subagents. Either way, make descriptions distinct, because they are what
  the model chooses by and what `tool_search` matches against.
- **Tool-call budget.** An agent makes at most 10 tool calls per execution unless you
  set `config.tools.maxToolCalls`. A per-item loop over a list uses up that budget
  quickly, so ship a batch form, or raise the cap on purpose.
- **Task bundle and tool chain.** A flow is the platform's explicit chain: fixed step
  order, data passing, per-step error handling. Expose it as one tool
  (`toolType: "flow"`) when the agent should run the whole sequence as a single call.
  Map tool parameters to flow inputs with `parameterMapping`. The model receives the
  flow's terminal step output; to return a composite status object instead, assign it
  to a flow variable and name that variable in `outputVariable`. A variable name that
  starts with `_` is rejected, and a variable the flow never assigns fails the call.
- **Code Mode for batch, chain, and fan-out.** When the logic between calls varies by
  input (loops over a list, conditional chains, several sources merged), set
  `config.tools.codeModeConfig` on the agent or prompt step. `toolPool` lists the tool
  ids the model can call (wildcards such as `mcp:*` work), and `timeoutMs` defaults to 60000. The model writes JavaScript that calls those tools in a sandbox, and
  intermediate values never enter model context. Choose a `flow` tool when the order
  is fixed; choose Code Mode when the model must write the logic.
- **Binary results.** A binary tool result, such as a screenshot or a generated image,
  carries a `runtype-asset://` handle. To accept it in your own tool, declare the input
  as a string with `"contentEncoding": "base64"`; a handle passed there is replaced with
  the stored bytes before your tool runs, so the model never copies base64. A parameter
  without that declaration receives the handle string unchanged.
- **Abstraction ladder.** Built-in and Orthogonal catalog tools are the low rung;
  `custom`, `external`, and `mcp` tools the middle; flows and subagents the
  top. Compose subagents as saved subagent tools, inline subagent tools, or dynamic
  spawning through `config.tools.subagentConfig`, which gives the agent a
  `spawn_subagent` tool. Subagents have their own caps; read
  `get_platform_documentation(topic="subagent-delegation")`.
- **Gateway and adapter.** An MCP server attached through `config.tools.mcpServers` is
  a Tool Gateway: one connection, many tools. An `external` tool is a Tool Adapter: it
  wraps an upstream API behind a clean interface. For a GraphQL API, use an `external`
  tool that POSTs the query; the `graphql` tool type is not executable.
- **Operation mode.** On an agent, gate destructive tools with
  `config.tools.approval.require` (for example, `["delete_files"]`; patterns such as
  `mcp:*` work). Approval asks a person before the call runs; it complements a
  `preview` mode but does not replace it. A `tool-call` flow step runs a catalog tool
  deterministically with no approval gate, so there a preview must be a distinct tool
  or a `mode` parameter. Approval details:
  `get_platform_documentation(topic="agent-design")`.
- **Description length.** A new saved tool's description is capped at 500 characters. When
  dependency hints, replacement notes, and deprecation notes do not fit, move them into
  parameter descriptions or the error text.
- **Registry and discovery.** `list_tools` covers saved tools,
  `discover_mcp_server_tools` an MCP server, and
  `get_platform_documentation(topic="builtin-tools")` the catalog. A `tool-call` step
  that names a catalog id nobody answers to is rejected as
  `TOOL_CALL_STEP_UNKNOWN_CATALOG_TOOL`.
- **Traces and verification.** Find real sequences with `list_runs` (filtered by `agentId`) and
  `trace_execution`. Test one tool with `execute_tool`, then run the agent with
  `execute_agent` and read the trace to confirm the tool choice.
- **Versioning.** Agents and flows are versioned (`publish_agent_version`,
  `publish_flow_version`); a tool behavior change ships behind a new published version
  rather than in place.
