---
name: ux-designer
description: UX/UI design principles for building and critiquing interfaces. Use for accessibility audits (WCAG, EAA), microcopy, forms, navigation, onboarding, internationalization and RTL, voice and AI interfaces, and design systems.
---

# UX Designer Skill

Apply the following UX/UI principles when designing or reviewing interfaces.

## When to Apply This Skill

Use this skill when:
- Designing or reviewing user interfaces, components, and mobile-first layouts
- Implementing accessibility features or auditing against WCAG 2.2 AA
- Creating forms, navigation, search, and other interactive elements
- Writing UI copy and microcopy
- Planning user research, or building and maintaining design systems
- Designing collaborative/multiplayer features (presence, real-time editing, sharing, permissions, version history)
- Building canvas-based or whiteboard applications
- Designing AI-powered interfaces (chat, copilots, agents, generative UI)
- Evaluating designs for dark patterns, ethical compliance, and user trust
- Creating onboarding flows, activation funnels, and first-run experiences
- Designing notification systems and attention management
- Building dashboards and data visualizations
- Internationalizing/localizing UI or adding right-to-left (RTL) language support
- Designing voice, multimodal, or cross-device input experiences

## Core Design Philosophy

### User-Centered Design
1. **Understand users first** - Research before designing
2. **Reduce cognitive load** - Keep interfaces simple and intuitive
3. **Provide feedback** - Every action should have a visible response
4. **Maintain consistency** - Follow established patterns users expect
5. **Design for accessibility** - Include all users from the start

### Calm & Clarity Over Complexity
- **Cognitive clarity over sensory richness** - Calm, legible interfaces beat busy,
  flashy ones. Motion, color, and density should earn their place by aiding
  understanding, not by impressing.
- **AI as a respectful copilot, not an autopilot** - Offer AI assistance optionally
  (sidebars, overlays, suggestions); keep the user in control and every AI action
  reversible and transparent. See [references/14-ai-ux-patterns.md](references/14-ai-ux-patterns.md).
- **Responsible adaptation over hyper-personalization** - Adapt to genuine user
  needs and context; avoid manipulative or opaque personalization.
- **Depth and judgment over polish** - As UI becomes a commodity, the value is in
  research, correctness, and knowing when *not* to add something.

### The UX Hierarchy of Needs
1. **Functional** - Does it work?
2. **Reliable** - Is it dependable?
3. **Usable** - Is it easy to use?
4. **Convenient** - Is it frictionless?
5. **Pleasurable** - Is it delightful?

## Core Guidelines

### Before Designing
- Understand user goals and pain points
- Review existing patterns in the codebase
- Consider accessibility requirements (WCAG 2.2 AA)
- Define success metrics

### Visual Design
- One dominant element per screen — the primary action outranks all others in size and contrast
- Consistent typography (16px+ body, 1.3-1.6x heading scale)
- Sufficient color contrast (4.5:1 for text)
- Spacing drawn from a single scale (4px or 8px base unit)

### Interaction Design
- Touch targets minimum 44×44px (iOS) / 48×48dp (Android)
- Important actions in thumb-friendly zones (bottom/center on mobile)
- Every interaction produces a visible response
- Response appears within 100ms of input
- Smooth animations (300-500ms duration)
- Support `prefers-reduced-motion`

### Forms
- Inline validation (on blur, not during typing)
- Clear error messages near the field
- Required fields marked with asterisk (*)
- Logical field order and grouping

### Navigation
- Limited top-level items (7±2 rule)
- Current location always visible
- Mobile: bottom navigation preferred
- Consistent navigation across pages

### Accessibility
- All interactive elements reachable and operable by keyboard
- Every control has an accessible name and role exposed to screen readers
- Color not sole conveyor of information
- Focus states visible
- Alt text for images

### Collaborative Features
- Presence indicators (cursors, avatars, typing)
- Clear conflict prevention/resolution
- Offline state communication
- Client-specific undo/redo
- Permission levels clearly communicated

### Canvas/Spatial Apps
- Cursor-centered zoom (not screen center)
- Smart guides and snapping with toggle
- Minimap for large canvases
- Full keyboard navigation support
- Viewport culling for performance

