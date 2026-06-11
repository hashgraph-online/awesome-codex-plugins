# Flow Step Types

Every step in a flow has a `type` and a config blob specific to that type. This is the catalog, grouped by category, with the config hints that matter.

Inside a flow, step results become variables. Reference them with `{{stepName.field}}` in templates (`prompt`, `template`, `api-call`, `send-email`) or via the `input` object in `transform-data` JS code.
Prefer live `flow-step-types` and `types-flow-steps` when available.

## Contents

- [AI steps](#ai-steps)
- [Document steps](#document-steps)
- [Integration steps](#integration-steps)
- [Data steps](#data-steps)
- [Vector steps](#vector-steps)
- [Memory steps](#memory-steps)
- [Communication steps](#communication-steps)
- [Control flow steps](#control-flow-steps)
- [Step composition notes](#step-composition-notes)

## AI steps

### `prompt`

AI model call. Generates text or JSON via an LLM. Supports tool use, streaming, and agent mode for multi-turn tool loops.

Config: `model`, `systemPrompt`, `userPrompt`, `responseFormat` (`text` | `json`), `outputVariable`, `tools`

When to use: any LLM call inside a flow. For agent loops with tool use, register tools here rather than as separate `tool-call` steps.

### `execute-agent`

Run an existing agent with a message and capture the response.

Config: `agentId`, `message`, `outputVariable`

When to use: when a flow's reasoning step is more naturally an existing agent than an inline prompt. Common in multi-agent orchestration.

## Document steps

### `template`

Render a Liquid template into HTML, email-html, markdown, PDF, or text.

Config: `template` (Liquid body), `outputFormat`, `outputVariable`, optional `inputs` map, optional `partials`, optional `pdfOptions`, optional `asArtifact`, optional `streamOutput`, optional `sampleData`

**Prefer over `prompt` when output is a structured document** (invoice, receipt, email body, report) and the data is already available. Templates are deterministic, fast, and cheap. Use a prompt when you need the LLM to write the prose; use a template when you need it formatted.

### `generate-pdf`

Render HTML or markdown to a PDF, store it in asset storage, return a sharable URL.

Config: `html` OR `markdown`, `filename`, `visibility` (`public` | `private`), `pdfOptions` (format, landscape, margin), `outputVariable`

For **inline PDF bytes** (no asset storage), use `template` with `outputFormat: "pdf"` instead.

### `store-asset`

Save a file to asset storage from a URL download or inline base64 content.

Config: `url` OR `content` (base64), `filename`, `contentType`, `visibility`, `outputVariable`

Returns a public URL or signed private URL.

## Integration steps

### `fetch-url`

Make an HTTP request and capture the response.

Config: `http` (url, method, headers, body), `responseType` (`json` | `text` | `xml`), `outputVariable`

Lightweight HTTP. For anything more complex (auth, request templates, response mapping), use `api-call`.

### `api-call`

Structured API call with auth, request templates, and response mapping.

Config: `http`, `auth`, `requestTemplate`, `responseMapping`, `outputVariable`

When to use: when the same API will be called multiple ways in the flow, or when response shape needs explicit mapping. Otherwise `fetch-url` is simpler.

### `paginate-api`

Fetch paginated data from an API endpoint across multiple pages.

Config: `url`, `paginationType`, `entityPath`, `outputVariable`

### `crawl`

Crawl a website and extract content from pages.

Config: `url`, `limit`, `depth`, `outputVariable`

Uses Firecrawl or similar by default — check the workspace's integration config.

### `search`

Web or AI-powered search.

Config: `provider`, `query`, `maxResults`, `outputVariable`

### `fetch-github`

Fetch files or data from a GitHub repository.

Config: `repo`, `path`, `outputVariable`

### `tool-call`

Invoke a specific tool deterministically at a fixed point in the flow.

Config: `toolId`, `parameters`, `outputVariable`

**Prefer registering tools on `prompt` steps over `tool-call`** unless you need a deterministic invocation. Tool-call is for "always run this exact tool here"; prompt-with-tools is for "let the LLM decide".

## Data steps

### `transform-data`

Execute JavaScript code in a sandboxed environment.

Config: `script`, `outputVariable`, `sandboxProvider` (`cloudflare-worker` default | `quickjs` | `runtype-sandbox` | `daytona`; legacy `cloudflare-sandbox` input remaps to `runtype-sandbox`), optional `language` (`javascript` | `typescript` | `python`, defaults to `javascript` for `runtype-sandbox`)

Access flow variables via the `input` object. Return value becomes the step output. Use this for any data shaping that isn't worth a tool — schema conversion, filtering, aggregation, math.

### `retrieve-record`

Load records from the Runtype record store.

Config: `recordType`, `recordName`, `recordFilter` (`{ type, where: { field, op, value } }`), `outputVariable`

Lookup by id, by `type + name`, or via a chip-style `recordFilter` over metadata and top-level columns (`id`, `name`, `createdAt`, `updatedAt`).

### `upsert-record`

Create or update a record.

Config: `recordType`, `sourceVariable` (**must point to a JSON object**), `outputVariable`

### `update-record`

Update specific fields on an existing record.

Config: `recordId`, `recordFilter` (`{ type, where }`), `updates`, `mergeStrategy` (`merge` | `replace` | `deep-merge`), `outputVariable`

Finds the record by id, by `type+name`, or by chip filter (first match wins, ordered by `updatedAt` desc).

## Vector steps

### `generate-embedding`

Create a vector embedding from text.

Config: `inputSource`, `text`, `embeddingModel`, `outputVariable`

### `vector-search`

Search a vector store for semantically similar documents.

Config: `query`, `limit`, `threshold`, `outputVariable`

### `store-vector`

Store vector embeddings in a vector database.

Config: `vectorsSource`, `destination`, `outputVariable`

Typical RAG flow: `crawl` → `transform-data` (chunk) → `generate-embedding` → `store-vector`. At query time: `generate-embedding` → `vector-search` → `prompt` (with retrieved context in the user prompt).

## Memory steps

Long-term agent memory steps — the flow-level equivalent of the auto-injected agent memory tools. Each addresses a memory profile via a `profileTemplate` (supports variables, e.g. `{{_agent.id}}`, `{{_user.id}}`).

### `save-memory`

Ingest text from a variable into a Cloudflare Agent Memory profile.

Config: `profileTemplate`, `contentVariable`, optional `sessionId`, optional `outputVariable`, optional `errorHandling`, optional `defaultValue`

### `recall-memory`

Recall a synthesized answer from a Cloudflare Agent Memory profile for a query.

Config: `profileTemplate`, `queryTemplate`, `outputVariable`, optional `thinkingLevel` (`low` | `medium` | `high`), optional `responseLength` (`short` | `medium` | `long`), optional `errorHandling`, optional `defaultValue`

### `memory-summary`

Fetch a markdown summary of a Cloudflare Agent Memory profile.

Config: `profileTemplate`, `outputVariable`, optional `sessionId`, optional `errorHandling`, optional `defaultValue`

## Communication steps

### `send-email`

Send an email message.

Config: `from`, `to`, `subject`, `html`, `outputVariable`

### `send-text`

Send an SMS text message.

Config: `from`, `to`, `message`, `outputVariable`

### `send-event`

Emit a custom event for downstream consumers or integrations.

Config: `eventType`, `payload`, `outputVariable`

### `send-stream`

Stream a response back to the caller via SSE. Used for `chat` and other streaming surfaces.

Config: `sourceVariable`, `streamType`

## Control flow steps

### `conditional`

Branch the flow based on a JavaScript expression.

Config: `condition` (JS expression), `trueSteps`, `falseSteps`

The condition runs in a sandbox with access to flow variables. Each branch is its own array of steps.

### `set-variable`

Set a flow variable to a static or computed value.

Config: `variableName`, `value`

Lightweight scratchpad — use for constants, derived values you'll reference in templates.

### `wait-until`

Pause flow execution until a condition is met or a timeout occurs.

Config: `condition`, `timeoutMs`, `pollIntervalMs`

Useful for waiting on external state (e.g., a webhook to fire, a record to update).

## Step composition notes

**Variables and templating.** Most config fields that accept text support template syntax: `{{variable.path}}`. This works in `prompt`, `template`, `api-call`, `send-email`, etc. Inside `transform-data`, access the same data via JS: `input.variable.path`.

**Secrets in config.** Use `{{secret:KEY}}` (singular `secret`, colon, UPPER_CASE) inside tool config when a step needs a secret. Don't inline values. `{{secrets:KEY}}` (plural) is invalid; `{{secrets.key}}` (plural with dot) is a different system for per-request dispatch-scoped values.

**Step ordering.** Steps run in declaration order. There's no native parallelism primitive — if you need parallel API calls, do them in a single `transform-data` step with `Promise.all`.

### Per-step `when` conditions

**Every step has an optional `when` condition** — a JS expression that decides whether the step runs at all. If `when` evaluates falsy, the step is skipped.

This is what most "only do this if X" needs. Reach for `when` before reaching for a `conditional` step.

- Use `when` when: "skip this step unless something is true."
- Use `conditional` when: "branch into one of two distinct sequences of multiple steps."
- Use sandbox `transform-data` for complex branching as a last resort.

### Per-step error handling

Default: **on failure, continue to the next step.** This is intentional because downstream LLMs often handle gaps gracefully (e.g. "I couldn't look up X, but here's what I can tell you anyway").

Configurable per step:

- **Retry count** — how many times to retry on transient failure.
- **Retry backoff** — wait time between retries.
- **Retry with fallback model** — for `prompt` steps, retry with a different model on failure.
- **Hard fail** — stop the whole flow.

Set this intentionally. Critical steps (the final `send-email`, the only `upsert-record`) should usually hard-fail rather than continue. LLM steps that produce text the next step massages can usually continue.

### Per-step streaming visibility

Runtype is streaming-native. Every step can be configured to either expose its output in the user-visible stream or hide it.

Defaults: long-running steps usually expose progress; pure computation steps usually don't.

For explicit user-visible messages mid-flow, use `send-stream` steps ("Looking up your order...", "Generating the report..."). These are different from automatic step output — they're intentional user-facing communications during execution.

### Code execution is the last line of defense

Common anti-pattern: pre-processing JSON to clean it up before passing to a `prompt` step. The LLM almost always handles the raw JSON fine. Skip the transform.

Use `transform-data` for:

- Genuine fan-out (parallel API calls via `Promise.all`)
- Complex branching that's clearer in code than in `conditional` blocks
- Sensitive-data shielding (compute something the LLM shouldn't see)
- Math, aggregation, schema reshaping where determinism matters

Don't use `transform-data` to:

- Replicate business logic that lives in your internal system — register an API call as a tool instead
- Clean up JSON for an LLM — the LLM can read it as is
- Sequence things that could be sequenced declaratively as separate steps

**Keep flows focused.** When a flow grows large, consider splitting it into sub-flows (call them via `dispatch` from inside `transform-data`, or via `execute-agent` if the sub-step is more naturally an agent). The one enforced structural limit is nested `conditional` depth, capped at 10.
