---
name: vault-mirror
description: Use when you need to populate the Meta-Vault with machine-generated notes derived from session-orchestrator JSONL records. Converts entries from `.orchestrator/metrics/sessions.jsonl` and `.orchestrator/metrics/learnings.jsonl` into vault-conformant Markdown under `50-sessions/` and `40-learnings/`. Called automatically at session-end Phase 3.7 and after evolve Phase 3.5 — only when `vault-integration.enabled=true` and `vault-integration.mode != "off"`. Idempotent: re-runs safely; skips hand-authored notes. Triggers: "mirror to vault", "sync session notes to vault", "write learning notes to vault", "vault-mirror failed at session close". <example>Context: session-end is finalizing, vault-integration.mode is "warn". user: "/close" assistant: "Running vault-mirror to write 50-sessions/session-2026-05-17.md from the closing session record — 1 created, 0 skipped."</example>
model: haiku
---

# Vault Mirror Skill

> Project-instruction file resolution: `CLAUDE.md` and `AGENTS.md` (Codex CLI) are transparent aliases — see [skills/_shared/instruction-file-resolution.md](../_shared/instruction-file-resolution.md). When this skill mentions Session Config in `CLAUDE.md`, the alias rule applies.

## Purpose

vault-mirror populates the Meta-Vault with machine-generated notes derived from structured JSONL records. It converts entries from `.orchestrator/metrics/sessions.jsonl` and `.orchestrator/metrics/learnings.jsonl` into vault-conformant Markdown files under numeric-prefix subdirectories. This is distinct from vault-sync, which validates the vault — vault-sync validates the vault; vault-mirror populates it. The two skills are complementary: vault-mirror writes notes, vault-sync checks that the vault as a whole remains conformant.

## When Invoked

vault-mirror is called in two places:

- **Phase 3.7 of session-end** (`skills/session-end/session-metrics-write.md`) — mirrors the sessions.jsonl entry for the closing session.
- **Phase 3.5 of evolve** (`skills/evolve/SKILL.md`) — mirrors all learnings.jsonl entries added during the evolve cycle.

Both call sites are conditional: vault-mirror runs only when `vault-integration.enabled == true` AND `vault-integration.mode != "off"` in the project's Session Config. When either condition is not met, the call site skips silently and vault-mirror is never invoked.

## Inputs

`scripts/vault-mirror.mjs` is the implementation. All arguments are required except `--dry-run`.

| Flag | Type | Required | Description |
|---|---|---|---|
| `--vault-dir` | path | yes | Absolute path to the Meta-Vault root directory. Must exist. |
| `--source` | path | yes | Path to the JSONL file to read (one JSON object per line). Must exist. |
| `--kind` | `session` or `learning` | yes | Determines which generator and target path are used. |
| `--dry-run` | flag | no | Parse and resolve paths but do not write any files. Emits action lines as normal. |

Empty lines in the JSONL source are silently skipped.

## Outputs

One JSON line is written to stdout for each non-empty JSONL entry processed. Exit code reflects the run outcome.

### Action values

| `action` | Meaning |
|---|---|
| `created` | Entry did not exist in the vault; file created. |
| `updated` | Entry existed (generator marker present, same id) with an older `updated` date; file overwritten. |
| `skipped-noop` | Entry existed, same id, `updated` date not advanced; file unchanged. |
| `skipped-handwritten` | A file at the target path has no `_generator` marker (or an unknown generator); left untouched. |
| `skipped-collision-resolved` | A file at the target path has the generator marker but a different `id`; a disambiguated slug was used instead. |
| `skipped-invalid` | Entry is missing one or more required fields; entry skipped, processing continues. |
| `skipped-quality-low` | Entry failed the quality gate (PRD F1.2): learning `confidence` below `vault-mirror.quality.min-confidence` (CLI: `--quality-min-confidence`, default `0.5`), or session rendered-narrative length below `vault-mirror.quality.min-narrative-chars` (CLI: `--quality-min-narrative-chars`, default `400`). The emitted JSON line includes a `reason` field describing the violated threshold and `path: null` (no file was created). The quality gate runs **before** `--force`; `--force` does not bypass it. |

