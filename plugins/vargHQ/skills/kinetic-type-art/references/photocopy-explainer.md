# Photocopy explainer

Explainer graphics made of photocopied paper and toner: a question turns into a number grid and an answer, or a newspaper-style clipping blooms under a highlighter. For video essays, history explainers, data stories with a zine feel. Variants: explainer, article. 16:9 and 1:1; 15-25 s.

## How the pros do it
- The photocopy look in steps: desaturate, crush Levels (black 41, white 214), speckle grain, a 1.7 px blur, and horizontal motion-blur streaks for machine bands; halftone dots for photos [31].
- Assemble by hand and keep the accidents: tape, scratches, mis-feeds; analog assembly gives the look, and the "mistakes" are part of it [53].
- Mix hand-made marks with a plain grotesque [53]; Swiss-style grid and grotesque keep the information readable [25].
- Newsprint serif for clippings (Old Standard TT), mono for numbers (Space Mono, Courier Prime), a grotesque for labels [27].
- Reading pace: on-screen text must sit long enough to read at 20 characters/s [37].
- Paper as a shader on stills: PaperTexture (grain, fibres, folds), HalftoneDots, ImageDithering [42].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `photocopy-explainer.explainer` | Question card → number grid → answer stamp | paper #EDEAE2, toner #151515, highlight #FFE900 multiply, Space Mono + Inter |
| `photocopy-explainer.article` | Fake-generic newspaper clipping, highlighter sweeps a line | newsprint #E9E4D8, ink #1A1A1A, Old Standard TT 700 headline, highlighter #FFE900 at 85% multiply |
| `photocopy-explainer.zine` | Two-ink riso zine version | #3255A4 + #FF48B0 [30] on #F4F1EA |

## Timing and numbers
- Cards slide in like paper on a copier glass: 10-14 f `power3.out`, with 0.5-1.5deg rotation and 2-6 px drop shadow (blur 6 px, 25%).
- Hold each text card for max(1.5 s, characters / 20 s) [37].
- Number grid: cells fill one per 2-3 f in reading order; final answer stamps in 4 f (scale 1.3 to 1, `back.out(2)`), 1-2 f toner smear.
- Highlighter: a rect with `scaleX` 0 to 1 over 12-18 f per line (`power2.inOut`), height 1.1x x-height, 1-2 px wobbly edge, multiply.
- Toner jitter: whole frame shifts ±1 px every 2 f; brightness flicker ±3%.
- Copier band: a horizontal light bar sweeps top to bottom once per scene in 18-24 f, 15% opacity.
- Grid: 16:9 12 columns, 96 px margin; 1:1 8 columns, 72 px.

## Build it
1. Build cards as HTML; run the whole frame through a toner pass: grayscale, contrast 1.4-1.8, a threshold-like curve, grain.
2. For stills (photos, clipping backgrounds) use paper-shaders `paper-finish` and `halftone-overlay` [42]; for type keep real text and add grain on top so it stays crisp.
3. Generic newspaper: invent the masthead and the article text. Never reproduce a real publication's masthead, layout or story.
4. ffmpeg toner pass on a rendered MP4: `-vf "format=gray,eq=contrast=1.6:brightness=0.03,curves=all='0/0 0.35/0.1 0.65/0.9 1/1',noise=alls=18:allf=t,gblur=sigma=0.8"` (noise strength 0-100, temporal flag; gblur sigma) [33]. Streaks: a second branch with `boxblur=20:1` at 10% blend, horizontal.
5. HyperFrames `texture-mask-text` (texture masks through letterforms) and `grain-overlay` [41].

## Mistakes that look amateur
- Pure black on pure white with no grain → looks like a PDF, not a copy [31].
- Blurred body text from the toner pass → apply grain/threshold to backgrounds and photos, keep type sharp.
- Highlighter as an opaque yellow box over the words → multiply blend, slightly taller than x-height.
- Copying a real newspaper's masthead or article → generic, invented content only.
- Cards that fade → paper slides and drops; it never fades.
- Text cards gone before they can be read → characters / 20 s minimum [37].

## Sources
[25] PRINT, Swiss Style — https://www.printmag.com/?p=1387
[27] google/fonts METADATA — https://github.com/google/fonts — Old Standard TT, Space Mono, Courier Prime licenses
[30] Riso inks — https://rdrr.io/github/anfederico/risoinks/src/R/color.R
[31] Envato Tuts+, photocopy textures — https://design.tutsplus.com/tutorials/how-to-create-photocopy-and-xerox-textures--cms-109034 — the numeric recipe
[33] FFmpeg filters — https://ffmpeg.org/ffmpeg-filters.html
[37] Netflix Timed Text Style Guide — https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-USA-Timed-Text-Style-Guide
[41] HyperFrames registry — https://github.com/heygen-com/hyperframes/tree/main/registry — texture-mask-text, grain-overlay
[42] varg paper-shaders — https://github.com/vargHQ/skills/tree/main/paper-shaders — PaperTexture, HalftoneDots
[53] Art of the Title, Se7en — https://www.artofthetitle.com/title/se7en/ — hand assembly, accidents, hand marks + grotesque
