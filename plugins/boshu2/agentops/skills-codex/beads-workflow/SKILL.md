---
name: beads-workflow
description: Use when converting markdown plans into br
---
<!-- TOC: Quick Start | Conversion Prompt | Polishing | bd → br Migration | Quality Checklist | Lifecycle Disciplines | When Beads Are Ready | Validation | References -->

# Beads Workflow — From Plan to Actionable Tasks

> **Core Principle:** "Check your beads N times, implement once" — where N is as many as you can stomach.
>
> Beads are so detailed and polished that you can mechanically unleash a big swarm of agents to implement them, and it will come out just about perfectly.

This skill is the **conversion and shaping doctrine** — plan → beads, dependency/wave shaping, polish, lifecycle. It does NOT re-document the `br`/`bv` command surface: both binaries self-describe (`br --help`, `bv --help`, plus the beads_rust README and the `beads-br` / `beads-bv` skills). One hard rule worth front-loading: **never run bare `bv`** — it launches an interactive TUI; agents use `bv --robot-*` surfaces only.

## Quick Start

```bash
br init              # 1. Initialize beads in project
                     # 2. Convert plan to beads (THE EXACT PROMPT below)
                     # 3. Polish iteratively, 6-9 rounds, until steady-state
br dep cycles        # 4. Validate: must be empty
bv --robot-insights  #    ...and check graph health
bv --robot-next      # 5. Begin implementation: get first bead
```

## THE EXACT PROMPT — Plan to Beads Conversion

```
OK so now read ALL of [YOUR_PLAN_FILE].md; please take ALL of that and elaborate on it and use it to create a comprehensive and granular set of beads for all this with tasks, subtasks, and dependency structure overlaid, with detailed comments so that the whole thing is totally self-contained and self-documenting (including relevant background, reasoning/justification, considerations, etc.-- anything we'd want our "future self" to know about the goals and intentions and thought process and how it serves the over-arching goals of the project.). The beads should be so detailed that we never need to consult back to the original markdown plan document. Remember to ONLY use the `br` tool to create and modify the beads and add the dependencies. Use ultrathink.
```

**What this creates:** tasks and subtasks with clear scope, dependency links (what blocks what), detailed descriptions with background/reasoning/considerations — self-contained, so the original plan is never needed again.

All other exact prompts — the short conversion variant, the polish prompts, and the fresh-session re-establish-context sequence — live in [PROMPTS.md](references/PROMPTS.md). What a well-formed bead looks like (required elements, description guidelines, anti-patterns) is [BEAD-ANATOMY.md](references/BEAD-ANATOMY.md).

## Polishing Protocol

Operating in "plan space" is far cheaper than correcting in implementation space — that is the rationale for the whole loop:

1. Run the polish prompt ([PROMPTS.md](references/PROMPTS.md) — Polish (Standard)). Its non-negotiables: do not oversimplify, do not lose features, and ensure each bead includes comprehensive unit + e2e test scope.
2. Review changes.
3. Repeat until steady-state (typically 6-9 rounds).
4. If it flatlines, start a fresh CC session: re-establish context (read AGENTS.md/README, investigate the code), then review the beads with `br`/`bv`, then resume polishing. Exact prompts in [PROMPTS.md](references/PROMPTS.md).
5. Optionally have an alternative model (Codex/GPT) do a final cross-review round.

## bd → br Migration (Docs)

Use this when you see legacy `bd` references in AGENTS.md or docs.

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

## Quality Checklist

Before implementation, verify each bead:

- [ ] **Self-contained** — Understandable without external context
- [ ] **Clear scope** — One coherent piece of work
- [ ] **Dependencies explicit** — Links to blocking/blocked beads
- [ ] **Testable** — Clear success criteria
- [ ] **Includes tests** — Unit and e2e tests in scope
- [ ] **Preserves features** — Nothing from plan was lost
- [ ] **Not oversimplified** — Complexity preserved where needed
- [ ] **No cycles** — `br dep cycles` returns empty

