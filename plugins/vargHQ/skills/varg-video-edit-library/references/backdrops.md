# Backdrops

What sits behind the words and the UI: gradients, grids and dots, aurora, noise, spotlights and blurred product shots. 9 takes. Browse them with previews at https://skills.varg.ai/browse/skills/backdrops/.

A backdrop should make the product look better and never compete with it. Keep motion slow (loops of 10–20 s), saturation moderate, text areas calm, and add a little grain to big gradients; dark gradient, faint grid and spotlight looks are the SaaS standard, so give them your brand colors to stand apart.

## Slow Mesh Gradient

<a id="slow-mesh-gradient"></a>Soft brand-colored fields blend and drift slowly behind titles and UI.

Built on [Mesh Gradient Background](https://github.com/heygen-com/hyperframes/tree/main/registry/components/mesh-gradient-bg) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Three or four large blurred color fields from the brand palette, moving a few percent per second, never sharp.

- **When:** Default backdrop for product shots, titles and end cards when there is no footage.
- **Watch out:** Do not animate it fast or saturate it fully; it must sit behind UI without fighting it.
- **Timing:** Drift loop 10–20 s; movement ≤ 3% of frame per second.
- **Also called:** mesh gradient, Stripe gradient, color blobs
- **Card:** https://skills.varg.ai/skills/slow-mesh-gradient/

### FFmpeg

```bash
ffmpeg -f lavfi -i "gradients=s=1920x1080:c0=0x7C3AED:c1=0xF97316:c2=0x0B0B12:n=3:speed=0.005:d=10" -c:v libx264 bg.mp4
```

### HyperFrames

```bash
npx hyperframes add mesh-gradient-bg
```
Or `mesh-gradient` (WebGPU shader); set colors from the brand tokens.

### Remotion

```tsx
const t = frame / fps;
background:`radial-gradient(40% 50% at ${30+Math.sin(t/3)*8}% ${40+Math.cos(t/4)*6}%, #7C3AED 0%, transparent 70%), radial-gradient(45% 55% at ${70+Math.cos(t/5)*8}% 60%, #F97316 0%, transparent 70%), #0B0B12`
```

### CapCut

Background → Canvas → Gradient, or search Media → Library "gradient background" and lower its saturation.

### Components

- Mesh Gradient Background (hyperframes): `npx hyperframes add mesh-gradient-bg` · https://skills.varg.ai/component/hf.mesh-gradient-bg/
- Mesh Gradient (hyperframes): `npx hyperframes add mesh-gradient` · https://skills.varg.ai/component/hf.mesh-gradient/
- Halo (shadergradient): `npm i @shadergradient/react @react-three/fiber three three-stdlib camera-controls` · https://skills.varg.ai/component/shadergradient.halo/

Sources: [DEV: how to make animated gradients like Stripe](https://dev.to/jordienr/how-to-make-animated-gradients-like-stripe-56nh) · [UX Design Bootcamp: the rise of Linear style design](https://bootcamp.uxdesign.cc/the-rise-of-linear-style-design-origins-trends-and-techniques-4fd96aab7646)

## Aurora Behind the Title

<a id="aurora-behind-title"></a>Blurred light streaks drift sideways across a dark frame behind a centered title.

Built on [Aurora Background](https://ui.aceternity.com/components/aurora-background) by aceternity, Aceternity License (free components). The write-up and recipes are varg's.

Dark base with blue/violet/amber light bands moving slowly; the title sits in the calmest area.

- **When:** Open titles and end cards for AI and dev tools — the Linear-era dark aesthetic.
- **Watch out:** Do not use it on every scene; it is a title device, not a UI background.
- **Timing:** Cycle shortened to 8–12 s so motion reads in a 4–6 s shot.
- **Also called:** aurora background, northern lights, light streaks
- **Card:** https://skills.varg.ai/skills/aurora-behind-title/

### HyperFrames

```bash
npx hyperframes add aurora-drift
```
Loop-exact ambient drift; or `aurora` (WebGPU shader) for curtains.

### Remotion

```tsx
// npx shadcn@latest add @aceternity/aurora-background
// make the CSS keyframe seek-safe: animationPlayState:'paused', animationDelay:`-${frame/fps}s`
```

### CapCut

Media → Library: search "aurora"/"light streaks" stock; reduce brightness 20% so titles pop.

### Components

- Aurora Background (aceternity): `npx shadcn@latest add @aceternity/aurora-background` · https://skills.varg.ai/component/aceternity.aurora-background/
- Aurora Drift (hyperframes): `npx hyperframes add aurora-drift` · https://skills.varg.ai/component/hf.aurora-drift/
- Aurora (react-bits): `npx shadcn@latest add @react-bits/Aurora-JS-CSS` · https://skills.varg.ai/component/reactbits.aurora/

Sources: [UX Design Bootcamp: the rise of Linear style design](https://bootcamp.uxdesign.cc/the-rise-of-linear-style-design-origins-trends-and-techniques-4fd96aab7646) · [Anthony Hobday: a critique of the Linear website](https://anthonyhobday.com/blog/20230119.html)

## Faint Grid or Dot Field

<a id="faint-grid-field"></a>A very faint line grid or dot field gives structure behind UI and code, with a soft radial fade.

Built on [Flickering Grid](https://github.com/magicuidesign/magicui/blob/main/apps/www/registry/magicui/flickering-grid.tsx) by magic-ui, MIT. The write-up and recipes are varg's.

1 px lines at 4–8% opacity on a ~40 px module, or twinkling dots; fades out toward the edges or behind the hero.

- **When:** Developer and infra products; diagrams and code scenes that need a technical floor.
- **Watch out:** Do not leave the grid at uniform full opacity behind text; fade it where the content sits.
- **Timing:** Static or slow twinkle (2–4 s period); optional parallax 1–2% with camera moves.
- **Also called:** grid background, dot grid, blueprint grid
- **Card:** https://skills.varg.ai/skills/faint-grid-field/

### FFmpeg

```bash
ffmpeg -f lavfi -i "color=c=0x0A0A0A:s=1920x1080:d=10,drawgrid=w=40:h=40:t=1:c=white@0.06" grid.mp4
```

### HyperFrames

```bash
npx hyperframes add dynamic-grid
```
Driven by CSS variables; tween `--cell` or `--opacity` on the timeline if it should breathe.

### Remotion

```tsx
<AbsoluteFill style={{backgroundImage:'linear-gradient(#ffffff0f 1px,transparent 1px),linear-gradient(90deg,#ffffff0f 1px,transparent 1px)', backgroundSize:'40px 40px', maskImage:'radial-gradient(ellipse at center,#000 30%,transparent 75%)'}}/>
```

### CapCut

Search Media → Library "grid background"; set Opacity 20–30% over a dark solid.

### Components

- Flickering Grid (magic-ui): `npx shadcn@latest add @magicui/flickering-grid` · https://skills.varg.ai/component/magicui.flickering-grid/
- Graph Paper (hero-patterns): `curl -LO https://heropatterns.com/svg/graph-paper.zip` · https://skills.varg.ai/component/heropatterns.graph-paper/
- Dynamic Grid (hyperframes): `npx hyperframes add dynamic-grid` · https://skills.varg.ai/component/hf.dynamic-grid/

Sources: [Setproduct: the Vercel aesthetic, blueprint grid design](https://www.setproduct.com/blog/complete-guide-to-blueprint-grid-design) · [Vercel: designing and building the Vercel Ship platform](https://vercel.com/blog/designing-and-building-the-vercel-ship-conference-platform)

## Spotlight From Above

<a id="spotlight-from-above"></a>Soft light cones fall from the top of a dark frame onto the product or title.

Built on [Spotlight New](https://ui.aceternity.com/components/spotlight-new) by aceternity, Aceternity License (free components). The write-up and recipes are varg's.

One or two wide, blurred white cones from the top corners, swaying a few degrees; the subject sits in the pool of light.

- **When:** Hero reveals, premium product moments, keynote-style titles.
- **Watch out:** Do not light the edges brighter than the subject; the pool of light goes where the eye should go.
- **Timing:** Sway loop 6–10 s; fade-in of the light 0.8–1.2 s before the subject appears.
- **Also called:** light cone, lamp effect, top light
- **Card:** https://skills.varg.ai/skills/spotlight-from-above/

### HyperFrames

```bash
npx hyperframes add godrays
```
Or layer two blurred conic gradients and tween their `rotation` ±4° with `sine.inOut`.

### Remotion

```tsx
// npx shadcn@latest add @aceternity/spotlight-new  (drive sway from frame)
const r = Math.sin(frame/fps*Math.PI*2/8)*4;
```

### CapCut

Effects → Lighting → "Spotlight"/"Light beam"; place above the subject; lower intensity.

### Components

- Spotlight New (aceternity): `npx shadcn@latest add @aceternity/spotlight-new` · https://skills.varg.ai/component/aceternity.spotlight-new/
- Lamp Effect (aceternity): `npx shadcn@latest add @aceternity/lamp` · https://skills.varg.ai/component/aceternity.lamp-effect/
- Light Rays (react-bits): `npx shadcn@latest add @react-bits/LightRays-JS-CSS` · https://skills.varg.ai/component/reactbits.light-rays/

Sources: [UX Design Bootcamp: the rise of Linear style design](https://bootcamp.uxdesign.cc/the-rise-of-linear-style-design-origins-trends-and-techniques-4fd96aab7646)

## Film Grain Over Gradient

<a id="film-grain-over-gradient"></a>A fine animated grain sits over the gradient so it feels printed, removes banding and looks less digital.

Built on [Grain Overlay](https://github.com/heygen-com/hyperframes/tree/main/registry/components/grain-overlay) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Subtle monochrome noise at 4–8% opacity, crawling each frame; colors underneath stay unchanged.

- **When:** Any gradient-heavy film; especially warm, editorial or retro brands.
- **Watch out:** Do not push grain above ~10% on UI shots; it softens text and kills compression.
- **Timing:** Regenerate grain every frame (or every 2 frames for a filmic feel).
- **Also called:** grainy gradient, noise texture, grain overlay
- **Card:** https://skills.varg.ai/skills/film-grain-over-gradient/

### FFmpeg

```bash
-vf "noise=alls=12:allf=t+u"
```

### HyperFrames

```bash
npx hyperframes add grain-overlay
```

### Remotion

```tsx
<svg width="100%" height="100%" style={{position:'absolute',opacity:0.06,mixBlendMode:'overlay'}}><filter id="n"><feTurbulence baseFrequency="0.9" seed={frame}/></filter><rect width="100%" height="100%" filter="url(#n)"/></svg>
```

### CapCut

Effects → search "grain"/"film"; set intensity low (10–20).

### Components

- Grain Overlay (hyperframes): `npx hyperframes add grain-overlay` · https://skills.varg.ai/component/hf.grain-overlay/
- Noise (react-bits): `npx shadcn@latest add @react-bits/Noise-JS-CSS` · https://skills.varg.ai/component/reactbits.noise/
- Nighty night (shadergradient): `npm i @shadergradient/react @react-three/fiber three three-stdlib camera-controls` · https://skills.varg.ai/component/shadergradient.nighty-night/

Sources: [Bram.us: grainy gradients](https://www.bram.us/2021/09/16/grainy-gradients) · [fffuel gggrain: SVG grainy gradient generator](https://fffuel.co/gggrain/)

## Blurred Product Behind Text

<a id="blurred-product-behind"></a>The product UI itself, heavily blurred and dimmed, becomes the backdrop for a title or quote.

Built on [Backdrop](https://remocn.dev/r/backdrop.json) by Kapish Dima (remocn), MIT. The write-up and recipes are varg's.

A screenshot at 20–40 px blur and 50–60% brightness with a vignette; title sharp on top; the UI shape is still recognizable.

- **When:** Transitions between demo and title so the film stays inside the product's colors.
- **Watch out:** Do not blur so little that UI text is half-readable; it distracts more than either sharp or fully soft.
- **Timing:** Blur in 0.4–0.6 s from the sharp shot (rack focus), hold, unblur into the next demo.
- **Also called:** blur of UI, frosted product, UI as backdrop
- **Card:** https://skills.varg.ai/skills/blurred-product-behind/

### FFmpeg

```bash
-vf "gblur=sigma=24,eq=brightness=-0.25,vignette=PI/5"
```

### HyperFrames

```bash
npx hyperframes add vignette
```
`tl.to("#ui",{filter:"blur(28px) brightness(0.55)",duration:0.5,ease:"power2.inOut"},t)` then fade the title in.

### Remotion

```tsx
// npx shadcn@latest add @remocn/backdrop
const b = interpolate(frame,[0,15],[0,28],{extrapolateRight:'clamp'});
<Img src={ui} style={{filter:`blur(${b}px) brightness(${1-b/60})`}}/>
```

### CapCut

Duplicate the UI clip; on the copy apply Effects → "Blur" (strong) + Adjust → Brightness −30; put the title on top.

### Components

- Backdrop (remocn): `npx shadcn@latest add @remocn/backdrop` · https://skills.varg.ai/component/remocn.backdrop/
- Vignette (hyperframes): `npx hyperframes add vignette` · https://skills.varg.ai/component/hf.vignette/
- Background Emphasis Type (hyperframes): `npx hyperframes add mk-emphasis-type` · https://skills.varg.ai/component/hf.mk-emphasis-type/

Sources: [UX Design Bootcamp: the rise of Linear style design](https://bootcamp.uxdesign.cc/the-rise-of-linear-style-design-origins-trends-and-techniques-4fd96aab7646) · [Lago: we killed our motion design job (Linear-style films, Remotion)](https://getlago.com/blog/we-killed-our-motion-design-job)

## Perspective Grid Tunnel

<a id="perspective-grid-tunnel"></a>A card or title floats in a perspective tunnel or floor grid while light streaks race along the lines.

Built on [Warp Background](https://github.com/magicuidesign/magicui/blob/main/apps/www/registry/magicui/warp-background.tsx) by magic-ui, MIT. The write-up and recipes are varg's.

Grid walls/floor converging to a vanishing point; thin colored streaks travel toward the camera; content centered.

- **When:** Energy and speed beats: launches, "faster" claims, transitions between sections.
- **Watch out:** Do not use it behind dense UI; the converging lines pull focus away from small text.
- **Timing:** Streaks 0.8–1.5 s each, staggered; floor scroll loop 2–4 s.
- **Also called:** warp background, retro grid, grid tunnel
- **Card:** https://skills.varg.ai/skills/perspective-grid-tunnel/

### HyperFrames

```bash
npx hyperframes add gallery-tunnel
```
Or a CSS floor grid with `rotateX(70deg)` and a timeline-driven `background-position-y`.

### Remotion

```tsx
<div style={{transform:'perspective(600px) rotateX(70deg)', backgroundImage:'linear-gradient(#f0f3 1px,transparent 1px),linear-gradient(90deg,#f0f3 1px,transparent 1px)', backgroundSize:'60px 60px', backgroundPositionY:`${frame*4}px`}}/>
```

### CapCut

Media → Library: search "retro grid"/"tunnel" loops; put the product card on top with a glow.

### Components

- Warp Background (magic-ui): `npx shadcn@latest add @magicui/warp-background` · https://skills.varg.ai/component/magicui.warp-background/
- Retro Grid (magic-ui): `npx shadcn@latest add @magicui/retro-grid` · https://skills.varg.ai/component/magicui.retro-grid/
- Gallery Tunnel (hyperframes): `npx hyperframes add gallery-tunnel` · https://skills.varg.ai/component/hf.gallery-tunnel/

Sources: [Setproduct: the Vercel aesthetic, blueprint grid design](https://www.setproduct.com/blog/complete-guide-to-blueprint-grid-design)

## Brand-Color Silk Waves

<a id="brand-silk-waves"></a>Smooth silk-like folds or wave bands in brand colors flow slowly behind the content.

Built on [Silk](https://github.com/DavidHDev/react-bits/blob/main/src/content/Backgrounds/Silk/Silk.jsx) by react-bits, MIT + Commons Clause. The write-up and recipes are varg's.

Soft satin folds or broad blurred waves; one hue family, subtle highlights, slow motion.

- **When:** Consumer and creative brands; music, audio and design tools.
- **Watch out:** Do not pick more than two hues; rainbow silk reads as a screensaver.
- **Timing:** Flow speed low (one fold crossing per 4–6 s).
- **Also called:** silk background, wavy gradient, flowing bands
- **Card:** https://skills.varg.ai/skills/brand-silk-waves/

### HyperFrames

```bash
npx hyperframes add flowing-gradient
```
WebGPU shader; set the two brand colors as variables.

### Remotion

```tsx
// npx shadcn@latest add @aceternity/wavy-background  (seed its noise with frame for seek-safety)
```

### CapCut

Search Media → Library "silk"/"waves background"; apply Adjust → HSL to shift to brand hue.

### Components

- Silk (react-bits): `npx shadcn@latest add @react-bits/Silk-JS-CSS` · https://skills.varg.ai/component/reactbits.silk/
- Wavy Background (aceternity): `npx shadcn@latest add @aceternity/wavy-background` · https://skills.varg.ai/component/aceternity.wavy-background/
- Flowing Gradient (hyperframes): `npx hyperframes add flowing-gradient` · https://skills.varg.ai/component/hf.flowing-gradient/

Sources: [DEV: how to make animated gradients like Stripe](https://dev.to/jordienr/how-to-make-animated-gradients-like-stripe-56nh)

## Quiet Particle Field

<a id="quiet-particle-field"></a>Out-of-focus dots drift slowly in depth behind the content, adding life without motion noise.

Built on [Ambient](https://github.com/tsparticles/presets/blob/main/presets/ambient/src/options.ts) by tsparticles, MIT. The write-up and recipes are varg's.

Sparse soft circles of two or three sizes, low opacity, drifting upward or sideways; a faint glow line optional.

- **When:** Long holds on titles or quotes; calm sections of a film.
- **Watch out:** Do not increase density until it looks like snow; 20–60 particles on 1080p is plenty.
- **Timing:** Drift 5–20 px/s with a fixed seed so renders match.
- **Also called:** bokeh particles, ambient dots, sparkles
- **Card:** https://skills.varg.ai/skills/quiet-particle-field/

### HyperFrames

```bash
npx hyperframes add starfield
```
Seek-safe: particle positions are a function of time and seed.

### Remotion

```tsx
const rnd = (i:number)=> (Math.sin(i*999)*10000)%1;
Array.from({length:40}).map((_,i)=> <div style={{left:`${Math.abs(rnd(i))*100}%`, top:`${(Math.abs(rnd(i+7))*100 - frame*0.05*(1+i%3))%100+100}%`}}/>)
```

### CapCut

Media → Library: search "bokeh"/"particles"; Blend → Screen at 30–50% opacity over the background.

### Components

- Ambient (tsparticles): `pnpm add @tsparticles/engine @tsparticles/slim @tsparticles/preset-<name>` · https://skills.varg.ai/component/tsparticles.ambient/
- Particles (magic-ui): `npx shadcn@latest add @magicui/particles` · https://skills.varg.ai/component/magicui.particles/
- Sparkles (aceternity): `npx shadcn@latest add @aceternity/sparkles` · https://skills.varg.ai/component/aceternity.sparkles/
- Starfield (hyperframes): `npx hyperframes add starfield` · https://skills.varg.ai/component/hf.starfield/

Sources: [UX Design Bootcamp: the rise of Linear style design](https://bootcamp.uxdesign.cc/the-rise-of-linear-style-design-origins-trends-and-techniques-4fd96aab7646)
