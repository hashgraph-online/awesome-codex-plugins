# Motion

A real browser, so CSS motion actually runs: `transition`, `@keyframes`, `transform`,
`:hover` · `:focus-visible` · `:active`, `@starting-style`, `:has()`, `<details>`,
`<dialog>`, and scroll-driven `animation-timeline: scroll() / view()`.

Duration, easing, travel distance and stagger are all decidable here — with three
devices that static ladders never need.

## Three devices

**1. One trigger fires them all.** Specimens that autoplay on their own clocks drift
out of phase and can't be compared. Put a single `전체 재생` button at the top of the
row that restarts every specimen in the same frame.

    document.querySelectorAll('.spec').forEach(el => {
      el.classList.remove('run'); void el.offsetWidth; el.classList.add('run');
    });

The `void el.offsetWidth` reflow is what makes the restart take — without it the class
removal and re-add collapse into nothing.

`.spec` is also what the engine in `references/controls.md` stamps, so the two meet here.
Put `run` on the figure and key the CSS off it — `.spec.run .thing { animation: ... }` —
and remember that **any scrub re-stamps the ladder and clears `run`.** Duration and
easing scrub like any other axis; the replay button just has to be pressed again after.

**2. Replay.** It's over before it's judged. Keep the button reachable, or loop.

**3. A slow-motion toggle.** This is the one that matters. **A 200ms easing difference
is invisible at real speed** — `ease-out` and `cubic-bezier(.22,1,.36,1)` are
indistinguishable until slowed down.

    :root.slow * { animation-duration: 4s !important; transition-duration: 4s !important; }

Offer 1x and 0.25x. **Decide at 1x, distinguish at 0.25x** — a curve that reads
beautifully in slow motion can be imperceptible at speed, and shipping runs at 1x.

## Ladders

| axis | ladder |
|---|---|
| duration | 80 · 120 · 160 · 200 · 300ms |
| easing | `linear` · `ease-out` · `cubic-bezier(.4,0,.2,1)` · `cubic-bezier(.22,1,.36,1)` · `cubic-bezier(.34,1.56,.64,1)` |
| travel | 2 · 4 · 8 · 16 · 24px |
| stagger | 20 · 40 · 60 · 80ms per item |

Easing needs a **travel long enough to show the curve** — 2px of movement makes every
curve identical. Lay easing specimens out over at least 24px, or over opacity plus
transform together.

Stagger only reads with enough items. Six minimum.

## What can't be settled here

- **Screenshots capture static state only.** Verification step 3 can't see motion at
  all, so a motion unit rests entirely on what the user reports from the browser.
  Say so rather than implying it was checked.
- **Entry and exit timing around mount/unmount will differ** — the real library sets the
  state attributes, the sheet imitates them (`references/sweeping.md`).
- **Motion libraries don't take these values directly.** If the project uses Framer
  Motion, GSAP or similar, spring physics has no CSS equivalent — a cubic-bezier is an
  approximation, not a translation. **This belongs in the blast radius report**, not
  discovered afterwards:

  > 이 easing 은 CSS transition 기준입니다. 프로젝트는 Framer Motion 을 쓰므로
  > spring 파라미터로 옮겨야 하고, 완전히 같지는 않습니다.

  Detect it: `grep -o 'framer-motion\|gsap\|@react-spring[a-z/]*' package.json | sort -u`

## Reduced motion

Whatever gets chosen, the applied code needs a `prefers-reduced-motion: reduce` branch.
Don't make it a unit of its own — raise it once at the apply gate and carry the value into
a reduced variant (usually opacity only, no transform).
