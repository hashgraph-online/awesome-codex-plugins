---
name: fitts-law-screen-edges
description: 'Use this skill when designing for the edges and corners of the screen — where the cursor cannot overshoot, making them effectively infinite-sized targets along one axis. Trigger when designing global navigation, system menus, sticky headers, fixed sidebars, full-bleed CTAs, or anywhere you can put the most-frequent or hardest-to-find actions. Trigger when reviewing an app that has wasteful margins on every side and asks the user to aim for tiny targets in the middle. Sub-aspect of `fitts-law`; read that first if you haven''t already.'
---

# Fitts's Law and the screen edge

The screen edge is the most undervalued real estate in modern web UI. Because the cursor cannot move past the edge, an element placed flush against an edge is effectively *infinite* in size along the axis perpendicular to that edge — the user can fly the cursor past the screen boundary and the cursor stops on the target without precision.

## Why edges matter

The Fitts's Law equation depends on target width along the axis of motion:

```
T = a + b · log₂(D / W + 1)
```

When `W` approaches infinity, the log term collapses to nearly zero — the only remaining cost is the constant base time. This is why Mac's menu bar at the top edge is faster to acquire than a menu in a window: the cursor can fly upward without ever overshooting.

Three consequences:

1. **Edges are faster targets than mid-screen elements**, regardless of element size.
2. **Corners are even faster** — they're "infinite" along *two* axes. The cursor can fly up-and-left to reach a top-left button without precision.
3. **Modern web apps systematically waste this advantage** by adding margins, rounded containers, or "card layouts" that pull all interactive elements away from edges.

## The classic examples

- **macOS menu bar.** Top edge of the entire display. Reaching `File` is fast; reaching the menu inside an application window is slow. (Windows menus inside windows lose this advantage; one of the design debates of the 1990s.)
- **Windows Start button.** Bottom-left corner of the display. Effectively infinite in two axes.
- **iOS home indicator / app switcher gesture.** Bottom edge of the screen — your thumb can swipe up from past the edge and the gesture still registers.
- **Browser back button (when in the browser chrome).** Top edge of the browser window.

## What this means for web design

### 1. Sticky headers earn their position

A `position: fixed; top: 0` navigation bar puts global actions at the top edge, where the user can find them instantly without aiming. The trade-off is screen real estate — you've spent ~56px of vertical space.

```html
<header style="position: sticky; top: 0; z-index: 50; background: white; border-bottom: 1px solid hsl(0 0% 90%);">
  <nav><!-- primary nav --></nav>
</header>
```

The same nav placed mid-page (without sticking) is slower to reach when the user has scrolled.

### 2. Bottom toolbars on mobile

A bottom-anchored navigation bar on mobile combines:

- Edge advantage (cursor / thumb can fly to the bottom and stop).
- Thumb-reach advantage (lower screen is easier for thumb).
- Persistent visibility (always reachable, no scrolling required).

This is why mobile bottom-nav is the modern convention for primary navigation.

### 3. Full-bleed CTAs

A button that extends all the way to the screen edge is far easier to hit than the same button with 24px right margin. On mobile especially, "full-width" buttons are deliberately sized this way for Fitts's reasons.

```html
<!-- Full-bleed CTA: edge advantage on left and right -->
<button style="width: 100%; padding: 16px; font-size: 16px;">Continue</button>
```

If the design feels like it "needs" margin around the button for aesthetic reasons, weigh the cost — you're spending speed for prettiness.

### 4. Side panels and drawers

A side panel that slides in from the right edge has the edge advantage on its right side: the user can fly the cursor right to reach the panel's controls without aiming. Same applies to bottom-sliding drawers.

### 5. The corner advantage

Corners are special. A button in a corner is the easiest target on the screen — the user can move toward both axes simultaneously without precision. Use this for:

- **Account menus** (top-right corner is the convention).
- **Close buttons on full-screen overlays** (top-right or top-left).
- **FAB (floating action button)** on mobile (typically bottom-right corner).
- **"Skip to content" links** (usually top-left, becomes visible on focus).

## What to put at edges

Not everything belongs at the edge. The edge is finite; spend it on the high-value content:

- **Top edge:** global navigation, search, account menu. (Things the user needs *anywhere* in the app.)
- **Bottom edge:** primary action on mobile (FAB, "Save," "Continue"); on desktop, status bars or persistent CTAs in conversion flows.
- **Right edge:** detail panels, properties panes, contextual sidebars.
- **Left edge:** primary navigation in app shells (sidebar nav).
- **Corners:** the rarest, highest-value targets — close, account, primary global action.

## Where the edge advantage is lost

A few patterns that forfeit edge real estate:

### "Card layout" pages with full margins

Modern web apps often render content inside a `max-width: 1200px; margin: 0 auto;` container with 24–48px page margins. Everything interactive is now mid-screen; no edge advantage anywhere.

This is sometimes the right trade-off (readable content width, breathing room, consistent layout across screen sizes), but it costs Fitts's Law performance. At minimum, ensure the global navigation chrome (sticky header, sidebar) does still use the edges.

