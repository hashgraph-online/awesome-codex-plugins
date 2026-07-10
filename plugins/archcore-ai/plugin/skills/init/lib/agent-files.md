# Agent-instruction file catalog

Reference data for `/archcore:init` agent-instruction import — Detect Step A.4 finds candidates and sizes them; Phase B plans the import; Phase E creates it. Edit this file to add new agent-instruction file types as the ecosystem grows.

## Probe paths

Check each in order. Paths can be exact filenames or globs. A file counts if it exists and is non-empty.

| Path / glob | Class | Tool / convention |
|-------------|-------|-------------------|
| `CLAUDE.md` | `aggregate` | Claude Code (project-level memory) |
| `CLAUDE.local.md` | `aggregate` | Claude Code (user-local overrides, usually gitignored) |
| `AGENTS.md` | `aggregate` | Cross-tool convention (Claude Code reads it via import; OpenAI-adjacent tools use it too) |
| `.cursorrules` | `aggregate` | Cursor (legacy single-file format) |
| `.cursor/rules/*.mdc` | `modular-rule` | Cursor 2.x (rule files with frontmatter-configurable scope) |
| `.cursor/rules/*.md` | `modular-rule` | Cursor 2.x (plain markdown rule files) |
| `.github/copilot-instructions.md` | `aggregate` | GitHub Copilot (custom instructions) |
| `.github/instructions/*.md` | `modular-rule` | GitHub Copilot (modular instruction files) |
| `.windsurfrules` | `aggregate` | Windsurf (single-file) |
| `.windsurf/rules/*.md` | `modular-rule` | Windsurf (modular) |
| `.junie/guidelines.md` | `aggregate` | JetBrains Junie |
| `CONVENTIONS.md` | `aggregate` | Aider (convention file at repo root) |

## File classes — default import mode

Two classes, distinguished by how the source tool structures the file, drive different default import behavior:

- **`aggregate`** — a single file covering many topics; may be large (100–500+ lines). **Default: `link`** (one pointer `doc` per file) at `light`/`standard` depth. Importing the whole file as one archcore doc would breach the ≤ 200-line cap and produce an AGENTS.md-style blob; extract (split into typed docs per `extract-routing.md`, cap-guarded) is the default at **`deep`** depth and an opt-in via `edit` otherwise.
- **`modular-rule`** — a file that IS one rule, by the source tool's own design convention (Cursor/Copilot/Windsurf keep each rule small and single-purpose). **Default: `extract`** — one `rule`/`doc` per file (see "Modular-rule default behavior" below). These files carry the highest-signal, already-human-authored context in the repo; linking them as empty pointers is the value most first-day inits leave on the table.

## Source slugging

Slug the source filename for use in the `source:<slug>` tag. Algorithm:

1. Start from the **repo-root-relative** path (e.g., `AGENTS.md`, `.cursor/rules/styling.mdc`, `.github/copilot-instructions.md`).
2. Lowercase everything.
3. Strip any leading dot from the first path segment (`.cursorrules` → `cursorrules`, but `.cursor/rules/styling.mdc` → `cursor/rules/styling.mdc` — the dot on `.cursor` is stripped, not inner dots).
4. Replace `/` with `-`.
5. Replace `.` with `-`.
6. Collapse any run of two or more `-` into a single `-`.
7. Remove any non-alphanumeric-non-hyphen character (defensive).
8. Trim leading / trailing `-`.

Examples:

| Source path | Slug |
|-------------|------|
| `AGENTS.md` | `agents-md` |
| `CLAUDE.md` | `claude-md` |
| `CLAUDE.local.md` | `claude-local-md` |
| `.cursorrules` | `cursorrules` |
| `.cursor/rules/styling.mdc` | `cursor-rules-styling-mdc` |
| `.cursor/rules/styling.md` | `cursor-rules-styling-md` |
| `.github/copilot-instructions.md` | `github-copilot-instructions-md` |
| `.github/instructions/testing.md` | `github-instructions-testing-md` |
| `.windsurfrules` | `windsurfrules` |
| `.junie/guidelines.md` | `junie-guidelines-md` |
| `CONVENTIONS.md` | `conventions-md` |

