# Art forms: 82 looks for animated video, and how to build each

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
| [Pop-up book](art-forms/pop-up-book.md) | An open book seen at an angle: the pages swing open and layered card pieces stand up off them, each with a fold shadow, a visible card edge and a shadow on the page. | smooth, full frame rate | HyperFrames (canvas), Blender for real folded paper |
| [Papercut and sanjhi (lace-cut paper)](art-forms/papercut.md) | One colour of cut paper on a plain ground: a scalloped medallion and corner pieces full of symmetrical cut-outs, with a soft shadow that shows the paper is a layer above the page. | steps 8 times a second | HyperFrames (canvas or SVG) |
| [Brick toy](art-forms/brick-toy.md) | Everything built from studded plastic bricks on a green baseplate: visible studs, a glossy edge, flat bright colours, and bricks that drop in one at a time on twos. | steps 12 times a second | HyperFrames (canvas), Blender for glossy plastic |
| [String puppet and kathputli](art-forms/string-puppet.md) | Marionettes in bright Rajasthani dress: big painted wooden heads, turbans and ghagras, strings to a control bar at the top, jerky dangling motion, in a small theatre with red curtains and a gold valance. | steps 8 times a second | HyperFrames (canvas or SVG) |

## Drawn and painted

| Art form | What it is | Cadence | Usual tool |
|---|---|---|---|
| [Anime and cel shading](art-forms/cel-shaded.md) | Light broken into two or three flat tones with a hard edge between them, and an ink outline around every form. | steps 12 times a second | Three.js inside HyperFrames |
| [2D flat vector explainer](art-forms/flat-explainer.md) | The plain explainer look: flat fills, a few colours, simple shapes and icons, smooth eased motion. | smooth, full frame rate | HyperFrames (DOM, SVG) |
| [Whiteboard and doodle](art-forms/whiteboard.md) | Marker lines that draw themselves on a white board, in the order someone would draw them: simple diagrams and a few handwritten words, one accent colour. | steps 10 times a second | HyperFrames (canvas or SVG) |
| [Watercolour](art-forms/watercolour.md) | Transparent washes on textured paper: colour that spreads, pools darker at its edge, and lets the paper show through. | steps 12 times a second | HyperFrames (canvas or SVG) |
| [Ink wash (sumi-e)](art-forms/ink-wash.md) | Black ink in every shade from deep black to pale grey, laid down in tapered brush strokes on rice paper, with a great deal left empty. | steps 12 times a second | HyperFrames (canvas or SVG) |
| [Line art](art-forms/line-art.md) | One weight of line on a plain ground, no shading: the drawing draws itself, then quivers slightly as if redrawn each frame. | steps 10 times a second | HyperFrames (SVG or canvas) |
| [Rotoscope look](art-forms/rotoscope.md) | Real movement traced by hand: lifelike motion, flat colour fields that drift, and an outline that shimmers. | steps 12 times a second | HyperFrames (canvas over video) |
| [Motion comic](art-forms/motion-comic.md) | Comic panels brought to life: layers inside a panel slide at different speeds under a slow camera move, then a hard cut to the next panel. | smooth, full frame rate | HyperFrames (DOM or canvas) |
| [UPA and mid-century modern](art-forms/upa-midcentury.md) | Flat, stylised design from 1950s cartoons: geometric characters, abstract backgrounds, colour printed slightly off its outline, and very few drawings. | steps 8 times a second | HyperFrames (canvas, SVG) |
| [Rubber-hose cartoon](art-forms/rubber-hose.md) | The 1920s cartoon: limbs like hoses with no elbows or knees, round bodies that bounce to the music, black and white film. | steps 12 times a second | HyperFrames (canvas, SVG) |
| [Linocut and woodcut print](art-forms/linocut.md) | A relief print: bold flat shapes in one to three inks, with white gouge marks where the block was carved. | steps 8 times a second | HyperFrames (canvas, SVG) |
| [Pencil sketch](art-forms/pencil-sketch.md) | Graphite lines on toothed paper: thin hatching that builds tone, a doubled and searching outline, and a thumb-smudged shadow. | steps 8 times a second | HyperFrames (canvas or SVG) |
| [Charcoal](art-forms/charcoal.md) | Soft black dust smeared and rubbed on rough paper: dark masses with crumbling edges, greys made by rubbing, and highlights lifted out with an eraser. | steps 8 times a second | HyperFrames (canvas) |
| [Oil painting and impasto](art-forms/oil-painting.md) | Thick oil paint laid in visible, directional brush strokes: colour mixed on the canvas, strokes that follow the shape of the thing, and raised light ridges where the paint is heaped up. | steps 12 times a second | HyperFrames (canvas) |
| [Gouache storybook](art-forms/gouache.md) | Flat, matte, opaque layers of paint with hand-cut edges and faint brush streaks: the look of a printed picture book. | steps 8 times a second | HyperFrames (canvas or SVG) |
| [Crayon and oil pastel](art-forms/crayon.md) | Waxy, broken strokes of bright colour on toothed paper, scribbled in one slanted direction with fat outlines pushed past the edges. | steps 8 times a second | HyperFrames (canvas) |
| [Chalkboard](art-forms/chalkboard.md) | White and coloured chalk on a dark green-black board: dusty, broken lines that draw themselves, ghosts of old eraser swipes, and a stub of chalk at the tip of each line. | steps 10 times a second | HyperFrames (canvas or SVG) |
| [One continuous line](art-forms/one-line.md) | A whole subject drawn by one unbroken line on a flat colour: the pen never lifts, crosses itself where it must, and the finished drawing is a single curve. | smooth, full frame rate | HyperFrames (SVG or canvas) |
| [Paint-on-glass](art-forms/paint-on-glass.md) | Oil paint smeared on a lit sheet of glass: translucent colour that glows against the light, deeper where it is thick, finger streaks dragged behind, and shapes that melt from one thing into the next. | steps 12 times a second | HyperFrames (canvas) |
| [Sand animation](art-forms/sand-art.md) | A light table seen from above: a warm glowing backlight, sand as dark sepia masses, and light showing through wherever the sand is thin, with soft graded edges. | steps 12 times a second | HyperFrames (canvas) |
| [Retro anime (80s and 90s)](art-forms/retro-anime.md) | A hand-painted television look: hard two-tone shading, banded sunset skies, a striped sun, a lit skyline, a figure from behind with hair and scarf in the wind, a little film grain and a soft glow. | steps 8 times a second | HyperFrames (canvas), or Blender with a toon material for 3D |
| [Manga (black and white with screentone)](art-forms/manga.md) | Black and white only: inked panels with thick borders, screentone dots for grey, speed lines and bursts, and one dramatic moment drawn large. | steps 8 times a second | HyperFrames (canvas or SVG) |
| [Chibi](art-forms/chibi.md) | A character two or three heads tall: a huge head, a tiny body, big shiny eyes, rosy cheeks and a bounce with a real squash and stretch. | steps 12 times a second | HyperFrames (canvas or SVG) |
| [Modern TV cartoon](art-forms/tv-cartoon.md) | Thick, even outlines and flat, bright colour on simple geometric characters: squares, circles and triangles with big eyes, bouncing on twos against a plain, flat background. | steps 12 times a second | HyperFrames (canvas or SVG) |
| [Gothic cartoon](art-forms/gothic-cartoon.md) | Spindly, hollow-eyed figures and crooked houses with lit windows under a pale moon, curly trees and bats, in purple and black: a cartoon that is spooky and funny at once. | steps 8 times a second | HyperFrames (canvas or SVG) |

