---
name: footage-effects
description: >-
  Eight effects for footage you already have, each as tested ffmpeg filter chains plus HyperFrames and
  Remotion equivalents: glow and bloom (soft, film halation, sci-fi, sunset, anamorphic streaks,
  ominous), digital glitch (subtle to corrupt), CRT screen (consumer TV, arcade grille, green and
  amber terminal), chromatic aberration (lens, radial, linear split), halftone (ink on paper, CMY
  screen, LED wall, mosaic), acid photocopy, radial zoom blur and wave or heat distortion. Presets
  give thresholds, blur scales, offsets in px at 1080p, screen angles, ink colors, scanline periods
  and where in the edit each effect belongs, from Xor (GM Shaders), the libretro CRT shaders, GPU
  Gems, Steve Yedlin and Andrew Kramer. Use when someone wants a glitch, glow, VHS-era CRT, halftone,
  chromatic or heat-haze look on a clip, or a zoom-blur punch on the beat. NOT for color grading and
  LUTs, animated backgrounds without footage (paper-shaders) or generating new footage (varg-ai).
license: MIT
compatibility: >-
  ffmpeg 6+ (all 34 chains tested on FFmpeg 9.0.2 at 1920x1080, 30 fps). Optional: HyperFrames 0.8
  (npx hyperframes; brings Chrome, needs Node 22 and ffmpeg) or Remotion 4. No API key.
metadata:
  author: vargHQ
  version: "0.1.0"
  varg.cost.typical: "0 credits; renders locally"
  varg.runtime.typical: "seconds to a few minutes per clip with ffmpeg"
  varg.models: "none"
  varg.outputs: "mp4 or ProRes mov from ffmpeg; HyperFrames or Remotion layers"
  varg.presets: "8 templates, 34 presets"
---

# Footage effects: glow, glitch, CRT, halftone and more on real video

Eight effects applied to real footage, each preset a complete ffmpeg command that was rendered and checked, plus a HyperFrames or Remotion version for compositions. They are accents: strong settings live in short hits on beats and cuts, and the subject's face and the type stay clean.

## Gates

- **The person's footage.** Apply effects only to clips the person owns or licensed.
- **Cap every command.** Generated inputs never end: always pass `-t <clip duration>` and `blend=...:shortest=1`, as the presets do.
- **Protect faces and type.** No bloom, glitch or fringes over captions, logos or a centered face; keep text on an untreated layer.
- **Seek-safe and seeded.** Every random value is a hash of the frame number, so renders repeat exactly.
- **No credits here.** These templates render locally for free. Generated footage, voice or music is the varg-ai skill: call `estimate_cost` and wait for the person's approval before any generation.

## Pick a template

8 templates, 34 presets. Each reference file has the same sections: how the pros do it (every rule cited), presets, timing and numbers, how to build it, mistakes that look amateur, sources. Each JSON file holds the same presets as machine-readable values.

| Template | Use it for | Presets | Files |
|---|---|---|---|
| **Acid photocopy** | Turn real footage into a stuttering two-ink photocopy (teal, red, cream) or a black-toner zine copy on scanned paper. | Stutter flyer, Still print, Mono toner | [`acid-photocopy.md`](references/acid-photocopy.md) · [`json`](assets/presets/acid-photocopy.json) |
| **Chromatic aberration** | Split real footage's red, green and blue into a fringe that grows toward the frame edges (lens), across the frame (digital), or pulsing (psychedelic). | Lens (subtle), Radial (strong), Linear RGB split, Acid trip | [`chromatic-aberration.md`](references/chromatic-aberration.md) · [`json`](assets/presets/chromatic-aberration.json) |
| **CRT screen** | Put real footage (or a chat/UI scene) on a curved CRT: phosphor mask, scanlines, bloom, rounded corners, optional afterglow. | Consumer TV, Arcade aperture grille, Green phosphor terminal, Amber terminal | [`crt-screen.md`](references/crt-screen.md) · [`json`](assets/presets/crt-screen.json) |
| **Digital glitch** | Glitch real footage with RGB splits, torn rows, swapped blocks, stutter and macroblock corruption, in deterministic bursts. | Subtle, Default, Intense, Jittery, Corrupt | [`digital-glitch.md`](references/digital-glitch.md) · [`json`](assets/presets/digital-glitch.json) |
| **Glow and bloom** | Make the bright parts of real footage glow: neutral bloom, film halation, coloured halos or long anamorphic streaks. | Soft bloom, Film halation, Sci-fi cyan, Sunset warm, Anamorphic streaks, Ominous red | [`glow-bloom.md`](references/glow-bloom.md) · [`json`](assets/presets/glow-bloom.json) |
| **Halftone footage** | Turn real footage into halftone print (one ink or CMY rosettes), an LED wall or a colour mosaic. | Ink on paper, Colour screen (CMY), LED wall, Colour mosaic | [`halftone-footage.md`](references/halftone-footage.md) · [`json`](assets/presets/halftone-footage.json) |
| **Radial zoom blur** | Pull real footage into a zoom blur toward a centre, as a constant look, a beat punch, a fringed burst or light streaks. | Soft pull, Punch-in hit, Fringe burst, Light streak (brightest) | [`radial-zoom-blur.md`](references/radial-zoom-blur.md) · [`json`](assets/presets/radial-zoom-blur.json) |
| **Wave and heat distortion** | Make real footage ripple like heat haze or water, or smear itself along its own brightness. | Heat haze, Water ripple, Self-smear (colour-driven), Sine wave | [`wave-distortion.md`](references/wave-distortion.md) · [`json`](assets/presets/wave-distortion.json) |

