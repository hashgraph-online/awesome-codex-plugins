# Global Sources — Local/Global Reading Convention

Plugin runtime asset. Loaded by skills (`context`, `audit`, `capture`,
`decide`, `plan`) **only when** MCP results indicate a project mounts global
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
