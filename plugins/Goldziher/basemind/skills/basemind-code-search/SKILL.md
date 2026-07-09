---
name: basemind-code-search
description: >-
  Find where code is defined and used without reading files — symbol search, file outlines,
  references, callers, call graphs, implementations, dependents, and indexed regex over content.
  Reach for it whenever the user asks "where is X defined", "what calls Y", "what implements Z",
  "what's the shape of this file", or whenever you're about to grep or open files to learn structure.
---

# basemind-code-search — navigate code without reading it

basemind pre-indexes the repo into a tree-sitter code map across 300+ languages. Structural
questions — where a symbol lives, what calls it, what shape a file has — resolve from the index in
milliseconds and return **paths, line numbers, and signatures, not file bodies**. That is a fraction
of the tokens of reading source, so it is the default, not an optimization.

**basemind first, grep/read fallback.** If a question is about _where_, _what calls_, _what shape_,
or _what implements_, a basemind tool answers it cheaper than `grep`/`rg` or opening files. Drop to
raw shell only when no tool covers the question.

## The discipline

- **`outline` a file before you open it.** A 1000-line file becomes a 30-line table of contents.
  Read the actual source only once you have the exact span, then read _that range_, not the file.
- **`search_symbols` instead of `grep` for a definition.** It matches indexed symbol names and
  returns `path:line`, skipping the comment/string/test-name noise grep drowns you in.
- **`find_references` / `find_callers` instead of grepping call sites.** Indexed call edges, not
  text matches.
- **`workspace_grep` instead of shelling out to ripgrep** when you genuinely need regex over
  content — it runs over the in-RAM index and returns capped, structured hits.
- **Do not re-read a file basemind already mapped.** If the outline answered the question, stop.
- **`rescan` after you edit code**, not a server reconnect. Pass `paths: [...]` to limit it.

## Tool routing

| Question | MCP tool | CLI |
|---|---|---|
| "Where is X defined?" | `search_symbols` (substring, optional `kind`) | `basemind query symbol "X"` |
| "What's the shape of file F?" | `outline` (add `l2: true` for calls + docs) | `basemind query outline F [--l2]` |
| "What calls X?" (any name) | `find_references` | `basemind query references "X"` |
| "What calls this specific definition?" | `find_callers` (path + name + optional kind) | `basemind query callers F name [--kind]` |
| "Trace the call graph from a function?" | `call_graph` (BFS, bounded by `max_depth` / `max_nodes`) | `basemind query call-graph "name" [--direction --max-depth]` |
| "What implements / extends / inherits X?" | `find_implementations` (Rust, Python, TS/TSX, JS) | `basemind query implementations "X"` |
| "What imports module M?" | `dependents` | `basemind query dependents "M"` |
| "What files are indexed?" | `list_files` (filter by `language` / `path_contains`) | `basemind query list-files [--language --path-contains]` |
| "Regex over file contents?" | `workspace_grep` | `basemind query grep "pattern" [--language --path-contains]` |
| "What's indexed?" | `status` | `basemind query status` |
| "Refresh the index after editing?" | `rescan` (optional `paths`) | `basemind scan` |
| "Fetch the next page?" | pass `next_cursor` from the prior response as `cursor` | — |

## Examples

```text
search_symbols { needle: "MapCache" }
→ src/mcp/mod.rs:79:1 MapCache (struct)
  src/mcp/mod.rs:88:1 MapCache (impl)

find_references { name: "process_file" }
→ src/scanner.rs:142:9 process_file
  src/scanner.rs:201:13 process_file

outline { path: "src/mcp/tools.rs" }
→ 21 #[tool] outline (function)
  112 #[tool] search_symbols (function)
```

## Notes

- Matching on symbol names is **substring**: `find_references("bar")` matches `Foo::bar()` and
  `bar()` alike. There is no scope resolution — cross-check with `outline` when disambiguation matters.
- Lists are capped (`limit`, default 100, max 1000). Index scanners use `scan_cap = limit * 8` to
  bound work on common names.
- Needs an index at `.basemind/` — run `basemind scan` first (see the `basemind-scan` skill). "No
  indexed files" means the scan hasn't run in this repo yet.

For git history / blame / diffs see `basemind-git-history`; for document RAG and semantic search see
`basemind-documents`; for agent coordination see `basemind-comms`.