### AI Interfaces
- AI-generated content clearly labeled
- Source attribution for AI claims
- User feedback mechanism (thumbs up/down)
- Stop/cancel generation control
- Human override always available

### Onboarding
- First-run experience guides users to "aha moment"
- Empty states provide clear next actions
- Onboarding is skippable and won't re-show
- Sign-up collects only essential fields

### Notifications
- Notification severity matches visual treatment
- Push permission requested in context (not on first visit)
- Users can control notification preferences per channel
- Toasts auto-dismiss within 4-8s
- Toasts carrying an undoable action expose that action as a button

### Ethical Design
- Accept/reject buttons have equal visual prominence
- No pre-checked optional consent boxes
- Cancellation is as easy as subscription
- No confirmshaming in decline copy

### Internationalization
- RTL-ready (logical CSS properties, layout verified in `dir="rtl"`)
- Tolerant of ~30-40% text expansion (no fixed-width labels/buttons)
- No text baked into images; all strings externalized
- Locale-aware date/number/currency formatting via `Intl`
- Pluralization handled with ICU plural rules, not string concatenation
- Language switcher uses endonyms, not flags

## Decision Trees

### Modal vs. Side Panel vs. Full Page

```
What is the user doing?
├── Quick confirmation or simple input (1-3 fields)?
│   └── → Modal dialog
├── Viewing/editing details while keeping main context visible?
│   ├── Content is narrow (form, properties, chat)?
│   │   └── → Side panel
│   └── Content needs significant width?
│       └── → Full-page overlay (with back navigation)
├── Multi-step workflow or complex form?
│   ├── Steps are short (2-3 fields each)?
│   │   └── → Modal with stepper
│   └── Steps are long or need reference to other content?
│       └── → Full page with stepper
└── Creating a new complex entity (document, project)?
    └── → Full page (dedicated creation flow)
```

### Notification Type Selection

```
What needs the user's attention?
├── Immediate action required?
│   ├── Blocking (must resolve before continuing)?
│   │   └── → Modal dialog (confirmation, error recovery)
│   └── Non-blocking but urgent?
│       └── → Banner (top of page, persistent until dismissed)
├── Feedback on a completed action?
│   ├── Success or low-importance info?
│   │   └── → Toast (auto-dismiss 4-8s)
│   └── Warning or error?
│       └── → Toast with action button (manual dismiss)
├── Background event (new message, update from others)?
│   ├── User is in the same context?
│   │   └── → Badge + subtle inline indicator
│   └── User is elsewhere in the app?
│       └── → Badge on nav item + optional push notification
└── System status (maintenance, connectivity)?
    └── → Persistent banner (top or bottom of viewport)
```

## Detailed Documentation

- For core UX principles and heuristics, see [references/01-core-principles.md](references/01-core-principles.md)
- For Laws of UX quick reference, see [references/02-laws-of-ux.md](references/02-laws-of-ux.md)
- For WCAG 2.2 accessibility compliance, see [references/03-accessibility.md](references/03-accessibility.md)
- For visual design patterns, see [references/04-visual-design.md](references/04-visual-design.md)
- For information architecture, see [references/05-information-architecture.md](references/05-information-architecture.md)
- For interaction design patterns, see [references/06-interaction-design.md](references/06-interaction-design.md)
- For form and input design, see [references/07-forms-and-inputs.md](references/07-forms-and-inputs.md)
- For mobile UX best practices, see [references/08-mobile-ux.md](references/08-mobile-ux.md)
- For UX writing and microcopy, see [references/09-ux-writing.md](references/09-ux-writing.md)
- For user research methods, see [references/10-user-research.md](references/10-user-research.md)
- For design system creation, see [references/11-design-systems.md](references/11-design-systems.md)
- For collaborative presence, live cursors, and awareness indicators, see [references/12a-presence-awareness.md](references/12a-presence-awareness.md)
- For conflict resolution, sync, sharing, and offline UX, see [references/12b-conflict-resolution-sync.md](references/12b-conflict-resolution-sync.md)
- For canvas navigation, zoom, pan, and object manipulation, see [references/13a-canvas-navigation.md](references/13a-canvas-navigation.md)
- For canvas elements, layers, performance, and whiteboard patterns, see [references/13b-canvas-objects-performance.md](references/13b-canvas-objects-performance.md)
- For AI and LLM interface design (chat, copilots, agents), see [references/14-ai-ux-patterns.md](references/14-ai-ux-patterns.md)
- For ethical design and dark pattern avoidance, see [references/15-ethical-design.md](references/15-ethical-design.md)
- For onboarding flows and user activation, see [references/16-onboarding.md](references/16-onboarding.md)
- For notification systems and attention management, see [references/17-notifications.md](references/17-notifications.md)
- For data visualization and dashboard design, see [references/18-data-visualization.md](references/18-data-visualization.md)
- For search interface design and autocomplete, see [references/19-search-ux.md](references/19-search-ux.md)
- For emotional design and trust-building patterns, see [references/20-emotional-design.md](references/20-emotional-design.md)
- For data tables, sortable lists, pagination, and bulk actions, see [references/21-data-tables.md](references/21-data-tables.md)
- For loading states, skeleton screens, optimistic updates, and perceived performance, see [references/22-performance-ux.md](references/22-performance-ux.md)
- For internationalization, localization, and RTL design, see [references/23-internationalization.md](references/23-internationalization.md)
- For voice, multimodal, and cross-device input patterns, see [references/24-voice-and-multimodal.md](references/24-voice-and-multimodal.md)