### Modal dialogs

A modal dialog floating in the middle of the screen has *no* edge advantage. The "close" X is mid-screen, not at the edge. Good modal libraries put the close button at the modal's top-right corner — close to the edge of the modal, even if not the screen.

When a dialog needs to be reachable quickly (e.g., a side sheet for editing a row), prefer a `Sheet` or `Drawer` that anchors to a screen edge over a centered `Dialog`.

### Paginated content with mid-screen prev/next

Content that "paginates" with prev/next buttons mid-screen forfeits the screen edge. Better: anchor prev/next to the screen edges so they're always findable.

### Mobile drawers that don't reach the edge

A "bottom sheet" with rounded corners that floats above the bottom edge. The visual rounding is nice; the edge advantage is forfeited. On most modern designs the sheet is allowed to touch the bottom edge for the home-indicator-clearance area.

## Browser chrome confounds

Web apps don't fully control the screen edges — the browser owns the very top (URL bar, tabs) and the very bottom on mobile (URL bar, system gestures). The "edge" available to a web app is the inside edge of the viewport.

This is why "fullscreen mode" exists in browsers: it gives back the screen edges to the app. Apps that benefit from edge advantages (drawing tools, video editors, presentation software) often offer a "Hide UI" or fullscreen toggle.

## Worked examples

### Example 1: a sticky header earning its space

```html
<header style="
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  height: 56px;
  padding: 0 16px;
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid hsl(0 0% 92%);
">
  <a href="/" style="font-weight: 600;">Acme</a>
  <nav style="display: flex; gap: 16px; margin-left: 32px;">
    <a href="/products">Products</a>
    <a href="/pricing">Pricing</a>
    <a href="/docs">Docs</a>
  </nav>
  <div style="margin-left: auto; display: flex; gap: 8px;">
    <button>Sign in</button>
    <button class="primary">Get started</button>
  </div>
</header>
```

The header sticks to the top edge — easy to reach by flying upward. Account / "Get started" are top-right corner-adjacent.

### Example 2: full-bleed mobile CTA

```html
<div class="page-content" style="padding: 24px;">
  <h1>Confirm your order</h1>
  <p>...summary...</p>
</div>

<!-- Sticky CTA at the bottom edge, full width -->
<div style="
  position: sticky;
  bottom: 0;
  padding: 12px;
  padding-bottom: calc(12px + env(safe-area-inset-bottom));
  background: white;
  border-top: 1px solid hsl(0 0% 92%);
">
  <button class="primary" style="width: 100%; height: 48px;">Place order</button>
</div>
```

The button is full-bleed (no horizontal margin), bottom-anchored. On mobile, the user's thumb flies down to the bottom and stops on the button. Two edge advantages stacked.

### Example 3: a side sheet for row detail

```html
<!-- Main view -->
<table>...</table>

<!-- Side sheet anchored to right edge when open -->
<aside style="
  position: fixed;
  top: 0; bottom: 0;
  right: 0;
  width: min(480px, 100vw);
  background: white;
  box-shadow: -4px 0 24px rgba(0,0,0,0.08);
">
  <header style="display: flex; justify-content: space-between; padding: 16px;">
    <h2>Edit row</h2>
    <button aria-label="Close" style="width: 36px; height: 36px;">×</button>
  </header>
  <form>...</form>
</aside>
```

The sheet's right edge is the screen edge — the user can fly the cursor right to grab any control. The close button at the top-right is corner-adjacent.

## Anti-patterns

- **The all-margin app.** Every screen has 24–48px margins on all sides. No edge is reachable; every target requires precision. Common in "card-y" admin templates.
- **The middle-screen modal with edge controls.** A centered modal where the close X is at the modal's edge but the modal is far from the screen edge. The user aims twice (to the modal, then to the X). Either anchor the modal to a screen edge (sheet) or accept that the close requires precision.
- **The hidden global nav.** A hamburger menu that opens a panel mid-screen. Every primary navigation tap is now a precision aim. Stick the nav at an edge.
- **The "we'll add Wifi-symbol margin around everything" reflex.** Margin-everywhere is the cosmetic fix that costs Fitts's. Reserve margin for places it actually serves visual hierarchy.

## Heuristics

1. **Map the high-frequency interactions.** What does the user do most? Are those at edges or mid-screen? If mid-screen, ask whether you can move them.
2. **The "fly to it" test.** With your eyes closed, can you guess the rough location of the global navigation? If it's at an edge, yes. If it's centered with margin, no.
3. **The precision audit.** Click each primary action. Was precision required, or did the cursor have a "wall" to stop against? Walls = edge advantage.

## Related sub-skills

- **`fitts-law`** (parent).
- **`fitts-law-touch-targets`** — on touch, the safe-area inset complicates pure edge use.
- **`affordance`** — the edge target still needs to look like a target.
- **`visibility`** (cognition) — an edge-anchored control must be visible to be useful.
