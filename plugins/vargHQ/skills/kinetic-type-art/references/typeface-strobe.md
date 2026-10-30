# Typeface strobe

One word cut through many typefaces on a fast beat, a new face every beat or every few frames, ending on the brand face. For title cards, music promos, festival bumpers. 16:9, 9:16, 1:1; 3-5 s.

## How the pros do it
- The strobe credit sequence for a 2009 feature film was built frame by frame, with fast cuts used to make the image "vibrate" and to probe the limits of readability [50].
- The typeface order was edited to the music's rhythm [50].
- Each face was chosen to match the film's mood and the person it named; the designer avoided obviously copying other titles, and only about 60% of the designs made the cut [50].
- One anchor face (a condensed grotesque in all caps) carried most cards, and the wild faces (blackletter, stencil, slab, OCR, wide techno, outlined, shaded) were spikes around it [51].
- Recreating title sequences is a recognised way to practise type animation [8].
- Keep the word's position and cap height fixed so only the face changes; set every face to the same cap height, not the same font-size.

## Presets
| Preset | Look | Key values |
|---|---|---|
| `typeface-strobe.beat` | One face per beat, 9 faces, ends on anchor | 120 BPM, 15 f per face, white on black |
| `typeface-strobe.frames` | Strobe: a new face every 2-3 frames, then lock | 2 f per face for 24 f, then 3 f, then hold anchor |
| `typeface-strobe.color` | Face and background colour change together | 9 pairs from riso inks [30], 4 f per face |

## Timing and numbers
- Beat mode: 120 BPM = 15 f per face; 8 faces + a final 2-beat hold on the anchor = 150 f (5 s); 9 faces with no hold = 135 f (4.5 s).
- Strobe mode: 2 f per face (15 faces/s at 30 fps) is our floor; the word stays legible because position and cap height never move, while the faces flicker at the edge of readability as in [50]. Mix: 3 f x 6, 2 f x 12, then 3 f x 4, land and hold 20-30 f.
- Sudden swaps only (no crossfade, no tween); swap on frame 0 of the beat [38].
- Cap height fixed at 28-35% of frame height (16:9) / 18-22% of width (9:16); baseline fixed.
- Suggested 9-face set (all OFL [27]): Anton (anchor), Bodoni Moda 900, UnifrakturMaguntia, Big Shoulders Stencil 900, Alfa Slab One, Michroma, Monoton, Rubik Mono One, Pacifico; end on Anton.
- Contrast pattern: alternate wide/narrow and serif/sans so consecutive faces differ in silhouette.
- Photosensitivity: fast full-frame light/dark flashing is a seizure risk (the reference sequence's catalogue entry carries a flashing-lights warning [51]). Keep the strobe in the type, keep the background constant, or add a warning card.

## Build it
1. Load all fonts before the first frame (`document.fonts.load` for each family); missing fonts render a fallback and wreck the strobe.
2. Measure cap height per face once (canvas `measureText().actualBoundingBoxAscent` on "H") and compute font-size per face = targetCap / capRatio.
3. Stack N spans in the same box; on the timeline set `visibility` per span with `set` calls at frame-exact times (`tl.set(span[i], {autoAlpha:1}, i*framesPerFace/fps)`).
4. Per-face colour or treatment (outline, shaded) via classes, not tweens.
5. HyperFrames `kinetic-type-swap` shows the hold-and-swap slot mechanics [41]; Remotion: `const i = Math.floor(frame / framesPerFace)`.

## Mistakes that look amateur
- Faces at the same font-size → word jumps in height; normalise cap height.
- Crossfades between faces → strobe needs hard cuts [50].
- Similar faces back to back (two geometric sans) → swap is invisible; alternate silhouettes.
- No anchor → nothing to land on; end on the brand face and hold.
- Unlicensed commercial fonts copied from a famous sequence → use OFL equivalents.
- Full-frame flashing with no warning → keep the flash in the type [51].

## Sources
[8] @sarah_edo — https://x.com/sarah_edo/status/1231665606895624192 — recreating titles as practice
[27] google/fonts METADATA — https://github.com/google/fonts — licenses of the 9 faces
[30] Riso inks — https://rdrr.io/github/anfederico/risoinks/src/R/color.R
[38] Silverman Sound BPM calculator — https://www.silvermansound.com/bpm-to-fps-calculator
[41] HyperFrames registry, kinetic-type-swap — https://github.com/heygen-com/hyperframes/tree/main/registry
[50] Art of the Title, Enter the Void (Tom Kan) — https://www.artofthetitle.com/title/enter-the-void — frame-by-frame, rhythm, readability limits
[51] Fonts In Use, Enter the Void (Pedro Teles) — https://fontsinuse.com/uses/61211/enter-the-void-title-sequence — the face palette
