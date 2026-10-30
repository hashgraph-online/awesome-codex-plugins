# Hyphen bridge wordmark

Two words joined by a hyphen that grows into a long bar, stands up vertical, and shrinks back to a hyphen, pulling the words apart and together. For co-brand lockups, "X-Y" product names, partner reveals. Variants: paper, night, riso. 16:9, 9:16, 1:1; 3-5 s.

## How the pros do it
- Get the mark right first: a hyphen is the shortest dash, an en dash about half an em, an em dash about the width of a capital H; hyphens are never spaced [24]. The rest state must be a true hyphen, unspaced.
- Use the hyphen's own thickness and vertical position from the font (it sits around the x-height middle); draw the bar as a rect matched to those metrics so the morph starts and ends invisibly.
- Anticipation before the grow (a 1-2 px pull-in), overshoot at full length, and a moving hold [39].
- Loose parts drag: the words follow the bar's ends a few frames late [39].
- Caps grotesque or condensed tracks +0.05em; mixed-case lockups stay at 0 [22].
- One ease family across the move [21].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `hyphen-bridge-wordmark.paper` | Black grotesque on paper | Inter 800, #111111 on #F2EFE8, bar grows to 60% frame width |
| `hyphen-bridge-wordmark.night` | White on black, bar in accent | #F2EFE8 on #0B0B0D, bar #FF5A1F |
| `hyphen-bridge-wordmark.riso` | Blue words, pink bar, overprint | #3255A4 words, #FF48B0 bar [30], multiply, paper #F4F1EA |

## Timing and numbers (4 s = 120 f)
- 0-12 f: lockup appears (hard cut or 8 f mask wipe).
- 12-24 f: hold.
- 24-27 f: anticipation, bar shrinks 10% (`power2.in`).
- 27-45 f: bar grows to 45-60% of frame width, words pushed out, `expo.out` (18 f); words lag 2-3 f.
- 45-63 f: bar rotates 90deg about its centre to vertical and lengthens to 70-80% of frame height; words slide back toward centre (`power3.inOut`, 18 f).
- 63-81 f: bar shrinks back to hyphen size and rotates back to 0deg, words close in (`back.out(1.4)`, 18 f).
- 81-120 f: hold the clean lockup (39 f).
- Bar thickness = the font's hyphen stroke (about 7-9% of cap height for a bold grotesque; measure it).
- Lockup width at rest: 55-70% of frame width (16:9), 85% (9:16).

## Build it
1. Render word A, a hidden real hyphen (for metrics), word B in one line; measure the hyphen's bounding box (canvas `measureText` with `actualBoundingBox*`).
2. Replace the hyphen by an absolutely positioned div with the same box; animate its `scaleX`, `rotate`, `scaleY` (transform-origin centre).
3. Words: translate A left and B right by half the bar's extra length each frame (`onUpdate` from the bar's current length) plus a 2-3 f lag via a second tween.
4. Riso: bar on its own layer with multiply and a 2 px offset; paper texture from paper-shaders [42].
5. HyperFrames `center-build`/`kinetic-center-build` for the push mechanics; `titlecard-lockup` for the static end [41].

## Mistakes that look amateur
- Using an en/em dash glyph or spacing the hyphen → wrong mark at rest [24].
- Bar thickness differs from the hyphen → visible jump at start and end; match metrics.
- Rotation around the wrong origin → the bar swings off the baseline; rotate about its centre.
- Words locked rigidly to the bar ends → add 2-3 f drag [39].
- No hold at the end → brand never reads; hold 1+ s.
- Linear easing on the grow → feels mechanical; `expo.out` then `back.out`.

## Sources
[21] GSAP Eases — https://gsap.com/docs/v3/Eases/
[22] Butterick, Letterspacing — https://practicaltypography.com/letterspacing.html
[24] Butterick, Hyphens and dashes — https://practicaltypography.com/hyphens-and-dashes.html — mark lengths, no spaces
[30] Riso inks — https://rdrr.io/github/anfederico/risoinks/src/R/color.R
[39] Netguru, 12 principles — https://www.netguru.com/blog/illustrators-eye-12-principles-of-animation — anticipation, drag, hold
[41] HyperFrames registry — https://github.com/heygen-com/hyperframes/tree/main/registry — kinetic-center-build, titlecard-lockup
[42] varg paper-shaders — https://github.com/vargHQ/skills/tree/main/paper-shaders
[5] @natAndrewson, riso print — https://x.com/natAndrewson/status/1262744907355058186 — blue/pink ink set
