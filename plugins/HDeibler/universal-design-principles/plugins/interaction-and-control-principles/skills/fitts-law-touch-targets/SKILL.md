---
name: fitts-law-touch-targets
description: 'Use this skill when designing for touch — phones, tablets, kiosks, in-car displays, smart-TV remotes, anything where the input is a finger or thumb rather than a precise pointer. Trigger when sizing buttons for mobile, debugging "users keep mistapping," designing a mobile bottom-nav, picking icon sizes for a phone toolbar, or reviewing whether a desktop UI is touch-friendly. Sub-aspect of `fitts-law`; read that first if you haven''t already.'
---

# Fitts's Law for touch targets

The finger is a much wider, much less precise pointer than a mouse cursor. Fitts's Law still applies, but the constants change dramatically — and a few touch-specific phenomena (occlusion, thumb reach, edge gestures) layer on top. This skill covers the practical rules.

## Minimum sizes

Every major touch platform publishes a recommended minimum. They converge:

| Platform / spec | Minimum target | Notes |
|---|---|---|
| **Apple HIG (iOS)** | 44×44 pt | The most-cited number; matches average finger contact. |
| **Material Design (Android)** | 48×48 dp | Roughly equivalent to Apple's 44pt at common densities. |
| **Microsoft (Windows touch)** | 40×40 effective px | Slightly smaller; Microsoft's research basis. |
| **WCAG 2.5.5 (Level AAA)** | 44×44 CSS px | Strictest accessibility minimum. |
| **WCAG 2.5.8 (Level AA, 2.2)** | 24×24 CSS px (with adequate spacing) | Newer, more lenient minimum. |

The practical rule: **44×44 CSS pixels for any touchable element**. This is the safe number across platforms and accessibility levels. Going smaller is occasionally defensible in specific dense expert contexts; never as a default.

The visible *icon* inside the button can be smaller (16–24px is common). The *hit area* — the actual touchable region — is what 44×44 measures.

```css
/* Right: a small icon with a generous tap area */
.icon-button {
  display: inline-grid;
  place-items: center;
  width: 44px;
  height: 44px;
  padding: 10px;        /* keeps icon centered while tap area stays at 44 */
  border: 0;
  background: transparent;
  border-radius: 22px;
}
.icon-button svg { width: 20px; height: 20px; }
```

## Spacing between targets

Fitts's Law is about acquiring *one* target. When targets are clustered, *spacing* between them prevents accidental neighbor-taps. The convention:

- **At least 8px of clear space** between adjacent touch targets.
- **44×44 hit area applies to each target**, even if visually they overlap (e.g., padded buttons share visual edges).

For dense clusters (chip rows, segmented controls), increase visual differentiation: bordered, with internal padding, with adequate gap.

## The thumb-reach map

When a phone is held one-handed, the thumb can reach some screen regions easily and others only with strain. Research (Hoober and others) maps this:

```
+--------------------+
|       hard         |  <- top of screen, far from thumb base
|   hard | medium    |
| medium | easy      |
| medium | easy      |
| medium | easy      |  <- bottom-right (right hand) is easiest
+--------------------+
```

For right-handed users, the bottom-right of the screen is easiest; the top-left is hardest. Left-handed users mirror.

**Practical implications:**

- **Primary actions go in the lower portion of the screen.** Floating action buttons (FAB) at bottom-right are a strong Fitts-and-thumb-reach win.
- **Bottom navigation beats top navigation** for high-frequency tap-to-navigate patterns.
- **Top-bar actions should be infrequent or hand-agnostic** (search, settings, profile menu — not "save" or "publish").
- **Reachability features** (iOS double-tap-home; Android one-handed mode) exist because top corners are genuinely hard.

```html
<!-- Bottom nav: thumb-friendly, primary destinations -->
<nav style="position: fixed; bottom: 0; left: 0; right: 0;">
  <!-- 3-5 destinations, evenly spaced, 56px+ tall -->
</nav>

<!-- FAB: bottom-right for right-handed primary action -->
<button style="position: fixed; bottom: 24px; right: 24px; width: 56px; height: 56px; border-radius: 28px;">
  <PlusIcon />
</button>
```

## Occlusion (the finger covers the target)

Once the user's finger touches the screen, it covers the target. A few consequences:

- **Confirm visually after touch, not just on touch-up.** The user wants to know the press registered before they lift.
- **Don't rely on the user reading text under their finger.** Tooltips, micro-confirmations, "what does this do?" hints under the touch point are invisible.
- **Touch targets should provide visual state changes that radiate beyond the finger** — color flash on the whole row, a ripple effect, an outline that extends past the contact area.

Material Design's ripple effect is a classic occlusion-mitigation: the ripple expands outward from the touch point, providing visible feedback that survives the finger's presence.

```css
@keyframes ripple {
  to { transform: scale(4); opacity: 0; }
}
.button-pressed::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.2;
  animation: ripple 600ms;
}
```

## Edge gestures and the safe area

Modern phones use the screen edges for system gestures (back-swipe, app-switcher, control-center). A button placed at the absolute edge competes with these gestures.

**Practical rule:** keep an 8–16px inset from the edges for primary interactive content. Use the system's safe-area insets for top notch and bottom home-indicator clearance:

```css
.bottom-bar {
  padding-bottom: env(safe-area-inset-bottom);
}
.top-bar {
  padding-top: env(safe-area-inset-top);
}
```

The screen-edge Fitts-Law advantage still works for *layout* (a tap target abutting the edge is large in one dimension), but *interaction* must respect system gestures.

## Hover states (and why they don't translate)

Touch devices have no hover. UI patterns that rely on hover-revealed actions (a row's "Edit" / "Delete" buttons that appear on cursor over) silently fail on touch. Mitigations:

- **Always-visible row actions** (perhaps dimmed; see below). Touch users see and can tap them.
- **Press-and-hold** to reveal a context menu (analogous to right-click).
- **Swipe gestures** for revealed actions (iOS-style swipe-to-delete on a list row).

Don't ship "hover to discover the action" patterns to mobile.

## Worked examples

### Example 1: a row in a list with an action button

**Anti-pattern (mouse-only):**

```html
<li class="list-item">
  <span>Project Acme</span>
  <button class="hover-only" style="opacity: 0;">Open</button>
</li>
<style>
  .list-item:hover .hover-only { opacity: 1; }
</style>
```

On touch, the button is invisible — and even if you tap it, you can't see it.

**Right (touch-friendly):**

```html
<li class="list-item" style="display: flex; align-items: center; padding: 12px 16px; min-height: 56px;">
  <span style="flex: 1;">Project Acme</span>
  <button aria-label="Open Acme" style="width: 44px; height: 44px;">
    <ChevronRightIcon />
  </button>
</li>
```

The action is always visible; the row itself meets the 44px height minimum (56px is even better).

### Example 2: a numeric stepper

```html
<div class="stepper" style="display: inline-flex; align-items: center; gap: 12px;">
  <button aria-label="Decrease" style="width: 44px; height: 44px;">−</button>
  <input type="number" value="1" style="width: 60px; height: 44px; text-align: center;" />
  <button aria-label="Increase" style="width: 44px; height: 44px;">+</button>
</div>
```

Both buttons are 44×44 with 12px gap to the input — generous spacing prevents misclicks.

### Example 3: a floating action button (FAB)

```html
<button class="fab" aria-label="New post" style="
  position: fixed;
  bottom: calc(24px + env(safe-area-inset-bottom));
  right: 24px;
  width: 56px; height: 56px;
  border-radius: 28px;
  background: var(--brand);
  color: white;
  display: grid; place-items: center;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
">
  <PlusIcon />
</button>
```

Bottom-right for thumb reach. 56×56 hit area. Safe-area-inset for home-indicator clearance. Subtle shadow because FABs *do* float above content.

### Example 4: a tab bar

```html
<nav class="tab-bar" style="
  position: fixed; bottom: 0; left: 0; right: 0;
  display: grid; grid-template-columns: repeat(5, 1fr);
  height: calc(56px + env(safe-area-inset-bottom));
  padding-bottom: env(safe-area-inset-bottom);
  background: white;
  border-top: 1px solid hsl(0 0% 90%);
">
  <button class="tab" aria-current="page">
    <HomeIcon style="width: 24px; height: 24px;" />
    <span style="font-size: 10px;">Home</span>
  </button>
  <!-- four more tabs -->
</nav>

<style>
  .tab {
    display: grid; place-items: center; gap: 2px;
    border: 0; background: transparent;
    color: hsl(0 0% 50%);
  }
  .tab[aria-current="page"] { color: var(--brand); }
</style>
```

5 tabs across the bottom. Each tab gets ~76px width × 56px height — generously above 44×44.

## Anti-patterns

- **Tiny X close on a popover.** A 16×16 X in the corner. On touch, nearly impossible to hit reliably.
- **Stacked menu items at 32px row height.** The user means to tap "Settings" and gets "Sign out." Make rows ≥ 44px (preferably 48–56px) on touch.
- **Edge-flush primary actions.** A "Send" button at the absolute right edge that triggers the system back-gesture instead. Inset 8–16px.
- **Hover-only actions.** Row actions, contextual menus, tooltips that only appear on cursor-over. Either always-visible or accessible via tap-to-reveal.
- **Inert spacing.** A 44×44 visual button with only 16×16 of actual touchable area (because some CSS issue). Audit with browser DevTools' touch emulator.

## Heuristics

1. **The thumb test.** Hold your phone one-handed, naturally. Try to tap every primary action. Anything that requires a hand-shift is wrong-position.
2. **The fingertip overlay.** In design comps, overlay a 44×44 circle on every interactive element. Anything where the circle exceeds the visual element's bounds is fine; anything smaller than the circle is too small.
3. **Real-device testing on the smallest target screen.** A design that works on a Pixel 7 may fail on a small Android device or iPhone SE. Test on actual hardware in actual hands.
4. **The bystander test.** Watch someone else use your app. Where do they hesitate or correct themselves? Each correction is a Fitts-or-occlusion failure.

## Related sub-skills

- **`fitts-law`** (parent).
- **`fitts-law-screen-edges`** — companion for desktop; some overlap on mobile (safe areas).
- **`affordance`** (parent plugin) — touch targets need visual affordance to be discoverable.
- **`accessibility-operable`** (process plugin) — touch target sizes are an accessibility minimum; don't go below.
