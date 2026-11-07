# Server Design

How to design what an MCP server exposes — tools, resources, prompts, errors, state, and server instructions — so a model can use it correctly and a host can afford to load it. The normative rules come from the `2026-07-28` specification; the design guidance comes from host vendors' published evaluations and is labeled as such.

> Korean version: [`server-design.ko.md`](server-design.ko.md)

## Contents

- Pick the primitive by who controls it
- Tool surface
- Errors
- State across calls
- Asking for input mid-call
- Resources and prompts
- Server instructions
- Annotations
- Extensions
- Verify the design

## Pick the primitive by who controls it

The server overview fixes who decides when each primitive is used (checked 2026-11-07).

| Primitive | Controlled by | Use it for | Do not use it for |
|---|---|---|---|
| Tool | The model | Actions and queries the model should decide to run | Data the application should attach on its own schedule |
| Resource | The application | Context the host attaches or the user picks: files, records, schemas, identified by URI | Operations with side effects |
| Prompt | The user | Templates a person invokes explicitly, such as a slash command | Hidden instructions the model should always follow |

"User-controlled" decides *when* a prompt is used, "not who authors its content"; the server still writes prompt content, so prompts are server-supplied text like any other.

For workflow knowledge rather than callable operations, the Skills extension (`io.modelcontextprotocol/skills`, Beta) serves agent skills as resources that hosts read lazily — "Hosts **MUST NOT** retrieve files ahead of need" (skills extension page, checked 2026-11-07). It is opt-in, and host support is uneven; do not depend on it without checking the target host.

## Tool surface

Normative rules (tools page, checked 2026-11-07):

- Names **SHOULD** be 1–128 characters, case-sensitive, using only `A-Z a-z 0-9 _ - .`, and unique within the server. SEP-986 originally proposed 1–64 characters with `/` allowed; the specification text supersedes it.
- `tools/list` **MUST NOT** vary per connection or as a side effect of other requests; it **MAY** vary by the authorization on the request, for example returning only tools the caller's scopes allow.
- Tools **SHOULD** come back in a deterministic order, which "improves LLM prompt cache hit rates when tools are included in model context".
- `inputSchema` **MUST** be a valid JSON Schema object (2020-12 by default; any 2020-12 keyword is allowed). A tool with no parameters should use `{"type": "object", "additionalProperties": false}`.
- With an `outputSchema`, the server **MUST** return conforming `structuredContent`, and for backwards compatibility **SHOULD** also return the serialized JSON in a text block.

Design guidance from Anthropic's tool-evaluation work ("Writing effective tools for agents", 2025-09-11, checked 2026-11-07) — vendor practice, not protocol:

| Guideline | Concrete form |
|---|---|
| "More tools don't always lead to better outcomes." | Build a few tools shaped around tasks, not a 1:1 wrapper per API endpoint: `schedule_event` instead of `list_users` + `list_events` + `create_event`; `search_logs` instead of `read_logs`. |
| Namespace by service or resource | Prefix or suffix related tools; the article reports that the choice has "non-trivial effects" on evaluations, so measure it. |
| Return high-signal fields | Prefer names, URLs, and file types over opaque identifiers such as `uuid` or `mime_type`; add a `response_format` enum (`concise` / `detailed`) when callers sometimes need IDs. The article measured roughly a third of the tokens with concise responses. |
| Bound response size | Paginate, filter, or truncate with sensible defaults, and say in the truncated output how to get more. |
| Name parameters unambiguously | `user_id`, not `user`; describe each tool as you would to a new teammate. |

Hosts enforce their own ceilings. Claude Code warns when a tool's output exceeds 10,000 tokens and caps it at 25,000 tokens by default (Claude Code MCP docs, checked 2026-11-07). A server that returns more than its callers can hold is broken for them, whatever the specification allows.

## Errors

The tools page separates two channels (checked 2026-11-07).

