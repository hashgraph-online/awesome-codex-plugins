---
name: ockhams-equivalent-designs
description: 'Identify when two design options are functionally equivalent so the razor can be applied. Use when comparing design alternatives, evaluating whether two implementations of a feature actually produce the same outcome, or recognizing that a complex solution doesn''t earn its place against a simpler one. Most design debates involve actual tradeoffs; the razor only cuts when the alternatives genuinely produce equivalent results. The skill is identifying equivalence honestly rather than rationalizing complexity.'
---

# Ockham's Razor — equivalent designs

The razor cuts when alternatives are functionally equivalent. The skill is recognizing when alternatives actually are equivalent — versus when a more complex alternative serves a real need that the simpler one doesn't.

Designers and engineers often defend complexity by imagining benefits the complex solution provides. Sometimes those benefits are real; sometimes they're rationalization. The discipline is honest evaluation of whether the complexity earns its place.

## Defining functional equivalence

Two designs are functionally equivalent when they produce the same outcome for users. Specifically:

**Same goal achieved.** The user can accomplish what they're trying to accomplish.

**Same quality of outcome.** The result is equally good (correct, complete, accurate).

**Same cost to user.** The user pays roughly the same in time, attention, learning.

**Same edge case handling.** Both work for the cases users actually encounter.

**Same downstream effects.** Both leave the system in the same state for subsequent interactions.

If these are equal, the designs are equivalent for the user, and the razor cuts toward simpler.

## When designs that look equivalent aren't

Designs may look equivalent on the surface but actually differ in important ways:

**Edge case behavior.** One design handles unusual cases gracefully; the other fails. The behavior in the typical case is the same; the long tail differs.

**Performance.** One design is fast at small scale; the other scales better at large scale. Both work today; the difference matters tomorrow.

**Error recovery.** One design recovers from failures elegantly; the other doesn't. Most of the time, neither fails; in the failure cases, they differ sharply.

**Discoverability.** Two designs achieve the same task, but one is more discoverable. Users find one and not the other.

**Accessibility.** Two designs work for typical users; one fails for users with disabilities.

**Internationalization.** Two designs work in English; one fails in non-English contexts.

**Future flexibility.** Two designs do the same thing today; one is easier to evolve.

When evaluating equivalence, check these dimensions, not just the happy path.

## When complexity actually earns its place

A more complex design earns its place when it:

**Solves a real problem the simpler doesn't.** Not a hypothetical problem; an actual user pain point with evidence.

**Serves an important audience the simpler doesn't.** Even if the audience is small, if it's strategically important, the complexity may be justified.

**Enables future capabilities.** Architectural complexity that supports planned future work, not speculative future work.

**Improves reliability or performance materially.** Not in theory; in measurement.

**Reduces other complexity.** Sometimes adding one component eliminates several others. The net change is simplification.

If none of these apply, the complexity doesn't earn its place.

## Evaluating equivalence honestly

Engineers and designers tend to defend their preferred designs. Honest equivalence evaluation requires:

**Defining "the user's goal" specifically.** Vague goals make any solution look reasonable. Precise goals make tradeoffs visible.

**Listing the actual differences.** What does design A do that B doesn't? What does B do that A doesn't? Be specific.

**Quantifying the differences.** Not "A is faster" — "A handles 1000 req/sec, B handles 5000." Numbers force honesty.

**Identifying who pays for the differences.** Often complexity benefits some users (or the team) and costs others. Be explicit.

**Time-shifting the comparison.** Today, the simpler design may be sufficient. In two years, the more complex one may be necessary. Make the time horizon explicit.

## Worked examples

### Two API designs that look equivalent

**Option A:** A single endpoint that takes a complex JSON body specifying everything.

**Option B:** Multiple endpoints, each with simpler parameters.

At first they look equivalent — both expose the same functionality. But:

- Option A is harder to document (the complex body has many fields).
- Option B has more endpoints to maintain.
- Option A has more validation logic for the body.
- Option B is easier for clients to understand piecemeal.
- Option A allows transactional behavior (one call); Option B doesn't.

If transactional behavior matters, A wins. If documentation and approachability matter more, B wins. They're not equivalent; pick based on what matters.

### Two feature implementations that are equivalent

**Option A:** A wizard with 3 steps to configure a new resource.

**Option B:** A single page with the same fields shown all at once.

Both produce the same configured resource. The user experience differs (wizard vs. single page) but the outcome is the same.

For a complex configuration with many interdependent decisions, the wizard helps the user; A is preferred. For a simple configuration with few fields, the single page is faster; B is preferred.

If the configuration is genuinely simple, A's complexity doesn't earn its place. The razor cuts toward B.

### Two architecture choices

**Option A:** A microservices architecture with 12 services.

**Option B:** A monolithic architecture in a single codebase.

If the team is small and the throughput modest, A's complexity (network, deployment, monitoring) doesn't earn its place against B's simplicity. The razor cuts toward B.

If the team is large with many independent groups, A's complexity may be justified by the parallelization it enables. The razor doesn't cut — they're not equivalent for this team.

The right call depends on context. The discipline is to honestly evaluate the context, not to default to either.

### Two visual treatments

**Option A:** Detailed icons with multiple colors and gradients.

**Option B:** Simple line icons in a single color.

Both can communicate the same information. Option A may have aesthetic appeal but doesn't communicate more. Option B is faster to render, easier to maintain (consistent stroke weights), more flexible (color from currentColor), and more accessible (high contrast).

The razor cuts toward B unless A's aesthetic is genuinely strategic to the brand. Even then, A should earn its place against the costs.

### A complex feature defended on hypotheticals

Engineering team proposes a complex configuration system: "Users will want to customize this in the future." Current users don't ask for it; no design pressure for it; speculative future need.

The razor cuts: don't build it now. If future need materializes, build it then. YAGNI (You Aren't Gonna Need It). Premature flexibility is a common form of accumulated complexity.

## Anti-patterns

**Defending complexity with hypotheticals.** "We might need this someday." Without evidence, the complexity isn't earning its place.

**Equivalence claims without checking edge cases.** Two designs equivalent on the happy path may differ sharply on the long tail.

**Dismissing simpler options because they "feel less professional."** Aesthetic preference for complexity doesn't earn complexity's place.

**Failing to time-shift the evaluation.** Today's equivalence may not be tomorrow's. Long-lived systems deserve longer-horizon evaluation.

**Confusing "more features" with "better."** Complexity isn't quality. A focused product can be better than a sprawling one.

**Comparing designs that aren't actually equivalent.** Apples and oranges. Pick designs that achieve the same goal, then evaluate the differences.

## Heuristic checklist

When considering two designs, ask: **What's the specific user goal each design serves?** Be precise. **Are they actually equivalent on the goal?** Not just the happy path; check edge cases, accessibility, scaling. **What are the differences?** List specifically. **What does the complexity earn?** Should be a real, measurable benefit. **What does the complexity cost?** Cognitive, maintenance, evolution. **If equivalent, choose simpler. If not, the razor doesn't apply.**

## Related sub-skills

- `ockhams-razor` — parent principle on preferring simpler designs.
- `ockhams-feature-pruning` — sibling skill on removing accumulated complexity.
- `form-follows-function` — closely related; both ask whether each design element earns its place.
- `iteration` — equivalence evaluation evolves over time as you learn more about user needs.

## See also

- `references/comparison-template.md` — a template for honest design comparison.
