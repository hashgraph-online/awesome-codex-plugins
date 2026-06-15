---
name: curate
description: "Run curate."
---

# $curate — Canonical Miner Skill

> **Role:** miner. Input = trinity slice (transcripts, `.agents/`, `bd`, `git`). Output = skill diffs (proposed), bd updates, rare wiki entries. **Never mutates code.**

> **Status (2026-05-08):** introduced ADDITIVE in Phase 1 (m6v5.D.1 / soc-78s2v). Existing miners (dream, harvest, forge, compile, retro, post-mortem-mining, flywheel, trace, provenance, defrag) stay until Phase 3 shim conversion (m6v5.D.3). Fix-C smoke (`soc-wb2aa`) gates Phase 3.

## Modes (≤8 per Fix-F mode-flag budget)

| Mode | Purpose | Replaces (post-Phase 3) |
|---|---|---|
| `--mode=dream` | Overnight bounded INGEST→REDUCE→MEASURE on `.agents/` | `$dream` |
| `--mode=harvest` | Cross-rig promotion + post-mortem mining + flywheel rollup | `$harvest`, `$post-mortem` (mining half), `$flywheel` |
| `--mode=forge` | Per-session transcript mining (SessionEnd cadence) | `$forge` |
| `--mode=compile` | Mine→Grow→Defrag→Lint corpus pipeline | `$compile` |
| `--mode=retro` | Single-session learning capture | `$retro` |
| `--mode=defrag` | Knowledge defragmentation (overnight) | `compile-session-defrag.sh` hook |
| `--mode=watch` | In-session drift / loop detection (15-min cadence) | `research-loop-detector.sh` hook |
| `--mode=provenance` | Decision-trace + artifact-provenance walk | `$provenance`, `$recover` |

**Mode-budget assertion:** 8 modes. Adding a 9th requires demoting an existing one OR refusing the addition (per Fix-F § continuous CI gate).

**Anti-goals (hard constraints from architecture):**

- NEVER mutates source code.
- NEVER invokes `$rpi` or any code-mutating flow.
- NEVER performs git operations (no commits, branches, push, rebase, checkout).
- NEVER creates symlinks anywhere.

## Quick Start

```bash
$curate --mode=harvest                  # cross-rig promotion sweep
$curate --mode=forge                    # mine the most recent session's transcript
$curate --mode=dream --duration=8h      # overnight bounded run
$curate --mode=compile                  # rebuild .agents/ corpus
$curate --mode=retro                    # capture this session's learning
$curate --mode=defrag                   # knowledge defragmentation
$curate --mode=watch                    # in-session drift check
$curate --mode=provenance --bead=soc-X  # walk decision trace for a bead
```

## Execution

### Step 1: Resolve mode + scope

Parse `--mode`. Each mode has its own scope semantics:

| Mode | Reads | Writes | Cadence (typical loop binding) |
|---|---|---|---|
| dream | `.agents/` corpus | `.agents/overnight/<run-id>/` summary + per-iteration JSON | overnight (1×/24h) |
| harvest | `.agents/` across rigs (`~/.agents/learnings/`) | `~/.agents/learnings/` (promotion), `.agents/harvest/latest.json` | daily (1×/24h) |
| forge | runtime session transcripts or exported JSONL logs | `.agents/learnings/`, `.agents/patterns/` | per-session or 30m loop |
| compile | `.agents/` corpus | `wiki/INDEX.generated.md`, `.agents/compile/<date>.md` | weekly |
| retro | this session's transcript + recent diffs | `.agents/retro/index.jsonl` (append) | per-session (manual) |
| defrag | `.agents/` corpus | `.agents/defrag/<date>.md` (cleanup report) | overnight (1×/24h) |
| watch | last 100 lines of current session transcript | `.agents/watch/<date>.md` (advisory) | in-session 15m loop |
| provenance | `bd` graph + `git log` + `.agents/` for given anchor | `.agents/provenance/<anchor>.md` | on-demand |

### Step 2: Acquire lock (when applicable)

For `--mode=dream`: acquire `.agents/overnight/run.lock` exclusively. If held, exit with "another curator holds the lock" message; do NOT block.

For `--mode=harvest`: check the dream lock. If held, defer harvest to next loop fire.

For `--mode=forge`: per-session lock at `.agents/forge/session-<id>.lock`. Auto-released at end of run.

Other modes: no lock; concurrent invocation is safe.

### Step 3: Run the mode-specific body

Each mode delegates to a body section in this skill (see § per-mode bodies below for outline; full content moves to `references/<mode>.md` at Phase 2 startup).

### Step 4: Produce artifacts

Output is one of (priority order, per architecture knowledge-flywheel rule):

