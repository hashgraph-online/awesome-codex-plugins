# Controls

## Optional controls — not the default sheet

A fixed ladder or matrix needs none of this; render its specimens directly. Add a
slider only when the user asks to adjust directly, or when a continuous transition
can't be judged from fixed steps, and say that purpose on the sheet. Numeric values,
a matrix, or discrete layouts (one/two/three columns) are not reasons.

Include only the controls the task needs. Label each with the property and a live
value with units (`블러 12px`), never a generic `창` or `간격`.

Before presenting any added slider, exercise its minimum, middle, and maximum and
check actual component styles/layout, caption values, valid bounds/steps, and reload
restoration. In a snapped ladder keep `(n - 1) * spread <= scale.length - 1` so endpoints
do not collapse into repeated candidates. The reference engine is a starting point,
not a verified implementation for every scale. If interaction cannot be verified,
omit the slider and provide fixed candidates; do not ship a nonfunctional control.

Selection and refinement requests still happen in chat, using the specimen letters.

**What controls may move — the whole guardrail:**

- the **window** of the axis that was ordered (centre, spacing, snap)
- the **context** it is judged in (background, repetition, size, content)

**Nothing else.** A colour picker on a spacing ladder turns this into a toy and the
measurement dies with it. The one exception is the blank-slate matrix — two axes by
construction, `references/sweeping.md`.

## Config — what I write per section

The counts below are examples. One object, `L`, keyed by section id, in a `<script>` **before** the engine. Section
ids stay short and selector-safe: `u1`, `u2`, `m1`.

```js
const L = {
  u3: {
    kind: 'ladder',
    axes: [{ scale: [2,4,8,12,16,24], n: 5, center: 3, spread: 1, step: 1, unit: 'px' }],
    inSystem: [4,8,12,16],
    token: `--shadow-blur-md`, uses: 23,
    resolve: v => `검정 12% · 번짐 ${v}px`,
    eye: v => v >= 20 ? '여기서부터 떠 보입니다' : '',
    draw: (el, v) => el.style.setProperty('--blur', v + 'px'),
  },
};
```

- `scale` — the ladder's candidate values, **in order**. The project's own scale when
  detection found one, otherwise the default ladder in `references/sweeping.md`.
  Entries may be numbers or class names; see the utility fork below
- `inSystem` — which of them exist as a token or utility today. `'all'` when every
  entry does. This is what the cost chip reads
- `token` · `uses` — the token this axis hangs off and its grep count. **`token: null`
  on a blank slate** and the chip disappears, which is correct — there is no cost to
  show when nothing is being changed
- `resolve` · `eye` — **functions of the value, never per letter**
  (`references/sweeping.md`)
- `draw` — applies the value to a clone. Set a CSS variable the specimen's own CSS
  reads. Never write a full style string here

### The utility fork

With Tailwind the specimen carries a class, not a value. `scale` becomes class names and
`draw` swaps them. Everything else is unchanged — the engine indexes the array, so it
never does arithmetic on the entries.

**Mark the component node `target` in the template.** `draw` receives the wrapper, and
the wrapper holds every context block — the backgrounds, the sizes, the repetition. A
variable set on it reaches the component by inheritance; **a class does not.** It has to
be put on each component node by hand, and there is more than one of them.

```js
axes: [{ scale: ['rounded-none','rounded-sm','rounded','rounded-md','rounded-lg'],
         n: 5, center: 2, spread: 1 }],
inSystem: 'all',
draw: (el, c) => el.querySelectorAll('.target').forEach(t => {
  t.className = t.className.replace(/\brounded\S*/g, '').replace(/\s+/g, ' ').trim() + ' ' + c;
}),
```

Getting this wrong **fails silently and looks fine**: the class lands on the wrapper, the
component keeps whatever it was born with, and every rung renders identically. Nothing
throws. Verification step 2 in `SKILL.md` is what catches it — read the computed style
off the component and confirm the rungs actually differ.

Free mode is numeric only, so the `스케일에 맞춤` checkbox hides itself here.

## Snap — off-scale is reachable, never free and never silent

`스케일에 맞춤` is **on by default.** Snapped, the window walks the scale's own steps and
every rung is a value the project already has: `토큰 그대로`.

Off, rungs are continuous — `step` apart — and any rung that isn't on the scale flips
its chip:

    토큰 그대로            →    --shadow-blur-md 고침 (23곳) · 또는 새 토큰

and draws a dashed outline.

## Optional markup

The following is a structural example for an interactive sheet, not a default template.
Choose only the needed controls and replace generic labels with the property and live value.

