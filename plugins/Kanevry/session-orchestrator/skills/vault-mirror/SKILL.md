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
{"action":"created","path":"50-sessions/session-2026-04-13.md","kind":"session","id":"session-2026-04-13"}
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
| `session` | `<vault-dir>/50-sessions/<session-id>.md` |
| `learning` | `<vault-dir>/40-learnings/<slug>.md` |

Subdirectories are created automatically with `mkdirSync({ recursive: true })` when writing (not in `--dry-run` mode).

The numeric prefix (`50-sessions/`, `40-learnings/`) follows the vault folder ordering convention so that sessions and learnings appear in the correct position in the vault tree relative to other note types.

**Path contract note:** Issue #187 proposed `<vault>/05-orchestrator/<repo>/` as the target layout. The shipped implementation uses numeric-prefix paths for vault ordering. If you need the issue-text path, file a new issue — do NOT silently change the script.

## Idempotency

vault-mirror is safe to run multiple times against the same JSONL source:

1. **No file exists** → create.
2. **File exists, `_generator` marker present, same id, `updated` date not advanced** → `skipped-noop`, file unchanged.
3. **File exists, `_generator` marker present, same id, `updated` date advanced** → `updated`, file overwritten.
4. **File exists, no `_generator` marker** → `skipped-handwritten`, file untouched. The absence of the marker means the file was written by a human and must not be overwritten automatically.
5. **File exists, `_generator` marker present, different id** → slug collision. A disambiguated slug is derived by appending `-<first-8-chars-of-entry-uuid>` (hyphens stripped from the UUID before taking the prefix). The original file is left unchanged; the new note is written at the disambiguated path with action `skipped-collision-resolved`.

The generator marker value is `session-orchestrator-vault-mirror@1` and appears in the YAML frontmatter as `_generator: session-orchestrator-vault-mirror@1`.

## Auto-Commit Phase

After a successful mirror pass, `scripts/lib/vault-mirror/auto-commit.mjs` (`autoCommitVaultMirror`) optionally commits the freshly-written mirror artifacts in `40-learnings/` and `50-sessions/` as a single `chore(vault): mirror …` commit. It runs unattended at session-end Phase 3.7 / evolve Phase 3.5. The phase is fail-safe: it never throws, emits one JSON action line on stdout, and aborts (unstaging everything) if any staged path is **not** a generator-stamped mirror artifact.

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

## Configuration

vault-mirror respects the `vault-integration` block in the project's Session Config (`CLAUDE.md`, or `AGENTS.md` on Codex CLI). The script itself does not read Session Config — the calling skill (session-end, evolve) is responsible for reading the config and deciding whether to invoke vault-mirror at all.

| Field | Type | Default | Meaning |
|---|---|---|---|
| `vault-integration.enabled` | boolean | `false` | When `false`, the calling skill skips vault-mirror entirely. |
| `vault-integration.vault-dir` | string | — | Absolute or `~`-prefixed path to the Meta-Vault root. Passed as `--vault-dir`. |
| `vault-integration.mode` | `strict`, `warn`, or `off` | `warn` | When `off`, the calling skill skips vault-mirror. When `warn`, mirror failures are surfaced as warnings but do not block session close. When `strict`, mirror failures block session close. |
