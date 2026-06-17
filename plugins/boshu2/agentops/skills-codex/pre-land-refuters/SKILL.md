---
name: pre-land-refuters
description: Dispatch unbiased parallel refuters (Fable + Codex, read-only) before landing a large multi-surface change.
---

# pre-land-refuters (Codex)

Codex-native entry point for the `pre-land-refuters` operator skill.

The AgentOps source skill `../../skills/pre-land-refuters/SKILL.md` is the
source of truth for the refuter-panel contract: freeze a mechanical claim,
dispatch stake-free validators from two model families, fix findings forward,
re-verify pins on the landed tree. Read it first, then use `prompt.md` for the
Codex runtime profile.

## Codex Runtime Contract

- On this runtime, Codex IS one refuter lane: run the validation itself in a
  read-only sandbox; request the second-family refuter through an interactive
  ATM/NTM validator pane (see `$codex-approval`); print-mode workers are forbidden.
- Load only the claim, the pinned fixtures, and the diff under test.
- Return concrete evidence: commands run, per-fixture pass/fail, verdict
  CONFIRMED/REFUTED with numbered findings.
