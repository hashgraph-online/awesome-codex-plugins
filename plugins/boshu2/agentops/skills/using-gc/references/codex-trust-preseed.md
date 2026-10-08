# Codex trust pre-seed: what `ao gc prepare` and `ao gc check` do

Detail behind the operating rule in the skill: run `ao gc prepare`, start the
city, then run `ao gc prepare` again before dispatching.

## What `prepare` stages

`prepare` verifies the exact official workflow and rig-role pins, snapshots the
upstream validation scripts and schemas unchanged inside the rig's `.gc`
runtime, installs small AgentOps-owned wrappers at the formula check paths,
selects an existing Python that can import PyYAML, and links the AgentOps skills
into the city and rig Codex sinks. Skills come from the enclosing AgentOps
checkout when one is present, otherwise from the installed skills root;
`--skills-source` pins a different directory. It never modifies the GC binary,
cache, formulas, roles or upstream pack. It does not support `--dry-run`; use
`check` for a read-only inspection.

## Trust pre-seed

`prepare` pre-seeds Codex trust for every session directory that exists when it
runs: the city and rig roots, each `.gc/agents/**` session home and each rig
worktree root. A Codex session in one of those directories then does not block
on the interactive trust dialog. Both persisted layers live in
`$CODEX_HOME/config.toml` (default `~/.codex/config.toml`):

- workspace trust, `[projects."<dir>"] trust_level = "trusted"`. Without it Codex
  silently reports the directory as having no hooks at all.
- per-hook trust, `[hooks.state."<hooks.json>:<event>:<m>:<h>"] trusted_hash =
  "sha256:..."`, which the pack's per-provider `.codex/hooks.json` would otherwise
  prompt for. Hook digests are read back from Codex's own `hooks/list`, never
  recomputed.

Hook trust needs the Codex CLI: `prepare` runs `codex app-server` (from PATH or
`--codex-bin`) to read hook identities. With no Codex CLI available it warns,
seeds workspace trust only, and a later `check` fails on every session
directory whose `.codex/hooks.json` has no recorded hook trust.

Trust is judged by value, not by the presence of a table. `prepare` appends only
missing entries and refuses, naming the entry, when one exists but does not
confer trust: an explicit `trust_level = "untrusted"`, a hook Codex reports as
changed since it was trusted, a recorded hook Codex still rejects, or a hook
recorded `enabled = false` (a disabled hook is not a trusted working hook). It
never overwrites an operator decision, and re-running is a no-op. It fails
rather than continue if Codex returns an empty or unrecognized hook list. The
trust store is never edited in place: merged content is parsed in memory first,
then installed with the CLI's durable atomic writer, so no failure path leaves
a partially written Codex config.

## What `check` verifies

`ao gc check` verifies the same pre-seed from local state only. It runs no Codex
subprocess and writes nothing: it derives each expected hook key from the
directory's own `hooks.json` and names the specific deficient directory or hook
by the same rule `prepare` seeds to. It accepts `--codex-bin` but only rejects
an explicit path that is not executable; it never runs it.

## Two named limitations

1. **`check` cannot detect a stale hash.** Because it never asks Codex, a
   recorded `trusted_hash` that no longer matches the hook's current content
   reads as satisfied and still raises the trust dialog in a real session. Only
   `prepare` sees that: Codex reports the hook as changed and `prepare` refuses.
   A green `check` means "trust is recorded", not "trust is fresh".
2. **Homes created after `prepare` are not covered.** Discovery is by filesystem
   marker, so the guarantee covers session directories that exist at `prepare`
   time. A session home Gas City materializes later still carries untrusted
   hooks on its first spawn; `prepare` names the configured agents that have no
   home yet.
