# Anti-pattern Catalog

Load this catalog only when mapping detector output or a rendered observation to a rule. The registry is a judgment aid, not a universal ban list. `autofix` means a deterministic replacement may be safe only after the stated exception check.

## Contents

- Rule table
- Registry interpretation
- Second wave and review date
- Sources

## Rule table

| ID | Category | Scope | Default severity | Static | Autofix | Pattern and exception |
|---|---|---|---|---:|---:|---|
| `surface.gradient-text` | surface | default-risk | P2 | yes | no | Gradient-clipped headline; preserve explicit brand/reference typography |
| `surface.purple-gradient` | surface | default-risk | P2 | yes | no | Purple→blue/pink gradient; preserve documented brand tokens |
| `surface.random-glow` | surface | review-only | P3 | partial | no | Glow without hierarchy/brand role |
| `surface.decorative-orb` | surface | default-risk | P2 | partial | yes | Orb/blob without content, interaction, semantic, or brand role |
| `surface.thick-side-stripe` | surface | default-risk | P2 | yes | no | Thick colored card edge without meaning |
| `surface.uniform-radius` | surface | context-dependent | P3 | partial | no | One radius on every hierarchy level; design-system token may justify it |
| `surface.uniform-shadow` | surface | context-dependent | P3 | partial | no | Same elevation everywhere; explicit elevation system may justify it |
| `surface.status-dot` | surface | default-risk | P3 | partial | yes | Dot without state or legend |
| `surface.version-label` | surface | default-risk | P3 | partial | yes | Decorative “v2.0/new” label without product meaning |
| `surface.decorative-pill` | surface | default-risk | P3 | partial | yes | Image/heading pill with no category, state, or action role |
| `surface.token-drift` | surface | default-risk | P2 | partial | no | Literal color/font outside confirmed tokens; local exception may exist |
| `structure.three-equal-cards` | structure | context-dependent | P1 | partial | no | Three identical icon-heading-copy cards; preserve real three-peer comparisons |
| `structure.card-in-card` | structure | default-risk | P2 | yes | no | Nested presentation cards without semantic grouping |
| `structure.centered-hero` | structure | review-only | P3 | partial | no | Repeated centered hero; page purpose may require it |
| `structure.template-sequence` | structure | review-only | P2 | no | no | Hero→3 features→CTA→footer without product-specific information architecture |
| `structure.ai-nav` | structure | review-only | P3 | partial | no | Wordmark-left, links-middle, CTA-right fingerprint |
| `structure.ai-footer` | structure | review-only | P3 | partial | no | Generic Product/Company/Resources/Legal four-column footer |
| `structure.bento-without-ia` | structure | context-dependent | P2 | partial | no | Bento placement unrelated to priority or data |
| `copy.placeholder-person` | typography-copy | default-risk | P1 | yes | yes | John/Jane Doe or obvious fake testimonial identity |
| `copy.placeholder-brand` | typography-copy | default-risk | P1 | yes | yes | Acme/Nexus/SmartFlow-like placeholder presented as real brand |
| `copy.cliche` | typography-copy | context-dependent | P3 | yes | no | Elevate, seamless, next-gen, unleash, game-changer; quote/domain use may be valid |
| `copy.unsupported-metric` | typography-copy | default-risk | P1 | partial | yes | Percentage/metric claim with no local source |
| `copy.unsupported-proof` | typography-copy | default-risk | P1 | partial | yes | Testimonial, trust badge, proof bar, or claim without source |
| `copy.repeated-eyebrow` | typography-copy | review-only | P3 | partial | no | Uppercase eyebrow on every section |
| `motion.transition-all` | motion-interaction | universal | P2 | yes | yes | Broad transition; replace with the properties that actually change |
| `motion.layout-property` | motion-interaction | universal | P1 | yes | no | Animates top/left/width/height/margin/padding |
| `motion.missing-reduced-motion` | motion-interaction | universal | P1 | partial | no | Significant motion with no reduced-motion path |
| `motion.scale-everywhere` | motion-interaction | default-risk | P2 | yes | no | Same hover scale on unrelated controls/cards |
| `motion.hover-only` | motion-interaction | universal | P1 | partial | no | Essential affordance or content available only on hover |
| `quality.missing-focus-visible` | quality | universal | P1 | partial | no | Visible controls have focus suppression and no clear replacement |
| `quality.missing-alt` | quality | universal | P1 | partial | no | Informative image lacks alt; decorative image may need empty alt |
| `quality.mobile-overflow-risk` | quality | universal | P1 | partial | no | Fixed/min-width likely to overflow; rendering must confirm |
| `quality.fake-chrome` | quality | default-risk | P2 | yes | no | Browser/phone/IDE/terminal chrome used as unsupported decoration |
| `structure.repeated-eyebrow` | structure | review-only | P3 | yes | no | Repeated eyebrow/kicker signature; preserve labels that carry real hierarchy or sequence |
| `structure.numbered-section-label` | structure | context-dependent | P3 | yes | no | 01/02/03 markers; preserve a sequence users must follow |
| `structure.identical-icon-card-cluster` | structure | context-dependent | P2 | yes | no | Three feature-card/icon-tile signatures; preserve genuine peer data and actions |
| `surface.radial-glow` | surface | review-only | P3 | yes | no | Radial glow signature; preserve purposeful lighting or brand material |
| `surface.grid-background` | surface | review-only | P3 | yes | no | Repeated gradient grid; preserve real map/canvas/blueprint context |
| `surface.border-plus-wide-shadow` | surface | context-dependent | P3 | yes | no | Border plus wide shadow; preserve documented elevation systems |
| `type.decorative-monospace` | typography-copy | default-risk | P3 | yes | no | Monospace with decorative technical language; preserve code, IDs, logs, measurements, and real state |
| `motion.pulse-without-state` | motion-interaction | default-risk | P2 | yes | no | Pulse signature; preserve recording, sync, unread, notification, or live state |
| `quality.heading-skip` | quality | universal | P2 | yes | no | Static h1→h3 heading skip; component composition may require review |
| `type.unchosen-default-font` | typography-copy | default-risk | P3 | no | no | Inter, Roboto, a system stack, or a fashionable display face used everywhere with no reason in the brief or system; preserve a documented brand face |
| `type.font-not-shipped` | quality | universal | P2 | partial | no | A declared face the build never loads, so the screen falls back silently; preserve system stacks declared on purpose |
| `surface.second-wave-default` | surface | review-only | P3 | no | no | Cream background with an italic serif display, emerald "safe" accent, or neobrutalist hard offset shadow used as the escape from the first-wave look; preserve when the brief or reference calls for it |
| `structure.bento-escape` | structure | context-dependent | P2 | no | no | Bento grid whose tile sizes do not follow priority or data; preserve a bento that encodes real priority |
| `copy.ai-sparkle` | typography-copy | default-risk | P3 | no | no | Sparkle, wand, or star icon and purple as the "AI color"; preserve when the brand already uses that mark |
| `quality.missing-states` | quality | universal | P1 | no | no | Loading, empty, or error state missing or left blank; preserve deliberate absence only when the surface cannot reach that state |
| `quality.contrast-below-floor` | quality | universal | P1 | no | no | Text or a required non-text element under the contrast floor; rendering or token math must confirm |
| `structure.mockup-boxed` | structure | review-only | P2 | no | no | Faux product window shrunk into a card with even margins; preserve when the slot itself is a card thumbnail |
| `quality.focus-suppressed` | quality | universal | P1 | yes | no | `outline: none` or `focus:outline-none` source signature; preserve when an equally visible `:focus-visible` replacement exists |
| `quality.zoom-blocked` | quality | universal | P1 | yes | no | Viewport meta with `user-scalable=no` or `maximum-scale=1`; no exception |
| `quality.clickable-div` | quality | universal | P1 | yes | no | `div` or `span` with a click handler; preserve only a custom control that has a role, state attributes, and keyboard support |
| `quality.dead-anchor` | quality | universal | P2 | yes | no | `href="#"` with no destination; preserve a real in-page anchor written as `#id` |
| `quality.media-unsized` | quality | universal | P2 | yes | no | `img`, `video`, or `iframe` with no width, height, or aspect-ratio; preserve when CSS on the element sets an aspect ratio |
| `copy.em-dash` | typography-copy | default-risk | P3 | yes | no | Em dash in source text; preserve quoted sources and an owner-approved voice sample |
| `copy.generic-cta` | typography-copy | context-dependent | P3 | yes | no | "Get started", "Learn more", "Try now", "Explore", "Discover" as the label; preserve a label the brand guide requires |
| `structure.viewport-height` | structure | context-dependent | P3 | yes | no | `100vh` or `h-screen` section; preserve a deliberate full-screen view that uses `dvh` on mobile |
| `quality.dead-control` | quality | universal | P1 | no | no | Button, link, dropdown, or form with no real behavior, or a nav item with no destination; preserve a visibly labelled "Coming soon" |
| `quality.theme-broken` | quality | universal | P1 | no | no | A shipped light or dark theme that breaks contrast, fonts, or layout |
| `quality.patch-script` | quality | universal | P1 | no | no | A feature added by a script that rewrites source or CSS with string replacement |
| `copy.fabricated-claim` | typography-copy | universal | P1 | no | no | Security, compliance, performance, or customer claim with no evidence |
| `copy.assumed-asset` | typography-copy | default-risk | P1 | no | no | Logo, avatar, product mark, or photo of people created as final without confirmation; preserve labelled placeholders |
| `copy.emoji-decoration` | typography-copy | default-risk | P3 | no | no | Emoji in headings, bullets, badges, or buttons; preserve emoji that are user content |
| `structure.template-faq` | structure | universal | P2 | no | no | FAQ of template questions not asked by this product's users |
| `structure.uniform-rhythm` | structure | context-dependent | P2 | no | no | Every section the same title + subtitle + card grid; preserve when RHYTHM 1 is the declared choice |
| `structure.alternating-background` | structure | review-only | P3 | no | no | The only variation between sections is the background color |
| `structure.three-step-default` | structure | context-dependent | P3 | no | no | "How it works" always three numbered round icons; preserve when the real process has three steps |
| `structure.pricing-default` | structure | context-dependent | P2 | no | no | Three tiers with the middle badged "Most popular" whatever the real plans; preserve the real plan count and a reasoned highlight |
| `structure.demo-without-product` | structure | default-risk | P1 | no | no | A page selling a product never shown working, or signup with no terms or privacy page |
| `structure.skeleton-product-shot` | structure | default-risk | P2 | no | no | Skeleton bars used as the hero or feature "screenshot" |
| `structure.dashboard-shell` | structure | context-dependent | P2 | no | no | Sidebar + top bar + four stat cards + chart + table chosen before the screen's job |
| `structure.filler-feed` | structure | universal | P1 | no | no | Activity feed of invented people and events |
| `structure.chart-without-question` | structure | review-only | P3 | no | no | Chart with a generic title and no question it answers |
| `structure.generic-columns` | structure | review-only | P3 | no | no | Name / Status / Date / Actions columns regardless of the data |
| `structure.product-clone` | structure | default-risk | P2 | no | no | Overall look copied from a well-known product the user did not ask for |
| `surface.dark-default` | surface | context-dependent | P3 | no | no | Dark theme only because it looks technical; preserve developer, media, and creative tools with a stated reason |
| `surface.arrow-everywhere` | surface | review-only | P3 | no | no | Arrows on almost every button |
| `surface.generic-illustration` | surface | default-risk | P3 | no | no | Stock or 3D blob illustrations with no connection to the product |
| `surface.dose-exceeded` | surface | default-risk | P2 | no | no | Blur on navbar, cards, modals, and sidebar together, glow on everything, pill shapes on every element, or large shadows everywhere |
| `type.default-icon-set` | typography-copy | review-only | P3 | no | no | Every icon from one default thin-stroke library with no decision behind it |

