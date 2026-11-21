# Repeating word corridor

One word repeated along the four walls of a square corridor that rushes toward the viewer. A 5-8 s opener, a chorus hit in a music video, or a transition into a title. Variants: paper, night, riso. 16:9, 9:16, 1:1.

## How the pros do it
- Build the corridor as an open-ended cube: four planes each rotated 90deg on X or Y from their own edge, with perspective on the scene; size each wall to the container's long edge so all walls have equal depth [1].
- Move the words along the walls with a linear translate and loop it; the motion is the wall content moving, not the camera [1][41].
- Fade the far end into the background colour so new words emerge from fog instead of popping [41].
- Text pushed along z stays sharp if it is real text or SVG [4].
- Caps condensed grotesque reads best on walls seen at a steep angle; track caps +0.05em minimum [22].
- Riso variant: overprint two inks with multiply and a 1-3 px offset; the blue/pink/yellow three-drum set is a printmaker staple [5][30].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `word-corridor.paper` | Black words on off-white walls, paper grain | bg #F2EFE8, ink #111111, Anton 400 caps, perspective 600 px, speed 1 word-length per beat |
| `word-corridor.night` | White words in a black corridor, far end glows | bg #0B0B0D, ink #F2EFE8, end glow #FF5A1F at 30%, fog to bg over last 40% |
| `word-corridor.riso` | Blue and pink words alternate wall by wall, overprinted | paper #F4F1EA, inks #3255A4 + #FF48B0 [30], multiply, 2 px offset on pink |

## Timing and numbers
- Duration 7 s = 210 f. Speed locked to music: at 120 BPM (15 f/beat) move one word pitch per beat; on the drop double the speed for 2 beats, then back.
- Word pitch = word width + 0.6em gap. Repeat the word 12-20 times per wall so the far end is always filled.
- Corridor cross-section = full frame at the near plane; walls extend 4-6x the frame width deep.
- CSS: `perspective: 600px` (paper/riso), `450px` for a more violent rush (night). Smaller = stronger effect [35].
- Three.js alternative: PerspectiveCamera fov 60-75, camera stays at z=0, wall texture UV offset increases linearly.
- Font size on the wall: cap height = 55-65% of the wall's height.
- Opening: 0-15 f the corridor fades from bg; closing: on the last beat cut to the word flat and centred (match cut), hold 20-30 f.

## Build it
1. HyperFrames `gallery-tunnel` gives the corridor, fog and loop; replace its slabs with text tiles, or build four `div` walls as in [1] [41].
2. Each wall: a flex row of the word repeated, `white-space: nowrap`, width = wall depth, `transform: rotateY(90deg)` (sides) or `rotateX(-90deg)` (floor/ceiling) from the near edge.
3. Timeline: `x = -(beatIndex(t) * pitch) % pitch * repeats` with linear interpolation between beats; drive from `tl.time()`.
4. Fog: linear-gradient overlay per wall from transparent (near) to bg (far).
5. Riso: render walls twice (two inks), second copy offset 2 px, `mix-blend-mode: multiply`; add a paper texture via paper-shaders `paper-finish` [42].
6. End with a match cut to the flat word using the same font and colour.

## Mistakes that look amateur
- Camera flies, walls stay → slower to build and drifts off-axis; move wall content, keep camera fixed.
- Uneven wall depths → sides and floor vanish to different points; size all walls to the long edge [1].
- Words pop at the vanishing point → add fog.
- Speed not on the beat → set pitch per beat from BPM [38].
- Lowercase thin serif on steep walls → unreadable; condensed caps.
- Riso with flat 100% opacity colours → use multiply and misregistration.

## Sources
[1] @jh3yy, CSS 3D tunnel — https://x.com/jh3yy/status/1732553845530566855 — open cube, rotated sides, linear content
[4] @jh3yy, blow-out text — https://x.com/jh3yy/status/1702790661911494765 — crisp text in z
[5] @natAndrewson, riso print — https://x.com/natAndrewson/status/1262744907355058186 — blue, fluorescent pink, yellow
[22] Butterick, Letterspacing — https://practicaltypography.com/letterspacing.html
[30] Riso inks — https://rdrr.io/github/anfederico/risoinks/src/R/color.R — ink hexes
[35] MDN, perspective — https://developer.mozilla.org/en-US/docs/Web/CSS/perspective
[38] Silverman Sound BPM calculator — https://www.silvermansound.com/bpm-to-fps-calculator
[41] HyperFrames registry, gallery-tunnel — https://github.com/heygen-com/hyperframes/tree/main/registry — speed, fog
[42] varg paper-shaders — https://github.com/vargHQ/skills/tree/main/paper-shaders — paper finish
