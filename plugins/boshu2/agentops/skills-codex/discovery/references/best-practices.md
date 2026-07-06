# RPI lifecycle best practices

Citation table extracted during research for `soc-bcrn` (RPI lifecycle sharpening). The lifecycle skills (`/rpi`, `/discovery`, `/crank`, `/validate`) MUST reference principles by `#` from this file — they MUST NOT duplicate the body content here. When a principle is wrong or stale, update this file and the citations fix themselves.

Source research: `.agents/research/2026-05-07-rpi-lifecycle-sharpening.md` §Objective 4.

## Table A — Principles to encode

| # | Principle | Source citation | Encode in |
|---|---|---|---|
| 1 | Explicit done criteria | `docs/context-lifecycle.md` (Gap 1) | discovery, plan, validation |
| 2 | Strict delegation over compression | `skills/shared/references/strict-delegation-contract.md`, `.agents/learnings/2026-04-19-orchestrator-compression-anti-pattern.md` | rpi, discovery, crank, validation |
| 3 | Fresh context per worker (Ralph Wiggum) | `docs/scale-without-swarms.md` | crank, swarm |
| 4 | Isolation + waves + gates (3–5 workers/wave) | `docs/scale-without-swarms.md` | crank |
| 5 | Evidence-based gates, not vibe | `docs/context-lifecycle.md` Gap 1 | validation, vibe |
| 6 | Test-first when feasible | `skills/crank/SKILL.md` (test-first mode) | crank |
| 7 | Atomic changes compose | `docs/brownian-ratchet.md` | crank |
| 8 | Reconcile, don't push | `PRODUCT.md` design principle (K8s control loops), `docs/cdlc.md` | rpi, evolve |
| 9 | Agent fungibility + filesystem results | `PRODUCT.md` operational principle #5, `skills/agent-fungibility-philosophy/SKILL.md` | rpi, crank, swarm |
| 10 | Chaos + filter + ratchet (Brownian) | `docs/brownian-ratchet.md` | rpi, evolve |
| 11 | Structured handoffs over freeform | `skills/rpi/SKILL.md` (execution-packet contract) | rpi, discovery, validation |
| 12 | Knowledge flywheel closure | `docs/context-lifecycle.md` Gap 3 | rpi, post-mortem, curate (forge mode) |
| 13 | Information flows + rules + self-organization (Meadows) | `PRODUCT.md` design principle #1 | rpi (top-of-skill framing) |
| 14 | DevOps Three Ways (flow, feedback, learning) | `docs/the-science.md`, `PRODUCT.md` design principle #2 | rpi (top-of-skill framing) |

## Table B — Anti-patterns to forbid

| # | Anti-pattern | Source citation | Forbid in |
|---|---|---|---|
| 1 | Compression of strict delegation (inline phase work) | `.agents/learnings/2026-04-19-orchestrator-compression-anti-pattern.md` | rpi, discovery, validation |
| 2 | Massive uncoordinated swarms (60+ unbounded) | `docs/scale-without-swarms.md` | crank, swarm |
| 3 | Magic-claimed compounding (without a real mechanism — the in-session loop, or the out-of-session substrate: NTM + MCP + managed-agents) | `PRODUCT.md` mission section | dream, evolve |
| 4 | Vibe-based gates without rubric / separate-context grader | `PRODUCT.md` Gap 1 | validation, vibe |
| 5 | Vendor memory follows the chat (context must reload from disk) | `PRODUCT.md` mission | rpi (orchestrator persists; phase workers DO NOT carry chat memory) |
| 6 | Coverage-padding tests | `.claude/rules/go.md`, `.claude/rules/python.md`, `skills/standards/` | crank, test |

## How to cite

When a phase skill (or sibling) wants to invoke a principle, write a single line referencing the row by number:

```markdown
See [best practices](references/best-practices.md) #2 (strict delegation) and #5 (evidence-based gates).
```

Do not paste the principle body. Citations stay short; the source-of-truth is here. Anti-patterns are cited the same way: `See [best practices](references/best-practices.md) Table B #1 (compression).`

## Mechanical enforcement

- Principle #2 + Anti-pattern #1: `scripts/check-skill-isolation.sh` lints phase-skill SKILL.md bodies for compression patterns (introduced in `soc-bcrn` UW2).
- Principle #5 + Anti-pattern #4: `skills/validate/SKILL.md` defines the per-criterion verdict shape (introduced in `soc-bcrn` UW1; folded from the retired `validation` skill).
- Principle #11: `schemas/execution-packet.schema.json` (`$defs/Criterion`) is the canonical handoff shape.
