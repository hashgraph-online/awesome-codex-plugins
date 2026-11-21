# Sources: kinetic type art family

Every URL below was opened in this research session (WebFetch, curl of a raw file, or the X tools). Numbers are shared by all 17 reference files and the JSON presets. Quotes in the references are short phrases with attribution; everything else is paraphrased.

Template slugs used below: perspective-photo-wall (PW), type-specimen-grid (TS), word-corridor (WC), justified-manifesto (JM), didone-city-title (DC), bitten-word-title (BW), anime-command-screen (AC), scan-glitch-wordmark (GW), echo-halftone-portrait (EH), typeface-strobe (TF), red-beat-words (RB), hyphen-bridge-wordmark (HB), crt-decrypt-title (CD), particle-burst-title (PB), photocopy-explainer (PX), glyph-tracking-terminal (GT), liquid-art-reveal (LR).

## Practitioners on X

| # | Who | Why they count | Post | What we took | Used by |
|---|---|---|---|---|---|
| 1 | @jh3yy (Jhey Tompkins) | Creative engineer known for CSS/3D motion demos; posts with 1k+ likes and CodePen sources | https://x.com/jh3yy/status/1732553845530566855 | Tunnel = open-ended cube, each side `rotateX(90deg)` from its edge, `perspective: 100px` on the scene, sides sized to the container's long edge, content translated linearly along each wall | WC, PW |
| 2 | @jh3yy | same | https://x.com/jh3yy/status/1852465034481598662 | Scramble by sliding a vertical strip of letters with `steps(11)` over 0.25 s with per-letter delay | CD, AC |
| 3 | @jh3yy | same | https://x.com/jh3yy/status/1762979019446698310 | Glyph flip glitch: 0.2 s per letter through `_` and two random glyphs, 0.05 s stagger by index | GW, CD |
| 4 | @jh3yy | same | https://x.com/jh3yy/status/1702790661911494765 | Blow-out type: SVG text pushed along z (`translate3d(0.05ch,0,99vh)`) inside `perspective:100vh`; SVG keeps glyphs crisp while they scale | GT, WC, PW |
| 5 | @natAndrewson (Natalie Andrewson) | Illustrator who sells and subscribes risograph prints | https://x.com/natAndrewson/status/1262744907355058186 | Classic three-drum riso set: medium blue, fluorescent pink, yellow | WC, HB, TS, EH |
| 6 | @ilovetypography (I Love Typography) | Long-running type publication and foundry shop | https://x.com/ilovetypography/status/1576905152849510401 | Variable display fonts as the tool for titles and type animation | TS, DC |
| 7 | @tsumiki_room (TsumikiRoom) | TouchDesigner artist, kinetic type studies with 1.5k likes | https://x.com/tsumiki_room/status/2096229986827182422 | Kinetic type built from single-stroke (stroke) fonts rather than filled outlines | DC, GT |
| 8 | @sarah_edo (Sarah Drasner) | Web animation author and educator | https://x.com/sarah_edo/status/1231665606895624192 | Recreating title sequences from Art of the Title as type-animation practice | TF, RB |
| 9 | @_chenglou (Cheng Lou) | Front-end engineer (React, ReasonML); 64k likes on this post | https://x.com/_chenglou/status/2037713766205608234 | Userland text measurement: get glyph positions without DOM reflow, so layout can be computed per frame | GT, JM |
| 10 | @HudsandGuis (HUDS+GUIS) | Long-running archive of film UI (FUI) work | https://x.com/HudsandGuis/status/1427767264720285701 | Pointer to Perception's FUI talk; the archive is the reference library for screen graphics | AC |
| 11 | @yiannifive (Yianni) | Motion designer posting Cavalry type experiments | https://x.com/yiannifive/status/2023883254978531704 | Type rebuilt from discrete cells (voxels) as a motion idea | PB |
| 12 | @jh3yy | same | https://x.com/jh3yy/status/1867330835415707959 | Several ways to scramble text with CSS alone or JS | CD |

## Articles and guides

