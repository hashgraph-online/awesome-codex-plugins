# Landing and Marketing Pages

How the rules apply to a page whose job is to persuade a first-time visitor — a product landing page, homepage, feature page, or launch page. The visitor is skimming, has not decided to care, and can leave at any second. Load this alongside the platform guide (usually `references/web.md`).

## Attention Is Front-Loaded

A landing page has seconds to earn a scroll. In NN/g's 2018 eyetracking study ("Scrolling and Attention", 120 participants, desktop at 1920×1080), 57% of viewing time was above the fold, 74% within the first two screenfuls, and 81% within the first three. NN/g's 2015 data ("The Fold Manifesto") found the 100px just above the fold drew 102% more views than the 100px just below it. Liu, White & Dumais 2010 (SIGIR) found visitors are most likely to leave in the first moments of a visit.

People do scroll — but only when what they see first promises it is worth it. Both studies are desktop; treat them as direction, not mobile figures.

- **Answer "why would they care?" first** — the problem the product solves or the outcome it gives, for this audience. Settle it before writing the page; every section after it is evidence for that answer, and a section that supports nothing is cut (`rules/cognitive-load.md`)
- **The top section states it** — what it is, who it is for, why they would care, and the one next step — in the user's words, not a slogan (`rules/microcopy.md`, `rules/aesthetic-usability.md`)
- **One primary call to action**, visible in the first screenful and repeated down the page; a secondary action ("See a demo") styled quieter (`rules/von-restorff.md`)

## Headings Carry the Argument

Most visitors read the headings and little else. NN/g's "Text Scanning Patterns: Eyetracking Evidence" (Pernice 2019) calls this the layer-cake pattern — eyes jump between headings and subheadings, reading body text only under the one that matters to them — and rates it the most effective way to scan.

- **A skim of the headings alone should make the whole case.** Read them in order with the body hidden; if the argument does not survive, rewrite the headings, not the body
- **Lead each heading with its most informative words** — "Invoices chase themselves" not "Features" or "Why choose us" (`rules/scanning.md`)
- **Benefits before features** — each section leads with the outcome for the visitor, then the feature that delivers it

## Order Sections by the Visitor's Questions

A first-time visitor arrives with doubts, roughly in this order: what is it, is it for me, does it work, can I trust it, what does it cost, what if it goes wrong. Each section answers the next doubt this audience actually has.

The stock sequence — hero, logo strip, three feature cards, testimonials, pricing, FAQ, final CTA — is a reasonable default, not a rule. Every generated landing page tends to use it, so pages end up interchangeable. Reorder, merge, or drop sections to match what this audience doubts most: a developer tool may need a code sample before any testimonial; an unknown brand may need proof straight after the hero; a page with one obvious objection (price, migration effort, security) answers it early rather than in the FAQ.

- **Show the real product** — screenshots or short recordings of the actual UI, not abstract illustrations, so visitors see what they are signing up for
- **Real proof next to the call to action and after a claim** — customer logos, attributed testimonials, real usage numbers (`rules/social-proof.md`); invented ones are `rules/deceptive-patterns.md`
- **Answer objections where they arise**, not only in a closing FAQ — a risk-reversal line (free plan, no card, cancel anytime) belongs beside the CTA it unblocks (`rules/reciprocity.md`)
- **No auto-rotating hero carousels** — NN/g (Nielsen 2013) found users miss content in them, and they read as ads (banner blindness). Anything that moves for more than 5 seconds needs a pause control (WCAG 2.2.2, Pause, Stop, Hide)
- **Short path to value** — sign-up with the fewest fields, or a way to try the product first (`rules/reciprocity.md`, `rules/defaults.md`)
- **Link to pricing** from the navigation — hidden pricing makes visitors assume the worst

## Load the Hero First

The first screenful is where visitors decide, so it must appear fast. The hero image is usually the page's Largest Contentful Paint; a good LCP is 2.5 seconds or less at the 75th percentile of visits, measured separately on mobile and desktop (web.dev, "Optimize Largest Contentful Paint").

- **Never lazy-load the hero image** — lazy-loading the LCP image always delays it
- **Keep it discoverable in the initial HTML** as an `<img>`; if it must be a CSS background or injected by JavaScript, preload it
- **Mark it `fetchpriority="high"`** — and no more than one or two images per page, or the hint stops meaning anything (web.dev, "Optimize resource loading with the Fetch Priority API")

## Neighbouring Skills

This guide decides what the page must say and in what order. When installed, defer to:

- a **copywriting or conversion skill** for the wording of headlines, subheads, and CTAs, and for conversion audits of a live page
- a **visual-design skill** for typography, colour, and the overall look — including steering away from the generic, templated aesthetic AI-generated pages share
