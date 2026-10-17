---
name: affordance-false-and-anti
description: 'Use this skill when designing or fixing controls that mislead users — elements that look interactive but aren''t (false affordance), or controls that need to clearly communicate "you can''t do that here" (anti-affordance, like disabled states). Trigger when reviewing UIs where users tap inert elements expecting response, when designing disabled states, when picking treatments for read-only fields, or when a "decorative" element is being mistaken for a button. Sub-aspect of `affordance`; read that first.'
---

# False affordance and anti-affordance

The mirror images of standard affordance: the elements that *look* interactive but aren't, and the elements that *are* interactive but should signal "not right now." Both deserve as much design attention as standard affordance — and both are routinely neglected.

## False affordance: looks interactive, isn't

A false affordance is an element whose visual treatment suggests interactivity it doesn't have. The user is led to expect an action; the action doesn't happen; trust drops.

Common sources:

- **Cards and panels styled like buttons.** A bordered, rounded, slightly-elevated container holds static content. Users tap; nothing happens.
- **Hover states on non-interactive elements.** A box that highlights on hover but isn't clickable. Users learn to mistrust hover signals.
- **Hyperlink-blue text that isn't a link.** Some design systems use blue for emphasis without realizing users read it as link affordance.
- **Underlined non-link text.** Underline is a strong link signifier; using it for emphasis or definition collides with that convention.
- **Icon-buttons next to non-interactive content.** A trash icon shown next to an item the user actually can't delete.

### Fixes

- Strip interactive-looking treatments from inert content. Use neutral backgrounds, no borders, no hover changes.
- Reserve underlines for actual links. Use bold or italics for emphasis instead.
- If a box must look distinct, use *uniform connectedness* (a tinted region) rather than *button-like elevation* (drop shadow, border).

## Anti-affordance: signaling "you can't"

Anti-affordance is the deliberate design of cues that tell the user "this is interactive in principle but unavailable to you right now." The most common case: disabled controls.

A disabled control needs to:

1. **Look different** from enabled (lower opacity, neutral color, no fill).
2. **Not respond** to hover or click as it would when enabled.
3. **Show a "no" cursor** (`cursor: not-allowed`).
4. **Optionally explain** why it's disabled — via tooltip or adjacent text.

```html
<button class="btn" disabled
        aria-disabled="true"
        title="Add at least one item to checkout">
  Continue to checkout
</button>
```

```css
.btn[disabled] {
  background: hsl(0 0% 92%);
  color: hsl(0 0% 50%);
  cursor: not-allowed;
  opacity: 0.7;
}
.btn[disabled]:hover {
  /* no change — this is the anti-affordance */
  background: hsl(0 0% 92%);
}
```

### When *not* to disable

A common UX mistake: disabling a button silently when the user "isn't ready" (form has unfilled required field; cart is empty). The user sees a non-responsive button and doesn't know why.

Better:

- **Keep the button enabled** and surface the validation error on click. The user gets a clear explanation rather than a silent block.
- Or, if the button must be disabled, **explain why** alongside it (a small note, a tooltip on hover/focus, or a visible reason).

```html
<button class="btn">Continue to checkout</button>
<p class="hint">Add at least one item to your cart to continue.</p>
```

The user can read the hint and act; the button isn't a dead end.

### Read-only fields

A field that's input-shaped but not editable is a special anti-affordance case.

```html
<label>Account ID
  <input type="text" value="acct_8f3c7a" readonly />
</label>
```

```css
input[readonly] {
  background: hsl(0 0% 96%);
  color: hsl(0 0% 30%);
  cursor: text;       /* still selectable for copy */
  border: 1px solid hsl(0 0% 90%);
}
```

The treatment says "this is data, not a control" — neutral background, no focus outline activation, but still selectable so users can copy.

For fields that aren't *currently* editable but *could* be (e.g., locked behind a permission), the visual treatment should hint that editability exists in principle.

## False affordance from animation

A subtle modern source: animating a non-interactive element. A heading that wiggles, an icon that pulses, a card that slowly tilts. These attract attention; users assume attention means interactivity.

If the animation is decoration only, audit whether it's drawing attention away from real interactive controls. If it's a callout for new content, ensure clicking does *something* — even if just to dismiss the callout.

## Worked examples

### Example 1: a card that *should* be clickable vs. one that shouldn't

```html
<!-- Clickable: card-link wraps, hover responds -->
<a href="/projects/acme" class="card-link">
  <article class="card">...</article>
</a>

<!-- Inert: no link wrap, no hover response -->
<article class="card card--inert">
  <h3>System status</h3>
  <p>All services operational.</p>
</article>
```

```css
.card { padding: 16px; border: 1px solid hsl(0 0% 88%); border-radius: 8px; }
.card-link { display: block; text-decoration: none; color: inherit; }
.card-link:hover .card { border-color: hsl(220 90% 60%); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }

.card--inert {
  background: hsl(0 0% 98%);  /* slightly different bg signals "informational" */
  border-color: hsl(0 0% 92%);
}
.card--inert:hover {
  /* no change — anti-affordance */
}
```

The clickable card shifts on hover; the inert one stays still. Users learn quickly that hover-responsive cards are clickable and others aren't.

### Example 2: read-only vs. disabled vs. unavailable

Three subtly different states, each with its own anti-affordance:

```html
<!-- Read-only: data, never editable here -->
<label>Workspace ID
  <input value="ws_abc123" readonly />
</label>

<!-- Disabled because of state: editable when condition is met -->
<label>Email
  <input value="user@example.com" disabled aria-describedby="email-locked" />
</label>
<p id="email-locked" class="hint">Verify your email to enable changes.</p>

<!-- Unavailable due to permission: visible but not actionable -->
<label class="field-locked">
  <span>Workspace name <LockIcon aria-hidden /></span>
  <input value="Acme Inc" readonly />
  <p class="hint">Only workspace admins can change this.</p>
</label>
```

The user gets specific anti-affordance signals for each: read-only data is visually demoted; conditionally-disabled is enabled-looking-but-with-explanation; permission-locked has a lock icon and explanation.

## Anti-patterns

- **Decorative elevation on content cards.** Drop shadows that suggest "object you can interact with" on cards that are pure content. Strip the shadow.
- **Disabled-button silent dead ends.** A submit button that's just disabled with no explanation. Users hunt for what's wrong.
- **Read-only fields styled identically to editable.** Users tab into them, type, get confused.
- **Inert hover responses.** A non-clickable element with a hover style applied "for visual interest." Users tap it, nothing happens, trust drops.

## Heuristics

1. **The "I tapped, nothing happened" audit.** Watch users. Each unproductive tap is a false-affordance failure or an anti-affordance failure (disabled with no explanation).
2. **The hover-style audit.** Every element with a hover state should be interactive. If you have hover styles on non-interactive elements, strip them.
3. **The disabled-with-context check.** Every disabled control on every page should answer "why?" — via tooltip, adjacent text, or context.

## Related sub-skills

- **`affordance`** (parent).
- **`affordance-signifiers`** — the standard case of making affordance visible.
- **`feedback-loop`** — disabled controls should still give *some* feedback (cursor change at minimum).
- **`accessibility-understandable`** (process) — disabled states must be programmatically conveyed (`disabled` attribute, `aria-disabled`).
