# The sheet page

How a comparison sheet is laid out around its specimens. Captions, the boundary line
and the recommendation → `references/sweeping.md`.

## The section guide

Every section opens, under its title, with a short guide telling the user what this
section asks of them. Three fixed labels, each one or two full sentences — enough that
someone who skipped the chat can still judge the section without guessing:

```
정할 것 — 공지 뒤에 깔리는 선택 표시의 가로 폭을 정합니다. K 는 칸 폭을 그대로
          따라가서 화면이 넓어질수록 길어지고, L 은 어느 화면에서든 46 으로 고정됩니다.
볼 곳   — 390 과 480 열에서 공지 뒤 면의 가로 길이를 비교해 보세요. 480 에서 K 는
          L 보다 약 1.6 배 넓습니다. 320 에서는 칸이 47 이라 둘이 거의 같아 보입니다.
답하기  — 채팅에 글자로 알려주세요. 하나로 정하셨다면 "L 로 갈게", 방향은 좋은데
          조금 다르게 보고 싶다면 "K 에서 더 좁게" 처럼 말씀하시면 됩니다.
```

1. `정할 것` — the one decision this section exists for, in plain words: what is being
   decided and how the lettered options differ in behavior, not only in value. Only
   the ordered axis — never a next axis
2. `볼 곳` — where on the specimens the difference shows, at which size or background
   it shows most, and roughly how big it is. Say where it doesn't show, too, so the
   user doesn't stare at identical columns
3. `답하기` — how to answer in chat, with one choice and one refine example using this
   section's real letters

Plain sentences, not fragments — the user reads this cold. Keep each label to two
sentences; anything longer belongs in the specimen captions.

This is a reading guide, not a recommendation — it never leans toward an option. It
sits above the specimens; the boundary line and the recommendation stay below them.


## Turn dividers

A sheet grows over several chat turns. Everything appended in response to one user
message sits under one divider, so the user can tell which turn produced what:

```
요청 2 · 화살표 비교와 도크 전체  ------------------------------
  화살표 크기 — 16 vs 20 vs 24
  도크 전체 — 높이·모서리
```

- `요청 N ·` and a few words of what was asked, the same words as the table-of-contents
  turn label. Label on the left, heavier rule, the widest gap on the page.
- Every turn that appends gets one, including a refine that continues an earlier
  section's letters. An in-place revision of an existing section adds none.
- **Section titles start with the element's name**, as the user calls it —
  `화살표 크기 — ...`, `도크 전체 — ...`. That is what separates two elements inside one turn;
  there is no separate element divider.
- `<div class="turn">`, never a `<section>` — the reloader counts sections.


## The table of contents

A fixed sidebar on the left lists every turn and, under it, the titles of the sections
that turn added. It gives a long sheet a way back to any earlier comparison.

```
목차
요청 1 · 시트가 화면 폭을 쓰는 방식
  시트 폭 — 시안 칸을 화면에 어떻게 채울지
요청 2 · 요청별 목차 사이드바
  사이드바 폭 — 고정 폭을 얼마로 둘지
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
<body class="has-toc">
  <nav class="toc">
    <div class="toc-h">목차</div>
    <div class="toc-turn">요청 1 · 시트가 화면 폭을 쓰는 방식</div>
    <a href="#r1-1">시트 폭 — 시안 칸을 화면에 어떻게 채울지</a>
  </nav>
  <main> <div class="turn">...</div> <section id="r1-1">...</section> </main>
</body>
```

```css
.has-toc { display:flex; align-items:flex-start }
.has-toc > main { flex:1; min-width:0 }
.toc { flex:none; width:220px; position:sticky; top:0; height:100vh; overflow-y:auto;
       padding:28px 16px; background:var(--surface); border-right:1px solid var(--line);
       font-size:12px }
.toc-h { font-size:11px; font-weight:700; color:var(--muted); letter-spacing:.04em; margin:0 0 14px }
.toc-turn { font-weight:700; font-size:12.5px; margin:16px 0 4px }
.toc a { display:block; color:var(--sub); text-decoration:none; padding:4px 8px;
         margin-left:-8px; border-radius:6px }
.toc a.cur { background:var(--accent-tint); color:var(--accent); font-weight:600 }
```

```html
<script>
(() => {
  const links = [...document.querySelectorAll('.toc a')];
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (!e.isIntersecting) return;
    links.forEach(a => a.classList.toggle('cur', a.hash === '#' + e.target.id));
  }), { rootMargin: '0px 0px -70% 0px' });
  document.querySelectorAll('section[id]').forEach(s => io.observe(s));
})();
</script>
```

The `var(--...)` tokens come from the sheet style below.


