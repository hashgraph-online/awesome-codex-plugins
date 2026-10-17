---
name: extracting-keywords
description: Use when extracting keywords (YAKE/RAKE) from documents — and, secondarily, when detecting document language or generating embeddings for RAG and search. Covers the keyword config (and its feature gating), `--detect-language`, and the standalone `embed` command with real flags.
---

# Extracting keywords, language, and embeddings

Use this for the enrichment surface around extraction: statistical keyword
extraction, language detection, and vector embeddings. Keywords and
language detection ride along with extraction and land on the result;
embeddings are produced by a dedicated `embed` command.

## Keywords (YAKE / RAKE)

Keyword extraction is configured via the `[keywords]` config block (or
inline JSON) — there is no single `--keywords` CLI flag. When enabled,
extracted keywords appear on `result.keywords`. Two algorithms are
available:

- **YAKE** (`"yake"`) — statistical, unsupervised single-document
  extraction. Good general default.
- **RAKE** (`"rake"`) — co-occurrence / phrase-based. Favors multi-word
  key phrases.

> Feature-gated: keyword extraction requires the CLI to be built with the
> `keywords-yake` and/or `keywords-rake` Cargo features (both are in the
> default/`full` build). If the CLI was built without them, the `[keywords]`
> config block is silently ignored — `result.keywords` simply stays empty
> rather than erroring. The `"yake"` algorithm needs `keywords-yake`; `"rake"`
> needs `keywords-rake`.

Enable via inline JSON on the CLI:

```bash
kreuzberg extract paper.pdf --format json \
  --config-json '{"keywords":{"algorithm":"yake","max_keywords":15,"language":"en"}}' \
  | jq '.keywords'
```

Or in a config file:

```toml
[keywords]
algorithm = "rake"       # "yake" or "rake"
max_keywords = 10        # default 10
min_score = 0.0          # filter below this score (ranges differ per algorithm)
ngram_range = [1, 3]     # unigrams..trigrams (default)
language = "en"          # stopword language; omit to skip stopword filtering
```

```bash
kreuzberg extract report.pdf --config kreuzberg.toml --format json | jq '.keywords'
```

Field notes:

- `max_keywords` caps how many keywords are returned (default 10).
- `min_score` filters low-scoring keywords; note YAKE scores are
  *lower-is-better* while RAKE scores are *higher-is-better*, so a single
  threshold behaves differently per algorithm.
- `ngram_range` is `[min, max]`: `[1,1]` unigrams only, `[1,2]` adds
  bigrams, `[1,3]` (default) adds trigrams.
- `language` enables stopword filtering for that language; omit it to
  disable stopword filtering entirely.

## Language detection

Language detection is a real CLI flag: `--detect-language`. Detected
languages appear on `result.detected_languages`:

```bash
kreuzberg extract multilingual.pdf --detect-language true --format json \
  | jq '.detected_languages'
```

In a config file it lives under `[language_detection]`:

```toml
[language_detection]
enabled = true
min_confidence = 0.8
detect_multiple = false
```

The CLI flag enables detection with `min_confidence = 0.8` and
single-language mode; use the config block to detect multiple languages or
tune confidence.

## Embeddings (`embed` command)

The standalone `embed` command produces vector embeddings for text from
`--text` (repeatable) or stdin. It does not run extraction — pipe
extracted content in if you want document embeddings.

```bash
# Local ONNX preset model (default provider)
kreuzberg embed --text "first passage" --text "second passage" --preset balanced

# Embed extracted document text
kreuzberg extract report.pdf | kreuzberg embed --preset quality
```

Presets for the local provider: `fast`, `balanced` (default), `quality`,
`multilingual`. Output defaults to JSON (`--format json`).

`--provider` selects the embedding source:

| Provider | Flag                                  | Notes                                         |
| -------- | ------------------------------------- | --------------------------------------------- |
| `local`  | `--preset <fast\|balanced\|quality\|multilingual>` | **Default.** ONNX model, no API key. |
| `llm`    | `--model <id>` `--api-key <key>`      | liter-llm routing, e.g. `openai/text-embedding-3-small`. |
| `plugin` | `--plugin <name>`                     | A backend pre-registered in-process via the plugin API. |

```bash
# Provider-hosted embeddings via an LLM
kreuzberg embed --text "query text" \
  --provider llm --model openai/text-embedding-3-small --api-key "$OPENAI_API_KEY"
```

Local embedding presets must be downloaded first if not cached. Pre-warm
them with the cache command:

```bash
kreuzberg cache warm --embedding-model balanced   # one preset
kreuzberg cache warm --all-embeddings             # all four presets
```

## Programmatic access

Keywords and detected languages live on the extraction result:

```python
from kreuzberg import extract_file_sync, ExtractionConfig

result = extract_file_sync(
    "paper.pdf",
    config=ExtractionConfig(),  # configure keywords/language_detection on the config
)
print(result.keywords)             # extracted keywords (when enabled)
print(result.detected_languages)   # detected languages (when enabled)
```

See `references/python-api.md` and `references/configuration.md` in the
sibling `kreuzberg` skill for the keyword / language-detection config
classes and the embedding presets.

## Common pitfalls

- **No `--keywords` flag** — keyword extraction is config-only. Use
  `--config-json '{"keywords":{...}}'` or a `[keywords]` config block.
- **`min_score` direction** — lower is better for YAKE, higher is better
  for RAKE; pick the threshold to match the algorithm.
- **Embeddings ≠ extraction** — `embed` only takes raw text. Pipe
  `kreuzberg extract` output into it for document vectors.
- **Cold embedding models** — first local run downloads the preset; run
  `kreuzberg cache warm --all-embeddings` to pre-populate.

See `references/advanced-features.md` for the embeddings pipeline and
`references/cli-reference.md` for the `embed` and `cache warm` flag sets.
