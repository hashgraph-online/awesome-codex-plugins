---
name: consistency-internal
description: 'Apply internal consistency — making your product coherent with itself across all surfaces, components, and flows. Use when designing or auditing component libraries, defining design tokens, settling cross-team naming conventions, planning a design-system rollout, integrating acquired or legacy code, or evaluating whether two features should share or diverge in their interaction model. Internal consistency is enforced through design systems, shared vocabularies, and process discipline; it erodes through hand-off losses, sprint-driven shortcuts, and team boundaries that don''t coordinate.'
---

# Consistency — internal

Internal consistency is the property of a product being coherent with itself. Every screen, every flow, every component looks like it came from the same product, and equivalent operations behave the same way. Users transfer their learning across surfaces because the product rewards them for doing so.

Internal consistency is hard to maintain by good intentions alone. Teams ship in parallel, designers move on, design tokens drift, components get forked. The systems that maintain consistency over years are the ones that build it into the production process — design systems with real components, design tokens enforced by code, lint rules that fail builds for off-system colors.

## The mechanisms of internal consistency

Internal consistency rests on a few mechanisms working together.

**A design system with real components.** A library of buttons, inputs, modals, cards, tabs, etc., that is the canonical implementation. Designers compose with it; engineers use it; everyone gets the same behavior because there's only one implementation to use. The design system is not a documentation site full of screenshots — it's actual production components, code, and design tokens that flow through to the product.

**Design tokens enforced by code.** Colors, spacings, typographic sizes, border-radii, shadows, animations — all defined as named tokens (`color.primary.500`, `spacing.4`, `radius.md`) and used through those names rather than as raw values. When a designer changes the canonical primary blue, every component that uses `color.primary.500` updates automatically. When an engineer hard-codes a custom blue, a lint rule flags it.

**A shared vocabulary.** The same concepts have the same names across the product, the documentation, the marketing, and the support content. The "workspace" is always called the "workspace," not sometimes "team" and sometimes "org." The "save" action is always called "save," not sometimes "store" or "submit." Vocabulary drift is one of the easiest consistency violations to ship and one of the hardest to recover from once shipped.

**Pattern documentation for non-component decisions.** Some design decisions don't fit neatly into components — when to use a modal vs. an inline form, when to redirect vs. open in a new view, how to handle empty states, how to handle errors. These need pattern documentation so teams making decisions can reach for the same answer.

**Reviews and audits.** Design reviews and engineering reviews catch inconsistencies before they ship. Periodic audits across the live product catch the inconsistencies that slipped through. Both require ongoing investment, but the alternative — letting inconsistency accumulate until a major rebuild is needed — is more expensive.

## Common sources of internal inconsistency

Internal inconsistency creeps in through a few well-known channels.

**Different teams building parallel features.** Team A and Team B both ship features in the same release. They consult the design system but encounter cases the system doesn't cover. Each team makes a reasonable local decision. The decisions differ. The product now has two ways to handle the same case.

**Quick fixes under deadline pressure.** A bug needs to be fixed before launch. The designer is unavailable. The engineer makes a styling tweak that solves the immediate problem and ships. The tweak is now in production, slightly off-system, and may persist for years.

**Acquisitions and integrations.** A product acquires another product. Two design systems collide. Without active integration work, both systems persist, with users encountering both depending on which surface they're in. The seam between them is visible and irritating.

**Legacy that the design system never reached.** A part of the product was built before the design system existed and was never migrated. It's been working "well enough" for years, but it looks and behaves differently from everything around it.

**Design system gaps.** The design system covers 80% of cases; the remaining 20% are ad-hoc. Without conscious effort, the ad-hoc patterns drift apart over time.

**Tool fragmentation.** Different teams use different tools (one designs in Figma, another in Sketch, another sketches in Whimsical) without shared component libraries. Decisions made in different tools diverge.

## Worked examples

### A design system that prevents drift

A product team adopts a design system with: a code library of React components, design tokens for color/spacing/typography, lint rules that fail builds for off-token values, a Figma library that mirrors the code components, and a small "design ops" team that owns the system.

Two years later, despite shipping hundreds of features, the product still looks coherent. Drift is suppressed at production time. New components are added to the system rather than ad-hoc'd. Engineers can't even ship an off-system color without a lint failure. The discipline is in the tooling.

