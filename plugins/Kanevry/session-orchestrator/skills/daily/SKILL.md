---
name: daily
user-invocable: true
tags: [vault, daily, obsidian, pkm]
model: haiku
model-preference: sonnet
model-preference-codex: gpt-5.4-mini
model-preference-cursor: claude-sonnet-4-6
description: >
  Use this skill when creating today's daily note in the Meta-Vault (03-daily/YYYY-MM-DD.md) with valid
  vaultFrontmatterSchema-compliant YAML frontmatter. Idempotent: re-running on the
  same day opens the existing note instead of overwriting. Use when starting a work
  day, capturing scratch notes, or bootstrapping the inbox flow.
---

# Daily Skill

## Status

IMPLEMENTED 2026-04-13.

## Purpose

Bootstraps today's daily note in the Meta-Vault so the user can start capturing
thoughts, scratch work, and "done today" items without yak-shaving YAML
frontmatter each morning. The daily note is the anchor of the PKM workflow: it
is where the inbox flow starts, where daily momentum is tracked, and where
evening reflections land. Every daily note carries the same frontmatter shape
(validated by `vaultFrontmatterSchema`), which makes Dataview queries and the
vault-sync validator trivial.

## Prerequisites

- Must be invoked from inside a Meta-Vault root (cwd contains `03-daily/`) OR
  with `VAULT_DIR` resolved to the vault path (see Resolution Order below).
- `03-daily/` must already exist — the skill fails fast if it does not.
- `bash` + `sed` + `date` (always available on macOS/Linux).

### VAULT_DIR Resolution Order

1. `vault-integration.vault-dir` in Session Config (highest precedence)
2. `VAULT_DIR` environment variable
3. `$PWD` (fallback when neither is set)

Claude must read Session Config and export `VAULT_DIR` before calling
`generate.sh`. The canonical pattern (mirrors `session-end` and `evolve`):

```bash
CONFIG=$(cat .orchestrator/session-config.yaml | yq -o json)
VM_DIR=$(echo "$CONFIG" | jq -r '."vault-integration"."vault-dir" // empty')
: "${VM_DIR:=$VAULT_DIR}"
VAULT_DIR="$VM_DIR" bash /path/to/skills/daily/generate.sh
```

`generate.sh` itself reads only `VAULT_DIR` (pure bash, no Config parser).

## Algorithm

1. **Resolve `VAULT_DIR`.** Check `vault-integration.vault-dir` in Session
   Config first; fall back to the `VAULT_DIR` env var; then `$PWD`. The
   config field takes precedence — see Prerequisites for the canonical
   resolution snippet. `generate.sh` then validates: template exists (exit 2
   if not), vault dir exists (exit 3 if not), `03-daily/` exists (exit 4 if
   not).
2. **Compute today's date.** `date +%Y-%m-%d` — ISO 8601 date-only, respecting
   the system timezone (the user is in Vienna, so `Europe/Vienna` via system TZ).
3. **Target path.** `$VAULT_DIR/03-daily/YYYY-MM-DD.md`.
4. **Idempotency check.** If the target already exists, print
   `Daily note already exists: <path>` and exit 0. Never overwrite.
5. **Render template.** Read `templates/daily.md.tpl` (next to this SKILL.md)
   and substitute `{{date}}`, `{{id}}`, `{{created}}`, `{{updated}}`,
   `{{title}}`, `{{weekday}}` via `sed`. The template is literal markdown; the
   only shell interpolation happens in the `sed` substitutions.
6. **Write to target path.** Uses `sed … > "$TARGET.tmp" && mv "$TARGET.tmp"
   "$TARGET"` to avoid leaving a half-written file on disk if sed fails.
7. **Validate** (recommended but not automatic in `generate.sh`). Callers
   should run the vault-sync validator over the vault in hard mode to confirm
   schema compliance:
   ```bash
   VAULT_DIR="$VAULT_DIR" bash ../vault-sync/validator.sh --mode hard
   ```
   The BATS test suite runs this check on every run — see
   `tests/daily.bats`. If validation ever fails, the template has drifted from
   the canonical Zod schema; fix the template, do not downgrade the gate.
8. **Print success.** `Created daily note: <path>` on stdout, exit 0.

## Implementation

The deterministic path is implemented in `generate.sh` (pure bash). An
LLM-driven fallback is unnecessary: daily-note creation is a 100%
mechanical transform and a shell script is faster, cheaper, and more
reliable than an LLM round-trip. Recommended invocation:

```bash
# Resolve vault dir from Session Config first, env var as fallback:
CONFIG=$(cat .orchestrator/session-config.yaml | yq -o json)
VM_DIR=$(echo "$CONFIG" | jq -r '."vault-integration"."vault-dir" // empty')
: "${VM_DIR:=$VAULT_DIR}"
VAULT_DIR="$VM_DIR" bash ~/Projects/session-orchestrator/skills/daily/generate.sh
```

Or, if `VAULT_DIR` is already set in the environment and Session Config has
no `vault-integration.vault-dir` override:

```bash
VAULT_DIR=~/Projects/vault bash ~/Projects/session-orchestrator/skills/daily/generate.sh
```

