# Critical Analysis Framework

Brainstorming Step 5. Always performed — scale critique depth to reversibility, blast radius, and stakes; never skip, even score-0 work gets a 2-line risk-and-mitigation.

First run the simplicity audit ([`../../shared/adopting-external-features.md`](../../shared/adopting-external-features.md)) on every candidate: an approach that fails it is `RECONSIDER` regardless of other strengths.

Pick depth by stakes: low → **MINIMAL**, medium → **MID**, high (security / data integrity / costly-to-reverse / cross-service) → **FULL**.

## MINIMAL

```
Risk: [biggest thing that could go wrong]
Mitigation: [how the approach handles it]
```

No real risk → *"Risk: Trivial — [why]. No mitigation needed."* — still write it.

## MID

Decision · Key Risk (with evidence) · Watch Out For (1-2 anti-patterns) · Recommendation PROCEED / PROCEED WITH CHANGES / RECONSIDER · Source (1-2 refs).

## FULL

Adds to MID: what you're getting right (skip if nothing, don't fabricate) · 2-5 risks each with what/why/evidence/severity CRITICAL·HIGH·MEDIUM · hidden assumptions ("assuming X, breaks if Y" — only ones that could actually break) · alternatives table (Approach/Pros/Cons/Best When) · anti-patterns ("Do NOT X because Y. Source: Z") · Verdict PROCEED / PROCEED WITH CHANGES / RECONSIDER / STOP. Source-quality tiering in `../../shared/agents/research-agent.md`.
