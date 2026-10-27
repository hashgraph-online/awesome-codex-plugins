# layout — the reflow-free chat surface (the ONE sizing standard)

The single source of truth for how a CometChat surface is SIZED so it renders full-size
from the first frame and never reflows. `core`, `placement`, and `calls` POINT here
instead of each re-stating the CSS — change the rule once, here.

> **The kit is NOT the problem.** Every UI Kit component fills its parent by design
> (`height:100%` / flex-fill) and ships its OWN loading/empty state
> (`loadingView` / `emptyView` slots). A surface that starts small and grows, or collapses
> to ~0px, is a HOST **container-sizing** defect, not a kit bug: the host box is
> **content-driven** instead of **pinned**. Pin the box and the kit renders full-size
> immediately and swaps loading→loaded INSIDE a stable box — zero shift.

## The named failure modes

Two distinct sizing defects, one root cause (a content-driven box the kit then fills):

1. **Static collapse** — the surface renders as a ~0px sliver / crammed top-left, because
   the mount container (or an ancestor) has no resolved height. (The #1 "UI looks broken"
   report; anti-patterns #8.)
2. **Load-transition reflow** *(named here for the first time)* — the surface is SMALL
   while the conversation list loads, then GROWS to full size once content arrives; height
   and/or width expand WITH content instead of being pinned. It looks broken and can
   misplace the UI. Root cause: the box is **content-driven** (ancestor chain not
   `height:100%`, or the container uses `min-height`/`auto`, or an intermediate wrapper
   isn't sized), so before content loads there is nothing to give the box its size — the
   kit fills "nothing," and only grows as messages/list items arrive. **A pinned box with
   a prepared ancestor chain is full-size from frame 1; the kit's own loading state fills
   it; the swap to loaded causes NO reflow.**

## The five invariants (a reflow-free surface satisfies ALL)

**(a) Prepare the ancestor chain.** Make `html, body, #root` full-height so a
`100dvh`/`100%` on your container has a non-zero chain to resolve against:
```css
html, body, #root { height: 100%; margin: 0; }
```
A bare app usually has NONE of these → every descendant height resolves against `0`. A
fresh Vite/CRA/Next scaffold has the OPPOSITE problem — it CENTERS + width-caps + pads
`#root` (`max-width:1280px; margin:0 auto; padding:2rem; text-align:center` +
`body{display:flex; place-items:center}`), gutter-boxing chat into a centered island with
content clipping off the edge. **Watch for a WIDTH-PINNED root, not just `max-width`
(AUDIT-035):** some scaffolds pin `#root { width: 1126px; margin: 0 auto; border-inline: … }`
— nulling only `max-width` leaves the fixed `width`, so the surface stays gutter-boxed on
desktop AND overflows horizontally on a phone. Reset `width` (and `min-height`/`border`) too.
Either way, RESET/PREPARE the root before the chat CSS — add what's missing AND undo the
scaffold cruft (AUDIT-019/035):
```css
#root { width: auto; max-width: none; min-height: 0; border: 0; text-align: left; display: block; }  /* undo cap/center/pad AND a width-pin */
body  { display: block; place-items: normal; min-width: 0; }   /* undo body flex-centering */
*, *::before, *::after { box-sizing: border-box; }
```

**(b) Pin the surface to a content-INDEPENDENT height.** The surface box's height must NOT
depend on its content. Full-page → `height: 100dvh` (a stable viewport height). Embedded →
a **fixed height** (e.g. `600px`) or a **sized grid/flex CELL** that supplies one. **Never
`min-height` and never `auto`** on the surface box — those grow with content and are the
load-transition reflow. `100dvh` (dynamic viewport height) beats `100vh` on mobile (no jump
when the URL bar hides).

**(c) Size the columns/panes.** Sizing the root is NOT enough — the columns are the kit's
actual parents and must resolve a height + a bounded width, or the kit fills content size
and the surface crams into the top-left:
```css
.cc-app        { display: flex; height: 100dvh; width: 100%; overflow: hidden; }
.cc-app .list-column  { width: 320px; flex-shrink: 0; height: 100%; }
.cc-app .message-pane { flex: 1 1 0; min-width: 0; min-height: 0; height: 100%;
                        display: flex; flex-direction: column; overflow: hidden; }
```
**`min-height: 0` + `min-width: 0`** are load-bearing: a flex child's default
`min-height:auto` refuses to shrink below its content, so a long list/message GROWS the
parent (reflow + overflow) instead of scrolling inside it. `min-height:0` lets the child
**scroll, not grow the parent**; `min-width:0` + `overflow:hidden` stop horizontal spill.

**Keep `CometChatProvider` OUT of the flex chain, and don't rely on `height:100%` in a flex
chain (AUDIT-036).** `CometChatProvider` renders a `<div class="cometchat">` wrapper. Put it
OUTSIDE the sized `.cc-app` (wrap the whole surface) — NOT between `.cc-app` and the columns:
a wrapper there becomes an unsized block in the flex row, so the columns stop forming a row
and the pane's height chain collapses (measured live: the message pane shrank to just its
65px header). The `height:100%` in (c) above works ONLY because `.cc-app` is a fixed
`100dvh` box (a definite height for `%` to resolve against). If you add an **app bar above
the surface** so `.cc-app` becomes a flex *child* (`flex:1`) instead of a fixed `100dvh`
box, its height is flex-derived/indefinite and `height:100%` on the columns collapses to
content — drive heights through the flex chain instead: every level `display:flex` +
`flex:1 1 0` + `min-height:0` (stretch, not `height:100%`), give the provider's `.cometchat`
wrapper `flex:1 1 0; min-height:0; display:flex`, and flex the list vs composer explicitly
(list `flex:1 1 0; min-height:0`, composer `flex:0 0 auto`).

**(d) Render the kit's OWN loading state inside the pinned box — no load-transition
reflow.** The surface must be **full-size BEFORE content loads, not grow into it.** Because
(a)–(c) pin the box independently of content, the kit's built-in loading/empty state
(`loadingView` / `emptyView` — the components ship them) renders as a **full-size
skeleton**, and when real data arrives the loaded view swaps in **inside the same box with
zero shift.** Do NOT gate the whole surface behind your own "is it loaded yet?" flag that
mounts a small placeholder then a big chat — that IS the reflow. Mount the sized surface
immediately; let each component show its own loading state in place.

**(e) No `transform` / `filter` on ancestors.** A non-`none` `transform`, `filter`,
`backdrop-filter`, `perspective`, or `will-change:transform` on any ancestor of the chat
creates a containing block that clips the kit's `position:fixed` overlays (options menu,
emoji picker, reactions, thread panel, call screen) — and Tailwind `translate-*`/`scale-*`/
`rotate-*`/`transition-transform` all compile to `transform`. Animate `right`/`left`/width
instead (anti-patterns #11). Also: don't let host global CSS (`text-align`/flex-centering/
`flex`/a reset/Tailwind base) leak onto the `.cometchat` subtree — it mis-sizes kit
internals; scope it away and customize via `--cometchat-*` vars + view slots (anti-patterns
#12), never by overriding internal BEM classes.

## The minimal full-page recipe (put it BEFORE the chat CSS)

Assemble the three CSS blocks above in order — (a) prepare/RESET the ancestor chain FIRST,
then (b) pin `.cc-app` to `100dvh`, then (c) size the columns with `min-height:0` (= scroll,
don't grow). That exact stack (nothing more) is the full-page recipe.

For the grown three-column app the same invariants hold with an extra `.side-column`
(fixed-ish width, `height:100%`, `min-height:0`) — the full 3-column CSS is in
`cometchat-react-v7-placement` (the Combined-app recipe), which references THIS standard for
the invariants.

## Embedded (not full-page)

Opt out of `100dvh`, keep invariants (a),(c),(d),(e): give the surface box a **fixed
height** (`height:600px`) or drop it into a **sized grid/flex cell** whose track supplies a
resolved height (`grid-template-rows: 1fr` on a `100dvh` parent, or a flex parent with the
region `flex:1; min-height:0`). Never a `min-height`/`auto` region — same reflow. See the
`placement` embedded/popup/sidebar variants.

## The invariant, per platform (this file is the WEB recipe)

The PRINCIPLE is universal — every platform's UI Kit fills its container and must not
reflow between loading and loaded, so every platform pins a content-independent box and
lets the kit's own loading state fill it. The RECIPE differs:
- **web (react/angular):** this file — `100dvh` + the prepared/reset ancestor chain + the
  `min-height:0` columns + no `transform`/`filter` on ancestors + the kit's
  `loadingView`/`emptyView` inside the pinned box.
- **mobile (rn/flutter/native), when those packs exist:** the equivalent — flex-fill /
  `Expanded`/`match_parent` to a stable screen size, safe-area insets, keyboard-avoidance
  so the composer doesn't reflow the list, and the kit's own loading state inside the
  pinned screen. Each platform's `core`/`placement` bakes its own `layout` recipe and
  inherits the SAME contract (`prepared-ancestor-chain`, `pinned-viewport-height`,
  `no-load-transition-reflow`, `column-min-height-0` — the web tokens; a platform renames
  the mechanism, not the invariant). See the factory `RULES.md` "Layout / sizing" rule.

## Verify (advisory, human check)

Full-size from the FIRST frame (a full-height skeleton, not a small box that grows); no
reflow when the conversation list finishes loading (the box doesn't change size); no ~0px
collapse; no horizontal scrollbar at wide (1280) or narrow (720) widths
(`scrollWidth > innerWidth` ⇒ broken); overlays (menus, emoji, thread, call) anchor to the
viewport (no `transform`/`filter` ancestor). If it grows into place, an ancestor is
content-driven — walk (a)→(c).
