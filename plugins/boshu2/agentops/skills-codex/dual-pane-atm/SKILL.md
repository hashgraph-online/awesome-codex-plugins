---
name: dual-pane-atm
description: Repeatable mixed-model ATM duel — Opus
---
# $dual-pane-atm — Opus + Codex collaborative ATM orchestration

> **You are the single orchestrator.** One operator (this session or a lead pane)
> spawns exactly two worker panes — Claude Opus and Codex gpt-5.5 — assigns
> disjoint roles, verifies engagement, tends liveness, and synthesizes evidence.
> Workers do the work; you do logistics, reserves, and convergence. Do not let
> both panes become co-orchestrators.

Repeatable pattern for **collaborative** cross-model ATM sessions: architecture
design, build+review pairs, explore+implement splits, and lighter author+refuter
loops. Distinct from adversarial duels (`dueling-idea-wizards` — Codex skill) and from
N-way bead queues ([`$using-atm`](../using-atm/SKILL.md)).

## When to use (routing table)

| Shape | Use when | Skip when |
|---|---|---|
| **Single agent** (default) | One deliverable, one writer, fits this session | Need cross-family fresh eyes, wall-clock persistence, or provably disjoint parallel lanes |
| **`$dual-pane-atm`** (this skill) | **Exactly two** complementary roles across Claude+Codex; human attach/steer; bounded session with synthesis artifact; collaborative (not scored adversarial duel) | One-shot with no attach need (shape 0 inline); ≥3 parallel writers ([`$swarm`](../swarm/SKILL.md)); unattended bead queue ([`$using-atm`](../using-atm/SKILL.md)); pure ideation scoring duel (`dueling-idea-wizards`) |
| **`dueling-idea-wizards`** (Codex) | Adversarial cross-score (0–1000), reveal/rebuttal, consensus matrix from disagreement | Implementing/building; cooperative handoff; you already know the split |
| **`$swarm`** | ≥2 in-session parallel workers with disjoint file manifests + wave gating | Need persistent tmux panes, cross-vendor TUI steering, or hours-long runs |
| **`$using-atm`** | Unattended N-pane bead queue, `$rpi`/`$evolve` loops, fluid population | Fixed two-pane collaborative session with operator synthesis |

**Front door:** if unsure whether any ATM is warranted, run
[`$automation-shape-routing`](../automation-shape-routing/SKILL.md) first.

## Critical constraints

- **⛔ LAW 0 — never `claude -p` / `claude --print`.** Claude work runs in an
  interactive Opus pane; Codex runs via TUI goal lifecycle or `codex exec` when
  headless is explicitly requested.
- **One bead = one whole skill.** Dispatch `$rpi`, `$implement`, `$research`, etc.
  as a single invocable unit per pane — never decompose RPI phases into ATM steps.
- **Worktree-per-bead** when either lane edits tracked files. No shared checkout
  writes from panes.
- **Partition before lock.** If write-sets can be disjoint, assign ownership —
  use `am reserve` only when partition fails.
- **Evidence over agreement.** Collaborative sessions still require artifacts
  (diffs, test tails, gate output) — not mutual praise.

## Orchestrator workflow

```
1. ROUTE    → confirm dual-pane fits (table above); pick work-split pattern
2. BEAD     → optional: BEADS_DIR="$(ao beads dir)" br create/claim; bead_id = join-key
3. SPAWN    → atm spawn with --reserve paths (see references/spawn-checklist.md)
3b. VERIFY   → `atm mapping --session="$SESSION"` — confirm pane numbers before any send
4. DISPATCH → verify first lane engaged; then second lane (--codex-goal for Codex)
5. TEND     → meter lies; atm save / codex preflight; gate interrupts first
6. SYNTH    → merge artifacts → .agents/dual-pane/<session>-report.md
7. CLOSE    → am release, atm kill session, br close with evidence
```

**Checkpoint:** first lane shows engagement (artifact, `wait-goal-engaged`, or CPU)
before dispatching the second.

## Spawn contract

Minimal collaborative spawn (from CEP duel pattern):

```bash
LABEL=<short-name>   # e.g. cep-duel, claim-overlay
SESSION="agentops--$LABEL"
BEAD_ID=<optional>   # join-key for coordination ledger + br notes
# Disjoint lane globs; for smoke-only runs use e.g. /tmp/dual-pane-opus/ /tmp/dual-pane-codex/
RESERVE_GLOBS="docs/contracts/ cli/internal/"   # space-separated globs, one --reserve value

atm spawn agentops --label "$LABEL" --no-user \
  --cc=1:opus --cod=1:gpt-5.5 \
  --reserve "$RESERVE_GLOBS" \
  --no-cass-context --ready-timeout=2m --json

atm mapping --session="$SESSION"   # confirm Opus/Codex pane numbers before sends

# Opus (pane 1 when --no-user): prefer plain send; --json optional
atm send "$SESSION" --pane=1 --file packet-opus.md \
  --no-cass-check --force-non-interactive
# Advisory: if `--json` exits 1 with empty stdout, retry without `--json`

# Codex (pane 2 when --no-user): goal lifecycle — NEVER bare slash send
atm codex preflight --session "$SESSION" --pane 2 --json
atm send "$SESSION" --pane=2 --codex-goal --file packet-codex.md \
  --no-cass-check --force-non-interactive --json
atm codex wait-goal-engaged --session "$SESSION" --pane 2 --json
```