## Reference Values

### Layout & Typography

| Metric | Value | Context |
|--------|-------|---------|
| Touch target | 44-48px | Minimum tappable area |
| Body text | 16px+ | Minimum readable size |
| Line height | 1.2-1.45 | Optimal readability |
| Line length | 50-75 chars | Ideal for reading |
| Contrast ratio | 4.5:1 | WCAG AA for normal text |
| Contrast ratio | 3:1 | WCAG AA for large text |
| Working memory | 7±2 items | Miller's Law |
| Text expansion | ~30-40% | Translation growth (DE/FI/RU) |

### Interaction & Animation

| Metric | Value | Context |
|--------|-------|---------|
| Animation | 300-500ms | Natural feeling duration |
| Touch feedback | < 100ms | Perceived instant response |
| Form abandonment | 81% | Users who start but don't finish |
| Canvas zoom range | 10%-4000% | Typical design tool range |
| Smart guide snap | 2-8px | Distance before snapping |
| Canvas render | 60fps | Target during pan/zoom |

### Collaboration

| Metric | Value | Context |
|--------|-------|---------|
| Cursor update rate | 50-100ms | Smooth live cursor movement |
| Cursor label max | 12 chars | Truncate longer usernames |
| Avatar stack | 3-5 visible | Use "+N" for overflow |

### AI Interfaces

| Metric | Value | Context |
|--------|-------|---------|
| AI first token | < 1s | Perceived responsiveness |
| AI streaming | 30-80 tok/s | Natural reading pace |
| Copilot accept rate | 25-35% | Suggestion usefulness |

### Engagement Metrics

| Metric | Value | Context |
|--------|-------|---------|
| Onboarding completion | > 65% | Checklist finish rate |
| Time to first value | < 5 min | Sign-up to activation |
| Toast duration | 4-8s | Auto-dismiss timing |
| Search success | > 70% | Users finding results |
| NPS | > 50 | User sentiment |

## Anti-Patterns to Avoid

