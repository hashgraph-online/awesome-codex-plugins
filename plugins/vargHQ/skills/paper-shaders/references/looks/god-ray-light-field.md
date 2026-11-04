# God-ray light field

Shafts of light from a bright core, graded blue and finished with film grain: a cinematic backdrop for a logo reveal, a title, a quote or a "something is coming" teaser. 16:9, 9:16 and 1:1; 6–10 s, or a 1.2 s reveal ramp at the head of a longer shot.

## How the pros do it
- Use Paper's GodRays: up to 5 ray colours plus `colorBack` and `colorBloom`; `density` = number of rays, `spotty` = ray length, `midSize`/`midIntensity` = the glowing core, `bloom` = overlay strength. Alpha in the ray colours layers them. [4][18][20]
- Move the light source with `offsetX`/`offsetY`; Paper's own "Linear" preset puts it at `offsetX 0.2, offsetY -0.8` for shafts from above. Check the first still, and flip the sign if the rays come from the wrong edge. [20]
- Few long rays read as light through a gap: Paper's "Ether" uses `density 0.03`, `spotty 0.77`. Many short rays read as a starburst. [20]
- For a reveal, ramp `intensity` and `midIntensity` from 0 with `paramsAt` over about 1.2 s with an ease-out; the varg `god-rays-reveal` preset does exactly this. [20]
- Real light shafts fade with distance from the source (a per-sample decay between 0 and 1) and the occluder is rendered black first; sparse sampling shows a regular pattern, which stochastic (jittered) sampling hides. Use this if you write your own rays over a logo silhouette. [31]
- Grain is a separate layer: SVG `feTurbulence` fractal noise, `baseFrequency 0.65`, 3 octaves, pushed with `contrast(170%) brightness(1000%)`, blended over the rays with `isolation: isolate` on the wrapper. [30]
- Grain and fine light gradients are what video compression destroys first; Lucas Pope's best result for a dithered game was 1080p, 60 fps, ProRes uploaded directly, and it still suffered. Render at final resolution and export at high bitrate. [11]
- GodRays' internal time runs at `0.2 × u_time`, so timeScale 0.25–0.6 already gives a slow, majestic drift; Paper's default ships at 0.75. [19][20]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `overhead` | Shafts from above into navy | speed 0.4; offsetY -0.8; back #050A18, bloom #8FB4FF; colors #3D7BFF66 #9CC2FFB3 #FFFFFF; density 0.35, spotty 0.3, midSize 0.15, midIntensity 0.6, intensity 0.75, bloom 0.5; grain 8% |
| `off-center` | Source top right, raking light | speed 0.4; offsetX 0.35, offsetY -0.35; back #040814, bloom #6E9BFF; density 0.3, spotty 0.35, midSize 0.12, intensity 0.7, bloom 0.45; grain 8% |
| `streaks` | Few long thin streaks | speed 0.3; back #03060F, bloom #FFFFFF; colors #148EFFA6 #C4DFFEBE #232A47; density 0.05, spotty 0.8, midSize 0.1, midIntensity 0.6, intensity 0.6, bloom 0.6; grain 7% |
| `photograph` | Desaturated blue-grey, heavy grain | speed 0.25; back #0B0E14, bloom #B8C4D8; colors #7F95B866 #C9D6EA99 #F2F4F8; density 0.3, spotty 0.3, intensity 0.6, bloom 0.25; grain 14% |
| `bright-core` | White-hot core, strong bloom | speed 0.6; back #060B1C, bloom #4D7DFF; midSize 0.35, midIntensity 0.95, intensity 0.85, bloom 0.8; 1.2 s ease-out ramp; grain 8% |

## Timing and numbers
- Reveal: `intensity = 0.85 × easeOutCubic(min(t/1.2, 1))` (36 frames at 30 fps); hold the logo 0.5 s after the ramp ends before any type animates.
- Grain layer: opacity 6–10% for clean looks, 12–16% for the photographic look; re-seed the noise per output frame (`seed = floor(seconds × 24)`) so it moves like film, and it stays seek-safe.
- Blue grade: keep `colorBack` below 10% luminance (#03060F–#0B0E14) so the core reads as the brightest thing on screen; text sits away from the core, in the darker third.
- 9:16: place the source above the top edge (`offsetY` about -0.8) so rays fall across the caption-free middle.

## Build it
1. Start from the varg preset `god-rays-reveal` or Paper's `paper-god-rays-linear` / `paper-god-rays-ether` in `vargHQ/skills/paper-shaders`. [20]
2. Paste the preset params above; set every sizing param; mount through `paperFrameSource` with `paramsAt` for the reveal ramp. [20]
3. Grain on a higher track: HyperFrames `grain-overlay` component, or an inline SVG `feTurbulence` (`type="fractalNoise" baseFrequency="0.65" numOctaves="3"`) whose `seed` attribute is set from the frame number in a frame source. [30][39]
4. Optional: HyperFrames `godrays` block (rays from a corner over deep blue, WebGPU) as a ready alternative. [39]

## Mistakes that look amateur
- Rays at full intensity from frame 0 → ramp from 0 over 1–1.5 s; light should arrive. [20]
- Core centred behind the headline → move the source with offsets and put type in the dark third.
- Static grain (same noise every frame) → re-seed per frame; frozen grain reads as a dirty lens.
- Grain at 25%+ to look "cinematic" → 6–14%; heavy grain is eaten by the encoder and turns to blocky mush. [11]
- Saturated electric blue everywhere → keep ray colours partly transparent (alpha 0x59–0xB3) and only one pure white. [18][20]
- Rendering at 720p and upscaling → render at the delivery size; grain and ray edges change size with the pixel ratio. [19][20]

## Sources
[4] Stephen Haney (Paper co-founder) — GodRays shader release — https://x.com/stephenhaney/status/1889423544523882961
[11] Lucas Pope (Return of the Obra Dinn) — capture and compression of fine dither/grain — https://x.com/dukope/status/1300259933414330368 and https://x.com/dukope/status/1300260173919866880
[18] Paper — Shaders reference — https://shaders.paper.design/llms.txt — GodRays params
[19] Paper — shader source — https://github.com/paper-design/shaders — `t = .2 * u_time` in god-rays.ts
[20] vargHQ — paper-shaders skill — Paper Linear/Ether/Default values, `god-rays-reveal` ramp
[30] Jimmy Chion — Grainy Gradients, CSS-Tricks — https://css-tricks.com/grainy-gradients/ — feTurbulence grain values
[31] Kenny Mitchell (EA) — GPU Gems 3 ch. 13 — https://developer.nvidia.com/gpugems/gpugems3/part-ii-light-and-shadows/chapter-13-volumetric-light-scattering-post-process — decay, occluder pre-pass, stochastic sampling
[39] HeyGen HyperFrames registry — `godrays` block, `grain-overlay` component