Full checklist: [references/spawn-checklist.md](references/spawn-checklist.md).

**Pane verify:** after spawn, run `atm mapping --session="$SESSION"` (or the equivalent pane-layout inspect documented in [`$using-atm`](../using-atm/SKILL.md)) and match pane numbers to the table below before `atm send`.

**`--reserve`:** pass **one** quoted flag value listing all lane globs space-separated (e.g. `--reserve "/path/opus/ /path/codex/"`). Do not pass two separate quoted arguments or bare tokens after `--reserve`.

**Pane addressing** (see checklist table):

| Session shape | Opus | Codex | AGY |
|---|---|---|---|
| **`--no-user`** (dual) | pane 1 | pane 2 | — |
| **`--no-user`** (tri-vendor) | pane 1 | pane 2 | pane 3 |
| **User pane present** | pane 2 | pane 3 | — |

With user attach, `--agent=1` == `--pane=2` (Opus). Prefer `--agent` for workers when tri-pane.

**Codex cold engage:** optional `--codex-goal` on first send may timeout before the TUI is warm. Retry the send and/or run `atm codex wait-goal-engaged` again — advisory only; does not block spawn/teardown.

## Tri-vendor extension (Opus + Codex + AGY)

Optional **three worker panes** — Claude Opus, Codex, and **AGY** (Antigravity
interactive TUI) — with **`--no-user`**. This is **not** the anti-pattern
“three-pane dual” (user attach + two workers); tri-vendor is **worker-only** and
smoke-tested as `agentops--dual-pane-agy-smoke`.

```bash
LABEL=dual-pane-agy-smoke   # or your session label
SESSION="agentops--$LABEL"
RESERVE_GLOBS="/tmp/dual-pane-opus/ /tmp/dual-pane-codex/ /tmp/dual-pane-agy/"

atm spawn agentops --label "$LABEL" --no-user \
  --cc=1:opus --cod=1:gpt-5.5 --agy=1 \
  --reserve "$RESERVE_GLOBS" \
  --no-cass-context --ready-timeout=2m --json
```

**Pane map (`--no-user`, tri-vendor):** 1 = Opus, 2 = Codex, 3 = AGY (tmux
window `:1` on typical ATM layouts).

**Sends:**

| Pane | Contract |
|---|---|
| **1 Opus** | `atm send "$SESSION" --pane=1 --file packet-opus.md` (same as dual-pane) |
| **2 Codex** | `atm codex preflight --pane 2` until `recommended_action: proceed`, then `--codex-goal --file` + `wait-goal-engaged` — do not `--codex-goal` while preflight says `wait` |
| **3 AGY** | `atm send "$SESSION" --agy --file packet-agy.md` (or `--pane=3`) — interactive AGY TUI only; **not** `agy -p`, **not** `gemini -p` |

**Verify panes:** prefer spawn `--json` `panes[]` or `tmux list-panes -t "$SESSION:1"`.
When Agent Mail is unavailable, `atm mapping --session="$SESSION"` may be empty
despite healthy panes — do not treat empty mapping as spawn failure.

**Observability gap:** `atm activity` may list only Claude + Codex lanes and omit
AGY; use tmux capture on pane 3 for AGY liveness.

Checklist block: [references/spawn-checklist.md](references/spawn-checklist.md) § Tri-vendor (+AGY).

## In-session duel (no durable panes)

For a **one-shot one-way-door decision** ("duel it out"), you don't need
persistent panes — run the same mixed-model duel **in-session**:

- Spawn ≥3 perspective subagents via the **Agent tool with `model:` override**
  (e.g. `opus` + `fable`) — each argues one opposed thesis, attacks the others,
  names its own weakness. Independent contexts = a real duel.
- Add the **cross-family voice** with `codex exec "<prompt>" </dev/null`
  (`</dev/null` dodges the exec stdin-stall). Never `claude -p` (LAW 0).
- Winnow to a SynthesisPacket; **opposed theses that converge on the same slice
  are the signal**. This is the substrate **`$discovery`'s fanout gate** runs.

Durable panes (above) for multi-session/long-running work; in-session for a
single bounded decision. `$reverse-engineer` routes one-way-door steals here.

## Work-split patterns

Pick one before spawn; declare it in the coordination ledger and both packets.

| Pattern | Opus lane | Codex lane | Reserve split |
|---|---|---|---|
| **Disjoint ownership** | Overlay/docs (`docs/contracts/`) | CLI/Go (`cli/`) | Per-lane globs |
| **Explore + write** | Read-only `$research` or architecture draft | `$implement` on scoped slice | Write lane reserves hot paths only |
| **Author + refuter** (light) | Author implementation or design doc | Read-only `$review` or refuter prompt | Author reserves write paths; refuter read-only |
| **Dual draft → synthesize** | Draft A to `DRAFT_OPUS.md` | Draft B to `DRAFT_CODEX.md` | Orchestrator-owned output dir only |

