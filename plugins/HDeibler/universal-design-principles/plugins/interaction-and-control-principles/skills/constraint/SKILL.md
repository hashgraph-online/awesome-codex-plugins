---
name: constraint
description: 'Use this skill whenever the design must structurally prevent invalid actions — input validation, disabled states, required fields, type-restricted inputs, mode locks, role-based gates, hardware lockouts. Trigger when designing forms, picking input types, designing destructive flows, gating multi-step procedures, or thinking about how to prevent a class of errors from being possible at all. Constraint is one of the foundational principles in ''Universal Principles of Design'' (Lidwell, Holden, Butler 2003) and one of the strongest design moves available — preventing wrong actions is more powerful than detecting them after the fact.'
---

# Constraint

A constraint is anything that limits the actions a user can perform on a system. Some constraints are physical (you can't insert a USB-C connector upside-down because the shape rejects it). Some are psychological (you don't try to push a door labeled "PULL" because the convention overrides the impulse). Both kinds work upstream of error: instead of catching wrong actions after they happen, constraints make wrong actions hard or impossible.

## Definition (in our own words)

A constraint is a deliberate limitation on what the user can do. The limitation may be implemented in the physical structure of the design (a slot that only accepts one shape), in the system's software (a button disabled until preconditions are met), or in the user's psychology (a convention that makes the wrong action feel obviously wrong). All three reduce error rates dramatically — constraints are usually cheaper than recovery, because they prevent the recovery from being needed.

## Origins and research lineage

- **Donald Norman**, *The Design of Everyday Things* (1988). Introduced constraints as one of the central tools for usable design. Norman distinguished four types: *physical, semantic, cultural, logical*. Lidwell, Holden, and Butler simplify to two (physical and psychological), with psychological encompassing semantic, cultural, and logical.
- **Lidwell, Holden & Butler** (2003) compactly distinguish:
  - **Physical constraints**: paths (channels that direct motion), axes (rotary controls), barriers (block undesired actions).
  - **Psychological constraints**: symbols (semantic communication), conventions (learned practices), mappings (perceived control-effect relationships).
- **James Reason**, *Human Error* (1990). Argued for constraints as the strongest defense against slip-type errors — making the wrong action structurally impossible is more reliable than training operators to avoid it.
- **Affordance theory** (J. J. Gibson, 1979) is the conceptual companion: affordance suggests what *can* be done; constraint blocks what *can't*. Together they describe the action space.

## Why constraints matter

Every error you prevent at the design layer is an error you don't have to detect, recover from, explain, or apologize for. Constraints are the design layer's strongest move because they operate before error occurs:

- **Confirmation** asks the user to verify after they've taken the wrong-feeling action.
- **Undo** lets them recover after they've taken the wrong action.
- **Constraint** makes the wrong action impossible in the first place.

The discipline: when you're tempted to add a confirmation, ask first whether a constraint would do the same job better. Often yes.

## Physical constraints

In hardware, physical constraints are the shape of an object directing how it can be used.

The book identifies three subtypes:

### Paths

Channels that direct motion. Examples:

- A scrollbar that constrains motion to one axis.
- A slot that only accepts a specific connector shape.
- A door with hinges on one side; it only swings one direction.

In software UI: a slider input is a path constraint — the user can only move along one dimension.

### Axes

Rotary controls. Convert applied force into rotation. Examples:

- A doorknob.
- A trackball.
- A volume knob.

In software UI: rotation gestures, dial inputs, the "spin" of an iOS time picker.

### Barriers

Block, slow, or redirect motion. Examples:

