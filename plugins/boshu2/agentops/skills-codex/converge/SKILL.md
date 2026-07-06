---
name: converge
description: Drive a fix→re-run-judge-panel loop to
---
# $converge — bounded judge-panel convergence

> **Quick Ref:** This is a thin memo. The implementation is the Go command
> **`ao converge`** (`cli/cmd/ao/converge.go`). Do not reimplement the loop in
> shell — invoke the binary.

**YOU MUST EXECUTE THE Go COMMAND. Do not describe or re-author the loop.**

## What it does

`ao converge` runs a bounded **fix → re-run-judge-panel** loop until the judges
agree or it blocks:

- **Converged** ⇔ ≥2 distinct **non-author contexts** PASS with zero FAIL.
- **BLOCK** after **3 consecutive** failing rounds.
- **NOT-CONVERGED** when `--max-rounds` elapses with neither terminal condition.
- **KILLED** when `<dir>/.agents/rpi/KILL` appears at a round boundary.

The **independence axis is fresh CONTEXT, not model family**: the producing model
may judge its own work from a *fresh* context; only the author's context is
excluded. `--require-cross-family` is an optional strengthener (additionally
require ≥2 model families).

## The one rule that makes it trustworthy

The command runs a **two-sided canary entry gate** before any judge dispatch: it
proves the gate **rejects** a planted self-judge verdict **and accepts** a known-good
one. An empty/PASS result is a lie until proven to bite — a failed canary aborts
the run.

## How to run it

```bash
ao converge --max-rounds 5 --min-contexts 2
ao converge --require-cross-family      # add the cross-family strengthener
ao converge --help
```

## The asymmetry you must honor

The **FIX step is yours** (the orchestrating agent). The dispatched judge leg is
**non-mutating** — it emits a verdict + evidence, never edits the repo. Between
rounds: read the judges' reasons, apply the fix yourself, then re-run.

## Cross-vendor dispatch table (two legs, LAW 0)

| You are running in | Judge leg | How |
|---|---|---|
| **Claude** context | Claude → **Codex** judge | Go headless `ao codex dispatch` (Codex Pro sub), non-mutating |
| **Codex** context | Codex → **Claude** judge | **Delegated to a pane** — `codex-approval` skill / NTM Claude pane |

⛔ **LAW 0:** never a headless `claude` print-mode call, on either leg. The Codex→Claude
leg has **no Go transport** by design — it routes to an interactive pane.

## Boundary

`ao converge` emits a **CLAIM + evidence**. It never writes a binding verdict —
MTO remains the sole writer of binding verdicts. No component here decides a merge.

## See also

- `cli/cmd/ao/converge.go` — the loop, criterion, fail-tracker, transport resolver.
- `cli/cmd/ao/converge_canary.go` — the two-sided entry gate.
- `cli/internal/liveness/quorum.go` — the context-quorum floor (`CheckSignificantActionDetailed`).
- `codex-approval` — the Codex→Claude pane-delegation leg.
