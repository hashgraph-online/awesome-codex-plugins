# Installed-Skill-Edit Guard (opt-in)

A PreToolUse `Edit|Write` guard that routes an edit of an **installed skill copy**
(`*/.claude/skills/**`, `*/.codex/skills/**`, `*/.gemini/skills/**`) back to the
repo source of truth (`skills/<name>/`). AgentOps 3.0 is hookless by design —
this guard ships **inert**; you activate it with the opt-in installer.

Bead: `age-workflow-guardrail-hooks-j39.1` (keystone of `age-workflow-guardrail-hooks-j39`).

## Why it exists — a TRUE mistake-token

An `Edit`/`Write` whose target path is under `*/.claude/skills/**` has **no
legitimate form**. Those files are installed / symlinked copies:

- they are **overwritten** on `scripts/install.sh`, so an edit there is silently
  lost work, or
- they **symlink through** to the factory checkout, so an edit there writes into
  whatever branch that checkout happens to be on — never the intended source.

CLAUDE.md's standing rule is "NEVER edit `~/.claude/skills/` — edit `skills/` in
this repo." That rule is advisory context, which is delta≈0. This guard makes it
**mechanical**: it keys on the action signature (the `file_path`), not the
agent's self-narrative, so it fires even when the agent believes it is doing the
right thing.

Unlike an activity-keyed guard (which false-fires on legitimate identical forms
and gets disabled — the #511 fate), this token is syntactically detectable with
**zero false-positive surface**: only an installed-skills `file_path` matches,
and a repo doc that merely *mentions* `claude/skills` in its body lands in
`tool_input.content`, never `file_path`.

## Reversible → ROUTE, not hard-block

Editing the wrong copy is recoverable (re-do the edit against `skills/`), so the
guard **routes** rather than hard-blocks: exit 2 + a one-line stderr redirect
naming the correct `skills/<name>/` target. It does not silently swallow the edit
or deny irreversibly.

## Context-budget doctrine

Hooks are the most powerful enforcement (mechanical, can't be reasoned past) but
they pollute context — use sparingly:

- **SILENT on the happy path**: any non-installed-skills `file_path` → exit 0,
  zero stdout, zero stderr.
- Fire the one redirect **only on a real violation**, at most **once per
  session** (sentinel-gated in `$TMPDIR`), so it never repeats.
- **NEVER emit stray stdout on an exit-0 PreToolUse path** — stdout there is
  parsed as JSON and a stray line breaks the tool call. Block via exit 2 +
  stderr only.

## The guard

Ships as `skills/cc-hooks/hooks/installed-skill-edit-guard.sh`. It reads the
PreToolUse JSON on stdin, matches `tool_input.file_path` only, and derives the
repo-relative `skills/<name>/` target for the redirect message.

## Opt-in install

```bash
# user scope (~/.claude/settings.json) — the default
scripts/install-installed-skill-edit-guard.sh

# project scope (.claude/settings.json)
scripts/install-installed-skill-edit-guard.sh --project

# explicit target
SETTINGS=/path/to/settings.json scripts/install-installed-skill-edit-guard.sh
```

The installer copies the guard to `~/.claude/hooks/installed-skill-edit-guard.sh`
and adds (idempotently) a PreToolUse `Edit|Write` matcher:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "~/.claude/hooks/installed-skill-edit-guard.sh" }
        ]
      }
    ]
  }
}
```

Requires `jq` on `PATH`.

## Test it

`tests/scripts/installed-skill-edit-guard.bats` round-trips the real PreToolUse
JSON shape on stdin and proves the contract:

- **FIRE (exit 2)**: `~/.claude/skills/<x>/SKILL.md`, an absolute
  `/Users/*/.claude/skills/**`, `.codex/skills/**`, `.gemini/skills/**`.
- **SILENT (exit 0, zero output)**: repo `skills/**` (absolute or relative), an
  unrelated source file, a doc whose path mentions `claude` but not the
  installed-skills segment, and a missing `file_path`.
- **once-per-session**: first violation fires, the second self-relaxes.

```bash
bats tests/scripts/installed-skill-edit-guard.bats
```

## Known limitations

It matches the `file_path` only, so it cannot guard an edit reached through a tool
that does not populate `file_path` (e.g. a `Bash` `sed -i` into the installed
copy) — that is a `Bash` path, not an `Edit`/`Write`, and out of scope here. The
cost of a missed case is one un-routed edit; there is no false fire and no broken
tool call. Erring toward silence keeps it cheap on context and safe to run.
