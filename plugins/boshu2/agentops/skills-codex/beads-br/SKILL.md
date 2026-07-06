---
name: beads-br
description: Local-first issue tracker (beads_rust) for
---
<!-- TOC: Critical Rules | Quick Workflow | Essential Commands | bv Integration | Plan → Beads Conversion | Issue-Lifecycle Discipline | References -->

# beads-br — Beads Rust Issue Tracker

> **Non-invasive:** br NEVER runs git commands. Sync and commit are YOUR responsibility.

## Critical Rules for Agents

| Rule | Why |
|------|-----|
| **ALWAYS use `--json`** | Structured output for parsing |
| **NEVER run bare `bv`** | Blocks session in TUI mode |
| **Sync is EXPLICIT** | `BEADS_DIR="$(ao beads dir)" br sync --flush-only` after changes |
| **Git is YOUR job** | br never runs git; `_beads/` sync is explicit |
| **No cycles allowed** | `br dep cycles` must return empty |

## Private-ledger repos — the persist_intent port contract

Some repos declare a **private bead ledger** separated from the public source
tree. The agentops repo is the canonical case; an agent that loads only this
skill (without the repo CLAUDE.md) must still honor these invariants:

| Invariant | Rule |
|---|---|
| **Indirection** | Resolve first with `ao beads dir`, then invoke as `BEADS_DIR="$(ao beads dir)" br <cmd>`. A worktree-local ledger path is valid only in the canonical checkout; linked worktrees use git's common dir to reach the canonical private ledger. |
| **Private repo** | `_beads/` is its **own git repository** (separate remote). Sync = `git -C "$(ao beads dir)" push`. |
| **Never leak** | never stage the private ledger from the host repo — bead bodies carry private context; the host repo is public and gitignores the ledger. |
| **bd is retired** | because the bd/Dolt remote-server lane was retired (2026-06-11) — do not run `bd` in a br repo; it appears only in explicitly-marked legacy notes. |
| **Prefix filter** | to prevent cross-project leakage in shared DBs, filter queries by the repo's issue prefix (e.g. `ag-`) before trusting `br ready` output. |
| **Writes fail closed** | because an empty/wrong `BEADS_DIR` makes br silently write a fallback tracker (age-gstf) — for `create`/`update`/`close`/`dep` use `BEADS_DIR="$(ao beads dir --require)" && export BEADS_DIR && br <write-cmd>`; `--require` refuses to print a path unless the directory holds a real ledger. |

This section is the `persist_intent` port contract: the skill that persists
intent owns the rules that keep that intent private and uncorrupted.

## Quick Workflow

```bash
# 1. Find work
BEADS_DIR="$(ao beads dir)" br ready --json

# 2. Claim it
BEADS_DIR="$(ao beads dir)" br update ag-abc123 --claim --json

# 3. Do work...

# 4. Complete (write commands: guarded, fail-closed resolution)
BEADS_DIR="$(ao beads dir --require)" && export BEADS_DIR && br close ag-abc123 --reason "Implemented X"

# 5. Sync to git (EXPLICIT!)
BEADS_DIR="$(ao beads dir)" br sync --flush-only
git -C "$(ao beads dir)" add -A && git -C "$(ao beads dir)" commit -m "tracker: close ag-abc123" && git -C "$(ao beads dir)" push
```

## Essential Commands

```bash
# Lifecycle
BEADS_DIR="$(ao beads dir)" br create "Title" -p 1 -t task --json
BEADS_DIR="$(ao beads dir)" br update <id> --claim --json
BEADS_DIR="$(ao beads dir)" br close <id> --reason "Done"
BEADS_DIR="$(ao beads dir)" br reopen <id>

# Querying (always use --json for agents)
BEADS_DIR="$(ao beads dir)" br ready --json
BEADS_DIR="$(ao beads dir)" br list --json
BEADS_DIR="$(ao beads dir)" br blocked --json
BEADS_DIR="$(ao beads dir)" br search "keyword"
BEADS_DIR="$(ao beads dir)" br show <id> --json

# Dependencies
BEADS_DIR="$(ao beads dir)" br dep add <child> <parent>
BEADS_DIR="$(ao beads dir)" br dep cycles
BEADS_DIR="$(ao beads dir)" br dep tree <id>

# Sync (EXPLICIT - never automatic)
BEADS_DIR="$(ao beads dir)" br sync --flush-only
BEADS_DIR="$(ao beads dir)" br sync --import-only

# System
BEADS_DIR="$(ao beads dir)" br doctor
BEADS_DIR="$(ao beads dir)" br config --list
```

## Priority Scale

| Priority | Meaning |
|----------|---------|
| 0 | Critical |
| 1 | High |
| 2 | Medium (default) |
| 3 | Low |
| 4 | Backlog |

## bv Integration

**CRITICAL:** Never run bare `bv` — it launches interactive TUI and blocks.

```bash
# Always use --robot-* flags:
bv --robot-next                      # Single top pick
bv --robot-triage                    # Full triage
bv --robot-plan                      # Parallel execution tracks
bv --robot-insights | jq '.Cycles'   # Check graph health
```

