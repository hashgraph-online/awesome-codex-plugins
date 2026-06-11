<div align="center">
<h1>llm-transpile</h1> 

<p align="center">
  <a href="https://github.com/epicsagas/llm-transpile/stargazers"><img alt="Stars" src="https://img.shields.io/github/stars/epicsagas/llm-transpile?style=for-the-badge&labelColor=0d1117&color=ffd700&logo=github&logoColor=white" /></a>
  <a href="https://github.com/epicsagas/llm-transpile/network/members"><img alt="Forks" src="https://img.shields.io/github/forks/epicsagas/llm-transpile?style=for-the-badge&labelColor=0d1117&color=2ecc71&logo=github&logoColor=white" /></a>
  <a href="https://github.com/epicsagas/llm-transpile/issues"><img alt="Issues" src="https://img.shields.io/github/issues/epicsagas/llm-transpile?style=for-the-badge&labelColor=0d1117&color=ff6b6b&logo=github&logoColor=white" /></a>
  <a href="https://github.com/epicsagas/llm-transpile/commits/main"><img alt="Last commit" src="https://img.shields.io/github/last-commit/epicsagas/llm-transpile?style=for-the-badge&labelColor=0d1117&color=58a6ff&logo=git&logoColor=white" /></a>
</p>
<p align="center">
  <a href="https://crates.io/crates/llm-transpile"><img alt="Crates.io" src="https://img.shields.io/crates/v/llm-transpile?style=for-the-badge&labelColor=0d1117&color=fc8d62&logo=rust&logoColor=white" /></a>
  <a href="https://docs.rs/llm-transpile"><img alt="docs.rs" src="https://img.shields.io/docsrs/llm-transpile?style=for-the-badge&labelColor=0d1117&color=8e44ad&logo=docsdotrs&logoColor=white" /></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-Apache--2.0-3fb950?style=for-the-badge&labelColor=0d1117" /></a>
  <a href="https://blog.rust-lang.org/"><img alt="Rust" src="https://img.shields.io/badge/rust-1.92+-d73a49?style=for-the-badge&labelColor=0d1117&logo=rust&logoColor=white" /></a>
  <a href="https://buymeacoffee.com/epicsaga"><img alt="Buy Me a Coffee" src="https://img.shields.io/badge/buy_me_a_coffee-FFDD00?style=for-the-badge&labelColor=0d1117&logo=buymeacoffee&logoColor=black" /></a>
</p>

**Token-optimized document transpiler for LLM pipelines**

[한국어](docs/i18n/README.ko.md) · [日本語](docs/i18n/README.ja.md) · [中文](docs/i18n/README.zh.md) · [Español](docs/i18n/README.es.md) · [Français](docs/i18n/README.fr.md) · [Deutsch](docs/i18n/README.de.md) · [Português](docs/i18n/README.pt.md) · [Русский](docs/i18n/README.ru.md) · [العربية](docs/i18n/README.ar.md) · [हिन्दी](docs/i18n/README.hi.md)

</div>

Raw documents (Markdown, HTML, plain text) → structured bridge format `<D>?<H><B>` — with adaptive compression that keeps you under token budget.

---

<details>
<summary>Table of Contents</summary>