1. **Dark patterns** - Deceptive UI that tricks users → see [15-ethical-design.md](references/15-ethical-design.md)
2. **Infinite scroll without context** - No sense of progress → see [21-data-tables.md](references/21-data-tables.md)
3. **Hidden navigation** - Hamburger menus on desktop → see [05-information-architecture.md](references/05-information-architecture.md)
4. **Autoplaying media** - Unexpected sound/video → see [03-accessibility.md](references/03-accessibility.md)
5. **Disabled buttons without explanation** - Confusing blocked states → see [06-interaction-design.md](references/06-interaction-design.md)
6. **Walls of text** - No visual hierarchy or chunking → see [04-visual-design.md](references/04-visual-design.md)
7. **Color-only feedback** - Excludes colorblind users → see [03-accessibility.md](references/03-accessibility.md)
8. **Tiny touch targets** - Frustrating on mobile → see [08-mobile-ux.md](references/08-mobile-ux.md)
9. **No loading states** - Users think system is broken → see [22-performance-ux.md](references/22-performance-ux.md)
10. **Popup/modal overuse** - Interrupts user flow → see [06-interaction-design.md](references/06-interaction-design.md)
11. **No presence indicators** - Users don't know who else is working → see [12a-presence-awareness.md](references/12a-presence-awareness.md)
12. **Silent sync failures** - Data loss without warning → see [12b-conflict-resolution-sync.md](references/12b-conflict-resolution-sync.md)
13. **Cursor overload** - Too many live cursors create visual noise → see [12a-presence-awareness.md](references/12a-presence-awareness.md)
14. **Screen-center zoom** - Disorienting; zoom at cursor instead → see [13a-canvas-navigation.md](references/13a-canvas-navigation.md)
15. **No offline indication** - Users think they're connected when not → see [12b-conflict-resolution-sync.md](references/12b-conflict-resolution-sync.md)
16. **Hidden AI** - Users should always know when interacting with AI → see [14-ai-ux-patterns.md](references/14-ai-ux-patterns.md)
17. **Over-automation** - AI changes applied without user awareness or consent → see [14-ai-ux-patterns.md](references/14-ai-ux-patterns.md)
18. **No AI undo** - AI-applied changes must be reversible → see [14-ai-ux-patterns.md](references/14-ai-ux-patterns.md)
19. **Confirmshaming** - Guilt-laden language on decline buttons → see [15-ethical-design.md](references/15-ethical-design.md)
20. **Asymmetric consent** - Big "Accept" button, tiny "Reject" link → see [15-ethical-design.md](references/15-ethical-design.md)
21. **Mandatory lengthy tours** - Forcing users through 10+ onboarding steps → see [16-onboarding.md](references/16-onboarding.md)
22. **Notification carpet bombing** - Every event as a push notification → see [17-notifications.md](references/17-notifications.md)
23. **Permission on first visit** - Asking for push permission before user sees value → see [17-notifications.md](references/17-notifications.md)
24. **Hardcoded/untranslatable strings** - Text baked into code/images, fixed-width containers, LTR-only layout → see [23-internationalization.md](references/23-internationalization.md)
25. **Voice-only flows / hidden mic** - No fallback modality, no recognition feedback, buried voice entry → see [24-voice-and-multimodal.md](references/24-voice-and-multimodal.md)

## Sources

This skill synthesizes best practices from:
- [Laws of UX](https://lawsofux.com/) - Jon Yablonski
- [Nielsen Norman Group](https://www.nngroup.com/) - Usability research
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/) - Accessibility guidelines
- [Material Design](https://m3.material.io/) - Google's design system
- [Human Interface Guidelines](https://developer.apple.com/design/) - Apple
- [Interaction Design Foundation](https://www.interaction-design.org/)
- [Liveblocks](https://liveblocks.io/) - Real-time collaboration patterns
- [Figma Engineering Blog](https://www.figma.com/blog/category/engineering/) - Multiplayer & canvas
- [Ably](https://ably.com/blog/collaborative-ux-best-practices) - Collaborative UX
- [Google PAIR Guidebook](https://pair.withgoogle.com/guidebook) - AI design patterns
- [Microsoft HAX Toolkit](https://www.microsoft.com/en-us/haxtoolkit/) - Human-AI interaction
- [Deceptive Design](https://www.deceptive.design/) - Dark pattern catalog
- [EU Digital Services Act](https://digital-strategy.ec.europa.eu/en/policies/digital-services-act-package) - Platform regulation
- [EU Accessibility Act](https://ec.europa.eu/social/main.jsp?catId=1202) - EN 301 549 / WCAG 2.1 AA mandate
- [W3C Internationalization (i18n) Activity](https://www.w3.org/International/) - i18n/l10n standards
- [Baymard Institute](https://baymard.com/) - E-commerce UX research
- [Edward Tufte](https://www.edwardtufte.com/) - Data visualization
- [ColorBrewer](https://colorbrewer2.org/) - Colorblind-safe palettes
- [The A11y Project](https://www.a11yproject.com/) - Accessibility community resource
- [web.dev](https://web.dev/) - Core Web Vitals and performance UX
- [Smashing Magazine](https://www.smashingmagazine.com/) - Practical UX/UI patterns
