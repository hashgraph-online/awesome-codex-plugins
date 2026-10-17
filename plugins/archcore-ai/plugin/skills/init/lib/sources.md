# Authored source catalog

Reference data for `/archcore:init`. The assessment gate (`SKILL.md` step 5) and the `discover` and `triage` gates of `skills/_shared/tracks/import.md` read this file. It defines the five discovery levels, the record each found source gets, the triage verdicts, and the measures the gate computes. Contract: `authored-source-discovery.spec`.

An **authored source** is a file, or a recoverable piece of git history, in which a person recorded knowledge about the repository: a convention, a decision, a procedure, a contract, a reference fact, or an intent. Source code and code comments are not authored sources; the code seed reads code.

## How to find it

Every path list below is a set of **non-exhaustive** examples, not a checklist. When the repository uses another layout, reason from what a file is for — who wrote it, for which reader, and whether it records knowledge that is still true — and add a source only on **positive evidence**. Prefer omission over a guess.

## Never a source

- The archcore managed block: the span from `<!-- archcore:start -->` to `<!-- archcore:end -->`, inclusive, which host wiring writes into `CLAUDE.md`, `AGENTS.md`, and `GEMINI.md`. Strip every such span before sizing, heading counts, and reading. A file whose only content is the managed block produces no source record.
- `.archcore/`, `.git/`, dependency directories (`node_modules/`, `vendor/`, `.venv/`), and build outputs (`dist/`, `build/`, `out/`, `target/`, `coverage/`, `.next/`).

## Levels

A plain init reads L1 and L2. `/archcore:init import` reads all five. A path subject limits every level to that path.

### L1 — agent instructions

Text written for a coding agent. Highest signal: the author already wrote it as context.

| Path or glob | Tool or convention |
|---|---|
| `CLAUDE.md`, `CLAUDE.local.md`, nested `**/CLAUDE.md` | Claude Code |
| `AGENTS.md`, nested `**/AGENTS.md` | cross-tool convention |
| `GEMINI.md` | Gemini CLI |
| `.claude/rules/*.md` | Claude Code rule files |
| `.cursorrules`, `.cursor/rules/*.mdc`, `.cursor/rules/*.md` | Cursor |
| `.github/copilot-instructions.md`, `.github/instructions/*.md` | GitHub Copilot |
| `.windsurfrules`, `.windsurf/rules/*.md` | Windsurf |
| `.junie/guidelines.md` | JetBrains Junie |
| `CONVENTIONS.md` | Aider |

A rule file of Cursor, Copilot, or Windsurf is one rule by its tool's design; expect one knowledge unit from it. Its YAML frontmatter is metadata: `description:` suggests a title, `globs:` suggests `scope_paths`.

### L2 — decision and design records

- Directories: `docs/adr/`, `doc/adr/`, `adr/`, `decisions/`, `docs/decisions/`, `rfcs/`, `docs/rfcs/`, `design/`, `docs/design/`, `proposals/`, `architecture/`.
- Files: `ARCHITECTURE.md`, `DESIGN.md`, and numbered records in the adr-tools or MADR form (`NNNN-title.md`).
- A record carries its own state (accepted, superseded, proposed). Record the state; a superseded record supports the record that replaced it and is not a target of its own.

### L3 — contributor docs

- Root files: `CONTRIBUTING.md`, `DEVELOPMENT.md`, `HACKING.md`, `TESTING.md`, `STYLEGUIDE.md`, the process part of `SECURITY.md`.
- The developer sections of `README.md` (setup, architecture, conventions) and the READMEs of packages in a workspace. The product pitch of a README is the skip class `marketing`.
- `runbooks/`, `ops/`, `playbooks/`, and the pull-request template (a checklist is a convention).
- A Markdown tree under `docs/` that holds **no** publish config.

### L4 — published docs tree

A tree is published when a publish config sits at its root or names it: `docusaurus.config.*`, `mkdocs.yml`, `astro.config.*` with Starlight, `.vitepress/config.*`, `docs.json` or `mint.json` (Mintlify), `conf.py` (Sphinx), `book.toml` (mdBook), `_config.yml` (Jekyll), `antora.yml`. One config root is one site.

Classify each page by its reader:

- **End user of the product** — tutorial, quickstart, API or CLI reference, how-to for users, marketing, changelog, release notes → verdict `skip`. The site already is the source of truth for that reader, and a copy would drift.
- **Contributor or maintainer** — architecture, internals, decisions, design notes, contributor process, operations → verdict `convert` or `mine`.
- **Undecided from the path and headings** → verdict `mine`; the body read decides.