## Registry interpretation

Static `yes` means the bundled detector can find a source signature, not that the UI is defective. `partial` means source heuristics need context or rendering. Browser-only and subjective patterns remain reportable only with an explicit warrant and caveat. For remediation steps, load `fix-playbook.md`.

Detector v2 reports `engine`, `evidenceKind`, detection/remediation confidence, cluster, and exception status. A `candidate` exception remains a visible review item; it does not suppress a finding or authorize automatic removal.

## Second wave and review date

The rows from `type.unchosen-default-font` to `structure.mockup-boxed`, and every row after `structure.viewport-height` whose Static column is `no`, are review rules: the bundled detector does not emit them, and they are reported from source reading, the delivery gate, the craft-floor checklist, or the independent review. Defaults change each year; re-read the sources below and this table at least every six months. `references/screen-patterns.md` gives the instead-of for the landing, dashboard, and decoration rows.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| The detector rule IDs, categories, scopes, severities, and exception notes | this package's own registry, implemented by `scripts/rule-registry.sh` |
| Frequency of the recurring defaults (purple gradient, default font, identical icon cards, glow, gradient text, eyebrow, uniform radius) across ten publishers | <https://github.com/febbhav/signs-of-ai-design/tree/854b46f18dee5cc174d45cec8cd4f3142fe46984>, <https://www.adriankrebs.ch/blog/design-slop/>, <https://www.925studios.co/blog/ai-slop-design-tells>, <https://github.com/ch040602/anti-ai-slop> |
| Second-wave defaults and their eras | <https://impeccable.style/slop/>, <https://solodesign.cc/blog/ai-design-slop-the-tells/> |
| A declared font must exist in the build | <https://tailthemes.com/blog/ai-design-slop-quality-gate> (2026-08-20) |
| AI features shown without sparkle icons or a purple AI color; a boxed window reads as a pasted screenshot | <https://github.com/benjitaylor/skills> (`stageshow` folder, commit `299140f`) (MIT) |
| The detector rows from `quality.zoom-blocked` to `structure.viewport-height` and the review rows after them (dead controls, broken themes, patch scripts, fabricated claims, assumed assets, template FAQ, section rhythm, pricing and three-step defaults, dashboard shell, filler feed, charts without a question, generic columns, product clones, dark default, arrows, illustrations, dose caps, default icon set) | <https://github.com/miqdadbadjuber/anti-slop> (commit `9504989`, `antislop/SKILL.md` Part 1 and R-01 to R-40, `antislop-ui/SKILL.md`; MIT, Copyright 2026 Miqdad Badjuber). The IDs, scopes, and severities are this package's own. |

### Evidence grade

Frequencies come from a convenience sample of 2025-2026 writing, much of it by vendors of anti-slop tooling. They order the catalog; they do not prove prevalence.
