# convergence-monitoring

Monitors iterative improvement loops (autoresearch, multi-wave sessions) for convergence.
Answers: **"should this loop keep running?"** — distinct from `/evolve` (retrospective
learning) and `quality-gates` (correctness verification).

## Attribution

Inspired by cavekit's documented convergence-monitoring concept (MIT, Julius Brussee).
Implemented from spec since upstream skill not yet published as of 2026-04-30.

## File Inventory

| File         | Purpose                                                                          |
|--------------|----------------------------------------------------------------------------------|
| `SKILL.md`   | Full skill spec — phases, decision table, diagnosis, recovery suggestions         |
| `SIGNALS.md` | Signal reference — computation, thresholds, false positives, event schema         |
| `README.md`  | This file                                                                         |

## Invocation

**Explicit:** `/convergence-monitoring` — standalone assessment from current session history.

**Embedded:** Set `convergence-monitoring: true` in Session Config. `wave-executor` and
`/autoresearch` will call this skill automatically after each Impl-Core/Impl-Polish wave.

## Verdicts

| Verdict       | Meaning                                       |
|---------------|-----------------------------------------------|
| `STOP`        | Loop has converged — declare done             |
| `CONTINUE`    | Still making progress — run next wave         |
| `INVESTIGATE` | Signals ambiguous or degrading — diagnose     |
| `SKIP`        | Not enough data or monitoring disabled        |

## See Also

`skills/wave-executor/wave-loop.md` · `skills/evolve/SKILL.md` ·
`skills/quality-gates/SKILL.md`