## Workflow

1. **Match the request** to a template and one or two presets from the table. Say which and why in one line, and show the person the preset names with their one-line looks before building anything.
2. **Read the reference** for that template, and load its JSON. Take values from the JSON; do not re-guess them.
3. **Build it** the way the reference's "Build it" section says, starting from the named HyperFrames blocks or varg components where it names them. Drive every value from timeline time so any frame renders the same on a re-render.
4. **Fit it to the brand:** swap in the person's colors and fonts only where the reference allows, then re-check contrast and safe zones with the numbers in "Timing and numbers".
5. **Check a draft:** render stills at the key moments (entrance, hold, exit), go through "Mistakes that look amateur", and fix before the final render.
6. **Render with ffmpeg** using the preset's `ffmpeg` chain from the JSON (inputs and filter graph), at CRF 14-16 for anything with grain, dots or scanlines.

## Rules that hold for every template

1. Deterministic or nothing: every random value is a hash of the frame number and every noise source is seeded, so renders are seekable and parallel-safe.
2. Generated lavfi inputs never end: cap the output with `-t <clip duration>` and use `blend` with `shortest=1`; pre-render static textures once with `trim=end_frame=1,loop=-1`.
3. Work in `gbrp` for blend, displace and per-channel tricks, but run `eq` and `vignette` in YUV: on RGB planes they tint the image.
4. Threshold, then multi-scale, then add: glow, streaks and halation start from a soft-knee threshold (0.45–0.95), blur at 2–3 scales (about 1:4:12) and screen or add the result.
5. Real optics are radial: lens chromatic aberration and zoom blur are zero at the centre and grow with radius; flat shifts read as digital glitch.
6. Accents, not grades: strong aberration, zoom and glitch presets live in 2-frame windows or 0.2–1.5 s hits on beats and cuts; only the subtle presets run a whole shot.
7. Print looks need print logic: rotated screens (C/M/Y/K at 15/75/0/45, single ink at 45°), spot-ink hex on warm paper, 3–6 px misregistration, static paper with moving toner.
8. Respect delivery: dots ≥10 px and integer scanline periods (3–4 px) at 1080p, CRF ≤14–16, and scale every pixel value with frame height.
9. Protect the subject and the type: keep fringes off central faces, no bloom or glitch over captions or the logo, text on an untreated layer.

## Built from

Xor (@XorDev, GM Shaders); HyperFrames media-treatment recipes; libretro crt-geom and crt-lottes (Timothy Lottes) with @komm64; Kenny Mitchell and Tiago Sousa (GPU Gems); Maxime Heckel and Paper (Ksenia Kondrashova, Agu Seguí); Steve Yedlin; Andrew Kramer (Video Copilot); Remotion, Boris FX, Maxon and Notch docs.

Every rule in the references cites its source by number. The full list, with links and what was taken from each, is in [`references/sources.md`](references/sources.md). Values marked as house defaults in a reference are our own starting points where no expert published a number.

## Related skills

- [paper-shaders](../paper-shaders/): shader backgrounds and textures without footage.
- [transition-craft](../transition-craft/): shake, zoom and bokeh transitions.
- [short-form-ffmpeg-cookbook](../short-form-ffmpeg-cookbook/): crop, captions, music.
- [varg-video-edit-library](../varg-video-edit-library/): 206 named edits for existing footage (cuts, transitions, headlines, UI, numbers).
