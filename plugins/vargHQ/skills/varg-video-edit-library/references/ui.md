# UI walkthroughs

How a product interface appears: screen-recording zoom and pan, UI that builds itself, floating panels, 3D tilts and dashboard reveals. 12 takes. Browse them with previews at https://skills.varg.ai/browse/skills/ui/.

Show the real product UI, one action at a time, and let the camera do the work. Strong launch films spend a big share of the runtime on real screens (the X launch was ~40%), push 1.5–2× into the part being used, and keep the frame still while the action happens; 3D tilts and floating panels are seasoning for hero moments, not the whole meal.

## Zoom to the Action

<a id="zoom-to-the-action"></a>The full app establishes, then the camera pushes 1.5–2× into the part being used and eases back out.

Built on [UI Focus Zoom](https://github.com/heygen-com/hyperframes/tree/main/registry/components/ui-focus-zoom) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

One settle on the full screen, a smooth decelerating push to the button or field, a short hold, and a pull back before the next action.

- **When:** Every screen recording where text would be unreadable at full frame — which is almost all of them at 1080p.
- **Watch out:** Do not zoom on every small move; zoom on the interaction, then stay still while it happens.
- **Timing:** Push 0.6–0.9 s (power3.inOut), hold ≥ 1.2 s, release 0.5–0.7 s. Scale 1.5–2.0×.
- **Also called:** punch-in on UI, focus zoom, screen recording zoom
- **Card:** https://skills.varg.ai/skills/zoom-to-the-action/

### FFmpeg

```bash
-vf "zoompan=z='if(between(it,4,6.4),min(zoom+0.03,1.8),max(zoom-0.04,1))':x='iw*0.72-iw/zoom/2':y='ih*0.30-ih/zoom/2':d=1:s=1920x1080:fps=60"
```

### HyperFrames

```bash
npx hyperframes add ui-focus-zoom
```
```js
// animate the wrapper, never the <video> itself
tl.to("#cam",{scale:1.8,xPercent:-18,yPercent:-10,duration:0.8,ease:"power3.inOut"},4)
  .to("#cam",{scale:1,xPercent:0,yPercent:0,duration:0.6,ease:"power3.inOut"},6.4);
```

### Remotion

```tsx
// npx shadcn@latest add @remocn/stage
const z = interpolate(frame,[120,144,192,210],[1,1.8,1.8,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.inOut(Easing.cubic)});
<AbsoluteFill style={{transform:`scale(${z})`, transformOrigin:'72% 30%'}}><OffthreadVideo src={rec}/></AbsoluteFill>
```

### CapCut

Select the clip → Video → Basic → Scale/Position keyframes: 100% → 180% over 0.8 s at the click, back to 100% after; or use the "Auto zoom"/"Zoom" effect on desktop.

### Components

- UI Focus Zoom (hyperframes): `npx hyperframes add ui-focus-zoom` · https://skills.varg.ai/component/hf.ui-focus-zoom/
- Stage (remocn): `npx shadcn@latest add @remocn/stage` · https://skills.varg.ai/component/remocn.stage/
- Camera Punch-In (hyperframes): `npx hyperframes add yt-camera-move` · https://skills.varg.ai/component/hf.yt-camera-move/
- Parallax Zoom (hyperframes): `npx hyperframes add parallax-zoom` · https://skills.varg.ai/component/hf.parallax-zoom/

Sources: [Screen Studio: auto zoom, cursor smoothing, click effects](https://screen.studio/) · [Trainn: how to add zoom effects to product demo videos](https://trainn.co/answers/how-to-add-zoom-effects-to-product-demo-videos/) · [OpenScreen docs: creating demos (zoom regions from cursor dwell)](https://www.mintlify.com/siddharthvaddem/openscreen/guides/creating-demos)

## 3D Tilted Dashboard Reveal

<a id="tilted-dashboard-reveal"></a>The dashboard rises from a steep 3D tilt to flat, like a screen lifting toward the viewer.

Built on [3D UI Reveal](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/ui-3d-reveal) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Screenshot on a plane tilted ~25–40° back, with a soft shadow and glow; it rotates to 0° while scaling up and the shadow tightens.

- **When:** The hero reveal of a web app or dashboard, right after the title.
- **Watch out:** Do not tilt past ~45°; the UI text compresses and the shot reads as a gimmick.
- **Timing:** 1.0–1.4 s, expo.out; start rotateX 30°, scale 0.85, y +80 px.
- **Also called:** perspective reveal, UI tilt, dashboard hero
- **Card:** https://skills.varg.ai/skills/tilted-dashboard-reveal/

### HyperFrames

```bash
npx hyperframes add ui-3d-reveal
```
```js
tl.from("#ui",{rotationX:32,scale:0.85,y:80,transformPerspective:1600,transformOrigin:"50% 100%",duration:1.2,ease:"expo.out"},0.3);
```

### Remotion

```tsx
const p = spring({frame, fps, config:{damping:200}});
<div style={{perspective:1600}}><Img src={ui} style={{transform:`rotateX(${interpolate(p,[0,1],[32,0])}deg) scale(${interpolate(p,[0,1],[0.85,1])})`, transformOrigin:'50% 100%'}}/></div>
```

### CapCut

Overlay the screenshot; Effects → search "3D"/"perspective" or Animation In "Rotate in 3D"; add a shadow in Basic.

### Components

- 3D UI Reveal (hyperframes): `npx hyperframes add ui-3d-reveal` · https://skills.varg.ai/component/hf.ui-3d-reveal/
- Tilt Card (hyperframes): `npx hyperframes add tilt-card` · https://skills.varg.ai/component/hf.tilt-card/
- Stage (remocn): `npx shadcn@latest add @remocn/stage` · https://skills.varg.ai/component/remocn.stage/

Sources: [UX Design Bootcamp: the rise of Linear style design](https://bootcamp.uxdesign.cc/the-rise-of-linear-style-design-origins-trends-and-techniques-4fd96aab7646) · [Rotato: 14 video mockup ideas and examples](https://rotato.app/blog/mockup-video-examples)

## Floating UI Panels in Depth

<a id="floating-ui-panels"></a>The interface splits into its panels, which float apart in depth with parallax, then snap back.

Built on [Camera Rig Depth Stack](https://github.com/heygen-com/hyperframes/tree/main/registry/components/camera-rig-depth-stack) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Sidebar, main view and modal separate on the z-axis at different depths; the camera drifts so near panels move faster.

- **When:** Explain how a product is built (layers, modules) or make a static screen feel alive.
- **Watch out:** Do not separate more than 3–5 layers; more becomes a cloud of rectangles.
- **Timing:** Separate 0.8 s, drift 2–3 s linear, re-stack 0.6 s power3.inOut.
- **Also called:** exploded UI, layered panels, depth stack
- **Card:** https://skills.varg.ai/skills/floating-ui-panels/

### HyperFrames

```bash
npx hyperframes add camera-rig-depth-stack
```
Or `exploded-stack` for isometric plates with labels beside each layer.

### Remotion

```tsx
layers.map((l,i)=>{const z=interpolate(frame,[0,24],[0,i*120],{extrapolateRight:'clamp'}); return <Img src={l} style={{position:'absolute', transform:`translateZ(${z}px)`}}/>})
// parent: perspective:1800, transformStyle:'preserve-3d', rotateY drift
```

### CapCut

Cut the screenshot into layers (one PNG per panel), stack as Overlays, keyframe each Position/Scale differently for parallax.

### Components

- Camera Rig Depth Stack (hyperframes): `npx hyperframes add camera-rig-depth-stack` · https://skills.varg.ai/component/hf.camera-rig-depth-stack/
- Exploded Stack (hyperframes): `npx hyperframes add exploded-stack` · https://skills.varg.ai/component/hf.exploded-stack/
- Keyframe Scrub Stack (hyperframes): `npx hyperframes add keyframe-scrub-stack` · https://skills.varg.ai/component/hf.keyframe-scrub-stack/

Sources: [Steve Lemuel: Raycast kinetic product motion (Figma + Jitter)](https://contra.com/p/llNMeeMX-raycast-kinetic-product-motion) · [Rotato: 14 video mockup ideas and examples](https://rotato.app/blog/mockup-video-examples)

## UI Builds Itself Piece by Piece

<a id="ui-builds-itself"></a>Grey skeleton blocks pulse once, then real cards, charts and text fill in with a stagger.

Built on [Skeleton Reveal](https://github.com/heygen-com/hyperframes/tree/main/registry/components/skeleton-reveal) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Layout appears as soft placeholders, then each block cross-fades to real content top-left to bottom-right.

- **When:** Show that a product generates or loads something (AI output, a report, a dashboard).
- **Watch out:** Do not stagger 30 tiny elements individually; group into 4–8 blocks.
- **Timing:** Skeleton pulse 0.6 s, then blocks 0.3 s each, 60–100 ms stagger.
- **Also called:** skeleton to content, UI build-up, staggered UI
- **Card:** https://skills.varg.ai/skills/ui-builds-itself/

### HyperFrames

```bash
npx hyperframes add skeleton-reveal
npx hyperframes add stagger-lattice
```
Use `stagger:{each:0.08,from:"start",grid:"auto"}` on the block elements.

### Remotion

```tsx
// npx shadcn@latest add @remocn/skeleton
const loaded = frame > 20 + i*3;
```

### CapCut

Two versions of the screenshot (blank wireframe and final); cross-fade with Mask → Linear keyframed diagonally.

### Components

- Skeleton Reveal (hyperframes): `npx hyperframes add skeleton-reveal` · https://skills.varg.ai/component/hf.skeleton-reveal/
- Stagger Lattice (hyperframes): `npx hyperframes add stagger-lattice` · https://skills.varg.ai/component/hf.stagger-lattice/
- UI Skeleton (remocn): `npx shadcn@latest add @remocn/skeleton` · https://skills.varg.ai/component/remocn.skeleton/

Sources: [Trace visualization: showing users what your AI agent is doing](https://agentinterface-co.pages.dev/blog/trace-visualization-showing-users-what-ai-agent-does.html) · [Jitter: UI element templates](https://jitter.video/templates/ui-elements)

## Before/After UI Wipe

<a id="before-after-ui-wipe"></a>A divider sweeps across one screen, turning the old version into the new one underneath.

Built on [Before After Wipe](https://github.com/heygen-com/hyperframes/tree/main/registry/components/before-after-wipe) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Two aligned screenshots stacked; a thin vertical line with a handle travels left to right; labels "Before" and "After" in the corners.

- **When:** Redesigns, AI clean-ups, automation (messy spreadsheet → clean report).
- **Watch out:** Do not compare screenshots that are not pixel-aligned; any shift makes the wipe look broken.
- **Timing:** Wipe 1.0–1.5 s power2.inOut; optional pause at 50% for 0.5 s.
- **Also called:** comparison slider, split wipe, old vs new UI
- **Card:** https://skills.varg.ai/skills/before-after-ui-wipe/

### FFmpeg

```bash
ffmpeg -loop 1 -t 3 -i before.png -loop 1 -t 3 -i after.png -filter_complex "[0][1]xfade=transition=wiperight:duration=1.2:offset=1" out.mp4
```

### HyperFrames

```bash
npx hyperframes add before-after-wipe
```
Drop the two images into the block's slots; tween `--split` from 0 to 100%.

### Remotion

```tsx
const x = interpolate(frame,[0,40],[0,100],{extrapolateRight:'clamp',easing:Easing.inOut(Easing.quad)});
<Img src={after}/><Img src={before} style={{position:'absolute',inset:0,clipPath:`inset(0 0 0 ${x}%)`}}/>
```

### CapCut

Put "after" over "before"; Mask → Linear (rotated 90°) on the top clip and keyframe its position across.

### Components

- Before After Wipe (hyperframes): `npx hyperframes add before-after-wipe` · https://skills.varg.ai/component/hf.before-after-wipe/
- Comparison Split (hyperframes): `npx hyperframes add comparison-split` · https://skills.varg.ai/component/hf.comparison-split/
- Page Slide (hyperframes): `npx hyperframes add page-slide` · https://skills.varg.ai/component/hf.page-slide/

Sources: [FFmpeg filters documentation (timeline enable, drawtext, zoompan, overlay)](https://ffmpeg.org/ffmpeg-filters.html) · [Bohdan Motion: Secureframe launch video, one pain per scene](https://x.com/bohdanmotion/status/2069369111231049803)

## Card Expands Into Detail

<a id="card-expands-to-detail"></a>A small card grows into a full detail panel in one continuous shape change.

Built on [Card Resize](https://github.com/heygen-com/hyperframes/tree/main/registry/components/card-resize) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A list item's corners stretch to fill the frame while its content cross-fades to the detail layout; no cut, no fade to black.

- **When:** Move from overview to detail inside the product without losing the viewer.
- **Watch out:** Do not fade between two unrelated screenshots and call it a morph; the edges must travel.
- **Timing:** 0.5–0.7 s, power3.inOut (or spring damping ~20).
- **Also called:** shared element, modal morph, card resize
- **Card:** https://skills.varg.ai/skills/card-expands-to-detail/

### HyperFrames

```bash
npx hyperframes add card-resize
```
Or `modal-morph`: both layouts are measured once and the timeline interpolates the box.

### Remotion

```tsx
const p = spring({frame, fps, config:{damping:20}});
const box = {x:interpolate(p,[0,1],[a.x,b.x]), y:interpolate(p,[0,1],[a.y,b.y]), w:interpolate(p,[0,1],[a.w,b.w]), h:interpolate(p,[0,1],[a.h,b.h])};
```

### CapCut

Keyframe the card overlay's Scale and Position to the full-frame size, then cross-fade to the detail screenshot over the last 4 frames.

### Components

- Card Resize (hyperframes): `npx hyperframes add card-resize` · https://skills.varg.ai/component/hf.card-resize/
- Modal Morph (hyperframes): `npx hyperframes add modal-morph` · https://skills.varg.ai/component/hf.modal-morph/
- Panel Reveal (hyperframes): `npx hyperframes add panel-reveal` · https://skills.varg.ai/component/hf.panel-reveal/

Sources: [zero on X: Apple-keynote launch film prompt (Screen Studio zoom, no crossfades)](https://x.com/twoclipping/status/2103835273813496100) · [Material Design: motion duration and easing](https://m1.material.io/motion/duration-easing.html)

## Filmed Off a Monitor

<a id="filmed-off-a-monitor"></a>The UI looks filmed on a real display: slight perspective, focus falloff and glare.

Built on [Filmed Screen](https://github.com/heygen-com/hyperframes/tree/main/registry/components/filmed-screen) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

A screen plane at a gentle angle; depth of field keeps one element sharp while edges blur; soft highlight and a hint of pixel texture.

- **When:** Give a flat screen recording a cinematic, physical feel between crisp UI shots.
- **Watch out:** Do not blur the part being explained; move the focus to it.
- **Timing:** Camera drift 3–5 s linear; focus pull 0.6 s.
- **Also called:** screen with depth of field, monitor shot, physical screen
- **Card:** https://skills.varg.ai/skills/filmed-off-a-monitor/

### HyperFrames

```bash
npx hyperframes add filmed-screen
```
Point the block's focus target at the element the voiceover names.

### Remotion

```tsx
// npx shadcn@latest add @remocn/camera-lens
<div style={{transform:'perspective(1400px) rotateY(-14deg) rotateX(6deg)', filter:'contrast(1.05)'}}><OffthreadVideo src={rec}/></div>
```

### CapCut

Apply Effects → "Lens blur"/"Depth of field" with a radial focus; add a light-leak overlay at 15% opacity.

### Components

- Filmed Screen (hyperframes): `npx hyperframes add filmed-screen` · https://skills.varg.ai/component/hf.filmed-screen/
- Camera Lens (remocn): `npx shadcn@latest add @remocn/camera-lens` · https://skills.varg.ai/component/remocn.camera-lens/

Sources: [Lago: we killed our motion design job (Linear-style films, Remotion)](https://getlago.com/blog/we-killed-our-motion-design-job) · [Steve Lemuel: Raycast kinetic product motion (Figma + Jitter)](https://contra.com/p/llNMeeMX-raycast-kinetic-product-motion)

## Form Fills Itself

<a id="form-fills-itself"></a>A cursor tabs through a short form; fields type, validate and the submit button resolves to success.

Built on [Signup Flow](https://github.com/heygen-com/hyperframes/tree/main/registry/components/signup-flow) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Clean card with labeled inputs; each field focuses with a ring, types at human cadence, gets a check; button goes loading → success.

- **When:** Show how fast sign-up or setup is ("30 seconds to your first project").
- **Watch out:** Do not type real-speed long emails; keep values short and speed typing up 2–3×.
- **Timing:** Each field 0.6–1.0 s; button loading 0.4 s; success check 0.4 s.
- **Also called:** signup flow, input typing, onboarding form
- **Card:** https://skills.varg.ai/skills/form-fills-itself/

### HyperFrames

```bash
npx hyperframes add signup-flow
```
Pair with `input-feedback` for a shake on a wrong value before the correct one.

### Remotion

```tsx
// npx shadcn@latest add @remocn/signup-flow
// or compose @remocn/input + @remocn/button with state = f(frame)
```

### CapCut

Record the real form; speed up typing segments 2–3× (Speed → Normal); add click SFX.

### Components

- Signup Flow (hyperframes): `npx hyperframes add signup-flow` · https://skills.varg.ai/component/hf.signup-flow/
- UI Signup Flow (remocn): `npx shadcn@latest add @remocn/signup-flow` · https://skills.varg.ai/component/remocn.signup-flow/
- Input Feedback (hyperframes): `npx hyperframes add input-feedback` · https://skills.varg.ai/component/hf.input-feedback/

Sources: [Jitter: UI element templates](https://jitter.video/templates/ui-elements) · [Consensus: 5 tips to record the best product video](https://goconsensus.com/blog/5-crucial-tips-to-recording-the-best-product-video)

## Toggle Turns the Feature On

<a id="toggle-turns-feature-on"></a>A cursor flips a settings switch and the result appears at once elsewhere in the UI.

Built on [Settings Toggle Flow](https://github.com/heygen-com/hyperframes/tree/main/registry/components/settings-toggle-flow) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Settings row with a switch; the thumb slides with a small overshoot, the track fills with accent, and a preview updates beside it.

- **When:** Features that are one click away: dark mode, AI assist, auto-sync.
- **Watch out:** Do not show the toggle without its effect; cut or pan to what changed within 0.5 s.
- **Timing:** Thumb 0.2–0.3 s back.out(2); effect 0.3–0.5 s after.
- **Also called:** switch flip, settings toggle, enable feature
- **Card:** https://skills.varg.ai/skills/toggle-turns-feature-on/

### HyperFrames

```bash
npx hyperframes add settings-toggle-flow
```
Or `toggle-flip` for one oversized switch as a hero beat.

### Remotion

```tsx
// npx shadcn@latest add @remocn/switch
const on = spring({frame: frame-clickAt, fps, config:{damping:12, stiffness:200}});
```

### CapCut

Record the real toggle, zoom 150% on it (keyframes), and add a click SFX on the frame it flips.

### Components

- Settings Toggle Flow (hyperframes): `npx hyperframes add settings-toggle-flow` · https://skills.varg.ai/component/hf.settings-toggle-flow/
- UI Switch (remocn): `npx shadcn@latest add @remocn/switch` · https://skills.varg.ai/component/remocn.switch/
- Toggle Flip (hyperframes): `npx hyperframes add toggle-flip` · https://skills.varg.ai/component/hf.toggle-flip/

Sources: [Bohdan Motion: breakdown of the Claude Design launch video](https://x.com/bohdanmotion/status/2080610655237751033) · [Jitter: UI element templates](https://jitter.video/templates/ui-elements)

## Command Palette Pop

<a id="command-palette-pop"></a>⌘K opens a palette, a few letters filter the list, the highlight moves and Enter fires the action.

Built on [UI Command Menu](https://remocn.dev/r/command-menu.json) by Kapish Dima (remocn), MIT. The write-up and recipes are varg's.

Backdrop dims, a centered palette scales from 96%, results filter as letters type, a highlight bar slides to the pick.

- **When:** Keyboard-first tools (Raycast, Linear-style apps), power-user features.
- **Watch out:** Do not leave the palette tiny in frame; zoom to ~60% of frame width so results are readable.
- **Timing:** Open 0.2 s (scale 0.96→1), typing 60–80 ms/char, highlight slide 0.15 s, close 0.15 s.
- **Also called:** cmd+k, command menu, spotlight search
- **Card:** https://skills.varg.ai/skills/command-palette-pop/

### HyperFrames

```bash
npx hyperframes add menu-morph
```
Build the list in HTML; tween the highlight `y` between rows with `power2.out`, 0.15 s.

### Remotion

```tsx
// npx shadcn@latest add @remocn/command-menu
// npx shadcn@latest add @remocn/command-menu-item
```

### CapCut

Record the real palette; add a keystroke overlay text "⌘ K" for 0.8 s when it opens.

### Components

- UI Command Menu (remocn): `npx shadcn@latest add @remocn/command-menu` · https://skills.varg.ai/component/remocn.command-menu/
- UI Command Menu Item (remocn): `npx shadcn@latest add @remocn/command-menu-item` · https://skills.varg.ai/component/remocn.command-menu-item/
- Menu Morph (hyperframes): `npx hyperframes add menu-morph` · https://skills.varg.ai/component/hf.menu-morph/
- Keystroke (remocn): `npx shadcn@latest add @remocn/keystroke` · https://skills.varg.ai/component/remocn.keystroke/

Sources: [Steve Lemuel: Raycast kinetic product motion (Figma + Jitter)](https://contra.com/p/llNMeeMX-raycast-kinetic-product-motion) · [KeyCastr: open-source keystroke visualizer](https://github.com/keycastr/keycastr)

## Pinned Mock, Changing States

<a id="pinned-mock-changing-states"></a>One product frame stays put while tabs or captions switch it through several feature states.

Built on [Sticky Mock Swap](https://github.com/heygen-com/hyperframes/tree/main/registry/components/sticky-mock-swap) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

The mock holds center; a tab indicator slides between labels and the screen cross-fades to the matching state.

- **When:** Walk through 3–5 features quickly without re-establishing the UI each time.
- **Watch out:** Do not move the mock between states; stillness is what makes the changes readable.
- **Timing:** Indicator slide 0.3 s, screen cross-fade 0.25 s, 2–3 s per state.
- **Also called:** sticky mock, feature tabs, tabbed walkthrough
- **Card:** https://skills.varg.ai/skills/pinned-mock-changing-states/

### HyperFrames

```bash
npx hyperframes add sticky-mock-swap
npx hyperframes add tabs-slide-indicator
```

### Remotion

```tsx
// npx shadcn@latest add @remocn/tabs
const active = Math.min(states.length-1, Math.floor(frame/(fps*2.5)));
```

### CapCut

Stack the state screenshots back to back on one track with 0.25 s "Dissolve" transitions; add a tab bar overlay with a moving highlight shape.

### Components

- Sticky Mock Swap (hyperframes): `npx hyperframes add sticky-mock-swap` · https://skills.varg.ai/component/hf.sticky-mock-swap/
- Tabs Slide Indicator (hyperframes): `npx hyperframes add tabs-slide-indicator` · https://skills.varg.ai/component/hf.tabs-slide-indicator/
- Animated Background (motion-primitives): `npx motion-primitives@latest add animated-background` · https://skills.varg.ai/component/motionprimitives.animated-background/
- UI Tabs (remocn): `npx shadcn@latest add @remocn/tabs` · https://skills.varg.ai/component/remocn.tabs/

Sources: [Bohdan Motion: X launch video, 40% of runtime on real UI](https://x.com/bohdanmotion/status/2079611760894431568) · [Jitter: UI element templates](https://jitter.video/templates/ui-elements)

## Liquid Glass UI Layer

<a id="liquid-glass-ui-layer"></a>Frosted, refractive glass cards and toolbars float over a colorful scene or photo.

Built on [Liquid Glass Notification](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/liquid-glass-notification) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Rounded panels with background blur, a thin bright rim and slight edge refraction; content stays sharp on top.

- **When:** Consumer and Apple-platform products; notification or widget beats over imagery.
- **Watch out:** Do not stack glass on a flat grey background; glass needs color and detail behind it to read.
- **Timing:** Panels drift 0.5–1 s, power2.out; keep blur radius stable across frames.
- **Also called:** glass panels, frosted UI, iOS 26 glass
- **Card:** https://skills.varg.ai/skills/liquid-glass-ui-layer/

### HyperFrames

```bash
npx hyperframes add liquid-glass-notification
```
Or `liquid-glass-widgets` / `vfx-liquid-glass` for shader-based refraction.

### Remotion

```tsx
<div style={{backdropFilter:'blur(24px) saturate(1.6)', background:'rgba(255,255,255,0.18)', border:'1px solid rgba(255,255,255,0.4)', borderRadius:28}}/>
```

### CapCut

Add a rounded rectangle shape, set opacity 25%, and on the clip below apply Mask + Blur in the same area.

### Components

- Liquid Glass Notification (hyperframes): `npx hyperframes add liquid-glass-notification` · https://skills.varg.ai/component/hf.liquid-glass-notification/
- Liquid Glass (hyperframes): `npx hyperframes add vfx-liquid-glass` · https://skills.varg.ai/component/hf.vfx-liquid-glass/
- Liquid Glass Widgets (hyperframes): `npx hyperframes add liquid-glass-widgets` · https://skills.varg.ai/component/hf.liquid-glass-widgets/

Sources: [zero on X: Apple-keynote launch film prompt (Screen Studio zoom, no crossfades)](https://x.com/twoclipping/status/2103835273813496100)