## Geometry, pixels and 3D

| Art form | What it is | Cadence | Usual tool |
|---|---|---|---|
| [Isometric](art-forms/isometric.md) | A parallel projection seen from above at an angle: no perspective, three visible faces per block, a tidy model world. | smooth, full frame rate | HyperFrames (canvas, SVG) or Three.js |
| [Low-poly 3D](art-forms/low-poly.md) | Meshes with few polygons, each face lit as one flat facet. | smooth, full frame rate | Three.js inside HyperFrames |
| [Voxel](art-forms/voxel.md) | Everything built from cubes of one size on a grid, like a three-dimensional pixel picture. | steps 12 times a second | Three.js inside HyperFrames |
| [Pixel art](art-forms/pixel-art.md) | A tiny picture placed pixel by pixel and scaled up with hard edges: a few colours, no blur, sprites that step. | steps 8 times a second | HyperFrames (canvas) |
| [3D product render](art-forms/product-render.md) | A studio shot of an object: a seamless backdrop, soft key, fill and rim lights, controlled reflections, a slow turn. | smooth, full frame rate | Three.js, the 3D pack, or Blender |
| [Stylised 3D cartoon](art-forms/stylised-3d.md) | A soft, rounded 3D cartoon character or prop with a big readable face: smooth forms, a soft key light, a cool rim light and warm light that seems to pass through the skin. | smooth, full frame rate | Three.js inside HyperFrames, or Blender |
| [Toon 3D (cel-shaded, comic-book)](art-forms/toon-3d.md) | 3D forms cut into two or three flat shading bands, with a thick ink outline on every silhouette and a printed, painterly comic-book feel. | smooth, full frame rate | Three.js inside HyperFrames, or Blender (Freestyle) |
| [Point cloud and lidar scan](art-forms/point-cloud.md) | An object or scene made of thousands of glowing points on black, in blue and gold, turning slowly, with points that fade and shrink as they recede. | smooth, full frame rate | Three.js inside HyperFrames |
| [Tilt-shift miniature diorama](art-forms/diorama.md) | A tiny town seen from a high camera: saturated toy colours, little cars looping round the roads, and a blur that grows toward the top and bottom of the frame, so that it looks like a model. | smooth, full frame rate | Three.js inside HyperFrames, or Blender |
| [Parallax 2.5D](art-forms/parallax-2-5d.md) | Four to six flat painted layers moving at different speeds as the camera pans: a sky, far mountains, hills, a row of trees, a field and grass in front, so that a flat scene feels deep. | smooth, full frame rate | HyperFrames (canvas or Three.js) |

