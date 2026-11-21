# Moodboard: {TITLE} ({length} s, {aspect}, {platform})

Look: {one sentence: genre, era, capture medium}

## 1. References
| # | Link | Source | Lends (one) | Must not copy | Rights |
|---|---|---|---|---|---|
| 1 | {url} | {FrameThrower / Refs / Are.na / own / link-only site} | {light / palette / framing / texture / type / motion} | {actor, logo, set…} | {feed / link-only} |

## 2. Light
Key: {source}, {direction, e.g. high camera-left, 45° off axis}, {hard / soft}, {Kelvin}
Fill / rim: {source, side, colour} · Motivated by: {window / lamp / streetlight / screen}
Same in every shot: {yes; one source family}

## 3. Subject lock
Identity: {face, age, hair, outfit with colour names, proportions, accessories}
Sheet: {file}, front / side / back / close-ups, flat 18% grey, shadowless light

## 4. Framing
Aspect: {16:9 / 9:16 / 2.39:1}
Per shot: {shot size}, camera {height}, {angle}, {lens mm}; subject at {position}, {% of frame height}
Unusual angles: {blockout or reference frame}

## 5. Palette (taken from reference #{n} with scripts/palette.py)
Shadows {#hex} · Midtones {#hex} · Highlights {#hex} · Accent {#hex} ({where only})
Contrast: {warm vs cold} · Not saturated: {everything except …}
Grade: {contrast, blacks, saturation, fade}

## 6. Motion
Average shot length: {s}
| Shot | Duration | Camera move (one) | Subject action (one) | Reference clip |
|---|---|---|---|---|
| 1 | {s} | {push-in / pan / tracking / static} | {action with timing} | {url} |

## 7. Texture
Medium: {film stock / device / era} · Flaws: {grain, halation, softness, compression}
Skin / surface: {pores, wear, fingerprints} · Post: {+2–3% grain, one compression pass}

## 8. Type (set in code)
{Font family} {weight}, {size px}, {#hex}, {case}, tracking {value}, at {x, y}; captions {style} from word timings

## 9. Sound
Voice: {…} · Music: {…} · Room tone: {…}

## Never
{"cinematic", evenly lit, perfect symmetry, invented hex, Inter/Roboto/Arial, purple gradients, centred text fading in, text drawn by the model, …}

## Checks (after the test stills)
| Line | Still 1 | Still 2 | Still 3 | Target |
|---|---|---|---|---|
| Palette ΔE | | | | ≤ 15 |
| Light | | | | key side, hardness, one family |
| Framing | | | | size, height, position, % |
| Texture | | | | visible at 100% |
| Motion cue | | | | present |
