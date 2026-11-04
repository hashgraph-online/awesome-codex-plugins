# Transitions

Every way to join two shots: CapCut-style zooms, whips, glitches and masks, FFmpeg xfade, Remotion TransitionSeries, HyperFrames and GL shader transitions. 60 takes. Browse them with previews at https://skills.varg.ai/browse/skills/transitions/.

## Mix (Cross Dissolve)

<a id="mix-dissolve"></a>The two shots blend through each other. The quietest transition: "time passes" or "this continues".

Built on [Fade Through](https://github.com/heygen-com/hyperframes/tree/main/registry/components/fade-through) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A fades out while B fades in over the same frames; halfway both are at 50%.

- **When:** Time passing, calm brand and wellness pieces, slideshow photos, soft scene changes.
- **Watch out:** Mixing between two busy shots makes mud; never use it to hide a weak cut in fast edits.
- **Timing:** 0.4–1.0 s (CapCut Mix default 1.0 s, a short Mix 0.47 s), linear or ease-in-out
- **Also called:** Mix, Dissolve, crossfade, cross dissolve, fade
- **Card:** https://skills.varg.ai/skills/mix-dissolve/

### FFmpeg

Same size/fps/pixel format on both inputs (see the Normalize card). offset = duration(A) - T = 5.0 - 0.5 = 4.5.
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]fps=30,settb=AVTB,format=yuv420p[a];[1:v]fps=30,settb=AVTB,format=yuv420p[b];\
[a][b]xfade=transition=fade:duration=0.5:offset=4.5[v];\
[0:a][1:a]acrossfade=d=0.5[au]" \
  -map "[v]" -map "[au]" -c:v libx264 -crf 18 -c:a aac out.mp4
```
`dissolve` is a different, dithered (noisy) dissolve; `fadefast`/`fadeslow` change the curve.

### HyperFrames

Shader `cross-warp-morph` from `@hyperframes/shader-transitions` placed at the cut (t = 4 s):
```html
<div id="s1" class="scene" style="background:#0a0a0a"><video src="a.mp4" muted playsinline></video></div>
<div id="s2" class="scene" style="background:#0a0a0a"><video src="b.mp4" muted playsinline></video></div>
<script src="https://cdn.jsdelivr.net/npm/@hyperframes/shader-transitions/dist/index.global.js"></script>
<script>
  const tl = HyperShader.init({ bgColor: "#0a0a0a", scenes: ["s1", "s2"],
    transitions: [{ time: 4, shader: "cross-warp-morph", duration: 0.8 }] });
  window.__timelines = window.__timelines || {}; window.__timelines["main"] = tl;
</script>
```
Each `.scene` needs an explicit background-color equal to `bgColor`.
Plain CSS crossfade: omit `shader` in that transition entry, or overlap two clips by 0.5 s and tween opacity (see the HyperFrames scene transition card).

### Remotion

```tsx
import {TransitionSeries, linearTiming, springTiming} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';

<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={90}><ShotA /></TransitionSeries.Sequence>
  <TransitionSeries.Transition presentation={fade()} timing={linearTiming({durationInFrames: 15})} />
  <TransitionSeries.Sequence durationInFrames={90}><ShotB /></TransitionSeries.Sequence>
</TransitionSeries>
```
Total = 90 + 90 - 15 frames: the transition overlaps the two shots.

### CapCut

Transitions tab → Basic / Overlay → Mix, Dissolve, Dissolve II/III. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions.

### Components

- Fade Through (hyperframes): `npx hyperframes add fade-through` · https://skills.varg.ai/component/hf.fade-through/
- Dissolve Transitions (hyperframes): `npx hyperframes add transitions-dissolve` · https://skills.varg.ai/component/hf.transitions-dissolve/
- Cross Warp Morph (hyperframes): `npx hyperframes add cross-warp-morph` · https://skills.varg.ai/component/hf.cross-warp-morph/
- Dreamy (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.dreamy/

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [Remotion: presentations](https://www.remotion.dev/docs/transitions/presentations) · [HyperFrames: @hyperframes/shader-transitions](https://hyperframes.heygen.com/packages/shader-transitions) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py)

## Dip to Black

<a id="black-fade"></a>A fades to black, then B fades up. Marks the end of a section or a bigger jump in time.

Built on [Fade Through](https://github.com/heygen-com/hyperframes/tree/main/registry/components/fade-through) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Picture darkens fully for a few frames, then the next shot rises out of black.

- **When:** Chapter breaks, endings, before a title card, emotional pauses.
- **Watch out:** Using it between every shot makes the piece feel like it keeps ending.
- **Timing:** 0.5–1.2 s total, hold black 2–6 frames; CapCut default 0.47 s
- **Also called:** Black Fade, fade through black, fade to black, dip to black
- **Card:** https://skills.varg.ai/skills/black-fade/

### FFmpeg

Same size/fps/pixel format on both inputs (see the Normalize card). offset = duration(A) - T = 5.0 - 0.8 = 4.2.
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]fps=30,settb=AVTB,format=yuv420p[a];[1:v]fps=30,settb=AVTB,format=yuv420p[b];\
[a][b]xfade=transition=fadeblack:duration=0.8:offset=4.2[v];\
[0:a][1:a]acrossfade=d=0.8[au]" \
  -map "[v]" -map "[au]" -c:v libx264 -crf 18 -c:a aac out.mp4
```

### HyperFrames

CSS colour dip: tween `#s1` opacity 1→0 (power1.in, 0.4 s) and `#s2` 0→1 (power1.out, 0.4 s) starting 0.4 s later, over a black root. Block: `npx hyperframes add fade-through`.

### Remotion

```tsx
import {TransitionSeries, linearTiming, springTiming} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';

<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={90}><ShotA /></TransitionSeries.Sequence>
  <TransitionSeries.Transition presentation={fade({shouldFadeOutExitingScene: true})} timing={linearTiming({durationInFrames: 24})} />
  <TransitionSeries.Sequence durationInFrames={90}><ShotB /></TransitionSeries.Sequence>
</TransitionSeries>
```
Total = 90 + 90 - 24 frames: the transition overlaps the two shots.
Put a black `<AbsoluteFill>` behind the series so the dip goes through black, not the background.

### CapCut

Transitions tab → Basic / Overlay → Black Fade. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions.

### Components

- Fade Through (hyperframes): `npx hyperframes add fade-through` · https://skills.varg.ai/component/hf.fade-through/
- Dissolve Transitions (hyperframes): `npx hyperframes add transitions-dissolve` · https://skills.varg.ai/component/hf.transitions-dissolve/

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [Remotion: presentations](https://www.remotion.dev/docs/transitions/presentations) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py)

## White Flash

<a id="white-flash"></a>The frame blows out to white for a moment and opens on the next shot. Energy, memory or a camera snap.

Built on [Flash Through White](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/flash-through-white) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Overexposed white flash peaking on the cut, then B fades back from white.

- **When:** Beat drops, memories, photo-shoot vibes, hype reels, transitions into a freeze frame.
- **Watch out:** Long white holds are tiring and an accessibility risk; keep it short and avoid repeated strobing.
- **Timing:** 0.2–0.4 s (CapCut White Flash 0.40–0.47 s); peak on the beat
- **Also called:** White Flash, Flash, Blanch, flash transition, fade through white, camera flash
- **Card:** https://skills.varg.ai/skills/white-flash/

### FFmpeg

Same size/fps/pixel format on both inputs (see the Normalize card). offset = duration(A) - T = 5.0 - 0.3 = 4.7.
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]fps=30,settb=AVTB,format=yuv420p[a];[1:v]fps=30,settb=AVTB,format=yuv420p[b];\
[a][b]xfade=transition=fadewhite:duration=0.3:offset=4.7[v];\
[0:a][1:a]acrossfade=d=0.3[au]" \
  -map "[v]" -map "[au]" -c:v libx264 -crf 18 -c:a aac out.mp4
```
Flash on a hard cut instead: `eq=brightness=0.6:enable='between(t,4.0,4.066)'` (eq supports timeline `enable`).

### HyperFrames

Shader `flash-through-white` from `@hyperframes/shader-transitions` placed at the cut (t = 4 s):
```html
<div id="s1" class="scene" style="background:#0a0a0a"><video src="a.mp4" muted playsinline></video></div>
<div id="s2" class="scene" style="background:#0a0a0a"><video src="b.mp4" muted playsinline></video></div>
<script src="https://cdn.jsdelivr.net/npm/@hyperframes/shader-transitions/dist/index.global.js"></script>
<script>
  const tl = HyperShader.init({ bgColor: "#0a0a0a", scenes: ["s1", "s2"],
    transitions: [{ time: 4, shader: "flash-through-white", duration: 0.4 }] });
  window.__timelines = window.__timelines || {}; window.__timelines["main"] = tl;
</script>
```
Each `.scene` needs an explicit background-color equal to `bgColor`. Or install the ready block: `npx hyperframes add flash-through-white`.

### Remotion

```tsx
import {TransitionSeries, linearTiming, springTiming} from '@remotion/transitions';
import {pushCut} from '@remotion/transitions/push-cut';

<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={90}><ShotA /></TransitionSeries.Sequence>
  <TransitionSeries.Transition presentation={pushCut({flashColor: '#ffffff', flashFrames: 3})} timing={linearTiming({durationInFrames: 11})} />
  <TransitionSeries.Sequence durationInFrames={90}><ShotB /></TransitionSeries.Sequence>
</TransitionSeries>
```
Total = 90 + 90 - 11 frames: the transition overlaps the two shots.
`pushCut` (v4.0.500+) is a hard cut with a short punch-in and a flash; for a pure flash place a white `<AbsoluteFill>` in `<TransitionSeries.Overlay durationInFrames={8}>`.

### CapCut

Transitions tab → Light Effect / Basic → White Flash, Flash, Blanch, B&W Flash, Strobe. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions.

### Components

- Flash Through White (hyperframes): `npx hyperframes add flash-through-white` · https://skills.varg.ai/component/hf.flash-through-white/
- Editorial Flash Overlay (hyperframes): `npx hyperframes add editorial-flash-overlay` · https://skills.varg.ai/component/hf.editorial-flash-overlay/
- Light Transitions (hyperframes): `npx hyperframes add transitions-light` · https://skills.varg.ai/component/hf.transitions-light/

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [Remotion: pushCut](https://www.remotion.dev/docs/transitions/presentations/push-cut) · [HyperFrames: @hyperframes/shader-transitions](https://hyperframes.heygen.com/packages/shader-transitions) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py)

## Pull In (Zoom In)

<a id="pull-in-zoom"></a>The camera rushes into shot A and lands, still moving forward, in shot B. The signature short-form transition.

Built on [Zoom Through Transition](https://github.com/heygen-com/hyperframes/tree/main/registry/components/zoom-through-transition) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A scales up fast with motion blur; B starts enlarged and settles to 100%, so the zoom feels continuous.

- **When:** Hooks, travel and fashion reels, going "into" a detail, on a beat.
- **Watch out:** On slow, emotional pieces; and stacking it on every cut.
- **Timing:** 0.3–0.5 s (CapCut Pull in 0.47 s), ease-in into the cut, ease-out after
- **Also called:** Pull in, Zoom in transition, zoom transition, punch zoom, Snap Zoom, Zoom to Change
- **Card:** https://skills.varg.ai/skills/pull-in-zoom/

### FFmpeg

Real two-sided zoom: last 0.3 s of A scales 1→1.5 with blur, first 0.3 s of B scales 1.5→1 (720p example):
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]trim=0:5,setpts=PTS-STARTPTS,scale=w='trunc(1280*(1+if(gte(t,4.7),(t-4.7)/0.3*0.5,0))/2)*2':h=-2:eval=frame,\
crop=1280:720,gblur=sigma=12:enable='gte(t,4.8)'[a];\
 [1:v]trim=0:4,setpts=PTS-STARTPTS,scale=w='trunc(1280*(1+if(lt(t,0.3),(0.3-t)/0.3*0.5,0))/2)*2':h=-2:eval=frame,\
crop=1280:720,gblur=sigma=12:enable='lt(t,0.2)'[b];\
 [a][b]concat=n=2:v=1:a=0[v]" -map "[v]" out.mp4
```
Quick version: `xfade=transition=zoomin:duration=0.4:offset=<A-0.4>` (zooms into A while fading to B).

### HyperFrames

CSS zoom-through on the two scene wrappers:
```js
tl.to("#s1", { scale: 2.5, opacity: 0, filter: "blur(8px)", duration: 0.4, ease: "power3.in" }, T);
tl.fromTo("#s2", { scale: 0.5, opacity: 0, filter: "blur(8px)" }, { scale: 1, opacity: 1, filter: "blur(0px)", duration: 0.4, ease: "power3.out" }, T);
```
Or `npx hyperframes add zoom-through-transition`; shader: `cinematic-zoom`.

### Remotion

```tsx
import {TransitionSeries, linearTiming, springTiming} from '@remotion/transitions';
import {zoomInOut} from '@remotion/transitions/zoom-in-out';

<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={90}><ShotA /></TransitionSeries.Sequence>
  <TransitionSeries.Transition presentation={zoomInOut({})} timing={linearTiming({durationInFrames: 12})} />
  <TransitionSeries.Sequence durationInFrames={90}><ShotB /></TransitionSeries.Sequence>
</TransitionSeries>
```
Total = 90 + 90 - 12 frames: the transition overlaps the two shots.
Shader presentations are built on Remotion's HTML-in-canvas: renders work out of the box (`--gl=angle`, or `--gl=swangle` without a GPU); the Studio preview needs Chrome with `chrome://flags/#canvas-draw-element` enabled. remocn `lensZoom()` (28 frames) adds barrel distortion, zoom blur and shake around the splice.

### CapCut

Transitions tab → Camera → Pull in, Snap Zoom, Zoom Transition, Zoom to Change, Twinkle Zoom. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions. Hand-made version: keyframe Scale 100→150% on A's last frames and 150→100% on B's first frames.

### Components

