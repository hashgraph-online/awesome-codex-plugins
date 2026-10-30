# Sources: footage effects (8 templates)

Every URL below was opened in this research session, with WebFetch or the X tools. Numbers are shared by all eight reference files and preset JSONs.

Template keys: ACID = acid-photocopy, ZOOM = radial-zoom-blur, CRT = crt-screen, CA = chromatic-aberration, GLOW = glow-bloom, HT = halftone-footage, GLITCH = digital-glitch, WAVE = wave-distortion.

## Practitioners on X

| # | Who | Why they count | Post | What we took | Used in |
|---|---|---|---|---|---|
| 1 | Xor (@XorDev) | Graphics programmer, author of GM Shaders, 14 years of shader work; the post has 1.9k likes and 1.6k bookmarks | https://x.com/XorDev/status/1831738521935360079 | One-line CA via screen-space derivatives: `col.rgb += dFdx(col.rgb)*vec3(3,0,-3)` | CA |
| 2 | Xor (@XorDev) | Same | https://x.com/XorDev/status/1762944762787647954 | Taxonomy of blurs: radial/zoom blur samples outward from a focal point and is cheap; bloom looks best at several blur levels; CA as a weighted linear/zoom blur | ZOOM, CA, GLOW |
| 3 | Xor (@XorDev) | Same | https://x.com/XorDev/status/1883916173231759858 | Bloom improves a lot when blurred at multiple scales and combined (Kawase-style) | GLOW |
| 4 | Xor (@XorDev) | Same | https://x.com/XorDev/status/1883915548502995174 | Dithering as stylization and as a way to hide banding | ACID |
| 5 | Xor (@XorDev) | Same | https://x.com/XorDev/status/2008979114544509285 | "Turbulence": add perpendicular sine waves over several iterations for fluid-like distortion | WAVE |
| 6 | komm64 (@komm64) | Game developer whose CRT shader post drew 1k likes and 680 bookmarks | https://x.com/komm64/status/2073558529097834584 | Split the CRT look into a signal stage (YIQ, chroma bandwidth, ghosting, noise) and a display stage (scanlines, mask, curvature, bezel); colour bleed should come from the signal path | CRT |
| 7 | Steve Yedlin (@steveyedlin) | Cinematographer (Knives Out; his own thread on its colour rendering: https://x.com/steveyedlin/status/1216449232892092418), known for film-emulation colour science | https://x.com/steveyedlin/status/1515462800629542912 | Halation erodes edges only in some circumstances; it is not a blanket softness | GLOW |
| 8 | Steve Yedlin (@steveyedlin) | Same | https://x.com/steveyedlin/status/1610040392296337409 and https://x.com/steveyedlin/status/1610039110445727745 | Grain and noise in the right character and amount read as texture, not defects; use texture to take the clinical edge off without a blunt diffusion look | ACID, GLOW |
| 9 | Andrew Kramer (@videocopilot) | Founder of Video Copilot, After Effects VFX educator | https://x.com/videocopilot/status/970977859568201732 | Procedural glitch built from fractal-noise displacement plus a colour glow, all inside AE | GLITCH |

## Articles, docs and source code

| # | Source | Author / who | URL | What we took | Used in |
|---|---|---|---|---|---|
| 10 | FFmpeg Filters Documentation | FFmpeg developers | https://ffmpeg.org/ffmpeg-filters.html | Filter names and options. Every option was checked against `ffmpeg -h filter=<name>` on FFmpeg 9.0.2, and all 34 preset chains were rendered on a 1080p test clip | all |
| 11 | GM Shaders Mini: Chromatic Aberration | Xor | https://mini.gmshaders.com/p/gm-shaders-mini-chromatic-aberration | Basic, linear, radial and twist CA; radial offset ~0.01 UV; 10-sample blended version with squared colours; contrast 0–2; "chromatic motion" across frames; always ship a way to turn it off | CA, ZOOM |
| 12 | GM Shaders Mini: Bloom | Xor | https://mini.gmshaders.com/p/gm-shaders-mini-bloom | Soft threshold `smoothstep(0.6, 0.8, luma)`; whole-image bloom looks hazy; several passes with growing spread, added together | GLOW |
| 13 | LearnOpenGL: Bloom | Joey de Vries' LearnOpenGL | https://learnopengl.com/Advanced-Lighting/Bloom | Rec.709 luma weights for the bright pass; 5-tap separable Gaussian, 10 ping-pong passes; add bloom before tone mapping | GLOW |
| 14 | Sapphire S_Glow | Boris FX | https://borisfx.com/documentation/sapphire/ae/glow/ | Default threshold 0.5, brightness 2, width 0.4, screen combine; per-channel widths R 1 / G 1.2 / B 1.4 | GLOW, ZOOM |
| 15 | Halation in Film Photography, Explained | Dmitri, Analog.Cafe | https://www.analog.cafe/r/halation-in-film-photography-i3q4 | Light reflects off the film base and re-exposes the red-sensitive layer, so halos are red/orange around bright points | GLOW |
| 16 | Chromatic aberration | Wikipedia | https://en.wikipedia.org/wiki/Chromatic_aberration | Lateral CA is a wavelength-dependent magnification, which software corrects by radially scaling R and B to match G, so it grows from the centre outward; axial CA is different and hard to fix | CA |
| 17 | crt-geom.glsl | libretro (cgwg et al.) | https://raw.githubusercontent.com/libretro/glsl-shaders/master/crt/shaders/crt-geom.glsl | Defaults: CRTgamma 2.4, monitor gamma 2.2, distance 1.6, radius 2.0, corner size 0.03, dot mask 0.3, scanline weight 0.3; beam width grows with brightness | CRT |
| 18 | crt-lottes.glsl | Timothy Lottes, libretro port | https://raw.githubusercontent.com/libretro/glsl-shaders/master/crt/shaders/crt-lottes.glsl | hardScan −8, hardPix −3, warpX 0.031, warpY 0.041, maskDark 0.5, maskLight 1.5, shadowMask 3 (1 TV, 2 aperture grille, 3 stretched VGA, 4 VGA), bloomAmount 0.15 | CRT |
| 19 | CRT effects list | Jobima and others, libretro forums | https://forums.libretro.com/t/crt-effects-list/49051 | Checklist: brightness-dependent scanline bloom, phosphor persistence, halation glow, masks, convergence errors growing toward the edges, curvature, vignette | CRT |
| 20 | GPU Gems 3, ch. 13: Volumetric Light Scattering as a Post-Process | Kenny Mitchell (EA) | https://developer.nvidia.com/gpugems/gpugems3/part-ii-light-and-shadows/chapter-13-volumetric-light-scattering-post-process | Radial sampling toward the light with NUM_SAMPLES, Density, Weight, Decay (0–1) and Exposure: the "light streak" zoom blur | ZOOM |
| 21 | After Effects CS3 User Guide: Radial Blur | Adobe | https://www.manualsdir.com/manuals/753848/adobe-after-effects-cs3.html?page=384 | Spin vs Zoom; in Zoom mode Amount is the blur length; draft quality looks grainy | ZOOM |
| 22 | BCC Radial Blur | Boris FX | https://borisfx.com/documentation/continuum/bcc-radial-blur/ | Blur (symmetric) vs Smear (one-directional) with smear falloff; animate the mix from the original | ZOOM |
| 23 | Point Blur | Plate docs | https://plate-docs.pages.dev/effects/blur/point/ | Average, Brightest and Darkest combine modes along each ray; Brightest suits light streaks | ZOOM |
| 24 | zoomBlur() | Remotion | https://www.remotion.dev/docs/effects/zoom-blur | `amount` in px (default 40), `center` in UV, `samples` 1–64 (default 24); works on `<Video>` | ZOOM |
| 25 | turbulentDisplace() | Remotion | https://www.remotion.dev/docs/effects/turbulent-displace | amount px (50), size px (100), complexity 1–10, evolution in degrees, cycleEvolution, seed, pinning; WebGL2 | WAVE |
| 26 | glow() | Remotion | https://www.remotion.dev/docs/effects/glow | radius 20, intensity 1, threshold 0, colour; single-scale | GLOW |
| 27 | chromaticAberration() | Remotion | https://www.remotion.dev/docs/effects/chromatic-aberration | amount 8 px, angle 0°; linear split only | CA |
| 28 | halftone() | Remotion | https://www.remotion.dev/docs/effects/halftone | shape circle/square/line, dotSize 20, dotSpacing, rotation, colorMode solid/source, invert | HT |
| 29 | Media-treatment recipes | HyperFrames (HeyGen) | https://raw.githubusercontent.com/heygen-com/hyperframes/main/skills/media-use/references/media-treatment-recipes.md | Tested payloads and ranges: CRT Display, VHS digitalGlitch keys, Editorial Halftone (CMYK 15/75/0/45), Two-Ink Editorial Print, Ordered Palette Dither | CRT, CA, HT, GLITCH, ACID |
| 30 | Grading reference | HyperFrames (HeyGen) | https://raw.githubusercontent.com/heygen-com/hyperframes/main/skills/media-use/references/grading.md | Animatable `--hf-color-grading-bloom` 0–3, blur, pixelate, dither; tween only on the paused GSAP timeline | GLOW, ZOOM |
| 31 | Halftone | Wikipedia | https://en.wikipedia.org/wiki/Halftone | Screens rotated to form rosettes and avoid moiré; newsprint 85 lpi, coated paper 85–185 lpi; round dots meet at 70% tone, square at 50% | HT |
| 32 | Shades of Halftone | Maxime Heckel | https://blog.maximeheckel.com/posts/shades-of-halftone/ | radius = uRadius·(0.1 + luma); CMYK radius ∝ sqrt(coverage); CMYK angles 15/75/0/45; sample colour at the cell centre; anti-alias with smoothstep or fwidth | HT |
| 33 | Retro print: CMYK halftone shader | Ksenia Kondrashova and Agu Seguí, Paper | https://paper.design/blog/retro-print-cmyk-halftone-shader | One colour per cell sampled at the centre; subtractive blend of four dot layers; grid noise to mimic a loose print head; inks #00B3FF / #FC4F9D / #FFD900 / #231F20 on #FBFAF4 | HT |
| 34 | Glitch Transition | Maxon (Red Giant Universe) | https://help.maxon.net/rg/en-us/Content/html/glitch-transition.html | RGB Split Max examples 15 and −60; compression subtle up to 50%, heavy above; small vs wide glitches, size, displacement, seed | GLITCH |
| 35 | Block Glitch node | Notch | https://manual.notch.one/1.0/en/docs/reference/nodes/post-fx/stylisation/block-glitch | Block size, breakup amount, displace amount, glitch rate and glitch duration as separate controls | GLITCH |
| 36 | DataMosh component | shaders.com | https://shaders.com/docs/components/datamosh | blockSize 48, intensity 0.7, drift 0.35, churn 0.4: how many macroblocks lock and smear, and how often they re-roll | GLITCH |
| 37 | New tutorial: Colorful Glitch FX | Andrew Kramer, Video Copilot blog | http://www.videocopilot.net/blog/2018/03/new-tutorial-colorful-glitch-fx-100-ae/ | Procedural glitch, colour glow, animating between titles | GLITCH |
| 38 | GPU Gems 2, ch. 19: Generic Refraction Simulation | Tiago Sousa (Crytek) | https://developer.nvidia.com/gpugems/gpugems2/part-ii-shading-lighting-and-shadows/chapter-19-generic-refraction-simulation | Perturb screen UVs by a scrolling normal map (scale 0.05; water 0.075, glass 0.2); mask so foreground objects do not leak into the distortion | WAVE |
| 39 | How to Create Heat Waves in After Effects | Caleb Ward, PremiumBeat | https://www.premiumbeat.com/blog/how-to-create-heat-waves-in-after-effects/ | Matte solid feathered 250 px with Turbulent Displace 245/100; adjustment layer Turbulent Displace 30/30, evolution one turn per 5 s; Fast Blur 4 | WAVE |
| 40 | Heat Distortion plug-in sneak peek | Andrew Kramer, Video Copilot blog | http://www.videocopilot.net/blog/2013/10/new-heat-distortion-plug-in-sneak-peak/ | Heat haze is hard to control with plain displacement and fractal noise; intensity is driven by a mask | WAVE |
| 41 | How to Create Photocopy and Xerox Textures | Monika Zagrobelna, Envato Tuts+ | https://design.tutsplus.com/tutorials/how-to-create-photocopy-and-xerox-textures--cms-109034 | Desaturate, Levels 41/214, Grain speckle 98/11, noise 162% mono, Gaussian 1.7 px; striped copy with motion blur and halftone | ACID |
| 42 | Colorful xerox photocopy effect in Photoshop | Photoshop Roadmap | https://www.photoshoproadmap.com/create-a-colorful-xerox-photocopy-effect-in-photoshop/ | Threshold strips mid-tones; median 1–2 px removes fine detail; reticulation density 20–22 | ACID |
| 43 | riso-colors | Matt DesLauriers (generative artist), data from stencil.wiki | https://github.com/mattdesl/riso-colors | Riso ink hex values with Pantone: Teal #00838A (321 U), Red #FF665E (Warm Red U), Bright Red #F15060 (185 U), Fluorescent Pink #FF48B0 (806 U), Blue #0078BF (3005 U), Yellow #FFE800 | ACID |

## Cinematic analysis

| # | Who | What they teach | Used in |
|---|---|---|---|
| 7, 8 | Steve Yedlin, cinematographer | Film artifacts (halation, grain) are tools with conditions: halation appears only at specific high-contrast edges, and grain belongs in the image as texture, not as an overall degradation. This is why the halation preset is thresholded high and kept within ~20 px of edges, and why the copier toner is temporal while the paper texture is static. | GLOW, ACID |
| 9, 37, 40 | Andrew Kramer, VFX educator | Glitch and heat are procedural, built from noise-driven displacement with mask-controlled intensity rather than stock overlays. This is why every preset here is a deterministic function of frame number with a mask or gate. | GLITCH, WAVE |
