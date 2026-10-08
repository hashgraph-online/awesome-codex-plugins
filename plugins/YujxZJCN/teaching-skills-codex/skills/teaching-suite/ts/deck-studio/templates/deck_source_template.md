<!--
Deck source template — the deck of record (SKILL Iron Rule 1).
Marp-flavored markdown: builds directly with Marp, converts cleanly via pandoc for
PPTX/Beamer routes. Edit THIS file and re-render; never edit the binary alone.
Conventions are explained in comments like this one; delete comments in real decks
or keep them — Marp ignores HTML comments that aren't directives.
Build (printed by renderer after every successful build):
  marp {{deck_filename}}.md --theme decks/theme/course.css --pdf --allow-local-files -o {{deck_filename}}.pdf
Built with: {{tool versions — renderer fills this in}}
-->

---
marp: true
theme: {{course_theme_name}}        <!-- from decks/theme/course.css, per theme spec -->
paginate: true                      <!-- page numbers on by default; title slide opts out -->
---

<!-- _class: title -->
<!-- _paginate: false -->

# {{course_code}} · {{meeting_topic}}

## {{course_title}} — Week {{N}}

{{professor_name}} · {{date}}

<!--
Speaker notes live in the HTML comment directly under a slide's content (Marp) —
deck_architect also emits pandoc's ::: notes blocks when the render route is PPTX.
Notes carry: what to say, timing pointer to the lesson plan segment, and any content
that exists only inside a figure (R10 — notes are the screen-reader-reachable copy).
-->

---

<!-- _class: content -->

# By the end of today you can {{outcome in student-facing words — from the outline, never invented}}

- {{outcome fragment 1}}
- {{outcome fragment 2}}

<!-- Seg S1 (activation). Outcomes slide comes from the outline verbatim in meaning. -->

---

<!-- _class: section -->

# {{Section name}}: {{one-line signal — why this matters / where it sits (R5)}}

<!-- Section divider at each segment boundary. Signal before detail: this line renders
     before any mechanism slides in the section. -->

---

<!-- _class: content -->

# {{Assertion title — a full sentence stating the slide's one claim (R2, R3)}}

- {{evidence fragment, ≤8 words (R4)}}
- {{evidence fragment}}
- {{evidence fragment — max 4 lines; more means split the slide}}

<!--
Speaker notes for this slide: {{what to say — from lecture notes, keyed to segment ID}}
[VERIFY] markers inherited from the outline stay here untouched.
Builds: append `*` list markers / use Marp fragment syntax ONLY where the outline
walks through stages (R6) — worked examples, derivations. Never decoration.
-->

---

<!-- _class: figure-full -->

# {{Assertion the figure proves}}

![{{alt text: one sentence stating what the figure SHOWS, e.g. "hit rate plateaus past 64MB for all three policies" (R10)}}](figures/W{{N}}_fig1.svg)

<!--
generated-by: figures/src/W{{N}}_fig1.py — rebuild with `python3 figures/src/W{{N}}_fig1.py`
Palette: theme categorical tokens (R8); meaning also carried by linestyle/labels (R9).
Professor-supplied figures: keep this comment but mark "professor-supplied — no script".
Data not from the professor: the script and these notes carry
[VERIFY: illustrative numbers — replace with real data or keep labeled as schematic].
-->

---

<!-- _class: board -->

# {{Assertion}} → board

<!-- [BOARD] segment from the outline: the slide stays deliberately minimal (R11).
     Notes carry what to draw/derive, from the lesson plan. -->

---

<!-- _class: content -->

# {{Activity name}}: {{task in one line}}

- **Task:** {{what students do}}
- **Time:** {{minutes}}
- **Deliverable:** {{what they produce}}

<!-- Active segments get exactly ONE slide; the activity sheet carries the rest. -->

---

<!-- _class: section -->

# What we established today

- {{assertion title of key slide 1 — the summary IS the skim of the titles (R3)}}
- {{assertion title of key slide 2}}
- {{forward link: one line to next meeting}}

<!-- Closing slide. Gaps anywhere above are [NEEDS CONTENT: <what>] — never filler
     (Iron Rule 6). Slide count here must match the rendered output (renderer verifies). -->