```html
<div class="ctx">
  <button data-ctx="bg" data-val="pair">흰·회</button>
  <button data-ctx="bg" data-val="dark">다크</button>
  <button data-ctx="rep" data-val="many">6개</button>
  <button data-ctx="rep" data-val="one">1개</button>
  <button data-ctx="size" data-val="both">두 크기</button>
  <button data-ctx="size" data-val="sm">작은 것만</button>
  <button data-ctx="size" data-val="lg">큰 것만</button>
</div>

<section id="u3" data-kind="ladder" data-axis="그림자 블러">
  <h2>그림자 블러 — ...</h2>
  <div class="scrub">
    <label>창 <input type="range" data-scrub="center:0"></label>
    <label>간격 <input type="range" data-scrub="spread:0" min="1" max="3"></label>
    <label><input type="checkbox" data-scrub="snap"> 스케일에 맞춤</label>
  </div>
  <template>
    <div class="on-white rep">...the real component, marked `target`, repeated...</div>
    <div class="on-gray rep">...</div>
    <div class="on-dark rep">...only when the project has a dark surface...</div>
  </template>
  <div class="ladder"></div>
  <p class="edge">경계 — B·C 는 이 크기에서 구분이 안 됩니다.</p>
</section>
```

The `<template>` holds the specimen **once** — every context (both backgrounds, both
sizes, the repetition) lives inside it and CSS shows or hides them. The engine stamps it
per rung. `data-scrub="center:0"` is `<what>:<axis index>`; a ladder has one axis, the
matrix has two.

One `<section>` per ladder, appended at the end — `references/liveview.md` counts them.
The section guide, captions and recommendation follow `references/sheet.md` and
`references/sweeping.md` as on a fixed sheet.

## A ladder that doesn't fit isn't a ladder

**Never let a comparison scroll sideways** — two specimens that can't be on screen
together are compared from memory, which is the one thing this tool exists to avoid.

When it does not fit, reconsider both the useful candidate count and context layout.
Remove redundant candidates or isolate context while preserving the distinctions the
user needs to judge. If the user specified a count, preserve it and adapt the layout
or split into clearly labeled groups. Do not force a fixed count into horizontal overflow.

## The boundary goes stale, the captions don't

The engine dims a boundary whose window moved and appends `— 창을 옮겼습니다. 경계는
다시 봐야 합니다`. It comes back on its own if the window returns.

**That dimming is an order to me, not to the user:** next turn, look again and rewrite
the line. Never leave a dimmed boundary standing while reporting as if it held.

## Choosing in chat

When the user scrubs, letters refer to the current window. Read the actual user tab
and its `.spec` data attributes before resolving a letter; do not infer its value
from a fresh tab or the initial config. If unavailable, ask for the displayed value.

## The engine

Only for a justified interactive sheet: adapt this example to the selected controls,
place it after the `L` block and before the reloader, and verify it as described above.
For a fixed sheet, omit it entirely.

