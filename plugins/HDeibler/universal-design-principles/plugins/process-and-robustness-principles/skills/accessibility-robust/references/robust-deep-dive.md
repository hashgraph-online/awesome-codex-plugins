# Robust: standards and edge cases

A reference complementing `accessibility-robust` SKILL.md with deeper detail on the WCAG 4.* criteria and ARIA practice.

## WCAG 4.* criteria summary

The Robust principle has one guideline (4.1) with three success criteria (one of which was deprecated in 2.2).

### 4.1 Compatible

- **4.1.1 Parsing (A)** — *deprecated in WCAG 2.2.* Originally required valid HTML; modern browsers handle invalid HTML well enough that this criterion was removed.
- **4.1.2 Name, Role, Value (A)** — every UI component has programmatically determinable name, role, and value (states/properties).
- **4.1.3 Status Messages (AA)** — programmatically conveyed status messages without focus shifts.

The framework here is the smallest of WCAG's four principles by criterion count, but it underlies most of the other principles' implementation: if your markup isn't robust, no amount of careful labeling rescues it.

## The ARIA hierarchy

ARIA (Accessible Rich Internet Applications) is a specification for adding semantic information to non-semantic markup. The relationship to native HTML:

1. **Use a native HTML element if one fits.** `<button>`, `<a>`, `<input>`, `<nav>`, `<form>`, `<label>`, `<dialog>`, etc.
2. **Use a native element with ARIA enhancement** when you need state native HTML doesn't express. `<button aria-pressed>`, `<a aria-current="page">`.
3. **Build with ARIA on `<div>` / `<span>`** only when no native element fits. Custom comboboxes, tablists, treegrids, sliders.

The first rule of ARIA: don't use ARIA. The second rule: use it when needed but use it correctly.

## ARIA patterns from WAI-ARIA Authoring Practices

The W3C's WAI-ARIA Authoring Practices Guide documents the canonical implementation of common interactive components. Patterns include:

- Accordion
- Alert / Alertdialog
- Breadcrumb
- Button
- Carousel
- Checkbox (custom)
- Combobox
- Dialog (modal)
- Disclosure
- Feed
- Grid
- Landmark regions
- Link
- Listbox
- Menu / Menubar
- Meter
- Radiogroup
- Slider
- Spinbutton
- Switch
- Tabs
- Toolbar
- Tooltip
- Tree / Treegrid

Each pattern documents required ARIA roles, properties, states, keyboard interactions, and focus management. When building a custom component, find the matching pattern first; build to spec.

## Live regions in depth

`aria-live` regions notify assistive tech of dynamic content changes. Three priority levels:

- `aria-live="off"` (default) — no announcement.
- `aria-live="polite"` — announce when convenient (after current speech). Use for non-urgent updates: search results count, save confirmations.
- `aria-live="assertive"` — interrupt and announce. Use sparingly, for genuinely urgent updates: critical errors, connection lost.

Convenience roles with implicit `aria-live`:

- `role="status"` ≈ `aria-live="polite"`.
- `role="alert"` ≈ `aria-live="assertive"` plus `aria-atomic="true"`.
- `role="log"` for chat-like sequential additions.
- `role="timer"` for countdowns.
- `role="progressbar"` for progress indicators.

### Live region pitfalls

- **The region must exist in the DOM at page load** for reliable announcement. Adding a live region just before populating it often misses the announcement.
- **Each announcement should replace previous content**, not append (unless using `role="log"`).
- **Don't announce every small change.** Aggregate updates; announce only when meaningful.
- **Test on multiple screen readers.** Announcement behavior varies (NVDA, VoiceOver, JAWS, TalkBack).

## Common semantic mistakes

### `<div>` for everything

A UI built without semantic elements is opaque to assistive tech and requires comprehensive ARIA to recover. The fix is structural: refactor to `<button>`, `<a>`, `<nav>`, `<main>`, `<form>`, `<label>`, `<table>` etc.

### Conflicting ARIA roles

Applying ARIA roles that contradict the underlying element:

- `<a href="..." role="button">` — `<a>` is already a link; `role="button"` conflicts.
- `<table role="presentation">` for actual tabular data — strips the semantics that make the table navigable.

### `aria-label` overriding visible text

```html
<button aria-label="Submit">Save</button>
```

The accessible name is "Submit"; the visible text is "Save." Voice-control users say "click Save" and it doesn't work. Always: visible text matches accessible name.

### Missing labels on form controls

Every `<input>`, `<select>`, `<textarea>` needs a programmatically associated `<label>`. `aria-label` is acceptable; `aria-labelledby` referencing visible text is also acceptable. Placeholder-only is not acceptable.

### Duplicate IDs

`aria-labelledby` and `aria-describedby` rely on `id` attribute uniqueness. Duplicate IDs (common with reusable components) break these associations silently.

## Testing for robustness

### Inspect the accessibility tree

Browser DevTools (Chrome, Firefox, Safari) all expose the accessibility tree — the structured representation that assistive tech sees. Key checks:

- Does each interactive element have a non-empty `Name`?
- Does each interactive element have a meaningful `Role`?
- Does each stateful element have correct `State` (checked, expanded, pressed, etc.)?

If "name: empty" or "role: generic" appears on an interactive element, the component is invisible to assistive tech.

### Run a screen reader

Test critical flows with VoiceOver (macOS/iOS), NVDA (Windows, free), or TalkBack (Android). Listen for:

- Unlabeled buttons / inputs.
- Components that don't announce their role.
- State changes that aren't announced.
- Garbled reading order.

### Validate HTML

W3C HTML Validator (validator.w3.org) catches:

- Duplicate IDs.
- Nested interactive elements.
- Invalid attribute values.
- Form controls without labels.

These often correlate with accessibility issues.

## Resources

- **WAI-ARIA Authoring Practices Guide** — w3.org/WAI/ARIA/apg.
- **ARIA in HTML spec** — w3.org/TR/html-aria.
- **MDN ARIA reference** — developer.mozilla.org/Web/Accessibility/ARIA.
- **A11y Project** — a11yproject.com.
- **Inclusive Components** (Heydon Pickering) — inclusive-components.design.

## Closing

Robust accessibility is invisible when it works (assistive tech "just works") and devastating when it fails (the component is unusable). Lean on semantic HTML and well-tested component libraries; reach for raw ARIA only when you must.