| # | Source | Who | URL | What we took | Used by |
|---|---|---|---|---|---|
| 20 | ScrambleTextPlugin docs | GSAP (GreenSock) | https://gsap.com/docs/v3/Plugins/ScrambleTextPlugin/ | `chars` (default upperCase or a custom string), `speed` (default 1, lower = slower refresh), `revealDelay` (default 0), `delimiter`, `rightToLeft`, `tweenLength` | CD, AC, GT |
| 21 | Eases docs | GSAP | https://gsap.com/docs/v3/Eases/ | Ease names: power1-4, expo, circ, back, elastic, sine, steps, none; `.in/.out/.inOut`; default `power1.out` | all |
| 22 | Letterspacing | Matthew Butterick, Practical Typography | https://practicaltypography.com/letterspacing.html | All caps: +5-12% (0.05-0.12em); do not letterspace lowercase; large lowercase may need tighter spacing | all |
| 23 | Justified text | Matthew Butterick | https://practicaltypography.com/justified-text.html | Justify only with hyphenation on; put extra space between words, not letters | JM |
| 24 | Hyphens and dashes | Matthew Butterick | https://practicaltypography.com/hyphens-and-dashes.html | Hyphen is the shortest mark; en dash about half an em; em dash about the width of a capital H; hyphens are never spaced | HB |
| 25 | Swiss Style: principles, typefaces, designers | Callie Budrick, PRINT (2020) | https://www.printmag.com/?p=1387 | Mathematical grid first; asymmetric layout; grotesque sans (Akzidenz, Univers, Helvetica); photography over illustration | TS, JM, PX |
| 26 | Introduction to variable fonts | Dave Crossland, Mustafa Kurtuldu, Roel Nieskens, Thomas Steiner (web.dev) | https://web.dev/articles/variable-fonts | Axes wght/wdth/slnt/opsz/ital; animate `font-variation-settings` directly (CSS variables do not interpolate); unset axes reset | TS, TF, DC |
| 27 | Google Fonts repository METADATA | Google Fonts | https://github.com/google/fonts | License (OFL/Apache) and variable-axis ranges for every font named in the presets, checked one by one | all |
| 28 | Didone (typography) | Wikipedia | https://en.wikipedia.org/wiki/Didone_(typography) | High contrast, vertical stress, unbracketed hairline serifs, ball terminals; "dazzle" at small sizes; optical sizes; fashion mastheads | DC |
| 29 | Bodoni* README | Owen Earl, indestructible type | https://github.com/indestructible-type/Bodoni | Bodoni family with optical sizes, OFL-1.1 | DC, TS |
| 30 | Riso ink color table | risoinks R package (A. Federico) | https://rdrr.io/github/anfederico/risoinks/src/R/color.R | Hex values for 78 riso inks (fluorescent pink #FF48B0, blue #0078BF, medium blue #3255A4, yellow #FFE800 ...) | WC, HB, TS, EH, PB |
| 31 | How to create photocopy and xerox textures | Envato Tuts+ | https://design.tutsplus.com/tutorials/how-to-create-photocopy-and-xerox-textures--cms-109034 | Numeric Photoshop recipes: desaturate, Levels 41/214, speckle grain, noise, 1.7 px blur, horizontal motion-blur streaks, halftone | PX, GW, EH |
| 32 | Making mosh-ups | Parker Higgins | https://parkerhiggins.net/2017/07/making-mosh-ups-automated-datamoshing-from-multiple-video-sources/ | Datamosh mechanics: swapping or dropping I-frames, repeating P-frames re-applies motion to old pixels | GW |
| 33 | FFmpeg filters documentation | FFmpeg | https://ffmpeg.org/ffmpeg-filters.html | Filter names; option ranges checked with `ffmpeg -h filter=` (rgbashift ±255 px, noise alls 0-100 + flags t/u, lagfun decay 0.95, tmix frames 3, gblur sigma, vignette PI/5) | GW, PX, EH, CD |
| 34 | feDisplacementMap | MDN | https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/feDisplacementMap | P'(x,y) = P(x + scale·(XC-0.5), y + scale·(YC-0.5)); example turbulence baseFrequency 0.05, numOctaves 2, scale 50 | LR, GW |
| 35 | perspective | MDN | https://developer.mozilla.org/en-US/docs/Web/CSS/perspective | Distance from viewer to z=0; smaller = stronger effect; anything closer than the perspective distance is not drawn; examples 550-800px | PW, WC, GT |
| 36 | crt-pi shader | davej, libretro glsl-shaders | https://raw.githubusercontent.com/libretro/glsl-shaders/master/crt/shaders/crt-pi.glsl | Defaults: scanline weight 6.0, gap brightness 0.12, mask brightness 0.70, bloom 1.5, curvature 0.10/0.15, gamma 2.4 in / 2.2 out; dark gaps raise moire | CD, AC |
| 37 | English (USA) Timed Text Style Guide | Netflix | https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-USA-Timed-Text-Style-Guide | Reading speed up to 20 characters/s (adults), 17 (children); 42 characters per line | JM, RB, PX, TF |
| 38 | BPM to FPS calculator | Silverman Sound | https://www.silvermansound.com/bpm-to-fps-calculator | Frames and seconds per beat and per bar for cut timing (formula: frames/beat = 60/BPM x fps) | all beat-locked |
| 39 | Illustrator's eye: 12 principles of animation | Agnieszka Koniuszek, Netguru | https://www.netguru.com/blog/illustrators-eye-12-principles-of-animation | Squash and stretch keeps volume; anticipation is a small opposite move; loose parts drag; moving hold 8-16 frames | BW, HB, DC |
| 40 | US10560604B2 Halftone screens | Google Patents | https://patents.google.com/patent/US10560604 | Four-colour screens at 0, 15, 45, 75 degrees produce a rosette moire viewers find less objectionable | EH |
| 41 | HyperFrames registry | HeyGen (Apache-2.0) | https://github.com/heygen-com/hyperframes/tree/main/registry | Existing blocks and their parameters (gallery-tunnel speed 3 segments/s; echo-trail 2-6 echoes, 0.03-0.3 s lag; scramble-reveal; particle-text-dissolve density cap; variable-font-flex stagger 0.06 s) | all |
| 42 | paper-shaders skill | vargHQ/skills (Paper Shaders 0.0.82) | https://github.com/vargHQ/skills/tree/main/paper-shaders | Frame-exact Warp, Water, FlutedGlass, HalftoneDots, HalftoneCmyk, Dithering, PaperTexture shaders; keep under ~12 shader hosts | LR, EH, PX, GW |

