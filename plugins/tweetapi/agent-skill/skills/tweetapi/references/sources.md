# Where to check facts

Use the narrowest source that answers the question, and check again whenever exact names, parameters or limits matter.

| Question | Source |
| --- | --- |
| What exists, and where to look | <https://tweetapi.com/llms.txt> |
| Endpoint details, parameters and responses | <https://tweetapi.com/ai-docs-v2.txt>, or the endpoint's own page under <https://tweetapi.com/docs> |
| Exact request and response schemas | <https://tweetapi.com/openapi-v2.json> |
| Prices, unit costs and billing rules | <https://tweetapi.com/pricing.json> |
| Agent and MCP setup | <https://tweetapi.com/docs/getting-started/agents> and <https://tweetapi.com/mcp> |
| SDK methods | <https://github.com/tweetapi/node> and <https://github.com/tweetapi/python> |
| Postman | <https://tweetapi.com/postman-v2.json> (every endpoint) and <https://tweetapi.com/postman-quickstart-v2.json> (three public reads) |
| Product overview | <https://tweetapi.com/docs/getting-started/overview> |
| Terms and privacy | <https://tweetapi.com/terms> and <https://tweetapi.com/privacy> |

These sources describe the whole API, including write and account endpoints. Being documented doesn't put an endpoint in scope: the rule in [SKILL.md](../SKILL.md) does.

Take parameter names from the endpoint docs, and SDK method names from the SDK's README. One doesn't tell you the other.

If two sources disagree about an endpoint you're about to call, tell the user and hold that call until it's settled. If a source can't be reached, say what you couldn't check instead of answering from memory.
