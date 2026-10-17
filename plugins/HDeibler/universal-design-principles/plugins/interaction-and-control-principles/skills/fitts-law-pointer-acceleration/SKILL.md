---
name: fitts-law-pointer-acceleration
description: 'Use this skill when the question involves cursor speed, pointer acceleration curves, or interaction with input devices that vary in precision (mouse, trackpad, stylus, touchscreen, eye-tracking). Trigger when designing for varied input devices, building drag interactions, designing scrubbers / sliders / handles, or analyzing why a UI feels "fiddly." Sub-aspect of `fitts-law`; read that first if you haven''t already.'
---

# Fitts's Law and pointer acceleration

The mouse and trackpad are not "raw" inputs — operating systems apply *acceleration curves* that translate physical movement into cursor displacement. Fast physical motion produces disproportionately fast cursor motion; slow physical motion produces precise, slow cursor motion. This curve interacts with Fitts's Law in ways that affect how target size and distance are perceived.

## What pointer acceleration does

A non-accelerated cursor maps physical motion to screen motion 1:1. To cross 1000 pixels, the user must move the mouse 1000 mouse-equivalent units. Fast or slow physical motion makes no difference to the resulting distance.

An accelerated cursor varies the multiplier based on physical speed:

- **Slow physical motion → low multiplier** (e.g., 0.5×). Used for precise positioning over small targets.
- **Fast physical motion → high multiplier** (e.g., 3–8×). Used for crossing large screen distances quickly.

The acceleration curve is what lets a single mouse on a 4K display traverse the full screen without lifting and re-anchoring (a problem 1990s mice without acceleration had).

For Fitts's Law, this means:

- **Distance is partly free.** Long traversals are accelerated, so movement time grows much less than the linear formula predicts.
- **Target size still matters.** Once the user is *near* the target, they slow down for fine positioning, and target size dominates again.
- **Trackpads and mice have different curves.** Same Fitts's task, different time outcomes.

## Implications for UI design

### 1. Distance matters less than naive Fitts's Law suggests on accelerated pointers

A toolbar at the top of a 1440px-wide window vs. one halfway down: the difference in actual cursor travel time is smaller than the geometric distance suggests. Don't sacrifice layout sense to "place everything close together" — acceleration absorbs much of the cost.

### 2. Target size matters *more* than naive Fitts's Law suggests near the target

When the cursor decelerates for fine positioning, small targets become disproportionately hard. A 16×16 button is much harder than a 24×24 button — more than the 50% size increase would suggest, because deceleration phase amplifies precision cost.

The takeaway: when in doubt, prefer *bigger* targets to *closer* targets. Acceleration handles distance; nothing handles fine-positioning except size.

### 3. Drag operations are sensitive to acceleration

A drag-and-drop interaction asks the user to move while pressing the button. Acceleration is still active, so a small physical motion can become a large cursor motion. This causes:

- **Overshoot on rapid drags.** The user releases past the target.
- **Jitter on fine drags.** Slow drags feel "sticky" or imprecise as the curve transitions.

Mitigations:

- **Provide visible drop zones** that are larger than the dragged item's footprint. The user has slop room.
- **Snap-to-grid or snap-to-target** for positioning interactions. Reduces precision burden.
- **Hold-modifier for fine control.** Hold `Shift` (or similar) to disable acceleration during drag. Common in drawing and layout tools.

### 4. Sliders and scrubbers benefit from gain control

A volume slider, a video scrubber, a date-range picker: the user is dragging to a precise value. With raw acceleration, large values are easy to skip past.

Patterns:

- **Variable gain on slider drag.** Drag near the slider track for fast scrubbing; drag away from the track (off-axis) for fine scrubbing. iOS scrubbers use this.
- **Snap-to-tick** for slider values that should land on integers or other discrete values.
- **Display the current value during drag** so the user can correct without lifting.

### 5. Different input devices, different curves

The same web app is used with:

- **Desktop mouse** — moderate acceleration, medium precision.
- **Trackpad** — high acceleration, lower precision (small physical surface), gestures.
- **Stylus / pen** — low/no acceleration, high precision.
- **Touchscreen** — no acceleration (1:1), but finger contact width adds imprecision.
- **Eye-tracking** — low precision, no fine positioning, dwell-based selection.

A UI that works on a 27" monitor with a precise mouse may be unusable with a trackpad on a 13" laptop. Test both.

For accessibility:

- **Switch devices** (single-button accessibility input) — every interactive element must be reachable through scanning, not pointer acquisition.
- **Sip-and-puff and other adaptive devices** — same.

## Worked examples

### Example 1: a slider with click-to-position

```html
<input type="range" min="0" max="100" value="50" />
```

Native `<input type="range">` works across input devices. The user can click anywhere on the track to jump to that value (no drag required); drag the thumb for fine adjustment; tap arrow keys for precise stepping. All of this is built in.

For custom sliders:

- **Make the track full-width clickable** (not just the thumb).
- **Make the thumb hit area ≥ 24×24** (often the visible thumb is smaller, but the hit area extends).
- **Support arrow keys** for keyboard increment.

### Example 2: a draggable list item

```html
<li draggable="true" class="task">
  <span class="drag-handle" aria-label="Drag to reorder">⋮⋮</span>
  Task name
</li>
```

The drag handle is visually small but should have a 32×32+ hit area. During drag:

- Show a visible placeholder where the item will drop (large drop target).
- Display drop indicators between rows.
- Provide a keyboard alternative (e.g., arrow keys to reorder) for users who can't drag.

### Example 3: a color picker

A 256×256 color square asks for very fine positioning (each pixel = a different color). Pointer acceleration makes this hard.

Mitigations:

- Provide numeric inputs (RGB / HSL / HEX) for users who need precision.
- Provide preset palette swatches for common selections.
- Allow `Shift+click` (or another modifier) for fine-position mode.

### Example 4: pinch-and-zoom (touch)

Touch has no acceleration, but two-finger gestures benefit from velocity-aware behavior:

- **Slow pinch** = precise zoom (small zoom factor change per pixel).
- **Fast pinch** = rapid zoom (larger zoom factor change per pixel).

Implementations: track pinch velocity; multiply zoom delta by a function of velocity.

## Anti-patterns

- **Custom sliders without keyboard support.** A drag-only slider is unusable for keyboard, switch-device, and many assistive-tech users. Always support arrow-key increment.
- **Tiny drag handles.** A 16×16 drag handle on a list row. The user can't reliably grab it; reordering becomes painful.
- **Drag-only reordering.** Reordering that requires drag-and-drop with no keyboard alternative. Inaccessible by default.
- **No snap on positioning.** A drag-to-arrange canvas with no grid, no snap-to-edge, no align-with-neighbor. Every placement requires fine positioning that pointer acceleration sabotages.
- **Hover-precision interactions.** A hover-only menu where the dropdown is below the trigger and the user must traverse a wedge-shaped path to reach the items. The trackpad user, with high acceleration, overshoots into adjacent menu items. Either use click-to-open or design wider safe traversal areas.

## Heuristics

1. **Test on a trackpad.** If your interaction requires a mouse to be usable, it's broken for ~half your users.
2. **Test with arrow keys.** Every interactive element should respond meaningfully to keyboard alternatives. (This is also accessibility.)
3. **The fine-positioning audit.** Walk through every interaction that asks for precision. Is there a coarser alternative (typed value, snap, increment buttons)?

## Related sub-skills

- **`fitts-law`** (parent).
- **`fitts-law-touch-targets`** — touch has no acceleration but its own precision constraints.
- **`affordance`** — drag handles need visible affordance.
- **`accessibility-operable`** (process plugin) — pointer-precision interactions must have non-pointer alternatives.
- **`mapping`** (cognition) — sliders and scrubbers map control motion to value change; mapping must be intuitive.