The cost: the design system itself requires investment (perhaps 1–2 dedicated people for a mid-sized product). The benefit: every team is faster because they're not re-deciding fundamentals, and the product stays coherent.

### A design system that lives only in screenshots

Another team's design system is a documentation site with screenshots and prose ("Use the Primary button for primary actions, the Secondary for secondary"). There are no actual code components or design tokens enforced anywhere. Each engineering team implements buttons themselves, intending to follow the screenshots. They each implement slightly differently.

Two years later, the product has a dozen subtly different button styles, and the design-system site no longer matches any of them. The system died because it didn't actually constrain production.

The lesson: a design system that isn't part of the production pipeline isn't a system; it's documentation, and documentation drifts away from reality.

### A vocabulary drift that ships to users

A team building a project-management product calls the unit of work "task" in the main UI, "item" in the API, "issue" in the documentation, and "ticket" in the support tooling. Each name was reasonable in its local context. But users encountering multiple surfaces are confused: are tasks and issues the same thing?

The fix is consolidation: pick one name, change all surfaces to use it, and update any external content. The effort is real; the alternative is paying a small confusion cost on every cross-surface interaction.

### Two confirmation patterns

A product has two confirmation flows shipped by different teams. One uses a modal: "Delete this? Cancel / Delete." The other uses an inline confirm with the button transforming into Yes/No. Users encountering one flow after the other are mildly confused.

The fix: pick one pattern (the modal for high-stakes actions; the inline for low-stakes) and apply it consistently. If the two patterns reflect a real difference in stakes, document the rule and apply it everywhere; if they don't, consolidate to one.

### Migrating a legacy section

A 5-year-old section of the product was built before the current design system. It still works, but it looks visibly different: older typography, older button styling, older spacing. The team faces a choice: leave it (cheap, but the inconsistency persists) or migrate it (expensive, but resolves the inconsistency).

The right call depends on usage. If the section is heavily used, migration is worth it because users encounter the inconsistency frequently. If it's lightly used, the migration cost may not be justified — but the section should at least be marked in the team's mental map as "out of system" so its inconsistency is acknowledged rather than denied.

## Anti-patterns

**Design system theater.** A beautifully documented design system that no one uses in production. The system exists; the actual product diverges from it; nothing enforces alignment. The effort spent on the documentation generates no consistency benefit.

**Aggressive consistency masking real differences.** A product where every list looks the same, every detail page looks the same, every form looks the same — even though some lists need to scan-able and dense while others need to highlight one or two items per row. Forced consistency at the layout level can flatten meaningful differences.

**Design system as straightjacket.** A design system so restrictive that teams can't accommodate genuine new patterns. They either work around the system (creating ad-hoc one-offs) or ship sub-optimal designs to stay within the system. Healthy design systems accommodate new patterns; rigid ones get bypassed.

**Component sprawl.** A design system that started small and accumulated dozens of similar components. Six button variants, eight modal types, four table styles. Teams can't tell which one to use. Periodic consolidation is needed to keep the system usable.

**Token drift.** Design tokens that started semantic (`color.primary`, `color.danger`) but accumulated literal aliases (`color.blue.500`, `color.red.500`) that bypass the semantic layer. Teams use the literal aliases for one-off cases and the semantic meaning erodes.

**Inconsistent accessibility behavior.** All buttons look the same but have different focus styles, keyboard handling, or ARIA properties. Visual consistency without behavioral consistency is the worst case for users with assistive tech, who rely on behavioral consistency more than visual.

## Heuristic checklist

When auditing internal consistency, ask: **Is there a single source of truth for components, tokens, and patterns?** If not, build one. **Are off-system values enforced against, or just discouraged?** Discouragement is unreliable. **Do all teams know about and use the system?** A system unknown to half the teams is half a system. **When new patterns are introduced, do they get added to the system?** Systems that don't grow with the product become irrelevant. **Is vocabulary consistent across UI, API, docs, marketing, and support?** Cross-surface vocabulary drift is invisible until users complain.

## Related sub-skills

- `consistency` — parent principle on the four kinds of consistency.
- `consistency-external` — sibling skill on external conventions.
- `mental-model` — internal consistency lets users build a stable mental model of the product.
- `recognition-over-recall` — consistent patterns strengthen recognition.
- `progressive-disclosure` — even hidden depth should be consistent in pattern with visible features.

## See also

- `references/design-system-mechanics.md` — practical patterns for building, maintaining, and evolving design systems.
