# @darkmoon_ai/mcp-server

A [Model Context Protocol](https://modelcontextprotocol.io) server that lets an MCP client (Claude Desktop, Goose, Continue, LibreChat, ...) drive [Darkmoon](https://github.com/ASCIT31/Dark-Moon), an open source (GPL-3.0) autonomous AI penetration testing platform.

## Requires Darkmoon Pro

The Darkmoon engine and CLI are open source. This server talks to the **Darkmoon Dashboard API**, which is part of **Darkmoon Pro** and always self-hosted: there is no public hosted endpoint, so you supply the base URL of your own instance. It does not work against the open source CLI alone.

## Tools

| Tool | Description |
|---|---|
| `run_pentest` | Start an autonomous pentest against one authorized target and return the `run_id` |
| `get_run_status` | Report `running`, `completed`, `error` or `unknown` for a run, from its run log |
| `list_campaigns` | List campaigns visible to the dashboard user (read only) |
| `get_findings` | Vulnerabilities and severity statistics for a campaign (read only) |

Only run assessments against systems you own or are explicitly authorized in writing to test. Findings can include false positives and must be reviewed by a qualified human.

## Configuration

| Variable | Description |
|---|---|
| `DARKMOON_BASE_URL` | Base URL of your Darkmoon Pro Dashboard API (required) |
| `DARKMOON_USERNAME`, `DARKMOON_PASSWORD` | Dashboard credentials; a JWT is requested on each call and never cached |
| `DARKMOON_TOKEN` | Alternative to username/password: a pre-issued JWT |
| `DARKMOON_TIMEOUT_MS` | Optional per-request timeout, default 60000 |

## Client configuration

Claude Desktop (`claude_desktop_config.json`), Continue and LibreChat use the same `mcpServers` shape:

```json
{
  "mcpServers": {
    "darkmoon": {
      "command": "npx",
      "args": ["-y", "@darkmoon_ai/mcp-server"],
      "env": {
        "DARKMOON_BASE_URL": "https://darkmoon.example.internal",
        "DARKMOON_USERNAME": "your-dashboard-user",
        "DARKMOON_PASSWORD": "your-dashboard-password"
      }
    }
  }
}
```

Goose (`~/.config/goose/config.yaml`):

```yaml
extensions:
  darkmoon:
    type: stdio
    enabled: true
    name: darkmoon
    cmd: npx
    args: ["-y", "@darkmoon_ai/mcp-server"]
    envs:
      DARKMOON_BASE_URL: https://darkmoon.example.internal
      DARKMOON_USERNAME: your-dashboard-user
      DARKMOON_PASSWORD: your-dashboard-password
```

Continue (`.continue/mcpServers/darkmoon.yaml`):

```yaml
name: Darkmoon
version: 0.1.0
schema: v1
mcpServers:
  - name: darkmoon
    command: npx
    args: ["-y", "@darkmoon_ai/mcp-server"]
    env:
      DARKMOON_BASE_URL: https://darkmoon.example.internal
      DARKMOON_USERNAME: your-dashboard-user
      DARKMOON_PASSWORD: your-dashboard-password
```

## Develop

```bash
npm install
npm run build
npm test      # mocked Dashboard API, in-memory MCP client and a real stdio process
```

## License

GPL-3.0-only, same as Darkmoon.
