# Shared-Checkout Discipline

When `~/dev/<repo>` is contended — peer Codex agent in the same directory,
NTM swarm pane, out-of-session scheduled operating-loop or `/evolve` run on the
substrate, or operator parallel session — **never edit in the
shared tree and never leave work
uncommitted between turns.** Use a `git worktree`. Commit-or-stash
incrementally with explicit paths. Verify a clean baseline before spawning
a swarm.

This is the prerequisite check that justifies [worktree-isolation.md](worktree-isolation.md).
worktree-isolation tells you *how* to isolate; this doc tells you *when*
you must — and what fails if you don't.

## When This Fires

| Signal | Action |
|---|---|
| `git status --short` returns foreign files you did not create | Switch to a worktree before any edit |
| Handoff or memory mentions "another session was here" | Worktree, even if `git status` is clean now |
| About to spawn a swarm (`/swarm`, `/crank`, NTM panes) | `git worktree add` first; point the session symlink at the worktree |
| About to run a destructive git command (`reset --hard`, `clean -fd`, `checkout -- .`) on a dirty tree | Stop. The "dirt" may be a peer's work |
| Multi-hour session about to end with uncommitted edits | Commit explicit paths now; do not leave work hostage to the next agent |

## Failure Modes (Why The Rule Exists)

**1. Branch-deletion data loss.** A full session's deliverables — README revision, a new skill, a Gherkin spec — left uncommitted on an ephemeral branch in the shared checkout. A concurrent session merged and deleted that branch, stashing the loose files to clean its own tree. The work survived only because the other session *stashed* rather than `git clean`-ed: luck, not discipline. Recovery required `git checkout stash@{N}^3 -- <paths>` across two stashes to reassemble.

> "in a shared or agent-contended checkout, commit (or at least branch) work **incrementally as each piece completes**, never at session end. A session-long pile of uncommitted edits is hostage to every other agent's branch operations — checkout switches, merges, `reset`, `clean`, branch deletion."
— `.agents/learnings/2026-05-17-quick-commit-early-in-contended-checkouts.md`

**2. Swarm attribution confounded.** A 4-pane duel swarm spawned directly into the live shared checkout. A concurrent co-tenant agent was also working there. The co-tenant's untracked file bleed and ~6 off-scope commits got attributed — in the orchestrator's own retro — to swarm scope-drift. They were not. Root cause: every committer in the shared checkout shows as the same git author, so swarm-pane work and co-tenant work are indistinguishable after the fact.

> "before spawning any swarm — `git worktree add` a dedicated directory and point the `ntm` session symlink at *that*, not at a live shared checkout. Also run `git status --untracked-files=all` at spawn; a non-clean tree means either stash the unrelated state or pick a different worktree."
— `.agents/learnings/2026-05-17-quick-swarm-isolated-worktree-or-attribution-confounds.md`

**3. Destructive recovery temptation.** Throughout the 2026-05-17 cascade session, 33+ foreign files persisted in the shared checkout. Every git operation had to either dodge them (via worktrees, used 8+ times: `/tmp/ao-rebase`, `/tmp/ao-int2`, `/tmp/ao-fix`, `/tmp/ao-full`, `/tmp/mo-sdlc`, `/tmp/ao-ci2`, `/tmp/ao-wiki-merge`, `/tmp/ao-fmt`) or risk destroying another agent's work via `git clean -fd` or `git checkout -- .`.

> "Worktrees were the only safe path. Used 8+ times … Each was cheap to create; the collisions they avoided were not."
— `.agents/learnings/2026-05-17-shared-checkout-discipline.md`

## How To Apply

### Pre-edit check (every turn)

```bash
git status --short
# If non-empty and you did not create those files → worktree required.
```

### Real work — use a worktree

```bash
# bd/Dolt is retired — use plain git worktree (track with br). Off fresh main:
git fetch origin main
git worktree add -b <type>/<bead-id>-<slug> /tmp/<repo>-<slug> origin/main
cd /tmp/<repo>-<slug>
# do work, commit, push from here
```

### Pre-swarm — verify clean baseline

```bash
# In the target worktree (NOT the shared checkout):
git status --untracked-files=all
# Empty → safe to spawn the swarm here.
# Non-empty → either stash with a labeled message, or pick a different worktree.
```

### Committing in a shared tree (when worktree is unavailable)

```bash
# Stage explicit paths only. Foreign WIP must not ride along.
git add path/a path/b path/c
git commit -m "..."

# NEVER:
git add -A      # adds everything, including peer's WIP
git add .       # same
```

### Commit cadence

Commit as each piece completes, not at session end. A 3-hour session with
zero commits is 3 hours of work hostage to the next destructive git command
any peer agent runs.

## What This Doc Does NOT Cover

- **`mcp-agent-mail` file reservations.** That is an orthogonal application-
  level lock layer (Agent Mail's `file_reservation_paths` tool). It does not
  replace git-level discipline; it complements it. See the `agent-mail`
  skill.
- **The proposed `check-worktree-disposition.sh` CI gate.** Filed as a
  follow-up; this doc documents the operator-level rule, not the gate.
- **Worktree mechanics in detail.** See [worktree-isolation.md](worktree-isolation.md)
  for the per-backend isolation semantics, sparse-checkout config, and
  post-spawn verification.

## See Also

- [worktree-isolation.md](worktree-isolation.md) — backend-specific worktree
  mechanics; this doc is the prerequisite "when to use" rule.
- [pre-spawn-friction-gates.md](pre-spawn-friction-gates.md) — broader
  pre-spawn gate inventory; clean-baseline is one such gate.
- [conflict-recovery.md](conflict-recovery.md) — recovery once contention
  has already produced a conflict.