## Lifecycle disciplines (2026-06-09, cards 17–20, cp-hhd7)

### Claim-verify before dispatch (card 3, cp-hhtu)

Before claiming a bead for dispatch, confirm no other actor already holds it (`br show <id>` — check assignee/status). A race-claim on an already-claimed bead creates two workers on the same task — one of them will silently lose work. The ledger is the lock: if the bead is claimed, coordinate via Agent Mail (use the bead ID as the thread ID and reservation reason), do not dispatch a second worker.

### Merged-before-close (card 17, cp-4gj6; POLICY → gate cp-hxp6 enforces)

A bead is durable only when its branch is **merged to trunk and the commit visible on the canonical store**. `br close` without a merge is a protection-off state — the work **will** recur as an incident (it did, 2026-06-09). For assurance-close contexts the gate cp-hxp6 enforces this; for other contexts, apply it as a practice: confirm `git log --oneline origin/main` includes the commit SHA before closing.

### Close with residual routed (card 19, ag-67yy)

When a close leaves a residual (un-merged work, deferred scope, a known gap), **route the residual to a successor bead in the same turn** — never accept-silently, never hold the parent open as a zombie. The pressure lives in the successor's priority, not in the open parent. Use `br close <id> --reason "Residual → <new-id>"`. Close-with-residual is honest; a zombie parent that never closes is the failure mode.

### Append notes, never replace (card, cp-7fxr)

`br update <id> --notes` is an **append** operation — it adds to the notes, it does NOT replace existing notes. When adding a progress note, pass only the new content; the flag accumulates. A `--notes` call that silently replaces prior notes erases audit history — the same silent-destruction class as the close-eater (cp-8720) and the split-brain (cp-4gkz).

### Fuzzy intent → bead in the same turn (card 20, cp-honb)

When a correction, idea, or complaint arrives mid-session, file the bead **in the same turn** with the verbatim words. Corrections that live only in chat evaporate. The feed IS the product.

## When Beads Are Ready

Your beads are ready for implementation when:

1. **Steady-state reached** — Multiple polish rounds yield minimal changes
2. **Cross-model reviewed** — At least one alternative model reviewed
3. **No cycles** — `br dep cycles` returns empty
4. **Tests included** — Each feature has associated test beads
5. **Dependencies clean** — Graph makes logical sense

## Validation

```bash
BEADS_DIR="$(ao beads dir)" br dep cycles # must be empty
bv --robot-insights | jq '.Cycles'       # graph health
bv --robot-insights | jq '.bottlenecks'  # wave shaping: what gates the most work
BEADS_DIR="$(ao beads dir)" br list --json | jq '.issues[]? | select(.description == "")'  # no empty descriptions
```

After any bead mutation session, flush and commit the private ledger: `BEADS_DIR="$(ao beads dir)" br sync --flush-only && git -C "$(ao beads dir)" add -A && git -C "$(ao beads dir)" commit`.

## Troubleshooting

For worktree/sync-branch errors, health checks, and full diagnostics, see [TROUBLESHOOTING.md](references/TROUBLESHOOTING.md). Quick health check: `BEADS_DIR="$(ao beads dir)" br config list`, `BEADS_DIR="$(ao beads dir)" br dep cycles`, `which br`.

## References

| Topic | Reference |
|-------|-----------|
| All prompts (conversion, polish, fresh-session) | [PROMPTS.md](references/PROMPTS.md) |
| Bead structure | [BEAD-ANATOMY.md](references/BEAD-ANATOMY.md) |
| Troubleshooting | [TROUBLESHOOTING.md](references/TROUBLESHOOTING.md) |
| br command reference | `br --help` or beads_rust README |
| BV triage / robot surfaces | `bv --help`; `beads-bv` skill |
| Coordination (reservations, threads) | `agent-mail` skill |