The extension stays in the slug deliberately — it prevents collisions between `styling.md` and `styling.mdc`, which Cursor treats as different files.

## Body first line (import pointer)

Exact format, used verbatim in link-mode and prepended to extract-mode content:

```
> Imported from `<exact-relative-path>` on <YYYY-MM-DD>.
```

Where:
- `<exact-relative-path>` — path from repo root as the user would type it (`AGENTS.md`, `.cursor/rules/styling.mdc`). Preserve casing, slashes, leading dots.
- `<YYYY-MM-DD>` — current UTC date when the import runs.

Rationale: the slug can't carry the full path (no slashes, no dots), so the pointer lives in the body where readers — human and AI — can navigate to the source file. The leading `>` marks it as a quote/pull-out so it reads as metadata, not body content.

## Link-mode body shape (aggregate default)

Exactly the pointer line. Nothing else. Body length < 200 bytes so the imported stub does not trigger the "functionally populated" check in `bin/lib/empty-state.sh` — a near-empty repo with only link imports still shows the empty-state nudge until the user creates real documents.

This shape is the default for `aggregate` files only. `modular-rule` files default to extract and produce substantive bodies that DO count toward "functionally populated" — which is correct: they exist only in a repo that already has authored conventions, and Step 0(b) has already routed a truly empty repo away before Step A.4 runs.

Example body for a link import:

```
> Imported from `AGENTS.md` on 2026-04-23.
```

## Modular-rule default behavior

For `modular-rule` files, extract is the default. One file yields **one document** (they are authored as one cohesive rule — see `extract-routing.md` "Modular-rule files are one rule by design"):

1. Strip the YAML frontmatter (`---` … `---`). Capture `description:` as the preferred title (`extract-routing.md` Route 1) and `globs:` only as a hint for later relation-wiring — never create a doc from frontmatter.
2. Classify the file body by content (`extract-routing.md` Routes 1–3): a convention/standard → `rule` in `conventions/`; a pure reference or role description (e.g. `project-role`, `rules-sync`) → `doc` in `imported/`; a decision write-up → `adr` at **`deep` depth only** (Route 2's depth gate — a `light`/`standard` decision block downgrades to `doc`). Only genuine conventions land in `conventions/`.
3. Body is reproduced **verbatim** (after frontmatter strip), preceded by the pointer line. No synthesis, no rewrite — this is human-authored, human-confirmed content.
4. `status: draft`, tags `imported` + `source:<slug>`. No umbrella doc for a single-file/single-doc import.

**Size guard.** A modular-rule file **> 200 lines** is treated as effectively aggregate: at `light`/`standard` depth import it as **`link`** (with a preview note "large rule file — `edit`/`deep` to extract/split") rather than emit a 200+-line doc or shatter it into fragments. At **`deep`** depth it is extracted and **split into its natural H2 sections**, recursively re-split by H3 (or paragraph groups) if any section itself still exceeds 200 lines — see `extract-routing.md` "Block splitting". This keeps a big authored file (e.g. a 240-line `error-handling.mdc`) from breaching the line cap at the cheap tiers while still surfacing its content when the user opts into `deep`.

**HIGH-cost gate for modular-rule files.** HIGH only when the combined size of modular-rule files exceeds **50 KB**. **File count is NOT a HIGH signal** — ten 30-line files is cheap (far cheaper than one hotspot spec). On modular-rule HIGH (rare), degrade to link with a preview warning; extract stays opt-in for those files.

## Extract-mode body shape

Pointer line, then a blank line, then the extracted content. See `lib/extract-routing.md` for how content is selected per document type.

## Umbrella document for extract mode

When a file is imported in extract mode and yields multiple documents, also create **one** umbrella `doc` in link-mode shape (title `Imported: <basename>`, body = pointer only). Each extracted document gets a `related` edge back to the umbrella. Purpose: a single graph node per source file, so re-runs and removals can find and clean up all derived documents at once.