1. **Skill diffs** — proposed changes to existing skill bodies, written to `.agents/skill-diffs/<date>-<skill>.diff`. Operator approves before applying. NEVER writes to `skills/` directly.
2. **bd updates** — `bd note` or new `br create` for surfaced issues. Direct, no approval queue.
3. **Knowledge entries** — `.agents/research/`, `.agents/learnings/`, `~/.agents/learnings/` (rare; only when knowledge is generally reusable).

### Step 5: Append to LOG.md

Every mode appends one line to `.agents/LOG.md`:

```
2026-MM-DDTHH:MM:SSZ [curate --mode=<mode>] <run-id> — <short-summary> — outputs: <artifact-paths>
```

### Step 6: Report

1. Mode + scope
2. Output path(s)
3. Surfaced bd issues (if any)
4. Loop continuation hint (next-fire cadence per architecture catalog)

## Per-mode bodies (outline)

### --mode=dream

Overnight INGEST → REDUCE → MEASURE iterations until halt:
- INGEST: scan `.agents/` for new artifacts since last run
- REDUCE: dedupe + score + cluster
- MEASURE: compute knowledge-corpus health metrics
- Halt when: wall-clock budget exhausted, plateau (K sub-epsilon deltas), regression beyond per-metric floor, metadata integrity failure
- Knowledge-only; never code mutation
- Output: `.agents/overnight/<run-id>/summary.{json,md}` + per-iteration archive

Detailed body remains inline until Phase 2 extraction.

### --mode=harvest

Cross-rig promotion sweep:
- Walk `.agents/` across all rigs (paths from `~/.agents/rigs.yaml` or fleet config)
- Extract learnings/patterns/research artifacts
- Dedupe by content hash
- Promote high-confidence items to `~/.agents/learnings/` global hub
- Roll up flywheel-health metrics as byproduct
- Output: `.agents/harvest/latest.json` + promoted files in global hub

Detailed body remains inline until Phase 2 extraction.

### --mode=forge

Per-session transcript mining:
- Locate the latest runtime transcript or exported JSONL log
- Extract knowledge candidates (decisions, patterns, anti-patterns, bug fixes)
- Validate candidates against finding-registry contract
- Queue to `.agents/knowledge/pending/` for curator review
- Output: pending markdown files; bd notes for high-confidence findings

Detailed body remains inline until Phase 2 extraction.

### --mode=compile

Corpus pipeline:
- Mine: extract candidate knowledge from `.agents/`
- Grow: merge into existing taxonomy
- Defrag: collapse redundant entries
- Lint: check for orphans, contradictions, staleness
- Output: `wiki/INDEX.generated.md` (rebuilt), `.agents/compile/<date>.md` (lint report)

Detailed body remains inline until Phase 2 extraction.

### --mode=retro

Single-session learning capture:
- Read last N turns + diff summary
- Identify one durable insight (or none — exit clean)
- Append to `.agents/retro/index.jsonl`
- Optional: surface to bd as note

Detailed body remains inline until Phase 2 extraction.

### --mode=defrag

Knowledge defragmentation:
- Find duplicate entries across `.agents/` (content-hash + semantic-similarity)
- Find broken backlinks
- Find stale entries (last_cited > TTL, low hit_count)
- Output: `.agents/defrag/<date>.md` with proposed retirements (NEVER auto-deletes; operator approves)

Detailed body remains inline until Phase 2 extraction.

### --mode=watch

In-session drift detection:
- Read last 100 transcript turns
- Detect: research loops without code change, repeated grep-without-read, oscillating decisions
- Write advisory to `.agents/watch/<date>.md`; surface high-severity to bd note
- Cheap; designed for 15-min cadence

Detailed body remains inline until Phase 2 extraction.

### --mode=provenance

Decision-trace walk:
- Given anchor (bead ID, file path, or decision marker)
- Walk: bd graph (parents, blockers, refs) + git log (commits touching anchor) + `.agents/` mentions
- Output: `.agents/provenance/<anchor>.md` with chronological trace

Detailed body remains inline until Phase 2 extraction.

## Constraints (one-role-per-skill)

- **One role: miner.** Output never mutates code; always lands as proposed diffs, bd updates, or wiki entries.
- **No new modes** without dropping/merging an existing one (Fix-F mode-budget cap = 8).
- **Lock contract** — dream mode is exclusive; harvest defers when dream is
  running; other modes are safe-concurrent.

## See Also

- `skills/rpi/SKILL.md` — orchestrator
- `skills/validate/SKILL.md` — validator role (paired canonical skill)
- `.agents/research/2026-05-08-fix-F-mode-flag-budget.md` — mode-cull rationale