## Cinematic analysis

| # | Source | Who | URL | What we took | Used by |
|---|---|---|---|---|---|
| 50 | Enter the Void (interview) | Art of the Title; designer Tom Kan, with Thorsten Fleisch | https://www.artofthetitle.com/title/enter-the-void | Type chosen per credited person and the film's mood; order cut to the music's rhythm; transitions built frame by frame; fast cuts for "visual vibration"; testing the limits of readability; only ~60% of designs used | TF, RB |
| 51 | Enter the Void title sequence | Pedro Teles, Fonts In Use | https://fontsinuse.com/uses/61211/enter-the-void-title-sequence | The actual palette: condensed grotesque caps as the anchor, plus blackletter, stencil, slab, OCR, wide techno, outlined and shaded faces | TF |
| 52 | Neon Genesis Evangelion | Peiran Tan, Fonts In Use | https://fontsinuse.com/uses/28760/neon-genesis-evangelion | Heavy Mincho serif "mechanically compressed" into interlocking black-and-white title cards; HUDs pair the serif with all-caps grotesque; condensed widths on interfaces | AC, CD |
| 53 | Se7en | Art of the Title; Kyle Cooper | https://www.artofthetitle.com/title/se7en/ | Hand-scratched type mixed with a grotesque; smear and jitter added in the film transfer; cut up for "temporal distress"; keep the optical printer's accidents; staccato edit | GW, PX, RB |
| 54 | The craft of screen graphics (David Sheldon-Hicks, Territory Studio) | Pushing Pixels (Kirill Grouchnikov) | https://www.pushing-pixels.org/2014/08/07/the-craft-of-screen-graphics-and-movie-user-interfaces-interview-with-david-sheldon-hicks-of-territory-studio.html | Believability over accuracy; one "operating system" across screens; worn glass, haze and overlays; build benchmark screens first | AC, CD |
| 55 | The craft of screen graphics (John LePore, Perception) | Pushing Pixels | https://pushing-pixels.org/?p=12751 | "The message is the priority"; huge type so the back row reads it; avoid boxes and windows all tinted blue; motion in sync with story beats | AC, CD, GT |

## Opened but not used

- Spoon Graphics xerox grunge tutorial (no numbers on the page).
- Codrops "Kinetic Typography with Three.js" (Cloudflare challenge, could not read).
- BBC subtitle guidelines (fetch blocked); Netflix guide used instead.
