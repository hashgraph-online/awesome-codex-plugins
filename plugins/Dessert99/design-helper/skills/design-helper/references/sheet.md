# The sheet page

How a comparison sheet is laid out around its specimens. Captions, the boundary line
and the recommendation → `references/sweeping.md`.

## Start from the kit

`$WS/sheet.html` is copied from `assets/sheet.html` (`references/liveview.md`). It
already holds the sheet style, the table of contents with its highlighter, the grid and
the reloader. Never rewrite the file and never retype those parts. Read it once, then
insert only what the turn adds, just above its marker:

| marker | what goes above it |
|---|---|
| `<!-- dh:head -->` | `<link>` to project stylesheets (`tokens.css`, `$WS/sheet.css`) |
| `/* dh:style */` | specimen CSS, inside the second `<style>` |
| `<!-- dh:toc -->` | this turn's `toc-turn` label and section links |
| `<!-- dh:main -->` | this turn's divider and sections |
| `<!-- dh:script -->` | control scripts, when a section has them |

Leave the markers in place: the next turn appends above them again. An in-place
revision edits the section where it is.

## Turn dividers

A sheet grows over several chat turns. Everything appended in response to one user
message sits under one divider, so the user can tell which turn produced what:

```
요청 2 · 화살표 비교와 도크 전체  ------------------------------
  화살표 크기: 16, 20, 24
  도크 전체: 높이와 모서리
```

- `요청 N ·` and a few words of what was asked, the same words as the table-of-contents
  turn label. Label on the left, heavier rule, the widest gap on the page.
- Every turn that appends gets one, including a refine that continues an earlier
  section's letters. An in-place revision of an existing section adds none.
- **Section titles start with the element's name**, as the user calls it —
  `화살표 크기: ...`, `도크 전체: ...`. That is what separates two elements inside one turn;
  there is no separate element divider.
- `<div class="turn">`, never a `<section>` — the reloader counts sections.


## The table of contents

A fixed sidebar on the left lists every turn and, under it, the titles of the sections
that turn added. It gives a long sheet a way back to any earlier comparison.

```
목차
요청 1 · 시트가 화면 폭을 쓰는 방식
  시트 폭: 시안 칸을 화면에 어떻게 채울지
요청 2 · 요청별 목차 사이드바
  사이드바 폭: 고정 폭을 얼마로 둘지
```

- **Contents only.** Turn labels (the same words as the turn divider) and section
  titles, each linking to its section. No chosen values, no status, no next steps.
- **220 wide, always open.** No collapse toggle and no breakpoint that hides it — the
  page body keeps one stable width, so the specimen grid never reflows under the user.
  The body takes the rest.
- **Sticky, scrolls on its own.** It stays in view while the page scrolls; a long list
  scrolls inside the sidebar.
- **The section in view is highlighted.** Only the reading position — never a choice.
- Every `<section>` gets a stable id, `r<turn>-<n>` (`r2-1`), for the links. The sidebar
  is a `<nav>`, never a `<section>` — the reloader counts sections.

```html
<!-- above dh:toc -->
<div class="toc-turn">요청 1 · 시트가 화면 폭을 쓰는 방식</div>
<a href="#r1-1">시트 폭</a>

<!-- above dh:main -->
<div class="turn">요청 1 · 시트가 화면 폭을 쓰는 방식</div>
<section id="r1-1">...</section>
```

The sidebar's style and its highlighter are in the kit.


## Filling the width

Lay a section's specimens on a grid that shares the page width among its cells, so no
empty band is left on the right however wide the window is:

The kit's `.grid` does this with `minmax(380px, 1fr)`; `.frame` centers the specimen.

Only the frame stretches. The specimen inside keeps its real pixel size, centered —
never scale or `zoom` it to fill the cell, because size is part of what is judged.
Set the minimum from the specimen's real width plus the frame padding (a 320 screen →
380), on the section's own grid when it differs:
`style="grid-template-columns:repeat(auto-fill, minmax(460px, 1fr))"`. A matrix, whose columns carry meaning, keeps its fixed column count instead.


## Sheet style

The sheet's own chrome (page, sidebar, frames, captions) is one fixed look:
white cells floating on a light gray page, and one blue for the reading path. It
belongs to the sheet, not to the specimens.

- **Cells float.** Specimen frames are white with a faint two-layer
  shadow and radius 14, so a specimen reads first without a line around every cell.
- **One accent, on the reading path only.** Blue marks the letter badge, the
  recommendation label and the current table-of-contents item. It never goes
  inside a frame or next to a specimen's surface, where it would bias a color judgment.
- **Neutral behind specimens.** The frame stays white. When the ordered axis is itself
  surface or background, the context rules in `references/sweeping.md#context` override the frame.

The CSS for all of this is the kit's first `<style>`. Specimens use the markup below.
The words inside follow `references/writing.md`.

```html
<section id="r1-1">
<h2>카드 그림자 블러</h2>
<div class="grid">
<div class="spec">
  <div class="frame">
    <div class="at">  <!-- only with a marker -->
      ...specimen...
      <i class="look x" style="left:12px; width:120px"></i>
    </div>
  </div>
  <div class="cap">
    <div class="n"><span class="badge">A</span>두께 얇음 · 모서리 각짐<span class="real">실물과 다름</span><span class="cost">새 변수</span></div>
    <p class="resolved">높이 52 · 안쪽 여백 0 · 모서리 14</p>
    <p>면이 적어 콘텐츠가 더 보입니다.</p>
    <dl class="gain">  <!-- only with a real trade-off, or a 다른 점 line -->
      <dt>얻는 것</dt><dd>...</dd>
      <dt>잃는 것</dt><dd>...</dd>
      <dt>다른 점</dt><dd>...</dd>
    </dl>
  </div>
</div>
...
</div>
<p class="bound"><b>경계</b><span>...</span></p>
<div class="pick"><b>추천 B</b><span>이유 ...</span></div>
</section>
```

- `.at` wraps the specimen only when it carries a marker. `.look.x` is a bracket under
  the spot (set `left` and `width`), `.look.y` one beside it (set `top` and `height`),
  both measured from the specimen's own corner. When the axis spreads past the
  specimen (shadow, glow, outline), move the bracket past the widest rung's spread,
  `style="bottom:-30px"`, and give the section's frames that much padding. Rules →
  `references/sweeping.md`.
- `.real` is the `실물과 다름` chip; its `다른 점` line joins the `gain` list.


## The first screen is the specimens

When a section appears, the reloader scrolls its top to the top of the user's window.
What fills that window is what gets judged, so it is the specimens.

- **Above the grid: the title and at most two lines of description.** What to decide,
  where to look, a shared `실물과 다름` note. Anything longer moves into the captions or
  under the ladder.
- **Every frame of the section fits in that first window** when the specimens are
  small enough to allow it. Drop context repetitions or near-duplicate rungs before
  letting a rung fall below it. A specimen taller than the window (a whole page) shows
  at least one full row of frames.
- **The recommendation stays below the specimens.** Read before looking, it decides
  for the eye.

`check.cjs` reports `firstScreen` per section: how many frames end inside one window
from the section's top. Below `specs` means a rung starts out of sight.