- [Why](#why)
- [Installation](#installation)
- [Updating](#updating)
- [CLI Usage](#cli-usage)
- [Usage Statistics](#usage-statistics)
- [Benchmarking](#benchmarking)
- [Library Usage](#library-usage)
- [Output Format](#output-format)
- [Fidelity Levels](#fidelity-levels)
- [Adaptive Compression](#adaptive-compression)
- [Input Formats](#input-formats)
- [Error Handling](#error-handling)
- [Performance](#performance)
- [Contributing](#contributing)
- [License](#license)

</details>

---

## Why

LLMs perform better when context is clean and dense. This library handles the mechanical work:

| | Feature | Why it matters |
|--|---------|----------------|
| 🏗️ | **Structural parsing** | Markdown/HTML/plain text → typed IR nodes (headings, paragraphs, tables, lists, code blocks) |
| 📉 | **Adaptive compression** | Automatically escalates through 4 stages as token budget fills up |
| 🔣 | **Symbol substitution** | Repeated domain terms → Unicode PUA characters, decoded by `<D>` dictionary header |
| 📊 | **Table linearization** | Markdown tables → compact `Key:Val` (≤5 rows) or pipe-separated rows for larger tables |
| 🌊 | **Streaming output** | Tokio stream delivers the first chunk immediately, minimizing TTFT |

### Benchmarks

37 documents, 4 formats, 5 languages — Apple M-series, `--release` build. Full report: [`eval/EVAL_REPORT.md`](eval/EVAL_REPORT.md)

| Format | Semantic reduction | Compressed reduction | Lossless word coverage | Throughput |
|--------|-------------------:|--------------------:|----------------------:|-----------:|
| Markdown (EN) | 29.8% | 42.0% | 99.7% | 895 tok/ms |
| Markdown (ML) | 43.1% | 43.9% | 97.3% | 3,483 tok/ms |
| HTML | 97.7% | 97.7% | 93.0% | 5,879 tok/ms |
| PlainText | 17.7% | 47.7% | 100.0% | 189 tok/ms |
| **Overall** | **79.2%** | **81.1%** | **98.4%** | **2,258 tok/ms** |

> HTML reduction reflects markup overhead removal (nav, scripts, styles), not prose compression alone.

---

## Installation

### Claude Code

```
/plugin marketplace add epicsagas/plugins
/plugin install transpile@epicsagas
```

Auto-installs the binary and seeds the PostToolUse hook on next session start — no additional setup required.

### Codex CLI

```bash
codex plugin marketplace add epicsagas/plugins
```

The PostToolUse hook is registered automatically — no further steps needed.

### macOS / Linux

```bash
brew install epicsagas/tap/llm-transpile
```

No Homebrew? Use the installer script:

```bash
curl --proto '=https' --tlsv1.2 -LsSf \
  https://github.com/epicsagas/llm-transpile/releases/latest/download/install.sh | sh
```

### Windows

```powershell
irm https://github.com/epicsagas/llm-transpile/releases/latest/download/install.ps1 | iex
```

### Via Rust toolchain

```bash
cargo binstall llm-transpile   # pre-built binary (fast)
cargo install llm-transpile    # build from source
```

### After installing

Configure tool integrations:

```bash
transpile install
```

`transpile install` launches an interactive wizard that detects and configures whichever tools are installed:

| Tool | Integration method | What it does |
|------|--------------------|--------------|
| **Antigravity** | `SKILL.md` | LLM auto-invokes `transpile` on document file extensions |
| **Cursor** | `.mdc` rule (`alwaysApply`) | Triggers `transpile` before reading document files |
| **OpenCode** | `SKILL.md` | LLM auto-invokes `transpile` on document file extensions |
| **Cline** | `SKILL.md` | LLM auto-invokes `transpile` on document file extensions |

All tools use a skill file that teaches the LLM to run `TRANSPILE_AGENT=<agent> transpile --input <file>` automatically — no size check needed, extension alone triggers it.

**Selective install / uninstall**

```bash
transpile install antigravity cursor    # specific tools only
transpile install --all                 # everything at once
transpile install --dry-run             # preview what would change
transpile install --list                # show status of all integrations

transpile uninstall cursor         # remove one
transpile uninstall --all          # remove everything
transpile uninstall --dry-run      # preview removals
```

### Library (Rust crate)

```toml
[dependencies]
llm-transpile = "0.1"
```

Requires **Rust 1.92+**.

**Antigravity (Gemini CLI)**

```bash
agy plugins install https://github.com/epicsagas/llm-transpile
```

Auto-installs the plugin (hooks) and registers it on next session start.

---

## Updating

| Method | Command |
|--------|---------|
| Homebrew | `brew upgrade llm-transpile` |
| curl / PowerShell installer | Re-run the install command above |
| cargo binstall | `cargo binstall llm-transpile@latest` |
| cargo install | `cargo install llm-transpile@latest` |

```bash
transpile --version
```

---

## CLI Usage

```
transpile [OPTIONS]

Options:
  -i, --input <FILE>       Input file path (reads from stdin if omitted)
  -f, --format <FORMAT>    Input format: markdown | html | plaintext  [default: markdown]
                           Auto-detected from file extension when --input is used
  -l, --fidelity <LEVEL>   Compression level: lossless | semantic | compressed  [default: semantic]
  -b, --budget <N>         Token budget upper limit (unlimited if omitted)
  -c, --count              Print only the input token count, then exit
  -j, --json               Output as JSON {input_tok, output_tok, reduction_pct, content}
  -q, --quiet              Suppress the stats line on stderr
      --stats              Print stats line to stdout after content (single-stream capture)
  -h, --help               Print help
  -V, --version            Print version
```

**Examples**

```bash
# Convert a Markdown file (format auto-detected from .md extension)
transpile --input doc.md

# Read from stdin — clean stdout, stats on stderr
cat doc.html | transpile --format html --fidelity compressed --budget 1024

# Pipe cleanly — suppress stats entirely
transpile --input doc.md --quiet | send_to_llm_api

# Check token count without converting
transpile --input doc.md --count

# JSON output for scripts and pipelines
transpile --input doc.md --json | jq '.reduction_pct'

# Capture content + stats in one stream (stdout)
transpile --input doc.md --stats > output_with_stats.txt

# Lossless — no compression, full content preserved (legal/audit docs)
transpile --input contract.md --fidelity lossless

# Aggressive compression into a 512-token budget
transpile --input article.md --fidelity compressed --budget 512
```

> Stats (`[273 → 150 tok  45.1% reduction]`) are written to **stderr** by default, so stdout stays clean for piping. Use `--quiet` to suppress, or `--stats` to redirect to stdout.

---

## Usage Statistics

Every `transpile` invocation automatically appends a record to `~/.agents/transpile/stats/YYYY-MM-DD.jsonl`.

### ASCII table

```bash
transpile stats show                # today
transpile stats show --days 7       # last N days
transpile stats show --agent claude # filter by agent
```

Example output:

```
transpile stats — last 7 days

  Date          Agent         Calls   Input tok  Output tok    Saved  Reduction
  ──────────────────────────────────────────────────────────────────────────
  2026-05-18                    238   4 999 355   4 248 769  750 586      15.0%
  2026-05-19                    390   1 577 739   1 463 504  114 235       7.2%
  2026-05-20                    288   2 148 207   1 836 916  311 291      14.5%
  2026-05-21                     99     635 313     544 709   90 604      14.3%
  2026-05-22                    299   8 328 530   7 732 860  595 670       7.2%
  2026-05-23                    418  15 939 148  13 501 134  2 438 014      15.3%
  2026-05-24                    186   3 313 950   2 782 467  531 483      16.0%
  ──────────────────────────────────────────────────────────────────────────
  Total                        1919  36 942 242  32 110 359  4 831 883      13.1%
```

### HTML dashboard

```bash
transpile stats report                 # opens in browser (default: last 7 days)
transpile stats report --days 30       # last 30 days
transpile stats report --no-open       # generate without opening
transpile stats report --out /tmp/custom.html
```

> Reports are generated at `~/.agents/transpile/reports/` by default. Override with `--out`.

**JSONL record fields**

| Field | Type | Description |
|-------|------|-------------|
| `ts` | ISO 8601 | Timestamp of the invocation |
| `agent` | string | Tool that triggered the call (`claude`, `antigravity`, `codex`, `opencode`) |
| `file` | string | Input file path (empty when reading from stdin) |
| `format` | string | `markdown`, `html`, or `plaintext` |
| `fidelity` | string | `lossless`, `semantic`, or `compressed` |
| `input_tok` | integer | Token count before transpilation |
| `output_tok` | integer | Token count after transpilation |
| `reduction_pct` | float | Percentage of tokens saved |
| `saved` | integer | Absolute tokens saved (`input_tok − output_tok`) |

**`TRANSPILE_AGENT` environment variable**

The `agent` field is populated from the `TRANSPILE_AGENT` environment variable. Each integration sets this automatically (`claude`, `antigravity`, `codex`, `opencode`, `cursor`). You can also set it manually:

```bash
TRANSPILE_AGENT=claude transpile --input doc.md
```

### Benchmarking

```bash
# Run benchmarks against a directory of test files
transpile bench run --dataset ./eval                    # generates JSONL log
transpile bench run --dataset ./eval --report           # run + open HTML report
transpile bench report                                 # regenerate report from logs
```

The HTML benchmark report includes:

- **KPI cards** — semantic reduction, compressed reduction, throughput (tok/ms), word coverage, total input tokens, run count
- **7 charts** — reduction trend over time, throughput per run, semantic vs throughput scatter, box plot per format, format distribution, token size histogram, word coverage donut
- **Runs table** — per-run summary with aggregate metrics
- **Records table** — per-file detail with filter by format, run, and filename
- **Theme toggle** — dark / light mode with persistent preference
- **Bilingual** — auto-detects Korean locale; manual 한/EN toggle

---

## Library Usage

### Synchronous

```rust
use llm_transpiler::{transpile, FidelityLevel, InputFormat};

let md = r#"
# Software License Agreement

This agreement is made between Licensor and Licensee.

| Item     | Cost  |
|----------|-------|
| Base fee | $800  |
| Support  | $200  |
"#;

let output = transpile(md, InputFormat::Markdown, FidelityLevel::Semantic, Some(4096))?;
println!("{}", output);
```

### Streaming (Tokio)

```rust
use llm_transpiler::{transpile_stream, FidelityLevel, InputFormat};
use futures::StreamExt;

let mut stream = transpile_stream(input, InputFormat::Markdown, FidelityLevel::Semantic, 4096).await;

while let Some(chunk) = stream.next().await {
    let chunk = chunk?;
    print!("{}", chunk.content);
    if chunk.is_final { break; }
}
```

### Token count estimate

```rust
let n = llm_transpiler::token_count("Hello, world!");
```

---

## Output Format

```
<D>                  ← Symbol dictionary (omitted when no substitutions occur)
{sym}=repeated-term
</D>
<H>                  ← YAML-like metadata header
t: document title
s: one-line summary
k: [keyword1, keyword2]
</H>
<B>                  ← Document body (compressed + substituted)
...content...
</B>
```

The `<D>` block uses Unicode Private Use Area characters (`U+E000–U+F8FF`) as compact symbol handles, avoiding collision with visible text patterns. The dictionary supports up to **6,400 unique terms** per document.

---

## Fidelity Levels

| Level | Typical use case | Compression applied |
|-------|-----------------|---------------------|
| `Lossless` | Legal / audit documents | None — original content guaranteed |
| `Semantic` | General RAG pipelines | Stopword removal + low-importance pruning |
| `Compressed` | Summarization, tight budgets | Maximum compression, first-sentence extraction |

---

## Adaptive Compression

The compressor monitors budget usage in real time and escalates automatically:

| Budget usage | Stage | What happens |
|---|---|---|
| 0–60% | `StopwordOnly` | English/Korean stopwords stripped |
| 60–80% | `PruneLowImportance` | Bottom 20% of paragraphs by importance score removed |
| 80–95% | `DeduplicateAndLinearize` | Duplicate sentences removed; tables linearized |
| 95%+ | `MaxCompression` | Each paragraph truncated to first sentence |

> `Lossless` mode bypasses all compression stages unconditionally.

During streaming, when budget usage crosses 80%, remaining nodes are automatically switched to `Compressed` mode.

---

## Input Formats

| `InputFormat` | Parser |
|---|---|
| `Markdown` | [pulldown-cmark](https://crates.io/crates/pulldown-cmark) — CommonMark + GFM tables |
| `Html` | ammonia sanitization → tag stripping → plain text pipeline |
| `PlainText` | Blank-line paragraph splitting |

---

## Error Handling

```rust
use llm_transpiler::TranspileError;

match transpile(input, format, fidelity, budget) {
    Ok(output) => { /* use output */ }
    Err(TranspileError::Parse(msg))          => eprintln!("parse failed: {msg}"),
    Err(TranspileError::SymbolOverflow(e))   => eprintln!("too many unique terms: {e}"),
    Err(TranspileError::LosslessModeViolation) => eprintln!("compression in lossless mode"),
    Err(e)                                   => eprintln!("error: {e}"),
}
```

---

## Performance

Measured on release build (`cargo build --release`), Apple M-series, 48 documents across Markdown / HTML / PlainText:

| Metric | Measured | Notes |
|--------|----------|-------|
| Throughput | **10,975 tok/ms** | ≈75× faster than Python parsing baseline |
| Semantic reduction | **33.9%** (Markdown) | 15–30% target met |
| Compressed reduction | **39.7%** (Markdown) | Budget-adaptive, guaranteed ≥ PruneLowImportance |
| Lossless word coverage | **98.8% avg** | Across all formats and languages |
| HTML reduction | **97.6%** | Reflects markup overhead removal (nav/scripts/styles) |
| Multilingual support | 15 languages tested | AR/DE/ES/FR/HI/IT/JA/KO/NL/PL/PT/RU/SV/TR/ZH — 99.4% avg word coverage |

Run the evaluation suite yourself:

```bash
cargo run --release --example eval
```

Full per-file breakdown, methodology, and known limitations: [`eval/EVAL_REPORT.md`](eval/EVAL_REPORT.md)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines. PRs welcome — check open issues labeled `good first issue`.

---

## License

Apache-2.0 — see [LICENSE](LICENSE).
