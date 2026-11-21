# One-word-per-beat red slam

Big condensed words, one per beat, full-frame on a red field: a punchy statement, hook or call to action that hits like a drum. For ad hooks, sport promos, protest-poster energy, lyric drops. 16:9, 9:16, 1:1; 3-5 s.

## How the pros do it
- Cut the words to the music: each word lands on a beat, like the order of title cards cut to a track's rhythm [50].
- A staccato edit is part of the look; jumpy, hard cuts instead of smooth moves [53].
- Condensed grotesque caps fill the frame with the fewest pixels of motion: Anton, Bebas Neue, League Gothic (wdth 75-100), Oswald, Antonio, Big Shoulders Display [27].
- Condensed caps already sit tight; track 0 to +0.02em, never wider than the gap test allows [22].
- Readability: one word per beat stays under the 20 characters/s adult reading speed up to about 180 BPM for short words [37][38].
- Registry `caption-kinetic-slam` gives the full-screen single word with alternating entrance directions [41].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `red-beat-words.slam` | White condensed caps on red, hard cuts | bg #E4002B, ink #FFFFFF, Anton, 120 BPM (15 f/word) |
| `red-beat-words.punch` | Each word scales in from 112% to 100% in 3 f | `expo.out` 3 f, slight 1-2deg rotation alternating |
| `red-beat-words.riso` | Riso red with black overprint and grain | bg #F65058 [30], ink #000000 multiply, 1 px offset, paper grain |
| `red-beat-words.invert` | Every 4th word inverts (red on white) as an accent | bar accent on beat 4, 8 |

## Timing and numbers (4 s at 120 BPM = 8 beats = 120 f)
- Word i appears on frame round(i·15); hard cut (0 f) or 3 f punch (`expo.out`), no exit animation: the next word replaces it.
- Word length rule: 3-8 characters fills best; longer words go to two lines or a smaller cap height.
- Size: fit word width to 86-92% of frame width (16:9) or cap height ≤ 38% of frame height, whichever is smaller; 9:16: fit to 84% of width, centred on 45% height (above captions).
- Final word holds 2 beats (30 f).
- Optional camera shake on the hit frame: 6-12 px, decays over 4 f (registry `camera-shake` profiles [41]).
- Accent: a single black bar or underline (12-16 px thick) under the key word.

## Build it
1. HyperFrames: start from `caption-kinetic-slam` (single word full-screen) and set entrances to hard cuts or 3 f scales [41].
2. Fit-text: measure word width once per word at a reference size, then set font-size = target / width·ref.
3. Timeline: `tl.set(word[i], {autoAlpha:1}, i*60/BPM)` and `tl.set(word[i-1], {autoAlpha:0}, i*60/BPM)`; compute times from absolute beat index [38].
4. Riso variant: grain from paper-shaders `paper-finish`; black ink layer with `mix-blend-mode: multiply` [42].
5. Remotion: `const i = Math.floor(frame / (fps*60/bpm))`.

## Mistakes that look amateur
- Words that fade in/out → slams are cuts.
- Words drift or slide between beats → hold still, change on the beat.
- Mixed fonts or weights → one condensed face, one weight.
- Wide tracking on condensed caps → loses density [22].
- Off-beat timing from rounding per beat → compute from absolute time [38].
- Text over the 9:16 bottom UI → keep the word above the bottom 20%.

## Sources
[22] Butterick, Letterspacing — https://practicaltypography.com/letterspacing.html
[27] google/fonts METADATA — https://github.com/google/fonts — condensed faces, licenses, axes
[30] Riso inks — https://rdrr.io/github/anfederico/risoinks/src/R/color.R — scarlet
[37] Netflix Timed Text Style Guide — https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-USA-Timed-Text-Style-Guide
[38] Silverman Sound BPM calculator — https://www.silvermansound.com/bpm-to-fps-calculator
[41] HyperFrames registry — https://github.com/heygen-com/hyperframes/tree/main/registry — caption-kinetic-slam, camera-shake
[42] varg paper-shaders — https://github.com/vargHQ/skills/tree/main/paper-shaders
[50] Art of the Title, Enter the Void — https://www.artofthetitle.com/title/enter-the-void — cut to the music's rhythm
[53] Art of the Title, Se7en — https://www.artofthetitle.com/title/se7en/ — staccato edit
