# Current public sources

Read the narrowest source that answers the task. Recheck these sources when exact endpoints, parameters, response fields, or installation steps matter.

## Canonical TweetAPI sources

- Documentation index: <https://tweetapi.com/llms.txt>
- Consolidated API documentation: <https://tweetapi.com/ai-docs-v2.txt>
- Product overview: <https://tweetapi.com/docs/getting-started/overview>
- Agent integration guide: <https://tweetapi.com/docs/getting-started/agents>
- OpenAPI 3.0.3 specification: <https://tweetapi.com/openapi-v2.json>
- Full Postman collection: <https://tweetapi.com/postman-v2.json>
- Read-only Postman quick start: <https://tweetapi.com/postman-quickstart-v2.json>
- Machine-readable pricing, unit costs, and billing rules: <https://tweetapi.com/pricing.json>
- Hosted MCP page: <https://tweetapi.com/mcp>
- Hosted MCP endpoint: <https://mcp.tweetapi.com/mcp>
- Node SDK: <https://github.com/tweetapi/node>
- Python SDK: <https://github.com/tweetapi/python>
- Privacy policy: <https://tweetapi.com/privacy>
- Terms of service: <https://tweetapi.com/terms>

Treat `llms.txt` as the discovery index and `ai-docs-v2.txt` as the current machine-readable documentation bundle. Answer price, plan, and unit-cost questions from `pricing.json` rather than remembered figures. Prefer the endpoint's public documentation page when it contains more specific constraints.

## Source rules

- Do not copy the complete endpoint catalog into this skill. It will drift.
- Do not assume a documented operation is inside this skill's read-only scope.
- Do not infer parameter names from an SDK method or vice versa.
- Do not invent missing response fields, cursor behavior, or limits.
- If public sources conflict, name the conflict and ask the user before making a live request.
- If a source cannot be reached, say what could not be verified and avoid presenting remembered details as current.

## Public contract artifacts

The OpenAPI document is the canonical public contract for the customer-facing `/tw-v2` API. The full Postman collection is generated from that OpenAPI document rather than maintained independently. The read-only quick start is a smaller onboarding collection for public-data requests.

Use these published artifacts directly; do not copy them into this skill or edit generated copies. Recheck the documentation index and the URLs above when exact contract availability matters.

The OpenAPI document, full Postman collection, and public API documentation also describe write, account, and private-data capabilities. Those remain outside this skill even when their contracts are public. The read-only quick start does not expand the hosted MCP tool allowlist.