## Type, data and retro

| Art form | What it is | Cadence | Usual tool |
|---|---|---|---|
| [Kinetic typography](art-forms/kinetic-type.md) | Moving words as the whole picture: scale, weight and timing carry the meaning. | smooth, full frame rate | HyperFrames (DOM) |
| [Infographic and data animation](art-forms/infographic.md) | A chart that builds in a sensible order: axes, then the data from an honest baseline, then the exact values. | smooth, full frame rate | HyperFrames (SVG, canvas) |
| [Lyric video](art-forms/lyric-video.md) | The words of a song as the main image, each line timed to the vocal and the active word lit. | smooth, full frame rate | HyperFrames (DOM, canvas) |
| [VHS and glitch](art-forms/vhs-glitch.md) | The damage of old tape and broken data: colour that bleeds sideways, scan lines, a band of noise at the bottom, sudden torn slices. | steps 30 times a second | HyperFrames (canvas) or Three.js post-processing |
| [Blueprint and technical drawing](art-forms/blueprint.md) | White lines on blue: a grid, an object drawn in outline, centre lines, dimensions and a title block. | smooth, full frame rate | HyperFrames (SVG, canvas) |
| [Neon sign](art-forms/neon-sign.md) | Glass tubes bent into letters and lit: a bright core, a coloured glow, a dark wall, tubes that light one by one and sometimes flicker. | steps 24 times a second | HyperFrames (canvas, SVG) |
| [Maths diagram](art-forms/math-diagram.md) | A chalk-on-navy maths explainer: an equation builds term by term, each term in its own colour with its own curve on the plot, then the sum curve draws on and a tangent line slides along it with its slope read out. | smooth, full frame rate | HyperFrames (canvas), or Manim for real maths |
| [Sticker explainer](art-forms/sticker-explainer.md) | Die-cut stickers with a thick white border and a drop shadow pop onto a desk with a bounce: icons and bold word stickers, each tilted a little and swaying. | smooth, full frame rate | HyperFrames (canvas or SVG) |
| [Memphis design](art-forms/memphis.md) | Scattered, playful confetti in the manner of 1980s Memphis design: squiggles and zigzags, triangles, circles and half-circles in red, yellow, blue and pink, black-and-white checks, stripes and dots. | steps 12 times a second | HyperFrames (canvas or SVG) |

