# Lacuna Music Plugin

Generate original instrumental music and vocal songs from Codex using Lacuna's published Model Context Protocol server.

## Capabilities

- Generate an instrumental from a natural-language style description.
- Turn supplied lyrics into a complete song with vocals.
- Retrieve a generation or wait until its audio URLs are ready.

Music generation spends credits from the authenticated Lacuna account. The MCP server returns a pending task immediately; clients should poll approximately every 10 seconds rather than busy-looping.

## Requirements

- A [Lacuna account](https://www.lacuna.fm/login) on Pro or higher.
- A `LACUNA_API_KEY` created at [Lacuna API settings](https://www.lacuna.fm/profile/api) with the `music:generate` scope.
- Node.js 18 or newer so Codex can launch the pinned `lacuna-mcp@0.3.3` package.

## Install in Codex

```sh
codex plugin marketplace add JOYLINK-LTD/lacuna-plugin
codex plugin add lacuna-music@lacuna
```

Make `LACUNA_API_KEY` available to Codex, restart the app, and test the plugin in a new task.

## Tools

| Tool | Purpose |
| --- | --- |
| `generate_music` | Creates a generation task and returns its pending task ID. |
| `get_generation` | Retrieves the current state of a generation task. |
| `wait_for_generation` | Polls until a task becomes `ready` or `failed`. |

## Repository layout

- `.agents/plugins/marketplace.json` — installable Codex marketplace.
- `.codex-plugin/plugin.json` — plugin manifest.
- `.mcp.json` — pinned stdio MCP connection.

See the [MCP documentation](https://www.lacuna.fm/docs/mcp) and [Lacuna Toolkit](https://github.com/JOYLINK-LTD/lacuna-toolkit) for the SDK, CLI, and standalone MCP package.

## Security

Do not commit or paste a Lacuna API key into this repository. See [SECURITY.md](SECURITY.md) for reporting instructions.

## License

MIT
