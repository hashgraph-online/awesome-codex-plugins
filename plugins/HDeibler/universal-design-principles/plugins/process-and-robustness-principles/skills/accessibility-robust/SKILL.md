---
name: accessibility-robust
description: 'Use this skill when the question is whether assistive technologies — screen readers, voice control, switch devices, refreshable braille displays — can reliably interpret your UI. Trigger when picking between semantic HTML and a custom-built component, when reaching for ARIA, when designing live regions for dynamic content (toasts, validation, search results), or when reviewing a UI built largely from `<div>` elements. Covers WCAG Principle 4 (Robust). Sub-aspect of `accessibility`; read that first if you haven''t already.'
---

# Accessibility — Robust

WCAG Principle 4: content must be robust enough to be interpreted reliably by a wide variety of user agents, including assistive technologies.

The two sub-criteria, simplified:

1. **Compatible** — markup is parsed correctly; name, role, and value are programmatically determinable for every UI component.
2. **Status messages** — programmatically-conveyed status updates without focus shifts.

Robustness is the layer most often broken by frameworks that abstract away HTML semantics. A `<div>`-based UI may be visually identical to a semantic one and entirely opaque to assistive tech.

## 1. Compatible

### Semantic HTML first

Use the right HTML element for the job. Browsers and assistive tech understand semantic elements without further annotation.

| Use this… | …not this |
|---|---|
| `<button>` | `<div>` with click handler |
| `<a href>` | `<span>` with click handler |
| `<input type="checkbox">` | `<div>` with custom toggle |
| `<nav>` | `<div class="nav">` |
| `<main>` | `<div class="main">` |
| `<form>` | `<div>` with submit button |
| `<label for="id">` | `<div>` next to an input |
| `<table>` for tabular data | nested divs styled as a grid |

The reason isn't aesthetic; semantic elements come with built-in:

- Keyboard handling (`<button>` activates on Enter/Space).
- Focus management (`<a href>` is in tab order).
- Accessibility tree role (`<nav>` is announced as "navigation landmark").
- Default styling that can be overridden but indicates affordance.
- Form submission, validation, and serialization.

A `<div role="button" tabindex="0" onclick onKeyDown>` is *almost* a button — and you've rebuilt 80% of what `<button>` provides for free, often imperfectly.

### Name, Role, Value

Every interactive component must have:

- **Name** — what is it? ("Save," "Email field," "Open menu")
- **Role** — what kind of thing is it? ("button," "textbox," "menu")
- **Value** — what's its current state? ("checked," "expanded," "disabled," current text)

Native HTML elements provide all three for free. For custom components, you provide them via ARIA.

```html
<!-- Native: name from text, role from <button>, value from disabled state -->
<button disabled>Save</button>

<!-- Custom: must declare all three -->
<div role="button"
     tabindex="0"
     aria-disabled="true">
  Save
</div>
```

### When to use ARIA

The first rule of ARIA: don't use ARIA. The second rule: don't use ARIA when a native element will do. The third rule: when you must use ARIA, use it correctly.

**Use ARIA when:**

- Building a custom component for which no native element exists (combobox, tablist, treegrid, slider) — use the appropriate WAI-ARIA pattern.
- Adding state to a component that has no native attribute (`aria-expanded`, `aria-current`, `aria-pressed`, `aria-selected`).
- Providing an accessible name when no visible label exists (`aria-label`, `aria-labelledby`).
- Associating descriptions or errors with controls (`aria-describedby`).
- Marking dynamic content for announcement (`aria-live`).

**Don't use ARIA to:**

- Reinvent native semantics (`role="button"` on `<button>`).
- Override semantics that work (`role="presentation"` on a `<table>` of tabular data).
- "Fix" inaccessible custom components without also adding keyboard support and state management.

### ARIA roles, properties, states

A few of the most-used:

| Attribute | Purpose | Example |
|---|---|---|
| `role` | Declare what kind of widget | `role="dialog"` |
| `aria-label` | Accessible name when no visible label | `<button aria-label="Close">×</button>` |
| `aria-labelledby` | Accessible name from another element | `<dialog aria-labelledby="title">` |
| `aria-describedby` | Description / error / hint | `<input aria-describedby="hint">` |
| `aria-expanded` | Disclosure state | `<button aria-expanded="false">` |
| `aria-current` | Current item in a set | `<a aria-current="page">` |
| `aria-pressed` | Toggle button state | `<button aria-pressed="true">` |
| `aria-checked` | Custom checkbox/radio state | `<div role="checkbox" aria-checked="true">` |
| `aria-selected` | Selected item in a listbox | `<div role="option" aria-selected="true">` |
| `aria-disabled` | Disabled (when `disabled` attr unavailable) | `<div aria-disabled="true">` |
| `aria-invalid` | Error state | `<input aria-invalid="true">` |
| `aria-required` | Required field | `<input aria-required="true">` |
| `aria-hidden` | Hide from accessibility tree | `<svg aria-hidden="true">` |
| `aria-live` | Announce changes | `<div aria-live="polite">` |
| `role="alert"` | Important announcement | `<div role="alert">` |

The WAI-ARIA Authoring Practices Guide documents complete patterns for: combobox, dialog, disclosure, feed, grid, listbox, menu, menubar, radiogroup, slider, tablist, treeview, and more. Reach for these patterns rather than inventing.

### Don't break native semantics

A common mistake: applying ARIA roles that *conflict* with the underlying element.

```html
<!-- Wrong: <a href> is already a link; role="button" overrides -->
<a href="/save" role="button">Save</a>

<!-- Wrong: <ul> already has list semantics; role="navigation" doesn't help -->
<ul role="navigation">...</ul>

<!-- Wrong: <table> for tabular data with role="presentation" strips semantics -->
<table role="presentation">...</table>
```

If you must override semantics (rare), you almost always have the wrong base element.

### Validate your HTML

Invalid HTML can cascade in unpredictable ways through accessibility tree construction. Validate occasionally with the W3C HTML Validator.

Common offenders:

- Duplicate IDs (breaks `aria-labelledby` and `aria-describedby`).
- Nested interactive elements (`<button>` inside `<a>`, `<a>` inside `<button>`).
- `<button>` inside `<button>`.
- Form controls not associated with `<label>`.

## 2. Status messages

Dynamic content updates that don't shift focus need to be announced to screen readers via live regions.

### Live regions

```html
<!-- Polite: announce when convenient (after current speech) -->
<div aria-live="polite" id="search-results-status"></div>

<!-- Assertive: interrupt; for critical messages only -->
<div aria-live="assertive" id="error-status"></div>
```

When you populate the live region, the screen reader reads the new content. The region must:

- Be present in the DOM *before* content is added (live regions don't announce content present at page load).
- Have only the new message inside it, replacing previous content.
- Be visible to assistive tech (don't `display: none`; use `sr-only` if you don't want it visible).

### `role="status"` and `role="alert"`

Convenience roles with built-in `aria-live` settings:

- `role="status"` ≈ `aria-live="polite"`. For non-critical updates ("Saved," "Loaded 24 results").
- `role="alert"` ≈ `aria-live="assertive"` plus `aria-atomic="true"`. For urgent updates ("Connection lost," "Form has 3 errors").

```html
<!-- Toast notification (status) -->
<div role="status">Changes saved</div>

<!-- Form error summary (alert) -->
<div role="alert">
  Please fix the following: Email is invalid; Password is too short.
</div>
```

Use `role="alert"` sparingly — it interrupts whatever the screen reader is doing. Reserve for genuine emergencies.

### Common live-region patterns

- **Toast notifications** — `role="status"` for success, info, warning; `role="alert"` for error.
- **Search results count** — `<div role="status">Showing 24 results</div>` updates as the user filters.
- **Form validation summary** — after a failed submit, populate `<div role="alert">` with the error count and let screen reader read it.
- **Auto-saving indicator** — `<div role="status">Saving... Saved at 3:42 PM</div>` updates during background saves.
- **Real-time data updates** — chat messages, stock prices: `aria-live="polite"` so the user hears them when convenient.

### Don't overdo announcements

Every announcement steals attention. Frequent live-region updates make the UI noisy for screen reader users. Rules of thumb:

- Don't announce hover state changes.
- Don't announce loading spinners (unless the load is unusually long).
- Don't announce purely cosmetic transitions.
- Aggregate where possible: instead of "Filter applied," "24 results loaded," "Filter applied," "12 results loaded" with each filter change, debounce and announce only the final state.

### `aria-atomic` and `aria-relevant`

Fine-tuning live region behavior:

- `aria-atomic="true"` — read the entire region content when any part changes (default for `role="alert"`; useful for counts that should always be read in context: "24 results" changing to "12 results").
- `aria-relevant` — control which mutation types announce (default is `additions text`). Rarely needed.

## Worked examples

### Example 1: a custom slider built right

```html
<label id="volume-label">Volume: <span id="volume-value">50</span>%</label>
<div role="slider"
     aria-labelledby="volume-label"
     aria-valuemin="0"
     aria-valuemax="100"
     aria-valuenow="50"
     tabindex="0"
     id="volume-slider"
     class="slider-track">
  <div class="slider-thumb" style="left: 50%;"></div>
</div>
```

Plus JavaScript:

- `ArrowLeft`/`ArrowRight` and `Home`/`End` adjust value.
- On adjustment, update `aria-valuenow` *and* the visible text (`#volume-value`).

The native `<input type="range">` does all of this automatically — strongly prefer that. Custom sliders are justified only when range can't meet your needs (multi-handle range, custom geometry, color picker).

### Example 2: a search results announcement

```html
<form>
  <label for="search">Search</label>
  <input id="search" oninput="runSearch(this.value)" />
</form>

<div id="results">…rendered results…</div>
<div id="results-status" class="sr-only" role="status"></div>

<script>
  function runSearch(q) {
    const results = doSearch(q);
    renderResults(results);
    document.getElementById('results-status').textContent =
      `${results.length} results for "${q}"`;
  }
</script>
```

Sighted users see results below the input; screen reader users hear "24 results for 'invoice'" without focus moving.

### Example 3: a toast that announces

```html
<div id="toast-region" aria-live="polite" aria-atomic="true" class="sr-only"></div>

<script>
  function showToast(message) {
    const region = document.getElementById('toast-region');
    region.textContent = message;
    showVisualToast(message); // separate visible UI
    setTimeout(() => region.textContent = '', 5000);
  }
</script>
```

The visible toast is rendered however your design library does it. The hidden live region is what assistive tech uses.

## Anti-patterns

- **`<div>` for everything.** A UI built without semantic elements is opaque to assistive tech and requires comprehensive ARIA to recover.
- **`role="button"` on a `<button>`.** Redundant; sometimes interferes with native behavior.
- **`aria-label` that contradicts visible text.** Voice control breaks; user says "click [visible text]" and nothing happens.
- **Live regions added at announcement time.** `<div aria-live="polite">` must be in the DOM at page load to be reliably observed; adding it dynamically often misses the announcement.
- **Aria-live on too much content.** Page-wide `aria-live` regions are constantly chattering. Scope to just the announcement element.
- **Custom dropdowns missing keyboard.** ARIA roles applied to a div but no `Tab`, `Esc`, or arrow-key handlers. The screen reader hears "menu" but the user can't operate it.
- **`role="presentation"` on tables of data.** Strips the semantics that make the table navigable. Reserve for genuinely-decorative table-shaped layouts.

## Heuristics

1. **The "is there a native element for this?" check.** Before reaching for ARIA, ask if HTML provides what you need. Almost always.
2. **The accessibility tree audit.** Chrome DevTools → Accessibility tab. Inspect any custom component. Does it have a name, role, and (where applicable) value? If "name: empty" or "role: generic," the component is invisible to assistive tech.
3. **The screen-reader walkthrough.** Open VoiceOver / NVDA / TalkBack and walk a critical flow. Listen for: unlabeled controls, components with no role, changes that aren't announced, "blank" or "press button to" without context.
4. **The HTML validator.** Run your most-complex pages through validator.w3.org. Duplicate IDs, nested interactive elements, and missing labels often surface here first.

## Related skills

- **`accessibility`** (parent).
- **`accessibility-perceivable`**, **`accessibility-operable`**, **`accessibility-understandable`** — siblings.
- **`feedback-loop`** (interaction) — live regions are accessibility's version of feedback.
- **`structural-forms`** (process) — semantic HTML is the structural-forms answer for accessibility.
- **`affordance`** (interaction) — semantic elements come with default affordances.
