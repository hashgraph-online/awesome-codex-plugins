# Disclosure affordances: pattern reference

A reference complementing `progressive-disclosure-disclosure-affordances` with deeper detail on each pattern's accessibility, motion design, and history.

## Native vs. custom

Modern HTML provides native primitives for several disclosure patterns:

- **`<details>` / `<summary>`** — inline expand. Native keyboard, semantics, ARIA-correct.
- **`<dialog>`** — modal. Native focus management when invoked via `.showModal()`.
- **`<select>`** — dropdown. Native scaffolding for popover-style choosers.

Native primitives come with accessibility for free. Custom implementations frequently get focus management, ARIA, and keyboard handling wrong. Reach for native first.

When native won't do (you need rich content inside the disclosure, you need styling unavailable on native), use a well-maintained accessible component library (Radix UI, React Aria, headless component sets, shadcn) rather than rolling your own.

## Pattern: inline expand (the `<details>` pattern)

```html
<details>
  <summary>Advanced filters</summary>
  <fieldset>
    <label>Created after <input type="date" /></label>
    <label>Tags <input /></label>
  </fieldset>
</details>
```

**Native behaviors for free:**
- Click summary or press Enter/Space to toggle.
- Toggle state in DOM (`open` attribute).
- Screen readers announce expanded/collapsed state.
- Keyboard focus on the summary by default.

**Styling considerations:**
- Default browser triangle marker can be hidden with `details > summary { list-style: none; }` and `summary::-webkit-details-marker { display: none; }`.
- Use `[open]` selector to style the expanded state differently.
- Animate the disclosure with care — `<details>` doesn't animate height by default; libraries like Motion or `interpolate-size: allow-keywords` (CSS) help.

## Pattern: accordion (multiple `<details>` or ARIA-driven)

A vertical stack of disclosure sections. The accessibility pattern is documented in WAI-ARIA Authoring Practices.

```html
<div class="accordion">
  <h3>
    <button aria-expanded="true" aria-controls="panel-1">
      Profile
    </button>
  </h3>
  <div id="panel-1">...profile fields...</div>

  <h3>
    <button aria-expanded="false" aria-controls="panel-2">
      Notifications
    </button>
  </h3>
  <div id="panel-2" hidden>...notification fields...</div>
</div>
```

Or simpler with `<details>`:

```html
<details open>
  <summary><h3>Profile</h3></summary>
  <div>...profile fields...</div>
</details>
<details>
  <summary><h3>Notifications</h3></summary>
  <div>...notification fields...</div>
</details>
```

**Single-open vs. multi-open:**

- **Single-open accordion** (only one section open at a time; opening another closes the previous) reduces visual mass but adds friction when comparing sections.
- **Multi-open accordion** (any combination open) is more flexible; common in settings pages. Lacks native scaffolding (since `<details>` siblings are independently open), but ARIA pattern handles it.

Pick single-open when sections are mutually exclusive in use. Pick multi-open when users may want to keep multiple sections open at once.

## Pattern: tabs

WAI-ARIA tablist pattern is well-documented. Brief structure:

```html
<div class="tabs">
  <div role="tablist" aria-label="Project sections">
    <button role="tab" aria-selected="true" aria-controls="overview-panel" id="overview-tab">
      Overview
    </button>
    <button role="tab" aria-selected="false" aria-controls="activity-panel" id="activity-tab">
      Activity
    </button>
  </div>
  <div role="tabpanel" id="overview-panel" aria-labelledby="overview-tab">
    ...overview content...
  </div>
  <div role="tabpanel" id="activity-panel" aria-labelledby="activity-tab" hidden>
    ...activity content...
  </div>
</div>
```

**Keyboard interactions** (per ARIA):
- `Tab` moves into the tablist; once focused, arrow keys move between tabs.
- `Enter` / `Space` activates the focused tab.
- `Home` / `End` go to first / last tab.

**Activation modes:**
- **Automatic** — focusing a tab activates it immediately. Good for short-load tabs; bad for tabs that fetch data on activation.
- **Manual** — focusing a tab moves focus but doesn't activate; user presses Enter to activate. Good for slow-load tabs.

## Pattern: side sheet / drawer

A panel that slides in from a screen edge. Implementation typically uses `<dialog>` with custom positioning, or a custom `<aside>` with focus management.

