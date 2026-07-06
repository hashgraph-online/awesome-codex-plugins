---
name: Context-Compiler
kind: concept
status: draft
see-also: [loop, rpi, context-density-rule, citation, primitive]
---
# Context-Compiler

The capability that turns the `.agents/` corpus into the working set a [Loop](loop.md) tick needs, and absorbs the tick's exhaust back into the corpus. "AgentOps is the in-session agent operating loop and the context compiler that feeds it" is the product thesis; this entry names the noun.

## What it does at each loop edge

| Edge | Mechanism | Effect |
|---|---|---|
| **In (tick start)** | `ao lookup --query <topic>` | A decay-ranked, token-budgeted slice of the corpus, just-in-time, not stacked |
| **Out (tick end)** | Evidence, decisions, citations, verdicts written to `.agents/` under the promotion ratchet | The exhaust of this tick becomes the seed of the next |
| **Rebuild** | `ao compile` (Mine → Grow → Defrag → Lint) | Keeps the corpus fresh between ticks |

## Context is the artifact, not a byproduct

Context is the engineering artifact handed off at every loop edge, and it compounds at every level. The corpus is the moat: the thing that grows and the thing worth protecting. The [Context Density Rule](context-density-rule.md) governs what is allowed to cross an edge: every high-value token carries intent, a boundary, evidence, a decision, a constraint, or a next action, and nothing else.

## When to use

- Use **Context-Compiler** when describing how context flows through the loop. Context flows through the corpus and the bead, never through loop plumbing return values.
- The ratchet rules keep compilation honest: a learning is durable only when it compiles into a gate, a test, or a rule (knowledge becomes constraints).

## Bounded context

**BC1 Corpus.** `ao lookup` / `ao compile` / `ao maturity` are its CLI surface; the loop (BC3) consumes them.

## See also

- `loop.md` — the loop the compiler feeds and absorbs from
- `rpi.md` — the tick whose Research and Ratchet beats call the compiler
- `context-density-rule.md` — what is allowed to cross a loop edge
- `citation.md` — how corpus entries reference each other and how agents claim use
