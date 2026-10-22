---
name: tool-design-interface
description: 'Design agent-facing tool names, descriptions, and parameter schemas; diagnose incorrect tool selection or inputs.'
user-invocable: true
argument-hint: '[tool whose name, description, or parameters to design]'
---

# Tool Interface Design

The interface is everything the model knows about a tool: a name, a description, and a
parameter schema. Humans infer; models do not. Anything not stated explicitly is
unknown to the agent, and the tool will be presented next to many others that can
confuse it. Write the interface as a prompt, because it is one.

## Procedure

1. **Name it verb-object** (`send_email`, `list_open_invoices`), one responsibility per
   tool, unambiguous next to every sibling.
2. **Write the description in four parts**: what it does, when to use it (and when
   not to, naming the alternative), what to call first if a prerequisite is missing,
   and what it returns.
3. **Constrain every parameter**: enums for finite sets, min/max for numbers, patterns
   for formats, explicit required-versus-optional.
4. **Minimize required parameters** with context-aware defaults, and document each
   default in the parameter description.
5. **Accept the identifiers a person would use** and resolve them internally.
6. **Coerce common variations** (dates, numbers as strings, single item versus array)
   to a canonical form inside the tool.
7. **State exclusivity rules and performance preferences** in the description and
   enforce them at the top of execution.
8. **Evaluate with realistic prompts.** A description is only known to be good when
   the agent selects and calls the tool correctly on inputs that resemble real usage.

## Rules with examples

### Mark the type

Signal side effects in both metadata and text. Query tools are read-only, retryable,
cacheable, and parallelizable; say so (the MCP annotation `readOnlyHint: true`, and
"Safe to retry" in the description). Command tools modify state; document
irreversibility in the first sentence ("Permanently deletes the user. Irreversible.")
and flag them destructive where the runtime supports it (`destructiveHint: true`).
Discovery tools (`list_tables`, `get_capabilities`, `who_am_i`) exist so the agent can
find out what is possible before acting; their descriptions say "call this first".

### Describe for the model

Pattern: Tool Description.

Before:

```text
Gets a user.
```

After:

```text
Retrieve one user by email (ada@example.com) or id (usr_abc123). Use this when you
already have an identifier; if you only have a name, call search_users first. Read-only,
safe to retry. Returns id, name, email, role, and active. To change fields, use
update_user.
```

Include examples of valid inputs, prerequisites, follow-ups, and alternatives. Do not
assume the model will infer anything a developer would find obvious. All prompt
engineering practice applies: explicit criteria, no ambiguity, one meaning per term.

### Constrain inputs

Pattern: Constrained Input.

Free-form strings invite invalid values and waste tokens on error handling.

```json
{
  "type": "object",
  "properties": {
    "title": { "type": "string", "minLength": 1, "maxLength": 200 },
    "priority": {
      "type": "string",
      "enum": ["low", "medium", "high", "urgent"],
      "description": "Ticket priority. Default medium."
    },
    "dueDays": { "type": "integer", "minimum": 1, "maximum": 365 },
    "email": { "type": "string", "format": "email" }
  },
  "required": ["title"]
}
```

Enums are self-documenting; still list the values in the description. Never assume
the model obeys the schema: it can hallucinate an unsupported enum value or an
out-of-range number. Validate early and fail with an error that lists the valid values.

### Fewer required parameters

Pattern: Smart Defaults.