Every L4 site also yields one `reference` fact: a `doc` that records the site's path, its build tool, and the topics it covers, so the agent knows where user-facing answers live.

During assessment, record each in-scope site's publish config as an L4 `reference` source, once per config root. Keep this record even when every page is `skip`. The page skip classes and the 400-byte stub threshold do not exclude this site record.

### L5 — git history

Run only when the repository has history and is not a shallow clone (`git rev-parse --is-shallow-repository` prints `false`).

| Input | Command shape | Use |
|---|---|---|
| Deleted Markdown | `git log --diff-filter=D --name-only --format= -- '*.md' '*.mdc'` | A deleted L1–L3 file is a candidate only when the code still confirms what it states; read it with `git show <commit>^:<path>` after the confirm. |
| Renames | `git log --follow --name-status -- <path>` | Follow a source to its current path; never list both names. |
| Freshness | `git log -1 --format=%cs -- <path>` | Fill `last_change`; compare with the last change of the code paths the source names. |
| Decision-bearing messages | `git log --format='%H%n%B' --grep='because\|instead of\|BREAKING\|decided'` | Evidence for a target `adr` that a standing source already opened. |

Two limits bind L5. Commit and merge messages are evidence, never a standalone source. L5 is never the only source of a target `rule`: a rule with no standing authored source has no owner to confirm it.

## Source record

| Field | Content |
|---|---|
| `path` | repository-relative path; for a deleted file, `<commit>^:<path>` |
| `level` | exactly one of `L1`–`L5` |
| `bytes` | size after stripping managed blocks |
| `headings` | count of H2 headings (H1 when the file has no H2) after stripping managed blocks — **outside fenced code blocks**; a `# comment` inside a shell fence is not a heading |
| `last_change` | date from git; omitted when the repository has no history |
| `verdict` | `convert`, `mine`, `reference`, or `skip` |
| `reason` | one line, shown in the preview |

## Triage verdicts

| Verdict | Meaning |
|---|---|
| `convert` | the whole file is authored knowledge; every knowledge unit becomes part of a target document |
| `mine` | part of the file is authored knowledge; the rest belongs to a skip class or to another reader |
| `reference` | the source stays where it is; one fact records where it lives (the L4 site fact) |
| `skip` | nothing is converted; the reason names the skip class |

