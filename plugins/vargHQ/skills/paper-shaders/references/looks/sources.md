# Sources: paper-shaders family (11 shader backgrounds)

Every URL below was opened in this research session (X posts through the X API, pages through WebFetch or curl).
Numbers are shared by all files in `references/` and `assets/presets/`.

Template slugs: `liquid-metal-field` (LM), `god-ray-light-field` (GR), `mesh-gradient-grain` (MG),
`grain-gradient-shapes` (GG), `dithered-gradient` (DG), `marbled-ink` (MB), `paper-texture` (PT),
`contour-lines` (CL), `hand-drawn-radial-burst` (RB), `gradient-flow` (GF), `datamosh-rain` (DR).

## Practitioners on X

| # | Who | Why they count | Post | What we took | Used in |
|---|---|---|---|---|---|
| 1 | Stephen Haney (@stephenhaney) | Co-founder of Paper, the design tool that ships Paper Shaders | https://x.com/stephenhaney/status/2072369858638233843 | Paper Shaders are fully open source and free for any use, including resale and plugins | all |
| 2 | Stephen Haney | same | https://x.com/stephenhaney/status/2105007065106419936 | New paper shader: fold lines, wrinkles, crumples, stripes, clipping, image blends | PT |
| 3 | Stephen Haney | same | https://x.com/stephenhaney/status/1882113262092976634 | Warp shader announcement (marbled fields) | MB, GF |
| 4 | Stephen Haney | same | https://x.com/stephenhaney/status/1889423544523882961 | GodRays shader published to the npm package | GR |
| 5 | Ksenia Kondrashova (@uuuuuulala) | Shader developer at Paper; author of many Paper shaders and CodePen WebGL work | https://x.com/uuuuuulala/status/2105014895309938878 | PaperTexture rebuilt: `angle` sets shadow direction (combine with `seed`), `roughnessSize`, `roughnessRows` = laid-paper stripes, manual blending, clipping by image alpha | PT |
| 6 | Ksenia Kondrashova | same | https://x.com/uuuuuulala/status/2003848893965193406 | Liquid-metal workflow: pick a predefined shape or upload an image, polish with sliders, export | LM |
| 7 | Ksenia Kondrashova | same | https://x.com/uuuuuulala/status/2044099750241415655 | LiquidMetal tip: `shape: "none"` and `scale: 1` keep the effect contained in the canvas bounds | LM |
| 8 | Ksenia Kondrashova | same | https://x.com/uuuuuulala/status/1696846819244863949 | fBm noise in polar coordinates as a complete background (credits The Book of Shaders) | CL, RB |
| 9 | Ksenia Kondrashova | same | https://x.com/uuuuuulala/status/2019435172953784718 | Paper blog on retro print aesthetics with HalftoneCMYK (see [33]) | DG, PT, RB |
| 10 | Lucas Pope (@dukope) | Creator of Return of the Obra Dinn, the reference for 1-bit dithered rendering | https://x.com/dukope/status/933700786260910080 | Dot flicker in motion reduced by mapping the dither pattern to a sphere, not to the screen | DG, RB |
| 11 | Lucas Pope | same | https://x.com/dukope/status/1300260173919866880 and https://x.com/dukope/status/1300259933414330368 | Blue-noise dither survives downscaling better than Bayer; best capture he managed was 1080p, 60 fps, ProRes uploaded directly, and it still "got murdered" | DG, GG, MG, RB, DR |
| 12 | Lucas Pope | same | https://x.com/dukope/status/490854690297364480 | Hi-contrast dither "looks terrible on YouTube"; the effect was made for GIF | DG, RB, DR |
| 13 | Lucas Pope | same | https://x.com/dukope/status/525304273488211968 | Blue noise has less tonal range than Bayer; it hurt characters most | DG |
| 14 | Rune Skovbo Johansen (@runevision) | Game developer known for surface-stable fractal dithering | https://x.com/runevision/status/1666067893447000066 | Dither dots stay a constant screen size while following surfaces | DG |
| 15 | Mirza Beig (@TheMirzaBeig) | Real-time VFX and shader artist (Unity, Shadertoy) | https://x.com/TheMirzaBeig/status/2007826704769618278 | "Hand-drawn" look from stepped time: `t = floor(t * n) / n` with n = 24 | RB, DR |
| 16 | Mirza Beig | same | https://x.com/TheMirzaBeig/status/1734567042882175412 | An extra noise octave plus feedback for domain warping from the base layer | MB, CL |
| 17 | Kubai087 (@Kubai087) | Product designer posting parameterized texture recipes (399 likes, 443 bookmarks) | https://x.com/Kubai087/status/2115091203465290087 | Ordered dither recipe: 4x4 Bayer, pixel block 2–9 px, threshold (m + 0.5)/16, 2–8 levels per channel | DG |

