---
name: tool-design
description: 'Design or audit the tools an AI agent calls (MCP server tools, function calling, Runtype runtime and saved tools), or find out why an agent picks the wrong tool or misuses one. Routes naming, schema, output, error, execution, and security work to focused guides.'
user-invocable: true
argument-hint: '[tool or tool set to design or review]'
---

# Tool Design

A tool that returns correct data can still fail in production because the agent could
not tell when to call it, what to pass, or what to do with the result. "Working" is not
the same as "agent-usable". This skill family treats the agent as the consumer and
designs for it.

The guidance is framework-neutral: it applies to MCP servers, native function calling,
Runtype runtime tools, and any custom loop. It is organized as 54 named patterns across
ten questions; `references/pattern-index.md` maps every pattern to the skill that owns
it.

## The consumer changed, so the design rules changed

| Aspect        | Integration middleware | Agent tools                             |
| ------------- | ---------------------- | --------------------------------------- |
| Consumer      | Applications           | An LLM                                  |
| Routing       | Predetermined flows    | Chosen by the agent at runtime          |
| Errors        | Dead-letter queue      | Recovery guidance the agent can act on  |
| Documentation | Written for humans     | Written for machine comprehension       |
| Composition   | Orchestrated by a bus  | Chained by the agent, non-deterministic |

Nothing enforces sequence for the agent. The tool descriptions, parameter shapes, result
shapes, and error messages are the only orchestration layer there is.

## Four rules that apply to every tool

1. **Design for the model, not the human.** Names, descriptions, parameter names, and
   error text are read by an LLM. Be literal, structured, and complete.
2. **Prompts express intent; code enforces rules.** Authorization, secrets, boundaries,
   and audit live in the tool layer. Never rely on the agent to police itself.
3. **Errors teach, not just fail.** Every failure says what went wrong, why, and the
   exact next call to make.
4. **Hint at what comes next.** Descriptions and results name prerequisites and
   follow-ups so the agent builds the workflow without trial and error.

## Procedure: design a new tool

1. **Classify it** on the three axes and write the answers down before writing a schema:
   - Type: `query` (read-only, retryable, cacheable), `command` (side effects, document
     irreversibility), or `discovery` (reveals what exists, schema, capabilities).
   - Integration: API, database, file system, or system operation. Databases and
     command tools need idempotency because agents retry on timeout.
   - Access pattern: synchronous (most tools; bounded seconds), async job (minutes;
     return a job id), streaming, or event-driven.
   - Maturity: start **atomic**. Move to enhanced, composite, or orchestrated only
     when traces show the signal (see "Level up on evidence").
2. **Write the interface** with `tool-design-interface`: a verb-object name, a description
   that says when to use it and when not to, constrained parameters, smart defaults,
   natural identifiers, and dependency hints.
3. **Shape the result** with `tool-design-output`: flat, token-efficient, paginated by
   cursor, summary by default, with GUI links and a next-action hint.
4. **Design the failure paths** with `tool-design-errors`: classify every error as
   retryable, permanent, needs-user-input, or needs-auth, and attach recovery steps.
5. **Decide execution semantics** with `tool-design-execution`: timeout, idempotency
   key, transaction or compensation, async job when work exceeds the sync budget.
6. **Lock the boundary** with `tool-design-security`: secrets injected server-side,
   permission checks in code, declared scopes, audit log, identity anchor.
7. **Place it in the set** with `tool-design-composition`: does it bundle a common
   sequence, accept a batch, offer preview mode, sit on an abstraction ladder?
8. **Test it as the agent would.** Call it with the inputs an LLM will plausibly send
   (natural-language dates, display names instead of ids, a single item where an array
   is expected) and read the errors back as if you knew nothing but the description.

## Procedure: review an existing tool set

Run this when asked to audit, review, or "figure out why the agent misuses" a toolkit.

1. **Inventory.** List every tool with type (query/command/discovery), parameter count,
   required-parameter count, and whether it has side effects. Flag any tool whose type
   is not obvious from its name.
2. **Read every description as the model.** For each tool, answer only from the
   description: when do I call this? what do I need first? what do I get back? If any
   answer is unclear, that is a finding.
3. **Check the parameters** against `tool-design-interface`: free-form strings that
   should be enums, required parameters that could default, ids where a natural
   identifier would do, secrets accepted as parameters (a security finding, not a
   style one), ambiguous "one of X or Y" pairs without enforcement.
4. **Check the results** against `tool-design-output`: raw upstream payloads, nested
   blobs, unbounded lists, missing `hasMore` and cursor, no GUI link, batch results
   that collapse to all-or-nothing.
5. **Check the errors** against `tool-design-errors`: raw status codes, messages with
   no next step, no retryable/permanent distinction, ambiguity resolved by guessing.
6. **Check execution and security** against `tool-design-execution` and
   `tool-design-security`: command tools with no idempotency story, work that cannot
   finish inside the timeout, permission logic in the system prompt, no audit trail.