## Agent Mail Coordination

Use bead ID as thread_id for multi-agent coordination:

```python
file_reservation_paths(..., reason="ag-123")
send_message(..., thread_id="ag-123", subject="[ag-123] Starting...")
# Work...
BEADS_DIR="$(ao beads dir)" br close ag-123 --reason "Completed"
release_file_reservations(...)
```

## Session Ending Pattern

```bash
git pull --rebase
BEADS_DIR="$(ao beads dir)" br sync --flush-only
git -C "$(ao beads dir)" add -A && git -C "$(ao beads dir)" commit -m "tracker: update issues" && git -C "$(ao beads dir)" push
git push
git status  # Verify clean
```

## Plan → Beads Conversion (absorbed from /beads-workflow)

Absorbed from the retired `beads-workflow` skill (ag-ez7y6 consolidation) —
requests for `/beads-workflow`, "beads workflow", or "convert this markdown
plan into beads" route **here**.

> **Core Principle:** "Check your beads N times, implement once" — where N is
> as many as you can stomach. Beads should be so detailed and polished that you
> can mechanically unleash a swarm of agents to implement them, and it will
> come out just about perfectly.

### THE EXACT PROMPT — plan to beads conversion

```
OK so now read ALL of [YOUR_PLAN_FILE].md; please take ALL of that and elaborate on it and use it to create a comprehensive and granular set of beads for all this with tasks, subtasks, and dependency structure overlaid, with detailed comments so that the whole thing is totally self-contained and self-documenting (including relevant background, reasoning/justification, considerations, etc.-- anything we'd want our "future self" to know about the goals and intentions and thought process and how it serves the over-arching goals of the project.). The beads should be so detailed that we never need to consult back to the original markdown plan document. Remember to ONLY use the `br` tool to create and modify the beads and add the dependencies. Use ultrathink.
```

**What this creates:** tasks and subtasks with clear scope, dependency links
(what blocks what), detailed descriptions with background/reasoning/
considerations — self-contained, so the original plan is never needed again.

All other exact prompts — the short conversion variant, the polish prompts,
and the fresh-session re-establish-context sequence — live in
[PROMPTS.md](references/PROMPTS.md). What a well-formed bead looks like
(required elements, description guidelines, anti-patterns) is
[BEAD-ANATOMY.md](references/BEAD-ANATOMY.md).

### Polishing Protocol

Operating in "plan space" is far cheaper than correcting in implementation
space — that is the rationale for the whole loop:

1. Run the polish prompt ([PROMPTS.md](references/PROMPTS.md) — Polish (Standard)). Its non-negotiables: do not oversimplify, do not lose features, and ensure each bead includes comprehensive unit + e2e test scope.
2. Review changes.
3. Repeat until steady-state (typically 6-9 rounds).
4. If it flatlines, start a fresh CC session: re-establish context (read AGENTS.md/README, investigate the code), then review the beads with `br`/`bv`, then resume polishing. Exact prompts in [PROMPTS.md](references/PROMPTS.md).
5. Optionally have an alternative model (Codex/GPT) do a final cross-review round.

### Quality Checklist

Before implementation, verify each bead:

- [ ] **Self-contained** — Understandable without external context
- [ ] **Clear scope** — One coherent piece of work
- [ ] **Dependencies explicit** — Links to blocking/blocked beads
- [ ] **Testable** — Clear success criteria
- [ ] **Includes tests** — Unit and e2e tests in scope
- [ ] **Preserves features** — Nothing from plan was lost
- [ ] **Not oversimplified** — Complexity preserved where needed
- [ ] **No cycles** — `br dep cycles` returns empty

### When Beads Are Ready

Your beads are ready for implementation when:

1. **Steady-state reached** — Multiple polish rounds yield minimal changes
2. **Cross-model reviewed** — At least one alternative model reviewed
3. **No cycles** — `br dep cycles` returns empty
4. **Tests included** — Each feature has associated test beads
5. **Dependencies clean** — Graph makes logical sense

```bash
BEADS_DIR="$(ao beads dir)" br dep cycles  # must be empty
bv --robot-insights | jq '.bottlenecks'    # wave shaping: what gates the most work
BEADS_DIR="$(ao beads dir)" br list --json | jq '.issues[]? | select(.description == "")'  # no empty descriptions
```

### bd → br Migration (Docs)

`bd` itself is retired — never run it (see the persist_intent invariants
above). Use this checklist only when scrubbing legacy `bd` references from
AGENTS.md or other docs:

**Behavioral difference (only one):** `br sync` never runs git commands. After `BEADS_DIR="$(ao beads dir)" br sync --flush-only`, you must commit and push the private ledger with `git -C "$(ao beads dir)" add -A`, `git -C "$(ao beads dir)" commit`, and `git -C "$(ao beads dir)" push`.

**Transform checklist (order matters):**
1. `bd` commands → `br` commands
2. `bd sync` → `BEADS_DIR="$(ao beads dir)" br sync --flush-only` + `git -C "$(ao beads dir)" add -A` + `git -C "$(ao beads dir)" commit`
3. Do NOT assume issue IDs must change `bd-*` → `br-*` — the prefix is configurable (often remains `bd-*`).
4. Remove daemon/auto-commit references

