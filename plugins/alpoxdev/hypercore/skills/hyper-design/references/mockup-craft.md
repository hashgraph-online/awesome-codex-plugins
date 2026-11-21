# Mockup Craft

Read in `mockup` mode. Faux product UI is an illustration of a product, built in the project's own stack (HTML and CSS, or the existing component framework), still or animated. It is not a working client, not browser automation, and never calls a live service.

## Contents

- 1. The idea
- 2. Five failure modes
- 3. Plan before code
- 4. The screen
- 5. Framing
- 6. Icons, marks, and color
- 7. Motion and the cursor
- 8. Verification

## 1. The Idea

A mockup reads as a real product, simplified to what the viewer needs, framed with intent, and every motion has a cause. Simplify the words, not the context: a full, structured screen in quiet neutrals, real words only on what the story is about, placeholder lines for the rest.

## 2. Five Failure Modes

| Failure | Looks like | Fix |
|---|---|---|
| Too much | real text in every row, numbers everywhere | count the real strings; turn the rest into placeholder bars |
| Wireframe | two gray blocks and a button | give the screen its full structure: navigation, panes, rows |
| Boxed | a whole window shrunk into a card with even margins | crop the window and let it run off one or two edges |
| Flat | every object the same weight in the same bordered card | one hero object; supporting objects lighter and smaller |
| Bland | a gray window with a cursor, unrelated to the brief | show the product's own look and the one action the brief is about |

## 3. Plan Before Code

Write into `brief.md`:

1. Medium and place: still or animation (loop, once in view, on hover); the slot size it will be shown at.
2. Look: map the product's tokens (canvas, surface, text levels, line, accent, radius, control and row height); do not invent a palette.
3. Story (animation only): three to five beats and a payoff; no cursor move without a reason; data never rewinds in view without a cause.
4. The one action and what is left out.

Design at the size it is shown. A narrow mobile slot gets its own compact layout, not a scaled-down desktop.

## 4. The Screen

| Rule | Value |
|---|---|
| Real strings | about 3 to 7: the title, the thing acted on, what is typed, the result |
| Placeholder bars | only away from where the eye lands; widths vary row to row (for example 60, 45, 70, 52%) |
| UI text | 11-15px at real size, scaled with the stage; never unreadably small |
| Line height of small text | at least 1.3 |
| Text inset | about 12px from the edge of a window, card, panel, or hovered row; under 8px is a defect |
| Row padding | 12px, 8px for dense lists |
| Big numbers | one number is allowed to be big; a number and its unit never wrap apart |
| Family and case | one family; sentence case |
| Headings | a faux app's title is not a document heading (`h1`-`h6`) on the host page |
| Alignment | no near-tangents: edges either align or sit clearly apart, never 1-3px off |

## 5. Framing

- One hero object, at most two satellites, and the satellites are different kinds.
- Crop roughly 10-40% of the hero off the stage; the hero fills at least two thirds of the stage width and runs off an edge.
- One gutter, measured in the final crop; a gutter that misses by a few pixels reads as a mistake.
- No plate behind a window on a white page, no dead corners, and no outline around the hero to point at it (it reads as a focus state nobody gave).
- A window keeps its device's shape; never draw platform chrome (status bars, home indicators, window controls) from memory: use the platform's real proportions from a screenshot or the project's assets.

## 6. Icons, Marks, and Color

- Icons come from one set, one stroke weight, one size (about 14-16px in UI); never hand-drawn glyphs; small icons filled; one color.
- Emoji are content, never icons.
- AI features get no sparkle, wand, or star icon and no purple "AI color"; show what the feature does.
- No invented logo: a letter in a colored square is not the product's mark. Use the product's real mark from the project, or a plain wordmark in the product font. Never reproduce third-party trademarks or app icons.
- A few ink levels and one accent; a gradient or glow serves the story or goes; nothing translucent overlaps other content.

## 7. Motion and the Cursor

| Rule | Value |
|---|---|
| Loop length | 10-16 s for a hero loop |
| Stagger | 40-80 ms between related items in reading order |
| Payoff | holds about 2 s; nothing sits still for more than about 3 s |
| Speed | UI feedback stays as fast as the real product; only storytelling motion slows |
| Continuity | a loop never plays a navigation backwards; the next action starts within about a second of the seam |
| Changes | change only what changed; solid objects do not fade through each other; nothing pops in |
| Cursor | travels to the next action; never covers the words it clicks; changes kind at the element edge; rests then fades |
| Reduced motion | show the payoff frame as a still |

## 8. Verification

- Set the still or poster frame first; it must tell the story alone.
- Capture the stage at its shown width and at a narrow width; answer every question from a frame you looked at, never from the code.
- Run the independent review (`rules/independent-review.md`) with the failure modes in §2 as its checklist.
- Fix the largest visible failure first, re-capture, and repeat within the budget.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| The idea, the five failure modes, the plan-first steps, the screen and framing numbers, the icon and mark rules, the motion and cursor rules, and answering from frames | <https://github.com/benjitaylor/skills> (`stageshow` folder, commit `299140f`) (`SKILL.md`, `references/craft.md`, `references/framing.md`, `references/motion.md`, `references/verify.md`; MIT, Copyright 2026 Benji Taylor). Rewritten in this package's words; no code, kit component, app icon, or brand asset was copied, and the source's `NOTICE.md` excludes its app icons and brand marks from the MIT license. |
| The source author describes part of the rule set as personal taste | <https://benji.org/stageshow> (2026-10-31) |

### Evidence grade

The numbers are one designer's tuned defaults for marketing illustrations, not standards. Treat them as starting values and re-derive them for unusual slots.