- Zoom Through Transition (hyperframes): `npx hyperframes add zoom-through-transition` · https://skills.varg.ai/component/hf.zoom-through-transition/
- Cinematic Zoom (hyperframes): `npx hyperframes add cinematic-zoom` · https://skills.varg.ai/component/hf.cinematic-zoom/
- Scale Transitions (hyperframes): `npx hyperframes add transitions-scale` · https://skills.varg.ai/component/hf.transitions-scale/
- Zoom Blur (remocn): `npx shadcn@latest add @remocn/zoom-blur` · https://skills.varg.ai/component/remocn.zoom-blur/
- Lens Zoom (remocn): `npx shadcn@latest add @remocn/lens-zoom` · https://skills.varg.ai/component/remocn.lens-zoom/
- Push Through (remocn): `npx shadcn@latest add @remocn/push-through` · https://skills.varg.ai/component/remocn.push-through/
- CrossZoom (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.cross-zoom/

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [FFmpeg filters: zoompan](https://ffmpeg.org/ffmpeg-filters.html#zoompan) · [Remotion: presentations](https://www.remotion.dev/docs/transitions/presentations) · [remocn: Lens Zoom](https://remocn.dev/docs/transitions/lens-zoom) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py) · [CapCut transition names incl. Pro (pyCapCut metadata)](https://github.com/GuanYixuan/pyCapCut/blob/main/pycapcut/metadata/transition_meta.py)

## Pull Out (Zoom Out)

<a id="pull-out-zoom"></a>The camera jerks backwards out of shot A and keeps pulling back as shot B settles in.

Built on [Parallax Unzoom](https://github.com/heygen-com/hyperframes/tree/main/registry/components/parallax-unzoom) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A shrinks away (over a blurred copy or black), B starts slightly enlarged and eases out to full frame.

- **When:** Reveals, "zoom out to see the bigger picture", endings of a sequence.
- **Watch out:** Low-resolution sources: the enlarged start of B shows softness.
- **Timing:** 0.3–0.5 s (CapCut Pull Out 0.47 s), ease-in then ease-out
- **Also called:** Pull Out, zoom out transition, pull back, Shrink
- **Card:** https://skills.varg.ai/skills/pull-out-zoom/

### FFmpeg

A shrinks to 60% over a blurred copy of itself; B starts at 140% and settles:
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]trim=0:5,setpts=PTS-STARTPTS,split[bg][fg];[bg]gblur=sigma=30[bgb];\
 [fg]scale=w='trunc(1280*(1-if(gte(t,4.7),(t-4.7)/0.3*0.4,0))/2)*2':h=-2:eval=frame[fgs];\
 [bgb][fgs]overlay=x=(W-w)/2:y=(H-h)/2:eval=frame[a];\
 [1:v]trim=0:4,setpts=PTS-STARTPTS,scale=w='trunc(1280*(1+if(lt(t,0.3),(0.3-t)/0.3*0.4,0))/2)*2':h=-2:eval=frame,crop=1280:720[b];\
 [a][b]concat=n=2:v=1:a=0[v]" -map "[v]" out.mp4
```

### HyperFrames

```js
tl.to("#s1", { scale: 0.6, opacity: 0, duration: 0.4, ease: "power3.in" }, T);
tl.fromTo("#s2", { scale: 1.4, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.4, ease: "power3.out" }, T);
```
Blocks: `parallax-unzoom`, `pull-back-reveal`.

### Remotion

Custom presentation: exiting scene `scale = 1 - 0.4 * presentationProgress`, entering scene `scale = 1.4 - 0.4 * presentationProgress` (see the Remotion custom presentation card).

### CapCut

Transitions tab → Camera → Pull Out, Shrink. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions.

### Components

- Parallax Unzoom (hyperframes): `npx hyperframes add parallax-unzoom` · https://skills.varg.ai/component/hf.parallax-unzoom/
- Pull Back Reveal (hyperframes): `npx hyperframes add pull-back-reveal` · https://skills.varg.ai/component/hf.pull-back-reveal/
- Scale Transitions (hyperframes): `npx hyperframes add transitions-scale` · https://skills.varg.ai/component/hf.transitions-scale/

Sources: [FFmpeg filters: overlay](https://ffmpeg.org/ffmpeg-filters.html#overlay) · [Remotion: custom presentations](https://www.remotion.dev/docs/transitions/presentations/custom) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py) · [CapCut transition names incl. Pro (pyCapCut metadata)](https://github.com/GuanYixuan/pyCapCut/blob/main/pycapcut/metadata/transition_meta.py)

## Zoom Blur

<a id="zoom-blur"></a>Both shots smear into a radial zoom blur that bursts open on the next shot.

Built on [CrossZoom](https://github.com/gl-transitions/gl-transitions/blob/master/transitions/CrossZoom.glsl) by rectalogic (gl-transitions), MIT. The write-up and recipes are varg's.

Streaks radiate from the centre, peak at the cut, then resolve sharply on B.

- **When:** Energetic promos, gaming, sport, speed-themed edits.
- **Watch out:** Overuse; and on faces where the radial smear distorts features.
- **Timing:** 0.4–0.7 s, ease-in-out
- **Also called:** radial zoom blur, Radial Blur, Twinkle Zoom, cross zoom, warp zoom
- **Card:** https://skills.varg.ai/skills/zoom-blur/

### FFmpeg

xfade has no radial blur. Use a GL transition via editly (`CrossZoom`) or approximate with `zoomin` plus a strong blur at the peak:
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]fps=30,settb=AVTB,format=yuv420p[a];[1:v]fps=30,settb=AVTB,format=yuv420p[b];\
 [a][b]xfade=transition=zoomin:duration=0.5:offset=4.5,gblur=sigma=18:enable='between(t,4.6,4.9)'[v]" -map "[v]" out.mp4
```

### HyperFrames

Shader `cinematic-zoom` from `@hyperframes/shader-transitions` placed at the cut (t = 4 s):
```html
<div id="s1" class="scene" style="background:#0a0a0a"><video src="a.mp4" muted playsinline></video></div>
<div id="s2" class="scene" style="background:#0a0a0a"><video src="b.mp4" muted playsinline></video></div>
<script src="https://cdn.jsdelivr.net/npm/@hyperframes/shader-transitions/dist/index.global.js"></script>
<script>
  const tl = HyperShader.init({ bgColor: "#0a0a0a", scenes: ["s1", "s2"],
    transitions: [{ time: 4, shader: "cinematic-zoom", duration: 0.6 }] });
  window.__timelines = window.__timelines || {}; window.__timelines["main"] = tl;
</script>
```
Each `.scene` needs an explicit background-color equal to `bgColor`. Or install the ready block: `npx hyperframes add cinematic-zoom`.

### Remotion

```tsx
import {TransitionSeries, linearTiming, springTiming} from '@remotion/transitions';
import {crossZoom} from '@remotion/transitions/cross-zoom';

<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={90}><ShotA /></TransitionSeries.Sequence>
  <TransitionSeries.Transition presentation={crossZoom({strength: 0.4})} timing={linearTiming({durationInFrames: 18})} />
  <TransitionSeries.Sequence durationInFrames={90}><ShotB /></TransitionSeries.Sequence>
</TransitionSeries>
```
Total = 90 + 90 - 18 frames: the transition overlaps the two shots.
Shader presentations are built on Remotion's HTML-in-canvas: renders work out of the box (`--gl=angle`, or `--gl=swangle` without a GPU); the Studio preview needs Chrome with `chrome://flags/#canvas-draw-element` enabled. Also `zoomBlur({})` from `@remotion/transitions/zoom-blur`.

### CapCut

Transitions tab → Blur / Camera → Radial Blur, Twinkle Zoom. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions.

### Components

- CrossZoom (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.cross-zoom/
- DreamyZoom (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.dreamy-zoom/
- Cinematic Zoom (hyperframes): `npx hyperframes add cinematic-zoom` · https://skills.varg.ai/component/hf.cinematic-zoom/
- Zoom Blur (remocn): `npx shadcn@latest add @remocn/zoom-blur` · https://skills.varg.ai/component/remocn.zoom-blur/
- Lens Zoom (remocn): `npx shadcn@latest add @remocn/lens-zoom` · https://skills.varg.ai/component/remocn.lens-zoom/

Sources: [Remotion: crossZoom (HTML-in-canvas)](https://www.remotion.dev/docs/transitions/presentations/cross-zoom) · [HyperFrames: @hyperframes/shader-transitions](https://hyperframes.heygen.com/packages/shader-transitions) · [GL Transitions gallery](https://gl-transitions.com) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py)

## Whip Swipe

<a id="whip-swipe"></a>A fast synthetic pan with heavy motion blur pushes A off and B in. Fakes a whip pan between any two shots.

Built on [Whip Pan](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/whip-pan) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Both images streak sideways at high speed and the next shot snaps into place.

- **When:** Travel, lifestyle, energetic product edits, on a whoosh SFX; matches footage that already moves sideways.
- **Watch out:** Direction changes between consecutive whips, and whips longer than 0.4 s (they read as slides).
- **Timing:** 0.2–0.35 s (6–10 frames at 30 fps), ease-in-out with the blur peaking mid-way
- **Also called:** Swipe Left, Whip Tear, Woosh, whip pan transition, swish, swipe transition
- **Card:** https://skills.varg.ai/skills/whip-swipe/

### FFmpeg

Push with horizontal motion blur over the transition window (A is 5 s, T = 0.25 s):
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]fps=30,settb=AVTB,format=yuv420p[a];[1:v]fps=30,settb=AVTB,format=yuv420p[b];\
 [a][b]xfade=transition=slideleft:duration=0.25:offset=4.75,\
gblur=sigma=40:sigmaV=0:steps=2:enable='between(t,4.75,5.0)'[v]" -map "[v]" out.mp4
```
Add a whoosh: `[2:a]adelay=4700:all=1` mixed in with amix.

### HyperFrames

Shader `whip-pan` from `@hyperframes/shader-transitions` placed at the cut (t = 4 s):
```html
<div id="s1" class="scene" style="background:#0a0a0a"><video src="a.mp4" muted playsinline></video></div>
<div id="s2" class="scene" style="background:#0a0a0a"><video src="b.mp4" muted playsinline></video></div>
<script src="https://cdn.jsdelivr.net/npm/@hyperframes/shader-transitions/dist/index.global.js"></script>
<script>
  const tl = HyperShader.init({ bgColor: "#0a0a0a", scenes: ["s1", "s2"],
    transitions: [{ time: 4, shader: "whip-pan", duration: 0.35 }] });
  window.__timelines = window.__timelines || {}; window.__timelines["main"] = tl;
</script>
```
Each `.scene` needs an explicit background-color equal to `bgColor`. Or install the ready block: `npx hyperframes add whip-pan`. DOM version with matched velocity and capped motion blur: `npx hyperframes add whip-pan-cut`.

### Remotion

remocn `whipPan()` presentation (direction left/right/up/down, blur 24 px, ~26 frames):
```tsx
import {whipPan} from '@/components/remocn/whip-pan';
<TransitionSeries.Transition timing={linearTiming({durationInFrames: 26})} presentation={whipPan()} />
```
Without it: `slide({direction: 'from-right'})` with `linearTiming({durationInFrames: 8})`.

### CapCut

Transitions tab → Camera / Slide → Swipe Left, Whip Tear, Woosh, 2-Screen Swipe. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions.

### Components

- Whip Pan (hyperframes): `npx hyperframes add whip-pan` · https://skills.varg.ai/component/hf.whip-pan/
- Whip Pan Cut (hyperframes): `npx hyperframes add whip-pan-cut` · https://skills.varg.ai/component/hf.whip-pan-cut/
- Whip Pan (remocn): `npx shadcn@latest add @remocn/whip-pan` · https://skills.varg.ai/component/remocn.whip-pan/
- Motion Blur (hyperframes): `npx hyperframes add motion-blur` · https://skills.varg.ai/component/hf.motion-blur/

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [FFmpeg filters: gblur](https://ffmpeg.org/ffmpeg-filters.html#gblur) · [remocn: Whip Pan](https://remocn.dev/docs/transitions/whip-pan) · [HyperFrames: @hyperframes/shader-transitions](https://hyperframes.heygen.com/packages/shader-transitions) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py) · [CapCut transition names incl. Pro (pyCapCut metadata)](https://github.com/GuanYixuan/pyCapCut/blob/main/pycapcut/metadata/transition_meta.py)

## Spin

<a id="spin-rotate"></a>The frame rotates fast around its centre (with blur) and comes out of the spin on the next shot.

Built on [Revolve](https://github.com/gl-transitions/gl-transitions/blob/master/transitions/Revolve.glsl) by bread (gl-transitions), MIT. The write-up and recipes are varg's.

A spins 90–360° and blurs; B spins in from the same direction and stops upright.

- **When:** Party, music, playful and transformation edits; matches footage with rotating motion.
- **Watch out:** Long slow spins (nausea) and spinning text-heavy shots.
- **Timing:** 0.3–0.8 s (CapCut Rotate CW II 0.8 s), ease-in-out
- **Also called:** Rotate CW II, Rotate CCW II, Center Rotate, Axis Rotation, CW Swirl, spin transition, roll transition
- **Card:** https://skills.varg.ai/skills/spin-rotate/

### FFmpeg

Spin out of A in its last 0.3 s, spin into B in its first 0.3 s (rotate's angle is a per-frame expression):
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]trim=0:5,setpts=PTS-STARTPTS,rotate=a='if(gte(t,4.7),PI*((t-4.7)/0.3)^2,0)',gblur=sigma=10:enable='gte(t,4.85)'[a];\
 [1:v]trim=0:4,setpts=PTS-STARTPTS,rotate=a='if(lt(t,0.3),-PI*(1-t/0.3)^2,0)',gblur=sigma=10:enable='lt(t,0.15)'[b];\
 [a][b]concat=n=2:v=1:a=0[v]" -map "[v]" out.mp4
```
Corners show `fillcolor` (black); scale both by 1.5 before rotating to hide them.

### HyperFrames

```js
tl.to("#s1", { rotation: 180, scale: 1.4, filter: "blur(10px)", opacity: 0, duration: 0.35, ease: "power3.in" }, T);
tl.fromTo("#s2", { rotation: -180, scale: 1.4, filter: "blur(10px)", opacity: 0 }, { rotation: 0, scale: 1, filter: "blur(0px)", opacity: 1, duration: 0.35, ease: "power3.out" }, T);
```

### Remotion

Custom presentation: `transform: rotate(${presentationProgress * 180}deg) scale(...)` on the exiting side, the reverse on the entering side; or `glTransition({name: 'Revolve_Left'})` (1.x name, see notes).

### CapCut

Transitions tab → Camera → Rotate CW II, Rotate CCW II, Center Rotate, Axis Rotation, CW Swirl. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions.

### Components

- Revolve (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.revolve/
- DreamyZoom (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.dreamy-zoom/
- 3D Transitions (hyperframes): `npx hyperframes add transitions-3d` · https://skills.varg.ai/component/hf.transitions-3d/

Sources: [FFmpeg filters: rotate](https://ffmpeg.org/ffmpeg-filters.html#rotate) · [Remotion: custom presentations](https://www.remotion.dev/docs/transitions/presentations/custom) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py) · [CapCut transition names incl. Pro (pyCapCut metadata)](https://github.com/GuanYixuan/pyCapCut/blob/main/pycapcut/metadata/transition_meta.py)

## Camera Shake

<a id="camera-shake"></a>A short violent shake (often with a zoom) hits on the cut, like an impact or a bass hit.

Built on [Camera Shake](https://github.com/heygen-com/hyperframes/tree/main/registry/components/camera-shake) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

The image jolts in x/y and slightly in scale for a few frames around the cut, then calms.

- **When:** Drops, punches, slams, gaming and hype edits.
- **Watch out:** Shaking calm or informational content; long shakes.
- **Timing:** 0.2–0.8 s (CapCut Shake 3 0.8 s); strongest on the first 3–4 frames
- **Also called:** Shake 3, Jerky Camera, Zoom Shake 2, Shake down, impact shake, shake transition
- **Card:** https://skills.varg.ai/skills/camera-shake/

### FFmpeg

Shake the first 0.4 s of B with crop offsets driven by sin/cos (crop x/y are evaluated per frame):
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[1:v]crop=w=iw-48:h=ih-48:x='24+24*sin(t*61)*max(0,1-t/0.4)':y='24+24*cos(t*47)*max(0,1-t/0.4)',scale=1280:720,setsar=1[b];\
 [0:v][b]concat=n=2:v=1:a=0[v]" -map "[v]" out.mp4
```

### HyperFrames

`npx hyperframes add camera-shake` (nine measured handheld/telephoto/rig profiles for any wrapper).

### Remotion

Wrap B in `<AbsoluteFill style={{transform: `translate(${dx}px, ${dy}px)`}}>` where dx/dy come from `noise2D` (@remotion/noise) times a decaying envelope from `interpolate(frame, [0, 12], [1, 0])`. remocn `impact-shake`, `lens-zoom` include shake.

### CapCut

Transitions tab → Camera → Shake 3, Jerky Camera, Zoom Shake 2, Shake down. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions. Or Effects → Video effects → a Shake effect over the first frames of B.

### Components

- Camera Shake (hyperframes): `npx hyperframes add camera-shake` · https://skills.varg.ai/component/hf.camera-shake/
- Impact Shake (remocn): `npx shadcn@latest add @remocn/impact-shake` · https://skills.varg.ai/component/remocn.impact-shake/
- Lens Zoom (remocn): `npx shadcn@latest add @remocn/lens-zoom` · https://skills.varg.ai/component/remocn.lens-zoom/

Sources: [FFmpeg filters: crop](https://ffmpeg.org/ffmpeg-filters.html#crop) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py) · [CapCut transition names incl. Pro (pyCapCut metadata)](https://github.com/GuanYixuan/pyCapCut/blob/main/pycapcut/metadata/transition_meta.py)

## Glitch

<a id="glitch-transition"></a>The frame tears into displaced slices, colour channels split and noise flickers as A breaks into B.

Built on [Glitch](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/glitch) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Horizontal slice offsets, RGB fringes, block noise and a flicker for a few frames around the cut.

- **When:** Tech, gaming, cyber, music and edgy fashion pieces; "signal lost" moments.
- **Watch out:** Corporate or calm content; long glitches stop reading as an artefact.
- **Timing:** 0.2–0.5 s (CapCut Glitch 0.47 s, RGB Glitch 1.0 s); keep under ~20 frames
- **Also called:** Glitch, RGB Glitch, Color Glitch, Urban Glitch, Signal Glitch 2, TV Flickers, digital glitch, datamosh
- **Card:** https://skills.varg.ai/skills/glitch-transition/

### FFmpeg

Hard cut with RGB split + temporal noise for 0.3 s around it (both filters support `enable`):
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]trim=0:4,setpts=PTS-STARTPTS[x];[1:v]trim=0:4,setpts=PTS-STARTPTS[y];\
 [x][y]concat=n=2:v=1:a=0,\
rgbashift=rh=-24:bh=24:enable='between(t,3.85,4.15)',\
noise=alls=60:allf=t:enable='between(t,3.85,4.15)'[v]" -map "[v]" out.mp4
```
Add `xfade=transition=pixelize` or `hlslice` for blockier tearing.

### HyperFrames

Shader `glitch` from `@hyperframes/shader-transitions` placed at the cut (t = 4 s):
```html
<div id="s1" class="scene" style="background:#0a0a0a"><video src="a.mp4" muted playsinline></video></div>
<div id="s2" class="scene" style="background:#0a0a0a"><video src="b.mp4" muted playsinline></video></div>
<script src="https://cdn.jsdelivr.net/npm/@hyperframes/shader-transitions/dist/index.global.js"></script>
<script>
  const tl = HyperShader.init({ bgColor: "#0a0a0a", scenes: ["s1", "s2"],
    transitions: [{ time: 4, shader: "glitch", duration: 0.5 }] });
  window.__timelines = window.__timelines || {}; window.__timelines["main"] = tl;
</script>
```
Each `.scene` needs an explicit background-color equal to `bgColor`. Or install the ready block: `npx hyperframes add glitch`.

### Remotion

remocn `glitchCut()` presentation, 12 frames recommended:
```tsx
import {glitchCut} from '@/components/remocn/glitch-cut';
<TransitionSeries.Transition timing={linearTiming({durationInFrames: 12})} presentation={glitchCut()} />
```
It needs HTML-in-canvas for the full effect (CSS fallback elsewhere); render with `--gl=angle`. GL: `GlitchMemories`, `GlitchDisplace`, `StripDatamoshGlitch`.

### CapCut

Transitions tab → Glitch → Glitch, RGB Glitch, Color Glitch, Urban Glitch, Signal Glitch 2, TV Flickers. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions.

### Components

- Glitch (hyperframes): `npx hyperframes add glitch` · https://skills.varg.ai/component/hf.glitch/
- Glitch Cut (remocn): `npx shadcn@latest add @remocn/glitch-cut` · https://skills.varg.ai/component/remocn.glitch-cut/
- GlitchMemories (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.glitch-memories/
- GlitchDisplace (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.glitch-displace/
- StripDatamoshGlitch (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.strip-datamosh-glitch/
- Pixel Sort (remocn): `npx shadcn@latest add @remocn/pixel-sort` · https://skills.varg.ai/component/remocn.pixel-sort/
- Displacement (remocn): `npx shadcn@latest add @remocn/displacement` · https://skills.varg.ai/component/remocn.displacement/

Sources: [FFmpeg filters: rgbashift](https://ffmpeg.org/ffmpeg-filters.html#rgbashift) · [remocn: Glitch Cut](https://remocn.dev/docs/transitions/glitch-cut) · [HyperFrames: @hyperframes/shader-transitions](https://hyperframes.heygen.com/packages/shader-transitions) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py) · [CapCut transition names incl. Pro (pyCapCut metadata)](https://github.com/GuanYixuan/pyCapCut/blob/main/pycapcut/metadata/transition_meta.py)

## Blur Through

<a id="blur-transition"></a>A blurs out of focus, the shots swap at peak blur, and B pulls back into focus.

Built on [Blur Transitions](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/transitions-blur) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Soft defocus (or a directional smear) hides the swap; like a lens racking between two scenes.

- **When:** Calm, premium and lifestyle pieces; when two shots have very different colours.
- **Watch out:** Very short blurs read as a focus mistake; give the peak a few frames.
- **Timing:** 0.5–1.0 s (CapCut Blur 0.47 s); calm 20–30 px blur, high energy 3–6 px
- **Also called:** Blur, Horizontal Blur, Vertical Blur, Blurred Highlight, focus pull, defocus transition
- **Card:** https://skills.varg.ai/skills/blur-transition/

### FFmpeg

Crossfade with a symmetrical Gaussian blur peak (A 5 s, T 0.6 s):
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]fps=30,settb=AVTB,format=yuv420p[a];[1:v]fps=30,settb=AVTB,format=yuv420p[b];\
 [a][b]xfade=transition=fade:duration=0.6:offset=4.4,gblur=sigma=20:enable='between(t,4.5,4.9)'[v]" -map "[v]" out.mp4
```
`xfade=transition=hblur` is a built-in horizontal-blur crossfade.

### HyperFrames

CSS blur crossfade:
```js
tl.to("#s1", { filter: "blur(10px)", scale: 1.03, opacity: 0, duration: 0.6, ease: "power2.inOut" }, T);
tl.fromTo("#s2", { filter: "blur(10px)", scale: 0.97, opacity: 0 }, { filter: "blur(0px)", scale: 1, opacity: 1, duration: 0.6, ease: "power2.inOut" }, T);
```
Block: `transitions-blur`; rack focus: `rack-focus`.

### Remotion

```tsx
import {TransitionSeries, linearTiming, springTiming} from '@remotion/transitions';
import {linearBlur} from '@remotion/transitions/linear-blur';

<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={90}><ShotA /></TransitionSeries.Sequence>
  <TransitionSeries.Transition presentation={linearBlur({intensity: 0.1})} timing={linearTiming({durationInFrames: 20})} />
  <TransitionSeries.Sequence durationInFrames={90}><ShotB /></TransitionSeries.Sequence>
</TransitionSeries>
```
Total = 90 + 90 - 20 frames: the transition overlaps the two shots.
Shader presentations are built on Remotion's HTML-in-canvas: renders work out of the box (`--gl=angle`, or `--gl=swangle` without a GPU); the Studio preview needs Chrome with `chrome://flags/#canvas-draw-element` enabled. CSS-only alternative: custom presentation with `filter: blur(${p*20}px)`; `blurSlide({})` adds motion.

### CapCut

Transitions tab → Blur → Blur, Horizontal Blur, Vertical Blur, Vertical Blur II, Blurred Highlight. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions.

### Components

- Blur Transitions (hyperframes): `npx hyperframes add transitions-blur` · https://skills.varg.ai/component/hf.transitions-blur/
- LinearBlur (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.linear-blur/
- Focus Pull (remocn): `npx shadcn@latest add @remocn/focus-pull` · https://skills.varg.ai/component/remocn.focus-pull/
- Rack Focus (hyperframes): `npx hyperframes add rack-focus` · https://skills.varg.ai/component/hf.rack-focus/

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [FFmpeg filters: gblur](https://ffmpeg.org/ffmpeg-filters.html#gblur) · [Remotion: presentations](https://www.remotion.dev/docs/transitions/presentations) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py)

## Light Leak

<a id="light-leak"></a>A warm wash of orange/red light drifts across and blows out the frame at the cut, then fades on B.

Built on [Light Leak](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/light-leak) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Soft, organic colour flares (like film exposed to light) cover the cut and recede.

- **When:** Memories, travel, weddings, retro or film-look edits, warm brand stories.
- **Watch out:** Cold, clinical or tech content; leaks that are visibly shaped blobs.
- **Timing:** 0.7–1.2 s (CapCut Light Leaks 1.0 s)
- **Also called:** Light Leaks, Camera Glow, Light Beam, light leak transition, analog leak
- **Card:** https://skills.varg.ai/skills/light-leak/

### FFmpeg

Overlay a light-leak clip (stock or generated) in screen mode over a short crossfade:
```bash
ffmpeg -i a.mp4 -i b.mp4 -i leak.mp4 -filter_complex \
"[0:v]fps=30,settb=AVTB,format=yuv420p[a];[1:v]fps=30,settb=AVTB,format=yuv420p[b];\
 [a][b]xfade=transition=fade:duration=0.4:offset=4.6[x];\
 [2:v]fps=30,settb=AVTB,format=yuv420p,scale=1280:720,setpts=PTS-STARTPTS+4.2/TB[l];\
 [x][l]blend=all_mode=screen:shortest=0:eof_action=pass[v]" -map "[v]" out.mp4
```
(`blend` needs equal sizes and formats; a 1 s leak clip on black starts at 4.2 s.)

### HyperFrames

Shader `light-leak` from `@hyperframes/shader-transitions` placed at the cut (t = 4 s):
```html
<div id="s1" class="scene" style="background:#0a0a0a"><video src="a.mp4" muted playsinline></video></div>
<div id="s2" class="scene" style="background:#0a0a0a"><video src="b.mp4" muted playsinline></video></div>
<script src="https://cdn.jsdelivr.net/npm/@hyperframes/shader-transitions/dist/index.global.js"></script>
<script>
  const tl = HyperShader.init({ bgColor: "#0a0a0a", scenes: ["s1", "s2"],
    transitions: [{ time: 4, shader: "light-leak", duration: 0.7 }] });
  window.__timelines = window.__timelines || {}; window.__timelines["main"] = tl;
</script>
```
Each `.scene` needs an explicit background-color equal to `bgColor`. Or install the ready block: `npx hyperframes add light-leak`. CSS overlay: `organic-light-leak-overlay`.

### Remotion

Light leak on the cut without shortening the timeline:
```tsx
import {lightLeak} from '@remotion/effects/light-leak';
<TransitionSeries.Overlay durationInFrames={30}>
  <Solid width={1920} height={1080} effects={[lightLeak({seed: 3, hueShift: 0, progress: interpolate(useCurrentFrame(), [0, 30], [0, 1])})]} />
</TransitionSeries.Overlay>
```
(`<LightLeak>` from `@remotion/light-leaks` is deprecated in favour of this effect; it reveals in the first half of progress and retracts in the second.)

### CapCut

Transitions tab → Light Effect → Light Leaks, Camera Glow, Light Beam. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions.

### Components

- Light Leak (hyperframes): `npx hyperframes add light-leak` · https://skills.varg.ai/component/hf.light-leak/
- Organic Light Leak Overlay (hyperframes): `npx hyperframes add organic-light-leak-overlay` · https://skills.varg.ai/component/hf.organic-light-leak-overlay/
- Light Leak (remocn): `npx shadcn@latest add @remocn/light-leak` · https://skills.varg.ai/component/remocn.light-leak/
- Light Transitions (hyperframes): `npx hyperframes add transitions-light` · https://skills.varg.ai/component/hf.transitions-light/

Sources: [Remotion: lightLeak() effect](https://www.remotion.dev/docs/effects/light-leak) · [Remotion: <TransitionSeries>](https://www.remotion.dev/docs/transitions/transitionseries) · [HyperFrames: @hyperframes/shader-transitions](https://hyperframes.heygen.com/packages/shader-transitions) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py) · [CapCut transition names incl. Pro (pyCapCut metadata)](https://github.com/GuanYixuan/pyCapCut/blob/main/pycapcut/metadata/transition_meta.py)

## Film Burn

<a id="film-burn"></a>Hot glowing holes or a flare burn across A like overheated film and reveal B.

Built on [FilmBurn](https://github.com/gl-transitions/gl-transitions/blob/master/transitions/FilmBurn.glsl) by anastasia-dunbar (gl-transitions), MIT. The write-up and recipes are varg's.

Bright orange-white burn edges eat the frame; the next shot shows through the burnt areas.

- **When:** Vintage, music video, documentary archive, dramatic chapter changes.
- **Watch out:** Mixing it with clean modern UI footage; it reads as a theme clash.
- **Timing:** 0.5–1.0 s (CapCut Film Burn 0.7 s, Burn 0.47 s)
- **Also called:** Film Burn, Burn, film burn transition, burn through, ember burn
- **Card:** https://skills.varg.ai/skills/film-burn/

### FFmpeg

No built-in burn. Screen-blend a film-burn overlay clip over a crossfade (same pattern as the Light Leak card), or run GL `FilmBurn`/`BurnThrough` via editly (1.x names `FilmBurn`, `burn0`).

### HyperFrames

Shader `ridged-burn` from `@hyperframes/shader-transitions` placed at the cut (t = 4 s):
```html
<div id="s1" class="scene" style="background:#0a0a0a"><video src="a.mp4" muted playsinline></video></div>
<div id="s2" class="scene" style="background:#0a0a0a"><video src="b.mp4" muted playsinline></video></div>
<script src="https://cdn.jsdelivr.net/npm/@hyperframes/shader-transitions/dist/index.global.js"></script>
<script>
  const tl = HyperShader.init({ bgColor: "#0a0a0a", scenes: ["s1", "s2"],
    transitions: [{ time: 4, shader: "ridged-burn", duration: 0.7 }] });
  window.__timelines = window.__timelines || {}; window.__timelines["main"] = tl;
</script>
```
Each `.scene` needs an explicit background-color equal to `bgColor`. Or install the ready block: `npx hyperframes add ridged-burn`.

### Remotion

```tsx
import {TransitionSeries, linearTiming, springTiming} from '@remotion/transitions';
import {filmBurn} from '@remotion/transitions/film-burn';

<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={90}><ShotA /></TransitionSeries.Sequence>
  <TransitionSeries.Transition presentation={filmBurn({seed: 1})} timing={linearTiming({durationInFrames: 24})} />
  <TransitionSeries.Sequence durationInFrames={90}><ShotB /></TransitionSeries.Sequence>
</TransitionSeries>
```
Total = 90 + 90 - 24 frames: the transition overlaps the two shots.
Shader presentations are built on Remotion's HTML-in-canvas: renders work out of the box (`--gl=angle`, or `--gl=swangle` without a GPU); the Studio preview needs Chrome with `chrome://flags/#canvas-draw-element` enabled.

### CapCut

Transitions tab → Light Effect → Film Burn, Burn. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions.

### Components

- FilmBurn (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.film-burn/
- BurnThrough (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.burn-through/
- Ridged Burn (hyperframes): `npx hyperframes add ridged-burn` · https://skills.varg.ai/component/hf.ridged-burn/
- Ember Burn (remocn): `npx shadcn@latest add @remocn/ember-burn` · https://skills.varg.ai/component/remocn.ember-burn/

Sources: [Remotion: presentations](https://www.remotion.dev/docs/transitions/presentations) · [HyperFrames: @hyperframes/shader-transitions](https://hyperframes.heygen.com/packages/shader-transitions) · [GL Transitions gallery](https://gl-transitions.com) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py) · [CapCut transition names incl. Pro (pyCapCut metadata)](https://github.com/GuanYixuan/pyCapCut/blob/main/pycapcut/metadata/transition_meta.py)

## Light Sweep

<a id="light-sweep"></a>A bright band or lens flare sweeps across the frame and the shot changes behind it.

Built on [Light Transitions](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/transitions-light) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A diagonal streak of light crosses the image; at its brightest point A becomes B.

- **When:** Product shots, luxury, beauty and logo reveals.
- **Watch out:** Fake-looking hard-edged flares; keep the band soft and the colour matched to the scene.
- **Timing:** 0.5–0.8 s (CapCut Light Sweep II 0.8 s, Lumin Flash 0.8 s)
- **Also called:** Light Sweep II, Lumin Flash, Lightflow Scan, lens flare transition, shine sweep
- **Card:** https://skills.varg.ai/skills/light-sweep/

### FFmpeg

Moving soft white band (generated with geq) screen-blended over a fade:
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]fps=30,settb=AVTB,format=yuv420p[a];[1:v]fps=30,settb=AVTB,format=yuv420p[b];[a][b]xfade=transition=fade:duration=0.3:offset=4.7[x];\
 [x]geq=lum='min(255,lum(X,Y)+180*exp(-pow((X+Y*0.5-(T-4.5)*3000)/120,2)))':cb='cb(X,Y)':cr='cr(X,Y)'[v]" -map "[v]" out.mp4
```
(geq is slow; for long clips trim the window first.)

### HyperFrames

Light family blocks: `transitions-light`, overlay `editorial-flash-overlay`; or tween a wide (2400px+) soft gradient bar across with `mix-blend-mode: screen` while swapping scenes at its peak.

### Remotion

`<TransitionSeries.Overlay durationInFrames={20}>` containing a rotated white gradient `<div>` whose `translateX` is interpolated from -100% to 100%, with `mixBlendMode: 'screen'`.

### CapCut

Transitions tab → Light Effect → Light Sweep II, Lumin Flash, Lightflow Scan. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions.

### Components

- Light Transitions (hyperframes): `npx hyperframes add transitions-light` · https://skills.varg.ai/component/hf.transitions-light/
- Editorial Flash Overlay (hyperframes): `npx hyperframes add editorial-flash-overlay` · https://skills.varg.ai/component/hf.editorial-flash-overlay/
- Light Leak (hyperframes): `npx hyperframes add light-leak` · https://skills.varg.ai/component/hf.light-leak/

Sources: [Remotion: <TransitionSeries>](https://www.remotion.dev/docs/transitions/transitionseries) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py) · [CapCut transition names incl. Pro (pyCapCut metadata)](https://github.com/GuanYixuan/pyCapCut/blob/main/pycapcut/metadata/transition_meta.py)

## Chromatic Split

<a id="chromatic-split"></a>Red, green and blue channels pull apart around the cut, then snap back together on the new shot.

Built on [Chromatic Aberration Wipe](https://github.com/heygen-com/hyperframes/tree/main/registry/components/chromatic-aberration-wipe) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Colour ghosts offset horizontally or radially for a few frames, with a slight zoom.

- **When:** Fashion, music, tech promos; as a lighter alternative to a full glitch.
- **Watch out:** Large offsets on text; keep the split brief.
- **Timing:** 0.2–0.5 s; peak offset on the cut
- **Also called:** RGB split, chromatic aberration transition, colour fringe, Rainbow Warp
- **Card:** https://skills.varg.ai/skills/chromatic-split/

### FFmpeg

Channel split ramping around a cut (rgbashift supports runtime `enable`; offsets are fixed per window, so stack 2 windows for a ramp):
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v][1:v]concat=n=2:v=1:a=0,\
rgbashift=rh=-10:bh=10:enable='between(t,3.8,3.9)+between(t,4.1,4.2)',\
rgbashift=rh=-30:bh=30:gv=6:enable='between(t,3.9,4.1)'[v]" -map "[v]" out.mp4
```

### HyperFrames

Shader `chromatic-split` from `@hyperframes/shader-transitions` placed at the cut (t = 4 s):
```html
<div id="s1" class="scene" style="background:#0a0a0a"><video src="a.mp4" muted playsinline></video></div>
<div id="s2" class="scene" style="background:#0a0a0a"><video src="b.mp4" muted playsinline></video></div>
<script src="https://cdn.jsdelivr.net/npm/@hyperframes/shader-transitions/dist/index.global.js"></script>
<script>
  const tl = HyperShader.init({ bgColor: "#0a0a0a", scenes: ["s1", "s2"],
    transitions: [{ time: 4, shader: "chromatic-split", duration: 0.5 }] });
  window.__timelines = window.__timelines || {}; window.__timelines["main"] = tl;
</script>
```
Each `.scene` needs an explicit background-color equal to `bgColor`. Or install the ready block: `npx hyperframes add chromatic-radial-split`. Slide variant: `npx hyperframes add chromatic-aberration-wipe`.

### Remotion

Custom presentation rendering three copies of `children` with `mixBlendMode: 'screen'`, tinted R/G/B via CSS filters and offset by `presentationProgress`; or `@remotion/effects/chromatic-aberration` on a canvas-based `<Video>`.

### CapCut

Transitions tab → Glitch / Distortion → RGB Glitch, Rainbow Warp. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions. Or Effects → Video effects → an RGB split effect for a few frames.

### Components

- Chromatic Aberration Wipe (hyperframes): `npx hyperframes add chromatic-aberration-wipe` · https://skills.varg.ai/component/hf.chromatic-aberration-wipe/
- Chromatic Radial Split (hyperframes): `npx hyperframes add chromatic-radial-split` · https://skills.varg.ai/component/hf.chromatic-radial-split/
- Gravitational Lens (hyperframes): `npx hyperframes add gravitational-lens` · https://skills.varg.ai/component/hf.gravitational-lens/

Sources: [FFmpeg filters: rgbashift](https://ffmpeg.org/ffmpeg-filters.html#rgbashift) · [HyperFrames: @hyperframes/shader-transitions](https://hyperframes.heygen.com/packages/shader-transitions) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py)

## Slide / Push

<a id="slide-push"></a>B pushes A out of frame (push), slides over it (cover) or A slides away to reveal B (reveal).

Built on [Directional Wipe](https://github.com/heygen-com/hyperframes/tree/main/registry/components/directional-wipe) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Hard-edged panels move in one direction; reads like swiping between cards or pages.

- **When:** Lists, steps, app demos, editorial and corporate explainers; "next point".
- **Watch out:** Mixing directions randomly; keep one direction for "forward".
- **Timing:** 0.3–0.5 s (CapCut Slide/Left/Right 0.47 s), power3.inOut
- **Also called:** Slide, Left, Right, Up, Push Away 2, push transition, cover, reveal
- **Card:** https://skills.varg.ai/skills/slide-push/

### FFmpeg

Same size/fps/pixel format on both inputs (see the Normalize card). offset = duration(A) - T = 5.0 - 0.4 = 4.6.
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]fps=30,settb=AVTB,format=yuv420p[a];[1:v]fps=30,settb=AVTB,format=yuv420p[b];\
[a][b]xfade=transition=slideleft:duration=0.4:offset=4.6[v];\
[0:a][1:a]acrossfade=d=0.4[au]" \
  -map "[v]" -map "[au]" -c:v libx264 -crf 18 -c:a aac out.mp4
```
Push = `slideleft|slideright|slideup|slidedown`; cover = `coverleft…coverdown`; reveal = `revealleft…revealdown`; soft-edged wipe = `smoothleft…`.

### HyperFrames

```js
tl.to("#s1", { x: -1920, duration: 0.5, ease: "power3.inOut" }, T);
tl.fromTo("#s2", { x: 1920, opacity: 1 }, { x: 0, duration: 0.5, ease: "power3.inOut" }, T);
```
Blocks: `directional-wipe`, `transitions-push`, `transitions-cover`; elastic: `rubber-band-bumper`.

### Remotion

```tsx
import {TransitionSeries, linearTiming, springTiming} from '@remotion/transitions';
import {slide} from '@remotion/transitions/slide';

<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={90}><ShotA /></TransitionSeries.Sequence>
  <TransitionSeries.Transition presentation={slide({direction: 'from-right'})} timing={springTiming({config: {damping: 200}, durationInFrames: 15})} />
  <TransitionSeries.Sequence durationInFrames={90}><ShotB /></TransitionSeries.Sequence>
</TransitionSeries>
```
Total = 90 + 90 - 15 frames: the transition overlaps the two shots.
`slide()` is also the default presentation; directions: from-left, from-right, from-top, from-bottom.

### CapCut

Transitions tab → Slide → Slide, Left, Right, Up, Push Away 2, Corner Slide. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions.

### Components

- Directional Wipe (hyperframes): `npx hyperframes add directional-wipe` · https://skills.varg.ai/component/hf.directional-wipe/
- Push Transitions (hyperframes): `npx hyperframes add transitions-push` · https://skills.varg.ai/component/hf.transitions-push/
- Cover Transitions (hyperframes): `npx hyperframes add transitions-cover` · https://skills.varg.ai/component/hf.transitions-cover/
- Slide Swap (remocn): `npx shadcn@latest add @remocn/slide-swap` · https://skills.varg.ai/component/remocn.slide-swap/
- Rubber Band Bumper (hyperframes): `npx hyperframes add rubber-band-bumper` · https://skills.varg.ai/component/hf.rubber-band-bumper/

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [Remotion: presentations](https://www.remotion.dev/docs/transitions/presentations) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py) · [CapCut transition names incl. Pro (pyCapCut metadata)](https://github.com/GuanYixuan/pyCapCut/blob/main/pycapcut/metadata/transition_meta.py)

## Wipe

<a id="wipe"></a>A moving edge replaces A with B across the frame while both images stay still.

Built on [Directional Wipe](https://github.com/heygen-com/hyperframes/tree/main/registry/components/directional-wipe) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A straight (or soft) line travels across; on one side A, on the other B.

- **When:** Classic "meanwhile", retro TV, comparisons and before/after.
- **Watch out:** Diagonal and corner wipes in serious content can look dated.
- **Timing:** 0.4–0.8 s (CapCut Wipe Left/Right 0.47 s), linear or ease-in-out
- **Also called:** Wipe Left, Wipe Right, Wipe Up, linear wipe, edge wipe
- **Card:** https://skills.varg.ai/skills/wipe/

### FFmpeg

Same size/fps/pixel format on both inputs (see the Normalize card). offset = duration(A) - T = 5.0 - 0.5 = 4.5.
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]fps=30,settb=AVTB,format=yuv420p[a];[1:v]fps=30,settb=AVTB,format=yuv420p[b];\
[a][b]xfade=transition=wipeleft:duration=0.5:offset=4.5[v];\
[0:a][1:a]acrossfade=d=0.5[au]" \
  -map "[v]" -map "[au]" -c:v libx264 -crf 18 -c:a aac out.mp4
```
Others: wiperight, wipeup, wipedown, wipetl/wipetr/wipebl/wipebr, diagtl…diagbr, smoothleft… (soft edge).

### HyperFrames

Clip-path wipe on the incoming wrapper:
```js
tl.fromTo("#s2", { clipPath: "polygon(0 0,0 0,0 100%,0 100%)", opacity: 1 },
  { clipPath: "polygon(0 0,100% 0,100% 100%,0 100%)", duration: 0.5, ease: "power2.inOut" }, T);
```
Comparison divider: `before-after-wipe`.

### Remotion

```tsx
import {TransitionSeries, linearTiming, springTiming} from '@remotion/transitions';
import {wipe} from '@remotion/transitions/wipe';

<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={90}><ShotA /></TransitionSeries.Sequence>
  <TransitionSeries.Transition presentation={wipe({direction: 'from-left'})} timing={linearTiming({durationInFrames: 20})} />
  <TransitionSeries.Sequence durationInFrames={90}><ShotB /></TransitionSeries.Sequence>
</TransitionSeries>
```
Total = 90 + 90 - 20 frames: the transition overlaps the two shots.
wipe() directions include diagonals: from-top-left, from-top-right, from-bottom-left, from-bottom-right.

### CapCut

Transitions tab → Slide / Basic → Wipe Left, Wipe Right, Wipe Up. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions.

### Components

- Directional Wipe (hyperframes): `npx hyperframes add directional-wipe` · https://skills.varg.ai/component/hf.directional-wipe/
- Before After Wipe (hyperframes): `npx hyperframes add before-after-wipe` · https://skills.varg.ai/component/hf.before-after-wipe/
- DirectionalWarp (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.directional-warp/
- Wind (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.wind/
- Caret Wipe (remocn): `npx shadcn@latest add @remocn/caret-wipe` · https://skills.varg.ai/component/remocn.caret-wipe/
- Wave Wipe (remocn): `npx shadcn@latest add @remocn/wave-wipe` · https://skills.varg.ai/component/remocn.wave-wipe/

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [Remotion: presentations](https://www.remotion.dev/docs/transitions/presentations) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py)

## Circle Iris

<a id="circle-iris"></a>B opens from (or A closes into) a growing circle, like an old-cartoon iris or a lens opening.

Built on [SDF Iris](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/sdf-iris) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A circular window expands from the subject or the centre until B fills the frame.

- **When:** Spotlighting a subject, playful and retro edits, focus on a product.
- **Watch out:** Off-centre irises that cut through faces; centre the circle on the subject.
- **Timing:** 0.5–0.8 s, ease-in-out (hold 2–6 frames as a dot for the cartoon iris)
- **Also called:** circle mask, iris wipe, iris in, iris out, circle open, Circular Slices II
- **Card:** https://skills.varg.ai/skills/circle-iris/

### FFmpeg

Same size/fps/pixel format on both inputs (see the Normalize card). offset = duration(A) - T = 5.0 - 0.6 = 4.4.
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]fps=30,settb=AVTB,format=yuv420p[a];[1:v]fps=30,settb=AVTB,format=yuv420p[b];\
[a][b]xfade=transition=circleopen:duration=0.6:offset=4.4[v];\
[0:a][1:a]acrossfade=d=0.6[au]" \
  -map "[v]" -map "[au]" -c:v libx264 -crf 18 -c:a aac out.mp4
```
`circleclose` shrinks a circle; `circlecrop` irises out to black and back in. Off-centre: `transition=custom:expr='if(lt(hypot(X-800,Y-400),(1-P)*1600),B,A)'` (P runs 1→0 during xfade).

### HyperFrames

Shader `sdf-iris` from `@hyperframes/shader-transitions` placed at the cut (t = 4 s):
```html
<div id="s1" class="scene" style="background:#0a0a0a"><video src="a.mp4" muted playsinline></video></div>
<div id="s2" class="scene" style="background:#0a0a0a"><video src="b.mp4" muted playsinline></video></div>
<script src="https://cdn.jsdelivr.net/npm/@hyperframes/shader-transitions/dist/index.global.js"></script>
<script>
  const tl = HyperShader.init({ bgColor: "#0a0a0a", scenes: ["s1", "s2"],
    transitions: [{ time: 4, shader: "sdf-iris", duration: 0.7 }] });
  window.__timelines = window.__timelines || {}; window.__timelines["main"] = tl;
</script>
```
Each `.scene` needs an explicit background-color equal to `bgColor`. Or install the ready block: `npx hyperframes add sdf-iris`. CSS: `npx hyperframes add iris-reveal` (clip-path circle from an authored origin).

### Remotion

```tsx
import {TransitionSeries, linearTiming, springTiming} from '@remotion/transitions';
import {iris} from '@remotion/transitions/iris';

<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={90}><ShotA /></TransitionSeries.Sequence>
  <TransitionSeries.Transition presentation={iris({width: 1920, height: 1080})} timing={linearTiming({durationInFrames: 20})} />
  <TransitionSeries.Sequence durationInFrames={90}><ShotB /></TransitionSeries.Sequence>
</TransitionSeries>
```
Total = 90 + 90 - 20 frames: the transition overlaps the two shots.
`iris()` requires `width` and `height` (the composition size).

### CapCut

Transitions tab → Mask → circle-shaped mask transitions (e.g. Circular Slices II). Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions. Hand-made: add a Mask → Circle on B and keyframe its size from 0 to full.

### Components

- SDF Iris (hyperframes): `npx hyperframes add sdf-iris` · https://skills.varg.ai/component/hf.sdf-iris/
- Iris Reveal (hyperframes): `npx hyperframes add iris-reveal` · https://skills.varg.ai/component/hf.iris-reveal/
- Iris Wipe (remocn): `npx shadcn@latest add @remocn/iris-wipe` · https://skills.varg.ai/component/remocn.iris-wipe/
- Radial Transitions (hyperframes): `npx hyperframes add transitions-radial` · https://skills.varg.ai/component/hf.transitions-radial/

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [Remotion: presentations](https://www.remotion.dev/docs/transitions/presentations) · [HyperFrames: @hyperframes/shader-transitions](https://hyperframes.heygen.com/packages/shader-transitions) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py)

## Heart Mask

<a id="heart-mask"></a>B appears through a heart shape that grows to fill the frame. Social, playful and romantic.

A heart-shaped window opens from the centre and expands until B covers everything.

- **When:** Couples, weddings, Valentine's, "favourite" moments, social posts.
- **Watch out:** Anything serious or corporate.
- **Timing:** 0.5–0.8 s, ease-out
- **Also called:** heart wipe, heart transition, love transition
- **Card:** https://skills.varg.ai/skills/heart-mask/

### FFmpeg

xfade custom expression with an implicit heart curve (P runs 1→0, so the heart grows as P falls):
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]fps=30,settb=AVTB,format=yuv420p[a];[1:v]fps=30,settb=AVTB,format=yuv420p[b];\
 [a][b]xfade=transition=custom:duration=0.7:offset=4.3:\
expr='if(lte(pow(pow((X-W/2)/(W*(1-P)+1),2)+pow((H/2-Y)/(W*(1-P)+1),2)-0.09,3)-pow((X-W/2)/(W*(1-P)+1),2)*pow((H/2-Y)/(W*(1-P)+1),3),0),B,A)'[v]" -map "[v]" out.mp4
```

### HyperFrames

Tween an SVG heart `clipPath` (or a CSS `mask-image` of a heart) on the incoming scene from scale 0 to 4, transform-origin centre.

### Remotion

`glTransition({name: 'heart'})` with @gl-transitions/remotion 0.1.0 (1.x name; `HeartWipe` in gl-transitions 2.0).

### CapCut

Transitions tab → Mask / Social media → heart-shaped transitions (names vary by version). Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions. Hand-made: Mask → Heart on B, keyframe its size.

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [@gl-transitions/remotion (README)](https://github.com/gl-transitions/gl-transitions/tree/master/packages/remotion) · [gl-transitions 2.0 changelog (renames)](https://github.com/gl-transitions/gl-transitions/blob/master/packages/gl-transitions/CHANGELOG.md) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py)

## Ink and Brush Reveal

<a id="ink-brush"></a>An organic ink blot, brush stroke or smoke plume spreads over A and B shows through the painted area.

Built on [Scribble Transition](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/hw-scribble-transition) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Irregular, hand-made edges bloom across the frame, unlike geometric wipes.

- **When:** Art, travel, food, Asian-inspired themes, creative portfolios.
- **Watch out:** Tech and data content; low-resolution matte assets with visible pixel edges.
- **Timing:** 0.5–2.0 s (CapCut White Ink 0.47 s, Reveal Brush 2.0 s)
- **Also called:** White Ink, Reveal Brush, ink transition, brush stroke transition, paint reveal, Black smoke, White smoke
- **Card:** https://skills.varg.ai/skills/ink-brush/

### FFmpeg

Use an ink/brush matte video (white paint on black) as the mask:
```bash
ffmpeg -i a.mp4 -i b.mp4 -i ink_matte.mp4 -filter_complex \
"[0:v]fps=30,settb=AVTB,format=yuv420p,scale=1280:720[a];[1:v]fps=30,settb=AVTB,format=yuv420p,scale=1280:720[b];\
 [2:v]fps=30,settb=AVTB,format=yuv420p,scale=1280:720,format=gray,format=yuv420p[m];\
 [a][b][m]maskedmerge[v]" -map "[v]" out.mp4
```
(maskedmerge shows B where the matte is white; align the matte's start with `setpts=PTS-STARTPTS+<cut>/TB` and pad with black.)

### HyperFrames

`npx hyperframes add hw-scribble-transition` (scribble bands cover the frame, the host cuts beneath, then clear); smoke-like organic: `domain-warp-dissolve`.

### Remotion

`glTransition({name: 'luma', textures: {luma: staticFile('brush.png')}})` animates a luma matte image (1.x name `luma`, 2.0 `LumaWipe`); or a custom presentation using a matte `<Video>` as CSS `mask-image`.

### CapCut

Transitions tab → Mask / Overlay → White Ink, Reveal Brush, Black smoke, White smoke. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions.

### Components

- Scribble Transition (hyperframes): `npx hyperframes add hw-scribble-transition` · https://skills.varg.ai/component/hf.hw-scribble-transition/
- Domain Warp Dissolve (hyperframes): `npx hyperframes add domain-warp-dissolve` · https://skills.varg.ai/component/hf.domain-warp-dissolve/
- Smoke Dissolve (remocn): `npx shadcn@latest add @remocn/smoke-dissolve` · https://skills.varg.ai/component/remocn.smoke-dissolve/
- Paper Tear (remocn): `npx shadcn@latest add @remocn/paper-tear` · https://skills.varg.ai/component/remocn.paper-tear/

Sources: [@gl-transitions/remotion (README)](https://github.com/gl-transitions/gl-transitions/tree/master/packages/remotion) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py) · [CapCut transition names incl. Pro (pyCapCut metadata)](https://github.com/GuanYixuan/pyCapCut/blob/main/pycapcut/metadata/transition_meta.py)

## Gradient (Luma) Wipe

<a id="luma-gradient-wipe"></a>B appears in the order of a grayscale map (gradient, noise or the image's own brightness).

Built on [Domain Warp Dissolve](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/domain-warp-dissolve) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Dark-to-light areas switch first, giving soft, organic or shaped reveals instead of one straight edge.

- **When:** Elegant scene changes, nature, dreamy edits; custom shapes from any grayscale matte.
- **Watch out:** Noisy mattes on noisy footage look like compression artefacts.
- **Timing:** 0.6–1.2 s (CapCut Gradient Wipe 0.47 s)
- **Also called:** Gradient Wipe, luma wipe, luma fade, noise dissolve, Dissolve II
- **Card:** https://skills.varg.ai/skills/luma-gradient-wipe/

### FFmpeg

Soft diagonal luma wipe with an xfade custom expression (0.15 softness band):
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]fps=30,settb=AVTB,format=yuv420p[a];[1:v]fps=30,settb=AVTB,format=yuv420p[b];\
 [a][b]xfade=transition=custom:duration=0.8:offset=4.2:\
expr='A*clip(((X/W+Y/H)/2-(1-P)*1.15+0.15)/0.15,0,1)+B*(1-clip(((X/W+Y/H)/2-(1-P)*1.15+0.15)/0.15,0,1))'[v]" -map "[v]" out.mp4
```
For an arbitrary matte use `maskedmerge` with a thresholded matte video, or GL `LumaWipe` via editly (1.x `luma`).

### HyperFrames

Shader `domain-warp` from `@hyperframes/shader-transitions` placed at the cut (t = 4 s):
```html
<div id="s1" class="scene" style="background:#0a0a0a"><video src="a.mp4" muted playsinline></video></div>
<div id="s2" class="scene" style="background:#0a0a0a"><video src="b.mp4" muted playsinline></video></div>
<script src="https://cdn.jsdelivr.net/npm/@hyperframes/shader-transitions/dist/index.global.js"></script>
<script>
  const tl = HyperShader.init({ bgColor: "#0a0a0a", scenes: ["s1", "s2"],
    transitions: [{ time: 4, shader: "domain-warp", duration: 0.8 }] });
  window.__timelines = window.__timelines || {}; window.__timelines["main"] = tl;
</script>
```
Each `.scene` needs an explicit background-color equal to `bgColor`. Or install the ready block: `npx hyperframes add domain-warp-dissolve`.

### Remotion

```tsx
import {TransitionSeries, linearTiming, springTiming} from '@remotion/transitions';
import {dissolve} from '@remotion/transitions/dissolve';

<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={90}><ShotA /></TransitionSeries.Sequence>
  <TransitionSeries.Transition presentation={dissolve({})} timing={linearTiming({durationInFrames: 24})} />
  <TransitionSeries.Sequence durationInFrames={90}><ShotB /></TransitionSeries.Sequence>
</TransitionSeries>
```
Total = 90 + 90 - 24 frames: the transition overlaps the two shots.
Shader presentations are built on Remotion's HTML-in-canvas: renders work out of the box (`--gl=angle`, or `--gl=swangle` without a GPU); the Studio preview needs Chrome with `chrome://flags/#canvas-draw-element` enabled. Remotion's `dissolve` is a shader dissolve with a glowing edge (lineWidth, spreadColor, hotColor), not a plain crossfade.

### CapCut

Transitions tab → Basic / Mask → Gradient Wipe, Dissolve II, Dissolve III. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions.

### Components

- Domain Warp Dissolve (hyperframes): `npx hyperframes add domain-warp-dissolve` · https://skills.varg.ai/component/hf.domain-warp-dissolve/
- Perlin Dissolve (remocn): `npx shadcn@latest add @remocn/perlin-dissolve` · https://skills.varg.ai/component/remocn.perlin-dissolve/
- Warp Dissolve (remocn): `npx shadcn@latest add @remocn/warp-dissolve` · https://skills.varg.ai/component/remocn.warp-dissolve/
- Grain Dissolve (remocn): `npx shadcn@latest add @remocn/grain-dissolve` · https://skills.varg.ai/component/remocn.grain-dissolve/
- LuminanceMelt (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.luminance-melt/

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [Remotion: presentations](https://www.remotion.dev/docs/transitions/presentations) · [HyperFrames: @hyperframes/shader-transitions](https://hyperframes.heygen.com/packages/shader-transitions) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py)

## 3D Cube

<a id="cube-3d"></a>Both shots sit on faces of a cube that turns, carrying A away and B into view.

Built on [Cube](https://github.com/gl-transitions/gl-transitions/blob/master/transitions/Cube.glsl) by gre (gl-transitions), MIT. The write-up and recipes are varg's.

Perspective rotation around a vertical (or horizontal) edge with the two shots as adjacent faces.

- **When:** Slideshows, social carousels, playful product feature runs.
- **Watch out:** Cinematic or emotional content; it reads as a template effect.
- **Timing:** 0.5–1.0 s (CapCut Cube 0.47 s, Cube Rotate 1.0 s), ease-in-out
- **Also called:** Cube, Cube Rotate, Cubic Flip, cube spin, box rotate
- **Card:** https://skills.varg.ai/skills/cube-3d/

### FFmpeg

No cube in xfade. Use editly with gl-transitions (1.x name `cube`):
```js
import editly from 'editly';
await editly({ outPath: 'out.mp4', clips: [
  { layers: [{ type: 'video', path: 'a.mp4' }], transition: { name: 'cube', duration: 0.8 } },
  { layers: [{ type: 'video', path: 'b.mp4' }] },
]});
```

### HyperFrames

Block `transitions-3d` (perspective flip/rotate); or a parent with `perspective: 1200px` and tween `rotationY` -90 → 0 on B while A goes 0 → 90 around a shared edge (`transformOrigin`).

### Remotion

```tsx
import {glTransition} from '@gl-transitions/remotion';
<TransitionSeries.Transition presentation={glTransition({name: 'cube', params: {persp: 0.7, unzoom: 0.3}})} timing={linearTiming({durationInFrames: 24})} />
```
@remotion/transitions has no cube presentation; `swap({})` is a related 3D swap (HTML-in-canvas).

### CapCut

Transitions tab → 3D → Cube, Cube Rotate, Cubic Flip. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions.

### Components

- Cube (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.cube/
- 3D Transitions (hyperframes): `npx hyperframes add transitions-3d` · https://skills.varg.ai/component/hf.transitions-3d/
- Swap (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.swap/

Sources: [@gl-transitions/remotion (README)](https://github.com/gl-transitions/gl-transitions/tree/master/packages/remotion) · [editly](https://github.com/mifi/editly) · [GL Transitions gallery](https://gl-transitions.com) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py) · [CapCut transition names incl. Pro (pyCapCut metadata)](https://github.com/GuanYixuan/pyCapCut/blob/main/pycapcut/metadata/transition_meta.py)

## 3D Flip

<a id="flip-3d"></a>The frame flips over like a card; its back side is the next shot.

Built on [3D Transitions](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/transitions-3d) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A rotates 180° in perspective around the centre axis and B is revealed on the reverse.

- **When:** Before/after, two sides of a story, playful reveals.
- **Watch out:** Long flips; and flipping footage that contains text (it mirrors mid-way).
- **Timing:** 0.4–1.0 s (CapCut Flip 1.0 s, Flip II 0.47 s), ease-in-out
- **Also called:** Flip, Flip II, Cutout Flip, Paper Flip, card flip, Flip & Zoom
- **Card:** https://skills.varg.ai/skills/flip-3d/

### FFmpeg

Approximate with a horizontal squeeze (A narrows to a line, B opens from it):
Same size/fps/pixel format on both inputs (see the Normalize card). offset = duration(A) - T = 5.0 - 0.5 = 4.5.
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]fps=30,settb=AVTB,format=yuv420p[a];[1:v]fps=30,settb=AVTB,format=yuv420p[b];\
[a][b]xfade=transition=squeezeh:duration=0.5:offset=4.5[v];\
[0:a][1:a]acrossfade=d=0.5[au]" \
  -map "[v]" -map "[au]" -c:v libx264 -crf 18 -c:a aac out.mp4
```

### HyperFrames

Block `transitions-3d`; manual: `perspective` on the root, tween `#s1` `rotationY: 0→90` (power2.in, 0.3 s), then `#s2` `rotationY: -90→0` (power2.out, 0.3 s).

### Remotion

```tsx
import {TransitionSeries, linearTiming, springTiming} from '@remotion/transitions';
import {flip} from '@remotion/transitions/flip';

<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={90}><ShotA /></TransitionSeries.Sequence>
  <TransitionSeries.Transition presentation={flip({direction: 'from-left', perspective: 1000})} timing={linearTiming({durationInFrames: 20})} />
  <TransitionSeries.Sequence durationInFrames={90}><ShotB /></TransitionSeries.Sequence>
</TransitionSeries>
```
Total = 90 + 90 - 20 frames: the transition overlaps the two shots.

### CapCut

Transitions tab → 3D → Flip, Flip II, Cutout Flip, Paper Flip, Flip & Zoom. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions.

### Components

- 3D Transitions (hyperframes): `npx hyperframes add transitions-3d` · https://skills.varg.ai/component/hf.transitions-3d/
- GridFlip (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.grid-flip/

Sources: [Remotion: presentations](https://www.remotion.dev/docs/transitions/presentations) · [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py) · [CapCut transition names incl. Pro (pyCapCut metadata)](https://github.com/GuanYixuan/pyCapCut/blob/main/pycapcut/metadata/transition_meta.py)

## Page Turn

<a id="page-turn"></a>Shot A peels or turns like a page and the next shot lies underneath.

Built on [InvertedPageCurl](https://github.com/gl-transitions/gl-transitions/blob/master/transitions/InvertedPageCurl.glsl) by hewlett-packard (gl-transitions), MIT. The write-up and recipes are varg's.

A corner curls up (or the page swings around its spine), casting a light shadow on B.

- **When:** Storytelling, scrapbooks, recipes, children's content, magazine looks.
- **Watch out:** Fast-paced action edits; the metaphor slows things down.
- **Timing:** 0.5–1.0 s (CapCut Page Turning 0.47 s, Fold Over 1.0 s)
- **Also called:** Page Turning, Flip Page, Fold Over, page curl, book flip
- **Card:** https://skills.varg.ai/skills/page-turn/

### FFmpeg

No page curl in xfade; use editly + GL `InvertedPageCurl` or `BookFlip` (names identical in 1.x).

### HyperFrames

`transitions-3d` block, or `rotationY` around `transformOrigin: "left center"` on `#s1` (0 → -180) with `backface-visibility: hidden`.

### Remotion

```tsx
import {TransitionSeries, linearTiming, springTiming} from '@remotion/transitions';
import {bookFlip} from '@remotion/transitions/book-flip';

<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={90}><ShotA /></TransitionSeries.Sequence>
  <TransitionSeries.Transition presentation={bookFlip({direction: 'from-right'})} timing={linearTiming({durationInFrames: 24})} />
  <TransitionSeries.Sequence durationInFrames={90}><ShotB /></TransitionSeries.Sequence>
</TransitionSeries>
```
Total = 90 + 90 - 24 frames: the transition overlaps the two shots.
Shader presentations are built on Remotion's HTML-in-canvas: renders work out of the box (`--gl=angle`, or `--gl=swangle` without a GPU); the Studio preview needs Chrome with `chrome://flags/#canvas-draw-element` enabled. Curl: `glTransition({name: 'InvertedPageCurl'})`.

### CapCut

Transitions tab → 3D / Slide → Page Turning, Flip Page, Fold Over. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions.

### Components

- InvertedPageCurl (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.inverted-page-curl/
- BookFlip (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.book-flip/
- Page Turn (remocn): `npx shadcn@latest add @remocn/page-turn` · https://skills.varg.ai/component/remocn.page-turn/
- Paper Tear (remocn): `npx shadcn@latest add @remocn/paper-tear` · https://skills.varg.ai/component/remocn.paper-tear/
- Torn Paper Rip (hyperframes): `npx hyperframes add torn-paper-rip` · https://skills.varg.ai/component/hf.torn-paper-rip/

Sources: [Remotion: presentations](https://www.remotion.dev/docs/transitions/presentations) · [@gl-transitions/remotion (README)](https://github.com/gl-transitions/gl-transitions/tree/master/packages/remotion) · [GL Transitions gallery](https://gl-transitions.com) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py) · [CapCut transition names incl. Pro (pyCapCut metadata)](https://github.com/GuanYixuan/pyCapCut/blob/main/pycapcut/metadata/transition_meta.py)

## Split and Slices

<a id="split-slices"></a>The frame breaks into bars that slide apart or open like doors, revealing the next shot.

Built on [Doorway](https://github.com/gl-transitions/gl-transitions/blob/master/transitions/Doorway.glsl) by gre (gl-transitions), MIT. The write-up and recipes are varg's.

Two or more panels (horizontal, vertical or diagonal) move away from each other with B behind.

- **When:** Tech, sport and editorial pieces; section openers.
- **Watch out:** Many thin slices on detailed footage turn into visual noise.
- **Timing:** 0.4–0.6 s (CapCut Split/Slices 0.47 s), power3.inOut
- **Also called:** Split, Split III, Split IV, Horizontal Slice, Vertical Slices, Diagonal Slices, Open Horizontally, Open Vertically
- **Card:** https://skills.varg.ai/skills/split-slices/

### FFmpeg

Same size/fps/pixel format on both inputs (see the Normalize card). offset = duration(A) - T = 5.0 - 0.5 = 4.5.
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]fps=30,settb=AVTB,format=yuv420p[a];[1:v]fps=30,settb=AVTB,format=yuv420p[b];\
[a][b]xfade=transition=vertopen:duration=0.5:offset=4.5[v];\
[0:a][1:a]acrossfade=d=0.5[au]" \
  -map "[v]" -map "[au]" -c:v libx264 -crf 18 -c:a aac out.mp4
```
Doors: vertopen/vertclose/horzopen/horzclose. Staggered slices: hlslice, hrslice, vuslice, vdslice.

### HyperFrames

Block `transitions-mechanical` / `transitions-grid`; GL: `Doorway` (splits and swings open).

### Remotion

Custom presentation: render `children` twice, each clipped to half (`clipPath: inset(0 50% 0 0)` / `inset(0 0 0 50%)`), translating ±50% by `presentationProgress` on the exiting side.

### CapCut

Transitions tab → Split → Split, Split III, Split IV, Horizontal Slice, Vertical Slices, Diagonal Slices, Open Horizontally, Open Vertically. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions.

### Components

- Doorway (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.doorway/
- Mechanical Transitions (hyperframes): `npx hyperframes add transitions-mechanical` · https://skills.varg.ai/component/hf.transitions-mechanical/
- Grid Transitions (hyperframes): `npx hyperframes add transitions-grid` · https://skills.varg.ai/component/hf.transitions-grid/
- Mondrian Split (remocn): `npx shadcn@latest add @remocn/mondrian-split` · https://skills.varg.ai/component/remocn.mondrian-split/

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [Remotion: custom presentations](https://www.remotion.dev/docs/transitions/presentations/custom) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py)

## Shutter and Blinds

<a id="shutter-blinds"></a>Stripes close over A like blinds or a shutter, then open on B.

Built on [Venetian Blinds](https://remocn.dev/r/venetian-blinds.json) by Kapish Dima (remocn), MIT. The write-up and recipes are varg's.

Repeated horizontal or vertical bars rotate or slide closed, then reopen on the new image.

- **When:** Mechanical, clinical or retro tech looks; photo slideshows.
- **Watch out:** Too few slats looks crude, too many shimmers; 6–16 bars depending on energy.
- **Timing:** 0.5–0.6 s (CapCut Shutter 0.47 s, Shutter II 0.6 s)
- **Also called:** Shutter, Shutter II, venetian blinds, window blinds, Blinds
- **Card:** https://skills.varg.ai/skills/shutter-blinds/

### FFmpeg

10 horizontal blinds via a custom xfade expression (tested; P runs 1→0):
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]fps=30,settb=AVTB,format=yuv420p[a];[1:v]fps=30,settb=AVTB,format=yuv420p[b];\
 [a][b]xfade=transition=custom:duration=0.6:offset=4.4:expr='if(gt(mod(Y*10/H,1),P),B,A)'[v]" -map "[v]" out.mp4
```

### HyperFrames

Block `transitions-cover` (horizontal and vertical blinds), `transitions-mechanical` (shutter).

### Remotion

`glTransition({name: 'windowblinds'})` (1.x name; `WindowBlinds` in 2.0).

### CapCut

Transitions tab → Basic / Split → Shutter, Shutter II. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions.

### Components

- Venetian Blinds (remocn): `npx shadcn@latest add @remocn/venetian-blinds` · https://skills.varg.ai/component/remocn.venetian-blinds/
- Cover Transitions (hyperframes): `npx hyperframes add transitions-cover` · https://skills.varg.ai/component/hf.transitions-cover/
- Mechanical Transitions (hyperframes): `npx hyperframes add transitions-mechanical` · https://skills.varg.ai/component/hf.transitions-mechanical/

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [@gl-transitions/remotion (README)](https://github.com/gl-transitions/gl-transitions/tree/master/packages/remotion) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py)

## Pixelate

<a id="pixelate-mosaic"></a>A breaks into ever larger pixels, swaps at the coarsest point, and B sharpens back.

Built on [Pixelize](https://github.com/gl-transitions/gl-transitions/blob/master/transitions/Pixelize.glsl) by gre (gl-transitions), MIT. The write-up and recipes are varg's.

Blocky mosaic grows then shrinks; reads as digital or retro gaming.

- **When:** Gaming, retro, tech, censorship gags.
- **Watch out:** Serious brand films; very large blocks on vertical video lose the subject.
- **Timing:** 0.4–0.8 s (CapCut Mosaic 0.47 s)
- **Also called:** Mosaic, pixelize, 8-bit transition, pixel dissolve
- **Card:** https://skills.varg.ai/skills/pixelate-mosaic/

### FFmpeg

Same size/fps/pixel format on both inputs (see the Normalize card). offset = duration(A) - T = 5.0 - 0.6 = 4.4.
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]fps=30,settb=AVTB,format=yuv420p[a];[1:v]fps=30,settb=AVTB,format=yuv420p[b];\
[a][b]xfade=transition=pixelize:duration=0.6:offset=4.4[v];\
[0:a][1:a]acrossfade=d=0.6[au]" \
  -map "[v]" -map "[au]" -c:v libx264 -crf 18 -c:a aac out.mp4
```

### HyperFrames

`npx hyperframes add grid-pixelate-wipe`; dithered: `ordered-dither-pass`.

### Remotion

`glTransition({name: 'pixelize'})` (1.x name; `Pixelize` in 2.0) or `@remotion/effects/pixelate` driven by `interpolate()` on a canvas-based `<Video>`.

### CapCut

Transitions tab → Glitch / Basic → Mosaic, Blocks. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions.

### Components

- Pixelize (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.pixelize/
- Mosaic (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.mosaic/
- Grid Pixelate Wipe (hyperframes): `npx hyperframes add grid-pixelate-wipe` · https://skills.varg.ai/component/hf.grid-pixelate-wipe/
- Ordered Dither Pass (hyperframes): `npx hyperframes add ordered-dither-pass` · https://skills.varg.ai/component/hf.ordered-dither-pass/
- Dither Dissolve (remocn): `npx shadcn@latest add @remocn/dither-dissolve` · https://skills.varg.ai/component/remocn.dither-dissolve/

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [@gl-transitions/remotion (README)](https://github.com/gl-transitions/gl-transitions/tree/master/packages/remotion) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py)

## Clock Wipe

<a id="clock-wipe"></a>A hand sweeps around the centre like a clock, replacing A with B.

Built on [Radial Transitions](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/transitions-radial) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A radial edge rotates 360° from 12 o'clock; Windmill uses several blades.

- **When:** Countdowns, time-based stories, playful retro edits.
- **Watch out:** Modern minimalist brands; it is a strongly retro look.
- **Timing:** 0.5–1.0 s (CapCut Clock wipe 0.47 s)
- **Also called:** Clock wipe, radial wipe, Windmill, angular wipe
- **Card:** https://skills.varg.ai/skills/clock-wipe/

### FFmpeg

Same size/fps/pixel format on both inputs (see the Normalize card). offset = duration(A) - T = 5.0 - 0.8 = 4.2.
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]fps=30,settb=AVTB,format=yuv420p[a];[1:v]fps=30,settb=AVTB,format=yuv420p[b];\
[a][b]xfade=transition=radial:duration=0.8:offset=4.2[v];\
[0:a][1:a]acrossfade=d=0.8[au]" \
  -map "[v]" -map "[au]" -c:v libx264 -crf 18 -c:a aac out.mp4
```

### HyperFrames

Block `transitions-radial`; CSS clock wipe: a 9-point polygon stepped through 4 quadrants (see the HyperFrames mechanical transitions reference).

### Remotion

```tsx
import {TransitionSeries, linearTiming, springTiming} from '@remotion/transitions';
import {clockWipe} from '@remotion/transitions/clock-wipe';

<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={90}><ShotA /></TransitionSeries.Sequence>
  <TransitionSeries.Transition presentation={clockWipe({width: 1920, height: 1080})} timing={linearTiming({durationInFrames: 24})} />
  <TransitionSeries.Sequence durationInFrames={90}><ShotB /></TransitionSeries.Sequence>
</TransitionSeries>
```
Total = 90 + 90 - 24 frames: the transition overlaps the two shots.
`clockWipe()` requires `width` and `height`.

### CapCut

Transitions tab → Basic / Wipe → Clock wipe, Windmill. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions.

### Components

- Radial Transitions (hyperframes): `npx hyperframes add transitions-radial` · https://skills.varg.ai/component/hf.transitions-radial/

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [Remotion: presentations](https://www.remotion.dev/docs/transitions/presentations) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py)

## Swirl Vortex

<a id="swirl-vortex"></a>A twists into a spiral at the centre and unwinds as B.

Built on [Swirl](https://github.com/gl-transitions/gl-transitions/blob/master/transitions/Swirl.glsl) by sergey-kosarevsky (gl-transitions), MIT. The write-up and recipes are varg's.

Pixels spin around the centre with increasing strength, then release onto the new shot.

- **When:** Dream sequences, flashbacks, magic, playful kids' content.
- **Watch out:** Faces at the centre of the swirl.
- **Timing:** 0.5–1.8 s (CapCut Whirlpool 0.47 s, Swirl 1.8 s)
- **Also called:** Whirlpool, Color Swirl, Swirl, Cartoon Swirl, Whirl, vortex
- **Card:** https://skills.varg.ai/skills/swirl-vortex/

### FFmpeg

No swirl in xfade; use editly + GL `Swirl` (same name in 1.x), or render the swirl in Remotion/HyperFrames.

### HyperFrames

Shader `swirl-vortex` from `@hyperframes/shader-transitions` placed at the cut (t = 4 s):
```html
<div id="s1" class="scene" style="background:#0a0a0a"><video src="a.mp4" muted playsinline></video></div>
<div id="s2" class="scene" style="background:#0a0a0a"><video src="b.mp4" muted playsinline></video></div>
<script src="https://cdn.jsdelivr.net/npm/@hyperframes/shader-transitions/dist/index.global.js"></script>
<script>
  const tl = HyperShader.init({ bgColor: "#0a0a0a", scenes: ["s1", "s2"],
    transitions: [{ time: 4, shader: "swirl-vortex", duration: 0.8 }] });
  window.__timelines = window.__timelines || {}; window.__timelines["main"] = tl;
</script>
```
Each `.scene` needs an explicit background-color equal to `bgColor`. Or install the ready block: `npx hyperframes add swirl-vortex`.

### Remotion

`glTransition({name: 'Swirl'})`, or remocn `swirl-dissolve` presentation.

### CapCut

Transitions tab → Distortion → Whirlpool, Color Swirl, Cartoon Swirl, Swirl, Whirl. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions.

### Components

- Swirl (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.swirl/
- Swirl Vortex (hyperframes): `npx hyperframes add swirl-vortex` · https://skills.varg.ai/component/hf.swirl-vortex/
- Swirl Dissolve (remocn): `npx shadcn@latest add @remocn/swirl-dissolve` · https://skills.varg.ai/component/remocn.swirl-dissolve/
- Kaleidoscope (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.kaleidoscope/

Sources: [@gl-transitions/remotion (README)](https://github.com/gl-transitions/gl-transitions/tree/master/packages/remotion) · [HyperFrames: @hyperframes/shader-transitions](https://hyperframes.heygen.com/packages/shader-transitions) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py) · [CapCut transition names incl. Pro (pyCapCut metadata)](https://github.com/GuanYixuan/pyCapCut/blob/main/pycapcut/metadata/transition_meta.py)

## Squeeze and Stretch

<a id="squeeze-stretch"></a>A is squashed or stretched toward an edge or the centre and B springs out the same way.

Built on [Rubber Band Bumper](https://github.com/heygen-com/hyperframes/tree/main/registry/components/rubber-band-bumper) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Rubbery scaling along one axis, like the image being sucked in or pulled like elastic.

- **When:** Playful, cartoonish and meme edits; app UI demos.
- **Watch out:** Live-action people in serious contexts; the distortion is comic.
- **Timing:** 0.4–1.2 s (CapCut Squeeze 0.47 s, Stretch 1.2 s, Inhale 0.6 s)
- **Also called:** Squeeze, Stretch, Stretch Left, Stretch Right, Inhale, Shaky Inhale, elastic transition
- **Card:** https://skills.varg.ai/skills/squeeze-stretch/

### FFmpeg

Same size/fps/pixel format on both inputs (see the Normalize card). offset = duration(A) - T = 5.0 - 0.5 = 4.5.
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]fps=30,settb=AVTB,format=yuv420p[a];[1:v]fps=30,settb=AVTB,format=yuv420p[b];\
[a][b]xfade=transition=squeezev:duration=0.5:offset=4.5[v];\
[0:a][1:a]acrossfade=d=0.5[au]" \
  -map "[v]" -map "[au]" -c:v libx264 -crf 18 -c:a aac out.mp4
```
`squeezeh` squeezes horizontally.

### HyperFrames

Squeeze from the push family: tween `#s1` `scaleX: 1→0` (transformOrigin left) and `#s2` `scaleX: 0→1` (transformOrigin right); elastic: `rubber-band-bumper`.

### Remotion

Custom presentation: exiting `transform: scaleX(${1 - p})` with `transformOrigin: 'left'`; entering `scaleX(${p})` from the right edge, eased with `Easing.bezier`.

### CapCut

Transitions tab → Distortion / Basic → Squeeze, Stretch, Stretch Left, Stretch Right, Inhale. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions.

### Components

- Rubber Band Bumper (hyperframes): `npx hyperframes add rubber-band-bumper` · https://skills.varg.ai/component/hf.rubber-band-bumper/
- Push Transitions (hyperframes): `npx hyperframes add transitions-push` · https://skills.varg.ai/component/hf.transitions-push/

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [Remotion: custom presentations](https://www.remotion.dev/docs/transitions/presentations/custom) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py) · [CapCut transition names incl. Pro (pyCapCut metadata)](https://github.com/GuanYixuan/pyCapCut/blob/main/pycapcut/metadata/transition_meta.py)

## Ripple and Wave

<a id="ripple-wave"></a>Rings or waves distort the frame like water while the shots crossfade.

Built on [WaterDrop](https://github.com/gl-transitions/gl-transitions/blob/master/transitions/WaterDrop.glsl) by pawel-plociennik (gl-transitions), MIT. The write-up and recipes are varg's.

Concentric ripples or sideways waves bend the image; the swap happens inside the distortion.

- **When:** Dream and memory, water and summer themes, calm transitions with motion.
- **Watch out:** Text-heavy shots; strong ripples on faces.
- **Timing:** 0.5–2.0 s (CapCut Wave Right 0.47 s, Wide Ripple 2.0 s)
- **Also called:** Wave Right, Wave Left, Curling Wave, Wide Ripple, Big Wave, water ripple, water drop
- **Card:** https://skills.varg.ai/skills/ripple-wave/

### FFmpeg

No ripple in xfade; editly + GL `WaterDrop` / `ripple` (1.x names), or `xfade=transition=hlwind` for a wind-blown wave.

### HyperFrames

Shader `ripple-waves` from `@hyperframes/shader-transitions` placed at the cut (t = 4 s):
```html
<div id="s1" class="scene" style="background:#0a0a0a"><video src="a.mp4" muted playsinline></video></div>
<div id="s2" class="scene" style="background:#0a0a0a"><video src="b.mp4" muted playsinline></video></div>
<script src="https://cdn.jsdelivr.net/npm/@hyperframes/shader-transitions/dist/index.global.js"></script>
<script>
  const tl = HyperShader.init({ bgColor: "#0a0a0a", scenes: ["s1", "s2"],
    transitions: [{ time: 4, shader: "ripple-waves", duration: 0.8 }] });
  window.__timelines = window.__timelines || {}; window.__timelines["main"] = tl;
</script>
```
Each `.scene` needs an explicit background-color equal to `bgColor`. Or install the ready block: `npx hyperframes add ripple-waves`.

### Remotion

```tsx
import {TransitionSeries, linearTiming, springTiming} from '@remotion/transitions';
import {ripple} from '@remotion/transitions/ripple';

<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={90}><ShotA /></TransitionSeries.Sequence>
  <TransitionSeries.Transition presentation={ripple({amplitude: 100, speed: 50})} timing={linearTiming({durationInFrames: 24})} />
  <TransitionSeries.Sequence durationInFrames={90}><ShotB /></TransitionSeries.Sequence>
</TransitionSeries>
```
Total = 90 + 90 - 24 frames: the transition overlaps the two shots.
Shader presentations are built on Remotion's HTML-in-canvas: renders work out of the box (`--gl=angle`, or `--gl=swangle` without a GPU); the Studio preview needs Chrome with `chrome://flags/#canvas-draw-element` enabled. amplitude 100 and speed 50 are the defaults.

### CapCut

Transitions tab → Distortion → Wave Right, Wave Left, Curling Wave, Wide Ripple, Big Wave. Desktop: drag the tile onto the cut between two clips and set Duration in the right panel ("Apply to all" reuses it on every cut). Mobile: tap the small white square between clips, pick the transition, drag the duration slider, tap ✓. Tab labels and placement change between versions and regions.

### Components

- WaterDrop (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.water-drop/
- Dreamy (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.dreamy/
- Ripple Waves (hyperframes): `npx hyperframes add ripple-waves` · https://skills.varg.ai/component/hf.ripple-waves/
- Ripple Zoom (remocn): `npx shadcn@latest add @remocn/ripple-zoom` · https://skills.varg.ai/component/remocn.ripple-zoom/
- ButterflyWaveScrawler (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.butterfly-wave-scrawler/

Sources: [Remotion: presentations](https://www.remotion.dev/docs/transitions/presentations) · [HyperFrames: @hyperframes/shader-transitions](https://hyperframes.heygen.com/packages/shader-transitions) · [GL Transitions gallery](https://gl-transitions.com) · [CapCut Help: transitions](https://www.capcut.com/help/transitions-in-capcut) · [CapCut: transition categories](https://capcut.com/resource/add-video-transition-online) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py) · [CapCut transition names incl. Pro (pyCapCut metadata)](https://github.com/GuanYixuan/pyCapCut/blob/main/pycapcut/metadata/transition_meta.py)

## Freeze Transition

<a id="freeze-transition"></a>Trend: freeze on a frame with a flash, cut out or zoom the subject, add a label, then cut to the next shot.

Built on [Beat Freeze Cut](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/beat-freeze-cut) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Motion stops with a white flash, the subject pops (outline, cut-out, zoom or paper texture), a beat later the edit moves on.

- **When:** Friend-group intros, sports highlights, outfit reveals, "that's me" memes, on a beat hit.
- **Watch out:** Freezing on motion-blurred frames; using it on every cut.
- **Timing:** Flash 2–3 frames, hold 0.5–1.5 s, then hard cut on the next beat
- **Also called:** freeze frame transition, freeze cutout, freeze + flash, character freeze, photo freeze
- **Card:** https://skills.varg.ai/skills/freeze-transition/

### FFmpeg

Freeze 1 s at 2.0 s with a 2-frame flash and a slow 1.0→1.15 zoom on the held frame:
```bash
ffmpeg -i in.mp4 -filter_complex \
"[0:v]split[v1][v2];[v1]trim=0:2,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=1[f];\
 [v2]trim=2,setpts=PTS-STARTPTS[r];[f][r]concat=n=2:v=1:a=0,\
scale=w='trunc(1280*(1+if(between(t,2,3),(t-2)*0.15,0))/2)*2':h=-2:eval=frame,crop=1280:720,\
eq=brightness=0.7:enable='between(t,2,2.066)'[v]" -map "[v]" out.mp4
```
Subject cut-out needs a matte (background removal) composited over the frozen frame.

### HyperFrames

`npx hyperframes add beat-freeze-cut` (speed ramp, freeze hit and hard cut) plus `freeze-frame-dressing` (paper, tape and flash dressing for a frozen or background-removed subject).

### Remotion

`<Sequence freeze={60}>` around the shot for the hold, a white `<AbsoluteFill>` flash for 2 frames, `scale` interpolated on the frozen layer; cut-out via an alpha video/PNG above it.

### CapCut

Freeze (toolbar) → on the frozen clip add Effects (Flash, Shake) and Remove background / Cutout on a duplicated layer; add a text label; cut on the next beat.

### Components

- Beat Freeze Cut (hyperframes): `npx hyperframes add beat-freeze-cut` · https://skills.varg.ai/component/hf.beat-freeze-cut/
- Freeze-Frame Dressing (hyperframes): `npx hyperframes add freeze-frame-dressing` · https://skills.varg.ai/component/hf.freeze-frame-dressing/
- Editorial Flash Overlay (hyperframes): `npx hyperframes add editorial-flash-overlay` · https://skills.varg.ai/component/hf.editorial-flash-overlay/

Sources: [FFmpeg filters: tpad](https://ffmpeg.org/ffmpeg-filters.html#tpad) · [Remotion: <Sequence>](https://www.remotion.dev/docs/sequence) · [CapCut: freeze frame (resource article)](https://www.capcut.com/resource/davinci-resolve-freeze-frame)

## Velocity Edit

<a id="velocity-edit"></a>Trend: speed curves on every clip (fast-slow-fast) synced to the beat, often with shake and flash on hits.

Built on [Beat Freeze Cut](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/beat-freeze-cut) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Each clip rushes in, drops into slow motion on the beat and rushes out; transitions are hidden in the fast parts.

- **When:** Dance, car, sport, gaming and fan edits on TikTok/Reels.
- **Watch out:** Footage below 60 fps for the slow parts; curves that ignore the beat.
- **Timing:** Fast parts 2–5×, slow parts 0.2–0.5×, slow point exactly on the beat
- **Also called:** velocity, velocity transition, speed curve edit, Montage curve, Hero curve, Bullet curve
- **Card:** https://skills.varg.ai/skills/velocity-edit/

### FFmpeg

Per clip: 3× in, 0.4× on the beat, 3× out, then concat clips (pitch kept by atempo; often the music replaces clip audio):
```bash
ffmpeg -i clip.mp4 -filter_complex \
"[0:v]split=3[s1][s2][s3];\
 [s1]trim=0:1.2,setpts=(PTS-STARTPTS)/3[v1];\
 [s2]trim=1.2:1.6,setpts=(PTS-STARTPTS)/0.4,minterpolate=fps=60[v2];\
 [s3]trim=1.6:3,setpts=(PTS-STARTPTS)/3[v3];\
 [v1][v2][v3]concat=n=3:v=1:a=0,fps=30[v]" -map "[v]" -an part.mp4
```

### HyperFrames

`rate` lane in `data-automation` with points like `{t:0,v:3},{t:0.4,v:0.4},{t:0.8,v:3}`; Studio speed presets include Montage, Hero, Bullet, Jump cut, Flash in, Flash out.

### Remotion

Per-frame speed function → accumulated `trimBefore` (Remotion speed-ramp snippet), with the slow point at the beat frame; add shake/flash overlays on the beat.

### CapCut

Speed → Curve → Montage / Hero / Bullet / Jump Cut / Flash In / Flash Out (or Custom), align the slow point to Beats markers, then add Shake/Flash effects on hits.

### Components

- Beat Freeze Cut (hyperframes): `npx hyperframes add beat-freeze-cut` · https://skills.varg.ai/component/hf.beat-freeze-cut/
- Beat Accent (hyperframes): `npx hyperframes add beat-accent` · https://skills.varg.ai/component/hf.beat-accent/
- Camera Shake (hyperframes): `npx hyperframes add camera-shake` · https://skills.varg.ai/component/hf.camera-shake/
- Motion Blur (hyperframes): `npx hyperframes add motion-blur` · https://skills.varg.ai/component/hf.motion-blur/

Sources: [FFmpeg filters: setpts](https://ffmpeg.org/ffmpeg-filters.html#setpts) · [Remotion: speed ramp snippet](https://www.remotion.dev/docs/miscellaneous/snippets/accelerated-video) · [HyperFrames: speed ramps](https://hyperframes.heygen.com/reference/speed-ramps) · [CapCut: speed curve tool](https://www.capcut.com/tools/speed-ramp)

## FFmpeg xfade Chain for N Clips

<a id="ffmpeg-xfade-chain"></a>Chain xfade + acrossfade across N clips; offset of the k-th transition = d1+…+dk − k·T.

Every join gets the same transition; total length = sum of clip durations − (N−1)·T.

- **When:** Batch slideshows, AI-shot sequences and reels where an agent must join many clips with transitions in one render.
- **Watch out:** Offsets computed from the source clips instead of the running output; and clips shorter than T.
- **Timing:** T usually 0.3–1.0 s; same T for every join keeps the math simple
- **Also called:** xfade offset math, chained xfade, acrossfade chain, slideshow transitions
- **Card:** https://skills.varg.ai/skills/ffmpeg-xfade-chain/

### FFmpeg

Each xfade's offset is measured on its first input, which is the output of the previous xfade (already shortened by (k−1)·T). So offset_k = (d1 + … + dk) − k·T. `acrossfade` overlaps audio by the same T, keeping it in sync.
```bash
#!/usr/bin/env bash
# xfade-chain.sh <transition> <T> out.mp4 clip1 clip2 [clip3 ...]   (tested with ffmpeg 8.1)
set -euo pipefail
TR=$1; T=$2; OUT=$3; shift 3
W=1080; H=1920; FPS=30; n=$#; i=0; off=0; f=""; inputs=()
for c in "$@"; do
  inputs+=(-i "$c")
  f+="[$i:v]fps=$FPS,scale=$W:$H:force_original_aspect_ratio=decrease,pad=$W:$H:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p,settb=AVTB,setpts=PTS-STARTPTS[v$i];"
  f+="[$i:a]aresample=48000,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS[a$i];"
  i=$((i+1))
done
vp=v0; ap=a0; i=1
for c in "${@:1:$((n-1))}"; do
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$c")
  off=$(echo "$off + $d - $T" | bc -l)            # offset_k = d1+..+dk - k*T
  f+="[$vp][v$i]xfade=transition=$TR:duration=$T:offset=$off[vx$i];"
  f+="[$ap][a$i]acrossfade=d=$T[ax$i];"
  vp=vx$i; ap=ax$i; i=$((i+1))
done
ffmpeg -y "${inputs[@]}" -filter_complex "${f%;}" -map "[$vp]" -map "[$ap]" \
  -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -movflags +faststart "$OUT"
```
Tested: 5 s + 4 s + 6 s with T = 0.5 → 14.0 s output.

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [FFmpeg filters: acrossfade](https://ffmpeg.org/ffmpeg-filters.html#acrossfade) · [FFmpeg filters: settb](https://ffmpeg.org/ffmpeg-filters.html#settb_002c-asettb)

## FFmpeg xfade Transition Reference

<a id="ffmpeg-xfade-reference"></a>All 58 built-in xfade transitions plus custom expressions, grouped by look, with the options that matter.

Fades, wipes, slides, covers/reveals, shape opens, slices, wind, squeeze, zoom, pixelize, blur.

- **When:** Pick a transition name for any ffmpeg join; check here before writing a custom expression.
- **Watch out:** Expecting camera-style effects (whip, spin, shake, glitch, light leak, 3D) from xfade; those need filter chains or GL/HTML engines.
- **Timing:** duration 0–60 s (default 1); offset in seconds from the first input's start (default 0)
- **Also called:** xfade list, xfade transitions, xfade names, xfade custom expr
- **Card:** https://skills.varg.ai/skills/ffmpeg-xfade-reference/

### FFmpeg

Options: `transition`, `duration`, `offset`, `expr`. Both inputs must be constant frame rate with the same resolution, pixel format, frame rate and timebase.

Fades: fade, fadefast, fadeslow, fadeblack, fadewhite, fadegrays, dissolve (dithered), distance.
Wipes: wipeleft/right/up/down, wipetl/tr/bl/br, diagtl/tr/bl/br, smoothleft/right/up/down (soft edge).
Moves: slideleft/right/up/down (push), coverleft/right/up/down (B over A), revealleft/right/up/down (A off B).
Shapes: circleopen, circleclose, circlecrop, rectcrop, vertopen, vertclose, horzopen, horzclose, radial (clock).
Slices and wind: hlslice, hrslice, vuslice, vdslice, hlwind, hrwind, vuwind, vdwind.
Other: squeezeh, squeezev, zoomin, pixelize, hblur, custom.

Custom: variables X, Y, W, H, P, PLANE, A, B and a0..a3(x,y), b0..b3(x,y). P runs from 1 at the start of the transition to 0 at the end (verified), so `if(gt(X/W,P),B,A)` reveals B from the right:
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
"[0:v]fps=30,settb=AVTB,format=yuv420p[a];[1:v]fps=30,settb=AVTB,format=yuv420p[b];\
 [a][b]xfade=transition=custom:duration=0.6:offset=4.4:expr='if(gt(mod(Y*10/H,1),P),B,A)'[v]" -map "[v]" blinds.mp4
```
GPU variants exist (`xfade_opencl`, `xfade_vulkan`) with a smaller set.

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade)

## Normalize Clips Before xfade

<a id="ffmpeg-normalize-before-xfade"></a>The #1 xfade failure: inputs differ in size, fps or timebase. Normalize every input first.

No visual change; it makes the filter graph valid.

- **When:** Every time clips come from different sources (phone + screen recording + AI video).
- **Watch out:** Fixing only fps: `fps=30` alone still leaves a different timebase (1/30 vs 1/15360) and xfade still fails.
- **Timing:** Applies before any transition
- **Also called:** timebase mismatch, xfade error, do not match, settb AVTB, fps normalize
- **Card:** https://skills.varg.ai/skills/ffmpeg-normalize-before-xfade/

### FFmpeg

Errors you will see (reproduced with ffmpeg 8.1):
- `First input link main parameters (size 1280x720) do not match the corresponding second input link xfade parameters (size 1920x1080)`
- `First input link main timebase (1/15360) do not match the corresponding second input link xfade timebase (1/12800)`

Normalize each input (video and audio):
```bash
[i:v]fps=30,scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,\
setsar=1,format=yuv420p,settb=AVTB,setpts=PTS-STARTPTS[vi];
[i:a]aresample=48000,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS[ai];
```
Also: variable-frame-rate phone video needs `fps=` first; still images need `-loop 1 -t <dur>` (or `loop`) to become video; clips without audio need `anullsrc` for acrossfade.

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [FFmpeg filters: settb](https://ffmpeg.org/ffmpeg-filters.html#settb_002c-asettb)

## GL Transitions via editly or FFmpeg

<a id="gl-transitions-ffmpeg-editly"></a>Run any of the ~125 GLSL gl-transitions between clips: editly (no custom build) or a patched FFmpeg.

Built on [Cube](https://github.com/gl-transitions/gl-transitions/blob/master/transitions/Cube.glsl) by gre (gl-transitions), MIT. The write-up and recipes are varg's.

Cube, page curl, doorway, morph, burn, glitch and other shader transitions xfade cannot do.

- **When:** Server-side batch renders that need 3D or organic transitions without a browser.
- **Watch out:** Mixing name sets: editly depends on gl-transitions 1.x (`crosswarp`, `cube`), the 2.0 catalog uses PascalCase (`CrossWarp`, `Cube`).
- **Timing:** 0.5–1.0 s typical
- **Also called:** gltransition filter, ffmpeg-gl-transition, editly, ffmpeg-concat, GLSL transitions
- **Card:** https://skills.varg.ai/skills/gl-transitions-ffmpeg-editly/

### FFmpeg

FFmpeg itself has no GL transitions. Option 1, editly (Node, standard ffmpeg):
```js
import editly from 'editly';
await editly({
  outPath: 'out.mp4',
  defaults: { transition: { name: 'crosswarp', duration: 0.5 } },
  clips: [
    { layers: [{ type: 'video', path: 'a.mp4' }] },
    { transition: { name: 'cube', duration: 1, params: { persp: 0.5 } }, layers: [{ type: 'video', path: 'b.mp4' }] },
    { layers: [{ type: 'video', path: 'c.mp4' }] },
  ],
});
```
`transition` on a clip applies between it and the next; also `random`, `dummy`, `directional-left|right|up|down`.
Option 2, the third-party `gltransition` filter (rebuild FFmpeg with the patch, needs an OpenGL/EGL context):
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex "gltransition=duration=1:offset=2:source=CrossWarp.glsl" out.mp4
```
The filter sets only `progress` and `ratio`; bake parameter uniforms into constants, and transitions that need extra textures do not work.

### Components

- Cube (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.cube/
- CrossZoom (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.cross-zoom/
- DirectionalWarp (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.directional-warp/
- Doorway (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.doorway/
- InvertedPageCurl (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.inverted-page-curl/
- FilmBurn (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.film-burn/

Sources: [editly](https://github.com/mifi/editly) · [ffmpeg-gl-transition (third-party filter)](https://github.com/transitive-bullshit/ffmpeg-gl-transition) · [GL Transitions gallery](https://gl-transitions.com) · [gl-transitions 2.0 changelog (renames)](https://github.com/gl-transitions/gl-transitions/blob/master/packages/gl-transitions/CHANGELOG.md)

## MoviePy Crossfade and Slide

<a id="moviepy-crossfade"></a>In MoviePy v2, crossfade with vfx.CrossFadeIn plus negative padding (or with_start in a CompositeVideoClip).

Crossfades and simple slide-ins from Python.

- **When:** Python pipelines that already use MoviePy; quick prototypes.
- **Watch out:** v1 syntax (`crossfadein`, `set_start`, `subclip`) on MoviePy 2.x; and slow renders of long timelines.
- **Timing:** Any; T = 0.5 s in the example
- **Also called:** moviepy, CrossFadeIn, concatenate_videoclips padding, CompositeVideoClip
- **Card:** https://skills.varg.ai/skills/moviepy-crossfade/

### MoviePy

Tested with MoviePy 2.2.1 (5 s + 4 s, T = 0.5 → 8.5 s):
```python
from moviepy import VideoFileClip, CompositeVideoClip, concatenate_videoclips, vfx, afx
T = 0.5
a = VideoFileClip('a.mp4').subclipped(0, 5).with_effects([afx.AudioFadeOut(T)])
b = VideoFileClip('b.mp4').subclipped(0, 4).with_effects([vfx.CrossFadeIn(T), afx.AudioFadeIn(T)])
out = concatenate_videoclips([a, b], method='compose', padding=-T)
# same thing explicitly:
# out = CompositeVideoClip([a, b.with_start(a.duration - T)])
out.write_videofile('out.mp4', fps=30)
```
`CrossFadeIn` only works inside a composite (it fades the clip's mask). Other effects: `vfx.SlideIn(duration, side)`, `vfx.SlideOut`, `vfx.FadeIn/FadeOut` (through black), `vfx.Freeze`, `vfx.MultiplySpeed`.

Sources: [MoviePy v2 video effects (CrossFadeIn, SlideIn)](https://github.com/Zulko/moviepy/tree/master/moviepy/video/fx)

## Remotion TransitionSeries

<a id="remotion-transitionseries"></a>Sequence scenes with <TransitionSeries>; each transition overlaps its neighbours, so the video gets shorter.

Any built-in or custom presentation between React scenes.

- **When:** Remotion projects; data-driven videos where scenes are components.
- **Watch out:** Forgetting that 40 + 60 frames with a 30-frame transition is 70 frames, not 100; and placing two transitions next to each other.
- **Timing:** linearTiming({durationInFrames}) or springTiming({config:{damping:200}}) (~23 frames at 30 fps)
- **Also called:** @remotion/transitions, TransitionSeries, linearTiming, springTiming, presentations
- **Card:** https://skills.varg.ai/skills/remotion-transitionseries/

### Remotion

```tsx
import {TransitionSeries, linearTiming, springTiming} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';
import {slide} from '@remotion/transitions/slide';

export const Edit = () => (
  <TransitionSeries>
    <TransitionSeries.Sequence durationInFrames={40}><A /></TransitionSeries.Sequence>
    <TransitionSeries.Transition presentation={fade()} timing={linearTiming({durationInFrames: 30})} />
    <TransitionSeries.Sequence durationInFrames={60}><B /></TransitionSeries.Sequence>
    <TransitionSeries.Transition presentation={slide({direction: 'from-right'})} timing={springTiming({config: {damping: 200}})} />
    <TransitionSeries.Sequence durationInFrames={90}><C /></TransitionSeries.Sequence>
  </TransitionSeries>
);
// total = 40 + 60 + 90 - 30 - 23 = 137 frames; compute with timing.getDurationInFrames({fps})
```
Rules: a transition may not be longer than either neighbour; no two transitions (or overlays) adjacent; a transition can be first/last to animate an entrance/exit; default presentation is `slide()`.

Built-ins in @remotion/transitions 4.0.539: CSS (work everywhere) `fade`, `slide`, `wipe`, `flip`, `clockWipe`, `iris`, `none`, `pushCut`; shader/HTML-in-canvas `blurSlide`, `bookFlip`, `crossZoom`, `crosswarp`, `dissolve`, `dreamyZoom`, `filmBurn`, `linearBlur`, `ripple`, `swap`, `zoomBlur`, `zoomInOut`. Each imports from `@remotion/transitions/<kebab-name>`. Shader presentations are built on Remotion's HTML-in-canvas: renders work out of the box (`--gl=angle`, or `--gl=swangle` without a GPU); the Studio preview needs Chrome with `chrome://flags/#canvas-draw-element` enabled.
There is no `cube` presentation; use `@gl-transitions/remotion`.

Sources: [Remotion: <TransitionSeries>](https://www.remotion.dev/docs/transitions/transitionseries) · [Remotion: presentations](https://www.remotion.dev/docs/transitions/presentations) · [Remotion: timings](https://www.remotion.dev/docs/transitions/timings) · [Remotion: crossZoom (HTML-in-canvas)](https://www.remotion.dev/docs/transitions/presentations/cross-zoom)

## Remotion Custom Presentation

<a id="remotion-custom-presentation"></a>Write your own transition as a component that receives progress (0→1) and whether it is entering or exiting.

Anything CSS can do (scale, rotate, clip-path, blur), or a WebGL shader via HTML-in-canvas.

- **When:** Pull-out zooms, spins, splits, brand-specific moves missing from the built-ins.
- **Watch out:** Non-absolute layouts inside scenes; both scenes are stacked during the overlap and must stay absolutely positioned.
- **Timing:** Whatever timing you pass to the Transition
- **Also called:** TransitionPresentation, presentationProgress, makeHtmlInCanvasPresentation, custom transition
- **Card:** https://skills.varg.ai/skills/remotion-custom-presentation/

### Remotion

```tsx
import type {TransitionPresentation, TransitionPresentationComponentProps} from '@remotion/transitions';
import {AbsoluteFill} from 'remotion';

type P = {maxScale: number};
const PullOut: React.FC<TransitionPresentationComponentProps<P>> = ({children, presentationDirection, presentationProgress: p, passedProps}) => {
  const s = presentationDirection === 'exiting'
    ? 1 - (1 - 1 / passedProps.maxScale) * p          // A shrinks
    : passedProps.maxScale - (passedProps.maxScale - 1) * p; // B settles from big
  return <AbsoluteFill style={{transform: `scale(${s})`, opacity: presentationDirection === 'entering' ? p : 1}}>{children}</AbsoluteFill>;
};
export const pullOut = (props: P): TransitionPresentation<P> => ({component: PullOut, props});
// <TransitionSeries.Transition presentation={pullOut({maxScale: 1.4})} timing={linearTiming({durationInFrames: 12})} />
```
For a GPU shader, `makeHtmlInCanvasPresentation(shader)` (exported from @remotion/transitions) wraps a function that receives `prevImage`, `nextImage`, `width`, `height`, `time` and `passedProps` on an OffscreenCanvas.

Sources: [Remotion: custom presentations](https://www.remotion.dev/docs/transitions/presentations/custom) · [Remotion: presentations](https://www.remotion.dev/docs/transitions/presentations)

## GL Transitions in Remotion

<a id="remotion-gl-transitions"></a>glTransition({name}) turns any gl-transitions shader into a TransitionSeries presentation.

Built on [Cube](https://github.com/gl-transitions/gl-transitions/blob/master/transitions/Cube.glsl) by gre (gl-transitions), MIT. The write-up and recipes are varg's.

Cube, page curl, doorway, morph, burn, kaleidoscope… between any React scenes.

- **When:** Remotion projects needing transitions beyond @remotion/transitions.
- **Watch out:** Mixing name sets: npm 0.1.0 peer-depends on gl-transitions ^1.76.1 (1.x names: `cube`, `crosswarp`, `burn0`); adapter 1.0.0 moves to 2.0 names (`Cube`, `CrossWarp`, `BurnThrough`).
- **Timing:** linearTiming({durationInFrames: 24–30})
- **Also called:** @gl-transitions/remotion, glTransition(), gl-transitions presentation
- **Card:** https://skills.varg.ai/skills/remotion-gl-transitions/

### Remotion

Remotion ≥ 4.0.500:
```bash
npm install gl-transitions @gl-transitions/remotion @remotion/transitions
```
```tsx
import {linearTiming, TransitionSeries} from '@remotion/transitions';
import {glTransition} from '@gl-transitions/remotion';

<TransitionSeries.Transition
  presentation={glTransition({name: 'cube', params: {persp: 0.7, unzoom: 0.3}})}
  timing={linearTiming({durationInFrames: 30})} />
// textures: glTransition({name: 'luma', textures: {luma: staticFile('spiral.png')}})
```
Renders work out of the box (`--gl=angle`, or `--gl=swangle` without a GPU); the Studio needs Chrome 149+ with `chrome://flags/#canvas-draw-element`. Transparent pixels show a captured scene or black, not layers under the series.

### Components

- Cube (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.cube/
- CrossZoom (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.cross-zoom/
- DreamyZoom (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.dreamy-zoom/
- DirectionalWarp (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.directional-warp/
- Doorway (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.doorway/
- InvertedPageCurl (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.inverted-page-curl/
- BookFlip (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.book-flip/
- Swirl (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.swirl/
- Morph (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.morph/
- FilmBurn (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.film-burn/
- Kaleidoscope (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.kaleidoscope/
- WaterDrop (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.water-drop/

Sources: [@gl-transitions/remotion (README)](https://github.com/gl-transitions/gl-transitions/tree/master/packages/remotion) · [gl-transitions 2.0 changelog (renames)](https://github.com/gl-transitions/gl-transitions/blob/master/packages/gl-transitions/CHANGELOG.md) · [GL Transitions gallery](https://gl-transitions.com)

## HyperFrames Shader Transition

<a id="hyperframes-shader-transition"></a>Place a WebGL shader between two HyperFrames scenes with HyperShader.init({scenes, transitions}).

Built on [Domain Warp Dissolve](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/domain-warp-dissolve) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

14 shaders: domain-warp, ridged-burn, whip-pan, sdf-iris, ripple-waves, gravitational-lens, cinematic-zoom, chromatic-split, glitch, swirl-vortex, thermal-distortion, flash-through-white, cross-warp-morph, light-leak.

- **When:** HyperFrames compositions that need per-pixel transitions; mix freely with CSS transitions.
- **Watch out:** CSS that html2canvas cannot capture: `transparent` in gradients, `var()` on captured elements, missing scene background-color.
- **Timing:** Calm 0.5–0.8 s, medium 0.3–0.5 s, high energy 0.15–0.3 s
- **Also called:** @hyperframes/shader-transitions, HyperShader.init, WebGL scene transition
- **Card:** https://skills.varg.ai/skills/hyperframes-shader-transition/

### HyperFrames

```html
<div id="root" data-composition-id="main" data-start="0" data-duration="12" data-width="1920" data-height="1080">
  <div id="s1" class="scene" style="background:#0a0a0a">…</div>
  <div id="s2" class="scene" style="background:#0a0a0a">…</div>
  <div id="s3" class="scene" style="background:#0a0a0a">…</div>
</div>
<script src="https://cdn.jsdelivr.net/npm/@hyperframes/shader-transitions/dist/index.global.js"></script>
<script>
  const tl = HyperShader.init({
    bgColor: "#0a0a0a", accentColor: "#ff6b2b",
    scenes: ["s1", "s2", "s3"],
    transitions: [
      { time: 4, shader: "whip-pan", duration: 0.4 },
      { time: 8, duration: 0.6 }          // no shader -> CSS crossfade
    ],
  });
  window.__timelines = window.__timelines || {}; window.__timelines["main"] = tl;
</script>
```
Let `init()` create the timeline and add your beat tweens to the returned `tl`. Without WebGL it falls back to normal playback. Ready blocks: `npx hyperframes add <slug>` (e.g. whip-pan, sdf-iris, domain-warp-dissolve).

### Components

- Domain Warp Dissolve (hyperframes): `npx hyperframes add domain-warp-dissolve` · https://skills.varg.ai/component/hf.domain-warp-dissolve/
- Ridged Burn (hyperframes): `npx hyperframes add ridged-burn` · https://skills.varg.ai/component/hf.ridged-burn/
- Whip Pan (hyperframes): `npx hyperframes add whip-pan` · https://skills.varg.ai/component/hf.whip-pan/
- SDF Iris (hyperframes): `npx hyperframes add sdf-iris` · https://skills.varg.ai/component/hf.sdf-iris/
- Ripple Waves (hyperframes): `npx hyperframes add ripple-waves` · https://skills.varg.ai/component/hf.ripple-waves/
- Gravitational Lens (hyperframes): `npx hyperframes add gravitational-lens` · https://skills.varg.ai/component/hf.gravitational-lens/
- Cinematic Zoom (hyperframes): `npx hyperframes add cinematic-zoom` · https://skills.varg.ai/component/hf.cinematic-zoom/
- Chromatic Radial Split (hyperframes): `npx hyperframes add chromatic-radial-split` · https://skills.varg.ai/component/hf.chromatic-radial-split/
- Glitch (hyperframes): `npx hyperframes add glitch` · https://skills.varg.ai/component/hf.glitch/
- Swirl Vortex (hyperframes): `npx hyperframes add swirl-vortex` · https://skills.varg.ai/component/hf.swirl-vortex/
- Thermal Distortion (hyperframes): `npx hyperframes add thermal-distortion` · https://skills.varg.ai/component/hf.thermal-distortion/
- Flash Through White (hyperframes): `npx hyperframes add flash-through-white` · https://skills.varg.ai/component/hf.flash-through-white/
- Cross Warp Morph (hyperframes): `npx hyperframes add cross-warp-morph` · https://skills.varg.ai/component/hf.cross-warp-morph/
- Light Leak (hyperframes): `npx hyperframes add light-leak` · https://skills.varg.ai/component/hf.light-leak/

Sources: [HyperFrames: @hyperframes/shader-transitions](https://hyperframes.heygen.com/packages/shader-transitions) · [HyperFrames: compositions](https://hyperframes.heygen.com/concepts/compositions)

## HyperFrames Scene Transition (CSS)

<a id="hyperframes-scene-transition"></a>Overlap two clips or sub-compositions on separate tracks and tween both wrappers at the same time T.

Built on [Fade Through](https://github.com/heygen-com/hyperframes/tree/main/registry/components/fade-through) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Crossfade, push, zoom-through, blur, iris or any CSS move between scenes or videos.

- **When:** Every multi-scene HyperFrames video; video clips need opacity plus matching volume envelopes.
- **Watch out:** Fading the outgoing scene out first and then animating the next one in: that is a dip, not a transition. Also don't animate the timed clip element itself.
- **Timing:** Presets: snappy 0.2 s power4.inOut, smooth 0.4 s power2.inOut, gentle 0.6 s sine.inOut
- **Also called:** clip overlap, sub-composition transition, GSAP transition, crossfade clips
- **Card:** https://skills.varg.ai/skills/hyperframes-scene-transition/

### HyperFrames

Video crossfade (0.5 s overlap, sound follows each clip):
```html
<div id="a-visual" class="inner"><video id="a" src="a.mp4" data-start="0" data-duration="3" data-track-index="0" data-has-audio="true"
  data-automation='{"version":1,"lanes":[{"target":"volume","points":[{"t":0,"v":1},{"t":2.5,"v":1},{"t":3,"v":0}]}]}'></video></div>
<div id="b-visual" class="inner"><video id="b" src="b.mp4" data-start="a - 0.5" data-duration="3" data-track-index="1" data-has-audio="true"
  data-automation='{"version":1,"lanes":[{"target":"volume","points":[{"t":0,"v":0},{"t":0.5,"v":1},{"t":3,"v":1}]}]}'></video></div>
<script>
  const tl = gsap.timeline({ paused: true });
  tl.set("#b-visual", { opacity: 0 }, 0)
    .to("#a-visual", { opacity: 0, duration: 0.5 }, 2.5)
    .to("#b-visual", { opacity: 1, duration: 0.5 }, 2.5);
  window.__timelines["main"] = tl;
</script>
```
For sub-compositions (`data-composition-src`), extend the outgoing host's `data-duration` by the overlap, pull the incoming host's `data-start` earlier by the same amount, put them on alternating tracks, and tween the host wrappers at T (e.g. push: `x: -1920` / `x: 1920 → 0`, power3.inOut). Tracks are editor rows; paint order is CSS z-index.

### Components

- Fade Through (hyperframes): `npx hyperframes add fade-through` · https://skills.varg.ai/component/hf.fade-through/
- Directional Wipe (hyperframes): `npx hyperframes add directional-wipe` · https://skills.varg.ai/component/hf.directional-wipe/
- Zoom Through Transition (hyperframes): `npx hyperframes add zoom-through-transition` · https://skills.varg.ai/component/hf.zoom-through-transition/
- Push Transitions (hyperframes): `npx hyperframes add transitions-push` · https://skills.varg.ai/component/hf.transitions-push/
- Blur Transitions (hyperframes): `npx hyperframes add transitions-blur` · https://skills.varg.ai/component/hf.transitions-blur/
- Dissolve Transitions (hyperframes): `npx hyperframes add transitions-dissolve` · https://skills.varg.ai/component/hf.transitions-dissolve/

Sources: [HyperFrames: data attributes](https://hyperframes.heygen.com/concepts/data-attributes) · [HyperFrames: compositions](https://hyperframes.heygen.com/concepts/compositions) · [HyperFrames: HTML schema](https://hyperframes.heygen.com/reference/html-schema)

## HyperFrames Whip with Motion Blur

<a id="hyperframes-whip-motion-blur"></a>Fly scene A out and scene B in at matched velocity with directional blur peaking at the swap.

Built on [Whip Pan Cut](https://github.com/heygen-com/hyperframes/tree/main/registry/components/whip-pan-cut) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A camera-like whip: both scenes travel the same way, blur peaks mid-move, B lands sharp.

- **When:** Energetic HyperFrames edits; DOM content (UI, type, product shots) where a shader capture is unnecessary.
- **Watch out:** Different directions or eases for the two halves; blur that lingers after B lands.
- **Timing:** 0.3–0.45 s total; power4.in out of A, power4.out into B
- **Also called:** whip-pan-cut, GSAP whip, motion blur whip, velocity-matched whip
- **Card:** https://skills.varg.ai/skills/hyperframes-whip-motion-blur/

### HyperFrames

Ready primitive: `npx hyperframes add whip-pan-cut` (capped directional motion blur, same-direction entry at matched velocity, speed-ramped). Hand-written:
```js
const T = 4, D = 0.18;
tl.to("#s1", { x: -1920, filter: "blur(24px)", duration: D, ease: "power4.in" }, T);
tl.fromTo("#s2", { x: 1920, filter: "blur(24px)" }, { x: 0, filter: "blur(0px)", duration: D * 1.4, ease: "power4.out" }, T + D);
```
CSS `blur()` is isotropic; for true directional blur use the `motion-blur` filter component (shutter-angle integration) or the `whip-pan` shader.

### Components

- Whip Pan Cut (hyperframes): `npx hyperframes add whip-pan-cut` · https://skills.varg.ai/component/hf.whip-pan-cut/
- Motion Blur (hyperframes): `npx hyperframes add motion-blur` · https://skills.varg.ai/component/hf.motion-blur/
- Whip Pan (hyperframes): `npx hyperframes add whip-pan` · https://skills.varg.ai/component/hf.whip-pan/
- Cut the Curve (hyperframes): `npx hyperframes add cut-the-curve` · https://skills.varg.ai/component/hf.cut-the-curve/

Sources: [HyperFrames: @hyperframes/shader-transitions](https://hyperframes.heygen.com/packages/shader-transitions) · [HyperFrames: motion prompting (transitions)](https://hyperframes.heygen.com/prompting/motion)

## OTIO and XML Handoff to NLEs

<a id="otio-fcpxml-handoff"></a>Write the edit (clips, cuts, dissolves) as OpenTimelineIO and convert to XML so an editor can finish it in an NLE.

An editable timeline in Resolve, Premiere or Final Cut with real cuts and dissolves instead of a flat render.

- **When:** When a human editor will refine the agent's rough cut; agency and post-production handoffs.
- **Watch out:** Assuming effects survive: only basic cuts and dissolves translate; designed transitions (whip, glitch, shader) do not.
- **Timing:** Dissolves: in_offset/out_offset need handles in the source on both sides
- **Also called:** OpenTimelineIO, FCPXML, FCP7 XML, Premiere handoff, Resolve import, EDL
- **Card:** https://skills.varg.ai/skills/otio-fcpxml-handoff/

### Python

Python with opentimelineio 0.18 (tested). Transitions sit between clips and do not change the track length; offsets need media beyond the cut:
```python
import opentimelineio as otio
RATE = 30
rt = lambda s: otio.opentime.RationalTime(round(s * RATE), RATE)
def clip(path, src_in, dur, media_dur):
    return otio.schema.Clip(name=path,
        media_reference=otio.schema.ExternalReference(target_url=path,
            available_range=otio.opentime.TimeRange(rt(0), rt(media_dur))),
        source_range=otio.opentime.TimeRange(rt(src_in), rt(dur)))
tl = otio.schema.Timeline(name='edit')
v = otio.schema.Track(name='V1', kind=otio.schema.TrackKind.Video); tl.tracks.append(v)
v.append(clip('a.mp4', 0, 5, 10))
v.append(otio.schema.Transition(transition_type=otio.schema.TransitionTypes.SMPTE_Dissolve,
                                in_offset=rt(0.25), out_offset=rt(0.25)))
v.append(clip('b.mp4', 1, 4, 10))
otio.adapters.write_to_file(tl, 'edit.otio')                          # Resolve 18.5+, Premiere 25.6+
otio.adapters.write_to_file(tl, 'edit.xml', adapter_name='fcp_xml')   # pip install otio-fcp-adapter
```
In the test the FCP7 XML kept the dissolve (`<transitionitem>` with `Cross Dissolve`), while `otio-fcpx-xml-adapter` (`fcpx_xml`) wrote the clips but dropped the transition. The FCP XML adapter also needs `available_range` on every media reference. CLI: `otioconvert -i edit.otio -o edit.xml -O fcp_xml`. Remotion projects can use the `remotion-opentimeline` agent skill (Remotion transitions are not exported as OTIO transitions).

Sources: [OpenTimelineIO: timeline structure (Transition)](https://opentimelineio.readthedocs.io/en/latest/tutorials/otio-timeline-structure.html) · [Remotion: export to OpenTimelineIO](https://www.remotion.dev/docs/export-opentimeline)

## CapCut Draft Automation

<a id="capcut-draft-automation"></a>Generate CapCut/JianYing drafts from code, with real CapCut transitions on each cut, then export in the app.

An editable CapCut project with Mix, Pull in, Glitch etc. already on the timeline.

- **When:** Mass-producing variants that creators finish in CapCut; teams living in CapCut.
- **Watch out:** Expecting headless export: these tools write drafts; rendering still happens in the CapCut app. Templates must have a plaintext draft_content.json (encrypted drafts are unsupported).
- **Timing:** Default per transition (e.g. Mix 1.0 s, Pull in 0.47 s) unless set
- **Also called:** pyCapCut, pyJianYingDraft, VectCut API, capcut-mate, JianYing draft, CapCut draft JSON
- **Card:** https://skills.varg.ai/skills/capcut-draft-automation/

### CapCut

pyCapCut (English CapCut; preview 0.1.x API, pin 0.0.4 for the old one). The transition is added to the earlier segment:
```python
import pycapcut as cc
from pycapcut import trange_seconds
draft = cc.DraftFolder(r'<CapCut Drafts folder>').create_draft('auto', 1080, 1920, allow_replace=True)
draft.add_track(cc.TrackType.video)
a = cc.VideoSegment('a.mp4', trange_seconds(0, duration=4))
b = cc.VideoSegment('b.mp4', trange_seconds(4, duration=4))
a.add_transition(cc.TransitionType.White_Flash, duration='0.4s')
draft.add_segment(a).add_segment(b)
draft.save()
```
pyJianYingDraft is the JianYing (Chinese) sibling with Chinese enum names (e.g. `TransitionType.叠化` for Mix). VectCutAPI (HTTP/MCP) takes `transition` and `transition_duration` (seconds) on `add_video`, resolved against `CapCut_Transition_type` names such as `Mix`, `Black_Fade`, `Pull_in`, `Glitch`, `Cube`. capcut-mate's `add_videos` takes `transition` (JianYing display name, e.g. 叠化) and `transition_duration` in microseconds. Open the draft in CapCut desktop and export manually.

Sources: [pyCapCut](https://github.com/GuanYixuan/pyCapCut) · [pyJianYingDraft](https://github.com/GuanYixuan/pyJianYingDraft) · [VectCutAPI](https://github.com/sun-guannan/VectCutAPI) · [capcut-mate (add_videos transition field)](https://github.com/Hommy-master/capcut-mate/blob/main/docs/add_videos.md) · [CapCut transition names + default durations (VectCut metadata)](https://github.com/sun-guannan/VectCutAPI/blob/main/pyJianYingDraft/metadata/capcut_transition_meta.py) · [CapCut transition names incl. Pro (pyCapCut metadata)](https://github.com/GuanYixuan/pyCapCut/blob/main/pycapcut/metadata/transition_meta.py)

## DaVinci Resolve AddTransition API

<a id="resolve-add-transition"></a>Resolve 21.1 added TimelineItem.AddTransition; earlier versions cannot add transitions by script.

Native Resolve transitions (Cross Dissolve, Fusion, OFX, audio) on a timeline built by script.

- **When:** Pipelines that assemble timelines in Resolve via Python/Lua and want dissolves without manual work.
- **Watch out:** Relying on it before 21.1; on older versions build the timeline as OTIO/FCP7 XML with transitions and import it.
- **Timing:** duration in frames (auto-calculated when omitted); needs handles on both clips
- **Also called:** Resolve scripting, TimelineItem.AddTransition, DaVinciResolveScript, Resolve API transitions
- **Card:** https://skills.varg.ai/skills/resolve-add-transition/

### Python

Resolve scripting (Python 3, run inside Resolve or with the scripting env):
```python
import DaVinciResolveScript as dvr
resolve = dvr.scriptapp('Resolve')
timeline = resolve.GetProjectManager().GetCurrentProject().GetCurrentTimeline()
items = timeline.GetItemListInTrack('video', 1)
# Resolve 21.1+: attach a dissolve to the end of the first clip, centred on the cut
items[0].AddTransition({'type': 'Cross Dissolve', 'category': 'simple', 'position': 'end', 'alignment': 'center', 'duration': 15})
```
TransitionOptions: `type` (name, e.g. 'Cross Dissolve'), `category` ('simple' | 'fusion' | 'ofx' | 'audio'), `position` ('start' | 'end'), `alignment` ('left' | 'center' | 'right'), `duration` (frames). Returns the transition TimelineItem or None. Older versions: `MediaPool.ImportTimelineFromFile('edit.otio' or FCP7 XML)`; `Timeline.Export(path, resolve.EXPORT_OTIO)` writes OTIO back out (FCPXML 1.3–1.7 export is unsupported since 18.1; 1.8–1.10 remain).

Sources: [DaVinci Resolve scripting API 21.1 README mirror](https://github.com/WheheoHu/bmd_doc/tree/main/_README_API/21_1_1) · [OpenTimelineIO: timeline structure (Transition)](https://opentimelineio.readthedocs.io/en/latest/tutorials/otio-timeline-structure.html)

## Cover and Reveal

<a id="xfade-cover-reveal"></a>B slides in over a still A (cover), or A slides away to uncover B (reveal). Variants: cover*/reveal* in four directions.

Built on [Cover Transitions](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/transitions-cover) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

One shot stays put while the other moves over or off it, like a card sliding over a card.

- **When:** Stacking scenes in a product walkthrough, deck-style explainers, card-based layouts.
- **Watch out:** Covering with a shot whose edge has no shadow — the layers look flat; add a soft shadow in HTML engines.
- **Timing:** 0.4–0.6 s, ease-out on cover, ease-in on reveal.
- **Also called:** Cover (CapCut), Uncover, Slide over
- **Card:** https://skills.varg.ai/skills/xfade-cover-reveal/

### FFmpeg

Both inputs need the same size, frame rate, timebase, SAR and pixel format (`settb=AVTB` fixes the timebase error that `fps` alone leaves). `offset` is where the transition starts on the first clip's timeline (its length minus the overlap).

```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
 "[0:v]fps=30,scale=1920:1080,setsar=1,settb=AVTB,format=yuv420p[a];[1:v]fps=30,scale=1920:1080,setsar=1,settb=AVTB,format=yuv420p[b];\
  [a][b]xfade=transition=coverleft:duration=0.5:offset=4.5[v];[0:a][1:a]acrossfade=d=0.5[a]" \
 -map "[v]" -map "[a]" out.mp4
```

### HyperFrames

`npx hyperframes add transitions-cover` shows the family; tween the top clip's x with a box-shadow on it.

### CapCut

Transitions → Slide → **Cover** / **Uncover**.

### Components

- Cover Transitions (hyperframes): `npx hyperframes add transitions-cover` · https://skills.varg.ai/component/hf.transitions-cover/

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [FFmpeg xfade gallery (trac wiki)](https://trac.ffmpeg.org/wiki/Xfade)

## Soft-Edge Wipe

<a id="xfade-smooth-wipe"></a>A wipe with a wide, feathered edge so the two shots blend along a gradient. Variants: smoothleft/right/up/down.

Built on [Colorama Wipe](https://github.com/heygen-com/hyperframes/tree/main/registry/components/colorama-wipe) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A blurred band moves across the frame, mixing A and B inside it.

- **When:** When a hard wipe is too graphic but a dissolve is too slow: travel, landscapes, lifestyle b-roll.
- **Watch out:** Using it between two busy shots: the blend band turns to mush.
- **Timing:** 0.6–1 s.
- **Also called:** Gradient wipe, Feather wipe
- **Card:** https://skills.varg.ai/skills/xfade-smooth-wipe/

### FFmpeg

Both inputs need the same size, frame rate, timebase, SAR and pixel format (`settb=AVTB` fixes the timebase error that `fps` alone leaves). `offset` is where the transition starts on the first clip's timeline (its length minus the overlap).

```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
 "[0:v]fps=30,scale=1920:1080,setsar=1,settb=AVTB,format=yuv420p[a];[1:v]fps=30,scale=1920:1080,setsar=1,settb=AVTB,format=yuv420p[b];\
  [a][b]xfade=transition=smoothleft:duration=0.5:offset=4.5[v];[0:a][1:a]acrossfade=d=0.5[a]" \
 -map "[v]" -map "[a]" out.mp4
```

### HyperFrames

Mask the incoming clip with an animated linear-gradient: `maskImage: linear-gradient(90deg, #000 40%, transparent 60%)` and tween the mask position.

### CapCut

Transitions → Basic → **Gradient wipe**.

### Components

- Colorama Wipe (hyperframes): `npx hyperframes add colorama-wipe` · https://skills.varg.ai/component/hf.colorama-wipe/

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [FFmpeg xfade gallery (trac wiki)](https://trac.ffmpeg.org/wiki/Xfade)

## Circle Crop Through Black

<a id="xfade-circle-crop"></a>A closes to a circle on black, then B opens from it — the cartoon “that’s all folks” beat.

Built on [Iris Wipe](https://remocn.dev/r/iris-wipe.json) by Kapish Dima (remocn), MIT. The write-up and recipes are varg's.

The frame shrinks to a circle, the screen goes black, and a circle grows into the next shot.

- **When:** A playful end of scene, comedic beats, retro edits.
- **Watch out:** Using it in a serious piece; it always reads as a gag.
- **Timing:** 0.8–1.2 s.
- **Also called:** Iris out / iris in, Circle close
- **Card:** https://skills.varg.ai/skills/xfade-circle-crop/

### FFmpeg

Both inputs need the same size, frame rate, timebase, SAR and pixel format (`settb=AVTB` fixes the timebase error that `fps` alone leaves). `offset` is where the transition starts on the first clip's timeline (its length minus the overlap).

```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
 "[0:v]fps=30,scale=1920:1080,setsar=1,settb=AVTB,format=yuv420p[a];[1:v]fps=30,scale=1920:1080,setsar=1,settb=AVTB,format=yuv420p[b];\
  [a][b]xfade=transition=circlecrop:duration=0.5:offset=4.5[v];[0:a][1:a]acrossfade=d=0.5[a]" \
 -map "[v]" -map "[a]" out.mp4
```

### HyperFrames

Two clip-path tweens: `circle(75% at 50% 50%)` → `circle(0%)` on A, then the reverse on B.

### CapCut

Transitions → Mask → **Circle** twice, through a black frame.

### Components

- Iris Wipe (remocn): `npx shadcn@latest add @remocn/iris-wipe` · https://skills.varg.ai/component/remocn.iris-wipe/

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [FFmpeg xfade gallery (trac wiki)](https://trac.ffmpeg.org/wiki/Xfade)

## Box Crop Through Black

<a id="xfade-rect-crop"></a>A shrinks into a rectangle on black, B grows out of one. A boxy cousin of the iris.

The frame closes as a rectangle to black, then opens as a rectangle on the next shot.

- **When:** Tech or UI-flavoured edits, framing a screen inside a screen.
- **Watch out:** Leaving the black too long between the boxes.
- **Timing:** 0.6–1 s.
- **Also called:** Box in / box out, Rectangle mask
- **Card:** https://skills.varg.ai/skills/xfade-rect-crop/

### FFmpeg

Both inputs need the same size, frame rate, timebase, SAR and pixel format (`settb=AVTB` fixes the timebase error that `fps` alone leaves). `offset` is where the transition starts on the first clip's timeline (its length minus the overlap).

```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
 "[0:v]fps=30,scale=1920:1080,setsar=1,settb=AVTB,format=yuv420p[a];[1:v]fps=30,scale=1920:1080,setsar=1,settb=AVTB,format=yuv420p[b];\
  [a][b]xfade=transition=rectcrop:duration=0.5:offset=4.5[v];[0:a][1:a]acrossfade=d=0.5[a]" \
 -map "[v]" -map "[a]" out.mp4
```

### HyperFrames

Tween `clipPath: inset(50% 50% 50% 50%)` to `inset(0)` on B after the same move closes A.

### CapCut

Transitions → Mask → **Rectangle**.

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [FFmpeg xfade gallery (trac wiki)](https://trac.ffmpeg.org/wiki/Xfade)

## Color-Distance Blend

<a id="xfade-distance"></a>A blend that swaps pixels by how different their colours are, so similar areas change first.

Built on [Cross Warp Morph](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/cross-warp-morph) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Shapes of B emerge where A and B already share colours, then the rest follows: a soft, organic morph.

- **When:** Two shots with matching palettes or composition: sky to sky, face to face.
- **Watch out:** Using it on unrelated shots, where it looks like a muddy dissolve.
- **Timing:** 0.8–1.2 s.
- **Also called:** Morph blend
- **Card:** https://skills.varg.ai/skills/xfade-distance/

### FFmpeg

Both inputs need the same size, frame rate, timebase, SAR and pixel format (`settb=AVTB` fixes the timebase error that `fps` alone leaves). `offset` is where the transition starts on the first clip's timeline (its length minus the overlap).

```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
 "[0:v]fps=30,scale=1920:1080,setsar=1,settb=AVTB,format=yuv420p[a];[1:v]fps=30,scale=1920:1080,setsar=1,settb=AVTB,format=yuv420p[b];\
  [a][b]xfade=transition=distance:duration=0.5:offset=4.5[v];[0:a][1:a]acrossfade=d=0.5[a]" \
 -map "[v]" -map "[a]" out.mp4
```

### HyperFrames

Closest: the `cross-warp-morph` or `domain-warp-dissolve` shader transitions.

### Components

- Cross Warp Morph (hyperframes): `npx hyperframes add cross-warp-morph` · https://skills.varg.ai/component/hf.cross-warp-morph/
- Morph (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.morph/

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [FFmpeg xfade gallery (trac wiki)](https://trac.ffmpeg.org/wiki/Xfade)

## Pixel Dissolve

<a id="xfade-pixel-dissolve"></a>A dithered dissolve: B appears pixel by pixel in random noise instead of a smooth fade.

Built on [Dither Dissolve](https://remocn.dev/r/dither-dissolve.json) by Kapish Dima (remocn), MIT. The write-up and recipes are varg's.

Speckles of the new shot spread over the old one like digital noise until it is gone.

- **When:** Retro, glitchy or game-styled edits; a lo-fi alternative to a cross dissolve.
- **Watch out:** Small output sizes: below 720p the noise looks like a compression error.
- **Timing:** 0.5–0.8 s.
- **Also called:** Noise dissolve, Dither dissolve
- **Card:** https://skills.varg.ai/skills/xfade-pixel-dissolve/

### FFmpeg

Both inputs need the same size, frame rate, timebase, SAR and pixel format (`settb=AVTB` fixes the timebase error that `fps` alone leaves). `offset` is where the transition starts on the first clip's timeline (its length minus the overlap).

```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
 "[0:v]fps=30,scale=1920:1080,setsar=1,settb=AVTB,format=yuv420p[a];[1:v]fps=30,scale=1920:1080,setsar=1,settb=AVTB,format=yuv420p[b];\
  [a][b]xfade=transition=dissolve:duration=0.5:offset=4.5[v];[0:a][1:a]acrossfade=d=0.5[a]" \
 -map "[v]" -map "[a]" out.mp4
```

### HyperFrames

`npx hyperframes add ordered-dither-pass` for a Bayer dither, or `halftone-dissolve`.

### Components

- Dither Dissolve (remocn): `npx shadcn@latest add @remocn/dither-dissolve` · https://skills.varg.ai/component/remocn.dither-dissolve/
- Ordered Dither Pass (hyperframes): `npx hyperframes add ordered-dither-pass` · https://skills.varg.ai/component/hf.ordered-dither-pass/

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [FFmpeg xfade gallery (trac wiki)](https://trac.ffmpeg.org/wiki/Xfade)

## Diagonal Wipe

<a id="xfade-diagonal-wipe"></a>A wipe that enters from a corner on a diagonal. Variants: diagtl, diagtr, diagbl, diagbr.

Built on [DirectionalWarp](https://github.com/gl-transitions/gl-transitions/blob/master/transitions/DirectionalWarp.glsl) by pschroen (gl-transitions), MIT. The write-up and recipes are varg's.

A slanted edge sweeps from one corner to the opposite one.

- **When:** Sports, energetic promos, splitting attention between two subjects.
- **Watch out:** Following a diagonal wipe with a horizontal one — pick one geometry per video.
- **Timing:** 0.4–0.6 s.
- **Also called:** Diagonal (CapCut), Slash wipe
- **Card:** https://skills.varg.ai/skills/xfade-diagonal-wipe/

### FFmpeg

Both inputs need the same size, frame rate, timebase, SAR and pixel format (`settb=AVTB` fixes the timebase error that `fps` alone leaves). `offset` is where the transition starts on the first clip's timeline (its length minus the overlap).

```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
 "[0:v]fps=30,scale=1920:1080,setsar=1,settb=AVTB,format=yuv420p[a];[1:v]fps=30,scale=1920:1080,setsar=1,settb=AVTB,format=yuv420p[b];\
  [a][b]xfade=transition=diagtl:duration=0.5:offset=4.5[v];[0:a][1:a]acrossfade=d=0.5[a]" \
 -map "[v]" -map "[a]" out.mp4
```

### HyperFrames

Clip-path polygon tween from a corner, or `glt.directional-warp` for a smeared diagonal.

### Remotion

```tsx
<TransitionSeries.Transition presentation={wipe({ direction: 'from-top-left' })} timing={linearTiming({ durationInFrames: 15 })} />
```

### CapCut

Transitions → Slide → **Diagonal wipe**.

### Components

- DirectionalWarp (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.directional-warp/

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [FFmpeg xfade gallery (trac wiki)](https://trac.ffmpeg.org/wiki/Xfade) · [Remotion transition presentations](https://www.remotion.dev/docs/transitions/presentations)

## Fade Through Gray

<a id="xfade-fade-grays"></a>A drains to black-and-white, crossfades to B in gray, and B regains its colour.

Colour leaves the frame, the two shots blend in monochrome, colour comes back on the new one.

- **When:** Flashbacks, memories, moving from past to present.
- **Watch out:** Using it between two shots that are already low-saturation; nobody sees it.
- **Timing:** 0.8–1.2 s.
- **Also called:** Desaturate fade, Memory fade
- **Card:** https://skills.varg.ai/skills/xfade-fade-grays/

### FFmpeg

Both inputs need the same size, frame rate, timebase, SAR and pixel format (`settb=AVTB` fixes the timebase error that `fps` alone leaves). `offset` is where the transition starts on the first clip's timeline (its length minus the overlap).

```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
 "[0:v]fps=30,scale=1920:1080,setsar=1,settb=AVTB,format=yuv420p[a];[1:v]fps=30,scale=1920:1080,setsar=1,settb=AVTB,format=yuv420p[b];\
  [a][b]xfade=transition=fadegrays:duration=0.5:offset=4.5[v];[0:a][1:a]acrossfade=d=0.5[a]" \
 -map "[v]" -map "[a]" out.mp4
```

### HyperFrames

Tween `filter: saturate(1→0)` on A and `saturate(0→1)` on B across a short opacity overlap.

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [FFmpeg xfade gallery (trac wiki)](https://trac.ffmpeg.org/wiki/Xfade)

## Corner Wipe

<a id="xfade-corner-wipe"></a>A rectangle grows from one corner until B fills the frame. Variants: wipetl, wipetr, wipebl, wipebr.

The new shot appears as a box anchored to a corner that expands to full screen.

- **When:** Picture-in-picture moments, reveals that start from a UI corner, retro TV edits.
- **Watch out:** Starting from a corner where nothing happens in shot B.
- **Timing:** 0.5–0.7 s.
- **Also called:** Corner reveal
- **Card:** https://skills.varg.ai/skills/xfade-corner-wipe/

### FFmpeg

Both inputs need the same size, frame rate, timebase, SAR and pixel format (`settb=AVTB` fixes the timebase error that `fps` alone leaves). `offset` is where the transition starts on the first clip's timeline (its length minus the overlap).

```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
 "[0:v]fps=30,scale=1920:1080,setsar=1,settb=AVTB,format=yuv420p[a];[1:v]fps=30,scale=1920:1080,setsar=1,settb=AVTB,format=yuv420p[b];\
  [a][b]xfade=transition=wipetl:duration=0.5:offset=4.5[v];[0:a][1:a]acrossfade=d=0.5[a]" \
 -map "[v]" -map "[a]" out.mp4
```

### HyperFrames

Clip-path `inset(0 100% 100% 0)` → `inset(0)` with ease-out.

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [FFmpeg xfade gallery (trac wiki)](https://trac.ffmpeg.org/wiki/Xfade)

## Zoom Into Next

<a id="xfade-zoom-in"></a>A scales up toward the viewer and fades, revealing B — the simple FFmpeg version of a zoom transition.

Built on [Zoom Through Transition](https://github.com/heygen-com/hyperframes/tree/main/registry/components/zoom-through-transition) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

The first shot grows past the frame while the second shows through.

- **When:** A quick push forward between scenes when you can’t add motion blur.
- **Watch out:** Expecting the CapCut Zoom look: xfade’s zoomin has no blur. For the punchy version scale and blur both shots yourself (see Pull In).
- **Timing:** 0.3–0.5 s.
- **Also called:** Zoom (xfade)
- **Card:** https://skills.varg.ai/skills/xfade-zoom-in/

### FFmpeg

Both inputs need the same size, frame rate, timebase, SAR and pixel format (`settb=AVTB` fixes the timebase error that `fps` alone leaves). `offset` is where the transition starts on the first clip's timeline (its length minus the overlap).

```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
 "[0:v]fps=30,scale=1920:1080,setsar=1,settb=AVTB,format=yuv420p[a];[1:v]fps=30,scale=1920:1080,setsar=1,settb=AVTB,format=yuv420p[b];\
  [a][b]xfade=transition=zoomin:duration=0.5:offset=4.5[v];[0:a][1:a]acrossfade=d=0.5[a]" \
 -map "[v]" -map "[a]" out.mp4
```

### HyperFrames

`npx hyperframes add zoom-through-transition` or `cinematic-zoom` for the blurred version.

### CapCut

Transitions → Camera → **Zoom in** (adds blur).

### Components

- Zoom Through Transition (hyperframes): `npx hyperframes add zoom-through-transition` · https://skills.varg.ai/component/hf.zoom-through-transition/
- Cinematic Zoom (hyperframes): `npx hyperframes add cinematic-zoom` · https://skills.varg.ai/component/hf.cinematic-zoom/

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [FFmpeg xfade gallery (trac wiki)](https://trac.ffmpeg.org/wiki/Xfade)

## Wind Wipe

<a id="xfade-wind"></a>A ragged, streaky wipe that blows A off the screen. Variants: hlwind, hrwind, vuwind, vdwind.

Built on [Wind](https://github.com/gl-transitions/gl-transitions/blob/master/transitions/Wind.glsl) by gre (gl-transitions), MIT. The write-up and recipes are varg's.

The edge of the wipe is torn into horizontal streaks as if the wind took the frame.

- **When:** Travel, outdoor and action edits; a softer alternative to a whip pan.
- **Watch out:** Using it on text-heavy frames where the streaks tear the letters.
- **Timing:** 0.5–0.8 s.
- **Also called:** Streak wipe
- **Card:** https://skills.varg.ai/skills/xfade-wind/

### FFmpeg

Both inputs need the same size, frame rate, timebase, SAR and pixel format (`settb=AVTB` fixes the timebase error that `fps` alone leaves). `offset` is where the transition starts on the first clip's timeline (its length minus the overlap).

```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
 "[0:v]fps=30,scale=1920:1080,setsar=1,settb=AVTB,format=yuv420p[a];[1:v]fps=30,scale=1920:1080,setsar=1,settb=AVTB,format=yuv420p[b];\
  [a][b]xfade=transition=hlwind:duration=0.5:offset=4.5[v];[0:a][1:a]acrossfade=d=0.5[a]" \
 -map "[v]" -map "[a]" out.mp4
```

### HyperFrames

GLSL route: `glt.wind` in a WebGL harness, or HyperFrames `transitions-distortion`.

### Components

- Wind (gl-transitions): `npm install gl-transitions` · https://skills.varg.ai/component/glt.wind/
- Distortion Transitions (hyperframes): `npx hyperframes add transitions-distortion` · https://skills.varg.ai/component/hf.transitions-distortion/

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [FFmpeg xfade gallery (trac wiki)](https://trac.ffmpeg.org/wiki/Xfade)

## Fast and Slow Fades

<a id="xfade-fade-fast-slow"></a>Dissolves with a curve: fadefast commits to B early, fadeslow lingers on A. Exist in FFmpeg 7+.

Like a cross dissolve, but the mix is not linear — the new shot takes over sooner (fast) or later (slow).

- **When:** When a linear dissolve feels mushy in the middle: fadefast keeps the pace up, fadeslow holds an emotional beat.
- **Watch out:** Older FFmpeg builds (6.x and earlier) do not have these names; check `ffmpeg -h filter=xfade`.
- **Timing:** 0.5–1 s.
- **Also called:** Eased dissolve
- **Card:** https://skills.varg.ai/skills/xfade-fade-fast-slow/

### FFmpeg

Both inputs need the same size, frame rate, timebase, SAR and pixel format (`settb=AVTB` fixes the timebase error that `fps` alone leaves). `offset` is where the transition starts on the first clip's timeline (its length minus the overlap).

```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
 "[0:v]fps=30,scale=1920:1080,setsar=1,settb=AVTB,format=yuv420p[a];[1:v]fps=30,scale=1920:1080,setsar=1,settb=AVTB,format=yuv420p[b];\
  [a][b]xfade=transition=fadefast:duration=0.5:offset=4.5[v];[0:a][1:a]acrossfade=d=0.5[a]" \
 -map "[v]" -map "[a]" out.mp4
```

### Remotion

Pass an eased timing to `fade()`: `linearTiming({ durationInFrames: 20, easing: Easing.out(Easing.cubic) })`.

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [FFmpeg xfade gallery (trac wiki)](https://trac.ffmpeg.org/wiki/Xfade) · [Remotion transition presentations](https://www.remotion.dev/docs/transitions/presentations)

## Custom xfade Expression

<a id="xfade-custom-expr"></a>Write your own transition as a per-pixel expression with xfade=transition=custom:expr=…

Anything you can describe per pixel from A, B, X, Y and progress P: a checkerboard, a diagonal band, a noise threshold.

- **When:** When none of the 50+ named transitions fits and you still want a one-pass FFmpeg render.
- **Watch out:** Slow renders on long clips: the expression runs for every pixel of every frame of the overlap.
- **Timing:** As designed.
- **Also called:** xfade expr
- **Card:** https://skills.varg.ai/skills/xfade-custom-expr/

### FFmpeg

Both inputs need the same size, frame rate, timebase, SAR and pixel format (`settb=AVTB` fixes the timebase error that `fps` alone leaves). `offset` is where the transition starts on the first clip's timeline (its length minus the overlap).

```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
 "[0:v]fps=30,scale=1920:1080,setsar=1,settb=AVTB,format=yuv420p[a];[1:v]fps=30,scale=1920:1080,setsar=1,settb=AVTB,format=yuv420p[b];\
  [a][b]xfade=transition=custom:duration=0.5:offset=4.5[v];[0:a][1:a]acrossfade=d=0.5[a]" \
 -map "[v]" -map "[a]" out.mp4
```

Custom: replace `transition=…` with an expression. P runs from 1 to 0 across the overlap; A and B are the two pixel values.
```bash
# vertical bands that flip at different times
xfade=transition=custom:duration=0.8:offset=4.2:expr='if(gt(P, mod(floor(X/(W/8)),2)*0.5+0.25), A, B)'
```

Sources: [FFmpeg filters: xfade](https://ffmpeg.org/ffmpeg-filters.html#xfade) · [FFmpeg xfade gallery (trac wiki)](https://trac.ffmpeg.org/wiki/Xfade)
