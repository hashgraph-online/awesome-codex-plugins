---
name: ockhams-razor
description: 'Apply Ockham''s Razor — given a choice between functionally equivalent designs, prefer the simplest. Use when comparing design approaches, evaluating whether a feature is necessary, deciding between elaborate and minimal solutions, auditing a product for accumulated complexity, or pruning features that no longer earn their place. The principle is not "always make things simpler" — it''s "when two designs do the same thing, pick the simpler one." Most design problems involve actual tradeoffs; the razor cuts only when functionality is truly equivalent.'
---

# Ockham's Razor

> **Definition.** Given a choice between two designs that perform the same function equally well, prefer the simpler. Simplicity reduces cognitive load, eases maintenance, lowers cost, improves performance, and reduces failure modes. Complexity should be added only when it earns its place by serving a real need. The principle is named for the medieval philosopher William of Ockham, who argued that "entities should not be multiplied beyond necessity" — the simplest explanation that fits the evidence is preferred.

In design, the razor cuts when comparing functionally equivalent options. If two designs serve the user's need equally well, pick the simpler one. The simpler design will be easier to learn, easier to maintain, less expensive to build, less likely to break, and easier to evolve.

The principle is widely cited and widely misapplied. It does not mean "always strip features" or "minimum viable everywhere." It means: don't add complexity that doesn't earn its place. When two equally-good options exist, choose simpler. When a more complex option is genuinely better, choose it; just verify that the complexity is actually paying its way.

## Why the razor matters

Complexity has costs that often go uncounted at the moment of decision:

**Cognitive cost.** Every feature, every option, every visual element costs the user attention and learning. A product with 50 features is harder to learn than one with 10, even if all 50 are individually useful.

**Maintenance cost.** Every line of code, every component, every dependency needs to be maintained. A simpler system has fewer places to update, fewer interactions to debug, fewer surprises.

**Reliability cost.** Each component is a potential failure point. A simpler system has fewer components, fewer interactions, fewer edge cases. Reliability tends to improve with simplicity.

**Performance cost.** Complex systems are harder to make fast. Simpler systems are usually faster by default.

**Evolution cost.** Adding a new feature to a simple system is easier than adding it to a complex one. Complexity compounds.

**Documentation cost.** Complex systems need more documentation, which itself becomes a maintenance burden.

These costs are paid continuously, often invisibly. Complexity feels free at the moment of addition; it becomes expensive over time.

## When the razor cuts

**When comparing two designs that produce the same outcome.** The simpler one is preferred.

**When evaluating whether to add a feature.** Does the feature earn its place? Could the user accomplish the same goal without it? If yes, the absence is simpler.

**When pruning an existing product.** Features, options, settings that don't serve the user well should be candidates for removal.

**When choosing technical architecture.** A simpler architecture (fewer services, fewer abstractions, fewer technologies) is easier to maintain.

**When picking between visual treatments.** A cleaner design that communicates the same information is preferred over an elaborate one.

## When the razor doesn't apply

**When the more complex option is genuinely better.** The razor cuts only when alternatives are equivalent. If the complex option serves users substantially better, choose it.

**When simplification destroys necessary capability.** A medical interface that simplifies away critical information is too simple. The right level of complexity depends on what the system needs to do.

**When the simpler option doesn't actually work.** A simple solution that doesn't solve the problem isn't simpler in any meaningful sense — it's just incomplete.

**When the complexity is in the underlying problem.** Some problems are genuinely complex. Trying to make the solution radically simpler than the problem usually fails.

The razor is a tiebreaker, not a mandate. Its work is to prevent unnecessary complexity, not to force inappropriate simplicity.

## Diagnosing accumulated complexity

Products tend to accumulate complexity over time, often invisibly. Symptoms:

**Settings that no one understands.** A settings panel with dozens of options whose meanings have been forgotten.

**Features that no one uses.** Features added for some specific need years ago that are now used by 0.1% of users.

**Workflows with branches.** A flow that has 8 different paths through it, each handling a slightly different case.

**Documentation that's longer than the code.** A sign that the design has accumulated complexity that's hard to explain.

**Onboarding that takes longer.** New users need more time to understand the product than they used to.

**Engineers afraid to touch certain code.** Code so complex that no one understands it; changes are risky.

**Many "exception" handlers.** A codebase with many special cases for specific situations.

These are all signs that the razor might be useful. Look for things that can be removed, simplified, or consolidated.

