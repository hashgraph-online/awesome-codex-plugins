# Shared craft for kinetic type art

Rules every template in this family uses. Template files only repeat what they change. Source numbers point to `../sources.md`.

## 1. Beat-locked timing

- Frames per beat = (60 / BPM) x fps [38]. At 30 fps: 90 BPM = 20 f, 100 BPM = 18 f, 120 BPM = 15 f, 128 BPM = 14.06 f, 140 BPM = 12.86 f, 150 BPM = 12 f.
- Prefer tempos that land on whole frames at your fps (30 fps: 90, 100, 120, 150, 180 BPM). For any other tempo, compute every event from absolute time, `frame = round(beatIndex * 60 / BPM * fps)`, never by adding a rounded beat length, or the error piles up across a bar [38].
- Cut on the beat, move between beats. A hard swap (typeface, word, colour) lands on frame 0 of the beat. Motion (scale, slide) starts 1-2 frames before the beat so the hit frame shows the word already in place (our rule, from how cut-on-beat edits read).
- Readability ceiling: adults read about 20 characters per second [37]. An average English word plus a space is about 6 characters, so sustained text tops out near 3 words/s. One word per beat is safe up to 180 BPM; two words per beat is a burst, not a paragraph.
- Hold the last word or lockup 8-16 frames minimum before anything leaves (a "moving hold") [39]; in title work hold 1-1.5 s.

| Words per beat | 100 BPM | 120 BPM | 140 BPM |
|---|---|---|---|
| 1 | 1.67 w/s | 2 w/s | 2.33 w/s |
| 2 | 3.33 w/s (burst only) | 4 w/s (burst only) | 4.67 w/s (too fast) |

## 2. Easing vocabulary (GSAP names) [21]

| Job | Ease | Duration at 30 fps |
|---|---|---|
| Word or glyph arrives | `expo.out` or `power4.out` | 8-14 f (0.27-0.47 s) |
| Word leaves | `power3.in` | 6-10 f, about 30% shorter than the entrance |
| Camera move between targets | `power2.inOut` | 10-20 f |
| Overshoot "spring wide" | `back.out(1.6)` | 12-18 f |
| Mechanical / glitch / decode | `steps(n)` or `none` | 2-10 f |
| Tunnel or wall travel | `none` (linear) | whole loop |

## 3. Typeface pairings (all free for commercial video) [27]

All are on Google Fonts. License checked in the google/fonts repository.

| Role | First choice | Alternatives | License | Variable axes |
|---|---|---|---|---|
| Didone display | Bodoni Moda | Playfair Display, Abril Fatface, DM Serif Display, Libre Bodoni, Prata, Gloock | OFL-1.1 | Bodoni Moda opsz 6-96, wght 400-900; Playfair wght 400-900 |
| Condensed grotesque | Anton | Bebas Neue, League Gothic (wdth 75-100), Oswald (wght 200-700), Antonio, Big Shoulders Display, Barlow Condensed | OFL-1.1 | see left |
| Neutral grotesque (Swiss) | Inter | Archivo (wdth 62-125, wght 100-900), Instrument Sans (wdth 75-100), Space Grotesk | OFL-1.1 | Inter opsz 14-32, wght 100-900 |
| Mono | JetBrains Mono | IBM Plex Mono, Space Mono, Martian Mono (wdth 75-112.5), Share Tech Mono, VT323 (CRT) | OFL-1.1 | JetBrains wght 100-800 |
| Editorial serif | Instrument Serif | Fraunces (opsz 9-144, SOFT, WONK), Old Standard TT (newsprint) | OFL-1.1 | |
| Japanese Mincho | Shippori Mincho | Zen Old Mincho, Noto Serif JP (wght 200-900) | OFL-1.1 | |
| Wild cards (strobe) | UnifrakturMaguntia, Big Shoulders Stencil, Alfa Slab One, Monoton, Michroma, Orbitron, Rubik Mono One, Dela Gothic One, Pacifico, Bungee, Sixtyfour | | OFL-1.1 | Sixtyfour has BLED and SCAN axes |

Pairing rule: one display face carries the voice, one grotesque or mono carries labels. Never two display faces in one frame except in a deliberate typeface strobe.

## 4. Spacing [22]

- All caps and small caps: +0.05 to +0.12em letter-spacing. Labels at 14-24 px: +0.08 to +0.12em.
- Lowercase: 0. Big lowercase display (over ~120 px at 1080p): -0.01 to -0.03em.
- Condensed caps used as a slam word: 0 to +0.02em; they already sit tight.
- Gap test: if another letter fits in the gap, the spacing is too wide [22].

## 5. Grid and safe zones

- Swiss grid: decide the grid before the type; asymmetric layouts, grotesque sans, photos rather than illustration [25].
- Working grid at 1920x1080: 12 columns, 24 px gutter, 96 px outer margin (5%). At 1080x1920: 6 columns, 24 px gutter, 72 px side margin, top safe 220 px and bottom safe 380 px for platform UI. At 1080x1080: 8 columns, 72 px margin. (Our working values.)
- Baseline unit 8 px; type sizes snap to it.

## 6. Palettes (hex)

| Variant | Background | Ink | Accent | Notes |
|---|---|---|---|---|
| Paper | #F2EFE8 | #111111 | #E4002B | our values; add paper texture [42] |
| Night | #0B0B0D | #F2EFE8 | #FF5A1F | our values |
| Riso | #F4F1EA (paper) | Medium Blue #3255A4 | Fluorescent Pink #FF48B0, Yellow #FFE800 | ink hexes from [30]; the three-drum blue/pink/yellow set is a printmaker staple [5]; overprint with `mix-blend-mode: multiply`, shift one ink 1-3 px for misregistration |
| Newsprint | #E9E4D8 | #1A1A1A | #D2515E (riso tomato) [30] | |
| CRT amber | #050403 | #FF8A1F | glow #FF5A00 | our values; scanlines per [36] |

## 7. Seek-safe rules (HyperFrames and Remotion)

- One paused GSAP timeline per composition, seeked by the renderer; no `Date.now()`, `requestAnimationFrame` clocks or unseeded `Math.random()` (use a seeded PRNG such as mulberry32) [41][42].
- Scramble and glitch frames are a pure function of (frame, glyph index, seed).
- Shaders get `time` from the timeline; Paper Shaders mount at speed 0 [42].
- Fonts loaded before the first frame (`document.fonts.ready`), or the first frames render in a fallback face.
