---
name: ux-designer
description: "UX principles for planning or auditing an interface: accessibility (WCAG, EAA), information architecture, microcopy, i18n/RTL, and AI or voice UX."
---

# UX Designer Skill

A UX depth library. Read the reference for the task before designing or reviewing; each number and pattern has one home there, so cite the reference rather than restating values from memory.

## Lens

Rank every decision by the UX hierarchy of needs: functional, then reliable, usable, convenient, and only then pleasurable.

- **Calm over busy.** Motion, color and density earn their place by aiding understanding.
- **AI as copilot, not autopilot.** AI help is optional, labeled, reversible and transparent.
- **Responsible adaptation.** Adapt to real user needs and context; never manipulate through opaque personalization.
- **Judgment over polish.** Research, correctness and knowing when not to add something are the value.

## Baseline

Every interface, whatever the task:

- Every interactive element is reachable and operable by keyboard, with a visible focus state and an accessible name and role.
- Color never carries information alone; images have text alternatives.
- Every action produces a visible response; motion respects `prefers-reduced-motion`.
- Errors appear next to their field in plain language.
- Consent is symmetric: equal-prominence accept and reject, nothing pre-checked, cancellation as easy as sign-up, neutral decline copy.
- Strings are externalized and layouts survive translation and `dir="rtl"`.

## References

| Task | Reference |
|---|---|
| Usability heuristics, mental models, anti-pattern audit index | [01-core-principles](references/01-core-principles.md) |
| Laws of UX (Fitts, Hick, Miller, Jakob) | [02-laws-of-ux](references/02-laws-of-ux.md) |
| WCAG 2.2 AA and EAA accessibility | [03-accessibility](references/03-accessibility.md) |
| Visual hierarchy, typography, spacing | [04-visual-design](references/04-visual-design.md) |
| Navigation, wayfinding, content structure | [05-information-architecture](references/05-information-architecture.md) |
| Feedback, states, gestures, modal vs panel vs page | [06-interaction-design](references/06-interaction-design.md) |
| Forms, validation, input types | [07-forms-and-inputs](references/07-forms-and-inputs.md) |
| Mobile ergonomics and thumb zones | [08-mobile-ux](references/08-mobile-ux.md) |
| UX writing and microcopy | [09-ux-writing](references/09-ux-writing.md) |
| User research methods | [10-user-research](references/10-user-research.md) |
| Design system foundations and governance | [11-design-systems](references/11-design-systems.md) |
| Presence, live cursors, avatars | [12a-presence-awareness](references/12a-presence-awareness.md) |
| Conflicts, sync, sharing, offline | [12b-conflict-resolution-sync](references/12b-conflict-resolution-sync.md) |
| Canvas zoom, pan, selection | [13a-canvas-navigation](references/13a-canvas-navigation.md) |
| Canvas objects, layers, performance | [13b-canvas-objects-performance](references/13b-canvas-objects-performance.md) |
| AI chat, copilots, agents, generative UI | [14-ai-ux-patterns](references/14-ai-ux-patterns.md) |
| Dark patterns and consent | [15-ethical-design](references/15-ethical-design.md) |
| Onboarding and activation | [16-onboarding](references/16-onboarding.md) |
| Notifications, toasts, attention | [17-notifications](references/17-notifications.md) |
| Dashboards and data visualization | [18-data-visualization](references/18-data-visualization.md) |
| Search and autocomplete | [19-search-ux](references/19-search-ux.md) |
| Emotional design and trust | [20-emotional-design](references/20-emotional-design.md) |
| Data tables, pagination, bulk actions | [21-data-tables](references/21-data-tables.md) |
| Loading, skeletons, optimistic updates | [22-performance-ux](references/22-performance-ux.md) |
| Internationalization and RTL | [23-internationalization](references/23-internationalization.md) |
| Voice, multimodal, cross-device input | [24-voice-and-multimodal](references/24-voice-and-multimodal.md) |

For an audit, walk the anti-pattern index in `01-core-principles` and report each hit with its reference.