| Channel | Use for | Shape |
|---|---|---|
| Protocol error | Unknown tool, malformed request, server fault | JSON-RPC `error` (for example `-32602`) |
| Tool execution error | API failures, input validation failures, business-rule violations | `result` with `isError: true` and readable `content` |

Clients **SHOULD** pass execution errors to the model "to enable self-correction"; they only **MAY** pass protocol errors. Put validation failures in the execution channel, and write the message as an instruction the model can act on — "Invalid departure date: must be in the future. Current date is …" — rather than a code or stack trace.

## State across calls

There is no protocol session. A server that needs state across calls returns an explicit handle from a creating tool and accepts it as an argument afterwards; the tools page gives this as non-normative design guidance (checked 2026-11-07).

- **A handle is a name, not a credential.** Authenticated servers check the caller against the handle on every call; unauthenticated servers make handles high-entropy (for example UUIDv4) and short-lived.
- **Keep handles opaque.** Encoded structure invites parsing and guessing.
- **State the lifetime in the creating tool's description** ("baskets expire after 24 hours of inactivity") so the model sees it before creating state.
- **Expired or unknown handles return a tool execution error that says so**, letting the model recover by creating a new one.

The security side of the same pattern — binding handles to the authenticated user — is in [`security-and-authorization.md`](security-and-authorization.md).

## Asking for input mid-call

When a tool needs a confirmation or a missing parameter, return `InputRequiredResult` with an `elicitation/create` request instead of failing ([`protocol-2026-07-28.md`](protocol-2026-07-28.md)).

- Ask only for modes the client declared (`form`, `url`); otherwise the request fails with `-32021`.
- Form mode accepts a flat object of primitive properties only. Never request passwords, API keys, tokens, or payment credentials through it; those go through URL mode.
- Do not assume the client will answer. Design the tool so that a missing answer leaves no half-applied change.
- Do not build new features on Roots or Sampling; both are deprecated. Take directories as tool parameters or configuration, and call a model provider directly when the server needs generation.

## Resources and prompts

- Resource-not-found returns `-32602` (clients **SHOULD** still accept the legacy `-32002`); servers **MUST NOT** answer a missing resource with an empty `contents` array.
- `file://` resources **MUST** sanitize paths against directory traversal.
- Resource links a tool returns are "not guaranteed to appear in the results of a `resources/list` request"; do not make the model depend on discovering them through listing.
- Prompt inputs and outputs **MUST** be validated against injection.
- List endpoints paginate with opaque cursors; clients **MUST NOT** parse them, and a missing `nextCursor` marks the end.

## Server instructions

`server/discover` may return `instructions`: text a host can place in the model's context to explain how the server's features fit together (discover page, checked 2026-11-07). The maintainers' guidance (server-instructions post, 2025-11-03, checked 2026-11-07):

- Write what tools and resources cannot convey on their own: ordering between tools, cross-tool relationships, rate limits, and operating constraints.
- Do not repeat tool descriptions, add marketing, give general behavioral instructions, or write a manual.
- Instructions do not guarantee behavior. "Don't rely on instructions for any critical actions … especially in security or privacy domains. These are better implemented as deterministic rules or hooks."
- Hosts decide whether and where to inject them. Test the target host before relying on them.

The post's own evaluation is small and attributed: 40 sessions in one host, where one model followed the intended three-step review workflow 8/10 times with instructions and 2/10 without, while another followed it 9/10 and 10/10. Read it as evidence that instructions help some models, not as an effect size.

## Annotations

`ToolAnnotations` carries four hints — `readOnlyHint` (default `false`), `destructiveHint` (default `true`), `idempotentHint` (default `false`), `openWorldHint` (default `true`) — plus `title`. The defaults assume the worst, and clients **MUST** treat annotations as untrusted unless the server is trusted (tools page; annotations post, 2026-03-16; checked 2026-11-07).

