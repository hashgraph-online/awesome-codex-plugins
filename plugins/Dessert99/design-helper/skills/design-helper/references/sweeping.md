# Drawing specimens

## Candidate scales

Reference values to sample from, not a count to fill.

| property | ladder |
|---|---|
| radius | 0 · 2 · 4 · 6 · 8 · 12 · 16 |
| shadow blur | 2 · 4 · 8 · 12 · 16 · 24 |
| shadow alpha | .04 · .06 · .08 · .12 · .16 |
| border width | 0.5 · 1 · 1.5 · 2 · 3 |
| spacing | 4 · 8 · 12 · 16 · 20 · 24 · 32 |
| font size | 12 · 13 · 14 · 16 · 18 · 20 |
| line height | 1.2 · 1.35 · 1.5 · 1.6 · 1.75 |
| letter spacing | -0.02 · -0.01 · 0 · 0.01 · 0.02em |
| opacity | .4 · .55 · .7 · .85 · 1 |
| blur (backdrop) | 4 · 8 · 12 · 20 · 32 |

When the project has a scale, **use its steps, not these.** The point of a ladder in a
tokenized project is to find which existing step fits, not to invent a new one.

Pick distinct steps around the current project value, or the middle when there is none.
A matrix puts one direction on rows and the other on columns, both labeled.

## Captions

Use the caption structure in `shared/writing.md#the-caption`; do not duplicate its
rules here. Label the current project value `현재값` when it is one of the rungs, so the
user can compare a change against the baseline. Costs describe the intended apply scope:
reusing a token is not the same as changing its shared definition. Include gain and loss
only for a concrete trade-off, never a fabricated downside for a simple value step.

### Where to look

When the rungs differ in one spot only (the bottom edge of a shadow, a title cut off at
320, the gap between two icons), mark that spot so the eye goes there first.

- **A gray bracket beside the spot, never on it.** It sits in the frame padding, outside
  the pixels being judged. No accent color: it is next to a specimen's surface.
- **The same spot on every rung**, so the eye moves from A to E along one line.
- **The caption names it.** Line 3 starts from the marked part: `표시한 아래 가장자리에서
  번짐이 넓어집니다.`
- Skip it when the whole specimen is what changes (a surface color, a whole-page layout).

Markup → `shared/sheet.md`.

### What is not the real thing

A specimen the user takes for the real component is judged as the real component. Say
on the sheet, next to it, wherever the specimen differs from what the code will do:

- markup rebuilt by hand instead of the project's own component
- state attributes imitated by class (`data-[open]:`, `aria-expanded`)
- a CSS curve standing in for a motion library's spring (`references/motion.md`)
- a font, icon or image that didn't load and was substituted

Each such specimen gets the chip `실물과 다름` on its title line and a labelled line
saying what differs:

```
C   x1.4                             실물과 다름  토큰 그대로
    다른 점  열림 상태를 클래스로 흉내 냈습니다. 실제로는 라이브러리가 붙입니다.
```

When every specimen in a section shares the same difference, say it once in the
section's description instead of on each caption. A specimen drawn from the real
component has no chip.

### Counts the search may have missed

A cost count like `23곳` comes from a search. When part of the code can't be found by
name (class names built at runtime, styles set from JavaScript, another package or a
CMS), the count is a floor. Write it as one: `--shadow-md 고침 (23곳 이상)`. What the
search couldn't reach is reported before applying (`worker.md`, `Blast radius`).

Under a ladder of one continuous value (blur, spacing, radius, duration), where the
perceptual steps break:

```
경계  B와 C는 이 크기에서 구분되지 않습니다. E부터 카드가 떠 보입니다.
```

Leave it out when the options are distinct choices (a position, an order, a layout):
there is no step to break, and the captions already say how each one differs.

### The recommendation

After the boundary line, every section ends with one recommended letter and why:

```
추천 B  320에서 A는 "타임라인"이 칸을 넘칩니다. B는 칸 사이를 4px 내주지만
        모든 폭에서 글자가 칸 안에 들어갑니다. 360 이상에서는 둘이 같습니다.
```

- **Below the specimens, never above them.** The user looks first, then reads it.
  The captions stay neutral.
- **The reason comes from the sheet** — the real content, widths, states and costs
  drawn there, and the trade-offs in the captions. Point at what is visible.
- When only taste separates the options, still name one, and say plainly that the
  reason is taste rather than inventing a functional one.
- It is advice, not a choice. Nothing is applied until the user picks in chat.


Chat is a pointer, not the explanation — two or three lines at most. A paragraph per
specimen in chat means the sheet was written wrong.

## A ladder that doesn't fit isn't a ladder

**Never let a comparison scroll sideways.** Two specimens that can't be on screen
together are compared from memory, which is the one thing this tool exists to avoid.

When it does not fit, drop near-duplicate candidates or isolate a context, keeping the
distinctions the user needs to judge. If the user specified a count, keep it and adapt
the layout or split it into clearly labeled groups.

## Context

A specimen judged in the wrong context is judged wrong. Draw the contexts the ordered
axis reacts to, not every context every time: extra copies the axis doesn't react to
only push rungs out of the first window.

**Backgrounds: at least two,** when the axis reacts to the surface behind it. Shadow,
border, opacity, blur and color all invert with it. White and gray at minimum; dark
too if the project has it.

**Repeat the element** when it appears in multiples in the real UI. One button never
reveals a shadow. Lay six in a list and "too heavy" becomes obvious.

**Two sizes** when the axis reads differently with size. The same radius reads
completely differently on a 32px chip and a 400px card. Radius, padding, border and
type size get small and large.

**Real content, always.** Placeholder boxes hide the problem: a card with lorem ipsum
and a card with a real headline, avatar and timestamp are different design problems.
Real content is not a toggle; there is no version of this where lorem ipsum is the
right specimen.

