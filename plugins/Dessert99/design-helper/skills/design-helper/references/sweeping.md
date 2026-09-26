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

## Captions — the sheet explains itself

The user reads the screen, not the chat. Everything needed to judge a specimen sits
next to it.

Up to four lines per specimen:

```
A   x1.8                                        토큰 그대로
    윗변 100% · 그림자 100%
    가장 세게 번집니다. B 와 그림자가 같아 한 쌍으로 붙습니다.
```

1. letter · the value being moved · its cost
2. what that value resolves to, when the value alone doesn't show it
3. one line on what it does to the eye
4. **only if there is a real trade-off** — what this option gains and what it gives up,
   against the others on the sheet:

```
B   안쪽을 줄이고 간격도 조금 줄임                     layout.css 변수 + phone-md 1곳
    360 미만: 아이콘 18 · 글자 11 · 칸 사이 8 · 양끝 12
    칸이 38 로 넓어져 "타임라인"이 칸 안에 딱 맞습니다.
    얻는 것 — 320 에서도 글자가 잘리지 않습니다. / 잃는 것 — 320 에서만 칸 사이가 피그마보다 4 좁습니다.
```

Leave line 4 out when nothing is given up — a pure step on a ladder usually has none.
Name concrete costs (a width that breaks, a token that moves, a state that stops
reading), never vague ones like `덜 깔끔함`.

Under the ladder, where the perceptual steps break:

```
경계 — B·C 는 이 크기에서 구분이 안 됩니다. E 부터 떠 보이기 시작합니다.
```

### The recommendation

After the boundary line, every section ends with one recommended letter and why:

```
추천 — B. 320 에서 A 는 "타임라인"이 칸을 넘치고, B 는 칸 사이 4 를 내주는 대신
       모든 폭에서 글자가 칸 안에 들어갑니다. 360 이상은 둘이 같아 차이가 320 에만 있습니다.
```

- **Below the specimens, never above them.** The user looks first, then reads it.
  The guide and captions stay neutral.
- **The reason comes from the sheet** — the real content, widths, states and costs
  drawn there, and the trade-offs in the captions. Point at what is visible.
- When only taste separates the options, still name one, and say plainly that the
  reason is taste rather than inventing a functional one.
- It is advice, not a choice. Nothing is applied until the user picks in chat.


On an interactive sheet, lines 2 and 3 are functions of the value, never per letter —
`references/controls.md`.

Chat is a pointer, not the explanation — two or three lines at most. A paragraph per
specimen in chat means the sheet was written wrong.

## Context

A specimen judged in the wrong context is judged wrong.

**Backgrounds — at least two.** Shadow, border, opacity and blur all invert with the
surface behind them. White and gray at minimum; dark too if the project has it.

**Repeat the element.** One button never reveals a shadow. Lay six in a list and
"too heavy" becomes obvious. Anything that appears in multiples in the real UI gets
drawn in multiples here.

**Two sizes.** The same radius reads completely differently on a 32px chip and a
400px card. Small and large, always.

**Real content.** Placeholder boxes hide the problem — a card with lorem ipsum and a
card with a real headline, avatar and timestamp are different design problems.

Show background, repetition and size contexts together. Context buttons may isolate one
condition when that materially helps; they bring no sliders with them. Never open a
sheet already narrowed because it looks tidier. Real content is not a toggle: there is no version of
this where lorem ipsum is the right specimen.

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

Clarify purpose and use when unknown — `references/clarification.md` — and inspect
available content and project conventions yourself. Then show starting points instead
of asking the user to describe a look.

**Show enough labeled coordinates to reveal useful directions and let them point.**
Use a matrix when the relationship between two directions helps; otherwise a small set
of labeled anchor specimens.

- **Label both edges with what moves and which way** — `무게 — 가벼움 → 무거움`,
  `모서리 — 각짐 → 둥글`. A matrix of finished looks with no labelled edges is a preset
  gallery. Labelled edges are what make `더 오른쪽` mean something, and that is the
  entire difference between the two
- **Name the properties a direction bundles, in the caption** — `무게 = 테두리 굵기 +
  글자 굵기 + 세로 여백`. The user has to be able to reject the coordinate system
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
middle, not thrown away. `references/stylesystems.md` calls this hunting a direction.

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
Mount/unmount timing is a motion question — `references/motion.md`.

## Wireframes

When the question is structure — layout, column split, sidebar width, content order —
strip everything else.

**Achromatic only. No color, no type styling, no shadow, no radius.** Gray blocks on
white. If a skin is on it, the skin gets judged instead of the structure.

- Block weight carries hierarchy: darker gray = heavier element
- Label blocks with their role (`네비`, `사이드바`, `본문`, `카드`) — not lorem ipsum
- Draw the real breakpoints if width is the question, not one arbitrary viewport
- Keep a real page's worth of content. Three blocks won't show a layout failing

Structure is settled first, skin afterwards — a separate order.
