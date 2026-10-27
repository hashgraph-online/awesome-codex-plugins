# VFX technique bank (canvas 2D equivalents of AE / Blender / animation devices)

**When to read:** step 4 (style frames: each direction names 2–3 techniques from here) and step 5 (every scene change in the shot map names its transition from §1). **Output:** a "technique" column in `shotmap.md` with the function name and parameters for each row.

Every entry has four parts: **looks like · source · how (parameters) · lib call** (`assets/template/motion-lib.js`; all functions are deterministic and safe for parallel rendering). `fx-demo.html` shows each one for one second. Run `node tools/render-fast.js fx-demo.html stills/fx --stills 0.45,1.45,…` to see them before choosing.

Sources: links come from research on 2026-10-24. Many anime-OP and MV uploads are third-party, so check frames at 0.25× (`tools/ref_frames.sh`) before copying a timing. Parameters are starting points for 1080×1920, not measured from the original work.

Two implementation rules apply to every technique:
1. Nothing accumulates between frames. Particles, trails and shards are closed-form `f(i, t)`, re-integrated from birth, or `drawAt(t − Δ)` drawn again.
2. Blur and glow run at 1/4 resolution and are scaled back up. Wrap the frame in `layer()` so post-processing can read it.

---

## 1 · Transitions (all `(drawA, drawB, p)`; put the cut point on a mapped hit)

