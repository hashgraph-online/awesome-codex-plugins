# Render traps: when the timeline is right and the file is wrong

HyperFrames and Three.js compositions are rendered by seeking a timeline frame by frame in headless Chrome. Several things that look fine in a live preview break in that render. Each trap below has the symptom, the cause, and the fix. Always judge the encoded file, not the preview: extract frames from the rendered MP4 at every beat and every cut.

## GSAP and timelines

**1. `fromTo` that shows too early.** A `fromTo` whose FROM values have `autoAlpha: 1` makes the element visible from the start. Put `autoAlpha: 0` in FROM and `1` in TO. A `fromTo` that starts after t = 0 on an element that must stay invisible until then needs `immediateRender: false`, or it applies its start values at once and can overwrite earlier tweens on the same property. If the element is hidden by CSS, also set the opacity in the TO values.

```js
// wrong: visible at t = 0 although the tween starts at 2
tl.fromTo(card, { autoAlpha: 1, y: 24 }, { autoAlpha: 1, y: 0, duration: 0.5 }, 2);
// right: hidden by CSS (opacity: 0), revealed at 2
tl.fromTo(card, { autoAlpha: 0, y: 24 }, { autoAlpha: 1, y: 0, duration: 0.5, immediateRender: false }, 2);
```

**2. An entrance that is still running when the exit starts.** In a sequential render the tween that finishes last on a property wins, so a late entrance can undo an exit that already completed, and a whole scene can vanish from the file while the preview looks fine. Start every exit at or after the end of its entrance. Compute yoyo repeats so a bob ends before the exit.

**3. Starting states belong in CSS.** A `tl.set(el, {...}, 0)` may not be applied when frame 0 is captured, so an element meant to start hidden flashes. Put the starting state (`opacity: 0`, an offset transform) in CSS.

**4. Durations round up to whole frames.** A root duration of 41.7667 s at 60 fps rendered 2507 frames when 2506 were planned. Write each duration as frames / fps minus a small epsilon (for example 0.001 s), and trim every segment to its planned frame count when you join segments.

**5. Do not tween `width`, `height`, `top` or `left`.** They trip the non-transform lint and animate badly. Build a resizing crop as a fixed full-frame layer with an animated `clip-path: inset(...)` and a transformed image inside.

**6. No timed sections with nested markup in the root.** Use untimed beat containers whose visibility the timeline owns, and time only the media elements individually.

## Drawing and styling

**7. SVG stroke drawing.** In the HyperFrames render, `pathLength="1"` with a numeric `strokeDashoffset` tween did not draw progressively: the line stayed invisible and then snapped. Measure the real length with `path.getTotalLength()` and set pixel values: `strokeDasharray = L`, tween `strokeDashoffset` from `L` to `0`. (In a normal browser page `pathLength="1"` draws, but with `vector-effect: non-scaling-stroke` Chrome draws the wrong amount there too, so the rule is the same everywhere: measured pixel lengths, and no `non-scaling-stroke` on a line you draw. brief2motion follows the same rule.)

**8. Style repeated components by class, never by id.** A second copy that shared an id lost its styles and painted black. Give each repeated image asset its own file; a `?u=` query on an `<img>` SVG source loaded as a broken image.

**9. Never put a `//` comment in the middle of packed one-line JavaScript.** It swallowed the rest of the line and objects silently vanished. Use `/* */`.

**10. Clip masked line reveals with room for descenders.** An `overflow: hidden` line mask cuts the descenders of italic serif type: pad the bottom of the line.

## Cost

**11. Heavy-overlay budget.** `backdrop-filter`, `filter: blur`, radial gradients and `clip-path` all count as overlays. Observed on a laptop: about 24 per composition is comfortable and about 40 captured black frames. Use a plain gradient "glass" over flat backgrounds and real backdrop blur only for small chips over UI. Frosted glass shows whatever is behind it, so the outgoing headline must be fully gone first.

**12. Workers are not free.** More render workers is not always faster. See the measured numbers in `SKILL.md` (Render settings); re-measure on your machine.

## 3D and WebGL

**13. A WebGL layer sits above the DOM and ignores DOM transitions.** A 3D character or canvas that is not given its own eased exit, synced to the transition, blinks off when the scene ends. Animate its opacity or position out with the same timing as the DOM exit.

**14. Update the camera matrix before projecting points at setup** (`camera.updateMatrixWorld()`); otherwise the projected positions are NaN and the effect silently never draws.

**15. Device pixel ratio at 4K.** Make the 3D renderer follow the pixel ratio of the render (not a hard-coded 1) when the delivery size is 4K, and give canvas-texture labels a resolution of size x DPR so text stays sharp.

**16. A small subject in a wide dark shot reads as frozen.** Go closer, chase each event with the camera, add slow ambient elements, and save the wide reveal for the moment the count takes over.

**17. Dark surfaces: roughness 1, metalness 0** when "lit versus dark" carries the meaning. A low-roughness dark window catches a point-light highlight and looks lit.

## ffmpeg

**18. Never give ffmpeg a glob as an input.** `ffmpeg -y -i dir/name-v*.mp4 out.mp4` treats the other matches as outputs and overwrites them. Resolve the file you want first and quote it.

## How to catch these

1. Render a draft, then run `scripts/check_seams.py` for flashes and pops and `scripts/check_clutter.py` for overlaps.
2. Pull frames from the encoded file at every beat and cut (`scripts/contact_sheet.sh`) and look at them.
3. Run `scripts/ocr_sweep.sh` for placeholder text that only exists in the render.
