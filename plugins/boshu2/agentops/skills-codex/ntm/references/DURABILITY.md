# Durability Stack — Checkpoint / Timeline / Handoff / Resume / Rollback

## Contents

- [Primitive comparison](#durability-stack--checkpoint--timeline--handoff--resume--rollback) — which to use
- [`ntm checkpoint`](#ntm-checkpoint) — snapshot pane/git/bv state
  - [What `save` captures](#what-save-captures)
  - [ID grammar](#id-grammar) — `last`, `~1`, `~N`, prefix, full
  - [Restore flags](#restore-flags-checkpointgo806-812)
  - [Export / import archive](#export--import-archive)
  - [Cross-machine handoff example](#cross-machine-handoff-example)
- [`ntm rollback`](#ntm-rollback) — apply snapshot's git + layout
- [`ntm timeline`](#ntm-timeline) — session event log
- [`ntm handoff`](#ntm-handoff) — human-readable YAML narrative
  - [Handoff file content](#handoff-file-content-handoffgo26-32)
  - [Create modes](#create-modes-handoffgo85-94)
  - [Ledger](#ledger) — rolling continuity log
- [`ntm resume`](#ntm-resume) — re-attach with handoff injection
- [Decision matrix](#decision-matrix) — goal → primitive
- [Gotchas](#gotchas)

---

NTM has five related but distinct primitives for session durability. Pick the right one.

| Primitive | Captures | When to use |
|-----------|----------|-------------|
| `checkpoint` | Pane scrollback + layout + git state + bv summary | Before a risky change, or for rollback |
| `rollback` | Applies a checkpoint's git state + pane layout | Restore code + panes from a checkpoint |
| `timeline` | Session event log (state transitions) | Post-session audit / productivity analysis |
| `handoff` | Human-readable YAML: goal / now / blockers / next | Context transfer to another operator or fresh agent |
| `resume` | Re-attaches session with handoff context injection | Pick up where an operator/agent left off |

Sources: `checkpoint.go`, `rollback.go`, `timeline.go`, `handoff.go`, `resume.go` under
`/dp/ntm/internal/cli/`.

## `ntm checkpoint`

Subcommands (`checkpoint.go:94-101`):

| Subcommand | Purpose |
|------------|---------|
| `save <session> [-m "msg"]` | Take a snapshot |
| `list [session]` | List snapshots |
| `show <session> <id>` | Full snapshot contents |
| `restore <session> [id]` | Restore panes + git state |
| `delete <session> <id>` | Delete |
| `verify <session>` | Integrity check |
| `export <session> <id>` | Portable archive |
| `import <archive>` | Import a portable archive |

### What `save` captures

- Pane configs: titles, agent types, commands (`checkpoint.go:116-120`).
- Pane scrollback — default 1000 lines, configurable via `--scrollback=N` (`checkpoint.go:200`).
- Git state: branch, commit hash, `IsDirty`, `StagedCount`, `UnstagedCount`, optional patch. Disable with `--no-git` (`checkpoint.go:201`).
- `cp.Assignments` (current bv/ntm assignments) and `cp.BVSummary`.

### Save flags

| Flag | Default |
|------|---------|
| `-m/--message <str>` | `""` |
| `--scrollback N` | 1000 lines per pane |
| `--no-git` | false |

### ID grammar

`save` emits `YYYYMMDD-HHMMSS`. `restore` accepts (`checkpoint.go:34-38`):
- Full ID: `20261230-123456`
- Prefix: `20261230`
- Aliases: `last`, `~1`, `~N` (N-th most recent)

### Restore flags (`checkpoint.go:806-812`)

- `--inject-context` re-injects scrollback into restored panes.
- `--scrollback N` limits inject size (0 = all).
- `-f/--force` skip confirmation.
- `-a/--attach` attach after restoring.
- `--skip-git-check` skip `IsDirty` validation.
- `--dry-run` preview.
- `--directory <path>` override target directory.

### Export / import archive

- `export` writes `.tar.gz` (default) or `.zip` (`--format=tar.gz|zip`).
- `--output <path>` destination.
- `--redact-secrets` strips sensitive material (`checkpoint.go:1099`).
- Manifest includes `exported_at`.
- `import <archive>` accepts `--session=<new>`, `--target-dir=<path>`, `--skip-verify`.

### Cross-machine handoff example

```bash
# Source machine
ntm checkpoint save myproject -m "pre-migration snapshot"
ntm checkpoint export myproject last \
  --output /tmp/myproject-snap.tar.gz --redact-secrets

scp /tmp/myproject-snap.tar.gz target:/tmp/

# Target machine
ntm checkpoint import /tmp/myproject-snap.tar.gz \
  --session=myproject-work --target-dir=/home/alice/work/myproject
ntm checkpoint restore myproject-work last --inject-context
```

## `ntm rollback`

`ntm rollback <session> [checkpoint-id]` (`rollback.go:19`). Applies a prior snapshot —
stashes changes, applies the stored patch, walks HEAD back to the captured commit when
present.

Flags (`rollback.go:118-122`):

- `--dry-run` — preview.
- `--no-stash` — don't stash before apply (risky).
- `--no-git` — pane-only rollback; leave git alone.
- `--last` — alias for `last` checkpoint ref.
- `--force` — skip confirmation.

ID grammar matches checkpoint: `last`, `~1`, `~N`, prefix, full.

## `ntm timeline`

Subcommands (`timeline.go:57-688`):

- `list` — all saved timelines.
- `show <session-id>` — full state transition log.
- `delete <session-id>`.
- `cleanup` — retention-based prune.
- `export <session-id>` — exportable event log.
- `stats` — storage stats.

Timelines are session-scoped audit streams: when each agent went idle/working/error,
when messages fired, when beads were claimed. Useful for post-session productivity
analysis or incident reconstruction. Distinct from checkpoints (state snapshots) and
handoffs (human narrative).

## `ntm handoff`

Human-readable YAML context transfer. Stored under
`.ntm/handoffs/<session>/<date>_<desc>.yaml`.

Subcommands (`handoff.go:40-43`): `create`, `list`, `show`, `ledger`.

### Handoff file content (`handoff.go:26-32`)

```yaml
goal: "Ship the auth refactor"
now: "PR #42 open; failing integration test on Windows"
status: in_progress
outcome: ""
decisions:
  - "Chose JWT over session cookies"
  - "Rejected refresh-token rotation for v1"
blockers:
  - "Flaky test on CI, unrelated"
next:
  - "Fix Windows test"
  - "Get final review"
files_changed:
  - internal/auth/*
git:
  branch: feat/auth
  commit: abc123
  dirty: false
```

### Create modes (`handoff.go:85-94`)

- `--goal "..."` + `--now "..."` → explicit inline.
- `--auto` → auto-generate from recent agent output.
- `--from-file <yaml>` → load pre-written.
- Interactive wizard if no flags.
- `--include-git` default true.
- `--format yaml|json|markdown`.
- `-o/--output <path>` (or `-` for stdout).

### Ledger

`.ntm/ledgers/CONTINUITY_{session}.md` (`handoff.go:156-181`) — rolling continuity log
combining the latest N handoffs.

## `ntm resume`

Re-attach a session with handoff context. Flags (`resume.go:97-104`):

| Flag | Purpose |
|------|---------|
| `--from <path>` | Specific handoff file |
| `--spawn` | Spawn fresh agents with handoff context (not just attach) |
| `--inject` | Inject context into existing panes |
| `--dry-run` | Preview |
| `--cc N` / `--cod N` / `--gmi N` | Agent counts (only with `--spawn`) |

If `--from` is omitted:

- With session name → `handoff.NewReader().FindLatest(session)` (`resume.go:165`).
- Without session → `FindLatestAny()` (`resume.go:157`).

## Decision matrix

| Goal | Use |
|------|-----|
| Snapshot before risky refactor | `checkpoint save` |
| Revert code + panes to an earlier state | `checkpoint restore` or `rollback` |
| Post-mortem: when did agents stop progressing? | `timeline show` |
| Transfer state to another operator | `handoff create` + `resume --from` |
| Move a session to a new machine | `checkpoint export` + `checkpoint import` |
| Resume after `ntm kill` | `resume --spawn` with prior handoff |
| Audit log of what happened during a session | `timeline export` |

## Gotchas

- `timeline` is session-scoped, not cross-project. Multiple sessions = multiple timelines.
- `checkpoint restore` default confirms; script flows need `-f/--force`.
- `rollback --no-stash` will lose uncommitted changes — pair it with manual stash.
- `handoff --auto` inference depends on recent pane output quality. Review before shipping.
- `resume --spawn --cc=N` ignores the prior pane count; pass it explicitly if you want to match.
