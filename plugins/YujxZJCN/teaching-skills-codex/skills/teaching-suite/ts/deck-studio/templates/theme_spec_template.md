# Theme Spec — {{course_code}} {{course_title}}

**Version:** {{theme_version}} · **Confirmed:** {{date_or_pending}}
**Render route(s):** {{marp | pandoc-reference-doc | python-pptx | beamer-tectonic}}

This document is the contract: deck_architect and figure_maker style by token name
from this spec only; the CSS / template implementation below is derived from it. A
change here is a change-history entry and a re-render, not an inline override.

## Identity & constraints

- **Course:** {{course_code}} — {{course_title}}, {{term}}
- **Institutional constraints:** {{brand colors with source, mandated .potx path, logo
  placement rules — or "none provided; accessible defaults in use"}}
- **Room reality:** {{projector/LED/online + hall size — drives the legibility floor}}
- **Language/script notes:** {{e.g., CJK font stack needed for bilingual decks}}

## Typography scale

| Role | Size (projected) | Weight | Font | Floor check (R1) |
|------|------------------|--------|------|------------------|
| Title | {{40pt}} | {{bold}} | {{font + fallback stack}} | ≥36pt ✓/✗ |
| Section divider | {{36pt}} | {{bold}} | {{ }} | ≥36pt ✓/✗ |
| Body | {{28pt}} | {{regular}} | {{ }} | ≥24pt ✓/✗ |
| Code | {{24pt}} | {{regular}} | {{mono font}} | ≥20pt ✓/✗ |
| Caption/credit | {{18pt}} | {{regular}} | {{ }} | ≥16pt ✓/✗ |

## Color tokens

Every pair lists its computed contrast ratio; pairs below 4.5:1 body / 3:1 large do
not enter this table (R7).

| Token | Hex | Used on | Contrast vs background | Pass |
|-------|-----|---------|------------------------|------|
| background | {{#FFFFFF}} | — | — | — |
| text-body | {{#1A1A1A}} | background | {{16.7:1}} | ✓ |
| text-title | {{#hex}} | background | {{ratio}} | ✓/✗ |
| accent | {{#hex}} | dividers, emphasis — never body text if below 4.5:1 | {{ratio}} | ✓/✗ |
| muted | {{#hex}} | captions, de-emphasis | {{ratio}} | ✓/✗ |

**Contrast substitutions made:** {{e.g., "institutional gold fails 4.5:1 on white —
demoted to divider accent; body emphasis uses institutional blue instead" — or "none"}}

## Palette (figures)

**Categorical** (colorblind-safe, in assignment order — default Okabe–Ito per
`ts/deck-studio/references/slide_design_rules.md` R8):

{{cat-1 #0072B2, cat-2 #E69F00, cat-3 #009E73, cat-4 #D55E00, cat-5 #CC79A7,
cat-6 #56B4E9, cat-7 #F0E442 (never text/thin lines on white), cat-8 #000000}}

**Sequential:** {{single-hue ramp endpoints, e.g., #DEEBF7 → #08306B}}
**Diverging (if needed):** {{e.g., #0072B2 ↔ #D55E00 through neutral}}

## Layout masters

| Master | Used for | Usage rule |
|--------|----------|------------|
| `title` | Slide 1 only | Course, meeting, date; no content |
| `section` | Segment boundaries | Section name + one-line signal (R5); nothing else |
| `content` | Assertion-evidence slides | Title zone = claim; evidence zone = figure/steps/≤4 lines (R3, R4) |
| `figure-full` | Figure carries the slide | Assertion title + full-bleed figure + credit line |
| `comparison` | Exactly two things side-by-side | Two panels max; three-way comparisons become a figure |
| `board` | `[BOARD]` segments | Assertion + "→ board"; deliberately minimal (R11) |
| {{additional master}} | {{ }} | {{ }} |

## Implementation — {{chosen route}}

### Marp CSS (if Marp route)

```css
/* decks/theme/course.css — generated from this spec; regenerate on spec change */
/* @theme {{course_code_lower}} */
@import "default";
section { font-size: {{body_pt}}pt; color: {{text-body}}; background: {{background}};
          font-family: {{font_stack}}; }
h1 { font-size: {{title_pt}}pt; color: {{text-title}}; }
section.section { /* divider master */ {{divider rules}} }
section.figure-full { {{figure-full rules}} }
section.comparison { {{two-column rules}} }
section.board { {{minimal board-slide rules}} }
```

### PPTX template notes (if python-pptx / reference-doc route)

- **Template file:** {{path to institutional .potx/.pptx}}
- **Master → layout mapping:** {{spec master → template layout name → placeholder
  names, one line each}}
- **Token deviations in the template:** {{spec values the template violates, e.g.,
  body 20pt < floor — professor decision: {{logged decision}}}}
- **What the build script controls vs inherits:** {{ }}

## Accessibility checklist (confirmed at theme checkpoint)

- [ ] All body/title pairs ≥4.5:1 / ≥3:1 (R7) — ratios in the token table
- [ ] Typography floors met on every master (R1)
- [ ] Categorical palette colorblind-safe; no red/green sole pairing (R8)
- [ ] No text-over-image surfaces without scrim; no decorative theme elements (R6)
- [ ] Fallback font stack stated; renders without the primary font installed

## Change history

| Date | Version | Change | Reason / professor decision |
|------|---------|--------|------------------------------|
| {{date}} | {{1.0}} | Initial theme | {{ }} |
