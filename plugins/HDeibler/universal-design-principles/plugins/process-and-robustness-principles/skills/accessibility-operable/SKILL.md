---
name: accessibility-operable
description: 'Use this skill when the question is whether users can *operate* a UI — keyboard, switch device, voice, screen-reader gestures — not just by mouse or touch. Trigger when designing keyboard navigation, focus management for modals/menus/popovers, drag-and-drop with alternatives, motion-heavy interactions, or any flow that asks the user to do something. Covers WCAG Principle 2 (Operable). Sub-aspect of `accessibility`; read that first if you haven''t already.'
---

# Accessibility — Operable

WCAG Principle 2: user-interface components and navigation must be operable.

The five sub-criteria, simplified:

1. **Keyboard accessible** — everything that works with mouse must work with keyboard.
2. **Enough time** — timing-out interactions are warned and extendable.
3. **Seizures and physical reactions** — no flashing content; respect motion preferences.
4. **Navigable** — users can find content and know where they are.
5. **Input modalities** — touch and other input methods supported with adequate target size.

## 1. Keyboard accessible

### Every interactive element is reachable via Tab

The default `Tab` order follows DOM source order and only includes natively focusable elements: `<a href>`, `<button>`, `<input>`, `<select>`, `<textarea>`, `<summary>`, `<iframe>`, plus elements with `tabindex="0"`.

- **Use semantic elements.** `<button>`, not `<div onclick>`.
- **Use `tabindex="0"`** to add custom interactive elements to tab order.
- **Use `tabindex="-1"`** to make an element programmatically focusable (e.g., for focus management) but not reachable via Tab.
- **Avoid `tabindex` > 0.** Positive tabindex creates a custom tab order that's almost always worse than DOM order and bewilders screen readers.

### Visible focus indicators

The user must see where focus is. Browsers provide default focus rings; never `outline: none` without a replacement.

```css
/* Right: replace, don't remove */
:focus { outline: none; }
:focus-visible {
  outline: 2px solid hsl(220 90% 50%);
  outline-offset: 2px;
  border-radius: 0.25rem;
}

/* Wrong: removes the only signal a keyboard user has */
*:focus { outline: none; }
```

`:focus-visible` (rather than `:focus`) shows the ring only when focus arrived via keyboard (or non-pointer means), not on every mouse click. This addresses the historical "designers don't want focus rings on click" concern without sacrificing keyboard accessibility.

### Standard keys for standard interactions

Honor user expectations:

| Key | Behavior |
|---|---|
| `Tab` | Focus next; `Shift+Tab` for previous |
| `Enter` / `Space` | Activate button, follow link, toggle checkbox |
| `Esc` | Close overlay (Dialog, Sheet, Popover, Combobox) |
| Arrow keys | Move within radio groups, sliders, tabs, menus, comboboxes |
| `Home` / `End` | First / last in a list or menu |
| `Page Up` / `Down` | Scroll a region |
| `/` | Often: focus search (de facto convention) |
| `Cmd/Ctrl+K` | Often: open command palette (de facto convention) |

ARIA Authoring Practices Guide documents canonical keyboard interactions for every common pattern.

### No keyboard traps

A keyboard trap is a region where focus enters and cannot leave via keyboard alone. Common offenders:

- Custom datepickers without arrow-key escape.
- Embedded iframes with their own focus management that don't release.
- Modal dialogs without `Esc` to close.

**Test:** keyboard-only walkthrough. If you ever get stuck and have to mouse to escape, you have a trap.

### Focus management for overlays

When a modal opens:

1. Move focus into the modal (typically the first focusable element, or a "primary" focus target).
2. Trap focus inside until the modal closes.
3. Restore focus to the trigger element when the modal closes.

```js
// Pseudocode — in practice use a library that handles edge cases
function openModal(modal, trigger) {
  modal.dataset.previousFocus = trigger;
  const focusables = modal.querySelectorAll('a, button, input, [tabindex="0"]');
  focusables[0]?.focus();
  // ... trap focus on Tab/Shift+Tab within `focusables` ...
}

function closeModal(modal) {
  modal.previousFocus?.focus();
}
```

