# Surface detection catalog

Reference data for `/archcore:init` Step A.2 (Detect sub-phase). SKILL.md wires the
`create_document` call; this file supplies detection logic plus the `## Output`
template.

## What it detects

The PUBLIC SURFACE = the named units a *consumer* of this repo reaches for by name,
when those units are **not already captured by the entry-point inventory**. Entry
points are where an external trigger crosses into the running program (HTTP/RPC
handlers, CLI binaries, queue workers, lifecycle hooks). The surface is the
complementary, often *static* outward shape that `detect-entry-points` leaves thin:

- the **routes / pages** a web app serves to a browser (incl. client-side routers);
- the **public API** a library / SDK exports to its importers;
- the **command catalog** of a multi-command CLI;
- the **skills / commands / agents** an agent-plugin or Markdown-tooling repo ships;
- the **screens / navigation** of a mobile app.

It is the document that answers "what does this repo expose?" for the archetypes
where there is no server with route handlers — libraries, SPAs, plugin/markdown
tooling, multi-command CLIs, mobile apps. The concept is role-based and
language/domain-agnostic. **NAMES + a one-line purpose only** — never params,
props, full signatures, or implementation.

## How to find it (any codebase)

1. **Identify the consumer relationship: who calls this code, and how?** A browser
   hitting routes, a developer importing a package, an operator typing commands, an
   agent host loading skills, a user tapping screens. That relationship names the
   surface kind — reason it from the manifest, the entry file, and the dominant
   file layout, not from training priors.
2. **Enumerate the declared named units for that kind, from evidence:**
   - **Web routes / pages** — framework route files or a router table (server- or
     client-side). Capture `path → component/handler name`.
   - **Library / SDK public API** — the package's *declared* exports: the manifest
     `exports`/`main`/`types` entry and what it re-exports, `__all__`, a crate's
     `pub` items in `lib.rs`, a Go package's exported identifiers, an `index.*`
     barrel that IS the public entry. Capture exported symbol names, grouped.
   - **CLI command catalog** — a multi-command CLI's registered subcommands.
     Capture `command — summary`.
   - **Agent / plugin / Markdown tooling** — the skills / commands / agents the
     repo ships: skill/command/agent definition files or a plugin manifest's
     declared components. Capture each unit's `name — description` (read from the
     file's frontmatter `name`/`description`, never invent).
   - **Mobile screens / navigation** — the navigation graph's named routes/screens.
3. **Capture NAMES + one-line purpose only.** Stop reading a source as soon as you
   have its named units. Never dump props, params, request/response shapes, or full
   signatures — those belong to a per-module `spec`, not this inventory.
4. **Cap at ~20 units**, most-central first (most referenced / most prominent);
   ties broken alphabetically. If more exist, append a final `| +N more |  |` row
   and stop; do not paginate.
5. Emit a signal only on positive evidence; when no candidate is unambiguous,
   prefer omission over a guess — never invent.

## Common signals (non-exhaustive examples)

These are non-exhaustive examples to orient pattern-matching — absence from this
list is NOT absence of signal; fall back to the method above for anything not
shown.

| Surface kind | Where to read it | Unit captured |
|---|---|---|
| Web routes (server) | Next.js `app/**/page.*` & `pages/**`, Remix/SvelteKit `routes/**`, Rails `config/routes.rb`, Django `urls.py`, Laravel `routes/*.php` | `path — view/handler` |
| Web routes (client) | React Router `<Route path>`, Vue Router / `pinia`-era route tables, Angular `RouterModule.forRoot([...])` | `path — component` |
| Library / SDK API | `package.json` `exports`/`main`, `__init__.py` `__all__`, Rust `lib.rs` `pub fn`/`pub struct`, Go exported identifiers, an `index.*` barrel | exported symbol name + kind |
| CLI commands | cobra `AddCommand`, click/typer groups, `commander`/`oclif`/`citty` command defs, Thor tasks | `command — summary` |
| Agent / plugin / md tooling | `**/skills/*/SKILL.md`, `**/commands/*.md`, `**/agents/*.md`, plugin manifest `commands`/`skills`/`agents` arrays | `name — frontmatter description` |
| Mobile screens | React Navigation `Stack.Screen`, Flutter `routes:`/`GoRouter`, iOS storyboard/SwiftUI `NavigationStack` destinations | `route/screen — purpose` |

**Do NOT restate entry points.** If `detect-entry-points` already enumerated the
HTTP routes or CLI commands as runtime entries, do not duplicate them here — the
surface doc exists for what the entry-point inventory does *not* cover. When the two
would overlap completely (a server whose every route is already an entry), skip the
surface doc.

## Output

`SKILL.md` Phase E fires the `create_document`; this catalog supplies the body.

| Field | Value |
|---|---|
| `type` | `doc` |
| `directory` | `architecture` |
| `filename` | `public-surface` |
| `title` | `Public surface` |
| `status` | `accepted` |
| `tags` | `['surface', 'architecture']` |
| Body cap | **≤ 25 lines** |

Body = an orientation line naming the surface kind, then grouped one-liners. Drop
empty groups; one line per unit; ≤ 25 unit lines (group `##` headings do not count).

```
Surface: {kind(s)} · {N} units.

## Routes
- /dashboard — DashboardPage (auth-gated overview).
- /invoices/:id — InvoiceDetail.

## Public API
- `parse(input)` — function, top-level export.
- `Tokenizer` — class.

## Skills
- init — first-time Archcore setup.
- capture — document a module or system.
```

## When to skip

- **No named surface exists** (an internal-only batch script tree with no exports,
  routes, commands, or skills) → produce nothing; emit a one-line progress note.
- **Already fully covered by the entry-point inventory** → skip; do not duplicate.
- **Single trivial unit** (one route, one export) → skip; not worth a document.

Surface once in the init closing message when skipped for "no surface":

> No public surface detected (no routes, exported API, command catalog, or shipped
> skills beyond the entry points already listed).

## Edge cases

- **Mixed surfaces** (a repo that is both a library and a small CLI) → one doc, one
  `##` group per kind; name both in the orientation line.
- **Monorepo / large mode** → group units under `### <domain-slug>` subsections,
  matching the domain slugs from `detect-domains.md`; scope to the selected domains.
- **Plugin/markdown tooling with many skills** → keep the highest-level units
  (skills, commands, agents); do not list every nested helper file.
