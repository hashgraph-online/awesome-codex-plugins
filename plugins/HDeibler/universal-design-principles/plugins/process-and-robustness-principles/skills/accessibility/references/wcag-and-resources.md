# Accessibility: WCAG, regulations, and resources

A reference complementing the `accessibility` SKILL.md with the legal and standards landscape and a curated resource list.

## The WCAG framework

The Web Content Accessibility Guidelines (WCAG) are published by the W3C's Web Accessibility Initiative (WAI). Versions in active use:

- **WCAG 2.0** (2008) — the foundational version still referenced in many legal contexts.
- **WCAG 2.1** (2018) — adds mobile, low-vision, and cognitive criteria.
- **WCAG 2.2** (2023) — adds focus appearance, dragging movements, target-size minimums, accessible authentication.
- **WCAG 3** (W3C draft) — restructures the framework; not yet a formal recommendation.

Each criterion has three conformance levels:

- **Level A** — basic accessibility; failures here often affect substantial user populations.
- **Level AA** — the practical legal target in most jurisdictions; most procurement and compliance refers to AA.
- **Level AAA** — the highest level; not always achievable on every page (some criteria conflict with design needs).

Most products aim for **WCAG 2.1 or 2.2 Level AA** as a practical target.

## Legal landscape (as of writing)

This is not legal advice. The landscape is evolving; consult counsel for specifics.

### United States

- **Americans with Disabilities Act (ADA)** — courts have increasingly held that web sites are "places of public accommodation" subject to ADA. WCAG 2.0/2.1 AA is the de facto standard cited in settlements.
- **Section 508** (Rehabilitation Act) — applies to federal agencies and federal contractors. Updated to align with WCAG 2.0 AA in 2017.
- **State laws** vary; California's Unruh Act and similar state statutes have been bases for accessibility lawsuits.

### European Union

- **European Accessibility Act (EAA)** — full effect June 2025. Applies to many consumer products and services. WCAG 2.1 AA is the harmonized standard.
- **Web Accessibility Directive** — applies to public-sector websites and apps.

### Other jurisdictions

- **Canada** (Accessible Canada Act, AODA in Ontario), **Australia** (DDA), **UK** (Equality Act + PSBAR), **Israel** (IS 5568) — all have similar frameworks targeting WCAG 2.0/2.1 AA.

The trend: more jurisdictions, lower thresholds for litigation, larger settlements. Building accessibly is increasingly a business risk-mitigation, not just an ethical position.

## What automated tools catch

Automated audits (axe-core, WAVE, Lighthouse) catch roughly 30% of accessibility issues — typically:

- Missing alt text.
- Color contrast failures.
- Missing form labels.
- Heading order issues.
- Some ARIA misuse.

Automated tools *don't* catch:

- Whether alt text is meaningful (just whether it exists).
- Whether keyboard navigation works for custom components.
- Whether focus management is correct.
- Whether copy is understandable.
- Whether interactions match user mental models.
- Most issues that come from *behavior*, not *markup*.

Use automated tools as a baseline; manual testing is required for most actual conformance.

## Manual testing

The shortlist:

1. **Keyboard-only walkthrough.** Unplug the mouse; complete every primary task. Find every trap, missing focus, hidden control.
2. **Screen reader walkthrough.** VoiceOver (macOS/iOS), NVDA (Windows), TalkBack (Android). Listen for unlabeled controls, missing announcements, garbled reading order.
3. **Zoom to 200% and 400%.** Reflow without horizontal scroll? Hit targets still hittable?
4. **Color blindness simulation.** Chrome DevTools or OS-level filters.
5. **High-contrast / dark mode.** Many users rely on these.
6. **Reduced motion.** Settings → Accessibility → Reduce Motion.
7. **Real disabled users.** No checklist substitutes for genuine usability testing with disabled participants.

## Resources

- **W3C WAI** — w3.org/WAI. Authoritative source for WCAG, ARIA, and methodology.
- **WAI-ARIA Authoring Practices Guide** — w3.org/WAI/ARIA/apg. Canonical accessible-component patterns.
- **WebAIM** — webaim.org. Practitioner-focused training, tools, and articles. Especially good: WAVE evaluator, contrast checker.
- **The A11y Project** — a11yproject.com. Practical patterns and checklists.
- **Inclusive Components** (Heydon Pickering) — inclusive-components.design. Component-by-component accessibility deep dives.
- **Smashing Magazine accessibility section** — many practical articles.
- **Deque axe** — deque.com/axe. Browser extension and CI tooling.
- **MDN Web Docs: Accessibility** — developer.mozilla.org/Web/Accessibility. Reference material.
- **GOV.UK Design System and Service Manual** — design-system.service.gov.uk. Government-grade accessibility patterns.

## Books

- **Horton, S. & Quesenbery, W.** *A Web for Everyone* (2013).
- **Pickering, H.** *Inclusive Design Patterns* (2016).
- **Holmes, K.** *Mismatch* (2018).

## Closing

WCAG is necessarily a checklist; accessibility is a practice. Treat WCAG as the floor and inclusive design as the ceiling. The investment in both is repaid in reach, in resilience, and increasingly in regulatory standing.
