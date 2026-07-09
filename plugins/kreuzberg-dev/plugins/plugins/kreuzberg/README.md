# kreuzberg

Extract text, tables, metadata, and images from 91+ document formats — PDF, Office, images with OCR, HTML, email, archives, academic — using the local `kreuzberg` CLI in your agent.

<!-- TODO: screenshot -->

## Install

### From the marketplace (recommended)

Pending review for official Claude marketplace.

Self-host:

```text
/plugin marketplace add kreuzberg-dev/plugins
/plugin install kreuzberg@kreuzberg
```

### Binary requirement

Install the `kreuzberg` CLI:

```bash
brew install kreuzberg-dev/tap/kreuzberg
```

Or run without a persistent install:

```bash
npx @kreuzberg/kreuzberg-cli --help
uvx --from kreuzberg-cli kreuzberg --help
```

Or download a prebuilt binary from the [latest GitHub release](https://github.com/kreuzberg-dev/kreuzberg/releases/latest), or build from source:

```bash
cargo install kreuzberg-cli --features mcp
```

The Python (`kreuzberg`) and Node (`@kreuzberg/node`) packages are language SDKs/bindings, not the CLI. The `kreuzberg` CLI binary includes the MCP server by default.

OCR ships with Tesseract by default. Install language packs for non-English documents:

```bash
brew install tesseract-lang        # macOS
sudo apt install tesseract-ocr-*   # Debian/Ubuntu
```

## Skills shipped

| Skill | Trigger |
|-------|---------|
| **kreuzberg** | Extract text, tables, metadata, and images from 91+ document formats (PDF, Office, images, HTML, email, archives, academic) using Kreuzberg. Use when writing code that calls Kreuzberg APIs in Python, Node.js/TypeScript, Rust, or CLI. Covers installation, extraction (sync/async), configuration (OCR, chunking, output format), batch processing, error handling, and plugins. |
| **extracting-with-ocr** | Use when extracting text from scanned PDFs, photographed pages, or images that have no embedded text layer. Covers OCR backends, language packs, force-OCR, and performance tuning. |
| **extracting-tables** | Use when extracting tabular data from PDFs, spreadsheets, or images. Covers layout-aware table detection, table model selection, output formats (markdown / JSON cells), and known limits. |
| **chunking** | Use when splitting extracted text into chunks for LLM context windows or RAG ingestion. Covers chunk size, overlap, markdown/yaml/semantic chunkers, tokenizer-based sizing, and the standalone `chunk` command. |
| **extracting-keywords** | Use when extracting keywords (YAKE/RAKE), detecting document language, or generating embeddings for RAG and search. Covers the keyword config, `--detect-language`, and the standalone `embed` command. |
| **batch-extraction** | Use when extracting from many files at once with shared config, bounded parallelism, per-file overrides, and error recovery. Covers the `batch` command, `--file-configs`, `--max-concurrent`, and output layout. |
| **picking-a-format** | Use when choosing an output format for extracted documents — text, markdown, djot, html, or JSON. Maps consumer (LLM, parser, archive) to the right `--format` / `--content-format` pair. |

**Reference materials** (linked from the `kreuzberg` skill):

| Reference | Content |
|-----------|---------|
| **CLI Reference** | All commands, flags, config precedence, exit codes |
| **Configuration Reference** | TOML/YAML/JSON formats, auto-discovery, env vars, full schema |
| **Supported Formats** | All 91+ formats with file extensions and MIME types |
| **Python API Reference** | All functions, config classes, plugin protocols, exact signatures |
| **Node.js API Reference** | All functions, TypeScript interfaces, worker pool APIs |
| **Rust API Reference** | All functions with feature gates, structs, Cargo.toml examples |
| **Advanced Features** | Plugins, embeddings, MCP server, API server, security limits |
| **Other Language Bindings** | Go, Ruby, Java, C#, PHP, Elixir, WASM, Docker |

## MCP tools

Run `kreuzberg mcp` to start the MCP server over stdio. The server exposes 13 tools:

**Extraction:** `extract_file`, `extract_bytes`, `batch_extract_files`, `detect_mime_type`, `extract_structured`

**Embeddings:** `embed_text`

**Chunking:** `chunk_text`

**Cache:** `cache_stats`, `cache_clear`, `cache_manifest`, `cache_warm`

**Metadata:** `list_formats`, `get_version`

All extraction tools accept an optional `config` object to override defaults.

## Configuration

Kreuzberg auto-discovers `kreuzberg.toml` from the current directory upward. Set config via:

1. **Environment variable**: `KREUZBERG_CONFIG_JSON='{"output_format":"markdown"}'`
2. **Config file** (TOML): `kreuzberg.toml` in cwd or a parent directory.
3. **CLI flag**: `kreuzberg extract doc.pdf --content-format markdown`

See `skills/kreuzberg/references/configuration.md` for the full schema and precedence rules.

## Examples

Extract a PDF to plain text and print it:

```text
kreuzberg extract document.pdf
```

Extract with markdown formatting for LLM context:

```text
kreuzberg extract report.pdf --content-format markdown
```

Extract tables from a spreadsheet as JSON:

```text
kreuzberg extract data.xlsx --format json
```

## Versioning

The plugin version tracks the marketplace `VERSION` file. See [CHANGELOG.md](../../CHANGELOG.md) for release notes.

## License

MIT. The skill content uses Elastic-2.0 references to the upstream [kreuzberg](https://github.com/kreuzberg-dev/kreuzberg) repository.

## See also

- **Marketplace**: [kreuzberg-dev/plugins](https://github.com/kreuzberg-dev/plugins)
- **Upstream**: [kreuzberg-dev/kreuzberg](https://github.com/kreuzberg-dev/kreuzberg)
- **Sibling plugins**: [kreuzcrawl](../kreuzcrawl/README.md), [kreuzberg-cloud](../kreuzberg-cloud/README.md)
