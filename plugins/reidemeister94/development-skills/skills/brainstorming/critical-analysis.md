# Critical Analysis Framework

Reference for brainstorming Step 5. **Always performed** — intensity scales with complexity score. Never SKIP.

Applies Iron Rules Principle 0 (be critical) and Principle 3 (simplicity by default). Every approach gets a simplicity audit before a recommendation.

---

## Simplicity Audit (Principle 3) — every approach

Before scoring complexity, answer for each candidate:

1. **Overlap:** Does an existing mechanism cover >50% of this need? Yes → reject or fold in.
2. **Reduction:** Can this be one fewer file / abstraction / config / dependency? Yes → do it.
3. **Earn-your-place:** Would removing it cause a real failure (not hypothetical)? No → don't add it.

An approach that fails the simplicity audit is `RECONSIDER` regardless of other strengths.

---

## Complexity Score (0-10)

Score 0-2 per dimension. Sum them.

| Dimension | 0 | 1 | 2 |
|-----------|---|---|---|
| **Reversibility** | Trivial (rename, format) | Moderate (new feature, refactor) | Costly/impossible (architecture, public API, migration) |
| **Blast radius** | Single file/function | Multiple files, one service | Multiple services / teams / consumers |
| **Ambiguity** | Single correct approach | Multiple valid approaches | Genuinely uncertain, trade-off dependent |
| **Novelty** | Done this exact thing before | Similar but different context | First time, unfamiliar domain/tech |
| **Stakes** | Low (cosmetic, internal) | Moderate (user-facing, performance) | High (security, data integrity, compliance) |

### Intensity threshold

| Score | Analysis depth |
|-------|----------------|
| 0-5 | **MINIMAL** — 2 lines (biggest risk + mitigation) |
| 6-7 | **MID** — 1-2 highest-risk dimensions |
| 8-10 | **FULL** — complete framework below |

**No SKIP.** Even score-0 work gets a 2-line risk-and-mitigation statement.

---

## MINIMAL (score 0-5)

```
Risk: [one sentence — biggest thing that could go wrong]
Mitigation: [one sentence — how the approach handles it]
```

No real risk → state *"Risk: Trivial — [why]. No mitigation needed."* — still write it.

---

## MID (score 6-7)

```
Decision: [one sentence]
Key Risk: [biggest risk with evidence]
Watch Out For: [1-2 anti-patterns]
Recommendation: PROCEED / PROCEED WITH CHANGES / RECONSIDER — [one sentence]
Source: [1-2 references]
```

---

## FULL (score 8-10)

```
The Request: [one-sentence restatement]
What You're Getting Right: [solid aspects — skip if nothing, don't fabricate]

Risks & Weaknesses:
  [RISK N: Name]
  - What: [description]
  - Why it matters: [impact if materialized]
  - Evidence: [citation — URL or source]
  - Severity: CRITICAL / HIGH / MEDIUM
  [2-5 risks, quality over quantity]

Hidden Assumptions: "You are assuming [X]. This breaks if [Y]." [only assumptions that could actually break]

Alternatives Considered:
  | Approach | Pros | Cons | Best When |

Anti-Patterns to Avoid: "Do NOT [X] because [Y]. Source: [Z]"

Verdict: PROCEED / PROCEED WITH CHANGES / RECONSIDER / STOP
  - PROCEED: sound, risks manageable
  - PROCEED WITH CHANGES: direction right, adjustments needed [list]
  - RECONSIDER: significant risks or better alternatives [explain]
  - STOP: fundamental flaw [explain]
  [2-3 sentence rationale]

Sources: [numbered list with URLs — use the source-quality tiering in `../../shared/agents/research-agent.md`]
```