A position, order or layout axis is judged on the real page around it
(`Structure and layout`, below), not on extra backgrounds and sizes.

Show the contexts that apply together. Never drop one the axis reacts to because the
sheet looks tidier without it; `shared/sheet.md` says how they fit the first window.
Context buttons may isolate one condition when that materially helps; they bring no
sliders with them.

### When context is a constraint, not a variable

> "황혼 배경에 어울리는 카드"

The background is now fixed, so the rule inverts: **hold the constraint and draw
everything on top of it.** Don't fall back to the white/gray default.

But a constraint is rarely one value. "황혼" is a range — pick 2–3 points across it
(해 지기 직전 주황 / 푸른 시간대 / 해 넘어간 뒤 남보라) and draw the ladder on each.

**Use the real background.** A gray stand-in makes the whole comparison worthless.

**A constraint rewrites the axes.** On a dusk background a drop shadow barely
registers — dark on dark. The axis that would have been "shadow" becomes "glow", or
"surface brightness", or "border luminance". Work out which axes the constraint
actually leaves alive before laying anything out.

## A blank slate — the coordinate sweep

> "버튼 만들어야 하는데 아직 아무것도 없어"

Clarify purpose and use when unknown — `shared/clarification.md` — and inspect
available content and project conventions yourself. Then show starting points instead
of asking the user to describe a look.

**Show enough labeled coordinates to reveal useful directions and let them point.**
Use a matrix when the relationship between two directions helps; otherwise a small set
of labeled anchor specimens.

- **Label both edges with what moves and which way** — `무게: 가벼움 → 무거움`,
  `모서리: 각짐 → 둥긂`. A matrix of finished looks with no labelled edges is a preset
  gallery. Labelled edges are what make `더 오른쪽` mean something, and that is the
  entire difference between the two
- **Name the properties a direction bundles, in the caption** — `무게: 테두리 굵기,
  글자 굵기, 세로 여백`. The user has to be able to reject the coordinate system
  itself. `무게 말고 밀도로 봐줘` is the most useful sentence available here and it
  cannot be said unless the axes are written down
- `더 오른쪽` in chat asks for more fixed candidates in that direction

### A cell is an anchor, not a decision

Both directions bundle several properties, so a chosen cell can't say which of them made
it good. Nothing in it is settled.

    출발점: 버튼 = E · 무게 중간 · 모서리 중간   (묶인 속성 전부 미해결)

`출발점:`, never `확정:`. The line is deliberately different — `확정:` is for a value
that was isolated on one axis and seen against its neighbours, and a matrix by
construction never does that.

**Then the blank slate is over.** The next order is an ordinary single-axis ladder drawn
on top of the anchor. The matrix is an opener, not a mode: once per target, and it does
not come back.

### A look exists, but the user wants a different direction

Anchor the exploration in what the code does today — the current value belongs in the
middle, not thrown away. `shared/stylesystems.md` calls this hunting a direction.

## Stateful parts — two rows

hover fires one at a time, so two specimens can never be hovered together.

- `실물` — touched directly with the mouse. Judges speed and feel
- `강제 상태` — default · hover · focus · active · disabled pinned by class, laid
  side by side. Contrasts color and lightness by eye

Both rows, always, for anything with states.

**What can't be judged here.** This is a shell that matches in shape only.
State-attribute styling like `data-[open]:` is imitated by hand — the real library
sets those attributes. Focus traps, keyboard nav and screen readers need the real
implementation. Shape and transition are decidable; **correctness of behavior is not.**
Mark these specimens on the sheet: `What is not the real thing`, above.
Mount/unmount timing is a motion question — `references/motion.md`.

## Structure and layout

When the question is structure (where a menu item goes, where filters sit, a column
split, sidebar width, content order), the axis is position. The look is not stripped:
it is the part held fixed, identical on every rung.

**Draw it in the real design.** The user judges a layout as it will ship. A filter row
that looks fine as gray outlines can crowd the real header, and a menu item that reads
well in a plain list can disappear among the real icons and group labels.

- **The project's own design** when one exists: its utilities, variables, fonts, icons
  and component markup, per `shared/stylesystems.md`. Copy the real screen's markup
  and classes; don't redraw it in generic black and white.
- **The design the user asked for** when the new part has requirements (a Figma frame,
  a reference screen, a description). Draw those, on top of the existing design around it.
- **Neither exists** (a blank slate with no stated look): write plain values directly
  and say so on the sheet (`임의값 탐색안`). Still real type, spacing and copy, not
  gray blocks.

Around the part that moves:

- Draw the real page around it: navigation, header, neighbouring sections, real copy,
  and a real page's worth of items. Three blocks won't show a layout failing.
- Draw the real breakpoints if width is the question, not one arbitrary viewport.
- Mark what moved with a `.dh-look` bracket beside it (`Where to look`). Never a gray fill
  or dashed box on it: that restyles the very thing being judged.
- Markup rebuilt by hand instead of the real component gets `실물과 다름`, as anywhere.

### A skeleton only on request

Draw gray blocks only when the user explicitly asks to see positions alone:
`뼈대만 보자` · `와이어프레임으로` · `위치만 보자` · `디자인 빼고`. A layout question is
not that request, and neither is an early stage, a rough request, or a large page.

- Achromatic only: no color, no type styling, no shadow, no radius. Gray blocks on white.
- Block weight carries hierarchy: darker gray = heavier element.
- Label blocks with their role (`네비`, `사이드바`, `본문`, `카드`), not lorem ipsum.
- The real breakpoints and a real page's worth of blocks, as above.

The request holds for that order only. The next order is drawn in the real design again
unless the user asks for a skeleton again.
