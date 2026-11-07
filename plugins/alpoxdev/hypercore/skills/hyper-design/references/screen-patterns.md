# Screen Patterns

Read when a finding concerns a landing page, marketing section, dashboard, admin panel, or signed-in view, or when a `design` or `restyle` plan reaches for a familiar section. Each entry names the default shape, why it reads as generated, and what to do instead. Rule IDs point at `references/anti-pattern-catalog.md`.

## Contents

- 1. Landing and marketing pages
- 2. App and dashboard screens
- 3. Decoration
- 4. Honest placeholders

## 1. Landing and Marketing Pages

| Pattern (rule ID) | Why it reads as generated | Instead |
|---|---|---|
| Hero, subtitle, two CTAs, screenshot, feature grid, testimonials, FAQ, CTA, footer, in that order (`structure.template-sequence`) | The order is the training-data default, not the product's story | Order sections by the product's narrative; a section without content (no real testimonials) does not exist |
| Every section is a centered title, a subtitle, and an identical card grid (`structure.uniform-rhythm`) | Sections blur together | Vary composition to match the RHYTHM dial: text-heavy and visual, symmetric and asymmetric |
| The only change between sections is the background flipping (`structure.alternating-background`) | Color does the work composition should do | Change the composition, not only the ground |
| "How it works" always three round icons with 1, 2, 3 (`structure.three-step-default`) | The real process is rarely three tidy steps | Show the real number of steps in the shape the workflow takes |
| A row of logos under the hero (`copy.unsupported-proof`) | A trust claim with no named, verifiable customer | Only real, permitted logos; otherwise no bar |
| Three pricing columns with the middle one badged "Most popular" (`structure.pricing-default`) | The shape is the default, so the emphasis means nothing | As many tiers as the product has; highlight the one that serves the goal and write why, or none |
| A page that sells a product never shown working, with no terms or privacy page (`structure.demo-without-product`) | Promises with nothing behind them | Show the real product, or say honestly that it has not shipped; signup or payment requires real legal pages |
| Product, Company, Resources, Legal footer columns (`structure.ai-footer`) | The columns come from the template | Group the links the site really has; one column can be better than four half-empty ones |
| A styled terminal window with typed commands as the hero (`quality.fake-chrome`) | A "developer tool" costume | A real screenshot for a real CLI; otherwise the real product UI |
| Gray skeleton bars as the "product shot" (`structure.skeleton-product-shot`) | Reads unfinished | A real screen with real words where the eye lands (`references/mockup-craft.md`) |
| Template FAQ ("Is my data secure?", "Can I cancel anytime?") (`structure.template-faq`) | Questions nobody from this product asked | Only real user questions; without them, no FAQ |
| The whole page dark because dark "looks tech" (`surface.dark-default`) | A trend, not a product decision | Choose the theme from brand, product type, and audience; with no fixed reason, ship a working light and dark toggle, both verified |

## 2. App and Dashboard Screens

| Pattern (rule ID) | Why it reads as generated | Instead |
|---|---|---|
| Left sidebar, top bar, four stat cards, a chart, and a table, whatever the product (`structure.dashboard-shell`) | A layout picked from memory instead of from the work the screen supports | Name the screen's job and the one decision the user makes there; build the hierarchy around it (the failing jobs are the page, the stat row a footnote) |
| Four stat cards (12,483 / 94.2% / $48.2K) with green "+12% this week" deltas (`copy.unsupported-metric`) | Decoration posing as data; the delta claims a series that does not exist | Real numbers wired to data, or the one metric that is real; a delta only with a real, named comparison period |
| "Sarah Chen updated a document, 2 hours ago" with rotating names (`structure.filler-feed`) | Invented people and events make an empty product look busy | Real events, or an honest empty state that says what to do first |
| A chart titled "Overview" placed because the space looked bare (`structure.chart-without-question`) | A chart is an answer; without the question it is texture | Write the question as the title ("Failed jobs per hour, last 24 h"); if a sentence answers better, write the sentence; segments keep 3:1 contrast |
| Name, Status, Date, Actions columns with a three-dot menu on every row (`structure.generic-columns`) | Columns come from the table component, not the data | Columns from the decision made in this table, the deciding field early; the row menu holds only actions that exist |
| Empty fields and cells filled with `John Doe`, `johndoe@example.com`, "Let's build something" (`copy.placeholder-person`) | Fabricated content disguised as real | Empty cells stay empty, or honest placeholders: `Your name`, `email@example.com`, `[REAL DATA]` |
| "No data available" with an illustration, a bare spinner, or a skeleton for a layout the data never fills (`quality.missing-states`) | The state exists but tells the user nothing | Empty says why and gives the one action that fills it; loading says what is loading; error says what failed and what to do; first run, filtered to nothing, and permission denied are different screens |

## 3. Decoration

| Pattern (rule ID) | Instead |
|---|---|
| Sparkle, star, magic wand, lightning, diamond, cube, robot, or orb as feature icons; purple as the "AI color" (`copy.ai-sparkle`) | An icon relevant to the feature, or none; show what the feature does |
| Every icon from the same default thin-stroke library (`type.default-icon-set`) | Choose the set for relevance and for the product's weight and stroke; the set is a decision |
| Emoji in headings, bullets, badges, and buttons (`copy.emoji-decoration`) | Remove them from interface text; a real icon with a reason, or nothing |
| An arrow on almost every button (`surface.arrow-everywhere`) | Keep it on the action that needs a direction cue |
| Pill + thin border + glow + dot + uppercase "AI Powered", "Beta", "New" (`surface.decorative-pill`) | A badge only for a real status; never the whole combination |
| A pill above the H1 repeating what the headline says (`structure.repeated-eyebrow`) | Cut it; fold real information into the headline or subheadline |
| A pulsing, glowing dot that marks nothing (`surface.status-dot`, `motion.pulse-without-state`) | A dot only for a real state, without glow or endless pulse |
| A thin colored stripe on the left edge of cards or rows (`surface.thick-side-stripe`) | Keep it only when it marks real state |
| Undraw, Storyset, or 3D blob characters (`surface.generic-illustration`) | A real screenshot or an illustration tied to the product |
| Blur on navbar, cards, modals, and sidebar at once; glow on everything; every element pill-shaped; large shadows everywhere (`surface.dose-exceeded`) | The dose caps in `rules/delivery-gate.md` §5 |
| An overall look copied from a well-known product the user did not ask for (`structure.product-clone`) | References inspire; the product keeps its own identity |

## 4. Honest Placeholders

When real content is missing and asking is not possible:

- logo: the product name in text in a suitable face, or `[LOGO]`
- person: initials or a simple shape, never an invented face or name
- numbers: not shown, or `[REAL DATA]`
- unfinished feature: removed, or a visible "Coming soon" label (plus a code comment)

An empty section is better than a fabricated one.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| The landing, app and dashboard, decoration, and placeholder patterns | <https://github.com/miqdadbadjuber/anti-slop> (commit `9504989`, `antislop/SKILL.md` Part 1 and R-05, R-17, R-18, R-21, R-23, R-26 to R-28, R-38; `antislop-ui/SKILL.md`; MIT, Copyright 2026 Miqdad Badjuber), rewritten for this package and mapped to its rule IDs |
| Frequency of the landing-page defaults across independent writers | `references/anti-pattern-catalog.md` Sources |

### Evidence grade

A practitioner catalog without measurement. Every pattern has a legitimate use; the catalog lists the default, and the exception is decided by the brief and the data.