Every parameter that can default should. Defaults are context-aware (current user,
current time, the user's only project), match the most common case, are documented
in the parameter description, and are overridable. Never default a destructive option
to on. Resolve defaults at runtime where possible: if the upstream needs a project id
and the user has exactly one project, the parameter is optional and the tool fills it.

### Take the identifier a person has

Pattern: Natural Identifier.

Requiring a UUID forces an extra lookup call on every use. Accept email, `@username`,
or display name, document which forms are accepted, resolve to the system id
internally, and return candidate matches when resolution is ambiguous (see
`tool-design-errors`). Cache resolutions where privacy policy allows.

### Exactly one of

Pattern: Mutual Exclusivity.

When a tool takes alternative selectors, the description lists every valid combination
("Provide exactly one of `conversationId`, `channelName`, or `userEmails`"), the tool
counts what was supplied at the start of execution, and a violation returns a clear
error naming the valid options. Express the rule in the schema too where the runtime
supports `oneOf`.

### Say what is faster or cheaper

Pattern: Performance Hint.

The agent cannot see cost. Tell it: "Prefer `conversationId` (direct) over
`channelName` (requires a lookup)", "For more than one item use `batch_get`", "Large
exports take minutes; use `start_export` and poll". Be specific about why. If evals show
the agent ignores the hint, strengthen the wording rather than adding a parameter.

### Accept what the agent will send

Pattern: Parameter Coercion.

Agents send `"2024-01-15"`, `"January 15"`, and `"yesterday"` for the same date; numbers
as strings; a single item where an array is expected; mixed case for identifiers.
Accept them, normalize early to one canonical form, document the accepted formats,
and log the format received so drift shows up in traces. Coercion is for benign
variation; it never widens a constrained enum or bypasses validation.

## Naming and parameter conventions

- Verb-object names; the same verb means the same thing across the set (`list_*`
  returns pages, `get_*` returns one, `search_*` takes a query).
- One casing convention for every parameter in the set.
- Parameter names say what the value is, not how it is used internally
  (`recipientEmail`, not `to`).
- Booleans read as questions with a safe default (`includeArchived: false`).
- No parameter exists only to carry a credential, a tenant id, or a trust decision;
  those come from context (`tool-design-security`).

## Anti-patterns

- A description that restates the name ("get_user: gets a user").
- `status: string` where five values are valid.
- Six required parameters for a call that usually needs one.
- Accepting only the internal UUID and no human identifier.
- Two selector parameters with no rule about supplying both or neither.
- Rejecting `"2024-01-15T00:00:00Z"` because the schema said `date`.
- A parameter named `data` or `options` that hides the real inputs.
- A `type: "string"` parameter (`payload`, `configJson`) that asks the model for
  stringified JSON. Models drop escapes when they nest JSON in a string. Declare
  `{ "type": "object" }` with its own `properties` instead.

## On Runtype

- **Where the interface lives.** On a saved tool (`create_tool`, `update_tool`),
  `description` is the model-facing text and `parametersSchema` is the JSON Schema the
  model sees. On create, `name` is limited to 100 characters and `description` to 500,
  so put what, when, prerequisites, and returns first, and move long examples into
  parameter descriptions. Validate inline (runtime) tools before saving with
  `validate_flow`, `validate_product_agent`, or `validate_product`.
- **Object schema at the root.** `parametersSchema` must declare `type: "object"` at the
  top level, or the tool fails when it is dispatched. For a tool with no inputs, such
  as `who_am_i`, use `{ "type": "object", "properties": {}, "required": [] }`. Wrap a
  list input in an object property instead of making the root an array. On a runtime
  tool, the validator flags a string parameter that asks for JSON (named `json`,
  `config`, `configuration`, or `payload`, or described as a JSON string) as
  `TOOL_PARAM_EMBEDDED_JSON_STRING`.
- **Names as the model sees them.** Write tool names in lowercase `snake_case`. Before
  the model sees a name, Runtype lowercases it, replaces every character other than
  `a-z`, `0-9`, and `_` with `_`, collapses repeated underscores, and trims leading and
  trailing underscores. A name that then starts with a digit gets a `tool_` prefix. A
  camelCase name loses its word boundaries (`sendEmail` becomes `sendemail`), and two
  names on one step that normalize to the same string are renamed with a numeric suffix
  (`send_email`, `send_email_1`).
- **Unique and reserved names.** Keep saved tool names unique in the account: a
  `tool:<name>` reference that matches two active tools fails validation with
  `TOOL_NAME_AMBIGUOUS`. The `runtype_` prefix is reserved for platform tools, so do not
  start a custom tool name with it. A tool whose model-facing name matches
  `runtype_set_state` is rejected at save time (`RESERVED_TOOL_NAME`) and dropped at
  run time.
  `_approvalReason` is a reserved parameter the platform appends to approval-gated
  tools; never declare it yourself.
- **Context-supplied parameters.** On runtime (inline) tools, list parameters that come
  from context in `hiddenParameterNames`. The runtime fills them from execution
  variables and removes them from the model's schema, so the model never passes tenant
  or auth context. Names that start with `_internal` are rejected; pass credentials as
  `{{secret:NAME}}` references instead.
- **User-supplied parameters.** When a value belongs to the person, not the model (a
  confirmation amount, an identifier only the user knows), declare it in
  `config.elicit: { message, requestedSchema, merge: "parameters" }` on an external or
  custom tool. Runtype removes those fields from the model's schema and asks the user
  for them before the call runs. Each requested property is a string, number, integer,
  or boolean. The final `parametersSchema` must set `additionalProperties: false`, and
  each requested property must match its definition there, including whether it is
  required.
- **Idempotency.** Set `idempotent: true` on a runtime tool that is safe to call a
  second time when an interrupted turn resumes.
- **External tool templates.** In `body`, write `{{param}}` with no surrounding quotes;
  values are typed automatically (strings quoted, numbers and booleans bare, objects
  serialized). URL and header templates substitute raw text. An optional parameter
  interpolated with no fallback ships a literal `{{param}}` when omitted; the validator
  flags it as `OPTIONAL_PARAM_IN_TOOL_TEMPLATE`. Give it a default or make it required.
- **Per-tool settings** for catalog tools go in `tools.toolConfigs` on an agent or
  prompt step, or in `config.toolConfig` on a `tool-call` step, never in extra
  parameters the model must fill.
- **Tool choice strategy.** `toolCallStrategy: "required"` without `maxToolCalls: 1`, or
  with a multi-turn loop, forces a tool call on every step and returns empty output;
  the validator warns with `TOOL_STRATEGY_REQUIRED_MULTISTEP`. Use `"auto"`.
  `"none"` with tools attached silently drops them (`TOOL_STRATEGY_NONE_WITH_TOOLS`).
  Provider-native tools (Anthropic, OpenAI and xAI web search) from two providers on
  one step route to one owner and silently leave the other's tools inert; the
  validator reports `PROVIDER_TOOLS_MIXED_OWNERS`.
- Names and descriptions are all that separate one tool from its neighbors, and with tool
  search (on by default for multi-turn agents at 20+ tools) they are also what the model
  searches; a vague description loses to a specific one.
- Built-in and Orthogonal tools ship with reviewed descriptions; read them through
  `get_platform_documentation(topic="builtin-tools")` and
  `get_platform_documentation(topic="orthogonal-tools")` as house style before writing
  a custom tool beside them.
- For the full field reference per tool type, read the Creating custom tools, Creating
  external tools, and Runtime tools pages in the Runtype docs, or call
  `search_documentation(query="runtime tools")`.