```html
<script>
(() => {
  const S = sessionStorage, $ = (s, r = document) => [...r.querySelectorAll(s)];
  const load = (k, d) => { try { return JSON.parse(S.getItem(k)) ?? d } catch { return d } };
  const save = (k, v) => { try { S.setItem(k, JSON.stringify(v)) } catch {} };
  const LET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', state = {};
  const ctx = load('ctx', { bg: 'pair', rep: 'many', size: 'both' });

  const syncCtx = () => {
    Object.assign(document.documentElement.dataset, ctx);
    $('[data-ctx]').forEach(b => b.setAttribute('aria-pressed', ctx[b.dataset.ctx] === b.dataset.val));
    save('ctx', ctx);
  };

  const rungs = (a, st, snap) => {
    const span = (a.n - 1) * st.spread, out = [];
    if (snap) {
      let s = Math.round(st.center - span / 2);
      s = Math.max(0, Math.min(a.scale.length - 1 - span, s));
      for (let i = 0; i < a.n; i++) out.push(a.scale[s + i * st.spread] ?? a.scale.at(-1));
    } else {
      const c = a.scale[Math.round(st.center)];
      for (let i = 0; i < a.n; i++) out.push(+(c + (i - (a.n - 1) / 2) * st.spread * a.step).toFixed(4));
    }
    return out;
  };

  const cap = (cf, letter, vals, extra) => {
    const txt = vals.map((x, k) => x + (cf.axes[k].unit || '')).join(' · ');
    const inSys = cf.inSystem === 'all' || vals.every(x => (cf.inSystem || []).includes(x));
    const c = document.createElement('div');
    c.className = 'cap';
    c.innerHTML =
      `<div class="n"><span class="badge">${letter}</span><span class="val">${txt}</span>` +
      (extra ? ' <span class="add">추가</span>' : '') +
      (cf.token ? `<span class="cost${inSys ? '' : ' off'}">${inSys ? '토큰 그대로'
        : `${cf.token} 고침 (${cf.uses}곳) · 또는 새 토큰`}</span>` : '') + `</div>` +
      `<p class="resolved">${cf.resolve ? cf.resolve(...vals) : ''}</p>` +
      `<p class="eye">${cf.eye ? cf.eye(...vals) : ''}</p>`;
    return c;
  };

  const edge = id => {
    const p = document.querySelector('#' + id + ' .edge'); if (!p) return;
    const now = JSON.stringify(state[id]);
    if (!p.dataset.window) p.dataset.window = now;
    p.classList.toggle('stale', p.dataset.window !== now);
  };

  const build = id => {
    const cf = L[id], sec = document.getElementById(id), st = state[id];
    const box = sec.querySelector('.ladder'), tpl = sec.querySelector('template');
    const cols = cf.axes.map((a, k) => rungs(a, st.axes[k], st.snap));
    const combos = cols.length === 1 ? cols[0].map(v => [v])
                 : cols[0].flatMap(r => cols[1].map(c => [r, c]));
    const list = [...combos, ...st.extra];
    if (cols.length > 1) { box.dataset.matrix = ''; box.style.setProperty('--cols', cols[1].length); }
    box.textContent = '';
    list.forEach((vals, i) => {
      const fig = document.createElement('figure');
      fig.className = 'spec'; fig.tabIndex = 0;
      fig.dataset.letter = LET[i] || '?';
      fig.dataset.vals = JSON.stringify(vals);
      const body = document.createElement('div');
      body.className = 'frame';
      body.append(tpl.content.cloneNode(true));
      fig.append(body, cap(cf, LET[i], vals, i >= combos.length));
      cf.draw(body, ...vals);
      box.append(fig);
    });
    edge(id);
  };

  const commit = id => { save('ctl:' + id, state[id]); build(id); };

  $('[data-ctx]').forEach(b => b.onclick = () => { ctx[b.dataset.ctx] = b.dataset.val; syncCtx(); });
  syncCtx();

  $('section[data-kind]').forEach(sec => {
    const cf = L[sec.id]; if (!cf) return;
    const st = state[sec.id] = load('ctl:' + sec.id, {
      snap: true, extra: [], axes: cf.axes.map(a => ({ center: a.center, spread: a.spread })),
    });
    $('[data-scrub]', sec).forEach(inp => {
      const [what, k] = inp.dataset.scrub.split(':');
      if (what === 'snap') {
        if (typeof cf.axes[0].scale[0] !== 'number') { inp.closest('label').hidden = true; st.snap = true; }
        inp.checked = st.snap;
        inp.onchange = () => { st.snap = inp.checked; commit(sec.id); };
        return;
      }
      if (what === 'center') inp.max = cf.axes[+k].scale.length - 1;
      inp.value = st.axes[+k][what];
      inp.oninput = () => { st.axes[+k][what] = +inp.value; commit(sec.id); };
    });
    build(sec.id);
  });
  document.addEventListener('keydown', e => {
    if (e.key !== 'ArrowUp' && e.key !== 'ArrowDown') return;
    const fig = e.target.closest && e.target.closest('.spec'); if (!fig) return;
    const sec = fig.closest('section'), cf = L[sec.id], a = cf.axes[0];
    if (cf.axes.length > 1 || typeof a.scale[0] !== 'number') return;
    e.preventDefault();
    const nv = +(JSON.parse(fig.dataset.vals)[0] + (e.key === 'ArrowUp' ? 1 : -1) * a.step).toFixed(4);
    const st = state[sec.id];
    if (!st.extra.some(x => x[0] === nv)) st.extra.push([nv]);
    commit(sec.id);
  });
})();
</script>
```

## The style

Only what the controls add. Everything else — page, frames, captions, badge, cost —
is the sheet style in `references/sheet.md`.

```css
.ctx { display:flex; gap:6px; flex-wrap:wrap; margin:0 0 24px }
.ctx button, .add { font:inherit; font-size:12px; padding:3px 10px; border-radius:99px;
        border:1px solid var(--line); background:var(--surface); color:var(--sub) }
.ctx button { cursor:pointer }
.ctx button[aria-pressed="true"] { background:var(--accent-tint); color:var(--accent);
        border-color:transparent }
.scrub { display:flex; gap:16px; align-items:center; color:var(--sub); margin:8px 0 16px }
.ladder { display:grid; grid-template-columns:repeat(auto-fill, minmax(380px, 1fr)); gap:36px 28px }
.ladder[data-matrix] { grid-template-columns:repeat(var(--cols), minmax(0, 1fr)) }
.spec { margin:0 }
.spec:focus-visible { outline:2px solid var(--accent); outline-offset:6px; border-radius:var(--radius) }
.val { font-variant-numeric:tabular-nums }
.cost.off { background:#fdf3e1; color:#8a5a00 }
.spec:has(.cost.off) .frame { outline:1px dashed #d9a441; outline-offset:4px }
.edge { color:var(--sub); margin:18px 0 0 }
.edge.stale { opacity:.45 }
.edge.stale::after { content:' — 창을 옮겼습니다. 경계는 다시 봐야 합니다' }

html[data-bg="pair"] .on-dark { display:none }
html[data-bg="dark"] .on-white, html[data-bg="dark"] .on-gray { display:none }
html[data-rep="one"] .rep > * + * { display:none }
html[data-size="sm"] .lg, html[data-size="lg"] .sm { display:none }
```