## Folk and print traditions

| Art form | What it is | Cadence | Usual tool |
|---|---|---|---|
| [Madhubani (Mithila)](art-forms/madhubani.md) | Double black outlines round bright flat fills, with every gap packed with hatching, dots or small motifs: fish, peacocks and lotuses inside a decorated border, with no empty space. | steps 8 times a second | HyperFrames (canvas or SVG) |
| [Warli](art-forms/warli.md) | White figures drawn in simple shapes on a terracotta wall: a circle for a head, two triangles joined at their tips for a body, stick arms and legs, a ring of people dancing hand in hand round a tarpa player, trees, huts and a sun. | steps 8 times a second | HyperFrames (canvas or SVG) |
| [Pattachitra](art-forms/pattachitra.md) | Bold black outlines and flat colour on a prepared ground: a thick ornamental border, an almond eye in profile, scale and fin patterns, and flowers and tendrils packed round the subject. | steps 8 times a second | HyperFrames (canvas or SVG) |
| [Gond](art-forms/gond.md) | Animals and trees in thin black outline, filled with bold flat colour in bands, each band carrying fine repeated marks of one colour: dots, dashes, parallel lines or fish-scale arcs. | steps 8 times a second | HyperFrames (canvas or SVG) |
| [Indian miniature (Mughal and Rajput)](art-forms/indian-miniature.md) | A small, richly detailed court painting in jewel tones: a flat, stacked space with no deep perspective, a gold border with a floral margin, fine ornament on every surface, and figures in profile. | steps 8 times a second | HyperFrames (canvas or SVG) |
| [Engraving and banknote hatching](art-forms/engraving.md) | Fine lines cut like a burin: hatching that follows the form and swells in the shadow, cross-hatching where it is darkest, a vignette of waves, and a woven guilloche frame, in one or two inks on cream paper. | smooth, full frame rate | HyperFrames (canvas) |
| [Silkscreen poster](art-forms/silkscreen.md) | A poster printed in a few flat inks that overprint, each a little out of register, with coarse halftone dots for tone: flat shapes, big blocks, and colours that mix where they overlap. | steps 8 times a second | HyperFrames (canvas) |
| [Art deco](art-forms/art-deco.md) | Gold lines, sunbursts and stepped, symmetric geometry on a deep ground: fans and arcs, a tower in steps, zigzag borders and small stars, in gold on navy and burgundy. | smooth, full frame rate | HyperFrames (canvas or SVG) |
| [Stained glass](art-forms/stained-glass.md) | Coloured panes held by thick dark lead lines in an arched window: a rose at the top, a diamond lattice below, and light glowing through each pane. | smooth, full frame rate | HyperFrames (canvas) |
| [Ukiyo-e woodblock](art-forms/ukiyo-e.md) | A Japanese woodblock print: flat areas of colour, fine ink outlines, a great curling wave of deep blue with claw-like fingers of foam, a pale banded sky, a small distant mountain and a red seal. | steps 8 times a second | HyperFrames (canvas or SVG) |

## Screens and cinema

