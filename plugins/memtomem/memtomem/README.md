# memtomem for Codex

Project memory for Codex CLI, backed by the exact-pinned memtomem MCP server:
`$memtomem-handoff` saves a checkpoint when a session ends and loads it back
with `resume`, `$memtomem-brief` compiles the project context and the open
handoff IDs when the next session starts, and `$memtomem-update` turns finished
work and recent commits into durable memories (see
[Project workflows](../../docs/guides/project-workflows.md)). The plugin also
ships skills for search, date-based recall, status, explicit saves, explicit
indexing, and first-time setup.

## Install from this repository

```sh
codex plugin marketplace add /path/to/memtomem
codex plugin add memtomem@memtomem
```

Start a new Codex thread after installation so the skills and MCP server are
loaded. BM25 is the default and requires no embedding provider.

The bundled server includes the ONNX dependencies so existing ONNX/E5 configurations
work without a separate Python installation step. The default remains
`provider=none` (BM25-only); installing the plugin does not enable embeddings.
Model artifacts are fetched only when the configured workflow needs them.

On a completely fresh machine or HOME, initialize the user-owned store once:

```sh
uvx --from 'memtomem[onnx]==0.7.6' mm init --preset minimal --non-interactive --mcp skip
uvx --from 'memtomem[onnx]==0.7.6' mm status
```

`--mcp skip` keeps the bootstrap from adding a second MCP registration because
the plugin already supplies the server.

If `~/.codex/config.toml` already has a hand-written `[mcp_servers.memtomem]`
section, that entry takes precedence and the plugin's bundled server is not
started (name-keyed; measured on codex-cli 0.145.0). Remove the section to use
the plugin's pinned server, and avoid registering memtomem under any other
name — a differently named entry is not deduplicated and both servers would
run. The source-checkout
[coexistence diagnostic and reconciliation](../../docs/guides/mcp-clients.md#keep-manual-mcp-and-plugin-skills)
can check both registrations and preview either choice. `keep-manual` leaves a
canonical `[mcp_servers.memtomem]` entry and the plugin cache unchanged. A
manual entry that keeps serving needs
`env = { MEMTOMEM_EXTRA_TOOLS = "mem_update_coverage" }` (the bundled server
sets it): without it `memtomem-update` stops before writing whenever a coverage
call is due, while `topic` mode still works.

For project-specific memories, keep the terminal in that project and create
the gitignored local tier explicitly:

```sh
cd /path/to/project
uvx --from 'memtomem[onnx]==0.7.6' mm mem init --scope project_local
```

The plugin does not self-authorize these trust steps. After initialization,
use `$memtomem-setup` with an explicit path; it performs a one-shot index
without silently registering a watched source.

Use `$memtomem-handoff` explicitly with `save` or `resume` to exchange a
compact project-local checkpoint with Claude Code or Kimi Code. It does not
capture a conversation or coordinate concurrent workers.

## Docs

- [Claude Code & Codex CLI plugin quickstart](https://github.com/memtomem/memtomem/blob/main/docs/guides/plugin-quickstart.md)
  ([한국어](https://github.com/memtomem/memtomem/blob/main/docs/guides/vibe-coding-getting-started-ko.md))
  — initialize one store, install one plugin, and verify a memory round trip
- [Codex integration guide](https://github.com/memtomem/memtomem/blob/main/docs/guides/integrations/codex.md)
  — complete skill reference and advanced MCP settings
- [Cross-runtime handoff guide](https://github.com/memtomem/memtomem/blob/main/docs/guides/integrations/cross-runtime-handoff.md)
  — one-Mac Claude Code, Codex CLI, and Kimi Code handoff