7. **Check the set as a whole** against `tool-design-composition`: near-duplicate tools,
   sequences the agent always performs together (bundle candidates), N-item loops
   (batch candidates), destructive tools without a preview mode, more tools than the
   model can hold in context at once.
8. **Report** findings as a table: tool, pattern violated, severity (blocks the agent /
   degrades reliability / polish), concrete fix. Lead with the findings that make the
   agent choose the wrong tool or fail to recover; those dominate observed failures.

## Level up on evidence, not ambition

Start atomic and watch traces. Each signal maps to a specific move:

| Signal in traces                               | Move                                            |
| ---------------------------------------------- | ----------------------------------------------- |
| High retry rate on one tool                    | Fix description and error guidance first        |
| The same tool sequence repeated across runs    | Bundle it into a task tool                      |
| Per-item loops over the same tool              | Add a batch variant                             |
| Partial completion of multi-step operations    | Add a transaction boundary or compensation      |
| Agent calls a tool it lacks prerequisites for  | Add dependency hints and a discovery tool       |
| Agent picks the wrong one of two similar tools | Merge them or sharpen the "use when / not when" |
| Long-running calls time out                    | Convert to an async job                         |

Do not build the orchestrated version first. Composite tools built before atomic usage
is understood encode guesses about workflows the agent never runs.

## Pre-ship checklist

Every tool must pass all of these before it reaches an agent:

- Name is verb-object and unambiguous next to every sibling tool.
- Description says what it does, when to use it, when not to, and what to call first.
- Every string input that has a finite set of valid values is an enum.
- Every optional parameter has a documented default; required parameters are minimal.
- Human-friendly identifiers are accepted and resolved internally.
- Result is flat, token-efficient, and consistent in shape across calls.
- Large results are cursor-paginated with an explicit `hasMore`.
- Errors carry a class (retryable / permanent / user input / auth) and a next step.
- Command tools state whether they are idempotent and how.
- Secrets are injected from context, never accepted as parameters.
- Permission checks run in code before the operation.
- Invocations are logged with redacted parameters.
- Destructive or costly commands are gated (approval, preview mode, or both).

`references/checklist.md` carries the same list with the pattern each row comes from.

## On Runtype

The preceding sections are framework-neutral. When you build natively on Runtype, the
platform enforces most of these patterns, so your job is to know which mechanism
carries each one.

### Which tool kind carries which pattern

| Tool kind (`toolType`) | What it is                                                                            | Patterns it carries                                                                                                                      |
| ---------------------- | ------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `external`             | HTTP call defined by `url`, `method`, `headers`, `body` template                      | Tool Adapter, Secret Injection (`{{secret:KEY}}`), request mapping (the `body` template)                                                 |
| `custom`               | Sandboxed code (JavaScript by default; TypeScript or Python in a sandbox environment) | Parameter Coercion, Response Shaper, Error Classification, Natural Identifier resolution; Tool Adapter when it opts into `networkAccess` |
| `flow`                 | A saved flow exposed as one tool, run synchronously                                   | Task Bundle, Tool Chain, Compensation (per-step `errorHandling`), Response Shaper (`outputVariable`)                                     |
| `subagent`             | Delegation to a saved or inline agent (`agentId` or `agent`)                          | Abstraction Ladder (the orchestrated rung), Scatter-Gather, Async Job (detached mode)                                                    |
| `local`                | Executed by the client (browser widget or SDK caller)                                 | Confirmation Request, anything needing the user's environment                                                                            |
| `mcp`                  | A tool discovered from an MCP server                                                  | Tool Gateway, Tool Registry (`discover_mcp_server_tools`)                                                                                |
| `builtin` / Orthogonal | Platform catalog tools (attached by id, not created)                                  | Canonical Tool Model, house style for descriptions                                                                                       |

An `external` tool returns the upstream response as-is; shape it in a `flow` tool
(`api-call` step into `transform-data`) or in a downstream `transform-data` step. A
`custom` tool can make the call itself only when it opts in: set `networkAccess` to an
`allowedHostnames` list, and declare any managed secret in `secrets` so the code sends a
phantom token that the egress proxy swaps for the real credential. Without
`networkAccess`, a `custom` tool has no network egress. A `flow` tool returns the flow's terminal step output; set
`config.outputVariable` to return one shaped variable instead. Long-running work is not
a `flow` tool either: a `subagent` tool with `config.execution.mode: "detached"` returns
a run handle, and `run_flow` with `async: true` returns an execution id (see
`tool-design-execution`).

`create_tool` also accepts `graphql`, but no executor runs that type: a call to a
`graphql` tool fails with an unsupported-type error. Send a GraphQL query from an
`external` tool with `method: "POST"` and the query in the `body` template.