Most accessible UI libraries (Radix UI, React Aria, headless component sets) do this automatically. Custom-built modals that skip focus management are inaccessible.

### Skip links

```html
<a href="#main" class="skip-link">Skip to main content</a>
<header><nav>... 50 nav items ...</nav></header>
<main id="main">...</main>

<style>
  .skip-link {
    position: absolute;
    left: -10000px;
    top: auto;
  }
  .skip-link:focus {
    position: fixed;
    top: 8px; left: 8px;
    padding: 8px 16px;
    background: black; color: white;
    z-index: 100;
  }
</style>
```

Keyboard users tab past nav to reach content quickly. Visible only on focus so it doesn't clutter sighted-mouse-user views.

## 2. Enough time

### Adjustable timing

If the system has timeouts (session expiry, captcha re-verify, time-limited form), users must be able to:

- Turn it off, OR
- Extend it, OR
- Adjust it (across a wide range, ≥ 10× default).

Exceptions: real-time events (auctions), where time limit is essential.

```html
<!-- Right: warn before timeout, allow extension -->
<dialog open>
  <h2>Session about to expire</h2>
  <p>You have 60 seconds before your session ends.</p>
  <button onclick="extendSession()">Stay signed in</button>
</dialog>
```

### No moving / blinking content (without controls)

Content that auto-moves, blinks, or scrolls for more than 5 seconds must be pause-able / stop-able.

This includes carousels, animated banners, news tickers, autoplaying video.

## 3. Seizures and physical reactions

### Three flashes or below

WCAG 2.3.1: don't have content that flashes more than 3 times per second. Photosensitive epilepsy can be triggered by flashing in the 3–55 Hz range.

