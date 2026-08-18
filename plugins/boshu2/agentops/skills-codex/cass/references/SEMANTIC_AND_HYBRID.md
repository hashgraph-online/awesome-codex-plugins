# Semantic & Hybrid Search

> **One-liner:** Lexical (BM25) is the default and is sufficient for >90% of agent queries. Enable semantic only when you don't know the exact wording.

## Contents

- [Decision Tree](#decision-tree)
- [Models — Three States](#models--three-states)
- [Building & Refreshing the Vector Index](#building--refreshing-the-vector-index)
- [Querying](#querying)
- [Background Backfill](#background-backfill)
- [Pitfalls](#pitfalls)

---

## Decision Tree

```
Need to find something?
│
├─ I know exact words / file names / IDs    → --mode lexical (default; do nothing)
├─ I want "things conceptually like X"       → --mode semantic   (needs MiniLM)
├─ Mix of both / not sure                    → --mode hybrid     (RRF combines results)
```

cass uses Reciprocal Rank Fusion for hybrid: `score = Σ 1 / (60 + rank_i)`. Top-of-list lexical hits stay near the top, but conceptually similar items the lexical index missed get surfaced.

---

## Models — Three States

```bash
cass models status --json | jq '{state, installed_size_bytes, total_size_bytes}'
```

| State | Meaning | Action |
|-------|---------|--------|
| `not_installed` | No model files; semantic falls back to **hash embedder** (lexical-overlap only) | `cass models install` to enable real semantic |
| `partial` | Some files present, others missing | `cass models verify` then re-install missing |
| `installed` | All files present and SHA256 verified | Use freely |

The hash embedder is **deterministic and instant** but only matches token overlap — it doesn't know "car ≈ automobile". For real semantic understanding you need the MiniLM bundle (~90MB).

### Install / Verify / Remove

```bash
cass models install                    # downloads from HuggingFace (default model)
cass models install --mirror <URL>     # use a different mirror (HF flaky on Windows / corp networks)
cass models install --from-file <DIR>  # air-gapped: install from a pre-downloaded model dir
cass models verify                     # SHA256 check, no network
cass models remove -y                  # frees ~90MB; semantic falls back to hash
cass models check-update               # see if a newer model rev exists
```

If `cass models install` fails on Windows with WSAENOTCONN (closed issue #193), retry once. If still failing, use `--mirror` to switch endpoints or `--from-file` with a model dir you copied from a working host. The required files are listed in the README's Semantic Search section.

---

## Building & Refreshing the Vector Index

```bash
# After install, build the FSVI vector index
cass index --semantic --json

# Add HNSW for O(log n) approximate search (recommended for >10k sessions)
cass index --semantic --build-hnsw --json

# Subsequent runs are incremental
cass index --semantic --json     # only new conversations get embedded
```

The vector index lives at `~/.local/share/coding-agent-search/vector_index/index-minilm-384.fsvi`. It's memory-mapped — opening a 1GB index doesn't read 1GB into RAM.

---

## Querying

```bash
# Lexical (default; fastest)
cass search "tantivy index" --mode lexical --json

# Semantic (requires --semantic-built index OR falls back to hash)
cass search "ways to make search faster" --mode semantic --json

# Hybrid (best for "I'll know it when I see it")
cass search "stuck index recovery" --mode hybrid --json

# Approximate semantic via HNSW (10–100x faster on big corpora)
cass search "QUERY" --mode semantic --approximate --json
```

If `--mode semantic` is used but no model is installed and `CASS_SEMANTIC_EMBEDDER=hash` is unset, cass **silently degrades to lexical** — the response includes `_meta.fallback_mode: "lexical"`. Always check that field before claiming semantic worked.

---

## Background Backfill

For very large corpora, semantic embedding can take minutes. cass schedules **low-impact background backfill** that respects idle/load budgets:

```bash
# Status of backfill (in-progress, completed, idle)
cass status --json | jq '.semantic'

# Force foreground build (skip backfill scheduler)
cass index --semantic --json
```

When `semantic.progressive_ready=true` but `hnsw_ready=false`, you can still query with `--mode semantic`; it'll do a brute-force vector scan (slower but correct).

---

## Pitfalls

- **Always check fallback mode.** A query that *looks* semantic may have run lexically:
  ```bash
  cass search "X" --mode hybrid --robot-meta --json | jq '._meta.fallback_mode // "ok"'
  ```
- **Hash embedder ≠ semantic.** It's deterministic and lexical-overlap only. Useful for env-pinning tests; not a substitute for MiniLM.
- **Vector index is per-embedder.** Switching embedders requires a rebuild: `cass index --semantic --embedder fastembed --json`.
- **Disk pressure**: the FSVI index can grow to ~1.5x the source SQLite size. If `df -h ~/.local/share` is tight, semantic backfill silently pauses.
- **Daemon mode (Unix only)**: `cass daemon` runs the model in-memory across queries to avoid 500ms model-load cost per call. Worth it if you're running >50 semantic queries/min.