- Set them truthfully: `readOnlyHint: true` on read-only tools, `destructiveHint: false` on additive ones, `openWorldHint: false` on closed-domain tools. Hosts use them to decide when to ask for confirmation.
- Never rely on them for safety. "An untrusted server can lie", and "if you need a guarantee that a tool can't exfiltrate data, that's a job for network controls or sandboxing, not a boolean hint."
- Annotations describe one tool; risk depends on the other tools in the session ([`security-and-authorization.md`](security-and-authorization.md)).

## Extensions

Extensions add capabilities outside the core under an identifier `{vendor-prefix}/{extension-name}` and are "always disabled by default and require explicit opt-in" (extensions overview, checked 2026-11-07). When one side lacks an extension, the other **MUST** fall back to core behavior or reject the request.

| Extension | Status (2026-11-07) | Use when |
|---|---|---|
| MCP Apps (`io.modelcontextprotocol/ui`) | Stable | A tool's result is an interactive UI the host renders in a sandboxed frame |
| Tasks (`io.modelcontextprotocol/tasks`) | Beta, headed to core | Long-running work the client polls with `tasks/get`; return a task only to clients that declared support |
| Skills (`io.modelcontextprotocol/skills`) | Beta | Serving agent skills as lazily read resources |
| OAuth Client Credentials, Enterprise-Managed Authorization | Stable | Machine-to-machine access and enterprise identity-provider policy |

The community client-support matrix and the Apps overview disagree about which hosts implement which extension; verify against the target host rather than either list.

## Verify the design

Protocol conformance ([`build-test-ship.md`](build-test-ship.md)) does not show that a model can use the tools. Anthropic's tool-evaluation method (checked 2026-11-07): build realistic tasks that need several, sometimes dozens of, tool calls; pair each with a verifiable outcome; avoid verifiers that reject correct answers over formatting; hold out a test set; and track calls, tokens, and errors alongside accuracy. Keep each run's transcript and tool calls so a reviewer can check the trajectory, not only the final answer.

## Sources

> All links checked 2026-11-07; specification pages are the `2026-07-28` revision, and blog dates are as printed on each post.

| Claim | Source | Published |
|---|---|---|
| Control model per primitive | <https://modelcontextprotocol.io/specification/2026-07-28/server> | rev. 2026-07-28 |
| Tool names, listing rules, schemas, errors, stateful-tool guidance, annotation trust | <https://modelcontextprotocol.io/specification/2026-07-28/server/tools> | rev. 2026-07-28 |
| Resource errors, traversal rule | <https://modelcontextprotocol.io/specification/2026-07-28/server/resources> | rev. 2026-07-28 |
| Prompt control nuance and validation | <https://modelcontextprotocol.io/specification/2026-07-28/server/prompts> | rev. 2026-07-28 |
| Cursor opacity | <https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/pagination> | rev. 2026-07-28 |
| Elicitation modes and secret prohibition | <https://modelcontextprotocol.io/specification/2026-07-28/client/elicitation> | rev. 2026-07-28 |
| `instructions` in the discover result | <https://modelcontextprotocol.io/specification/2026-07-28/server/discover> | rev. 2026-07-28 |
| Original tool-name proposal | <https://modelcontextprotocol.io/seps/986-specify-format-for-tool-names> | Final SEP |
| Server-instruction guidance and evaluation | <https://blog.modelcontextprotocol.io/posts/2025-11-03-using-server-instructions/> | 2025-11-03 |
| Annotation semantics and limits | <https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/> | 2026-03-16 |
| Extension identifiers, opt-in, status | <https://modelcontextprotocol.io/extensions/overview> | undated |
| Skills extension lazy retrieval | <https://modelcontextprotocol.io/extensions/skills/overview> | undated |
| Tool design and evaluation method | <https://www.anthropic.com/research/writing-tools-for-agents> | 2025-09-11 |
| Host output warning and cap | <https://code.claude.com/docs/en/mcp> | checked 2026-11-07 |
