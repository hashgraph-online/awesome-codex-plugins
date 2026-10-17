---
name: ockhams-feature-pruning
description: 'Prune accumulated complexity from a product — features, options, settings, code paths that no longer earn their place. Use when auditing a mature product, reducing surface area, simplifying complex workflows, or evaluating whether to remove low-usage features. Pruning is harder than adding because users (often a small but vocal minority) resist removal even when usage data justifies it. The skill is identifying what to prune, deciding how, and managing the transition.'
---

# Ockham's Razor — feature pruning

Feature pruning is the discipline of removing things that no longer earn their place. Most products accumulate features, options, and complexity over time; periodic pruning is necessary to prevent the product from becoming unusable through accumulated weight.

Pruning is hard. Users (often a small but loud minority) resist removal even when most users don't use the feature. Engineers may have spent significant effort building it. Marketing has highlighted it. The cost of removal feels concrete; the benefit (freedom from maintenance, simpler product, easier evolution) is diffuse.

But pruning, done well, is one of the highest-leverage product activities. A clean product evolves faster, costs less to maintain, is easier for new users to learn, and tends to keep its core users happier.

## What's a candidate for pruning

A feature, option, or piece of UI is a pruning candidate when one or more of:

**Low usage.** Below 1% of users (often below 5%) without clear strategic justification.

**High maintenance cost.** Bugs, support tickets, broken integrations.

**Dependency liability.** Depends on third-party services, deprecated APIs, or aging infrastructure.

**Confused with other features.** Users don't know which to use; designers can't articulate the difference.

**Originally built for a use case that's no longer relevant.** The customer who requested it no longer exists; the workflow it supported has changed.

**Functionality covered by other features.** Redundant with newer, better-designed capabilities.

**Cognitive overhead disproportionate to value.** A setting that adds choice but most users don't engage with.

**Holds back evolution.** Removing it would unlock significant simplification or new capability.

## What's not a candidate for pruning

Even if usage is low, don't prune when:

**Critical for a small but high-value audience.** The 1% who use the feature might be your most valuable customers.

**Required for compliance, legal, or accessibility.** The feature may serve a small audience but be essential for some context.

**Required for a workflow that doesn't have an alternative.** Even rare workflows shouldn't be eliminated unless an alternative exists.

**Strategic for future direction.** Some features are bets on a future use case; usage may grow.

**Underutilized due to discoverability, not lack of value.** Sometimes a low-usage feature is one users don't know exists; promotion may be a better answer than pruning.

## The pruning process

A disciplined pruning process:

**1. Audit.** List candidates based on usage data, support patterns, and engineering input.

**2. Investigate each candidate.** For each: who uses it, why, what would they do without it? Talk to representative users if possible.

**3. Categorize:**
- Prune outright (low usage, no important users dependent).
- Prune with migration (low usage but some users dependent; provide alternatives).
- Defer (currently rare but strategically important).
- Keep (justified despite low usage).

**4. Plan the migration for "prune with migration" candidates.** What's the alternative for affected users? How will you communicate? What's the timeline?

**5. Execute.** Announce, deprecate, remove. Each step has its own timeline.

**6. Measure.** After pruning, did the predicted benefits materialize? Are affected users staying or churning?

## Pruning patterns

**Soft removal.** Remove from default UI but keep accessible (e.g., behind a "legacy" menu). Lower cost; users who depend can still find it.

**Hard removal.** Remove entirely. Higher cost but cleaner result.

**Replacement.** Remove the old feature; provide a better alternative. Requires the alternative to actually serve the use case.

**Deprecation announcement.** Announce removal date in advance; let users prepare or migrate.

**Sunset migration.** Active outreach to users of the feature, helping them migrate.

The right pattern depends on usage volume, importance to users, and how cleanly the alternative covers the use case.

## Worked examples

### A feature with declining usage

A productivity tool has a "smart suggestions" feature that auto-recommends actions. Initially popular; over time, usage has declined as the product has evolved. Audit shows: 2% of users use it weekly; mostly long-term users; the suggestions are often ignored.

Decision: prune. Announce removal in 60 days. Email the 2% explaining the change and offering alternatives. Remove the feature; gain the maintenance time back.

Result: minimal churn; the product is simpler; the engineering team has more capacity for other work.

### A configuration setting that no one understands

A settings panel has a checkbox: "Enable advanced mode." When enabled, it changes some keyboard shortcuts. Audit shows: 0.3% of users have enabled it; support sometimes gets questions about it; documentation is unclear.

Decision: prune. Remove the setting; pick the better default for both modes; eliminate the divergent code paths. Communicate the change to the small affected audience.

Result: simpler settings, simpler code, easier to support.

### A feature dependent on a deprecated API

The product integrates with a third-party service via an API the third party is deprecating. Investigation reveals: the integration is used by 1% of users; building on the new API would take months; the use case is partially served by other integrations.

Decision: deprecate the integration; remove it when the old API shuts down. Communicate to affected users; recommend alternative integrations.

Result: avoided months of engineering work; users have alternatives.

### A "kept" decision

A product has a feature for converting documents to a niche format. Usage: 0.5%. But investigation reveals that the niche format is required by some government agencies; users who depend on it are mission-critical (legal, government, healthcare).

Decision: keep, despite low usage. Document the strategic reason. Plan to maintain it; budget for ongoing support.

Result: low usage but real importance; pruning would harm critical users.

### A redundant pair of features

A product has two ways to accomplish the same task: an older "import" workflow and a newer "drag to upload" feature. Both exist in the UI. Users sometimes use both; sometimes use only one.

Decision: prune the older "import" workflow. Verify the newer "drag to upload" handles all the cases. Communicate to users who used the older flow. Remove the older flow once migration is complete.

Result: cleaner UI, less code, less confusion.

## Anti-patterns

**Pruning what users actually need.** Removing a feature without verifying who depends on it. The 1% may be your best customers.

**Mass deprecation without migration paths.** Announcing many removals at once with no clear alternatives. Users feel abandoned.

**Soft removal that lingers forever.** Moving a feature to a "legacy" menu but never actually removing it. Maintenance cost continues; the simplification benefit is partial.

**Pruning on a whim.** Removing things because someone subjectively thinks they're not needed, without data. Often removes things that are actually used.

**No communication.** Pruning silently. Users discover the change when their workflow breaks. Trust is damaged.

**Pruning during major rebuilds.** Major rebuilds (often called "v2") that strip many features. Almost always less successful than incremental pruning.

**Reflexive feature-cutting.** Treating "shipped fewer features" as a virtue independent of context. Sometimes adding features is correct; sometimes pruning is. Be evidence-based.

## Heuristic checklist

When considering pruning, ask: **What's the actual usage of this feature?** Get data before deciding. **Who uses it, and why?** Talk to affected users. **What's the maintenance cost?** Engineering time, support load, complexity. **What's the alternative for users who depend?** Don't leave them stranded. **Is there a migration plan?** Don't just delete and walk away. **How will you communicate?** Surprise removal damages trust.

## Related sub-skills

- `ockhams-razor` — parent principle on preferring simpler designs.
- `ockhams-equivalent-designs` — sibling skill on identifying when designs are functionally equivalent.
- `80-20-rule` — most use is concentrated in a few features; the long tail is often pruning candidates.
- `iteration` — pruning is part of the iterative process of product evolution.
- `weakest-link` — sometimes the weakest link is a feature that should be removed.

## See also

- `references/pruning-process.md` — step-by-step process for pruning decisions.
