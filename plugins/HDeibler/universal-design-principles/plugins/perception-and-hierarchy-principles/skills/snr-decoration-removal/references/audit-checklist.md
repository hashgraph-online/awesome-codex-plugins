# Decoration-removal: extended audit checklist

A reference complementing `snr-decoration-removal` with a more granular audit method and patterns from teams that have run subtraction passes at scale.

## The expanded audit

For each visible element on a screen, run through:

```
1. PURPOSE
   [ ] Does this element have a clearly statable purpose?
   [ ] If purpose = "decoration," can I cut it?
   [ ] If purpose = "branding," can it move to chrome (header/footer) instead?

2. REDUNDANCY
   [ ] Does this element duplicate information already shown nearby?
   [ ] If it provides redundant signal for accessibility, keep it.
   [ ] If it's redundant for emphasis, evaluate whether the emphasis is earning its space.

3. DISCOVERABILITY (inverse check)
   [ ] If I removed this, would users be unable to find a feature they need?
   [ ] If the answer is "they'd find it via the menu / palette," cut it.
   [ ] If "they'd never find it," keep it but consider whether it should be smaller.

4. STATE-DEPENDENT
   [ ] Is this element shown when its state is the default? If yes, why?
     - Status icon for "active" when 99% of items are active = noise.
     - Loading spinner that never appears = harmless dead code.
     - Notification dot when count = 0 = noise; hide when zero.

5. AESTHETIC INVESTMENT
   [ ] Is this element here because the design "felt empty"?
   [ ] If yes, reconsider — empty space is valid; gratuitous fill isn't.
```

## Subtraction patterns from real redesigns

### Twitter's iconic-action redesign (2010s onward)

Original interface: each tweet showed Reply / Retweet / Like / Share / More icons inline. Audit: are all 5 visible on every tweet? Yes. Cut decorations? Reduced icon visual weight, shifted to outline-only style, increased spacing. Same actions, less ink.

### Apple Notes redesign (across versions)

Early versions: linen-textured backgrounds, leather-bound legal-pad metaphor, decorative line ruling. Later versions: pure white background, no decoration. Same functionality, much higher SNR.

### Linear's chrome reduction

Linear's editor (2018+) systematically stripped chrome that competing project-management tools defaulted on: heavy borders, status badges everywhere, action icons on every row. Result: visually quieter than Jira/Asana while showing the same information.

The pattern: subtraction is *easier in greenfield* than retrofitting. Existing products accumulate chrome over years; new products start with discipline.

## What teams reliably resist subtracting

Some categories survive most audits because subtraction is politically expensive:

- **Brand marks.** Marketing protects brand visibility; subtracting any brand mark requires sponsorship.
- **Stakeholder pet features.** A button placed there because someone in leadership wanted it; cutting it requires negotiation.
- **Compliance footers.** Cookie banners, terms links, copyright. Genuinely required, but can usually be visually demoted (smaller, lower-contrast).
- **A/B-tested additions.** Once an element shows even small lift in A/B test, removing it is hard. Aggregate decoration accumulates this way.

A useful tool: a periodic "subtraction sprint" with senior support, treating subtraction as a positive feature rather than a removal of someone's work.

## Subtraction in non-software contexts

### Editorial design

Magazines like *The Economist* and *Monocle* are notable for restraint: minimal kicker treatments, no rule overload, no callout boxes for every quote. The magazines that survived the print-decline era often did so by leaning into restraint as identity.

### Industrial product design

Dieter Rams' "Less, but better" and Apple's product-design lineage are both subtraction-as-discipline: every visible element earns its place; the rest is removed.

### Architecture

Mies van der Rohe's "Less is more" and the Modernist movement broadly applied subtraction to architecture. The cost: spaces that feel cold without decoration. The reward: clarity, durability, agelessness.

The lesson: subtraction without warmth produces cold UIs. Combine subtraction with thoughtful detail (good typography, generous whitespace, occasional warm flourishes) for "less, but better."

## Resources

- **Maeda, J.** *The Laws of Simplicity* (2006). Ten laws of simplification, applicable beyond software.
- **Krug, S.** *Don't Make Me Think* — practical web subtraction patterns.
- **Refactoring UI** — many before/after examples of subtraction passes.

## Closing

A subtraction pass is the cheapest design improvement available: no new content to create, no engineering cost beyond the deletes. It's also the hardest to schedule, because it doesn't ship a "feature." The teams that allocate time for it consistently produce visibly better products.
