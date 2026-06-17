---
name: converge
description: "Run converge."
---
# converge — bounded judge-panel convergence

> **Quick Ref:** Thin memo. The implementation is the Go command **`ao converge`**
> (`cli/cmd/ao/converge.go`). Do not reimplement the loop — invoke the binary.

`ao converge` runs a bounded **fix → re-run-judge-panel** loop until the judges
agree or it blocks:

- **Converged** ⇔ ≥2 distinct **non-author contexts** PASS with zero FAIL.
- **BLOCK** after 3 consecutive failing rounds.
- **NOT-CONVERGED** when `--max-rounds` elapses.
- **KILLED** when `<dir>/.agents/rpi/KILL` appears at a round boundary.

The independence axis is fresh CONTEXT, not model family. `--require-cross-family`
is an optional strengthener.

## Run it

```bash
ao converge --max-rounds 5 --min-contexts 2
ao converge --require-cross-family
```

## The asymmetry

The **FIX step is yours** (the orchestrating agent). The dispatched judge leg is
**non-mutating** — verdict + evidence only, never edits the repo.

## Codex leg (LAW 0)

In a Codex context, the Codex → **Claude** judge leg has NO headless transport:
delegate it to the `codex-approval` skill / an NTM Claude pane. Never a headless
claude print-mode call. The Claude → Codex leg uses `ao codex dispatch`.

## Canary

Before any dispatch, `ao converge` runs a two-sided canary entry gate — it proves
the gate rejects a planted self-judge verdict and accepts a known-good one. A
failed canary aborts the run. An empty/PASS result is a lie until proven to bite.

## Boundary

`ao converge` emits a CLAIM + evidence; MTO is the sole writer of binding verdicts.