```html
<dialog id="invoice-edit" class="sheet">
  <header>
    <h2>Edit invoice</h2>
    <button aria-label="Close">×</button>
  </header>
  <form>...</form>
  <footer>
    <button>Cancel</button>
    <button class="primary">Save</button>
  </footer>
</dialog>

<style>
  dialog.sheet[open] {
    position: fixed;
    top: 0; right: 0; bottom: 0;
    width: min(480px, 100vw);
    margin: 0;
    border: 0;
    border-left: 1px solid hsl(0 0% 88%);
    transition: transform 200ms ease-out;
  }
</style>
```

**Behaviors required:**
- Focus moves into the sheet on open.
- Focus is trapped inside while open.
- Focus returns to the trigger when closed.
- `Esc` closes.
- Click outside (on the backdrop) closes (typically).

`<dialog>` with `.showModal()` provides focus trap and Esc handling natively. Use it.

## Pattern: modal (true modal blocking interaction)

```html
<dialog id="confirm">
  <h2>Discard changes?</h2>
  <p>Your unsaved edits will be lost.</p>
  <form method="dialog">
    <button value="cancel">Cancel</button>
    <button value="confirm" class="destructive">Discard</button>
  </form>
</dialog>

<script>
  const dialog = document.getElementById('confirm');
  document.querySelector('[data-trigger="confirm"]').addEventListener('click', () => {
    dialog.showModal();
  });
  dialog.addEventListener('close', () => {
    if (dialog.returnValue === 'confirm') {
      // do destructive thing
    }
  });
</script>
```

The `<dialog>` element with `showModal()` provides:
- Modal blocking (background is inert).
- Focus trap.
- Esc to close.
- Backdrop styling via `::backdrop`.

Older browsers may need a polyfill; modern evergreen browsers support it directly.

## Pattern: tooltip

Tooltips reveal supplementary information on hover/focus. Several pitfalls:

- **Hover-only fails for touch and keyboard.** Always include focus trigger.
- **`title` attribute** is the most accessible but limited (no styling, slow show timing on most browsers).
- **Custom tooltips** require `aria-describedby` referencing the tooltip element.

```html
<button aria-describedby="trial-tooltip">
  Start free trial
</button>
<div id="trial-tooltip" role="tooltip" hidden>
  14 days, no credit card required.
</div>

<script>
  // Show tooltip on hover or focus; hide on blur or mouseleave.
</script>
```

**WAI-ARIA tooltip pattern requirements:**
- Tooltip appears on hover or focus.
- Tooltip dismisses on blur, mouseleave, or Esc.
- Tooltip content is referenced via `aria-describedby` on the trigger.
- Tooltip cannot contain interactive content (use a popover for that).

## Pattern: popover

Like a tooltip but can contain interactive content (buttons, links, form fields). Used for menus, comboboxes, contextual actions.

The browser-native `popover` attribute (released in 2023+) handles this:

```html
<button popovertarget="my-popover">Open menu</button>
<div id="my-popover" popover>
  <ul>
    <li><button>Option 1</button></li>
    <li><button>Option 2</button></li>
  </ul>
</div>
```

Native popover handles open/close, light-dismiss (click outside or Esc), and focus.

For older browsers or richer behavior, libraries like Floating UI handle positioning math.

## Motion design

Disclosure motion should:

- **Be brief.** 150–250ms is typical; longer feels slow.
- **Use ease-out timing** for opening (decelerates as it lands).
- **Respect `prefers-reduced-motion`.** Disable or shorten motion when the user has set this preference.

```css
@media (prefers-reduced-motion: reduce) {
  details, dialog, .accordion-content {
    transition: none;
  }
}
```

Motion serves comprehension: it shows the user *where* the new content came from. Slamming open with no transition feels jarring; long animations test patience.

## Heuristics

1. **The lightest-viable rule.** Pick the lightest disclosure affordance that does the job.
2. **The library check.** Are you using a well-tested component library, or did someone hand-roll this? Hand-rolled disclosures are nearly always missing some accessibility detail.
3. **The keyboard-only walk.** Open every disclosure on the page using only the keyboard. Anything you can't reach is broken.
4. **The screen-reader audit.** With NVDA / VoiceOver / TalkBack, walk through. Are expand/collapse states announced? Are tabs announced as "tab, X of Y"?

## Resources

- **WAI-ARIA Authoring Practices Guide** — w3.org/WAI/ARIA/apg. Canonical patterns for accordion, dialog, tablist, tooltip.
- **MDN: `<details>`, `<dialog>`, popover** — current browser support.
- **Inclusive Components** by Heydon Pickering — accessible patterns for disclosures, accordions, modals.
