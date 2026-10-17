# Redesign case patterns

A reference complementing `80-20-redesign-targeting` with case patterns from observed redesigns.

## The "ship of Theseus" redesign

Some products redesign continuously, surface by surface, never doing a single big-bang redesign. Linear, Notion, Stripe, GitHub all follow this pattern: every quarter, a few surfaces get attention; the system evolves incrementally.

Pros: low risk per release; learnings compound; team always shipping.

Cons: visual fragmentation between old and new; team must maintain design-system discipline so the surfaces remain cohesive.

## The big-bang redesign

A multi-quarter project that redesigns most of the product at once. Target.com's 2017 redesign, Reddit's 2018, Twitter's various redesigns.

Pros: cohesive launch moment; teams can rally around shared milestones; users feel the change.

Cons: high risk; users object to abrupt change; if metrics tank, hard to revert; opportunity cost of not shipping other things during the redesign.

In aggregate, big-bang redesigns underperform incremental ones — most show flat or declining metrics for 3–6 months post-launch as users re-learn.

## The hidden-A/B redesign

Major surfaces are redesigned and quietly tested in parallel for weeks before the new design replaces the old. Facebook, Google, and Amazon use this approach for high-traffic surfaces.

Pros: data-driven; you can kill bad redesigns; users get the better version.

Cons: requires substantial engineering investment in testing infrastructure; not feasible for smaller teams.

## Deprecation paths for the long tail

Surfaces that the redesign chose *not* to update need a plan:

- **Adopt new design system** for visual consistency, even without redesigning interaction.
- **Mark for future review** in a tracker; revisit annually.
- **Plan deprecation** for surfaces that aren't worth keeping.
- **Migrate users** off surfaces that are being removed.

The trailing 80% deserves *some* attention even if not full redesign — usually maintenance and design-system updates.

## Anti-pattern: redesign without metrics

A surface ships in new design with no before/after measurement. Six months later, no one can answer whether the redesign worked.

Always define metrics before shipping a redesign:

- Time-on-task for primary flows.
- Conversion rate for funnel surfaces.
- Support-ticket categorization changes.
- Qualitative satisfaction (NPS, in-product surveys).

If you can't define a metric, the redesign was probably aesthetic-only — fine, but be honest about that.

## Resources

- **NN/g** articles on redesign measurement and incremental design system rollouts.
- **Brignull, H.** writings on dark patterns to avoid in redesigns.
- **Product redesign case studies** from major companies (often presented at conferences like Config, Smashing).
