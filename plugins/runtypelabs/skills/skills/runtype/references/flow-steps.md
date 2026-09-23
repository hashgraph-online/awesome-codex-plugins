# Flow Steps: Selection and Pitfalls

Use `get_build_instructions(task="generate-flow")` for design and
`get_platform_documentation(topic="flow-step-types")` for the current catalog.
Fetch `types-flow-steps` for exact config types. This reference is a decision guide,
not a second schema registry; validate the complete `name` + `steps` before saving.

## Pick the smallest suitable step

| Need                                       | Step                                                  |
| ------------------------------------------ | ----------------------------------------------------- |
| Generate prose, classify, or extract JSON  | `prompt`                                              |
| Invoke a saved agent                       | `execute-agent`                                       |
| Format existing data into a document       | `template`; `generate-pdf` for a hosted PDF           |
| Host a file                                | `store-asset`                                         |
| HTTP retrieval / structured API call       | `fetch-url` / `api-call`                              |
| Fetch multiple pages / crawl a site        | `paginate-api` / `crawl`                              |
| Search the web                             | `search` or a provider-compatible search tool         |
| Invoke one exact tool without model choice | `tool-call`                                           |
| Deterministic shaping, filtering, or math  | `transform-data`                                      |
| Read one record / an array of records      | `get-record` / `list-records`                         |
| Write metadata / update a known record     | `upsert-record` / `update-record`                     |
| Embed, retrieve, or store vectors          | `generate-embedding`, `vector-search`, `store-vector` |
| Durable memory                             | `save-memory`, `recall-memory`, `memory-summary`      |
| Communicate                                | `send-email`, `send-event`, `send-stream`             |
| Choose a branch / bounded repetition       | `conditional` / `loop`                                |
| Set a value / poll an external endpoint    | `set-variable` / `wait-until`                         |

`retrieve-record` is deprecated: use the explicit object/array readers instead.
For GitHub retrieval, use a supported HTTP or catalog tool; there is no `fetch-github`
step. Do not infer a step type from a tool's name.

## Variables and inputs

- Outputs use `config.outputVariable`, not the display name of the step. Reference
  them as `{{variable.field}}`; read them as `input.variable.field` in transform JS.
- `get-record` returns one object; `list-records` returns an array, even for one match.
- `upsert-record.sourceVariable` must resolve to a JSON object containing metadata,
  not a string or `{ name, type, metadata }` wrapper. A stable `recordName` is required
  for repeatable upserts; omitting it creates a new timestamp-named record each run.
- Use `{{secret:KEY}}` for credentials. Do not inline values or use legacy dispatch
  `secrets` maps. Secret values belong in secure intake, not templates or chat.

## Control flow and code

Steps run in order. Use `when` for an optional step, `conditional` for mutually exclusive
sequences (binary or named branches), and `loop` for bounded repetition. Exact enum or
permission rules belong in deterministic code, not an LLM router. Skipped steps leave
existing variables untouched; prefer explicit branch outputs over shared-variable writes.

There is no `parallel` step type. Use a supported code-mode tool chain for independent
tool calls or a batch for many records. Do not assume every sandbox can fetch, access
credentials, or invoke other flows; check its provider and tool-pool capabilities first.

`wait-until` polls through `config.poll` (`http`, `success`, optional `intervalMs` and
`maxAttempts`); it is not a generic `condition` + `timeoutMs` step. Read
`operational-design` before configuring durable waits, retries, or long-running crawls.

## Failure and delivery

For a load-bearing output, explicitly set `config.errorHandling: { onError: "fail" }`.
Many context-step operation failures otherwise continue with a default/null output.
Input-contract failures are different: an invalid `upsert-record` source or unresolved
`update-record` target reports failure without writing output by default.

Isolate side effects and use idempotency keys where supported. A separate step or approval
gate does not guarantee exactly-once delivery; inspect status before retrying an ambiguous
send/payment timeout. Use safe test targets and verify the user-facing surface, not only
the underlying flow.
