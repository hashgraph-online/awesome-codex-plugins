<div align="center">

# Codex rg Guard

**Low-context `rg` / `grep` replacement for Codex that reduces search noise and context waste.**

Use a budgeted MCP search tool before broad repository searches flood the model
with raw matches, repeated snippets, or truncated shell output.

</div>

<br/>
<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/Docs-README-FFD700?style=for-the-badge" alt="Documentation"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
  <a href="https://github.com/Rycen7822/codex-rg-guard/releases"><img src="https://img.shields.io/badge/Download-Releases-FF6600?style=for-the-badge" alt="Releases"></a>
  <a href=".mcp.json"><img src="https://img.shields.io/badge/MCP-single%20tool-2ea44f?style=for-the-badge" alt="MCP: single tool"></a>
  <a href="rust-version/README.md"><img src="https://img.shields.io/badge/Runtime-Python%20%7C%20Rust-5865F2?style=for-the-badge" alt="Runtime: Python and Rust"></a>
</p>

> This project is intended for large or many-file projects where raw `rg` /
> `grep` can waste Codex context. For known files, tiny repositories, or narrow
> local checks, normal file reads and direct shell tools are usually simpler.

## Why

Raw search is great for humans, but it is often wasteful for coding agents:

- too many matches enter the conversation at once;
- long lines and repeated hits pollute context;
- shell output can be truncated before Codex sees the useful part;
- broad searches usually need file narrowing before line-level inspection.

Codex rg Guard keeps `ripgrep` as the underlying search engine, but wraps it in
a small budgeted interface designed for staged agent workflows.

## Features

- **Single MCP tool**: Codex sees only `cxs(op,args)`, keeping tool-list context small.
- **Files-first search**: `find(files_only:true)` identifies candidate files without snippets.
- **Bounded line hits**: line snippets are capped by total hits, per-file hits, line length, total output, process bytes, and timeout.
- **Pagination hints**: truncated files-only results expose `next_page.offset`.
- **Structured data search**: `json` searches JSON, JSONL, NDJSON, CSV, and TSV with field projection.
- **Symbol lookup**: lightweight regex-based `symbol` search for common language definitions.
- **Optional `rg` shim**: common `rg -n` calls can be intercepted and returned as compact JSON.
- **Two runtimes**: Python implementation for simple hacking, Rust implementation for faster native distribution.

## Install

| Variant | Best for | Runtime requirements |
| --- | --- | --- |
| Rust prebuilt package | Normal use and distribution | `rg` |
| Python version | Editing or debugging the original implementation | Python 3.10+, `rg` |
| Rust from source | Development and platform-specific builds | Rust toolchain, `rg` |

### Agent Self-Install Prompts

Copy the matching prompt into a Codex agent when you want it to install the
plugin for itself.

Rust prebuilt package, recommended for normal use:

```text
Install Codex rg Guard for yourself globally from repo `https://github.com/Rycen7822/codex-rg-guard`. Use the Rust prebuilt asset `https://github.com/Rycen7822/codex-rg-guard/releases/download/v0.2.4/codex-rg-guard-rust-0.2.4-x86_64-unknown-linux-gnu.tar.gz`, install it under `~/.codex/plugins/codex-rg-guard`, enable `codex-rg-guard@local-personal`, register MCP `cxs-rg-guard` to `~/.codex/plugins/codex-rg-guard/bin/cxs-mcp-server`, and verify with `cxs --help`, `codex mcp list`, and MCP `self_check`.
```

Python version, for editing or debugging the original implementation:

```text
Install the Python/source version of Codex rg Guard for yourself from repo `https://github.com/Rycen7822/codex-rg-guard`, not the Rust prebuilt package. Put the source tree under `~/.codex/plugins/codex-rg-guard`, register MCP `cxs-rg-guard` with `python3 ~/.codex/plugins/codex-rg-guard/mcp/cxs_mcp_server.py`, and verify the Python CLI/MCP path.
```

Rust from source, for platform-specific builds:

```text
Build Codex rg Guard from source for your platform by cloning `https://github.com/Rycen7822/codex-rg-guard`, then running `cd rust-version && cargo build --release --bins`. Package/install it with `rust-version/scripts/package-plugin.sh`, register the installed Rust MCP binary, and verify.
```

### Rust Prebuilt Package

Build the distributable package on the target platform or in CI:

```bash
bash rust-version/scripts/package-plugin.sh
```

The archive is written to:

```text
rust-version/dist/codex-rg-guard-rust-<version>-<target>.tar.gz
```

Install on the target machine:

```bash
tar -xzf codex-rg-guard-rust-<version>-<target>.tar.gz
./codex-rg-guard-rust-<version>-<target>/install-local.sh
```

Restart Codex, then enable **Codex rg Guard**.

Fallback direct MCP registration:

```bash
codex mcp add cxs-rg-guard -- ~/.codex/plugins/codex-rg-guard/bin/cxs-mcp-server
```

Optional shell tools:

```bash
export PATH="$HOME/.codex/plugins/codex-rg-guard/bin:$PATH"
```

### Python Version

Use this path when you want the original Python implementation or want to edit
the Python code directly.

```bash
unzip codex-rg-guard.zip
cd codex-rg-guard
./scripts/install-local.sh
```

Fallback direct MCP registration:

```bash
codex mcp add cxs-rg-guard -- python3 ~/.codex/plugins/codex-rg-guard/mcp/cxs_mcp_server.py
```

### Rust From Source

```bash
cd rust-version
cargo build --release --bins
cargo test
cargo clippy --all-targets --all-features -- -D warnings
```

From the repository root, build a package for a specific installed Rust target:

```bash
TARGET=x86_64-unknown-linux-musl bash rust-version/scripts/package-plugin.sh
```

## How It Works

Use broad search as a staged workflow instead of dumping raw matches:

1. Ask for matching files only.
2. Search only inside the candidate files for bounded line hits.
3. Read exact files or small spans with Codex-native file tools after a concrete file and line are known.
4. If a files-only result is truncated, repeat with `next_page.offset`.

Example first stage:

```json
{"op":"find","args":{"query":"ExactIdentifier","scopes":["docs","src"],"files_only":true}}
```

Example second stage:

```json
{"op":"find","args":{"query":"ExactIdentifier","paths":["src/example.py"],"max_total_hits":20}}
```

## MCP Operations

| Operation | Purpose |
| --- | --- |
| `find` | Content search with budgeted snippets or files-only output |
| `files` | File/path search without reading file contents |
| `symbol` | Lightweight definition lookup |
| `json` | Bounded structured-data search |
| `self_check` | Runtime and dependency check |

Codex sees one MCP tool:

```json
{"op":"find","args":{"query":"ExactIdentifier","scopes":["docs","analysis"]}}
```

## CLI

```bash
bin/cxs self-check
bin/cxs find "ExactIdentifier" --scope docs --scope analysis
bin/cxs find "ExactIdentifier" --files-only --scope docs --scope src
bin/cxs find "ExactIdentifier" --files-only --scope docs --scope src --offset 30
bin/cxs symbol train_loop
bin/cxs json --filter doc_id=doc-123 --field doc_id --field token_count --scope analysis
```

All outputs are compact JSON by default. Add `--pretty` for manual inspection.

## Optional rg Shim

```bash
export PATH="$HOME/.codex/plugins/codex-rg-guard/bin:$PATH"
```

Common `rg -n` calls return compact, budgeted JSON. Escape hatch:

```bash
CXS_RAW_RG=1 rg -n "pattern" .
```

## Project Layout

| Path | Description |
| --- | --- |
| `.mcp.json` | Python MCP registration used by the source plugin |
| `mcp/cxs_mcp_server.py` | Python MCP server |
| `cxs/` | Python core, CLI, and MCP implementation |
| `rust-version/` | Rust implementation, tests, and packaging scripts |
| `skills/rg-budget-search/SKILL.md` | Short Codex routing rule |
| `bin/` | Python-version CLI and shim entrypoints |

## Development

Python checks:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/self_check.py
```

Rust checks:

```bash
cd rust-version
cargo fmt --check
cargo test
cargo clippy --all-targets --all-features -- -D warnings
```

Python/Rust semantic compatibility check:

```bash
python3 rust-version/scripts/compare_python.py
```

## Notes

- `read` was intentionally removed; use Codex-native file reads after search narrows to a concrete file or span.
- `ast-grep` is optional and not used by the current implementation.
- Vector search, SQLite, embeddings, `jq`, and `fd` are not required.

## License

MIT
