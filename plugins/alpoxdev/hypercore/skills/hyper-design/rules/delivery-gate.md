# Delivery Gate

Read before handing over the result of `design`, `restyle`, `mockup`, or `clean`, and before writing the findings of `audit` or `verify`. This file owns the final pass/fail list, the evidence each line needs, and what happens when a line fails.

## 1. Principle

Two questions decide every item on this page:

- **Purpose:** what does this technique serve? A gradient, a glow, a card grid, a badge, or a motion is allowed when it serves hierarchy, identity, readability, or state, and the reason is written down in `brief.md`. "It looks modern" and "it is the default" are not reasons.
- **Liveliness:** removing generic patterns leaves a void, and the model fills a void with its most generic output. A clean but lifeless screen also fails; liveliness is added on purpose (§6).

Done means three things at once: every technique has a written purpose, the screen has its own identity, and it actually works.

## 2. How to Run the Gate

- Write the gate as a table in the report's `## 검증` section: item, `PASS | FAIL | n/a | not run`, and the evidence.
- A `PASS` without evidence is not a pass. Evidence is a file and line, a command and its output, a capture with viewport and state, or a recorded click-through ("Signup -> /signup, no console errors"; "empty form -> validation message"; "mobile menu -> opens and closes with Escape").
- When the deliverable cannot be run (a static mockup, source only), say so and verify each control by reading the code; mark rendered items `static_only`.
- Any `FAIL` blocks delivery. Fix it within the mode's correction budget (`rules/workflow.md` §4) and run the gate again; when the budget is spent, report the open lines instead of delivering.
- In `audit`, each failing line becomes a numbered finding; in `clean`, only Block 1 and the lines the edit touched are run.
- Another workflow leading the session never replaces this gate. Its own summary does not count as the gate.

## 3. Block 1: Honesty and Function (absolute)

Every answer must be **no**. These lines hold even when the brief asks otherwise; a conflict is raised with the owner, never resolved silently.

| # | Question | Rule |
|---|---|---|
| H1 | Is any number, statistic, delta, testimonial, customer logo, person, security or compliance claim, or performance figure shown without a real source? | `copy.unsupported-metric`, `copy.unsupported-proof`, `copy.fabricated-claim` |
| H2 | Is any realistic-looking content fabricated (features, team, activity feed entries, table rows, form values such as `John Doe`) instead of real or clearly labelled as placeholder (`[REAL DATA]`, "Coming soon")? | `copy.placeholder-person`, `structure.filler-feed` |
| H3 | Was a logo, avatar, product mark, or illustration of people created as if final without the owner's confirmation? | `copy.assumed-asset` |
| H4 | Does any button, link, dropdown, or form do nothing, or does a navigation item point to a page or section that does not exist? A placeholder needs a visible "Coming soon" label. | `quality.dead-control`, `quality.dead-anchor` |
| H5 | Does a data view lack its empty, loading, or error state, or do those states fail to say the cause and the next action? | `quality.missing-states` |
| H6 | Does an FAQ hold template questions that are not this product's users' real questions? | `structure.template-faq` |
| H7 | Does any shipped theme (light or dark) break colors, contrast, fonts, or layout? | `quality.theme-broken` |
| H8 | Was a feature added by a script that rewrites source or CSS with string replacement instead of being written in source? | `quality.patch-script` |
| H9 | Does the overall look copy a named popular product the user did not ask for? | `structure.product-clone` |
| H10 | Was the result delivered without being built or run, without the console checked, or without a recorded click-through of every interactive element? | `rules/validation-and-reporting.md` |
| H11 | Was a Lighthouse score or Core Web Vitals number reported that was not measured in this run? | `rules/craft-floor.md` §8 |

## 4. Block 2: Craft Floor (absolute)

Every item of `rules/craft-floor.md` §9 is `pass`, `n/a`, or `static_only` with a reason. The items most often skipped:

- every text pair computed with `references/contrast-check.md`, including text over images and gradients, checked at the worst point
- every control reachable by keyboard with a visible focus indicator; no `outline: none` without a replacement
- every enabled control shows `cursor: pointer`, is a native element, has an accessible name, and has distinct hover, active, and disabled states (`references/accessible-interaction.md`)
- no horizontal overflow, nothing clipped, and targets at least 24×24 CSS px (44 px on touch surfaces) with space between them at the narrowest width (`references/responsive-reflow.md`)
- every media element sized, the hero image not lazy, no render-blocking third-party script

## 5. Block 3: Purpose and Dose (technique allowed, reason required)

Each line fails only when the technique appears as a default with no written reason in `brief.md`, or past its dose cap.

| # | Technique | Pass when |
|---|---|---|
| P1 | Gradient, glow background, radial orb, purple or neon palette | It is brand identity or separates one hierarchy level from another, and the reason is written |
| P2 | Icons | Each icon is relevant to its content; the set is a decision, not the library default; no sparkle, wand, star, robot, or orb for "AI" |
| P3 | Typeface | The face is chosen from the brand or reference with a written reason, not because it is a model default |
| P4 | Background texture, grid, dot, or blueprint pattern | It supports the product's identity or a real canvas |
| P5 | Arrows on buttons | Only on the action that needs a direction cue |
| P6 | Badges, pills, status dots | Each marks a real status or label; never pill + thin border + glow + dot + uppercase together |
| P7 | Glass or backdrop blur | At most one or two elements; never navbar, cards, modals, and sidebar together |
| P8 | Shadow | It marks elevation for the few elements that lift; most surfaces sit flat |
| P9 | Glow | At most one or two focus elements; never on cards, buttons, badges, icons, borders, and background together |
| P10 | Card grids | Card size and treatment follow content weight; not every item is a card |
| P11 | Motion | Each motion has a written purpose and matches the MOTION dial; no endless loop without a real state |
| P12 | Illustrations | Each one connects to the product; otherwise a real screenshot or nothing |
| P13 | Palette | At most two or three core colors plus one accent, neutrals not counted, unless a documented system says otherwise |

## 6. Block 4: Liveliness (must be present)

Every answer must be **yes**.

| # | Question |
|---|---|
| L1 | Was the Design Read declared and the three dials (ENERGY, RHYTHM, MOTION) set in `brief.md` before building? |
| L2 | Does the result match its dials (RHYTHM 3 with identical sections fails; MOTION 1 with scroll choreography fails)? |
| L3 | Does each screen have exactly one clear focal point? |
| L4 | Is whitespace used as structure (grouping and rhythm), not left over? |
| L5 | Is there one deliberate accent: not zero, not everywhere? |
| L6 | Is there one identity motif: a specific, repeated pattern, gesture, or typographic voice? |
| L7 | If the logo and product name were swapped out, would the design still feel like this product and no other? |

A design built without direction and without a chance to ask is labelled "draft without direction", uses the honest dials ENERGY 1 / RHYTHM 1 / MOTION 1, and is never presented as a deliverable (`rules/design-direction.md` §10).

## 7. Conflicts With the Brief

When `DESIGN.md`, a brand guide, or the user's own sample asks for something a Block 1 line forbids, or for a pattern in Block 3 with no stated reason, do not follow it silently and do not override it silently: name the element, name the line it meets, ask once, and record the answer in `brief.md`. A bold palette or an unusual typeface is identity, never a conflict.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| The purpose test, the liveliness bar, the three-part definition of done, the Hard Gate / Purpose-Gate / Liveliness / Quality blocks, the dose caps, evidence for every PASS, the recorded click-through, the conflict protocol, and "the gate cannot be replaced by another workflow" | <https://github.com/miqdadbadjuber/anti-slop> (commit `9504989`, `antislop/SKILL.md` Parts 1-3 and Delivery Gate; MIT, Copyright 2026 Miqdad Badjuber). Rewritten for this package and mapped to its own rule IDs; the source's R-01 to R-40 numbering is not reused. |
| A builder grading its own output favors the median, so the gate asks for evidence rather than a verdict | `rules/independent-review.md` |

### Evidence grade

`LOCAL` - the gate is this package's adaptation. The source states the blocks and caps as its own design; no study measures the caps (for example "one or two glass elements").