## Articles, docs and source code

| # | Source | Author / owner | URL | What we took | Used in |
|---|---|---|---|---|---|
| 18 | Paper Shaders reference (llms.txt) | Paper | https://shaders.paper.design/llms.txt | Exact param names, ranges and meanings for every shader; `speed`/`frame` semantics | all |
| 19 | Paper Shaders source, v0.0.82 era (Apache-2.0) | Paper | https://github.com/paper-design/shaders (files `packages/shaders/src/shaders/{mesh-gradient,grain-gradient,dithering,god-rays,liquid-metal,warp,perlin-noise}.ts`) | Internal time scales (mesh `t = .5*(u_time+offset)`, grain `t = .1*(u_time+7)`, warp `t = .0625*(u_time+offset)`, god rays `t = .2*u_time`), grain built from `gl_FragCoord` so it ignores `scale`, Bayer 2/4/8 tables, `size` multiplied by pixel ratio | all |
| 20 | varg `paper-shaders` skill (MIT) | vargHQ | `vargHQ/skills/paper-shaders` (SKILL.md, references/shaders.md, determinism.md, brand-mapping.md, assets/presets/paper/*.json) | Speed-0 frame-exact mounting, `motion.timeScale`, `paramsAt`, `minPixelRatio: 1` for pixel looks, 124 Paper presets with exact values, complementary-hue rule, chrome stays neutral | all |
| 21 | Domain warping | Inigo Quilez | https://iquilezles.org/articles/warp/ | `fbm(p + 4r)` with q offsets (0,0),(5.2,1.3) and r offsets (1.7,9.2),(8.3,2.8); colour from f, \|q\| and r; Perlin's first procedural marble (1984) | MB, GF, CL |
| 22 | fBM | Inigo Quilez | https://iquilezles.org/articles/fbm/ | Gain G = 0.5 (H = 1) for natural terrain; detune lacunarity 2.01/1.99 and rotate the domain to avoid aligned artifacts | CL, MB |
| 23 | Distance estimation of implicit functions | Inigo Quilez | https://iquilezles.org/articles/distance/ | Constant-width isolines: `de = abs(f)/length(grad f)`, gradient from `dFdx/dFdy`, `smoothstep(1*eps, 2*eps, de)` | CL |
| 24 | Procedural palettes | Inigo Quilez | https://iquilezles.org/articles/palettes/ | `color(t) = a + b*cos(2π(c*t + d))`; integer c for seamless cycles | GF, MB, DR |
| 25 | The Book of Shaders ch. 13, fBM (+ `13/clouds.frag`) | Patricio Gonzalez Vivo, Jen Lowe | https://thebookofshaders.com/13/ and https://raw.githubusercontent.com/patriciogonzalezvivo/thebookofshaders/master/13/clouds.frag | 5–6 octaves, amplitude 0.5, frequency ×2, 0.5 rad rotation + shift 100 per octave; animated warp with `0.15*t` and `0.126*t`; teal/sand/navy colour mix | MB, CL, GF |
| 26 | The Book of Shaders ch. 07, Shapes | Patricio Gonzalez Vivo, Jen Lowe | https://thebookofshaders.com/07/ | Polar conversion `r = length(pos)*2.0; a = atan(pos.y,pos.x)`; shapes from radius as a function of angle | RB |
| 27 | Ditherpunk | Surma (Google Chrome team alum) | https://surma.dev/things/ditherpunk/ | Bayer recursion, normalise by 2^(2n+2); dither in linear light, not sRGB; Bayer levels 1 (4x4) and 3 (16x16) look best; 64x64 blue-noise tile is enough; Obra Dinn uses blue noise for environments, Bayer for people | DG, RB |
| 28 | GM Shaders Mini: Dither | Xor (@XorDev) | https://mini.gmshaders.com/p/gm-shaders-mini-dither | `floor(col*SHADES + dither)/SHADES` with a tiled Bayer texture; white noise gives a "grungy" look | DG, RB |
| 29 | Ordered dithering | Wikipedia | https://en.wikipedia.org/wiki/Ordered_dithering | Exact M2/M4/M8 matrices; 4x4 gives 17 visible patterns with two colours | DG, RB |
| 30 | Grainy Gradients | Jimmy Chion, CSS-Tricks | https://css-tricks.com/grainy-gradients/ | SVG `feTurbulence` fractalNoise, baseFrequency 0.65, 3 octaves; `contrast(170%) brightness(1000%)`; `isolation: isolate` | GR, MG, GG |
| 31 | GPU Gems 3 ch. 13, Volumetric Light Scattering as a Post-Process | Kenny Mitchell (EA) | https://developer.nvidia.com/gpugems/gpugems3/part-ii-light-and-shadows/chapter-13-volumetric-light-scattering-post-process | Radial sampling toward the light with density, weight, decay (0–1), exposure; occluders black in a pre-pass; stochastic sampling against pattern artifacts | GR |
| 32 | How to create the Stripe website gradient effect | Kevin Hufnagl | https://kevinhufnagl.com/how-to-stripe-website-gradient-effect/ | Four-colour flowing WebGL gradient (#6ec3f4, #3a3aff, #ff61ab, #E63946), skewed -12° section | GF, MG |
| 33 | Retro print CMYK halftone shader | Ksenia Kondrashova, Agu Seguí (Paper blog) | https://paper.design/blog/retro-print-cmyk-halftone-shader | Round dots, ink bleed, grid jitter; avoid pure digital primaries; warm inks 00B3FF / FC4F9D / FFD900 / 231F20 on FBFAF4; riso shift = duplicate and offset a layer | DG, PT, RB, GG |
| 34 | US Topo map symbol guide | USGS | https://www.usgs.gov/ngp-standards-and-specifications/us-topo-map-symbol-guide | Contours are brown; heavier index contours carry elevation labels; interval is stated in the legend (10 ft flat, 100 ft+ steep) | CL |
| 35 | risoinks colour table | anfederico (R package) | https://rdrr.io/github/anfederico/risoinks/src/R/color.R | Riso ink hex values: Fluorescent Pink #FF48B0, Blue #0078BF, Yellow #FFE800, Federal Blue #3D5588, Teal #00838A, Orange #FF6C2F, Sunflower #FFB511, Bright Red #F15060 | GG, DG, RB, DR |
| 36 | Macroblock | Wikipedia | https://en.wikipedia.org/wiki/Macroblock | Codec macroblocks are 16x16 samples, subdivided into transform and prediction blocks | DR |
| 37 | Compression artifact (datamoshing) | Wikipedia | https://en.wikipedia.org/wiki/Datamoshing | DCT block artifacts; intentional artifacts are glitch art / datamoshing | DR |
| 38 | How to create line boil animations | Jason Boone, PremiumBeat | https://www.premiumbeat.com/blog/how-to-create-line-boil-animations/ | Boil loop of 4 traced drawings at 8 fps, looped with `loopOut` | RB |
| 39 | HyperFrames registry items | HeyGen HyperFrames | https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry/blocks/<name>/registry-item.json (marble, liquid-metal, mesh-gradient, godrays, flowing-gradient, fractal-noise, sun-burst, aurora, glitch, domain-warp-dissolve, halftone-field; components grain-overlay, grain-field, ordered-dither-pass, mesh-gradient-bg) | Ready-made building blocks to start from | all |
| 40 | Paper marbling | Wikipedia | https://en.wikipedia.org/wiki/Paper_marbling | Colours dropped one after another, each spreading slightly less; rakes, combs and styluses pattern them | MB |

## Cinematic and craft analysis

| # | Source | Who | URL | What we took | Used in |
|---|---|---|---|---|---|
| 41 | Return of the Obra Dinn: Adventures in One Bit | Lucas Pope, PlayStation Blog | https://blog.playstation.com/2019/10/17/return-of-the-obra-dinn-adventures-in-one-bit-out-tomorrow/ | 640x360 dither pixels were too large for the eye to blend at fullscreen; moved to 800x450 + sphere-mapped dither; use dithering "as little as possible" | DG, RB |
| 42 | Noise and Turbulence (Academy Technical Achievement Award page) | Ken Perlin | https://mrl.cs.nyu.edu/~perlin/doc/oscar.html | Marble, fire and water in film VFX built from procedural noise textures | MB, CL |
