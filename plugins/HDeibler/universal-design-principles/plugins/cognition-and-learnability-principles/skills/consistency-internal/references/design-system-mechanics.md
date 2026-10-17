# Internal consistency — design-system mechanics

Practical patterns for building, maintaining, and evolving a design system that actually keeps a product consistent over years.

## Pattern: design tokens as the foundation

Define a small set of named values for color, spacing, typography, border-radius, shadow, and animation. Components use the names; engineers never use raw values. When the canonical value changes, every component updates.

A starter token set for color might be: `color.brand.primary`, `color.brand.secondary`, `color.semantic.success`, `color.semantic.warning`, `color.semantic.error`, `color.surface.base`, `color.surface.muted`, `color.surface.elevated`, `color.text.primary`, `color.text.muted`, `color.text.inverse`. Each maps to a literal value, but components reference the semantic name. This means a brand refresh changes one mapping; nothing else needs to change.

For spacing, a 4px or 8px base scale (`spacing.0`, `spacing.1`, `spacing.2`, …) covers most cases. Use multiples of the base; resist arbitrary values like 13px or 22px.

For typography, define a clear scale (`text.body.sm`, `text.body.md`, `text.heading.lg`, etc.) with size, weight, and line-height bundled together. This prevents ad-hoc combinations like "16px Inter Bold" that don't match anything in the system.

## Pattern: component library shipped via package

Components live in a package (`@yourcompany/ui` or similar) that all product code depends on. Updates ship as version bumps; teams pull updates explicitly. This gives the design system team a clear release cadence and gives product teams predictable upgrade timing.

The library should include:

- Core primitives (Button, Input, Select, Checkbox, Radio, Switch, etc.)
- Composite components (Modal, Drawer, Card, Tabs, Table, Toast, etc.)
- Layout primitives (Stack, Box, Grid, Spacer)
- Token definitions accessible programmatically

Components should be opinionated about appearance and unopinionated about content. They should accept content as props or children, and apply system styling automatically.

## Pattern: linting and visual regression

Lint rules catch off-system usage at code-review time. A few high-value rules:

- Reject hex colors in component code (force use of token references)
- Reject inline padding/margin values not on the spacing scale
- Reject font-family declarations outside the token system
- Warn on imports from outside the design system package

Visual regression testing (Chromatic, Percy, BackstopJS, etc.) catches unintentional visual changes when components or tokens evolve. Snapshots from before and after a change are compared; differences are flagged for review.

## Pattern: figma library mirroring code

Designers work in Figma with a component library that mirrors the code components. Token values are synchronized between the two. When a designer changes a component, it triggers a code review for the corresponding component update.

This requires investment to maintain (the two libraries can drift if not actively kept in sync), but it's the only pattern that prevents the "designed in Figma, implemented differently in code" failure mode.

Tools like Figma Tokens, Style Dictionary, and dedicated team workflows can semi-automate the synchronization.

## Pattern: pattern documentation for non-component decisions

Some consistency questions don't fit into components: when to use a modal vs. inline, how to handle empty states, what tone to use in error messages, how to title pages.

These need pattern documentation: short, opinionated guidance with examples. "When to use a modal: only for actions that interrupt the user's current task and require completion before continuing. For non-interrupting actions, use a Drawer. For confirmation of destructive actions, use the inline destructive-confirm pattern."

The documentation should be on the same internal site as the component library, so designers and engineers reach for it as a single source.

## Pattern: design-ops as a real team

Internal consistency requires sustained ownership. A "design-ops" team — typically 1–3 people for a mid-sized product, more for larger ones — owns the design system, runs reviews, builds tokens, ships component updates, evangelizes adoption, and audits the live product for drift.

Without ownership, the system erodes. With it, the system can sustain a coherent product across many years and teams.

## Pattern: contribution model

Product teams need a way to contribute new components or patterns when the system doesn't cover their case. The model usually looks like:

1. Team identifies a need not covered by the system.
2. Team builds the new component locally, with the design-ops team's review.
3. If the pattern proves useful across teams, it migrates into the system.
4. Other teams adopt the system version.

This prevents the system from being a bottleneck (teams can ship without waiting) while keeping the system growing in the right direction (proven patterns get promoted).

## Pattern: deprecation and migration

When the system needs to evolve, old patterns get deprecated. The deprecation needs a clear timeline:

- New: this is the canonical pattern; use it.
- Deprecated: still works, but new uses should switch to the new pattern.
- Removed: gone; remaining usages will break.

Clear deprecation timelines with migration guides let product teams plan their work. Sudden removals create churn and erode trust in the system.

## Pattern: cross-platform tokens

For products that ship to web, iOS, Android, and possibly desktop, tokens should be defined once in a platform-neutral format (JSON, YAML) and exported to each platform's native format (CSS variables for web, asset catalogs for iOS, resources for Android). Tools like Style Dictionary support this.

The benefit: a brand color change is one edit, propagating to every platform. The cost: the tooling pipeline needs to be built and maintained.

## Pattern: token escape hatches

Even the best design system needs occasional escape hatches. A truly novel surface (a marketing landing page, an experimental feature) may need values outside the system. Provide a clear escape mechanism (a "raw" token namespace, a known list of off-system colors) and require justification for its use. The escape hatch should be visible enough that uses can be tracked and consolidated over time.

The failure mode is having no escape hatch (forcing teams to work around the system, often invisibly) or having too easy an escape hatch (everyone uses it and the system becomes optional).

## Anti-patterns

**The "documentation is the system" trap.** A beautifully designed Storybook or Zeroheight site that nobody uses in production. The documentation describes a system that doesn't exist in code.

**The "no one owns it" trap.** A design system that depends on volunteer contributions from teams shipping product features. Without dedicated ownership, the system stagnates and drifts.

**The "boil the ocean" trap.** Trying to ship a complete design system before any team uses it. Better to ship a minimal viable system (10 core components + tokens) and grow it organically based on real usage.

**The "second system" trap.** Replacing an existing flawed-but-functional design system with a fully redesigned one. The migration takes years; the old and new systems coexist; the product becomes more inconsistent during the transition than it was before. Better to evolve the existing system in place.

**The "component for every screen" trap.** Building a custom component for every unique-looking screen instead of composing from primitives. The library balloons; reuse drops; consistency erodes because each screen has its own one-off.

## Audit pattern

Periodically (quarterly or so), audit the live product for consistency drift:

- Take screenshots of key surfaces.
- Identify off-system colors, spacings, typography, components.
- Categorize: legacy (predates the system), recent (drift), intentional (justified divergence).
- Plan remediation for the recent drift; document the intentional divergence; schedule legacy migration where it's worth the cost.

The audit itself is a forcing function: when teams know the audit is coming, they're less likely to ship off-system patterns.

## Cross-reference

For external consistency (with platform and category conventions outside your product), see `consistency-external`.