- A railroad crossing barrier.
- The boundary of a screen (the cursor stops there — Fitts's edge advantage).
- A child-safety cap on a medicine bottle.

In software UI: a modal dialog blocks interaction with the page beneath; a permission gate blocks access to a feature.

## Psychological constraints

Constraints that don't physically prevent action but lean on perception, convention, or knowledge.

The book identifies three subtypes:

### Symbols

Communicate meaning through language and iconography. Examples:

- A skull-and-crossbones on a poison bottle.
- The "WET FLOOR" sign.
- A red traffic light.

In software UI: a "Disabled" badge; a "Restricted" tooltip; a warning icon.

### Conventions

Learned practices. Examples:

- "Red means stop, green means go."
- "Click the X to close."
- "Cmd-S saves."

Conventions are a constraint because the user *expects* certain actions to do certain things; design that conforms is constrained-by-convention to behave as expected.

### Mappings

Perceived relationships between controls and effects. Examples:

- Light switches near the lights they control.
- A volume dial that turns the same way the user expects up/down to work.
- A stovetop where each burner has a knob in a corresponding position.

Good mappings constrain user error by making the wrong action *feel* wrong.

## When to apply

- **Always**, on input fields. Type, length, range, format.
- **Always**, on actions with preconditions. Submit disabled until form valid; "Send invoice" disabled until recipient selected.
- **On destructive actions where the constraint can be a forcing function**. Required type-to-confirm; required password re-entry.
- **On role-gated functionality**. Admin-only actions hidden or disabled for non-admins.
- **On state-dependent actions**. "Edit" only enabled in edit mode; "Save" only enabled when changes exist.

## When NOT to over-constrain

Constraints that don't reflect real requirements feel arbitrary and frustrating:

- **Forced format that's stricter than necessary** — a phone field that rejects parentheses.
- **Validation that reflects implementation, not user need** — "Display name must contain only ASCII." Why?
- **Mode locks the user can't predict** — a "read mode" they didn't enter and can't escape.
- **Disabled buttons with no explanation** — the user can't act and doesn't know why.

The discipline: constrain *real* requirements; communicate the constraint clearly when it surprises.

## Worked examples

### Example 1: input type as constraint

```html
<input type="email" required maxlength="254" autocomplete="email" />
<input type="tel" inputmode="numeric" pattern="[0-9-]+" />
<input type="number" min="0" max="999" step="1" />
```

The browser enforces the constraints. `type="email"` rejects malformed emails; `min="0"` rejects negative numbers. The user can't submit invalid input.

### Example 2: button disabled until valid

```html
<form id="signup">
  <input name="email" type="email" required />
  <input name="password" type="password" required minlength="12" />
  <button id="submit" disabled>Create account</button>
</form>

<script>
const form = document.getElementById('signup');
const btn = document.getElementById('submit');
form.addEventListener('input', () => {
  btn.disabled = !form.checkValidity();
});
</script>
```

Submit can't trigger until the form is valid. Pair with inline validation messages so the user knows what's missing.

### Example 3: role-based gating

```jsx
function DeleteButton({ project, currentUser }) {
  const canDelete = currentUser.role === 'admin' || project.ownerId === currentUser.id;
  if (!canDelete) {
    return null; // hide entirely; user can't even attempt
  }
  return <button onClick={confirmDelete}>Delete project</button>;
}
```

Users without permission don't see the button. The wrong action can't happen.

### Example 4: type-to-confirm as a forcing-function constraint

The destructive button is disabled until the user types the resource name. The constraint converts a single click into a deliberate multi-step action.

```html
<dialog>
  <h2>Delete workspace "Acme Inc"?</h2>
  <p>This cannot be undone. Type <strong>Acme Inc</strong> to confirm:</p>
  <input id="confirm" />
  <button id="delete-btn" disabled class="destructive">Delete workspace</button>
</dialog>

<script>
document.getElementById('confirm').addEventListener('input', e => {
  document.getElementById('delete-btn').disabled = e.target.value !== 'Acme Inc';
});
</script>
```

### Example 5: hardware-style physical constraint in UI

A drag-and-drop with a strict drop-zone restriction:

```js
function isValidDropTarget(item, target) {
  if (item.type === 'file' && target.acceptsFiles) return true;
  if (item.type === 'folder' && target.acceptsFolders) return true;
  return false;
}

dropZone.addEventListener('dragover', e => {
  if (isValidDropTarget(draggedItem, dropZone)) {
    dropZone.classList.add('drop-valid');
    e.preventDefault(); // allow drop
  } else {
    dropZone.classList.add('drop-invalid');
    // do not preventDefault — drop won't fire
  }
});
```

The browser's drag-and-drop API itself is a constraint mechanism: not preventing default during dragover prevents the drop. The user *can't* complete the wrong drop.

### Example 6: USB-C as the canonical physical constraint

USB-C connectors have rotational symmetry — they fit either way. USB-A connectors do not. Generations of users have struggled with the USB-A "flip the cable to insert it correctly" failure. USB-C eliminated the failure mode at the design layer; no error to recover from.

The lesson for software: when you can change the design so the failure can't happen, do that.

## Cross-domain examples

### Aviation: the auto-pilot disengagement

The auto-pilot can be disengaged by pulling back firmly on the yoke. The disengagement is *constrained* — a casual touch doesn't trigger it, a firm pull does. The constraint matches the seriousness of the action.

### Medicine: child-safety pill caps

A child-safety cap requires push-and-twist simultaneously. The constraint reduces accidental childhood poisoning dramatically. The cost: arthritic adults sometimes struggle with the cap. Trade-off acknowledged; the design is calibrated to the population at greatest risk.

### Industrial: dead-man switches

Equipment that requires continuous operator engagement (a hand on the trigger, a foot on the pedal) shuts off if the operator becomes incapacitated. The constraint protects against operator failure.

### Software: capability-based security

Modern security designs constrain code to only the capabilities it explicitly needs. A web page can't read your filesystem; an app can't access your microphone without explicit permission; a sandbox limits what an embedded program can do. Each is a constraint at the system layer.

## Anti-patterns

- **Disabled buttons with no explanation.** User doesn't know why they can't act.
- **Constraints that don't match user need** — overly strict format requirements that reject reasonable input.
- **Hidden constraints** — the user discovers the limit only after attempting (e.g., a character limit not mentioned until they exceed it).
- **Constraints framed as failures** — "Invalid input" instead of "Please enter a valid email like name@example.com."
- **Modal traps** — a modal that constrains too aggressively (no Esc, no close X) trapping the user.

## Heuristics

1. **The "what could the constraint replace?" check.** For each confirmation in your app, ask: could a constraint do this job? Often yes.
2. **The disabled-button audit.** Every disabled control should have a visible explanation of why it's disabled and what would enable it.
3. **The wrong-action thought experiment.** For each destructive flow, imagine a user attempting to take the wrong action. What constraint would prevent it?
4. **The convention check.** Are you violating a learned convention? If yes, the convention is a constraint working against you; either honor it or surface the violation explicitly.

## Related principles

- **`affordance`** — affordance suggests what *can* be done; constraint limits what *can't*. Companion principles.
- **`mapping`** — good mapping is a psychological constraint that makes wrong actions feel wrong.
- **`forgiveness`** — when constraint isn't possible, forgiveness handles the recovery.
- **`errors`** — constraints prevent the slip and mistake categories of error.
- **`expectation-effect`** — constraints work better when they match user expectation.
- **`visibility`** — constraints must be visible to be navigable.

## Sub-aspect skills

- **`constraint-physical`** — paths, axes, barriers; structural constraints in physical or screen-equivalent form.
- **`constraint-psychological`** — symbols, conventions, mappings; the constraint of expectation and learned practice.

## Closing

Constraint is one of the most powerful design tools and one of the most under-used. The reflexive design move on encountering an error is to add a confirmation or improve recovery; the better move, when possible, is to make the wrong action structurally impossible. Constraints are unglamorous but pay continuously across every user, every day.
