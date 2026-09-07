<p align="center">
  <img src="assets/readme-hero.png" alt="Read only what you need" width="100%" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/MCP-compatible-57a8ff" alt="MCP compatible" />
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-55e2cc" alt="Apache 2.0 license" /></a>
  <img src="https://img.shields.io/badge/node-%E2%89%A518-3c873a" alt="Node.js 18 or later" />
  <a href="https://github.com/hashgraph-online/hol-guard"><img src="https://img.shields.io/badge/HOL%20Guard-passing-00a67e" alt="HOL Guard Scanner" /></a>
</p>

<p align="center"><strong>Intelligent Markdown reading for MCP clients.</strong></p>

**mcp-md-reader** helps AI agents navigate large Markdown files and vaults without paying the context cost of reading everything. It returns a compact structure first, then only the precise section, metadata, or graph information the agent needs.

## Used in SkillNet

[SkillNet](https://github.com/ANFAIA/SkillNet) uses mcp-md-reader in its post-Markdown research:
agents can inspect the structure of company documentation and retrieve only the sections needed
for course generation. The reader remains a standalone MCP server; SkillNet is a consumer and
validation context, not a required runtime dependency.

| Smaller context | Deterministic retrieval | Vault-aware |
| :--- | :--- | :--- |
| Read the relevant section instead of a whole 3,000-token document. | Fuzzy structural matching—no embeddings and no LLM calls. | Search, index, and traverse relationships across a Markdown vault. |

> Start with `md_find` for a vault-wide question, then open the selected result with `md_section`.

## Why it matters

A 3,000-token file with 12 sections may only contain one relevant 300-token answer. Without a structural reader, an agent reads all 3,000 tokens. With this server, it can inspect a compact tree first and retrieve only the needed section. The exact reduction depends on the document and selected section.

```text
large Markdown file
        │
        ├── md_find / md_tree  → identify the relevant destination
        ├── md_section         → retrieve only that section
        └── md_vault_index     → explore connections across the vault
```

## MCP tools

| Tool | What it does | Typical saving |
| :--- | :--- | :---: |
| `md_find` | Finds relevant sections across a vault and ranks them. | — |
| `md_tree` | Returns a heading tree with token estimates. | ~93% |
| `md_section` | Retrieves a fuzzy-matched section. | ~88–99% |
| `md_frontmatter` | Returns YAML frontmatter only. | ~99% |
| `md_vault_index` | Queries the compiled graph of the entire vault. | — |

## Setup

```bash
git clone https://github.com/JoseEstevez520/mcp-md-reader.git
cd mcp-md-reader
npm install
npm run build
```

Register it with an MCP client such as Claude Code:

```bash
claude mcp add md-reader -- node /full/path/to/mcp-md-reader/dist/index.js
```

Restart the client and the five tools will be available natively.

### Codex plugin

The repository also contains a Codex plugin manifest and a bundled MCP executable. The bundle is
generated from `src/index.ts`, contains its runtime dependencies, and is smoke-tested against the
five exposed tools:

```bash
npm run bundle:plugin
npm test
```

The plugin entry point is `.codex-plugin/plugin.json`; its bundled server configuration is in
`.mcp.json`.

## Example

```text
> md_tree("notes/project.md")

File: notes/project.md
Full file: ~2428 tokens
This tree: ~84 tokens
Savings: ~97%
# Project
  ## Objective
  ## Current state
  ## Decisions

> md_section("notes/project.md", "Decisions")

Section: Decisions
Section tokens: ~297 | Full file: ~2428 | Savings: ~88%
```

## Search a vault with `md_find`

`md_find` is the front door for broad questions. It searches a compiled index using deterministic title, tag, filename, substring, shared-prefix, acronym, and CamelCase matching. The result contains only matching document regions—not the full vault—and tells the client which section to open next.

```text
> md_find({vault_path: "/path/to/vault", query: "row level security multi-tenant"})

Found 2 matching document(s).
Read a section → md_section(path, heading)
/path/to/vault/base_de_datos/postgres.md
  · Postgres › Row Level Security
```

## Explore relationships with `md_vault_index`

The vault index compiles Markdown files into a graph and refreshes when stale. Query stats, a node, neighbors, a shortest path, nodes by type, the most connected hubs, or isolated notes.

| Query | Purpose |
| :--- | :--- |
| `stats` | Total nodes, edges, and types. |
| `node` / `neighbors` | Inspect a note and its local graph. |
| `path` | Find the shortest connection between two notes. |
| `search_type` | List notes of a frontmatter type. |
| `most_connected` / `isolated` | Find hubs and orphaned notes. |

## Under the hood

- TypeScript + Node.js with the MCP SDK over stdio.
- Pure, code-block-aware string parsing—no external parser dependency.
- LRU memory cache plus persistent disk cache with mtime validation.
- Fuzzy heading matching for exact, prefix, word-boundary, acronym, and CamelCase queries.
- Vault graph traversal with automatic recompilation when the index is stale.

## Security and filesystem scope

The server runs locally with the filesystem permissions of the account that starts it. Tool calls
accept file and vault paths, so a trusted MCP client can request any Markdown file readable by that
account. Use a dedicated operating system account or equivalent filesystem controls when a stricter
boundary is required. Parsed documents may be cached in the operating system temporary directory.
See [SECURITY.md](SECURITY.md) for reporting and cache details.

## Reproducible tests and benchmark

```bash
npm ci
npm test
npm run benchmark
```

The default benchmark uses only the public corpus in `test/fixtures`. To measure another corpus,
set `MD_READER_BENCHMARK_DIR` to its directory before running the command. Token counts use
`ceil(characters / 4)`, not a model tokenizer, and every reported saving applies only to the corpus
that was measured.

For release history and benchmark details, see [CHANGELOG.md](CHANGELOG.md).

## License

[Apache License 2.0](LICENSE)