In practice, this rules out: rapid strobe effects, blinking text (don't), high-contrast flashing animations.

### Motion preferences

WCAG 2.3.3: respect `prefers-reduced-motion`. Many users (vestibular disorders, migraine, motion sensitivity) have configured their OS to request reduced motion.

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

For specific motion that's *meaningful* (a state change indicator), allow it but make it briefer / less dramatic in reduced-motion mode.

## 4. Navigable

### Page titles

Every page has a unique, descriptive `<title>`:

```html
<title>Settings — Notifications — Acme</title>
```

Screen reader users hear the title on page load; tab labels show it; browser history relies on it. Generic "Acme" titles for every page are useless.

### Focus order matches reading order

When a user tabs through a page, focus should follow the visual / logical reading order. CSS-rearranged elements (Grid, Flex order) can break this — test.

### Link purpose

Links should be understandable from their text alone (or from text + immediately-adjacent context). Screen reader users navigate by listing all links.

```html
<!-- Wrong: "click here" tells the screen reader user nothing -->
<p>To read more, <a href="/blog/post">click here</a>.</p>

<!-- Right: link text describes destination -->
<p>Read more in <a href="/blog/post">our annual review</a>.</p>
```

### Multiple ways to find content

WCAG 2.4.5 (AA): provide more than one way to find a page (search, sitemap, navigation, related-content links). Helps users with cognitive impairments and users who navigate non-linearly.

### Headings and labels are descriptive

`<h2>Article</h2>` — useless. `<h2>Q4 sales recap</h2>` — useful.

### Focus visible (covered above)

### Location indicators

Users need to know where they are. Breadcrumbs, current-page highlighting in nav, page titles all serve this.

```html
<nav>
  <a href="/dashboard">Dashboard</a>
  <a href="/projects" aria-current="page">Projects</a>
  <a href="/team">Team</a>
</nav>
```

`aria-current="page"` tells assistive tech which item is current; visual styling reinforces it.

## 5. Input modalities

### Target size (covered in `fitts-law-touch-targets`)

WCAG 2.5.5 (AAA): targets ≥ 44×44 CSS px.
WCAG 2.5.8 (AA, 2.2): targets ≥ 24×24 CSS px with adequate spacing.

### Pointer gestures

Multi-pointer or path-based gestures (pinch, swipe, drag) must have single-pointer alternatives:

- Pinch-to-zoom → buttons / keyboard for zoom in/out.
- Swipe-to-delete → swipe + always-visible action button.
- Drag-and-drop → keyboard reorder (arrows + spacebar).

### Pointer cancellation

The user can cancel a pointer action by moving away before lifting. Don't trigger destructive actions on `mousedown`; trigger on `mouseup` or `click`.

### Label in name

The accessible name must include any visible label text. Pattern:

```html
<!-- Right: visible text matches accessible name -->
<button>Save</button>

<!-- Wrong: aria-label overrides visible text, voice control breaks -->
<button aria-label="Submit">Save</button>
<!-- Voice user says "click Save" — fails because the accessible name is "Submit" -->
```

### Motion actuation

Functions triggered by device motion (shake, tilt) must have UI alternatives. Some users physically can't shake a device.

## Worked example: an accessible dropdown menu

```html
<div class="dropdown">
  <button id="menu-button"
          aria-haspopup="true"
          aria-expanded="false"
          aria-controls="actions-menu">
    Actions
  </button>
  <ul id="actions-menu"
      role="menu"
      hidden
      aria-labelledby="menu-button">
    <li role="menuitem" tabindex="-1">Edit</li>
    <li role="menuitem" tabindex="-1">Duplicate</li>
    <li role="menuitem" tabindex="-1">Archive</li>
    <li role="separator"></li>
    <li role="menuitem" tabindex="-1" class="destructive">Delete</li>
  </ul>
</div>
```

JavaScript to handle:

- `Enter`/`Space`/`ArrowDown` on the button: open menu, focus first item.
- `ArrowUp`/`ArrowDown` in menu: move focus.
- `Home`/`End`: first / last item.
- `Esc`: close, return focus to button.
- `Tab`: close, move to next focusable.
- Click outside: close.

Plus `aria-expanded` toggles between `"true"` and `"false"`.

This is verbose because menus genuinely have a lot of expected behavior. Use Radix, React Aria, or another library that implements WAI-ARIA Menu pattern correctly — don't roll your own.

## Anti-patterns

- **`outline: none` without a replacement.** Single largest accessibility crime in modern web design.
- **`<div onclick>`.** Not focusable, not keyboard-operable, not announced as a button. Use `<button>`.
- **Mouse-only menus.** Hover-revealed menus that close on `mouseout` with no keyboard equivalent.
- **Modal traps.** Modals that don't close on `Esc`, don't trap focus, don't restore focus on close.
- **Custom date pickers without keyboard.** Date pickers are notoriously inaccessible; if you must build one, follow ARIA Authoring Practices.
- **Drag-only reorder.** No keyboard alternative for sorting or reordering.
- **Auto-advancing carousels.** Focus thrash on every slide change; no way for keyboard users to read content before it disappears.

## Heuristics

1. **Unplug your mouse.** Walk through every primary flow. Anything you can't do with keyboard alone is broken.
2. **Tab around the page.** Focus indicators visible? Tab order logical? Any traps?
3. **Try `Esc` everywhere.** Open every overlay; `Esc` should close it.
4. **Test with `prefers-reduced-motion: reduce`.** macOS: System Settings → Accessibility → Display → Reduce Motion. Are critical animations still meaningful? Are decorative ones gone?
5. **Voice-control test.** macOS Voice Control or Windows Speech Recognition. Say "click [visible text]." If the click works, label-in-name is correct.

## Related skills

- **`accessibility`** (parent).
- **`accessibility-perceivable`** — what users see; complementary.
- **`accessibility-understandable`** — what users comprehend.
- **`accessibility-robust`** — markup that assistive tech can rely on.
- **`fitts-law`** and **`fitts-law-touch-targets`** (interaction) — target size.
- **`feedback-loop`** (interaction) — keyboard interactions need visible feedback too.