Or, if the user's cwd is already the vault:

```bash
cd ~/Projects/vault && bash ~/Projects/session-orchestrator/skills/daily/generate.sh
```

## Template Placeholders

| Placeholder   | Example            | Format                                                     |
| ------------- | ------------------ | ---------------------------------------------------------- |
| `{{date}}`    | `2026-04-13`       | ISO 8601 date (`YYYY-MM-DD`), also used inside the `id`    |
| `{{created}}` | `2026-04-13`       | ISO 8601 date (`YYYY-MM-DD`) — matches `isoDateRegex`      |
| `{{updated}}` | `2026-04-13`       | ISO 8601 date (`YYYY-MM-DD`) — matches `isoDateRegex`      |
| `{{title}}`   | `Daily 2026-04-13` | Human-readable heading, `Daily YYYY-MM-DD`                 |
| `{{weekday}}` | `Montag`           | Full German weekday name (lookup table keyed on `date +%u`) |

Note: `{{id}}` is **not** a separate placeholder — the template inlines
`id: daily-{{date}}` so there is only one date substitution. This keeps
template rendering to a single `sed` pass and prevents drift between `id`
and filename.

The German weekday is computed via a hardcoded lookup (1=Montag,
2=Dienstag, ..., 7=Sonntag) rather than `LC_TIME=de_DE.UTF-8 date +%A`
because not every macOS install has the `de_DE.UTF-8` locale compiled.

## Integration with vault-sync

The template **must** stay in sync with `vaultFrontmatterSchema`. The canonical
schema lives at:

```
~/Projects/projects-baseline/packages/zod-schemas/src/vault-frontmatter.ts
```

Required fields produced by the template: `id`, `type`, `created`, `updated`.
Optional-but-useful fields: `title`, `tags`, `status`. The `type` is hardcoded
to `daily` (one of the valid values in `vaultNoteTypeSchema`). The `id` is
`daily-YYYY-MM-DD` which is kebab-case and 16 chars — passes
`slugRegex.min(2).max(128)`.

The BATS suite runs the vault-sync validator end-to-end (`bats tests/daily.bats`
→ test 8), so any drift between the template and the schema breaks the build
of this skill, not of the vault that consumes it.

## Idempotency Guarantee

Running `generate.sh` twice on the same day is a no-op when the existing
file is valid:

1. The first run creates `$VAULT_DIR/03-daily/YYYY-MM-DD.md`.
2. The second run finds the file, confirms it is non-empty and starts with
   `---\n` (valid YAML frontmatter opener), prints
   `Daily note already exists: <path>`, and exits 0.

If the existing file is 0 bytes or lacks the `---\n` opener (e.g. a previous
run crashed between the `$TARGET.tmp` write and the `mv`), the corrupt file
is removed and the note is re-created cleanly.

The file is **never** re-rendered when intact. This matters because the user
edits the daily note throughout the day (ticking checkboxes, filling in the
Scratch section, etc.) and re-invoking `/daily` from anywhere — a later
session, a different tool, a keybind — must not destroy that work.

Verified by `tests/daily.bats` test 5: hash-compares the file before and after
a second `generate.sh` invocation.

## Anti-Patterns

- **DO NOT overwrite existing daily notes.** Re-running `/daily` is routine;
  losing the day's scratch notes is catastrophic. The idempotency check is
  load-bearing.
- **DO NOT hardcode the vault path.** `VAULT_DIR` is the contract. Hardcoding
  `~/Projects/vault` breaks tests, breaks any future multi-vault setup, and
  couples this skill to one user's machine.
- **DO NOT skip the post-write validation step.** If the BATS suite stops
  running the vault-sync validator, template drift will quietly ship invalid
  frontmatter into the vault and only be caught at the next session-end gate.
- **DO NOT use `LC_TIME` for the weekday.** The locale is not guaranteed to
  exist. Use the hardcoded lookup table.
- **DO NOT add `sed`-unsafe characters to the template.** The placeholders use
  `|` as the sed delimiter; if you add a `|` to any substituted value, sed
  will break. Keep substitutions plain.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success (created) or idempotent skip (already exists and valid) |
| 1 | Unexpected runtime failure (`set -e` caught an unhandled error) |
| 2 | Infra error: template file not found at `$SCRIPT_DIR/templates/daily.md.tpl` |
| 3 | Config error: `VAULT_DIR` does not exist as a directory |
| 4 | Vault structure error: `$VAULT_DIR/03-daily/` directory is missing |

## Files

- `SKILL.md` — this file.
- `generate.sh` — the POSIX bash implementation of the algorithm above.
- `templates/daily.md.tpl` — the daily-note template with `{{placeholder}}`
  markers.
- `tests/daily.bats` — 8 BATS test cases covering creation, substitution,
  idempotency, missing-dir errors, and end-to-end schema validation via
  vault-sync.

## Testing

From the skill directory:

```bash
bats tests/daily.bats
```

Expected: `8/8 passing`. Test 8 runs the vault-sync validator over a fixture
vault that contains only the freshly-generated daily note, proving end-to-end
schema compliance.
