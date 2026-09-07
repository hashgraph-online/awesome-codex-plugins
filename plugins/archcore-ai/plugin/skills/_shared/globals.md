# Global Sources — Local/Global Reading Convention

Plugin runtime asset. Loaded by skills (`init`, `plan`, `document`, `review`)
**only when** MCP results indicate a project mounts global
sources. Mirrors the CLI contract `local-overrides-global.rule` /
`global-sources.spec.md` shipped with the `archcore` CLI.

## When this applies

A project MAY mount read-only **global sources** (org-wide standards, a
platform/monorepo-root `.archcore/`) declared in `.archcore/settings.json`
`globals[]`. The MCP read tools then surface those documents alongside local
ones, each annotated with source fields.

**This file is opt-in by data.** If no result in a tool response carries
`global: true` / `read_only: true` / `source_kind: "global"`, the project has no
globals in play — ignore everything below and behave exactly as you would
without globals. No badge, no extra section, no behavioral change. Most projects
have no globals; the default path must stay unchanged for them.

## Detecting a global document

Read the source fields the MCP tools return — never infer authority from the
path or title (`local-overrides-global.rule`):

| Field | Local | Global |
|---|---|---|
| `source_kind` | `"local"` | `"global"` |
| `source_id` | `"local"` | the source id (e.g. `"company"`) |
| `global` | absent / `false` | `true` |
| `read_only` | absent / `false` | `true` |

`list_documents` and `get_document` always carry these. `search_documents`
carries them on a current CLI; an older CLI may omit them — when absent, treat
every result as local (the safe no-op default).

A current CLI (v0.8.0+) wraps `search_documents` output in an envelope:
`{"results": [...], "coverage": {...}}`. An older CLI returns a bare array.
Read whichever shape arrives — the result rows are identical in both.

## Searching across sources

`search_documents` and `list_documents` cover local and global documents
together. Every feature below is opt-in by data, like the rest of this file:
use it when the response shows it; an older CLI simply never shows it.

- **`coverage` is proof of what was searched.** It maps each source id to its
  scanned document count, e.g. `{"local": 102, "org": 42}`. An empty `results`
  next to a `coverage` that names a global source is a verified absence across
  every listed corpus — never read it as "the globals were skipped".
- **Word matching.** A current CLI matches every whitespace-separated word of
  `content`, in any order and at any distance ("plugin compatibility" matches
  "Plugin / CLI Compatibility"). An older CLI matches the exact substring.
  Query with the important words, not with a literal sentence.
- **Retry ladder for an empty result**, when `coverage` names a global source:
  first broaden to fewer or more general words; then `match: "any"`; then scope
  with `source: "global"` (or a declared source id) to probe the global corpus
  alone. After the ladder, report a true absence honestly.
- **Vocabulary map.** On a current CLI the SessionStart context carries a
  `GLOBALS` block naming each mounted source with its document counts and
  top-level directories. Use those directory names as query vocabulary for
  org-wide topics the local corpus does not cover.
- **`by_source` in `list_documents`.** A current CLI reports the full filtered
  count per source and keeps every source represented on the first page.
  Compare `by_source` with the page to see what a truncation dropped, and pass
  `source` to scope a listing.

## Reading convention

- **Local overrides global.** When the same topic is covered by both a local
  document and a global one, the local document is authoritative for this
  project; the global is the org-wide default it refines.
- **Same-slug pair** (e.g. a local `error-handling.rule.md` and a global one):
  the local is the effective rule; the global is background/context. Do not
  present the global as binding when a local one exists — note that the local
  overrides it.
- The tools surface **both** documents; precedence is a reading convention you
  apply, not a dedup the server performs. Do not drop the global silently.

## Write convention

- **All writes target local documents.** Global documents are read-only; the
  MCP write tools reject them (`cannot ... a read-only global source document`).
- Never `update_document` / `remove_document` against a global result. Never
  `add_relation` referencing a global on **either** endpoint (source or target)
  — relations connect local documents only. If a same-topic global exists and
  the user wants a change, create or edit the **local** document (an override)
  instead; corrections to the global itself belong upstream in its source
  repository.

## Presentation

- When you surface a global document to the user, mark it — e.g. append
  `[global · <source_id> · read-only]` to its line — so project-local knowledge
  is visibly distinct from org-wide defaults.
- When answering from a global while a local override exists, say so explicitly.
