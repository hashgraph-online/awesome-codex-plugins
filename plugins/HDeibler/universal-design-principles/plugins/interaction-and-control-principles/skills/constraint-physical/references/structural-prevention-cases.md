# Physical constraints: case reference

A reference complementing `constraint-physical` with examples and patterns.

## Hardware physical constraints

- **USB-C connectors** — rotational symmetry eliminates orientation error.
- **Plug-and-socket polarity** — three-prong electrical plugs only fit one way.
- **Child-safety caps** — require simultaneous push and twist.
- **Aircraft cockpit gear handles** — shaped differently from flap handles to prevent confusion at night.
- **Door hinges** — limit door swing to one direction.

Each removes a class of error at the structural layer.

## Software physical-style constraints

- **Type-restricted inputs** (`<input type="email">`, `<input type="number" min="0">`) — the browser rejects invalid values.
- **Maxlength on inputs** — can't type past the limit.
- **Read-only attribute** — value can be selected/copied but not changed.
- **Disabled buttons** — can't trigger their action.
- **Modal dialogs** — block interaction with content beneath.
- **Drag-validity gates** — drop only fires when the target accepts the dragged item.
- **Permission-gated routes** — server returns 403 for unauthorized requests; UI hides the entry points.

## Patterns

### Form validation as constraint

```html
<input type="email" required maxlength="254" />
<input type="number" min="0" max="999" />
<input type="date" min="2020-01-01" max="2030-12-31" />
```

The browser enforces; submission is blocked until valid.

### Mode locks

A "view-only" mode disables editing controls. A "presentation mode" hides chrome. Each mode is a constraint that limits the action space to what's appropriate for the current task.

### Capability-based permissions

Permissions in modern OSes (iOS, Android, macOS) constrain apps to declared capabilities. An app must request microphone access; the user must grant; the OS blocks until granted.

### Sandboxing

Web pages run in browser sandboxes that constrain access to filesystem, hardware, and other origins' content. The constraint prevents whole classes of malicious actions.

## Trade-offs

Physical constraints are powerful but rigid. Over-constraining frustrates legitimate use:

- A name field that rejects apostrophes (O'Brien, D'Angelo) breaks for many users.
- A phone field requiring exactly 10 digits rejects international formats.
- A modal that blocks interaction is appropriate for some workflows; oppressive in others.

Calibrate the constraint to real requirements; don't constrain more than necessary.

## Resources

- **Norman, D.** *The Design of Everyday Things*.
- **OWASP** input-validation guidance (security-side constraint).
- **WCAG** form-validation accessibility guidelines.
