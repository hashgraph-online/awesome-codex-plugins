---
name: affordance-signifiers
description: 'Use this skill when the design has interactive capability but users aren''t *seeing* it — when the affordance is technically present but the signifier (the visible cue that tells users "you can do this") is missing or weak. Trigger when reviewing flat-design UIs where everything looks the same, when designing custom controls, when stakeholders ask "should this be more obvious?", or when picking signifier strength for primary vs. secondary actions. Sub-aspect of `affordance`; read that first.'
---

# Signifiers: making affordance perceivable

In Norman's later refinement (2008), he distinguished *affordance* (the underlying possibility — a button can be pressed) from *signifier* (the visible cue that tells the user about the affordance — the button looks pressable). The distinction matters because designers control signifiers; affordances often exist regardless. A button that's missing a signifier still affords pressing — but no one knows.

## The signifier inventory

Every interactive element should carry one or more signifiers. The strongest are perceivable preattentively (within the first 200ms of viewing) without conscious thought.

### Strong signifiers

- **Filled background** with a brand or neutral color, distinct from the page background. Reads as "object."
- **Visible border** outlining the interactive region. Reads as "discrete element you can act on."
- **Drop shadow / elevation** suggesting the element floats above content.
- **Distinctive shape** (rounded rectangle for buttons, pill shape for chips, circle for FABs).
- **Underline** for links.

### Medium signifiers

- **Color difference from surrounding text** (the classic blue link).
- **Cursor change** on hover (`cursor: pointer`). Desktop only.
- **Hover state** (color shift, shadow change). Desktop only.
- **Focus ring** when keyboard-focused. Critical for keyboard users.
- **Iconography** (a pencil for edit, a trash for delete) for users who recognize the convention.

### Weak signifiers

- **Subtle color tint** (5% darker than background). Easy to miss.
- **Tiny chevron or arrow** at the edge. Easy to miss.
- **Implicit position** (e.g., "the bottom right of every card has the row actions"). Requires learning.

For new-user surfaces, lean on strong signifiers. For dense expert tools, medium signifiers are acceptable because users develop spatial memory.

## Signifier strength must match action stakes

A useful rule: signifier strength should match the action's importance and consequence.

```
Primary action (Submit, Buy, Continue)
  → Strongest signifier: filled background + brand color + cursor + hover

Secondary action (Cancel, Save Draft)
  → Medium signifier: outlined border + cursor + hover

Tertiary action (Help, More info)
  → Lighter signifier: text-only + color + underline on hover

Destructive action (Delete, Remove)
  → Different signifier: distinct color (red) + cursor + hover, often after a confirmation step
```

When the primary action has the same signifier as the tertiary, the user doesn't know which is most important. Signifier strength is a hierarchy decision.

## Hover, focus, and active state signifiers

Static signifiers tell the user "this is interactive." Response signifiers tell them "you've engaged it."

- **Hover** (mouse over): color shift, shadow lift, slight scale change.
- **Focus** (keyboard tab to): visible focus ring (`outline: 2px solid var(--ring); outline-offset: 2px`).
- **Active** (pressing/holding): darker color, slight inset shadow, no scale change.
- **Disabled**: lighter color, no hover/active response, `cursor: not-allowed`.

These should *layer*. A button with a strong static signifier should still respond to hover and focus.

```css
.btn {
  /* static signifier */
  background: hsl(220 90% 50%);
  color: white;
  padding: 8px 16px;
  border: 0;
  border-radius: 6px;
  cursor: pointer;
  transition: background 100ms;
}
.btn:hover { background: hsl(220 90% 45%); }
.btn:focus-visible {
  outline: 2px solid hsl(220 90% 50%);
  outline-offset: 2px;
}
.btn:active { background: hsl(220 90% 40%); }
.btn[disabled] {
  background: hsl(0 0% 92%);
  color: hsl(0 0% 50%);
  cursor: not-allowed;
}
```

Five distinct states; each communicates something different. Stripping any of them weakens the signifier system.

## Signifier patterns by component type

### Button

- Filled or outlined background.
- Distinct shape (typically rounded rectangle).
- Cursor pointer.
- Hover/focus/active states.
- Always pair with a verb label.

### Link

- Color (typically brand).
- Underline (always or on hover, depending on context).
- Cursor pointer.
- Distinct from surrounding body text.

### Input field

- Distinct background (usually different from surrounding page).
- Border (visible or visible on focus).
- Cursor text on hover.
- Focus ring or border-color change on focus.

### Toggle / switch

- Distinctive shape (pill with circular slider).
- Animated transition between states.
- Strong color difference between on and off.

### Drag handle

- Iconographic signifier (six dots, two-line "grip").
- `cursor: grab` on hover, `cursor: grabbing` on active.
- Often dimmed in still state, brighter on hover.

### Disclosure trigger (accordion, "More")

- Chevron or plus/minus icon.
- Animation on toggle.
- Cursor pointer.
- Often whole row is hover-responsive, not just the icon.

## Anti-patterns

- **Signifier-stripped flat design.** A "minimalist" button with no border, no background, no shadow. Identical to surrounding text except for slight color. Users miss it.
- **Hover-only signifier.** Element looks like content; only on hover does it reveal it's a button. Touch users see no signifier; keyboard users may not focus it; even mouse users may not hover.
- **Signifier mismatch with role.** A "tertiary" action (like a help link) given the strongest signifier — users press it expecting the primary action.
- **Inconsistent signifiers for the same role.** "Submit" buttons vary in style across pages. Each page is a re-learning.
- **Disabled controls without anti-affordance.** A disabled button that looks identical to enabled. Users tap; nothing happens; confusion.

## Heuristics

1. **The signifier audit.** For each interactive element on the page, list its signifiers. If the count is 0–1, signifier is too weak. 2+ stacked signifiers (background + cursor + hover) is the safer baseline.
2. **The role-vs-signifier check.** Does the visual emphasis of each element match its role importance? Primary action should have the strongest signifier; tertiary the weakest.
3. **The state coverage check.** For each interactive element, do you have static, hover, focus, active, and disabled signifiers? Missing focus = inaccessible to keyboard. Missing active = no press feedback.

## Related sub-skills

- **`affordance`** (parent).
- **`affordance-false-and-anti`** — the inverse problem: when signifiers suggest interactivity that isn't there.
- **`hierarchy`** (perception) — signifier strength is a hierarchy decision.
- **`accessibility-perceivable`** (process) — signifiers must be perceivable across abilities.
- **`feedback-loop`** — response signifiers (hover, focus, active) are micro-feedback.
