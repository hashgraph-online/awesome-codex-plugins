# Disabled state and false affordance: pattern reference

A reference complementing `affordance-false-and-anti` with deeper detail on disabled-state patterns and false-affordance audits.

## Disabled state patterns

The "disabled button" is one of the most contentious UX patterns. Three schools of thought:

### School 1: always disable invalid actions

Default in many UI libraries. The button is grayed out and inert until preconditions are met (e.g., form complete and valid).

**Pros:** unambiguous; user can't trigger an action that would fail.

**Cons:** silent unless paired with explanation. Users hunt for what's wrong. Particularly bad on long forms — the user can't tell which field is incomplete without scrolling and looking.

### School 2: keep enabled, validate on submit

The button stays enabled. Clicking triggers validation; errors appear inline with explanations.

**Pros:** explicit feedback. The user sees specifically what's wrong.

**Cons:** user expectation of "click works" is briefly violated. Some users assume the click failed silently; mitigations (loading state, scroll-to-error, focus-on-error) help.

### School 3: enable + inline status

Button stays enabled, but a status message nearby ("3 fields need attention") tells the user what's stopping them. Clicking still triggers full validation.

**Pros:** best of both worlds — no silent block, clear status, no hunting.

**Cons:** more design surface to maintain.

The right choice depends on form complexity and stakes. For short forms, School 1 with inline hints is fine. For long forms, School 2 or 3 wins because the user shouldn't have to memorize what's wrong while scrolling.

## Disabled state must be perceivable

Whichever school you pick, disabled controls need:

- **Visual demotion** — lower opacity, neutral background, reduced contrast.
- **`cursor: not-allowed`** — the universal "no" signal on hover.
- **`disabled` attribute** in HTML — semantically correct, prevents click events.
- **`aria-disabled="true"`** — for assistive tech, especially in custom components where native `disabled` doesn't apply.
- **No hover state response** — the button shouldn't shift on hover when disabled (that's a false signifier).

```css
.btn[disabled],
.btn[aria-disabled="true"] {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none; /* prevent click; or handle via JS */
}
```

## Read-only field treatment

A read-only field is anti-affordance for editability with retained affordance for selection (the user can still copy the value).

```css
input[readonly],
textarea[readonly] {
  background: hsl(0 0% 96%);
  border-color: hsl(0 0% 90%);
  color: hsl(0 0% 30%);
  cursor: text; /* still selectable */
}
input[readonly]:focus { outline: 0; box-shadow: none; }
```

Notes:

- Unlike `disabled`, `readonly` fields *are* in the form submission and *are* focusable.
- `cursor: text` (not `not-allowed`) because users can select and copy.
- Removing the focus outline avoids the false signifier of "you can edit this now."

## False-affordance audit checklist

```
[ ] Are any non-interactive elements styled as buttons (filled, bordered, raised)?
[ ] Are any non-interactive elements styled with hover responses?
[ ] Is any non-link text underlined?
[ ] Are any "decorative" icons sitting in positions where users expect buttons?
[ ] Are any animated elements drawing attention to non-interactive content?
[ ] Are any cards styled to look clickable but actually inert?
[ ] Are any read-only fields styled identically to editable?
```

Each "yes" is a candidate for false-affordance fix.

## Resources

- **Norman, D.** *Design of Everyday Things* — chapter on visibility and affordance.
- **NN/g** — articles on form field disabled states and validation patterns.
- **WCAG 4.1.2 Name, Role, Value** — disabled state must be programmatically conveyed.