## Sub-skills in this cluster

- **ockhams-feature-pruning** — Removing features, options, and complexity that no longer earn their place. The discipline of cutting back what's accumulated.
- **ockhams-equivalent-designs** — Identifying when two designs are functionally equivalent and applying the razor. The skill of recognizing when simpler is just as good.

## Worked examples

### Two equivalent designs for a setting

A team is debating two designs for a "default sort order" setting:

**Option A:** A dropdown with 5 options, each clearly named.

**Option B:** A wizard that asks the user 3 questions and infers the right sort.

Both produce the same result (the right default sort). Option A is simpler — fewer interactions, less code, less explanation needed. Option B is more elaborate but doesn't produce a better outcome.

The razor cuts: choose A.

### Feature that doesn't earn its place

A product has a "share via fax" feature added 5 years ago when one customer asked for it. Usage data shows: 0.001% of users have ever used it. The code requires ongoing maintenance and occasionally breaks.

The razor cuts: remove the feature. The few users who depend on it can be contacted; the maintenance burden goes away; the product becomes simpler.

### Architecture choice

A team is building a new microservice. Two options:

**Option A:** A simple service that handles the responsibility, in the team's primary language and tech stack.

**Option B:** A more elaborate service using a different language and framework chosen for theoretical performance benefits.

If Option A meets the requirements, the razor cuts toward it. The team knows the language, the tech stack is supported, the maintenance burden is lower. The theoretical performance of Option B doesn't earn its place if the simpler option is fast enough.

### Prune accumulated settings

A product's settings page has 50 options accumulated over years. Audit reveals: 15 options are used by less than 1% of users; 8 options are obsolete (the underlying feature was removed); 5 are duplicates of each other; 10 should be defaults rather than settings.

After pruning: 12 settings remain, each clearly justified. The settings page is dramatically simpler. The few users who depended on removed settings can be addressed individually.

### A more complex design that earns its place

A team is debating two designs for an editor:

**Option A:** A simple text-only editor.

**Option B:** A WYSIWYG editor with formatting, embeds, mentions, and inline collaboration.

The functions aren't equivalent — Option B does substantially more. If users need the additional capabilities, the complexity is justified. The razor doesn't say "always simpler"; it says "simpler when equivalent."

The complexity of Option B is acceptable because it earns its place by serving real needs that A can't.

## Anti-patterns

**Mistaking simplicity for value.** Stripping a product to "MVP" and shipping something that doesn't actually do useful work. Simplicity that fails to serve isn't simpler; it's incomplete.

**Adding complexity reflexively.** Every problem solved with a new feature, a new option, a new toggle. The product accumulates complexity that's never pruned.

**"Just one more option."** The temptation to add a configuration setting for every edge case. Each setting individually seems harmless; the accumulation becomes paralyzing.

**Applying the razor to the wrong things.** Stripping features that users depend on; simplifying interfaces past the point of usability; cutting maintenance work that's actually needed.

**Confusing minimal with simple.** A minimal-looking interface that requires deep navigation to find anything is not actually simple — it's hidden complexity. True simplicity means easy to use, not just visually sparse.

**Reflexive simplification.** Cutting things just because cutting feels virtuous. Verify that what's cut actually wasn't earning its place.

## Heuristic checklist

When considering a design choice, ask: **Are the alternatives functionally equivalent?** If yes, the razor cuts toward simpler. **What does the complexity earn?** If little, prefer simpler. **What does the complexity cost?** Cognitive, maintenance, reliability, performance, evolution. **Will this complexity be paid for over its lifetime?** If not, choose simpler. **Have I confused minimalism with simplicity?** True simplicity is ease of use, not just visual reduction.

## Related principles

- **Form Follows Function** — the razor and form-follows-function are closely related; both ask whether each element earns its place.
- **80/20 Rule** — most use is concentrated in a few features; the razor justifies pruning the long tail.
- **Signal-to-Noise Ratio** — simpler designs have higher signal-to-noise.
- **Mapping** — simpler mappings are easier to understand.
- **Hick's Law** — fewer options means faster decisions.
- **Iteration** — simplification is often an iterative process; what wasn't ready to remove last year may be ready now.

## See also

- `references/lineage.md` — origins in medieval philosophy and modern engineering.
- `ockhams-feature-pruning/` — sub-skill on pruning accumulated complexity.
- `ockhams-equivalent-designs/` — sub-skill on identifying functionally equivalent options.