| Technique | Looks like | Source | How | Lib call |
|---|---|---|---|---|
| Match cut | the last shape of shot A becomes a different object in shot B | *2001* bone → satellite; Gondry "Star Guitar" [CBgf2ZxIDZk](https://www.youtube.com/watch?v=CBgf2ZxIDZk) | last 6–8 frames move A's main shape to an anchor (cx, cy, R); B starts from the same R; colour leads by 4 frames; hard cut on the beat | plan in the shot map; `morph(ptsA, ptsB, p)` when the shapes should blend |
| Whip pan | frame is yanked sideways into streaks; the next scene arrives from the streaks | Edgar Wright scene changes ([Hot Fuzz editor interview](https://digitalfilms.wordpress.com/2007/06/16/interview-with-hot-fuzz-editor-chris-dickens/)) | 8–12 frames; travel ≥ 1.2 W; switch where speed peaks; start 2–3 frames before the beat; whoosh → impact | `whipPan(A, B, p, {dir, blur, taps})` |
| Zoom-through | camera dives into a hole (eye, O, screen, door) and the next scene is inside it | Röyksopp "Eple" [IKGfAmzyqYc](https://www.youtube.com/watch?v=IKGfAmzyqYc); Apple fly-through type | scale 1 → 40 with `ein` over 14–18 frames; B fills the hole, no blend; 20% white flash on the last 3 frames | `zoomThrough(A, B, p, {cx, cy, hole})` |
| Iris / shape wipe | the next scene opens inside a growing circle, star, heart or logo | Looney Tunes iris-out; OP circle crops | open with `eox` and close with `ein` over 10–14 frames; centre follows the protagonist; shape = brand mark | `iris(A, B, p, {shape, ring})` |
| Ink bleed | a blob with tendrils spreads and becomes the next scene | Codrops [Liquid Distortion](https://tympanus.net/codrops/2017/10/10/liquid-distortion-effects/); Shadertoy [fluid](https://www.shadertoy.com/view/fdcyzr) | noise-distance mask at 1/6 resolution; 20–28 frames, `eox`; start the bleed on the hit | `inkReveal(A, B, p, {cx, cy, noise})` |
| Shatter | A breaks into shards that fly off; B is behind | Video Copilot [Shatterize](https://www.videocopilot.net/tutorials/shatterize); Blender [Cell Fracture](https://docs.blender.org/manual/en/4.1/addons/object/cell_fracture.html) | the impact front travels outward from the hit point; push 400–900 px; gravity; ±6 rad of spin | `shatter(A, B, p, {cx, cy, cols, rows})` |
| Pixel dissolve | cells flip A → B in random, radial or wipe order | [gl-transitions](https://github.com/gl-transitions/gl-transitions) | cell 12–96 px; 12–20 frames; threshold = hash, distance or brightness | `pixelDissolve(A, B, p, {cell, order})` |
| Paper tear | A rips along a jagged line and the halves pull apart | stop-motion cutout channel ([Vimeo cutouts](https://vimeo.com/channels/cutouts)) | 12–16 frames, `eox`; ±3° per half; 6–10 px white fibre edge | `tear(A, B, p)` |
| Morph | circle → heart, word → icon, colour field → next layout | Chipotle "Back to the Start" (Cannes 2012 Film GP) [vimeo 28355660](https://vimeo.com/28355660) | resample both outlines to 64 points by arc length, align the start, `eio` over 18–24 frames | `morph(ptsA, ptsB, p)` → `smoothPath(pts, true); ctx.fill()` |
| Manga panels | the screen splits into slanted panels that slide in on hits; one panel later takes over the screen | Chainsaw Man OP "KICK BACK" [4MNbX4MRIFQ](https://www.youtube.com/watch?v=4MNbX4MRIFQ); [Spider-Verse (fxguide)](https://www.fxguide.com/fxfeatured/why-spider-verse-has-the-most-inventive-visuals-youll-see-this-year/) | gutters slanted 6–12°, 8–10 px black; one panel per 16th note; the final punch scales one panel to full screen | `panels([{poly, t0, draw, from}], t)` |
| Infinite zoom / Droste | the camera keeps pushing in; each window contains the next scene, forever | Eple; White Stripes "Seven Nation Army"; Shadertoy [Droste](https://www.shadertoy.com/view/Mdf3zM) · [roy.red/posts/droste](http://roy.red/posts/droste/) | ratio 3–6 per level; one level per bar; a linear z feels like one continuous push, and an eased z lurches on each beat | `infiniteZoom(drawLevel, z, {ratio})` |
| Smash cut | quiet or slow, then full and loud in one frame | Apple "1984" | 400–800 ms of hush before; first frame after is full composition, 1–2 white frames, +4–6% scale punch | `flash(t, [tcut])` + `beatCam` |
| Jump cut on beat | the same picture jumps framing on every onset with zero easing | Kendrick Lamar "HUMBLE." [tvTRZJ-4EyI](https://youtu.be/tvTRZJ-4EyI) | camera presets `[{s, r, x, y}]`, index = onset count; a bigger jump every 4 | `lastIdx(within(ON, a, b), t)` → preset |
| Object wipe | a big foreground object crosses the lens; the cut hides behind it | Edgar Wright; common in MVs | 6–10 frames; cut on the frame where the object fully covers the screen; object colour = B's main colour | draw a `rr`/`hero` blocker over `p < .5 ? A : B` |

## 2 · Rhythm devices (feed with `onsets / low_hits / high_hits` from analysis.json)

| Technique | How | Lib call |
|---|---|---|
| Beat camera | zoom punch + tilt on lows, ±8 px jitter on hats; every scene sits inside it | `ctx.save(); beatCam(t, LOW, HIGH); scene(t); ctx.restore()` |
| Speed ramp | change picture time only, leave the music alone: 10× slow-mo, then catch up on the hit | `const ta = speedRamp(t, [[4, 4], [4.5, 4.15], [4.6, 4.9]])` → `withTime(ta, scene)` |
| Stutter / frame hold | A A B A B B at 30 fps to fill the end of a bar; resolves on the next downbeat | `[sceneA, sceneB][stutter(t, t0)]()` |
| Flash frame | 1 white, inverted or black frame on chosen hits only; flashing on every beat kills the effect | `flash(t, BIG, {mode: 'invert'})` |
| On twos / threes | hold poses at 12 or 8 fps for a hand-made feel; main subject on twos, background on ones (Spider-Verse) | `const ta = onTwos(t)` |
| Freeze-frame callout | freeze with contrast 1.2 and saturation 0.7, a doodle circle and a name card for 0.5–0.9 s, then 2 stutters out | `withTime(t0, scene)` + `doodle` + `penText` |

## 3 · AE plug-in looks

| Technique | Looks like | Source | Parameters | Lib call |
|---|---|---|---|---|
| Trapcode Particular | streams of particles swirling in turbulence | [School of Motion tutorials](https://schoolofmotion.com/blog/trapcode-particular-tutorials-after-effects); curl noise [al-ro.github.io/projects/curl](https://al-ro.github.io/projects/curl/) | 300–3000 particles; life 2–4 s; turbulence scale ≈ ¼ screen; size 1 → 0 over life; additive | `curlParticles(t, {n, emit, rate, life, speed, scale, drift})` |
| Trapcode Form → logo | a cloud of points assembles into a word or logo on the drop | [Toolfarm Form](https://www.toolfarm.com/tutorial/tutorial_red_giant_quicktip_15_trapcode_form_city/) | sample step 10–16 px; stagger 0.35; `eox` | `assemble(samplePts(drawLogo, 14), p)` |
| Saber | neon light-sabre stroke with a hot core | [Video Copilot Saber](https://www.videocopilot.net/tutorials/saber_plug-in) · [reSXGxkyr0k](https://www.youtube.com/watch?v=reSXGxkyr0k) | core 4–8 px white; 3 glows at 8/24/64 px; flicker `0.85 + 0.15·hash(floor(t·24))` | `saber(pts, {color, w, glow, prog})` |
| Shine / god rays | light rays streaming from bright parts | [Video Copilot 3D light](https://www.videocopilot.net/blog/2014/02/new-tutorial-3d-light-in-after-effects/) | ray length 0.5–1 screen; 14 steps; decay per step | `shine(layer, x, y, {len, n})` |
| Glow | bloom on highlights | AE Glow; Saber without the plug-in [u7SxaTMgCJQ](https://www.youtube.com/watch?v=u7SxaTMgCJQ) | threshold 0.6–0.75; radii 12/36/96 | `glow(layer, {threshold})` |
| Element 3D extrusion | chunky 3D type or shapes with depth | [Video Copilot Element](https://www.videocopilot.net/tutorials/playlist/element3d/classic_car_3d_text) | depth ≈ 0.2–0.4 of the glyph height; side colour = darker hue of the face; animate depth on the hit | `extrude((c, face) => …, {depth, ang, side})` |
| Echo | ghost trail behind a moving object | [Motion Design School, smears with Echo](https://motiondesign.school/blog/smears-with-echo-effect/) | gap 1/24–1/12 s; 5–14 copies; decay 0.55–0.85 | `echo(drawAt, t, {n, gap, decay})` |
| Time displacement / slit-scan | the image smears in time band by band (the *2001* stargate) | [Toolfarm](https://www.toolfarm.com/tutorial/in-depth-time-effects-time-displacement-aka-slit-scan-with-examples/); [No Film School](https://nofilmschool.com/2016/11/how-to-create-2001-slit-scanning-effect) | lag 0.5–1.6 s across 24–32 bands; works only on things that move | `slitScan(drawAt, t, {bands, lag})` |
| RGB split + block glitch | colour fringes; slices shoved sideways for 3 frames | Shadertoy [VCR distortion](https://www.shadertoy.com/view/ldjGzV), [Fast CRT](https://www.shadertoy.com/view/7d2fzD) | split 4–18 px decaying over 6–10 frames; 3–7 bands of 10–120 px, ±20–180 px | `rgbSplit(glitchLayer, 14 * pulse(LOW, t, 5))`, `glitchSlices(L, pulse(HIGH, t))`, `crt()` |
| Datamosh (fake) | the new shot is dragged along by the old shot's motion | Chairlift "Evident Utensil" [vimeo 3139412](https://vimeo.com/3139412) ([Motionographer](https://motionographer.com/2009/02/19/tintori-and-nabil-breaking-your-internets/)) | freeze B's first frame; move its 32 px blocks with A's motion for 8–20 frames; 25% of blocks held | not in lib (one-off): `drawImage(B, x, y, 32, 32, x + dx·p, y + dy·p, 32, 32)` per block |
| Mosaic | pixelates, then resolves | gl-transitions | cell 64 → 1 with `exio` over 18 frames | `mosaic(layer, size)` |

## 4 · Blender looks, faked in 2D

| Technique | Looks like | Source | Parameters | Lib call |
|---|---|---|---|---|
| Geometry-nodes scatter and grow | hundreds of instances pop in, rippling out from a point | [Distribute Points on Faces](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/point/distribute_points_on_faces.html) | 100–2000 instances; Poisson min distance ≈ 1.1 × size; delay = distance; scale with `eback` | `scatterGrow(p, item, {n, origin, minD})` |
| Toon / cel shading | flat base, hard shadow band, hard highlight, ink outline | [Spiral Atlas toon guide](https://spiralatlas.github.io/a-rough-guide-to-toon-shading-in-blender/) | 2–3 tones; shadow = cooler, more saturated (not black); line 2–6 px | `toonBall(x, y, r, {base, shade, hi, rim, light})`; for any shape, offset a copy away from the light and `destination-out` it to get the shadow crescent |
| Grease Pencil | hand-drawn line living in the scene, tapered, boiling | [NijiGPen](https://github.com/chsh2/nijiGPen); [Grease Pencil channel](https://vimeo.com/channels/greasepencil) | width `sin(πu)^0.6`; boil at 12 fps with 1.5–3 px amplitude; build = trim path | `taper(pts, {w, prog})`, `doodle(...)` |
| Cloth drop | a banner or sheet falls and ripples into place | (no good 2D source; standard strip trick) | 12–24 strips; phase delay per strip; wave 20–60 px decaying; spring landing | `clothDrop(drawSheet, p, {strips, amp})` |
| Cell fracture | see Shatter in §1 | | | `shatter` |

## 5 · Stylised rendering

| Technique | Looks like | Source | Parameters | Lib call |
|---|---|---|---|---|
| Cut paper / craft | layers lifted off the page with shadows, fibre, stop-motion wobble | Chipotle "Back to the Start"; [layered-paper shadows](https://the-lilypad.com/forum/threads/shadow-technique-layered-paper.30516/) | 4–8 layers; shadow offset `4 + z·6`, blur `8 + z·10`; wobble ±1.5 px on twos | `paper(draw, {lift, wobble})` |
| Risograph | two or three ink plates printed off-register, with grain | [Hiromu Oka riso animation](https://www.itsnicethat.com/articles/hiromu-oka-hodo-station-process-animation-051222); Spider-Verse off-register depth | fluo pink `#FF48B0`, blue `#0078BF`, yellow `#FFE800`; offset 2 → 10 px on the hit | `riso(draw, {inks, off})` |
| Ordered dither | limited palette in Bayer dots (Obra Dinn, Game Boy) | [Surma, Ditherpunk](https://surma.dev/things/ditherpunk/); [Obra Dinn dither notes](https://forums.tigsource.com/index.php?topic=40832) | cell 3–6 px; 2–4 tones; 2-colour palette `#1a1b26 / #e8e0c8` | `dither(layer, {palette, px})` |
| Halftone variants | CMYK dots off-register; line screen; star or heart dots; a dot-size wipe | (existing `halftone`) | angles 15/75/0/45°; misregister 2–4 px | `halftone(...)` with `curve`, `ang` |
| Watercolour | soft, darker-edged washes | [Tyler Hobbs, watercolour](https://www.tylerxhobbs.com/words/a-guide-to-simulating-watercolor-paint-with-generative-art) | 30–100 layers at alpha 0.02–0.05; deform recursively about 5 times | `watercolor(cx, cy, r, color, {layers})` |
| Pencil / crayon hatching | tone built from 1–3 hatch directions | [Kyle Halladay, pencil sketch](https://kylehalladay.com/blog/tutorial/2017/02/21/Pencil-Sketch-Effect.html) | gap 6–10 px; 45° first, extra directions as it darkens; lines boil | `hatch(layer, {gap, angles})` |
| ASCII / decode | the image drawn in glyphs that scramble until they lock | [codrops-ascii-ogl](https://github.com/andrico1234/codrops-ascii-ogl) | cell 10–18 px; ramp `" .:-=+*#%@"`; decode = unlock order by hash | `ascii(layer, {cell, decode})` |
| Japanese OP title card | huge vertical heavy-serif type in black, red and cream, stamped in | Chainsaw Man OP; Jujutsu Kaisen OP1 | type height ≈ 70% of the screen; only `#0a0a0a / #d6001c / #f2efe6`; scale 1.4 → 1 over 6 frames + 1 white frame; add grain | `tategaki(text, x, y, size, {t0})` |
| Oversized cropped type | a letter so big only part of it shows; type becomes pure graphics | anime OPs, Spotify Wrapped | 1.5–3.5 × screen height; anchor off-screen; +3% on every beat | `ctx.font = SANS(900, H * 2.6)` |
| Kinetic letters | each letter pops with squash and stretch; font and colour swap on beats | Codrops [stagger reveal](https://tympanus.net/codrops/2020/06/17/making-stagger-reveal-animations-for-text/) | 1/16 note per letter; `scaleY` 1.35 → 0.85 → 1; 3–4 fonts that differ a lot in width | the `film.js` slam pattern; `textOnPath` for text on a curve |
| Film damage | scratches, dust, warm light leak | generic film overlay | 2 scratches every 2 frames; 6–14 dust specks; leak `#ff7a2a` +15% on hits | `filmDamage(t, {leak, hits})`, `grain` |
| Collage | torn photos, tape, doodle circles, mixed media slapped on each beat | Bocchi the Rock OP | ±8° rotation; torn edge 20–40 points ±4 px; tape `rgba(240,225,170,.6)`; slap scale 1.15 → 1 over 4 frames | `photoCard` + torn-poly clip + `doodle` |

## 6 · Structural surprises (the edit itself is the idea)

Pick at least one for any launch or brand film. Write it into the shot map as a row of its own:
1. **Fake ending:** at about 70%, play a full end card with logo, line and silence. After 1.5 s a small element (the dot in the logo, a comma) moves and pulls out act two, which shows the real feature.
2. **The UI takes over:** after 60% of the film in an MG world, a UI element zooms through (`zoomThrough`) to fill the screen, and the film continues inside the real product. Reference: Tubi "Interface Interruption", [Wikipedia](https://en.wikipedia.org/wiki/Interface_Interruption) (borrow the structure, not the execution).
3. **The viewer thinks it's broken:** glitch, freeze or a buffering spinner mid-film. Within 2 s the product fixes it, or the glitch turns out to be the doorway to the next scene. Keep one element stable so the error reads as intentional.
4. **Fourth wall:** the protagonist sees the captions and pushes them, stands on them or counts the beat in.
5. **Chain reaction:** every event is the physical result of the one before. Lock every link to the beat grid and land the last link on the biggest hit, which is also the logo. References: OK Go "This Too Shall Pass" [qybUFnY7Y8w](https://www.youtube.com/watch?v=qybUFnY7Y8w), Gondry "Star Guitar".
