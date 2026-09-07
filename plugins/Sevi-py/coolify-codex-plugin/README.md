# Coolify Codex Plugin

Control Coolify Cloud or a self-hosted Coolify instance from Codex through a local MCP server and a Coolify-aware workflow skill.

The plugin is built around a sanitized endpoint index generated from Coolify's official OpenAPI spec for the `v4.x` branch. It includes named tools for the workflows agents use most often, plus a generic API request tool and OpenAPI search for complete endpoint coverage as Coolify evolves.

## Capabilities

- Check Coolify health and version.
- List and inspect applications, databases, deployments, projects, resources, servers, services, and teams.
- Start, stop, and restart applications, databases, and services.
- Trigger deployments by UUID or tag.
- Read deployment history across applications without mistaking the running-deployments endpoint for full history.
- Read recent application logs.
- List, create, update, bulk update, and delete environment variables.
- Call any Coolify `/api/v1` endpoint with `coolify_request`.
- Search the bundled OpenAPI file with `coolify_openapi_search`.

## Requirements

- Node.js 20 or newer.
- Coolify Cloud, or a self-hosted Coolify instance with API access enabled.
- A Coolify API token.

## Install from GitHub

Add the Awesome Codex Plugins marketplace and install Coolify:

```bash
codex plugin marketplace add hashgraph-online/awesome-codex-plugins --ref main
codex plugin add coolify@awesome-codex-plugins
```

The plugin is also listed in the [Awesome Codex Plugins registry](https://github.com/hashgraph-online/awesome-codex-plugins#tools--integrations).

Create an API token in Coolify at `/security/api-tokens`. Use the least-privileged token that can perform the work you want Codex to do.

After installing from the Codex plugin marketplace, start a new Codex thread and ask:

```text
Connect Coolify
```

Codex will open a short-lived local setup page. Choose Coolify Cloud or self-hosted first; for self-hosted instances, enter the instance URL so the matching token page is shown. The token is saved locally and is not returned to the chat.

For local development, you can also run:

```bash
npm run setup
npm run setup -- --save
```

For local development without a URL argument, the terminal helper targets Coolify Cloud at `https://app.coolify.io`. Pass a URL when you want to use a self-hosted instance.

## Configuration

Marketplace users should use the browser setup opened by `coolify_configure`; it asks whether the instance is Coolify Cloud or self-hosted before showing a token link. For local development, run:

```bash
npm run setup -- --save
```

For self-hosted instances, pass either the instance root or the API root:

```bash
npm run setup -- --save https://coolify.example.com
npm run setup -- --save https://coolify.example.com/api/v1
```

The token is stored in the operating system credential store when available: macOS Keychain, Windows Credential Manager, or Linux Secret Service via `secret-tool`. If no native credential store is available, the plugin stores it in a local config file under `CODEX_HOME` or `~/.codex` with owner-only permissions. `COOLIFY_BASE_URL` and `COOLIFY_API_TOKEN` are still supported as fallbacks for automation.

## MCP Tools

| Tool | Purpose |
| --- | --- |
| `coolify_setup` | Generate setup URLs and token guidance. |
| `coolify_configure` | Open a local browser setup page or save a Coolify URL and API token locally. |
| `coolify_config_status` | Check whether a connection is configured without revealing the token. |
| `coolify_logout` | Remove the saved local connection. |
| `coolify_health` | Check instance health and version. |
| `coolify_openapi_search` | Find official endpoints, schemas, and request shapes. |
| `coolify_request` | Call any relative Coolify API path. |
| `coolify_list` | List common resource kinds. |
| `coolify_get` | Fetch one common resource. |
| `coolify_lifecycle` | Start, stop, or restart a resource. |
| `coolify_deploy` | Trigger a deployment. |
| `coolify_deployment_history` | List deployment history for one application or all applications. |
| `coolify_application_logs` | Fetch application logs. |
| `coolify_envs` | Manage environment variables. |

Sensitive-looking fields are redacted by default. Some tools accept `revealSensitive: true` for cases where the raw API response is explicitly needed.

`coolify_list` with `kind: "deployment"` mirrors Coolify's `GET /deployments` endpoint, which lists currently running deployments. Use `coolify_deployment_history` when you need historical deployments.

## Development

```bash
npm run setup -- --no-open
npm run setup -- --no-open https://coolify.example.com
npm run setup -- --save https://coolify.example.com
npm run check
npm run inspect:openapi
```

The MCP server and setup helper are dependency-free and use only Node.js built-ins. The server is written in plain JavaScript so the plugin can run directly without a TypeScript build step.

## Sources

- Coolify authorization docs: <https://coolify.io/docs/api-reference/authorization>
- Coolify OpenAPI source: <https://github.com/coollabsio/coolify/blob/v4.x/openapi.json>
- Coolify CLI automation reference: <https://github.com/coollabsio/coolify-cli>

## License

MIT
