# Structural graph navigation (graphify) — research Tier 1b recipe

> Optional. Used by `/research` Tier 1b when `graphify` is installed (PyPI `graphifyy`).
> It maps **structure** — what calls/defines/connects to what, across files **and**
> languages — which `grep` cannot see. Reach for it on *what is X / where / what's
> connected / cross-file-link* questions, **before** broad grep. It does **not** read
> in-body logic; for control flow, read the file (Tier 4).

## Why before grep

`grep` finds string matches; it cannot tell you that a shell pre-push hook is wired to
a Go quorum engine, or trace a call chain across packages. graphify's `explain`/`path`
give that structural map directly. The honest failure mode is behavioral: agents default
to grep even when a graph exists — so Tier 1b is an explicit *before-grep* step, not a
"nice to have."

## Refresh first — never query a stale graph

The structural (AST) layer is free and fast — re-extracting ~2,500 code files measured
at **~13s, no LLM**. Always refresh before querying:

```bash
graphify <repo> --update     # incremental: only changed files (seconds)
# first run on a repo: graphify <repo>   (full build; AST is the free part)
```

Only the AST/structural layer is cheap. The doc-semantic layer (LLM-extracted
doctrine↔code bridges) is expensive and slow-changing — **do not** depend on it live;
it is an occasional enrichment, not a research dependency.

## The three commands

```bash
graphify explain "<symbol>"     # what a node IS + everything it connects to (calls/defines).
                                # Clean, precise, no noise. Best for "what is X and what touches it".
graphify path "<A>" "<B>"       # shortest path A→B with the relation on each hop.
                                # Best for "how does A reach B" across files/languages.
graphify query "<tokens>"       # ranked neighborhood around matched nodes (BFS; --dfs to trace).
                                # Locator, not an answerer. REQUIRES the expansion step below.
```

## REQUIRED: query vocab-expansion (or `query` returns noise)

graphify's `query` matcher is **case-folded substring + IDF — no stemming, no synonyms,
no cross-language match**. Feeding it a raw question matches stray words (e.g. "decide",
"main") as substrings and collapses to noise. So before `graphify query`:

1. Extract the graph's actual vocabulary, then pick **only tokens that exist in it** (≤12):
   ```bash
   PY=$(cat graphify-out/.graphify_python)
   $PY -c "
   import json,re; from pathlib import Path
   d=json.loads(Path('graphify-out/graph.json').read_text()); v=set()
   for n in d['nodes']:
       for c in re.findall(r'[^\W\d_]+', n.get('label','') or '', re.UNICODE):
           for p in re.findall(r'[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+', c) or [c]:
               t=p.lower()
               if 3<=len(t)<=30: v.add(t)
   Path('graphify-out/.vocab.txt').write_text('\n'.join(sorted(v)))"
   ```
2. Choose tokens from `graphify-out/.vocab.txt` that match the query intent. **Never invent
   tokens.** Watch polysemy — a token like `merge` may pull in unrelated code; drop it if so.
   If no vocab token matches, say the corpus has no relevant vocabulary and fall through.
3. Run `graphify query "<picked tokens>" [--dfs] [--budget 1500]` and read the ranked nodes.

`explain` and `path` take a node label directly and need **no** expansion — prefer them when
you already know the symbol.

## Bounds (state these, don't oversell)

- **Structure, not logic.** `explain check_one_push` shows its callers/callees; the
  *decide-then-fail-closed* logic still means reading the file. The graph maps terrain; it
  doesn't read road signs.
- **AST only, for research.** The free structural layer is what research uses. The
  doc-semantic bridges are real but expensive to refresh — out of scope for the live tier.

## Graceful fallback

If `graphify` is not installed (`command -v graphify` empty), skip Tier 1b entirely and
continue with the remaining tiers — exactly like Tier 1 Code-Map skips when
`docs/code-map/` is absent. graphify is never a hard dependency.
