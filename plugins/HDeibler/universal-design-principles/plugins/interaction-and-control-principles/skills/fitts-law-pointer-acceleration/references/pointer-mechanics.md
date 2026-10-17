# Pointer mechanics: deeper reference

A reference complementing `fitts-law-pointer-acceleration` with deeper detail on input devices and pointer behavior.

## How pointer acceleration is computed

Operating systems apply a **transfer function** that maps physical input motion to cursor motion. The function is non-linear:

- Slow physical motion → roughly 1:1 mapping (precise positioning).
- Medium physical motion → 1.5–3× multiplier (general use).
- Fast physical motion → 3–10× multiplier (cross-screen traversal).

The exact curves vary by OS and user setting. macOS allows tuning via "Tracking speed" in System Settings; Windows offers similar controls. Some users (gamers, designers) disable acceleration entirely for predictability.

The trade-off:

- **With acceleration**: faster cross-screen traversal; harder fine positioning at high speeds.
- **Without acceleration**: predictable motion at all speeds; slow cross-screen traversal; less hand strain on small mice.

For most software UI, default OS acceleration is fine. The main implication for designers: when you can't assume what the user's curve looks like, prefer designs that don't rely on fine pointer positioning.

## Input devices and their characteristics

| Device | Typical acceleration | Precision | Comfort for fine work |
|---|---|---|---|
| Mouse | Medium | Good | Good |
| Trackpad | High | Lower | Moderate |
| Stylus / pen | None (1:1) | Very high | Excellent |
| Touchscreen | None (1:1) | Limited by finger size | Poor for small targets |
| Trackball | Medium | Good (after practice) | Good |
| Eye tracking | None | Low (~1° visual angle) | Limited; dwell-based |
| Switch device | N/A (scanning) | N/A | Slow; designed for accessibility |
| VR controller | High (variable) | Moderate | Moderate; depends on tracking |

A web app served to all of these must avoid designs that work only on the most precise devices.

## Drag operations

Drag is acceleration-sensitive in a way clicks aren't. While dragging, the user is committed — they can't pause to plan. A small physical motion can carry a large screen distance.

Mitigations:

- **Snap-to-grid.** Reduces precision burden; user lands on integer positions.
- **Snap-to-target.** As the dragged item approaches a drop zone, attractor logic snaps it. Common in drawing apps.
- **Visible drop zones.** A 100×100 drop area is much easier than a 10×10 target.
- **Hold modifier for fine control.** Shift to disable acceleration during drag (common in design tools).
- **Keyboard alternative.** Arrows + spacebar to reorder, for users who can't drag at all.

## Scrubbers and sliders

Sliders ask for precise positioning over a 1D range. Acceleration makes high-precision values hard to land on.

Patterns:

- **Variable-gain dragging.** Drag near the slider track for fast scrubbing; off-axis for fine. iOS scrubbers use this.
- **Snap-to-tick.** For discrete values (1–10 ratings, integer dB).
- **Visible value during drag.** So the user can correct without lifting.
- **Numeric input alongside.** For values that benefit from typed precision.

## Cross-domain examples

### Color pickers

A 256×256 color square asks for very fine positioning — every pixel is a different color. Plus typed RGB/HSL/HEX inputs (recognition over recall + numeric precision) and preset swatches (popular choices) to avoid forcing fine pointing.

### Audio mixers

DAWs (Logic, Ableton, Pro Tools) use both faders (drag with shift for fine control) and numeric inputs (type exact dB). The combination makes fader work fast and exact when needed.

### Maps

Map zoom buttons (+ / −) as discrete steps; pinch-to-zoom on touch; mouse wheel for continuous; double-click to zoom in to point. Multiple paths to the same goal, each suited to a different input device.

## Resources

- **MacKenzie, I. S.** *Human-Computer Interaction: An Empirical Research Perspective* (2013). Comprehensive coverage of input-device research.
- **Card, Moran, Newell** *The Psychology of Human-Computer Interaction* (1983). Foundational HCI input research.
- **OS-specific accessibility settings** — knowing how to test your own UI under different acceleration curves and pointer settings.

## Closing

Pointer acceleration is invisible when you're using your own machine and decisive when your user is on different hardware. Test on a trackpad, with arrows-only, with assistive switch input, with a stylus — and design for the union.