The MCP `create_tool` accepts `tool_type` in `flow`, `custom`, `external`, `graphql`,
`mcp`, `local`, with `name`, `description`, `parameters_schema` (JSON Schema), and
`config`. `name` is at most 100 characters and `description` at most 500 on create, so
keep the description tight and put detail in parameter descriptions and error text. The
REST API and SDKs (`POST /v1/tools`, spelled `toolType` and `parametersSchema`) accept
the same set plus `subagent`. To delegate to agents over MCP, pick the route by need:

- A fixed saved agent as a tool: wrap it in a flow with an `execute-agent` step and
  register that flow with `tool_type: "flow"`. Agent ids are not valid tool ids.
- Delegation the agent decides at run time: set the agent's
  `config.tools.subagentConfig`, which gives it a `spawn_subagent` tool.

`builtin` tools are never created; attach them by id through `config.tools.toolIds`.
Iterate with `update_tool` and `get_tool`; read
`get_platform_documentation(topic="external-tools")` and
`get_platform_documentation(topic="limits")` before designing.

### What the platform enforces for you

- Credentials: `{{secret:KEY}}` references resolve server-side and are the only
  credential contract. Never collect secret values in chat; hand the user the intake
  URL from `get_secret_intake_manifest`.
- Context injection: on runtime tools (an agent's `tools.runtimeTools` or
  `/v1/dispatch`), `hiddenParameterNames` strips parameters from the model-facing schema
  and fills them from execution variables. List `_endUser` or `_tenant` there to anchor
  the verified caller identity so the model never supplies it. Saved tools created with
  `create_tool` do not take this field. Names under `_internal` are rejected; use
  `{{secret:KEY}}` for credentials.
- Human-owned inputs: `config.elicit` on an `external` or `custom` tool pauses the run
  for a form before approval and dispatch. Use it instead of letting the model invent
  an argument that belongs to the person.
- Permission gate: `config.tools.approval.require` pauses the run for a human on the
  listed tools; the agent's `_approvalReason` is display-only, never a control signal.
  `approval.timeout` (default 5 min), `approval.requestReason`, and `approval.choices`
  (`alwaysAllow`, `alwaysDeny`) shape the prompt. Approval covers only calls a model
  chooses in an agent or prompt step. A flow `tool-call` step always runs, unattended.
- Idempotency: set `idempotent: true` only on runtime tools that are safe to run twice,
  such as reads or writes keyed by an idempotency key. When a turn is interrupted
  mid-call, Runtype re-runs only those; any other call returns an "effects unknown,
  verify before retrying" error instead of running twice. For MCP tools, declare
  `readOnlyHint` or `idempotentHint` on the server; with neither, the tool is treated
  as unsafe to re-run.
- Files and media: a binary media part of 4 KB or more in a tool result is stored and
  handed to the model as a `runtype-asset://` handle. Declare a parameter as
  `{ "type": "string", "contentEncoding": "base64" }` to receive those bytes; Runtype
  substitutes them before dispatch, so the model never re-emits the payload. This is
  the Resource Reference pattern on Runtype.
- Audit: every tool call is traced on the run and visible in Runs, Logs, and
  `trace_execution`.
- Timeouts: a runtime custom tool is limited to 30 s. A saved custom tool takes its own
  `timeout` in milliseconds, up to 300 s in the tool editor. MCP tools default to 30 s
  and can run up to 300 s only in background runs. A subagent tool defaults to 5 min.
  Longer work belongs in an async flow run or a detached subagent.
- Tool set controls: `maxToolCalls` bounds tool-call loops, and `toolCallStrategy` is
  `auto`, `required`, or `none`. Do not set `perToolLimits`: it is retired, and an agent
  that carries it is rejected. Bound the loop with `loopConfig.maxTurns` or
  `loopConfig.maxCost`, or enforce a per-tool budget inside the tool. `codeModeConfig`
  gives the agent a `code_mode` tool that chains a subset of its tools in sandboxed
  code, an alternative to hand-built bundle and batch tools.
- Tool count: 50 runtime tools per request. Tool search is on by default for multi-turn
  agents at 20+ tools (inline tools defer behind `tool_search`, and
  `tools.toolSearch.enabled: false` opts out). Single-turn agents send every tool on every
  request, so keep sets small or split them across agents.
- Save-time checks: `validate_flow` reports several checklist rows as stable codes
  (see `references/checklist.md`, "Checked for you on Runtype").

### The test loop

1. Read `validation.warnings` and `validation.recommendations` in the `create_tool` or
   `update_tool` response. The save succeeds even when they are present, so no error
   tells you to look.
2. `execute_tool` with the inputs an agent will plausibly send, including wrong ones,
   and read the result and error as the model would.
3. Wire it into an agent and run a realistic prompt with `execute_agent` or `dispatch`.
4. When a real run misuses the tool, pin it: `add_eval_case_from_execution`, then
   `run_eval_suite` after every description or schema change. Read
   `get_platform_documentation(topic="evals")` for tool-use eval layers.
