# Setup and API fallback

## Existing MCP connection

The creation server is `https://mcp.magichour.ai/`. Discover tools, call `ping`, then use `account_retrieve` before the first paid job to check actual API authorization. Discovery can work without credentials. A missing bearer token produces `Authentication required`; an invalid token can still receive `pong` from `ping` while the account read returns `401`. Do not reinstall skills to fix a credential error or treat `pong` alone as authenticated readiness.

For client-specific authentication, follow the maintained [MCP user guide](https://github.com/magichourhq/magic-hour-mcp/blob/main/user.md). Claude custom connectors currently require OAuth client ID `magic-hour-mcp`; do not assume dynamic client registration. API-key bearer authentication is available in compatible clients.

For Codex CLI, with `MAGIC_HOUR_API_KEY` already set securely in the shell used to launch Codex:

```sh
codex mcp add magic-hour --url https://mcp.magichour.ai/ --bearer-token-env-var MAGIC_HOUR_API_KEY
```

Restart the client session if the new tools are not discovered. Follow the user's configuration scope and preserve unrelated MCP servers.

## Use the API without MCP

The base URL is `https://api.magichour.ai`. Read the [current OpenAPI document](https://docs.magichour.ai/api-reference/openapi.json) for the exact request schema and send API requests with `Authorization: Bearer` using the environment value. Keep credentials on the server or local runtime, never in a browser bundle.

Prefer the official [Python SDK](https://github.com/magichourhq/magic-hour-python) or [Node SDK](https://github.com/magichourhq/magic-hour-node) already used by the project. Their `generate` helpers handle supported uploads, polling, and downloads. Consult the installed SDK's current signature before using it.

For direct HTTPS, the lifecycle is:

1. Upload inputs when required: `POST /v1/files/upload-urls`, then `PUT` the bytes to the returned URL.
2. Submit one job using the desired generation endpoint, such as `POST /v1/ai-image-generator` or `POST /v1/image-to-video`.
3. Retain the returned `id` and poll `GET /v1/image-projects/{id}`, `GET /v1/video-projects/{id}`, or `GET /v1/audio-projects/{id}` as appropriate.
4. On `complete`, use `downloads` to retrieve the output. Stop on `error` or `canceled`. Bound polling by time and respect rate limits.

Do not retry a creation POST automatically after an ambiguous network failure. Retry or resume retrieval of a known job instead. Do not claim that an idempotency header is supported unless the current API documents it.

Useful maintained references:

- [Create an API key](https://magichour.ai/developer)
- [Quick start](https://docs.magichour.ai/get-started/quick-start)
- [Inputs and outputs](https://docs.magichour.ai/integration/inputs-and-outputs)
- [Postman collection](https://docs.magichour.ai/integration/postman)
- [API pricing and calculator](https://magichour.ai/api)