Skip classes: `license`, `changelog` (changelogs and release notes), `generated` (a header or a generator config marks the file as output), `vendored`, `translation` (a localized copy of a page that is already a source), `marketing`, `template` (issue and discussion templates), `end-user-page` (L4 pages for users of the product), `superseded` (an L2 record another record replaces), `stale` (the code contradicts the file's main claims and no recent change touched it), `stub` (under 400 bytes after stripping — a one-line README holds no knowledge unit).

A source whose `last_change` is older than the last change of every code path it names is not `stale` by that fact alone; it is ranked later, and its claims are checked against the code during conversion.

## Measures for the assessment gate

The gate reads paths, sizes, headings, and git metadata — never a full body.

1. **`targets_est`** — count one target for each L4 `reference` site record. Add the counts of `convert` or `mine` sources by shape below. Headings alone overcount: a 2 KB file with six headings is one document, and a glossary with thirty entries is one `doc`. Size bounds each conversion count.

   | Source shape | Count |
   |---|---|
   | rule file of L1 (`.cursor/rules/*.mdc` and equivalents) | 1 |
   | aggregate file of L1 (`CLAUDE.md`, `AGENTS.md`, …) | `headings`, at most `ceil(bytes / 1.5 KB)`, at most 10 |
   | L2 record (one ADR, one RFC, one design doc) | 1, plus 1 per full 15 KB — a record that large splits under the 200-line cap |
   | single-topic file: a package README, a glossary, a security policy, any file whose headings are entries of one list | 1; 2 when above 8 KB |
   | any other L3 or L4 file | `headings`, at most `ceil(bytes / 8 KB)`, at most 10 |
   | a deleted file from L5 | 1 |

   Floor of 1 per source. Sum the counts, then subtract overlaps under one test only: two sources count once when they are single-topic files of the same kind (a root glossary and a `CONTEXT.md` language file), or when both name the same code path in a heading. Title similarity alone is not an overlap. A section that a Tier-1 fact owns (see "Overlap with seed facts") counts zero on a run that composes the seed.
2. **`tier`** — `none` when `targets_est` is 0 (see "No authored source"); `S` when `targets_est` is 1–8; `M` when 9–40; `L` above 40. Within 1 of a boundary (8 or 9; 40 or 41), take the higher tier: the staged path with a plan document is the safe one, and an estimate from headings is not exact. [assumption] The thresholds await calibration by `test/behavioral/import-bench.sh`.
3. **`coverage_set`** — search the L1–L2 sources for mentions of the ranked hotspot module paths. Match a **path-shaped** mention only: the path with at least one `/`, or the name inside backticks or followed by `/` — a bare word match turns `store`, `core`, or `filter` into dozens of false hits. A module that a source with the verdict `convert` or `mine` names in a heading, or names three or more times, enters the set with that source's path. This is an estimate: the preview labels it so.
4. **`levels_found`** — the levels with at least one non-`skip` source. An L4 `reference` site record includes L4 even when every page is `skip`; a lone site record yields `targets_est=1`, tier `S`.
5. **`deeper_present`** — a plain init and a refresh only. One path listing, no size, no heading count, no verdict: the L3 root files that exist, the count of `.md` files under `docs/`, and the publish configs of L4. The result never enters `targets_est`, `tier`, or `coverage_set`.

## No authored source

The assessment result is **no authored source** when `levels_found` is empty: no file was found, or every source found carries the verdict `skip`. `targets_est` is then 0 and `tier` is `none`. A result of this kind is a normal outcome, not an error, and it never licenses a guess: the init skill MUST NOT lower a skip class, read a body, or invent a source to reach a target.

| Run | What the init skill does |
|---|---|
| plain init or refresh, code present | composes the code seed over the unchanged pool; the preview carries no Covered line and no Authored sources block |
| plain init, no manifest and no source code | the **empty** route of `lib/host-wiring.md` |
| `import`, with or without a path | the **no-source** route: prints the no-source report, fires no gated operation, asks no confirm, composes no code seed |

**Announce line of a plain init or a refresh** — in place of the counts, name what was checked:

> Authored context: none at L1–L2 (no agent-instruction file, no decision record).

WHEN `deeper_present` is non-empty, add one line that names the paths and the command that reads them:

> Contributor docs exist below the levels this run reads (CONTRIBUTING.md, docs/ — 34 .md files, mkdocs.yml): `/archcore:init import` converts them.

**No-source report of the `import` mode** — one row per level, then the next command:

```
Import: no authored source to convert.
  L1 agent instructions   none
  L2 decision records     none
  L3 contributor docs     README.md — skip (stub, 212 B) · CHANGELOG.md — skip (changelog)
  L4 published docs       none
  L5 git history          off — shallow clone
Nothing was created. To overrule a verdict, name the path: "convert README.md".
```

1. List every `skip` source with its class, so the user sees that the file was found and why it was left.
2. IF the path subject does not exist, THEN say so and stop. IF the path exists and holds no source, THEN print the report for that path and name `/archcore:init import` without a path.
3. WHEN the user names a skipped path to convert, change that verdict and enter the track at `import.triage` with that source; the plan preview and its confirm follow as usual.
4. Close with the command that fits the corpus. No stack rule, run guide, or overview in `.archcore/` → `/archcore:init`, which seeds from the code and wires the host. Already seeded → `/archcore:document`: a repository without written conventions keeps them in people's heads, and one recorded decision or convention at a time is how they enter `.archcore/`.

## Overlap with seed facts

Agent-instruction files often restate what a Tier-1 fact extracts: run and build commands (the run guide), the directory layout (the top-level map), the stack (the stack rule). The fact stays the owner — init's idempotency flags key on it. Such a section is **evidence for the fact**, not a conversion target: give it to the matching detector (`extract-run-instructions.md` already reads authored run sections), count it zero in `targets_est`, and treat it as covered at the retire gate once the fact exists. A convention inside such a section ("always run `make lint` before a commit") is still a `rule` unit.

On a run that composes **no** seed — the `import` mode and the import-only route — such a section is a target, and it takes the **fact's own shape**: the type, directory, filename, title form, and tags of the matching detector's `## Output` section (`extract-run-instructions.md`, `detect-domains.md`, `detect-stack.md`). A later `/archcore:init refresh` then finds the fact present by its flag and composes no second run guide or layout map.

## Preview rows

Show every source, grouped by level, one row each: `path` — `level` — `verdict` — `reason`. `skip` rows stay visible so the user can overrule a verdict with `edit`.
