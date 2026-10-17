---
name: 80-20-feature-prioritization
description: 'Use this skill when scoping a roadmap, prioritizing features, planning an MVP, or deciding what to ship and what to defer. Trigger when the user asks "what should we build next?", "is this feature worth it?", "should we ship feature X?", or when reviewing a feature backlog. Sub-aspect of `80-20-rule`; read that first.'
---

# 80/20 in feature prioritization

The most direct application of the 80/20 rule: deciding which features to invest in. Most products accumulate features over time; many of those features see little use. The discipline is identifying the critical fraction worth deepening and the long tail worth either tucking or removing.

## The prioritization framework

For each feature (proposed or existing), gather:

### 1. Usage signal

If the feature exists: how many users engage with it? How often? Is engagement growing or declining?

If the feature is proposed: how many users say they want it? Is that signal coming from a vocal minority or a representative sample?

### 2. Value signal

When the feature is used, how much value does it produce? A rarely-used feature that produces enormous value when used (year-end tax export) may be more important than a frequently-used one that produces marginal value (a counter widget).

### 3. Effort signal

What does it cost to build, maintain, support, and document?

### 4. Strategic signal

Does the feature reinforce a competitive position, retain a key customer segment, or enable future capabilities?

The 80/20 cut isn't pure usage — it weights usage by value. A rarely-used essential feature stays in the critical fraction. A frequently-used decorative one might not.

## Decision matrix

A simple 2×2 to organize:

```
                    Low value          High value
                    ───────────         ──────────
Low effort     │  Cleanup later   │   Ship now
High effort    │  Don't build     │   Major investment
```

The tricky cases are the diagonals: low-effort + low-value tasks accumulate as "death by a thousand cuts" if not pruned; high-effort + high-value tasks need ruthless scoping or they slip schedule.

## Roadmap shaping

The 80/20 view of a roadmap:

- **The critical 20%** of planned work should account for ~80% of expected user impact. If the planned work is spread evenly across many small features, you're probably underweighting the few that matter most.
- **The trailing 80%** of planned work should be either skipped or radically scoped down.

A useful exercise: take a quarterly roadmap. For each item, estimate user impact and engineering effort. Sort by impact-per-effort. Cut the bottom half. The team's quarter is suddenly half the size with most of the impact preserved.

## When the 80/20 cut hurts

- **Power-user retention.** A feature only 5% of users touch may be the reason that 5% (often the highest-paying segment) chose your product.
- **Compliance and accessibility.** Required by law or ethics; can't be dropped.
- **Foundational capability.** A feature whose value is in *enabling* other features. Search isn't valuable in itself; it's valuable because it makes everything findable.
- **Trust signals.** Audit logs, exportable data, account deletion. Rarely used directly but their presence reassures prospects.

These deserve a different evaluation than pure-usage 80/20 would suggest.

## Roadmap anti-patterns

- **The feature factory.** Every quarter ships 10 features. Most are small. None move metrics. Time fragments across all of them.
- **The pet feature.** A senior leader's favorite that doesn't show up in user research but ships every quarter.
- **The "and one more thing."** A small tweak added to a major feature that doubles its scope.
- **The unfinished long tail.** Features shipped but never polished, growing into a maintenance burden.
- **The roadmap by request.** Building features customers asked for without checking whether they reflect underlying needs (often the underlying need is met by a different feature you already have).

## Worked example: pruning a settings page

A SaaS product's settings page has 38 controls. Usage analytics:

- 7 controls used by ≥50% of users monthly.
- 14 used by 10–50%.
- 17 used by <10%.

Of the trailing 17:
- 5 are needed for compliance (audit log, data export, account deletion). Keep.
- 4 are integrations with services the product team is winding down. Remove from settings; deprecate.
- 8 are legacy options most users have never touched. Move to "Advanced" disclosure; review for removal in a future cycle.

Result: settings page now shows ~7+5 (12 controls) primary; 14 secondary; rest tucked. Maintenance burden drops; common use is faster.

## Heuristics

1. **The "what does the data say?" check.** Usage analytics before opinion. If the data isn't available, instrument first; decide later.
2. **The "who would scream?" test.** For features in the trailing 80%, ask. Each scream is a candidate to retain (or relocate); silence is permission to cut.
3. **The "would we build this today?" test.** For each existing feature, imagine you were starting fresh. Would you build it? If no, it's a candidate for deprecation.
4. **The retention attribution.** Pair feature usage with retention/expansion data. Features used by retained users may be more valuable than raw usage suggests.

## Related sub-skills

- **`80-20-rule`** (parent).
- **`80-20-redesign-targeting`** — the within-existing-product version of the same prioritization.
- **`hicks-law`** — every feature is an option; cutting features cuts decision cost.
- **`progressive-disclosure`** — alternative to cutting: tucking.