Matrix + selection guide: [references/work-split-matrix.md](references/work-split-matrix.md).

## Dispatch

- **Whole skills per pane** — e.g. `atm send … --file packet.md` where packet
  contains `$implement ag-1234` or `$rpi ag-1234 --auto`, not per-phase ATM glue.
- **Codex:** always `--codex-goal` + preflight + `wait-goal-engaged`.
- **Claude:** direct `--file` or inline prompt; interactive pane only.
- **Headless Codex** only when operator explicitly requests it — use
  [`$codex-exec`](../codex-exec/SKILL.md), not a TUI pane.

Example packets:

```markdown
# packet-opus.md
$implement ag-xyz — own docs/contracts/claim-registry.yaml only.
Write progress to br note on ag-xyz every 30m. Coordinate via am; reserve before edit.

# packet-codex.md
$implement ag-xyz — own cli/internal/gates/claim*.go only.
Run tests; post test_tail to br note. Do not touch docs/contracts/.
```

## Coordination

**Join-key:** `bead_id` (or epic id) threads br notes, reserves, and optional
ledger. Both lanes reference the same id in mail subjects and commit messages.

**Agent Mail (`am`):**

```bash
am macros start-session   # each pane once
am file_reservations reserve <proj> <agent> "<path/glob>"
# cross-lane: am mail send --from <me> --to <peer> --subject "ag-xyz: …" --body "…"
```

**Worktree-per-bead:** mandatory for implementation splits —
[shared checkout discipline](../swarm/references/shared-checkout-discipline.md).

**Optional ledger** (`.agents/dual-pane/coordination.json`):

```json
{
  "session": "agentops--cep-duel",
  "bead_id": "ag-xyz",
  "pattern": "disjoint-ownership",
  "lanes": {
    "opus": {"pane": 1, "reserve": ["docs/"], "skill": "$implement"},
    "codex": {"pane": 2, "reserve": ["cli/"], "skill": "$implement"}
  },
  "artifacts": [],
  "converged": false
}
```

Orchestrator updates `artifacts` and flips `converged` at synthesis. Ledger `pane` values assume `--no-user` (Opus 1, Codex 2); use 2/3 when a user pane is present.

## Operator tending

This skill owns **spawn + split + dispatch**; live tending defers to
[`$using-atm`](../using-atm/SKILL.md) §Observing lanes and
[`$vibing-with-ntm`](../vibing-with-ntm/SKILL.md) tick loop.

Essentials:

1. **Meter lies** — `atm activity` / context-% freeze for Codex; never respawn
   from meter alone.
2. **`atm save <session>`** — Claude pane truth; for Codex use
   `atm codex palette-state --json` / `preflight --json`.
3. **Artifacts beat narrative** — PR, branch, output file, `br show`, test tail.
4. **Gate interrupts first** — answer `ACTION NEEDED` / merge gate before broad watch.
5. **Verify lane 1 before lane 2** — boot-race drops silent sends.

## Convergence criteria

Session is done when **all** hold:

- Each lane's declared deliverable exists (file, PR, or bead note with evidence).
- No unresolved `am` reservation conflicts; write lanes released or handed off.
- For implementation splits: tests/gate pass on merged or separately verified trees.
- Orchestrator synthesis written (report or br close reason cites both lanes).
- `atm kill agentops--<label>` after capture — do not leave idle duel panes.

## Anti-patterns

- ❌ **Shared checkout writes** from both panes — worktree-per-bead always.
- ❌ **Decomposing `$rpi` into ATM steps** — dispatch the whole skill once.
- ❌ **Love-fest without evidence** — require test tails, diffs, or gate output.
- ❌ **Adversarial scoring when you need a build** — use dueling-idea-wizards instead.
- ❌ **Three-pane "dual" (user + two workers)** — that's `$using-atm` attach + workers; re-scope. **Tri-vendor worker-only** (Opus + Codex + AGY, `--no-user`) is a documented extension above — not the same anti-pattern.
- ❌ **`claude -p` for Codex parity** — interactive pane or codex exec only.

## Codex twin

Per [`AGENTS-CODEX.md`](../../AGENTS-CODEX.md): after stabilizing this skill,
manually mirror to `skills-codex/dual-pane-atm/{SKILL.md,prompt.md}` and run
`scripts/regen-codex-hashes.sh --only dual-pane-atm`. Not auto-generated.

## References

- [references/spawn-checklist.md](references/spawn-checklist.md) — preflight + first-dispatch gates
- [references/work-split-matrix.md](references/work-split-matrix.md) — pattern selection + reserve examples
- [references/dual-pane-atm.feature](references/dual-pane-atm.feature) — acceptance scenarios for preflight and work-split gates
- [`$using-atm`](../using-atm/SKILL.md) — substrate spawn, codex preflight, meter lies
- [`$vibing-with-ntm`](../vibing-with-ntm/SKILL.md) — tending tick loop once panes are live
- [`$automation-shape-routing`](../automation-shape-routing/SKILL.md) — shape 0 vs ATM vs swarm front door
