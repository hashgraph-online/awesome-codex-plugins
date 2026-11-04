# Limits and error handling

Read the selected version's contract before relying on any bound. The live [service limits](https://computefirst.net/docs#limits), [OpenAPI](https://computefirst.net/openapi.json), and MCP `tools/list` were retrieved on 2026-10-16. Quotas below are published values, not load-test results.

## Bounds

| Surface | Verified contract or published bound |
| --- | --- |
| REST search | English lexical search; query up to 256 UTF-8 bytes and 40 distinct normalized terms; `limit` 1–5 (REST default 1). Use an explicit limit. |
| MCP search | `query`, optional `limit` 1–5; `include_contract` defaults to true. A confident match may carry its contract. |
| General request body | 262,144 bytes (256 KiB) of encoded JSON; tool-specific input bounds still apply. |
| Curated MCP arguments | 16,384 bytes (16 KiB) of encoded JSON; additional per-operation bounds appear in its schemas. |
| No-key daily executions | 2,000 per network, shared by callers on that network; shared global no-key pool 20,000. UTC-day reset; short-window limits also apply. |
| Hosted connectors | Published claude.ai and ChatGPT connector egress ranges use 7,500 per platform/day and a combined 10,000/day, inside the no-key pool. |
| Batch | 1–20 operations. Each resolved input, individual result, and aggregate response is limited to 256 KiB. Work budgets can refuse additional operations. |

The 793-tool catalog does not imply every tool is available through the 40-tool curated endpoint. A contract's large output allowance also does not override a smaller batch or transport bound.

Selected example-specific bounds:

- `decimal-add@1.0.0`: at most 40 digits excluding sign/point and 18 fractional digits per input. Decimal strings, no exponents, leading plus, or whitespace. This is addition, not currency rounding, tax, or interest.
- `csv-to-json@1.0.0`: up to 256,000 input bytes, 5,000 data rows, 256 columns, 256-byte header names; 1,048,576-byte contract output bound. All cells remain strings.
- `json-deep-diff@1.0.0`: maximum JSON depth 32, 10,000 nodes per value, 1,000 changes. Difference records are not JSON Patch.
- `iso-date-add-months@1.0.0`: years 0001–9999, month delta at most six digits excluding sign, result must stay in range. Calendar-day clamping; no timezone conversion.
- `text-line-endings-normalize@1.0.0`: contract text bound 1,048,576 bytes and output bound 2,097,152 bytes; the request-body ceiling still applies.
- `graph-topological-sort@1.0.0`: at most 2,000 nodes, 10,000 edges, 256-byte node IDs; directed simple graph, cycle rejected, ties by declared node index.

## Errors

Observed REST schema error (HTTP 400, numeric `a` sent to decimal-add):

```json
{"error":{"code":"invalid_input","message":"a must be a string"}}
```

Observed oversized request (HTTP 413):

```json
{"error":{"code":"body_too_large","message":"Request body exceeds 262144 bytes"}}
```

Observed unknown version/tool (HTTP 404):

```json
{"error":{"code":"tool_version_not_found","message":"Unknown tool or version"}}
```

MCP returned the invalid-input body above as JSON in text content with `result.isError: true` and HTTP 200. Curated oversized arguments similarly returned `curated_input_limit` with the message `Curated input exceeds 16 KiB of encoded JSON`.

For `invalid_input`, read `error.message`, recheck schemas **and semantics**, and rebuild the request. Schema shape alone does not establish valid decimal notation, calendar dates, or an acyclic graph. For unknown ids/versions, rediscover; do not invent an alternative version. Empty search results are a valid success response, not proof that a guessed tool exists.

Published HTTP 429 responses carry `error.retry_after` in seconds; wait accordingly. Do not immediately retry unchanged. Published `503 quota_unavailable` means quota checks are temporarily unavailable; the docs advise retrying in a minute. The OpenAPI also documents HTTP 401 if an optional supplied key is invalid; these no-key instructions send none.

## If using batches

Read `/v1/execute-batch` in OpenAPI or MCP `execute_batch`'s listed schema before building a batch. A successful HTTP response may still contain per-item failures: inspect `summary.failed`. Dependencies use JSON Pointers into earlier successful **results**, not their wrappers; self/forward references are disallowed. A failed dependency can skip a later item with 424. `batch_work_limit` means split refused work or run it separately. Finance and exact decimal power/root/expression tools consume the full factory allowance, so send additional factory operations separately. Do not replay already successful items. These batch details were verified from live schemas/documentation; the worked examples deliberately use single executions.