### Output line shape

```json
{"action":"created","path":"50-sessions/session-orchestrator/session-2026-04-13.md","kind":"session","id":"session-2026-04-13"}
```

`path` is relative to `--vault-dir`.

### Exit codes

| Code | Meaning |
|---|---|
| `0` | Success (including idempotent no-ops and per-entry skips). |
| `1` | Malformed JSON on a JSONL line — fatal, processing stops. Also returned when required CLI args are missing. |
| `2` | Filesystem error: `--vault-dir` not found, `--source` not found, or an unexpected write error. |

## Target Paths

| Kind | Target |
|---|---|
| `session` | `<vault-dir>/50-sessions/<repo>/<session-id>.md` |
| `learning` | `<vault-dir>/40-learnings/<repo>/<slug>.md` |

Subdirectories are created automatically with `mkdirSync({ recursive: true })` when writing (not in `--dry-run` mode).

The numeric prefix (`50-sessions/`, `40-learnings/`) follows the vault folder ordering convention so that sessions and learnings appear in the correct position in the vault tree relative to other note types.

**Per-project namespacing (#660).** New writes are namespaced under a per-repo subdirectory `<repo>/`, so a single shared vault can hold notes from multiple projects without cross-repo slug/id collisions. `<repo>` is resolved by `resolveRepoNamespace()` (`scripts/lib/vault-mirror/namespace.mjs`): the optional `vault-integration.vault-name` Session Config key (CLI: `--vault-name`) when set, else the git-origin repo slug via `deriveRepo()`, sanitised to a single kebab segment. Owner-privacy leaks (personal home path / private project slug / personal name) are redacted to `redacted-repo` before any write. The legacy **flat** layout (`40-learnings/<slug>.md`) is still read — the writer dual-probes the flat path so a pre-existing flat note is never duplicated; a one-time relocation of the historical flat corpus is tracked as a follow-up.

**Path contract note:** Issue #187 shipped the flat numeric-prefix layout (deferring the per-`<repo>` subfolder it sketched). Issue #660 adds that per-repo subfolder for write-isolation (above) while keeping the numeric-prefix ordering. If you need a different layout, file a new issue — do NOT silently change the script.

**Host-local pseudonym mapping (Epic #725 D5).** Without a map, EVERY owner-leaky repo namespace collapses to a single `redacted-repo/` subdir — which breaks the #660 write-isolation (N private repos share one directory → id/slug collisions) and destroys cross-repo attribution. A host-local **pseudonym map** fixes this: each real repo slug is assigned a stable, non-leaky pseudonym, so the vault gets `40-learnings/<pseudonym>/` (and matching `source-repo` frontmatter, via W2's attribution threading) instead of everyone landing in `redacted-repo/`. The map is a JSON object `{ "real-slug": "pseudonym-slug", … }` at a host-local path referenced by `owner.yaml` → `paths.namespace-map-path` (env `SO_NAMESPACE_MAP` overrides; precedence env > owner.yaml > unset). `resolveRepoNamespace()` consults the map ONLY at the redaction site (i.e. only when a repo would otherwise be redacted), looking up both the sanitised segment and the raw identifier; a hit returns the pseudonym and skips redaction, so clean/public repos never touch the map (or its lazy owner.yaml read). **Privacy guarantee:** the map file lives OUTSIDE every repo (alongside `owner.yaml` under `~/.config/session-orchestrator/`) and is never committed — only the pseudonyms reach the vault, the real names stay host-local. Each pseudonym is validated (must be a kebab slug AND must not itself be owner-leaky); invalid or leaky pseudonyms are dropped with a WARN. **Fallback:** an absent, unreadable, or malformed map — and any UNMAPPED owner-leaky repo — still redacts to `redacted-repo`, identical to pre-#725 behaviour. Implementation: `scripts/lib/vault-mirror/pseudonym-map.mjs` (`loadPseudonymMap`) + `namespace.mjs`.

## Idempotency

vault-mirror is safe to run multiple times against the same JSONL source:

1. **No file exists** → create.
2. **File exists, `_generator` marker present, same id, `updated` date not advanced** → `skipped-noop`, file unchanged.
3. **File exists, `_generator` marker present, same id, `updated` date advanced** → `updated`, file overwritten.
4. **File exists, no `_generator` marker** → `skipped-handwritten`, file untouched. The absence of the marker means the file was written by a human and must not be overwritten automatically.
5. **File exists, `_generator` marker present, different id** → slug collision. A disambiguated slug is derived by appending `-<first-8-chars-of-entry-uuid>` (hyphens stripped from the UUID before taking the prefix). The original file is left unchanged; the new note is written at the disambiguated path with action `skipped-collision-resolved`.

The generator marker value is `session-orchestrator-vault-mirror@1` and appears in the YAML frontmatter as `_generator: session-orchestrator-vault-mirror@1`.

## Auto-Commit Phase

After a successful mirror pass, `scripts/lib/vault-mirror/auto-commit.mjs` (`autoCommitVaultMirror(vaultDirPath, sessionId, repo)`) optionally commits the freshly-written mirror artifacts in `40-learnings/` and `50-sessions/` as a single `chore(vault): mirror …` commit. It runs unattended at session-end Phase 3.7 / evolve Phase 3.5. The phase is fail-safe: it never throws, emits one JSON action line on stdout, and aborts (unstaging everything) if any staged path is **not** a generator-stamped mirror artifact. When the optional `repo` namespace is passed (#660), staging is scoped to `40-learnings/<repo>` + `50-sessions/<repo>` and the phase additionally aborts with reason `cross-repo-staged-changes` if any staged file belongs to a different repo's namespace — so one project's mirror run can never commit another project's notes. Omitting `repo` preserves the legacy whole-directory behaviour.

### Pre-commit hook bypass (`--no-verify`)

The auto-commit deliberately commits with `--no-verify`, skipping the vault repo's pre-commit hooks. This bypass is **intentional** (issue #603), not gratuitous, for two reasons:

1. **Redundant validation.** Before committing, the phase runs `isMirrorArtifact()` on every staged path — a per-file frontmatter check for the `_generator: session-orchestrator-vault-mirror@1` marker. Any staged file lacking the marker triggers a full unstage and an `auto-commit-skipped` no-op. The committed files were written by vault-mirror's own generator, which already enforces conformant frontmatter (and the quality gate). The vault's pre-commit frontmatter / wiki-link validator would only re-check what is already guaranteed.
2. **Must not block an unattended close.** This is a machine auto-commit during session-end. An interactive, slow, or failing vault-side hook would stall the close. Bypassing it keeps session-end non-blocking.

Per `.claude/rules/development.md` Git Safety Protocol — *"Never skip hooks (`--no-verify`) unless the user has explicitly asked for it"* — the bypass is permissible here because it is **explicit, documented, and committing already-validated content**. A regression test in `tests/lib/vault-mirror/auto-commit.test.mjs` pins `--no-verify` into the commit git-args so a future silent removal is caught. If the vault's pre-commit hooks ever need to run on these commits, remove `--no-verify` together with this note and the test.

## Failure Modes

| Condition | Behaviour |
|---|---|
| Entry missing a required field | `skipped-invalid` emitted on stdout, error written to stderr, exit 0 (processing continues for remaining entries). |
| Malformed JSON on a JSONL line | Error written to stderr, exit 1 (processing stops). |
| `--vault-dir` not found | Error written to stderr, exit 2. |
| `--source` file not found | Error written to stderr, exit 2. |
| Hand-written file at target path | `skipped-handwritten` emitted on stdout, note written to stderr, file left unchanged. |
| Unknown `_generator` value in existing file | Treated as hand-written: `skipped-handwritten`, file left unchanged. |
| Unexpected filesystem write error | Error written to stderr, exit 2. |

## Examples

Mirror the sessions.jsonl for the current project into a vault:

```bash
node scripts/vault-mirror.mjs \
  --vault-dir ~/Projects/vault \
  --source .orchestrator/metrics/sessions.jsonl \
  --kind session
```

Dry-run a learnings mirror to preview actions without writing:

```bash
node scripts/vault-mirror.mjs \
  --vault-dir ~/Projects/vault \
  --source .orchestrator/metrics/learnings.jsonl \
  --kind learning \
  --dry-run
```

## Live State

**Phase 1 shipped and actively running.** As of 2026-05-09, the skill has produced:

- **847 learning notes** under `vault://40-learnings/` — each carries `_generator: session-orchestrator-vault-mirror@1` in the YAML frontmatter.
- **466 session notes** under `vault://50-sessions/` — same generator stamp.

Both target directories were verified by direct `ls | wc -l` measurement against `~/Projects/vault/`. The numeric-prefix layout (`40-learnings/`, `50-sessions/`) confirmed correct per the Target Paths spec above.

## Phase-2: Flat-Corpus Relocation (#700)

`scripts/relocate-vault-corpus.mjs` is a one-time operator utility that migrates the legacy flat vault corpus (`40-learnings/*.md` + `50-sessions/*.md` at depth 1) into the per-repo namespace subdirectories introduced by #660. Running it is **never required for vault-mirror to function** — the mirror writes to `<repo>/` subfolders since #660 automatically. Relocation is a clean-up step for vaults that accumulated notes before per-repo namespacing existed.

### Classifier logic

The classifier (`scripts/lib/vault-relocation-rules.mjs`) reads each file's YAML frontmatter:

- **Session notes** (`type: session`): derives repo from `repo:` frontmatter → `project/<slug>` tag → (optional, `--with-backfill` only) **backfill index** → `_unsorted` fallback.
- **Learning notes** (`type: learning`): derives repo from `project:` wikilink → `source:` free-text field → `source_session:` wikilink (transitive: looks up the session's own namespace) → `_unsorted` fallback.

Every derived value routes through `resolveRepoNamespace()` (the same CP1/CP6/CP10 leak-guard used by vault-mirror) so private slugs redact to `redacted-repo` and no personal home path leaks into a namespace.

### `repo:` backfill (`--with-backfill`, #700)

Most legacy session notes (~466 of 653 at last census) carry no `repo:` field, so they — and every learning that transitively points at them via `source_session:` — fall to `_unsorted`. `--with-backfill` infers the owning repo from an **authoritative** signal rather than a guess: the note's `id:` is joined against each sibling repo's own `.orchestrator/metrics/sessions.jsonl` `session_id`.

- **HIGH** — `id` found in exactly one repo's `sessions.jsonl` → that repo. (An `id` present in >1 repo is ambiguous → `SKIP`, never a guess.)
- **MEDIUM** — `id` not found, but the `branch+date` parsed from the id matches exactly one repo → that repo. (Colliding `branch+date` pairs → `SKIP`.)
- **SKIP** — no unambiguous signal → stays `_unsorted` (non-destructive).

The inference lives in the pure module `scripts/lib/vault-repo-backfill.mjs` (`inferRepoForSession` / `buildBackfillIndex` / `isBackfillDerivable`); the CLI builds the cross-repo `sessions.jsonl` index and threads it into both `buildSessionRepoIndex` (so backfilled sessions lift their transitive learnings) and the classify loop. Every inferred slug still passes through `resolveRepoNamespace()` — a mis-inferred private slug redacts to `redacted-repo` and is excluded from any confident move. Backfilled sessions feed `--derivable-only` exactly like `repo:`-carrying ones.

Non-derivable files (`_unsorted`, `redacted-repo`, `unknown-repo`) are moved to a `_unsorted/` subfolder (or skipped entirely when `--derivable-only` is set).

### Modes

| Mode | Flag | What happens |
|---|---|---|
| Preview (default) | `--dry-run` | Read-only scan — reports `would-move` lines, writes nothing. Always run this first. |
| Apply | `--apply` | Executes `git mv` (stages only — **no commit**). Operator reviews diff and commits separately. |
| Confident-only apply | `--apply --derivable-only` | Like `--apply` but skips files with `confident===false` (`_unsorted`, `redacted-repo`, `unknown-repo` destinations). |
| Backfill (opt-in) | `--with-backfill` | Infer `repo:` for repo-less session notes via the authoritative `id:` → sibling-repo `sessions.jsonl` join (HIGH/MEDIUM/SKIP). Composes with any mode; without it, output is byte-identical to before. |
| Repos root | `--repos-root <dir>` | Parent dir holding the sibling repos whose `sessions.jsonl` the backfill scans (default: parent of `--vault-dir`; `Archiv`/dot-dirs excluded). |
| Rollback | `--rollback <manifest>` | Reverses a prior `--apply` run using the reverse-manifest written at `<vault-dir>/.orchestrator/relocation-manifest-<ISO>.json`. |

**Scope filters:** `--learnings-only` / `--sessions-only` restrict to one corpus root.

### Safety model

1. **Dry-run is the default.** `--apply` must be explicit; there is no accidental write path.
2. **`--vault-dir` is required.** No default prevents silently operating on a wrong directory.
3. **Stage-only.** `--apply` calls `git mv` (which stages) but never commits. The operator owns the commit.
4. **Reverse-manifest.** Every `--apply` run writes `<vault-dir>/.orchestrator/relocation-manifest-<ISO>.json`. Pass this path to `--rollback` to undo.
5. **Structural idempotency.** Files already at depth ≥ 2 (already namespaced) are never enumerated or moved.
6. **Destination-collision guard.** If the target path already exists, the file is skipped with `reason: dest-exists` — no data is ever overwritten.
7. **Leak-guard guarantee.** Every derived namespace value runs through `resolveRepoNamespace()` before use. Private slugs redact to `redacted-repo`; files that would land in `redacted-repo/` are excluded by `--derivable-only` or left flat if the operator chooses.

### Usage

```bash
# Step 1: Preview (dry-run default)
node scripts/relocate-vault-corpus.mjs --vault-dir ~/Projects/vault

# Step 2: Move only confident files (skip _unsorted/redacted-repo)
node scripts/relocate-vault-corpus.mjs --vault-dir ~/Projects/vault --apply --derivable-only

# Step 2b: Lift coverage further by backfilling repo: for repo-less sessions (preview first)
node scripts/relocate-vault-corpus.mjs --vault-dir ~/Projects/vault --with-backfill --derivable-only          # dry-run
node scripts/relocate-vault-corpus.mjs --vault-dir ~/Projects/vault --with-backfill --derivable-only --apply  # then apply

# Step 3 (optional): Roll back if something looks wrong
node scripts/relocate-vault-corpus.mjs --rollback ~/Projects/vault/.orchestrator/relocation-manifest-<ISO>.json
```

Exit codes: `0` success (including dry-run); `1` input/arg error; `2` IO error. Data goes to stdout; diagnostics and summary go to stderr. Add `--json` for JSONL output (one record per file).

### N-root canonical guard (named vaults)

`scripts/vault-mirror.mjs` enforces that the `--vault-dir` target is a known vault (guard: git remote ends with a canonical vault suffix). Phase-2 generalises this from a single `/agents/vault` suffix to **N named suffixes** via `scripts/lib/named-vault-resolver.mjs`. When `vaults:` is declared in `owner.yaml` (see `owner-persona.md`), the guard uses `.some()` across all configured suffixes. When `vaults:` is absent, behaviour is byte-identical to the pre-#700 single-suffix path.

## Configuration

vault-mirror respects the `vault-integration` block in the project's Session Config (`CLAUDE.md`, or `AGENTS.md` on Codex CLI). The script itself does not read Session Config — the calling skill (session-end, evolve) is responsible for reading the config and deciding whether to invoke vault-mirror at all.

| Field | Type | Default | Meaning |
|---|---|---|---|
| `vault-integration.enabled` | boolean | `false` | When `false`, the calling skill skips vault-mirror entirely. |
| `vault-integration.vault-dir` | string | — | Absolute or `~`-prefixed path to the Meta-Vault root. Passed as `--vault-dir`. |
| `vault-integration.mode` | `strict`, `warn`, or `off` | `warn` | When `off`, the calling skill skips vault-mirror. When `warn`, mirror failures are surfaced as warnings but do not block session close. When `strict`, mirror failures block session close. |
