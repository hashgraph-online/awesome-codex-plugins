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
# or
cargo install kreuzberg-cli
```

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

The `kreuzberg` MCP server exposes:

- `extract` — single file extraction with config.
- `extract_batch` — batch extraction from multiple files.
- `detect_mime` — MIME type detection from bytes or path.
- `cache_clear` — clear the extraction cache.

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