**Verify:**
```bash
grep -c '`bd ' file.md        # must be 0
grep -c 'bd sync' file.md     # must be 0
grep -c 'br sync --flush-only' file.md  # must be > 0
```

## Issue-Lifecycle Discipline

Folded from the retired `beads` umbrella and `beads-workflow` lifecycle cards
(ag-ez7y6) — operating doctrine, not the command surface above. These keep the
tracker graph honest across sessions:

- **Live reads are authoritative.** Treat live `BEADS_DIR="$(ao beads dir)" br show` / `ready` / `list`
  output as the source of truth for current tracker state. Do NOT treat the
  exported `issues.jsonl` as the primary decision source when live `br` data is
  available — the JSONL is a git-friendly export artifact, refreshed on
  `BEADS_DIR="$(ao beads dir)" br sync --flush-only`.
- **Scoped closure proof on every close.** `br close <id> --reason` must name the
  touched files (or explicit no-file evidence artifact), the validation
  command(s) run, and the parent-reconciliation outcome. Never close a child
  bead with a generic reason like "done" or "implemented".
- **Reconcile the parent in the same session.** After closing or materially
  updating a child bead, reconcile the open parent: update stale "remaining gap"
  notes immediately, and close the parent when the child resolved its last real
  gap.
- **Narrow the umbrella issue before implementing.** If `BEADS_DIR="$(ao beads dir)" br ready --json` surfaces a
  broad umbrella bead, do not implement against vague parent wording — first
  narrow the remaining gap into an execution-ready child bead, land the child,
  then reconcile the parent.
- **Normalize stale queue items instead of skipping them.** Rewrite broad or
  partially-absorbed beads to the actual remaining gap rather than silently
  passing over them.
- **Claim-verify before dispatch (cp-hhtu).** Before claiming a bead for
  dispatch, confirm no other actor already holds it (`br show <id>` — check
  assignee/status). A race-claim on an already-claimed bead creates two workers
  on the same task — one of them will silently lose work. The ledger is the
  lock: if the bead is claimed, coordinate via Agent Mail (use the bead ID as
  the thread ID and reservation reason); do not dispatch a second worker.
- **Merged-before-close (cp-4gj6; gate cp-hxp6 enforces).** A bead is durable
  only when its branch is **merged to trunk and the commit visible on the
  canonical store**. `br close` without a merge is a protection-off state —
  the work **will** recur as an incident (it did, 2026-06-09). For
  assurance-close contexts the gate cp-hxp6 enforces this; for other contexts,
  apply it as a practice: confirm `git log --oneline origin/main` includes the
  commit SHA before closing.
- **Close with residual routed (ag-67yy).** When a close leaves a residual
  (un-merged work, deferred scope, a known gap), **route the residual to a
  successor bead in the same turn** — never accept-silently, never hold the
  parent open as a zombie. The pressure lives in the successor's priority, not
  in the open parent. Use `br close <id> --reason "Residual → <new-id>"`.
  Close-with-residual is honest; a zombie parent that never closes is the
  failure mode.
- **Append notes, never replace (cp-7fxr).** `br update <id> --notes` is an
  **append** operation — it adds to the notes, it does NOT replace existing
  notes. When adding a progress note, pass only the new content; the flag
  accumulates. A `--notes` call that silently replaces prior notes erases
  audit history — the same silent-destruction class as the close-eater
  (cp-8720) and the split-brain (cp-4gkz).
- **Fuzzy intent → bead in the same turn (cp-honb).** When a correction, idea,
  or complaint arrives mid-session, file the bead **in the same turn** with the
  verbatim words. Corrections that live only in chat evaporate. The feed IS
  the product.

## Anti-Patterns

- Running `br sync` without `--flush-only` or `--import-only`
- Forgetting sync before git commit
- Creating circular dependencies
- Running bare `bv`
- Assuming auto-commit behavior

## Storage

```
_beads/
├── beads.db        # SQLite (primary)
├── issues.jsonl    # Git-friendly export
└── config.yaml     # Optional config
```

## Troubleshooting

```bash
BEADS_DIR="$(ao beads dir)" br doctor       # Full diagnostics
BEADS_DIR="$(ao beads dir)" br dep cycles   # Must be empty
BEADS_DIR="$(ao beads dir)" br config --list
```

**Worktree error** (`'main' is already checked out`):
```bash
git branch beads-sync main
br config set sync.branch beads-sync
```

---

## References

| Topic | File |
|-------|------|
| Full command reference | [COMMANDS.md](references/COMMANDS.md) |
| Configuration details | [CONFIG.md](references/CONFIG.md) |
| Troubleshooting guide | [TROUBLESHOOTING.md](references/TROUBLESHOOTING.md) |
| Multi-agent patterns | [INTEGRATION.md](references/INTEGRATION.md) |
| Conversion/polish/fresh-session prompts | [PROMPTS.md](references/PROMPTS.md) |
| Bead structure (well-formed bead anatomy) | [BEAD-ANATOMY.md](references/BEAD-ANATOMY.md) |
