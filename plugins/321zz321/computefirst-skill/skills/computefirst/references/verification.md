# Verification record

Snapshot date: 2026-10-16. Requests used Node fetch or curl against the live HTTPS service without authentication, personal data, optional model headers, or reporting calls. Example inputs are synthetic.

| Surface | Evidence obtained |
| --- | --- |
| [`/llms.txt`](https://computefirst.net/llms.txt) | HTTP 200; free, no key/sign-up; discovery flow; 793 catalog tools. |
| [`/.well-known/mcp.json`](https://computefirst.net/.well-known/mcp.json) | HTTP 200; `catalog.toolCount` 793; Streamable HTTP endpoint; authentication not required. |
| [`/openapi.json`](https://computefirst.net/openapi.json) | HTTP 200; search parameters, versioned contract/execute paths, error statuses, batch schema. |
| [`/v1/stats`](https://computefirst.net/v1/stats) | HTTP 200; `tools` 793. |
| [`/llms-full.txt`](https://computefirst.net/llms-full.txt) | HTTP 200; 793 versioned catalog entries counted. |
| [`/mcp`](https://computefirst.net/mcp) | Initialize 200, initialized notification 202; tools/list 200 with 15 gateway tools; search, describe, execute succeeded. Numeric decimal input returned HTTP 200 with `isError: true`. |
| [`/mcp/chatgpt`](https://computefirst.net/mcp/chatgpt) | Initialize 200, initialized notification 202; tools/list 200 with 40 named tools; decimal_add succeeded. Oversized arguments returned `curated_input_limit`. |
| `/v1/tools/search?q=…` | All six exact example ids discovered at version 1.0.0; unknown synthetic task returned empty results. Oversized query returned 400. |
| `/v1/tools/{id}/versions/1.0.0` | HTTP 200 for all six example contracts; checked supported/unsupported scope, schemas, semantics, limits. Unknown synthetic id returned 404. |
| `/v1/tools/{id}/versions/1.0.0/execute` | All six worked examples returned HTTP 200; their complete result members appear verbatim in SKILL.md. Invalid types/notation returned 400; oversized body returned 413. |
| [`/docs#limits`](https://computefirst.net/docs#limits) | Published quotas, body ceiling, UTC/ISO behavior, and error handling read; quotas were not exhausted to test them. |

Client syntax comes from the official documentation linked next to each snippet in [setup.md](setup.md). Plugin/marketplace manifests can be checked with the installed Claude Code CLI using `claude plugin validate .` and `claude plugin validate .claude-plugin/plugin.json`. No GitHub publication or remote installation is implied by local validation.

Run from the repository root with Node.js 22 or later and network access:

```sh
node scripts/verify-examples.mjs
```

The dependency-free script reads the curl requests and expected JSON directly from SKILL.md; it has no separate expected-output fixtures. It checks discovery metadata/counts, search and contracts, all six result members, and both MCP connections. Any result difference, HTTP/RPC/tool error, malformed example, or count drift exits nonzero. It does not regenerate outputs, report savings, sign in, or retry calls automatically. Only the deterministic result member is compared; surrounding response metadata is excluded explicitly.
