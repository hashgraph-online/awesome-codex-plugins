# Art forms: 30 looks for animated video, and how to build each

Read this when a brief names a look ("claymation", "paper cut-out", "anime", "like a blueprint") or describes a feeling that a look would carry. It is the index. Each art form has its own page in `references/art-forms/` with its visual rules, timing, build recipe, assets, sound, pitfalls, sources and a tested demo. `scripts/art_route.py BRIEF.md` proposes one from a brief and says why.

An art form sets the look and the timing. The format (`references/formats.md`) still sets the beats, and the tool table in SKILL.md still sets the route.

## Three rules behind every look

1. **The picture is a function of time.** No clock, no timers, no `Math.random()`. HyperFrames renders by seeking, so anything that depends on the frame before it will be wrong. Randomness comes from a hash of the frame number or of a position.
2. **Handmade looks hold their drawings.** Clay, paper, felt, cel and ink change 8 to 12 times a second while the video stays at 24 or 30. Quantise time before posing anything: `const ts = Math.floor(t * 12) / 12`. In GSAP the same thing is `ease: "steps(12)"` on a one-second tween. Clean looks (flat explainer, low-poly, product render, type) stay smooth.
3. **Imperfection is seeded.** Line boil, paper jitter, lamp flicker, misregistered ink and tape damage are all keyed to the drawing number, so two renders of the same frame match exactly.

A `setInterval` that re-rolls a filter, the usual web recipe for line boil, breaks rule 1 and will not render correctly. Key the change to `Math.floor(t * 10)` instead.

## Craft and handmade

| Art form | What it is | Cadence | Usual tool |
|---|---|---|---|
| [Claymation](art-forms/claymation.md) | Figures of clay or plasticine, posed and photographed one frame at a time. | steps 12 times a second | Three.js inside HyperFrames |
| [Stop-motion look](art-forms/stop-motion.md) | Any real object moved and photographed a pose at a time. | steps 12 times a second | HyperFrames (canvas or DOM) or Three.js |
| [Paper cut-out](art-forms/paper-cutout.md) | Flat shapes cut from paper or card, layered, and moved a pose at a time. | steps 12 times a second | HyperFrames (canvas, SVG or DOM) |
| [Felt and fabric craft](art-forms/felt.md) | Shapes that look needle-felted or sewn: a fuzzy edge of loose fibres, a matte mottled surface, visible stitches. | steps 12 times a second | HyperFrames (canvas or SVG) |
| [Origami](art-forms/origami.md) | Paper folded from a flat sheet: sharp creases, flat facets, each fold a clean move followed by a pause. | smooth, full frame rate | HyperFrames (canvas or SVG), or Three.js |
| [Shadow puppetry](art-forms/shadow-puppet.md) | Flat figures held between a lamp and a cloth screen: dark silhouettes with punched patterns on a warm, glowing field. | steps 12 times a second | HyperFrames (canvas or SVG) |
| [Collage and mixed media](art-forms/collage.md) | Pieces of different papers, photographs and print stuck together: mismatched scale and texture, torn edges, hard shadows. | steps 8 times a second | HyperFrames (canvas or DOM) |
| [Risograph and halftone print](art-forms/risograph.md) | The look of a cheap stencil print: two to four bright inks laid over each other, visible grain, dot screens, and layers that never quite line up. | steps 8 times a second | HyperFrames (canvas or DOM) |

## Drawn and painted

