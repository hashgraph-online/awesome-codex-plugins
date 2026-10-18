# Web and SaaS

How the rules apply in a browser, from marketing pages to expert SaaS tools. A pointer and keyboard replace the thumb, screens are wide, and sessions are often long and task-focused.

## Know Which Kind of Product It Is

| | Consumer / marketing site | Expert SaaS tool |
|---|---|---|
| User | First-time, skimming, may leave any second | Repeat, trained, in the tool for hours |
| Density | Low — one idea per section | High is fine — experts want data, not whitespace |
| Shortcuts | Rarely used | Expected (keyboard shortcuts, command palette) |
| Main risk | Bounce before value is clear | Slow, repetitive work; errors at scale |

Hick's law and progressive disclosure push hardest on the consumer side; in expert tools, hiding frequently used controls to look "clean" costs more than it saves (`rules/progressive-disclosure.md` covers the trade-off).

## Navigation and Layout

- SaaS apps: a persistent sidebar (or top bar for few sections) with the current location highlighted — users must always know where they are and how to get back (`rules/jakobs-law.md`)
- Logo top-left links home; account and settings top-right or bottom of the sidebar; search top — conventions users look for first
- Keep the primary action of a page in a consistent place across pages, so it is found without searching
- Put the most-used nav items first and last; the middle of a long list is where items get lost (`rules/scanning.md`)

## Pointer, Hover, and Keyboard

- Hover is an enhancement, never the only way to discover an action — touch laptops and tablets have no hover. Wrap hover-only reveals in `@media (hover: hover)` and keep a visible alternative (`rules/signifiers.md`)
- Use real `<button>` and `<a>` elements so focus, Enter/Space, and cursor feedback come for free
- Show focus with `:focus-visible` (WCAG 2.4.7); never remove the outline without a replacement
- Expert tools: keyboard shortcuts for frequent actions, discoverable from menus and tooltips; a command palette (⌘K/Ctrl+K) for large action sets
- Clickable areas: whole rows and cards clickable when they lead somewhere; WCAG 2.5.8 sets a 24×24 CSS px minimum target

## Forms

- One column; labels above fields; group related fields (`rules/gestalt-grouping.md`)
- Long or branching forms: one question or topic per page, as the GOV.UK Design System does — fewer decisions per screen, easier error recovery
- Use `autocomplete` tokens (`email`, `name`, `tel`, `street-address`, `postal-code`, `cc-number`, `one-time-code`) so the browser fills what it knows — required for personal-data fields by WCAG 1.3.5 (`rules/defaults.md`)
- Right keyboard on mobile web: `type="email"`, `type="tel"`, `inputmode="numeric"`
- Validate when a field is left, not on every keystroke; show the error next to the field, in words that say how to fix it (`rules/microcopy.md`)
- Accept input in any reasonable format and normalise it — spaces in card numbers, dashes in phone numbers (`rules/error-prevention.md`)

## Data, Tables, and Dashboards

- Lead with the few numbers the user acts on; detail one click away
- Tables: sticky header, right-aligned numbers, sortable columns, a visible empty and loading state; keep row actions in a consistent column
- Show comparisons and change ("+12% vs last week") rather than raw numbers alone — a number without context forces the user to remember the previous one (`rules/cognitive-load.md`)
- Long operations (exports, imports, bulk edits): progress, the ability to leave the page, and a notification when done (`rules/system-status.md`)

## Landing Pages

A SaaS landing page has seconds to earn a scroll. Attention is front-loaded: in NN/g's 2018 eyetracking study ("Scrolling and Attention"), 57% of viewing time was above the fold and 74% within the first two screenfuls, and Liu, White & Dumais 2010 (SIGIR) found visitors are most likely to leave in the first moments of a visit.

- **Answer "why would they care?" first** — the problem the product solves or the outcome it gives, for this audience. Settle it before writing the page; every section after it is evidence for that answer, and a section that supports nothing is cut (`rules/cognitive-load.md`)
- **The top section states it** — what it is, who it is for, why they would care, and the one next step — in the user's words, not a slogan (`rules/microcopy.md`, `rules/aesthetic-usability.md`)
- **One primary call to action**, repeated down the page; a secondary action ("See a demo") styled quieter (`rules/von-restorff.md`)
- **Benefits before features** — each section leads with the outcome for the user, then the feature that delivers it (`rules/scanning.md`)
- **Show the real product** — screenshots or short recordings of the actual UI, not abstract illustrations, so visitors see what they are signing up for
- **Real proof next to the call to action** — customer logos, attributed testimonials, real usage numbers (`rules/social-proof.md`); invented ones are `rules/deceptive-patterns.md`
- **No auto-rotating hero carousels** — NN/g (Nielsen 2013) found users miss content in them, and they read as ads (banner blindness). Anything that moves for more than 5 seconds needs a pause control (WCAG 2.2.2, Pause, Stop, Hide)
- **Short path to value** — sign-up with the fewest fields, or a way to try the product first (`rules/reciprocity.md`, `rules/defaults.md`)
- **Link to pricing** from the navigation — hidden pricing makes visitors assume the worst

## Pricing and Plan Choice

- Three or four plans, one marked as recommended; compare on the few features that actually differ (`rules/hicks-law.md`)
- Anchoring and the decoy effect (Huber, Payne & Puto 1982) are real: a higher-priced plan makes the middle one look reasonable. Use them only with plans someone could genuinely want — a plan built to be unattractive is a deceptive pattern (`rules/deceptive-patterns.md`)
- Show the price the user will actually pay, including billing period and tax treatment; annual discounts shown as both the monthly equivalent and the annual total
- Cancellation must be as easy as sign-up — the FTC and EU both treat hard-to-cancel flows as dark patterns

## First Run and Empty States

- An empty dashboard is the first screen most SaaS users see: explain what will appear there and give the one action that fills it (`rules/microcopy.md`)
- Offer sample data or a template so value appears before setup work (`rules/reciprocity.md`)
- Setup checklists work — show real completed steps (account created ✓) and keep them short (`rules/goal-gradient.md`)

## Banners and Announcements

Anything shaped or placed like an ad — top banners, right-rail boxes, animated badges — is ignored (banner blindness, `rules/scanning.md`). Put important announcements inline, where the affected feature is.

## Response Times

- Under ~0.1 s feels instant — use for hover, press, toggle feedback
- Up to ~1 s keeps flow — show a subtle busy state
- Beyond ~1 s show progress; beyond ~10 s show percent or steps and let the user do something else

Skeleton screens and optimistic updates make waits feel shorter (`rules/system-status.md`).
