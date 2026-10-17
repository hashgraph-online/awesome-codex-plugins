# Operable: standards and edge cases

A reference complementing `accessibility-operable` SKILL.md with deeper detail on the WCAG 2.* criteria and harder cases.

## WCAG 2.* criteria summary

The Operable principle has five guidelines.

### 2.1 Keyboard accessible

- **2.1.1 Keyboard (A)** — all functionality available from a keyboard.
- **2.1.2 No Keyboard Trap (A)** — focus can always leave a region.
- **2.1.4 Character Key Shortcuts (A)** — single-character shortcuts are off by default or remappable.

### 2.2 Enough time

- **2.2.1 Timing Adjustable (A)** — time limits can be turned off, adjusted, or extended.
- **2.2.2 Pause, Stop, Hide (A)** — auto-moving content can be paused.

### 2.3 Seizures and physical reactions

- **2.3.1 Three Flashes or Below (A)** — no content flashes more than 3 times per second.
- **2.3.3 Animation from Interactions (AAA)** — motion triggered by interaction can be disabled.

### 2.4 Navigable

- **2.4.1 Bypass Blocks (A)** — skip links to main content.
- **2.4.2 Page Titled (A)** — page has a descriptive title.
- **2.4.3 Focus Order (A)** — focus follows a meaningful sequence.
- **2.4.4 Link Purpose (A)** — link text is meaningful in context.
- **2.4.5 Multiple Ways (AA)** — more than one way to find a page.
- **2.4.6 Headings and Labels (AA)** — headings and labels are descriptive.
- **2.4.7 Focus Visible (AA)** — the focused element is visually distinct.
- **2.4.11 Focus Not Obscured (Minimum) (AA, 2.2)** — focused elements not entirely hidden by other content.

### 2.5 Input modalities

- **2.5.1 Pointer Gestures (A)** — multi-pointer or path-based gestures have single-pointer alternatives.
- **2.5.2 Pointer Cancellation (A)** — pointer-down doesn't trigger destructive actions; users can cancel before pointer-up.
- **2.5.3 Label in Name (A)** — accessible name includes visible label text.
- **2.5.4 Motion Actuation (A)** — functions triggered by device motion have UI alternatives.
- **2.5.5 Target Size (Enhanced) (AAA)** — targets 44×44 CSS px.
- **2.5.7 Dragging Movements (AA, 2.2)** — dragging has a single-pointer alternative.
- **2.5.8 Target Size (Minimum) (AA, 2.2)** — targets 24×24 CSS px with adequate spacing.

## Hard cases

### Custom focus management

For modals, popovers, comboboxes, menus, the standard pattern:

- Focus moves into the component on open (typically first focusable element).
- Focus is trapped within the component while open.
- Focus returns to the triggering element when the component closes.

This is hard to implement correctly. Edge cases:

- The trigger was inside another modal.
- The trigger was removed from the DOM after the modal opened.
- The user navigated away while the modal was open.
- A nested modal opened.

Most accessible UI libraries (Radix UI, React Aria, headless component libraries) handle these — strongly prefer them over building from scratch.

### Skip links

The classic implementation:

```html
<a href="#main" class="skip-link">Skip to main content</a>

<style>
  .skip-link {
    position: absolute;
    left: -10000px;
    top: auto;
    width: 1px;
    height: 1px;
    overflow: hidden;
  }
  .skip-link:focus {
    position: fixed;
    top: 8px; left: 8px;
    width: auto; height: auto;
    padding: 8px 16px;
    background: black; color: white;
    z-index: 10000;
  }
</style>
```

Some teams provide multiple skip links (skip to nav, skip to main, skip to footer) for power users.

### Drag-and-drop with keyboard

Drag is hard to map to keyboard. Patterns:

- **Arrow keys + spacebar.** Spacebar to "pick up" an item; arrows to move; spacebar to drop. Used by sortable lists.
- **Type-to-position.** Type a number to move an item to that position.
- **Move to / dropdown.** A "Move to..." menu offering destination choices instead of physical drag.

WCAG 2.5.7 (AA, 2.2) requires *some* single-pointer alternative; keyboard alternative is even better.

### Animation and motion

WCAG 2.3.3 (AAA) covers interaction-triggered animation. CSS:

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

For motion that's *meaningful* (a state change), still allow a brief, subtle version even in reduced-motion mode — just avoid the elaborate or distracting variant.

### Focus-not-obscured (WCAG 2.2)

A new criterion in WCAG 2.2: when an element receives focus, it cannot be entirely hidden by other content (e.g., a sticky header). Test by tabbing through and checking that the focused element is fully visible at every step.

Common failures: a sticky header covering inputs as they receive focus; a footer covering form fields when tabbing through.

## Closing

Operable accessibility intersects with general usability — keyboard support and focus management aren't only "for disabled users"; they're for power users, mobile users with bluetooth keyboards, anyone in a hurry. Build it once; it benefits everyone.
