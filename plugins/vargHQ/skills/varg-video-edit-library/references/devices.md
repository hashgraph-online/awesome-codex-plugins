# Device mockups

Phones, laptops, browser windows and tablets: how the device enters, holds the screen and turns in 3D. 10 takes. Browse them with previews at https://skills.varg.ai/browse/skills/devices/.

A device frame tells the viewer where the product runs; it should never hide the product. Use clean, accurate frames (browser, phone, laptop), crop recordings to the screen's exact aspect, keep moves slow and decelerating, and push into the screen quickly when detail matters.

## Browser Window Frame

<a id="browser-window-frame"></a>The web app plays inside a clean browser window with traffic lights and a URL bar on a soft backdrop.

Built on [Safari](https://github.com/magicuidesign/magicui/blob/main/apps/www/registry/magicui/safari.tsx) by magic-ui, MIT. The write-up and recipes are varg's.

Rounded window, minimal chrome, real domain in the bar, big soft shadow, 6–10% padding around it on a gradient.

- **When:** Every web product demo; it tells the viewer "this runs in your browser".
- **Watch out:** Do not use a cluttered browser with tabs, bookmarks and extensions from your own machine.
- **Timing:** Window in 0.6 s (y 40 px, scale 0.96 → 1), then hold; zoom moves happen inside the window.
- **Also called:** Safari mockup, browser chrome, web app frame
- **Card:** https://skills.varg.ai/skills/browser-window-frame/

### FFmpeg

```bash
ffmpeg -i bg.png -i rec.mp4 -i chrome.png -filter_complex "[1]scale=1500:-1[r];[0][r]overlay=210:150[a];[a][2]overlay=210:96" -shortest out.mp4
```

### HyperFrames

```bash
npx hyperframes add browser-device-stage
```
Put the screen recording `<video class="clip">` in the stage's screen slot; animate the stage wrapper for moves.

### Remotion

```tsx
// npx shadcn@latest add @magicui/safari
<div style={{width:1500}}><Safari url="app.acme.com" videoSrc={staticFile('rec.mp4')}/></div>
// keeps 1203/753 aspect; size it with the wrapper
```

### CapCut

Add the recording over a gradient background; Video → Basic: Scale 80%, add a rounded Mask; overlay a browser-bar PNG on top.

### Components

- Safari (magic-ui): `npx shadcn@latest add @magicui/safari` · https://skills.varg.ai/component/magicui.safari/
- Browser Device Stage (hyperframes): `npx hyperframes add browser-device-stage` · https://skills.varg.ai/component/hf.browser-device-stage/

Sources: [Magic UI: Safari](https://magicui.design/docs/components/safari) · [Screen Studio: auto zoom, cursor smoothing, click effects](https://screen.studio/)

## Phone Frame with Live Screen

<a id="phone-frame-live-screen"></a>A screen recording plays edge to edge inside a realistic phone frame with Dynamic Island.

Built on [iPhone](https://github.com/magicuidesign/magicui/blob/main/apps/www/registry/magicui/iphone.tsx) by magic-ui, MIT. The write-up and recipes are varg's.

Dark or titanium frame, accurate corner radius, the recording fills the screen; the phone sits slightly off-center with a shadow.

- **When:** Mobile app demos and vertical recordings shown in a 16:9 film.
- **Watch out:** Do not letterbox the recording inside the phone; crop it to the screen's exact aspect.
- **Timing:** Phone rise 0.6–0.8 s, expo.out; keep it still while the screen content plays.
- **Also called:** iPhone mockup, phone frame, mobile mockup
- **Card:** https://skills.varg.ai/skills/phone-frame-live-screen/

### HyperFrames

```bash
npx hyperframes add device-frame-stage
```
Screen slot accepts a `<video>`; animate the frame wrapper, not the video.

### Remotion

```tsx
// npx shadcn@latest add @magicui/iphone
<Iphone videoSrc={staticFile('app.mp4')} />
```

### CapCut

Stickers/Overlay: add a transparent iPhone frame PNG above the recording; scale the recording to fit the screen and apply a rounded Mask.

### Components

- iPhone (magic-ui): `npx shadcn@latest add @magicui/iphone` · https://skills.varg.ai/component/magicui.iphone/
- Device Frame Stage (hyperframes): `npx hyperframes add device-frame-stage` · https://skills.varg.ai/component/hf.device-frame-stage/

Sources: [Rotato: how to make an animated mockup](https://rotato.app/blog/animated-mockup) · [Screen Studio: auto zoom, cursor smoothing, click effects](https://screen.studio/)

## Laptop Lid Opens to Screen

<a id="laptop-lid-opens"></a>A laptop lid tilts open and the screen content lifts toward the viewer, then becomes the full frame.

Built on [Macbook Scroll](https://ui.aceternity.com/components/macbook-scroll) by aceternity, Aceternity License (free components). The write-up and recipes are varg's.

Low-angle MacBook; the lid swings up, the screen lights, and the camera pushes into the display until the UI fills the frame.

- **When:** Desktop app or web app hero reveal; a premium transition from title to product.
- **Watch out:** Do not keep the UI tiny on the laptop for long; push in within 1–2 s.
- **Timing:** Lid 0.8–1.0 s power2.out, push-in 0.8 s expo.inOut.
- **Also called:** MacBook reveal, laptop open, lid tilt
- **Card:** https://skills.varg.ai/skills/laptop-lid-opens/

### HyperFrames

```bash
npx hyperframes add macos-tahoe-liquid-glass
```
Use its camera move to push into the screen, then cut to the flat recording.

### Remotion

```tsx
const lid = interpolate(frame,[0,24],[-90,0],{extrapolateRight:'clamp',easing:Easing.out(Easing.quad)});
<div style={{transform:`perspective(1600px) rotateX(${lid}deg)`, transformOrigin:'50% 100%'}}><Screen/></div>
```

### CapCut

Use a laptop template from Templates → search "laptop mockup"; replace the screen media; keyframe Scale to push into it.

### Components

- Macbook Scroll (aceternity): `npx shadcn@latest add @aceternity/macbook-scroll` · https://skills.varg.ai/component/aceternity.macbook-scroll/
- macOS Tahoe Liquid Glass Desktop (hyperframes): `npx hyperframes add macos-tahoe-liquid-glass` · https://skills.varg.ai/component/hf.macos-tahoe-liquid-glass/

Sources: [Rotato: 14 video mockup ideas and examples](https://rotato.app/blog/mockup-video-examples)

## 3D Phone Turn

<a id="3d-phone-turn"></a>A real 3D phone model turns in space with the app playing on its screen, then faces the camera.

Built on [iPhone & MacBook 3D Showcase](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/vfx-iphone-device) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Studio-lit phone rotates 30–60° on Y with reflections sliding over the glass, landing front-on as the screen content changes.

- **When:** Mobile launches and app-store style hero shots.
- **Watch out:** Do not spin a full 360° with the screen facing away for most of the shot; the screen is the product.
- **Timing:** 1.2–2 s, power2.inOut; land front-on and hold ≥ 1 s.
- **Also called:** device spin, phone rotate, turntable
- **Card:** https://skills.varg.ai/skills/3d-phone-turn/

### HyperFrames

```bash
npx hyperframes add vfx-iphone-device
```
Real GLTF iPhone with live HTML on the screen; tween the model's rotationY on the paused timeline.

### Remotion

```tsx
// @remotion/three + a GLB phone; map the screen texture to an OffthreadVideo frame
const ry = interpolate(frame,[0,48],[-0.9,0],{extrapolateRight:'clamp',easing:Easing.inOut(Easing.quad)});
```

### CapCut

Not native; render the turn in Rotato (pick a device + template, drop the recording) and import the clip.

### Components

- iPhone & MacBook 3D Showcase (hyperframes): `npx hyperframes add vfx-iphone-device` · https://skills.varg.ai/component/hf.vfx-iphone-device/
- Product Turntable (hyperframes): `npx hyperframes add product-turntable` · https://skills.varg.ai/component/hf.product-turntable/
- Turntable (remocn): `npx shadcn@latest add @remocn/turntable` · https://skills.varg.ai/component/remocn.turntable/

Sources: [Rotato: how to make an animated mockup](https://rotato.app/blog/animated-mockup) · [Rotato: 14 video mockup ideas and examples](https://rotato.app/blog/mockup-video-examples)

## Phone, Tablet and Laptop Splay

<a id="multi-device-splay"></a>Phone, tablet and laptop fan out from one stack into a proud row, each showing the same product.

Built on [Multi Device Splay](https://github.com/heygen-com/hyperframes/tree/main/registry/components/multi-device-splay) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Devices start overlapped center, then slide and rotate into a splayed arrangement with depth and shadow.

- **When:** Cross-platform claims ("everywhere you work") and launch finales.
- **Watch out:** Do not show three different apps; the same screen across sizes is the message.
- **Timing:** Splay 0.9–1.2 s expo.out with 0.08 s stagger; hold 1.5 s.
- **Also called:** device family, cross-platform, multi-device
- **Card:** https://skills.varg.ai/skills/multi-device-splay/

### HyperFrames

```bash
npx hyperframes add multi-device-splay
```

### Remotion

```tsx
[phone,tablet,laptop].map((d,i)=>{const p=spring({frame:frame-i*3,fps,config:{damping:18}}); return <Img src={d} style={{transform:`translateX(${interpolate(p,[0,1],[0,(i-1)*520])}px) rotate(${interpolate(p,[0,1],[0,(i-1)*-4])}deg)`}}/>})
```

### CapCut

Three device overlays starting at the same position; keyframe each Position/Rotation outward with 3-frame offsets.

### Components

- Multi Device Splay (hyperframes): `npx hyperframes add multi-device-splay` · https://skills.varg.ai/component/hf.multi-device-splay/
- App Showcase (hyperframes): `npx hyperframes add app-showcase` · https://skills.varg.ai/component/hf.app-showcase/

Sources: [Bohdan Motion: breakdown of the Replit Design launch video](https://x.com/bohdanmotion/status/2083248851750728188) · [Rotato: 14 video mockup ideas and examples](https://rotato.app/blog/mockup-video-examples)

## Push Through the Screen

<a id="push-through-the-screen"></a>A phone rises into view, then the camera pushes through its screen into the full-frame UI.

Built on [Parallax Device Dive](https://github.com/heygen-com/hyperframes/tree/main/registry/components/parallax-device-dive) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

The phone grows until its screen fills the frame; bezel slides off-frame and the UI layers separate slightly as you pass through.

- **When:** Bridge from a device beauty shot into a flat UI walkthrough without a cut.
- **Watch out:** Do not push in at constant speed; accelerate in, decelerate as the UI fills the frame.
- **Timing:** Rise 0.6 s, push 0.8–1.0 s expo.inOut.
- **Also called:** screen dive, fly into phone, parallax dive
- **Card:** https://skills.varg.ai/skills/push-through-the-screen/

### HyperFrames

```bash
npx hyperframes add parallax-device-dive
```

### Remotion

```tsx
const z = interpolate(frame,[18,42],[1,4.6],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.inOut(Easing.exp)});
<AbsoluteFill style={{transform:`scale(${z})`, transformOrigin:'50% 48%'}}><PhoneWithScreen/></AbsoluteFill>
```

### CapCut

Keyframe the phone mockup Scale 100% → 460% in 0.8 s, then cut on the frame the screen fills to the raw recording.

### Components

- Parallax Device Dive (hyperframes): `npx hyperframes add parallax-device-dive` · https://skills.varg.ai/component/hf.parallax-device-dive/
- iOS 26 Liquid Glass Home Screen (hyperframes): `npx hyperframes add ios26-liquid-glass` · https://skills.varg.ai/component/hf.ios26-liquid-glass/

Sources: [zero on X: Apple-keynote launch film prompt (Screen Studio zoom, no crossfades)](https://x.com/twoclipping/status/2103835273813496100) · [Rotato: 14 video mockup ideas and examples](https://rotato.app/blog/mockup-video-examples)

## Foldable Two-Screen Reveal

<a id="foldable-two-screen"></a>A foldable phone opens to show two screens side by side — before and after, or app and result.

The device unfolds from closed to open; each half carries its own screen (image, recording or URL).

- **When:** Two-sided stories: prompt and result, editor and preview, old and new.
- **Watch out:** Do not put unrelated content on the halves; the fold should mean "these two belong together".
- **Timing:** Unfold 0.8–1.2 s power2.inOut; hold 2 s.
- **Also called:** foldable phone, duo screen, unfold reveal
- **Card:** https://skills.varg.ai/skills/foldable-two-screen/

### HyperFrames

Use the varg template (HyperFrames-compatible screens): pass each half as an image, video, HTML page or URL.

### Remotion

```bash
git clone https://github.com/vargHQ/code2video-templates && cd code2video-templates/iphone-duo-fold && bun render.ts --screen app.png
```

### CapCut

Not native; render the fold with the template and import it as a clip.

### Components

- iPhone Duo Fold (varg): `git clone https://github.com/vargHQ/code2video-templates && cd code2video-templates/iphone-duo-fold && bun render.ts --screen app.png` · https://skills.varg.ai/component/varg.iphone-duo-fold/

Sources: [Rotato: 14 video mockup ideas and examples](https://rotato.app/blog/mockup-video-examples)

## Phone in Hand Insert

<a id="phone-in-hand-insert"></a>A portrait phone held in frame shows a lock screen or app moment, as if filmed by a person.

Built on [Slack Notification Ad](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/slack-notification-ad) by HeyGen (hyperframes), Apache-2.0. The write-up and recipes are varg's.

Portrait phone, slight handheld drift, notifications or the app opening; a snappy Apple-style cut-in and out.

- **When:** Consumer apps, notification-driven products, and YouTube/TikTok sponsor inserts.
- **Watch out:** Do not freeze the phone perfectly still; a 1–2 px handheld drift sells it.
- **Timing:** Insert 3–6 s; handheld drift ±2 px, 0.5 rad/s; cut in/out on beats.
- **Also called:** hand-held phone, lock screen insert, portrait phone moment
- **Card:** https://skills.varg.ai/skills/phone-in-hand-insert/

### HyperFrames

```bash
npx hyperframes add slack-notification-ad
```
Or `device-frame-stage` + `camera-shake` (handheld preset) for any screen.

### Remotion

```tsx
const dx = Math.sin(frame/23)*2, dy = Math.cos(frame/31)*2;
<div style={{transform:`translate(${dx}px,${dy}px) rotate(${dx*0.2}deg)`}}><Iphone videoSrc={app}/></div>
```

### CapCut

Film a hand holding a green-screen phone, then Remove BG → Chroma key and place the recording under it; or use a hand-phone template.

### Components

- Slack Notification Ad (hyperframes): `npx hyperframes add slack-notification-ad` · https://skills.varg.ai/component/hf.slack-notification-ad/
- Device Frame Stage (hyperframes): `npx hyperframes add device-frame-stage` · https://skills.varg.ai/component/hf.device-frame-stage/
- Camera Shake (hyperframes): `npx hyperframes add camera-shake` · https://skills.varg.ai/component/hf.camera-shake/
- iPhone (magic-ui): `npx shadcn@latest add @magicui/iphone` · https://skills.varg.ai/component/magicui.iphone/

Sources: [Rotato: 14 video mockup ideas and examples](https://rotato.app/blog/mockup-video-examples)

## Floating Device with Soft Bob

<a id="floating-device-bob"></a>The device hangs in space and bobs and tilts very slightly so a still shot never feels frozen.

Built on [Float](https://github.com/danielpetho/fancy/blob/main/src/fancy/components/blocks/float.tsx) by fancy, MIT. The write-up and recipes are varg's.

A slow 6–10 px vertical bob with a 1–2° tilt and a shadow that breathes with it.

- **When:** Holding on a screenshot while the voiceover explains, or behind a title.
- **Watch out:** Do not bob fast or far; anything over ~12 px reads as floating debris.
- **Timing:** Loop 3–5 s, sine.inOut, amplitude 6–10 px, tilt ±1.5°.
- **Also called:** levitating mockup, float, idle bob
- **Card:** https://skills.varg.ai/skills/floating-device-bob/

### HyperFrames

```bash
npx hyperframes add drift-hold
```
Loop-exact: period divides the clip length so the last frame matches the first.

### Remotion

```tsx
const y = Math.sin(frame/fps*Math.PI*2/4)*8;
const r = Math.sin(frame/fps*Math.PI*2/4 + 1)*1.5;
```

### CapCut

Animation → Combo/Loop: "Float"/"Bounce" at a slow speed; or keyframe Position Y up and down with ease.

### Components

- Float (fancy): `npx shadcn add @fancy/float` · https://skills.varg.ai/component/fancy.float/
- Drift Hold (hyperframes): `npx hyperframes add drift-hold` · https://skills.varg.ai/component/hf.drift-hold/

Sources: [Rotato: how to make an animated mockup](https://rotato.app/blog/animated-mockup)

## macOS Desktop Stage

<a id="macos-desktop-stage"></a>A full Mac desktop with menu bar, dock and app windows sets the stage for a desktop app demo.

Built on [macOS Tahoe Liquid Glass Desktop](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/macos-tahoe-liquid-glass) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Clean wallpaper, glass menu bar, one focused app window, and native notifications sliding in from the top right.

- **When:** Native desktop apps, menu bar utilities and system-level features.
- **Watch out:** Do not show a real desktop full of personal files; build a clean stage.
- **Timing:** Window open 0.3–0.4 s (scale 0.96→1), notification slide 0.4 s, hold 3 s each.
- **Also called:** Mac desktop, desktop app window, menu bar scene
- **Card:** https://skills.varg.ai/skills/macos-desktop-stage/

### HyperFrames

```bash
npx hyperframes add macos-tahoe-liquid-glass
npx hyperframes add macos-notification
```

### Remotion

```tsx
<AbsoluteFill style={{backgroundImage:`url(${wallpaper})`}}>
  <MenuBar/><Window style={{transform:`scale(${interpolate(spring({frame,fps,config:{damping:200}}),[0,1],[0.96,1])})`}}/>
</AbsoluteFill>
```

### CapCut

Use a clean wallpaper as background, overlay the app window recording with a rounded Mask and shadow; add a notification sticker.

### Components

- macOS Tahoe Liquid Glass Desktop (hyperframes): `npx hyperframes add macos-tahoe-liquid-glass` · https://skills.varg.ai/component/hf.macos-tahoe-liquid-glass/
- macOS Notification (hyperframes): `npx hyperframes add macos-notification` · https://skills.varg.ai/component/hf.macos-notification/
- Native Notification Pop (hyperframes): `npx hyperframes add native-notification-pop` · https://skills.varg.ai/component/hf.native-notification-pop/

Sources: [Screen Studio: auto zoom, cursor smoothing, click effects](https://screen.studio/)