## Filling the width

Lay a section's specimens on a grid that shares the page width among its cells, so no
empty band is left on the right however wide the window is:

```css
.grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(380px, 1fr)); gap:36px 28px }
.frame { display:flex; justify-content:center }   /* specimen stays at true size */
```

Only the frame stretches. The specimen inside keeps its real pixel size, centered —
never scale or `zoom` it to fill the cell, because size is part of what is judged.
Set the minimum from the specimen's real width plus the frame padding (a 320 screen →
380). A matrix, whose columns carry meaning, keeps its fixed column count instead.


## Sheet style

The sheet's own chrome — page, sidebar, guide, frames, captions — is one fixed look:
white cells floating on a light gray page, and one blue for the reading path. It
belongs to the sheet, not to the specimens.

- **Cells float.** Specimen frames and the guide box are white with a faint two-layer
  shadow and radius 14, so a specimen reads first without a line around every cell.
- **One accent, on the reading path only.** Blue marks the letter badge, the guide
  labels, the recommendation label and the current table-of-contents item. It never goes
  inside a frame or next to a specimen's surface, where it would bias a color judgment.
- **Neutral behind specimens.** The frame stays white. When the ordered axis is itself
  surface or background, the context rules in `references/sweeping.md#context` override the frame.

```css
:root {
  --page:#f1f1f3; --surface:#ffffff; --line:#e7e7ea; --ink:#1f1f23; --sub:#63636b;
  --muted:#8b8b93; --accent:#3b5bdb; --accent-tint:rgba(59,91,219,.10); --radius:14px;
  --float:0 1px 2px rgba(0,0,0,.05), 0 6px 20px rgba(0,0,0,.06);
}
*, *::before, *::after { box-sizing:border-box }
body { margin:0; background:var(--page); color:var(--ink);
       font:13px/1.6 -apple-system, "Pretendard", "Apple SD Gothic Neo", sans-serif }
main { padding:8px 44px 64px }

.turn { display:flex; align-items:center; gap:16px; margin:72px 0 0;
        font-size:14px; font-weight:700; color:var(--ink) }
.turn::after { content:""; flex:1; height:2px; background:#d4d4d9; border-radius:1px }
main > .turn:first-child { margin-top:32px }

section h2 { font-size:20px; letter-spacing:-.01em; margin:22px 0 6px }
.desc { color:var(--sub); margin:0 0 16px; max-width:820px }
.guide { display:grid; grid-template-columns:auto 1fr; gap:6px 14px; max-width:820px;
         margin:0 0 26px; padding:14px 18px; background:var(--surface);
         border:1px solid rgba(0,0,0,.04); border-radius:var(--radius); box-shadow:var(--float) }
.guide b { color:var(--accent); white-space:nowrap }

.frame { background:var(--surface); border:1px solid rgba(0,0,0,.04);
         border-radius:var(--radius); box-shadow:var(--float); padding:18px 14px; overflow:hidden }
.cap { margin-top:12px }
.cap .n { display:flex; align-items:center; gap:8px; font-weight:700 }
.badge { display:inline-grid; place-items:center; min-width:22px; height:22px; padding:0 6px;
         border-radius:6px; background:var(--accent); color:#fff; font-size:12px; font-weight:700 }
.cost { margin-left:auto; font-size:11.5px; font-weight:500; padding:1px 8px;
        border-radius:99px; background:var(--page); color:#52525b }
.cap p { margin:2px 0 0 } .cap .resolved { color:var(--muted) }
.bound { color:var(--sub); margin:18px 0 0 }
.gain { color:var(--sub) } .gain b { color:var(--ink); font-weight:600 }
.pick { display:flex; gap:12px; max-width:820px; margin:14px 0 0; padding:12px 16px;
        background:var(--surface); border:1px solid rgba(0,0,0,.04);
        border-radius:var(--radius); box-shadow:var(--float) }
.pick > b { color:var(--accent); white-space:nowrap }
```

```html
<div class="spec">
  <div class="frame">...specimen...</div>
  <div class="cap">
    <div class="n"><span class="badge">A</span>두께 얇음 · 모서리 각짐<span class="cost">새 변수</span></div>
    <p class="resolved">높이 52 · 안쪽 여백 0 · 모서리 14</p>
    <p>면이 적어 콘텐츠가 더 보입니다.</p>
    <p class="gain"><b>얻는 것</b> — ... / <b>잃는 것</b> — ...</p>  <!-- only with a real trade-off -->
  </div>
</div>
...
<p class="bound">경계 — ...</p>
<div class="pick"><b>추천 — B</b><span>이유 ...</span></div>
```