| Art form | What it is | Cadence | Usual tool |
|---|---|---|---|
| [Synthwave and outrun](art-forms/synthwave.md) | A neon night in magenta and cyan on deep purple: a striped sun sinking behind wireframe mountains, and a glowing grid floor that streams toward the horizon. | smooth, full frame rate | HyperFrames (canvas or Three.js) |
| [Cyberpunk night city](art-forms/cyberpunk.md) | A rainy night street in purple and amber: towers hung with flickering neon signs, a wet road that mirrors them, rain and ripples, and a lone figure under an umbrella. | steps 12 times a second | HyperFrames (canvas or Three.js) |
| [ASCII art](art-forms/ascii.md) | A scene drawn only from monospaced text characters chosen by brightness: a sunrise over a sea and a headland, with waves, glitter and birds that move. | steps 12 times a second | HyperFrames (canvas) |
| [1-bit dither](art-forms/dither-1bit.md) | Two colours only, ink and paper: gradients and shaded forms turned into patterns of pure dots, in a window with a striped title bar, like an early desktop computer. | steps 12 times a second | HyperFrames (canvas), or a Three.js post-process |
| [CRT terminal](art-forms/crt-terminal.md) | An amber phosphor terminal: text typed one character at a time, a block cursor, scanlines, glow, a slow rolling bar, and a screen that bulges at the middle. | steps 24 times a second | HyperFrames (canvas) |
| [Hologram HUD](art-forms/hologram-hud.md) | A cyan and blue wireframe turning in the dark, with readouts, bars, a dial, corner brackets, a scan band and a flicker with an occasional slipped strip. | steps 24 times a second | HyperFrames (canvas or Three.js) |
| [Thermal camera](art-forms/thermal.md) | A false-colour heat map through black, purple, red, orange, yellow and white: a hot head and hands, a warm mug, a cold window, a crosshair, a temperature readout and a colour scale. | steps 12 times a second | HyperFrames (canvas) |
| [Silent film](art-forms/silent-film.md) | Black and white at about 18 frames a second: grain, scratches, a wandering gate, flicker, an iris that opens and closes on a street scene, and an intertitle card with a framed title. | steps 18 times a second | HyperFrames (canvas), or ffmpeg filters on real footage |
| [Newsreel](art-forms/newsreel.md) | Sepia footage of the 1940s: a train racing past telegraph poles, a slanted headline banner, and a damaged print with scratches, hairs, dust, a burn flash and a jolt of the frame. | steps 18 times a second | HyperFrames (canvas), or ffmpeg filters on real footage |
| [Film noir](art-forms/film-noir.md) | High-contrast black and white: a wall striped by light through venetian blinds, a man in a fedora and trench coat under a street lamp, rain slanting through the lamp's cone, and a wet pavement. | smooth, full frame rate | HyperFrames (canvas), or Blender for a lit 3D scene |
| [Archive documentary: pan and zoom over stills](art-forms/archive-documentary.md) | A slow pan and zoom over still photographs laid on a desk, each with a white border and a shadow, with a lower-third caption and date that slide in for each picture, over film grain. | smooth, full frame rate | HyperFrames (canvas or CSS transforms) |

## Abstract and generative

| Art form | What it is | Cadence | Usual tool |
|---|---|---|---|
| [Particles](art-forms/particles.md) | Thousands of small glowing particles drift in from all over the frame and settle into a word, hold it, then burst apart and reform. | smooth, full frame rate | HyperFrames (canvas) or Three.js |
| [Liquid metaball (blobs that merge)](art-forms/liquid-metaball.md) | Glossy liquid blobs that drift, merge and split: a smooth colour gradient from warm to violet, a bright rim, and a soft highlight on each blob. | smooth, full frame rate | HyperFrames (canvas or WebGL shader) |
| [Flow-field generative](art-forms/flow-field.md) | Thousands of short strokes follow a drifting noise field and gather into an orb of swirling lines, in warm and violet inks on a dark ground. | smooth, full frame rate | HyperFrames (canvas) |
| [Psychedelic](art-forms/psychedelic.md) | A 1960s concert-poster look: concentric rings warped by slow waves in a cycling run of warm, saturated colours, with black ink lines over rays that turn behind them. | smooth, full frame rate | HyperFrames (canvas or WebGL shader) |
| [Bauhaus geometric](art-forms/bauhaus.md) | A poster of primary-colour circles, squares and triangles with black bars on a grid of cream and black lines, where every piece jumps from cell to cell in clean steps. | steps 12 times a second | HyperFrames (canvas or SVG) |

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

The files listed in `art-forms/looks-files.json` (`looks.js` and one file per later batch) hold one small demo per look (82 in all), and `art-forms/gallery.html` plays them. `tests/art_forms/check_looks.mjs` checks every one in a real browser.
These pages are generated from `references/art-forms.json` and those demo files by `scripts/build_art_forms.py`.
