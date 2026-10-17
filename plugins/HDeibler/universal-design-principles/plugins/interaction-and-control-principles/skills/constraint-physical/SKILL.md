---
name: constraint-physical
description: 'Use this skill when designing structural constraints that prevent invalid actions through the shape, layout, or behavior of the design itself — paths (channels of motion), axes (rotary controls), barriers (blocks). Trigger when designing input controls, drag-and-drop affordances, modal dialogs, or hardware-style structural prevention. Sub-aspect of `constraint`; read that first.'
---

# Physical constraints

Physical constraints prevent invalid actions through the structure of the design — the shape of a connector, the boundary of a screen, the channel of a slider. The user *can't* take the wrong action because the structure rejects it. Stronger than psychological constraints; not always available.

## The three subtypes (from the book)

### Paths

Channels that direct motion. The user can move along the path; off-path movement is impossible or rejected.

Software examples:

- **Sliders** constrain motion to one dimension.
- **Range inputs** constrain values to a defined min/max.
- **Scroll bars** constrain scrolling direction.
- **Dropdown lists** constrain selection to provided options.

```html
<!-- Path constraint: value must be 0-100 -->
<input type="range" min="0" max="100" value="50" />

<!-- Path constraint: choice from fixed set -->
<select>
  <option>Small</option>
  <option>Medium</option>
  <option>Large</option>
</select>
```

### Axes

Rotary controls. Convert applied force into rotation; effectively infinite range in a small space.

Software examples:

- **Rotation gestures** in canvas tools.
- **Color-wheel pickers** that constrain hue selection to a circular path.
- **Dial-style controls** for continuous values.

### Barriers

Block, slow, or redirect motion.

Software examples:

- **Modal dialogs** block interaction with content beneath.
- **Disabled buttons** block their action.
- **Permission gates** block access to features.
- **Screen edges** stop cursor motion (Fitts's edge advantage).
- **Form-validation blocks** prevent submission when invalid.

## Patterns

### Input-type constraints (paths)

```html
<input type="email" />     <!-- only accepts email format -->
<input type="number" min="0" />   <!-- only non-negative numbers -->
<input type="date" />      <!-- only valid dates -->
<input type="color" />     <!-- only valid hex colors -->
```

The browser enforces the constraint; the user can't submit invalid data.

### Drop-zone constraints (barriers)

A drag-and-drop interaction can constrain valid drops at the API level:

```js
dropZone.addEventListener('dragover', e => {
  if (isValidTarget(draggedItem, dropZone)) {
    e.preventDefault();  // allow drop
  }
  // not preventing default = drop won't fire
});
```

The browser's drag-and-drop API itself uses constraint: `preventDefault` opens the channel; absence keeps it blocked.

### Modal as barrier

```html
<dialog open>
  <h2>Required action</h2>
  <p>You must complete this step before continuing.</p>
  <button onclick="proceed()">Continue</button>
</dialog>
```

The dialog blocks interaction with the page beneath. Use sparingly; barriers irritate when they don't serve a clear purpose.

### Disabled state (block)

```html
<button id="submit" disabled>Submit</button>
```

The button can't trigger its action until enabled. Pair with explanation of what would enable it.

## When to use physical over psychological

- **When the consequence of the wrong action is severe** (data loss, security breach, irreversible operation). Physical constraints are stronger.
- **When the user is novice** or the system is unfamiliar — psychological constraints rely on prior knowledge that may not exist.
- **When there's no acceptable failure mode** — make the wrong action impossible.

## When physical constraints over-restrict

- **Format constraints stricter than necessary** — phone fields that reject parentheses; name fields that reject apostrophes.
- **Hardware-style barriers in software contexts** — a modal that blocks because of a non-blocking concern.
- **Disabled states that don't explain themselves** — user can't act and doesn't know why.

The discipline: constrain real requirements; explain when surprises occur.

## Resources

- **Norman, D.** *The Design of Everyday Things* (1988, 2013).
- **Lidwell, Holden & Butler** (2003).
- **WCAG** — input-type and validation constraints contribute to accessibility.

## Related sub-skills

- **`constraint`** (parent).
- **`constraint-psychological`** — the other half; symbols, conventions, mappings.
- **`affordance`** — affordance + constraint = the action space.
- **`accessibility-operable`** — physical constraints must be operable across assistive technologies.
