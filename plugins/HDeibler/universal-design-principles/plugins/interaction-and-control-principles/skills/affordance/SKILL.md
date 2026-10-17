---
name: affordance
description: 'Use this skill whenever the question is whether the user can tell what an element does — whether it looks clickable, draggable, expandable, editable, or interactive at all. Trigger when designing buttons, links, custom controls, drag handles, draggable cards, editable inline fields, or any interactive element. Trigger on reviews when users hesitate, miss controls, or click on things that aren''t interactive. Affordance is one of the most decisive principles in interaction design — Norman placed it at the center of *The Design of Everyday Things* — and it''s one of the most violated by modern flat-design conventions that strip the visual cues users rely on.'
---

# Affordance

Affordance is the relationship between an object's properties and the actions it makes possible. A door handle affords pulling; a flat plate affords pushing; a button affords pressing; a slider affords sliding. When the affordance matches the intended use, the design works without instruction. When the affordance contradicts the intended use, even a sign saying "PUSH" cannot fully repair it — users still try to pull the handle first.

## Definition (in our own words)

Affordance is what an object's appearance, shape, weight, and material tell the user about what they can do with it. The affordance lives partly in the object itself (a button has a graspable shape) and partly in the user's perception of it (a child seeing a button for the first time has a different model than an adult who's seen ten thousand). Designers control the visual and behavioral signals; users bring prior experience. Where the two align, the design "just works"; where they diverge, the user must read, ask, or guess.

## Origins and research lineage

- **James J. Gibson**, *The Ecological Approach to Visual Perception* (Houghton Mifflin, 1979). Gibson coined "affordance" in ecological psychology to describe what an environment offers an animal: a horizontal surface affords standing; a graspable object affords carrying. The concept predates HCI but maps naturally to it.
- **Donald Norman**, *The Design of Everyday Things* (1988, revised 2013). Translated affordance from Gibson's perceptual psychology into design vocabulary. Norman's iconic example — doors that look like they pull but actually push — became shorthand for affordance failure.
- **Norman's later refinement** — "Signifiers, not affordances" (2008). Norman clarified that what designers actually control are *signifiers* (visible cues that suggest an action). The affordance is the underlying possibility; the signifier is what tells the user about it. The book's principle covers both, but the distinction matters in fine-grained design discussion.
- **Lidwell, Holden & Butler** (2003) compactly stated the principle as "a property in which the physical characteristics of an object or environment influence its function" and gave the door-handle-vs-flat-plate example as the canonical illustration.
- **Web/UI affordance research** — Bagrow, Tognazzini, and many others have studied how affordance translates to flat 2D screens. The shift from skeuomorphic to flat design (around 2013) reduced traditional affordance signals; subsequent recovery (subtle shadows, hover states, motion) has rebuilt them in less literal forms.

## Why affordance matters

Affordance is the fastest comprehension channel a UI has. A user looking at a screen for half a second can tell — preattentively, before reading a single label — which elements are interactive and which are content. Strong affordance lets the user form a working theory of the page in seconds; weak affordance forces them to point at things and watch what happens.

The cost of weak affordance compounds:

- **Time wasted hovering** over non-interactive elements to check.
- **Time wasted scanning** for the interactive element among the inert ones.
- **Misclicks** on things that look interactive but aren't (or vice versa).
- **Anxiety** about what happens when something is clicked.
- **Eventual learned helplessness** — users stop exploring and stick to the obvious paths.

## When to apply

- **Every interactive element** must have an affordance signal. This is non-negotiable.
- **Every non-interactive element** must *not* look interactive. False affordance is as damaging as missing affordance.
- **Custom controls** — when reaching past native HTML elements, you take on responsibility for the affordances those native elements provided for free.
- **Empty states and onboarding** — affordance carries the "what can I do here?" answer before any text does.
- **Touch surfaces** — touch has no hover, so affordance must work in the still state.

## When NOT to apply (or when to be careful)

- **Decorative elements** that aren't interactive should not have affordance signals. A "Welcome" banner shouldn't look like a button just because it's prominent.
- **Disabled controls** need *anti-affordance* — visibly different (lower opacity, different cursor) so users don't try to interact.
- **Power-user-only controls in dense UIs** can have subtler affordance because experts use spatial memory; new-user surfaces need stronger cues.

## What the user reads as affordance

Affordance signals fall into a small set of categories:

### Shape and outline

A bordered, rectangular shape with text inside reads as a button — across cultures, across years. The convention is so strong that it survives flat design: even a single-line border is enough to communicate "pressable."

### Color contrast against context

An element that's a different color than its surroundings reads as set apart, often as interactive. The brand-color CTA is the canonical case.

### Depth and elevation

Drop shadows, gradients, raised edges all suggest "pressable object floating above the page." Even subtle elevation (`box-shadow: 0 1px 2px rgba(0,0,0,0.05)`) is enough to communicate "this is a button, not flat content."

### Cursor change

Hover changes the cursor (`cursor: pointer`) — a strong "this is clickable" signal on desktop. For touch users this doesn't help; pair with visual signals.

### Hover and focus state

Color change, shadow shift, slight scale on hover signals "this responds to you." Focus ring on keyboard focus signals "this is interactive and currently selected."

### Underline (for links)

Underlined text reads as a link. The convention is so old it predates the web (footnotes in print). Stripping link underlines for aesthetic reasons damages affordance — color alone is weaker, especially for color-blind users.

### Iconography

A trash-can icon affords delete; a pencil icon affords edit; a magnifying glass icon affords search. These are *learned* affordances — they require prior exposure — but conventional icons have become as universal as physical-object affordances were before screens.

### Position and grouping

Buttons clustered at the bottom of a card or modal afford "primary actions." A control isolated in the corner of a row affords "this row's options." Position carries affordance through learned UI conventions.

## Worked examples

### Example 1: button vs. text vs. plain content

```html
<!-- Plain content: no affordance, none expected -->
<p>Your account expires in 14 days.</p>

<!-- Link: text-link affordance (color + underline on hover) -->
<p>Your account expires in 14 days. <a href="/billing">Update billing</a></p>

<!-- Button: button affordance (shape + background) -->
<p>Your account expires in 14 days.</p>
<button class="btn-primary">Update billing</button>
```

```css
.btn-primary {
  background: hsl(220 90% 50%);
  color: white;
  padding: 8px 16px;
  border: 0;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
}
.btn-primary:hover { background: hsl(220 90% 45%); }
.btn-primary:focus-visible {
  outline: 2px solid hsl(220 90% 50%);
  outline-offset: 2px;
}

a { color: hsl(220 90% 40%); text-decoration: underline; text-decoration-thickness: 1px; text-underline-offset: 2px; }
a:hover { text-decoration-thickness: 2px; }
```

The plain `<p>` reads as content. The `<a>` reads as a link via color + underline. The `<button>` reads as a button via shape + color + cursor + hover.

### Example 2: clickable card

A common modern pattern: a card that's entirely clickable. The challenge: a card looks like content by default; making it clickable requires explicit signals.

```html
<a href="/projects/acme" class="card-link">
  <article class="project-card">
    <h3>Acme Project</h3>
    <p>Q4 marketing site refresh</p>
    <p class="meta">3 open tasks · Due May 15</p>
  </article>
</a>
```

```css
.card-link { text-decoration: none; color: inherit; display: block; }
.project-card {
  border: 1px solid hsl(0 0% 88%);
  border-radius: 8px;
  padding: 16px;
  background: white;
  transition: border-color 150ms, box-shadow 150ms, transform 150ms;
}
.card-link:hover .project-card {
  border-color: hsl(220 90% 60%);
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  transform: translateY(-1px);
}
.card-link:focus-visible .project-card {
  outline: 2px solid hsl(220 90% 50%);
  outline-offset: 2px;
}
```

The card's affordance: subtle border in the still state (suggesting "object, not flat content"), strong response on hover (border color, shadow lift, slight upward translate). Without those state changes, the card looks identical to a non-clickable info panel.

### Example 3: drag handle

A drag handle is a deliberately-novel control; its affordance must teach the user.

```html
<li class="sortable-row">
  <button class="drag-handle" aria-label="Drag to reorder">
    <svg viewBox="0 0 24 24" width="16" height="16">
      <circle cx="9" cy="6" r="1.5" /><circle cx="9" cy="12" r="1.5" /><circle cx="9" cy="18" r="1.5" />
      <circle cx="15" cy="6" r="1.5" /><circle cx="15" cy="12" r="1.5" /><circle cx="15" cy="18" r="1.5" />
    </svg>
  </button>
  Task name
</li>
```

```css
.drag-handle {
  cursor: grab;
  background: transparent;
  border: 0;
  padding: 8px;
  color: hsl(0 0% 60%);
}
.drag-handle:hover { color: hsl(0 0% 30%); }
.drag-handle:active { cursor: grabbing; }
```

The signals: the six-dot icon (an established convention), `cursor: grab` (signals "you can pick this up"), and a hover state to confirm the control responds.

### Example 4: editable inline text

A field that becomes editable on click — useful but affordance-fragile because the field looks like static text by default.

```html
<h2 class="editable" contenteditable="true">Project name</h2>
```

```css
.editable {
  cursor: text;
  border-bottom: 1px dashed transparent;
  padding-bottom: 2px;
  transition: border-color 150ms;
}
.editable:hover { border-bottom-color: hsl(0 0% 70%); }
.editable:focus {
  border-bottom-color: hsl(220 90% 50%);
  outline: 0;
}
```

Hover signals "you can interact" via the dashed underline. Focus locks in via solid color. Without these, users don't realize the heading is editable until they accidentally click and panic.

### Example 5: anti-affordance for disabled controls

```html
<button class="btn-primary" disabled>Save (no changes)</button>
```

```css
.btn-primary[disabled] {
  background: hsl(0 0% 92%);
  color: hsl(0 0% 50%);
  cursor: not-allowed;
}
.btn-primary[disabled]:hover { background: hsl(0 0% 92%); /* no change */ }
```

The disabled state visibly removes affordance: lighter color (recedes), `cursor: not-allowed` (signals impossibility), no hover response. Pair with a label or tooltip explaining *why* it's disabled — disabled affordance tells the user they can't, but not why.

## Cross-domain examples

### Door handles vs. push plates

Norman's canonical example. A vertical handle says "grab and pull." A horizontal flat plate says "push here." A door that requires pushing but has a handle is a *false affordance* — even with a "PUSH" sign, users will instinctively pull first. Better: replace the handle with a plate or bar shape.

### Industrial control design

Knobs afford turning. Switches afford flipping. Sliders afford sliding. Buttons afford pressing. Industrial designers select control types based on the action's semantics; mismatches create slips even with experienced operators.

### Lego bricks

Lego bricks afford stacking. The studs on top mate with the cavities on the bottom of the next brick. The shape *teaches* the assembly system — children figure out plugging without instruction because the shapes are unambiguous.

### Children's toys

A shape-sorter teaches affordance: square hole takes square block; round hole takes round block. The mismatched attempts fail visibly; the matched attempts succeed satisfyingly. This is affordance pedagogy in physical form.

### Software desktop metaphors

The original desktop metaphor (Xerox Star, Mac) borrowed affordance from physical desktops. Folders look like folders; trash looks like trash. The metaphor *teaches* the affordance via familiarity. Modern flat design has stripped the literal mimicry while retaining the structural affordances (folders are still containers; trash is still a destination).

## Anti-patterns

- **The flat-design no-affordance trap.** A "minimalist" UI where buttons have no border, no background, no cursor change. Users can't tell what's interactive without trial-and-error.
- **The mystery card.** Cards on a dashboard that are sometimes clickable and sometimes not, with no visual difference between the two states. Users learn to suspect everything.
- **Style-only links.** Links that have only a slight color difference from body text — no underline, no hover affordance change. Color-blind users see no difference.
- **Hover-only affordance on touch.** Affordance signals that only appear on hover fail entirely on touch devices. Build affordance into the still state.
- **Fake affordance.** A page header that looks like a button (bordered, raised) but isn't clickable. Users tap; nothing happens; trust erodes.
- **Inconsistent affordance.** Buttons that look like buttons in one place and like links in another, for the same action role. Each place is a re-learning.
- **Custom controls without inherited affordance.** Building a `<div onclick>` instead of `<button>` strips the native affordance signals (cursor, focus, keyboard activation). You must rebuild them all manually.

## Heuristics

1. **The squint test.** Squint at the screen until detail blurs. Can you still identify which elements are interactive? If everything blurs into the same shapes, affordance is too weak.
2. **The fresh-user click test.** Hand the design to someone who hasn't seen it. Watch what they hover and tap. Misses are affordance failures.
3. **The grayscale test.** Convert to grayscale. Affordance that depended on color (a blue link) collapses; you'll see what affordance remains. Robust affordance survives grayscale.
4. **The hover-off test.** Disable all hover states. Does the still state still communicate which elements are interactive? If no, you were leaning on hover too much.
5. **The keyboard-only test.** With Tab, can you reach every interactive element? Are the focus rings visible? Affordance for keyboard users is the focus ring; missing rings = missing affordance for them.

## Related principles

- **`constraint`** — affordance and constraint are complementary: affordance suggests what *can* be done; constraint blocks what *can't*. Both work together.
- **`mapping`** — affordance signals what an element does; mapping signals what it affects.
- **`mimicry`** — borrowing affordance from familiar physical or digital objects.
- **`wayfinding`** — interactive elements with affordance are wayfinding cues.
- **`feedback-loop`** — once acted on, the element gives feedback confirming the action.
- **`consistency`** — affordance only works when the same shape always means the same action.
- **`accessibility-perceivable`** — affordance must be perceivable across abilities; color-only affordance fails colorblind users.
- **`hierarchy`** — primary actions need stronger affordance than secondary; emphasis economy applies.

## Sub-aspect skills

- **`affordance-signifiers`** — Norman's later refinement: the visual cues designers control to make affordances perceivable. When the underlying affordance exists but the signifier is missing, the user doesn't know.
- **`affordance-false-and-anti`** — false affordance (looks interactive but isn't) and anti-affordance (deliberately signals "you can't do this here"). Both are crucial counterparts to standard affordance design.

## Closing

Affordance is the principle that decides whether your UI is intuitive or has to be taught. Strong affordance is invisible — users just *know* what to click — and weak affordance is the silent reason support tickets ask "how do I X?" when X is right there on the screen. Build affordance into the still state, layer on the response states, and audit every interactive element for whether someone seeing it for the first time would recognize it as interactive.
