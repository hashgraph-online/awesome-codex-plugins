# Setting up ultrafast for an agent

## Install the engine

One binary, `ultrafast`, with `uf` as its short name:

```bash
cargo install ultrafast                    # from crates.io
brew install ultrafastmov/tap/ultrafast    # macOS, prebuilt
docker run --gpus all ghcr.io/ultrafastmov/ultrafast:latest info
```

It renders with Metal on macOS (Apple silicon) and Vulkan on Linux and
Windows (WSL2). `uf info` names the GPU it found. H.264 and HEVC exports
encode on the GPU (Metal, or NVENC on NVIDIA); everything else (ProRes,
AV1, VP9, GIF, PNG and EXR sequences, sound alone) and exports on other
GPUs go through ffmpeg, so install it (`brew install ffmpeg`,
`apt install ffmpeg`).

## Connect a local agent (stdio)

`uf mcp` serves the tools over stdio. Renders run on this machine's GPU and
documents are files on it.

Claude Code:

```bash
claude mcp add ultrafast -- uf mcp
```

Codex:

```bash
codex mcp add ultrafast -- uf mcp
```

Antigravity CLI:

```bash
agy mcp add ultrafast uf mcp
```

Gemini CLI (`--scope user` adds it for every project). Since June 2026
Gemini CLI takes only paid Gemini API keys, Vertex AI and Code Assist
Standard or Enterprise; personal Google accounts use Antigravity CLI:

```bash
gemini mcp add --scope user ultrafast uf mcp
```

Cursor (`.cursor/mcp.json` or `~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "ultrafast": { "command": "uf", "args": ["mcp"] }
  }
}
```

Claude Desktop (`claude_desktop_config.json`: on macOS in
`~/Library/Application Support/Claude/`, on Windows in `%APPDATA%\Claude\`,
on Linux in `~/.config/Claude/`): the same `mcpServers` block. Desktop apps
don't see your shell's `PATH`, so give the full path from `which uf`, e.g.
`"command": "/opt/homebrew/bin/uf"`.

Exports of long films can take longer than a client's default tool timeout.
Raise it if exports time out: in Codex, add `tool_timeout_sec = 300` to the
`[mcp_servers.ultrafast]` table that `codex mcp add` wrote to its
`config.toml`; in Claude Code, set `MCP_TOOL_TIMEOUT` (milliseconds).

## Connect to a server (Streamable HTTP)

A self-hosted server (`ultrafast serve`, or the Docker image) answers MCP at
`/mcp`, e.g. `https://video.example.com/mcp`. Clients send its API key as a
bearer token.

Claude Code:

```bash
claude mcp add --transport http ultrafast https://video.example.com/mcp \
  --header "Authorization: Bearer $ULTRAFAST_API_KEY"
```

Codex:

```bash
codex mcp add ultrafast --url https://video.example.com/mcp \
  --bearer-token-env-var ULTRAFAST_API_KEY
```

Antigravity CLI (it sends the header as written and doesn't expand
variables, so the double quotes put the key itself in
`~/.gemini/config/mcp_config.json`):

```bash
agy mcp add --header "Authorization: Bearer $ULTRAFAST_API_KEY" ultrafast \
  https://video.example.com/mcp
```

Gemini CLI (single quotes keep `$ULTRAFAST_API_KEY` as a reference that
Gemini CLI reads from the environment when it connects):

```bash
gemini mcp add --scope user --transport http ultrafast \
  https://video.example.com/mcp \
  --header 'Authorization: Bearer $ULTRAFAST_API_KEY'
```

Cursor:

```json
{ "mcpServers": { "ultrafast": { "url": "https://video.example.com/mcp",
  "headers": { "Authorization": "Bearer ${env:ULTRAFAST_API_KEY}" } } } }
```

The remote tools take documents inline instead of file paths, and exports
come back as download links.

ultrafast Cloud (`https://mcp.ultrafast.mov`, not open yet) serves the same
tools with OAuth sign-in. That is what Claude's connectors (Settings →
Connectors, on web, desktop and mobile) and the ChatGPT app use.

## Add this skill

```bash
npx skills add ultrafastmov/ultrafast
```

It installs for Claude Code, Codex, Cursor, Gemini CLI and other agents.
Claude Code can also install the ultrafast plugin, which bundles this skill
with the `uf mcp` server:

```bash
claude plugin marketplace add ultrafastmov/ultrafast
claude plugin install ultrafast@ultrafast
```

In Antigravity CLI the repository itself is the plugin, with the same skill
and server:

```bash
agy plugin install https://github.com/ultrafastmov/ultrafast
```