| Art form | What it is | Cadence | Usual tool |
|---|---|---|---|
| [Anime and cel shading](art-forms/cel-shaded.md) | Light broken into two or three flat tones with a hard edge between them, and an ink outline around every form. | steps 12 times a second | Three.js inside HyperFrames |
| [2D flat vector explainer](art-forms/flat-explainer.md) | The plain explainer look: flat fills, a few colours, simple shapes and icons, smooth eased motion. | smooth, full frame rate | HyperFrames (DOM, SVG) |
| [Whiteboard and doodle](art-forms/whiteboard.md) | Marker lines that draw themselves on a white board, in the order someone would draw them. | steps 10 times a second | HyperFrames (canvas or SVG) |
| [Watercolour](art-forms/watercolour.md) | Transparent washes on textured paper: colour that spreads, pools darker at its edge, and lets the paper show through. | steps 12 times a second | HyperFrames (canvas or SVG) |
| [Ink wash (sumi-e)](art-forms/ink-wash.md) | Black ink in every shade from deep black to pale grey, laid down in tapered brush strokes on rice paper, with a great deal left empty. | steps 12 times a second | HyperFrames (canvas or SVG) |
| [Line art](art-forms/line-art.md) | One weight of line on a plain ground, no shading: the drawing draws itself, then quivers slightly as if redrawn each frame. | steps 10 times a second | HyperFrames (SVG or canvas) |
| [Rotoscope look](art-forms/rotoscope.md) | Real movement traced by hand: lifelike motion, flat colour fields that drift, and an outline that shimmers. | steps 12 times a second | HyperFrames (canvas over video) |
| [Motion comic](art-forms/motion-comic.md) | Comic panels brought to life: layers inside a panel slide at different speeds under a slow camera move, then a hard cut to the next panel. | smooth, full frame rate | HyperFrames (DOM or canvas) |
| [UPA and mid-century modern](art-forms/upa-midcentury.md) | Flat, stylised design from 1950s cartoons: geometric characters, abstract backgrounds, colour printed slightly off its outline, and very few drawings. | steps 8 times a second | HyperFrames (canvas, SVG) |
| [Rubber-hose cartoon](art-forms/rubber-hose.md) | The 1920s cartoon: limbs like hoses with no elbows or knees, round bodies that bounce to the music, black and white film. | steps 12 times a second | HyperFrames (canvas, SVG) |
| [Linocut and woodcut print](art-forms/linocut.md) | A relief print: bold flat shapes in one to three inks, with white gouge marks where the block was carved. | steps 8 times a second | HyperFrames (canvas, SVG) |

## Geometry, pixels and 3D

| Art form | What it is | Cadence | Usual tool |
|---|---|---|---|
| [Isometric](art-forms/isometric.md) | A parallel projection seen from above at an angle: no perspective, three visible faces per block, a tidy model world. | smooth, full frame rate | HyperFrames (canvas, SVG) or Three.js |
| [Low-poly 3D](art-forms/low-poly.md) | Meshes with few polygons, each face lit as one flat facet. | smooth, full frame rate | Three.js inside HyperFrames |
| [Voxel](art-forms/voxel.md) | Everything built from cubes of one size on a grid, like a three-dimensional pixel picture. | steps 12 times a second | Three.js inside HyperFrames |
| [Pixel art](art-forms/pixel-art.md) | A tiny picture placed pixel by pixel and scaled up with hard edges: a few colours, no blur, sprites that step. | steps 8 times a second | HyperFrames (canvas) |
| [3D product render](art-forms/product-render.md) | A studio shot of an object: a seamless backdrop, soft key, fill and rim lights, controlled reflections, a slow turn. | smooth, full frame rate | Three.js, the 3D pack, or Blender |

## Type, data and retro

| Art form | What it is | Cadence | Usual tool |
|---|---|---|---|
| [Kinetic typography](art-forms/kinetic-type.md) | Moving words as the whole picture: scale, weight and timing carry the meaning. | smooth, full frame rate | HyperFrames (DOM) |
| [Infographic and data animation](art-forms/infographic.md) | A chart that builds in a sensible order: axes, then the data from an honest baseline, then the exact values. | smooth, full frame rate | HyperFrames (SVG, canvas) |
| [Lyric video](art-forms/lyric-video.md) | The words of a song as the main image, each line timed to the vocal and the active word lit. | smooth, full frame rate | HyperFrames (DOM, canvas) |
| [VHS and glitch](art-forms/vhs-glitch.md) | The damage of old tape and broken data: colour that bleeds sideways, scan lines, a band of noise at the bottom, sudden torn slices. | steps 30 times a second | HyperFrames (canvas) or Three.js post-processing |
| [Blueprint and technical drawing](art-forms/blueprint.md) | White lines on blue: a grid, an object drawn in outline, centre lines, dimensions and a title block. | smooth, full frame rate | HyperFrames (SVG, canvas) |
| [Neon sign](art-forms/neon-sign.md) | Glass tubes bent into letters and lit: a bright core, a coloured glow, a dark wall, tubes that light one by one and sometimes flicker. | steps 24 times a second | HyperFrames (canvas, SVG) |

## Choosing one from a brief

