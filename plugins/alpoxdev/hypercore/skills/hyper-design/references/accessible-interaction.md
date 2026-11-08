# Accessible Interaction

Read when a write mode builds or edits controls, forms, dialogs, tabs, or dynamic content, and when an audit finding concerns a control's role, name, state, or keyboard use. Each entry is Tell, Why, Fix; the code is a starting shape to adapt to the project's stack, not a library to paste.

## Contents

- 1. Affordances
- 2. Keyboard and focus
- 3. Forms and errors
- 4. Dynamic content
- 5. Whole documents
- 6. Code shapes

## 1. Affordances

| Tell | Why | Fix |
|---|---|---|
| A button, `summary`, checkbox label, or `[role="button"]` keeps the arrow cursor (often after a CSS reset sets `button { cursor: default }`) | The arrow says "this is text"; people hesitate or never click | One base rule after the reset gives every enabled control `cursor: pointer` and disabled controls `cursor: not-allowed` (§6.1); never on something that does nothing |
| `<div onClick>`, `<span onClick>`, `<a>` without `href`, or `<a href="#" onClick>` used for an action | No role, so screen readers do not announce a control and the keyboard skips it | Actions are `<button type="button">`; navigation is `<a href>` to a real destination; a custom control that cannot be native gets a role, its state attributes, and full keyboard support |
| An icon-only close, menu, search, or social button with no text | A screen reader says "button" and nothing else; voice control cannot name it | An `aria-label` or visually hidden text matching the visible meaning; the icon gets `aria-hidden="true"` |
| A control looks the same at rest, on hover, pressed, and disabled; a grayed-out button still fires | No feedback that the action registered; a disabled control looks broken | Distinct `:hover`, `:active`, `:focus-visible`, and disabled styles held to 3:1; prefer the `disabled` attribute, or `aria-disabled="true"` plus a code-level block when it must stay focusable |
| Status shown by color alone: a red border, a green chip | Excludes color-blind users and vanishes in forced-colors mode | Pair every color signal with text or an icon; error text first |
| Drag is the only way to reorder, resize, or pick a value | Fails people who cannot drag (WCAG 2.5.7) | Offer a click, tap, or keyboard path: move-up and move-down buttons, a number input beside a slider |

## 2. Keyboard and Focus

| Tell | Why | Fix |
|---|---|---|
| `outline: none` with no replacement | Keyboard users lose their place | A `:focus-visible` style with 3:1 against neighbors, in every theme |
| Menus open on hover only; a dropdown opens by click but not by keyboard | The control does not exist for keyboard and touch users | Every interactive element works with Tab, Shift+Tab, Enter, and Space; dialogs close with Escape |
| Focus jumps around because DOM order differs from visual order | Navigation is unpredictable | Keep source order equal to visual order; add a skip link on long pages (§6.2); give real content `tabindex="-1"` only inside a controlled focus target |
| A custom modal lets Tab escape behind it | Keyboard users end up in the hidden page | Prefer the native `<dialog>` with `showModal()`, which traps focus and closes on Escape; return focus to the opener on close |
| Tabs built from plain buttons with no roles | Screen readers cannot tell which panel is shown | `role="tablist"`, `role="tab"` with `aria-selected` and `aria-controls`, `role="tabpanel"`; arrow keys move between tabs, the active tab has `tabindex="0"`, the others `-1` |

## 3. Forms and Errors

- Every field has a visible `<label for>` (or a wrapping label); a placeholder is a hint, never the label. Use `autocomplete` tokens for personal data.
- Instructions that apply before typing sit above or beside the field and are tied with `aria-describedby`.
- Validate on submit or on leaving a field the user has changed, never on focus. Mark the field `aria-invalid="true"`, show the message next to it, keep the input, and say how to fix it in plain words.
- A form with several fields shows an error summary at the top on submit, moves focus to it, and links each line to its field; the wording matches the inline messages.
- On a phone, the focused field scrolls into view above the on-screen keyboard; leave enough bottom padding that the keyboard never covers it.

## 4. Dynamic Content

- Content that changes without a page load (a saved toast, a result count, an upload finished) is announced through a live region that exists before the change: `aria-live="polite"` for status, `role="alert"` only for urgent errors.
- Clear a live region, then write the new text on the next frame, so the same message repeated is announced again.
- Loading text says what is loading ("Loading invoices"), not only a spinner.

## 5. Whole Documents

Apply only when the task produces a full page or an app shell, never to a single component:

- `<html lang>` set to the content language, a unique `<title>`, and landmarks: `header`, `nav`, `main`, `footer`.
- One `h1` and no skipped heading levels.
- The viewport meta never blocks zoom.

## 6. Code Shapes

### 6.1 Pointer cursor base layer

```css
@layer base {
  :where(a[href], button, summary, select, label[for],
         input:is([type="checkbox"], [type="radio"], [type="file"], [type="range"],
                  [type="color"], [type="submit"], [type="button"], [type="reset"]),
         [role="button"], [role="link"], [role="tab"], [role="switch"],
         [role="menuitem"], [role="option"]) {
    cursor: pointer;
  }
  :where(label:has(> input:is([type="checkbox"], [type="radio"]))) { cursor: pointer; }
  :where(:disabled, [aria-disabled="true"]) { cursor: not-allowed; }
}
```

Text inputs keep `cursor: text`; drag handles use `grab` and `grabbing`. In Tailwind, place this after the preflight layer.

### 6.2 Skip link

```html
<a class="skip-link" href="#main">Skip to content</a>
<main id="main" tabindex="-1">…</main>
```

```css
.skip-link { position: absolute; inset-inline-start: 0.5rem; translate: 0 -200%; }
.skip-link:focus-visible { translate: 0 0.5rem; }
```

### 6.3 Native dialog

```html
<button type="button" aria-haspopup="dialog" aria-controls="rename">Rename</button>
<dialog id="rename" aria-labelledby="rename-title">
  <h2 id="rename-title">Rename project</h2>
  <form method="dialog">
    <label for="rename-name">Name</label>
    <input id="rename-name" name="name" required>
    <button value="cancel" formnovalidate>Cancel</button>
    <button value="save">Save</button>
  </form>
</dialog>
```

Open it with `dialog.showModal()`, which traps focus and closes on Escape; move focus back to the opener in the `close` event.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| The affordance entries (pointer cursor base layer, native elements, accessible names, distinct states, color-only feedback, page semantics only for whole documents) and the pattern list (focus trap, skip link, error handling, labels, dragging alternatives, tabs, live regions) | <https://github.com/miqdadbadjuber/anti-slop> (commit `9504989`, `antislop-human/SKILL.md` and its `references/A11Y-PATTERNS.md`; MIT, Copyright 2026 Miqdad Badjuber; the patterns file is adapted from <https://github.com/addyosmani/web-quality-skills>, MIT, Copyright 2026 Addy Osmani). The code in §6 was written for this package, not copied. |
| Name, role, value; keyboard operability; focus visible; dragging movements; status messages | <https://www.w3.org/TR/2024/REC-WCAG22-20241212/> (SC 4.1.2, 2.1.1, 2.4.7, 2.5.7, 4.1.3) |
| The native `dialog` element traps focus in `showModal()` and closes on Escape | <https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/dialog> |

### Evidence grade

The WCAG criteria are normative. The pointer cursor rule is a widely used convention, not a WCAG requirement, and is held as a default.
