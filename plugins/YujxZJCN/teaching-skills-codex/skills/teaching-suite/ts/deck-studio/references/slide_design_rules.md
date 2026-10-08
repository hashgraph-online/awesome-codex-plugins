# Slide Design Rules

The rulebook deck-studio *enforces*, not suggests. Every rule below derives from the
cognitive-load and multimedia evidence (Pedagogy Foundations §9) or the accessibility
baseline (§7 / Quality Gate U1). Agents apply these silently in artifacts and cite the
check id (R1, R2…) when flagging; `restyle` mode reports against the full checklist
like a gate. The professor can overrule any rule with a logged reason (Checkpoint
Protocol) — what they cannot get is a deck that violated one silently.

## R1 — Legibility floor: 24pt body, contrast-checked

Body text never renders below **24pt-equivalent** at projection scale; 28pt is the
comfortable default. Titles ≥36pt. Code ≥20pt only when the excerpt is ≤8 lines and
the room is known. "It fits if we use 18pt" means the slide has too much content, not
that the floor moves.

**Projection legibility table** (full-size slide, typical lecture hall):

| Element | Floor | Comfortable | Legible from |
|---------|-------|-------------|--------------|
| Title | 36pt | 40–44pt | back row, any hall |
| Body text | 24pt | 28–32pt | ~15 m |
| Figure axis labels | 18pt-equiv after scaling | 20pt-equiv | ~12 m |
| Code | 20pt | 24pt | ~10 m — prefer shorter excerpts over smaller type |
| Captions/credits | 16pt | 18pt | front half — never load-bearing content |

Rule of thumb when the hall is unknown: stand 2 m from a 13″ laptop showing the slide;
if you can't read it, row 20 can't either.

## R2 — One idea per slide

Each slide makes exactly one point. Two points sharing a slide compete for the same
working memory (§9 segmenting); the fix is a split, a merge into a genuinely single
larger point, or a cut — never a denser layout. Corollary: a slide whose point you
cannot state in one sentence does not have one yet.

## R3 — Assertion-evidence pattern

**Title = the claim, stated as a sentence. Body = the evidence for that claim** — a
figure, a worked step, a minimal table or code excerpt. "Hash collisions are
inevitable; the design choice is how to resolve them" — not "Hash Collisions."
A reader skimming only the titles gets the argument of the lecture. Topic-phrase
titles are permitted only on structure slides (title, dividers, agenda); a derived
assertion title (written by deck-studio, not the outline) is always flagged
`[DERIVED TITLE]` for the professor to confirm.

## R4 — Text density ceilings

- Max **4 body lines** per slide; max ~**8 words** per line.
- No full sentences as bullets — fragments carrying the keyword. The one exception:
  verbatim quotes (set as quotes, attributed) and the assertion title itself.
- **No paragraph walls, ever.** Prose belongs in lecture notes and handouts. An
  outline item that is irreducibly a paragraph goes back to lesson-builder as a
  content-design flag — it does not get shrunk onto the slide.
- Tables: ≤4 columns × ≤5 rows on a slide; bigger tables become a figure that shows
  the pattern, with the full table in the handout.

## R5 — Signal before detail

Within a slide and across a section: the *why-this-matters / where-this-sits* element
renders before the mechanism (§9 signaling). Section dividers carry the section's
one-line signal, not just its name. A detail slide appearing before its section's
signal slide is a sequencing defect.

## R6 — Build and animation discipline

Progressive disclosure (stepwise reveal) only where it serves processing: worked
examples, derivations, diagrams that accrete — places where showing everything at once
would force the audience to self-sequence. Everything else renders complete.
Transitions, motion effects, and decorative animation: never. A build that exists to
add energy is decoration (§9), and it breaks handout and PDF exports besides.

## R7 — Contrast

Text/background pairs: **≥4.5:1** for body text, **≥3:1** for large text (≥24pt
regular / ≥18.5pt bold) — WCAG AA, checked computationally, not by eye. Text over
images or gradients fails by default unless a solid scrim restores the ratio.
Institutional brand colors failing contrast are demoted to accents and dividers, with
the substitution flagged once.

## R8 — Colorblind-safe palette

Wherever color distinguishes categories, the palette is colorblind-safe. Default
(Okabe–Ito, in order):

| Token | Hex | Name |
|-------|-----|------|
| cat-1 | `#0072B2` | blue |
| cat-2 | `#E69F00` | orange |
| cat-3 | `#009E73` | bluish green |
| cat-4 | `#D55E00` | vermillion |
| cat-5 | `#CC79A7` | reddish purple |
| cat-6 | `#56B4E9` | sky blue |
| cat-7 | `#F0E442` | yellow — never for text or thin lines on white |
| cat-8 | `#000000` | black |

Sequential data: a single-hue ramp (e.g., light→dark blue), not a rainbow. The
red/green pairing as sole differentiator is prohibited everywhere.

## R9 — Meaning never by color alone

Anything color distinguishes is also distinguished by something else: linestyle,
marker shape, direct label, position, or pattern. This is what makes R8 survive a
grayscale handout print.

## R10 — Alt text and reading order

- Every figure carries alt text **in the deck source**: one sentence stating what the
  figure shows ("hit rate plateaus past 64MB for all three policies"), not what it is
  ("a line chart"). Decorative elements (none should exist — R6/§9) would be marked
  decorative.
- Reading order in the source matches visual order: title → signal → evidence →
  notes. Multi-column layouts state their order; exported PDFs/PPTX inherit a sane
  tab/reading order from a sane source, not from post-hoc fixes.
- Speaker notes restate any content that exists only inside a figure — notes are the
  screen-reader-reachable and search-reachable copy.

## R11 — When slides are the wrong medium

Some segments should not be slides, and a minimal slide pointing elsewhere beats a
slide pretending to do the work:

- **Derivations done with students** — board work; slides race ahead of the chalk.
  The slide is the assertion + "→ board" (`[BOARD]` flag from the outline).
- **Live coding / live demos** — switch to the real tool; a screenshot of an IDE is a
  promise the demo breaks.
- **Open discussion** — one slide with the prompt and the time; the room does the rest.
- **Dense reference material** — handout, not slide (R4 tables rule).

Deck-studio honors `[BOARD]` flags from lesson-builder and never reconstitutes them
into full slides. Whether a segment *should* be board work is lesson-builder's call —
flag, don't decide.

## Restyle audit checklist (`restyle` mode)

`restyle` runs every check below against the existing deck and reports like a gate:
finding → check id → slide numbers → suggested fix. Violations never block — they
itemize the rebuild plan the professor confirms.

| Check | Test |
|-------|------|
| R1 | Any text below the legibility floor (per-element table above)? |
| R2 | Slides making more than one point? |
| R3 | Topic titles where assertions belong (structure slides exempt)? |
| R4 | Lines > 4, words/line > ~8, full-sentence bullets, paragraph walls, oversized tables? |
| R5 | Detail before signal, within slides or across the section? |
| R6 | Decorative animation; builds that don't serve processing? |
| R7 | Any text/background pair below 4.5:1 (3:1 large)? |
| R8 | Categorical colors off the safe palette; red/green as sole differentiator; rainbow ramps? |
| R9 | Meaning carried by color alone? |
| R10 | Figures missing alt text; reading order broken in source or export? |
| R11 | Slides doing work that belongs on the board / in a demo / in a handout? |

Report footer states totals by check id and the three highest-impact fixes first —
a 40-finding report with no priorities is noise, not an audit.