| The brief is about | Try | Why |
|---|---|---|
| children, family, a gentle story | paper cut-out, claymation, felt | handmade textures feel warm and safe |
| a folk tale, a myth, heritage | shadow puppetry, linocut, ink wash | the form carries the tradition; check the iconography with a source |
| explaining a product or a process | flat vector explainer, isometric, whiteboard | clean shapes keep attention on the idea |
| numbers | infographic | the chart is the picture; every number needs a source |
| a song or a quote | lyric video, kinetic typography | the words are the content |
| a physical product | 3D product render, claymation for a playful take | the object is the hero |
| nostalgia | VHS and glitch, pixel art, rubber-hose, UPA mid-century | each one is a decade |
| calm, reflective | watercolour, ink wash, line art | slow, sparse, quiet |
| loud, independent | risograph, collage, motion comic | print energy and hard cuts |

If the brief names a look, use it. If it names none and nothing above fits, do not force one: the plain formats in `references/formats.md` are a look too.

## Tools that exist, by name

- SVG filters: `feTurbulence` (noise), `feDisplacementMap` (bend by noise: rough edges, line boil, ink bleed), `feMorphology` (thicken or thin: outlines), `feColorMatrix` and `feComponentTransfer` (recolour, threshold, duotone), `feGaussianBlur`.
- CSS: `steps()` timing, `mix-blend-mode: multiply` for overprinted ink and `screen` or `plus-lighter` for glow, `image-rendering: pixelated`, `filter: drop-shadow()`.
- GSAP: `ease: "steps(n)"`; `fromTo` inside scenes; one paused root timeline.
- three.js materials and passes that ship in its examples: `MeshToonMaterial` with a `gradientMap`, `OutlineEffect`, `SobelOperatorShader`, `HalftonePass`, `RenderPixelatedPass`, `FilmPass`, `RGBShiftShader`, `GlitchPass`, `UnrealBloomPass`, `OutputPass`. It ships no watercolour (Kuwahara) pass and no VHS pass.
- Blender does these better than a browser: real subsurface clay, fur and felt fibre, folded paper with thickness, photoreal product shots, Freestyle line art.

## Repositories studied

Each was cloned outside this repository and its licence file was read first. No code from any of them is copied here; the demos were written for this skill. Licences as written in each repo on 17 Nov 2026.

| Repo | Licence | What it taught |
|---|---|---|
| [mrdoob/three.js](https://github.com/mrdoob/three.js) | MIT | which toon, outline, halftone, pixel, film and glitch files really ship in its examples, and how its toon example builds a gradient map |
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | Apache-2.0 | the seek rules that every look obeys: no clock, no unseeded randomness, time as the only input |
| [pmndrs/postprocessing](https://github.com/pmndrs/postprocessing) | Zlib | the effects it offers for print, pixel, scan-line and glitch looks |
| [pmndrs/drei](https://github.com/pmndrs/drei) | MIT | helper patterns for outlines and toon materials in React Three Fiber |
| [paper-design/shaders](https://github.com/paper-design/shaders) | Apache-2.0 | paper texture, halftone and dithering as shaders; a source to reach for when a look needs more than a canvas |
| [rough-stuff/rough](https://github.com/rough-stuff/rough) | MIT | sketchy shapes and hachure fills for whiteboard and line-art looks |
| [pixijs/filters](https://github.com/pixijs/filters) | MIT | which artefacts make a CRT, old-film or glitch filter convincing |
| [amandaghassaei/OrigamiSimulator](https://github.com/amandaghassaei/OrigamiSimulator) | MIT | folding from crease patterns, for origami beyond a few folds |
| [danielesteban/cubitos](https://github.com/danielesteban/cubitos) | MIT | voxel rendering in three.js |
| [motion-canvas/motion-canvas](https://github.com/motion-canvas/motion-canvas) | MIT | another code-first animation tool; how it structures time |
| [ykob/sketch-threejs](https://github.com/ykob/sketch-threejs) | MIT | a gallery of shader sketches |
| [mattatz/THREE.Watercolor](https://github.com/mattatz/THREE.Watercolor) | MIT (2015) | an older watercolour shader; too dated to build on |
| [remotion-dev/remotion](https://github.com/remotion-dev/remotion) | Remotion licence (a company licence above a size) | read only, for how its examples stage looks |
| [nidorx/matcaps](https://github.com/nidorx/matcaps) | no licence file | read only: a matcap gives a quick clay look, but these images cannot be reused, so the clay demo uses a rough material and a generated bump map |

## The demos

`art-forms/looks.js` holds one small demo per look (31 in all), and `art-forms/gallery.html` plays them. `tests/art_forms/check_looks.mjs` checks every one in a real browser.
These pages are generated from `references/art-forms.json` and `art-forms/looks.js` by `scripts/build_art_forms.py`.
