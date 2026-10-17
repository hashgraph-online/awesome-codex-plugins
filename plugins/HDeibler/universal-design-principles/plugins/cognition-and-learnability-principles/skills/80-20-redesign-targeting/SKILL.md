---
name: 80-20-redesign-targeting
description: 'Use this skill when scoping a redesign or refactor — choosing which existing surfaces deserve full attention and which can be left mostly alone. Trigger when the user asks "where should we focus our redesign?", "do we need to redo all of this?", or when planning incremental design improvements with limited capacity. Sub-aspect of `80-20-rule`; read that first.'
---

# 80/20 in redesign targeting

A common failure mode of redesigns: trying to redo everything. The result is years-long projects that ship late, lose institutional context, and arrive in a state no better than incremental updates would have produced. The 80/20 rule applied to redesign: identify the surfaces that produce most of user pain or business value; concentrate redesign effort there; leave the rest alone or batch into a maintenance pass.

## How to identify high-value surfaces

### 1. Pain analysis

Where do users struggle? Sources:
- Support ticket categorization (which surfaces generate the most "how do I..." or "I can't..." tickets)
- Session recordings and rage-click analytics
- Drop-off / abandonment metrics (where users leave the funnel)
- Time-on-task for primary flows (where users get stuck)

The 80/20 cut: ~20% of surfaces typically account for ~80% of pain.

### 2. Traffic analysis

Where do users actually spend time? A beautiful but rarely-visited page deserves less polish than an ugly but constantly-used one.

Cross-reference traffic with the surface's role: a low-traffic but business-critical surface (Settings → Billing) earns redesign even if traffic alone wouldn't justify it.

### 3. Business-impact analysis

Conversion surfaces (sign-up, checkout, upgrade) often punch above their traffic weight. A 5% lift on a low-traffic checkout might exceed a 30% lift on a high-traffic blog.

### 4. Strategic-fit analysis

Some surfaces represent the brand or category position. The marketing home page, the first-run experience, the demo screen for sales. These deserve disproportionate attention because they shape perception of the whole product.

## The redesign 80/20 plan

A typical redesign plan that respects 80/20:

```
Phase 1 (the critical 20% — heavy investment)
  - Top 3–5 user-facing surfaces by pain × traffic × business impact
  - Full redesign: research, design, build, polish, A/B test
  - Often 60–70% of the project budget

Phase 2 (the meaningful tail — moderate investment)
  - Next 10–15 surfaces
  - Update to new design system; fix obvious issues; don't redesign whole flows
  - 20–30% of budget

Phase 3 (the rest — minimal investment)
  - All remaining surfaces
  - Apply new design system tokens; update components; cosmetic only
  - 10% of budget

Phase 4 (revisit)
  - Six months in: re-measure. The "rest" that wasn't redesigned might still be performing fine.
  - For surfaces that turn out to be problematic, fold into the next cycle.
```

Phases 1–3 ship over the course of the project; Phase 4 is the post-mortem that informs the next cycle.

## When the 80/20 cut hurts

- **Design system consistency.** If only 20% of surfaces get the new design and 80% don't, the product feels visually fragmented. Mitigation: even surfaces that don't get full redesign should adopt the design system tokens (color, type, spacing) for consistency.
- **Migration burden.** Mixing old and new components creates maintenance complexity. Plan for the eventual deprecation of old components even if you're not redesigning every surface that uses them.
- **Edge-case surfaces.** A surface used by 1% of users might be the *only* surface for a critical use case. The 80/20 cut shouldn't drop it.

## Anti-patterns

- **The Big Bang redesign.** Two-year project to redesign everything. Ships late, loses context, doesn't move metrics.
- **Surface-by-surface without strategy.** Each surface designed independently with no shared system. Result: visual inconsistency.
- **Pet-surface focus.** The team enjoys redesigning the most fun surfaces (marketing landing) while neglecting the highest-pain ones (settings, billing).
- **No measurement.** A redesign ships with no before/after metrics. The team can't tell if it worked.

## Heuristics

1. **The pain-traffic matrix.** Plot surfaces by pain × traffic. Concentrate redesign on the top-right quadrant.
2. **The "would users notice?" check.** For each candidate surface, ask: if we redesigned this and showed users, would they tell us it's better? If "probably not," lower priority.
3. **The conversion-impact estimate.** For business-critical surfaces, estimate revenue impact of a 10% lift. Surfaces where 10% lift is meaningful deserve A/B tested redesign; surfaces where it isn't deserve cosmetic-only updates.
4. **The post-redesign metric.** Define metrics before the redesign ships. If you can't measure improvement, you didn't redesign for the right reason.

## Related sub-skills

- **`80-20-rule`** (parent).
- **`80-20-feature-prioritization`** — applied to new feature planning rather than redesign.
- **`iteration`** (process) — redesigns benefit from iterative releases, not big bangs.
- **`factor-of-safety`** (process) — redesign with safety: A/B test, kill-switch, rollback paths.
