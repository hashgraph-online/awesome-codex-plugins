# Grids & carousels

Bento grids, photo carousels, marquee walls, stacked cards and filmstrips. 9 takes. Browse them with previews at https://skills.varg.ai/browse/skills/galleries/.

Grids and carousels show breadth fast; they work when one element leads and the rest give texture. Bento grids give each tile a single idea, carousels dim and shrink side items, and marquee walls never carry the message — the headline on top does.

## Bento Feature Grid

<a id="bento-feature-grid"></a>Features land in a grid of differently sized rounded tiles — one hero tile, smaller supporting ones.

Built on [Rounded Media Grid](https://github.com/heygen-com/hyperframes/tree/main/registry/blocks/mk-placeholder-grid) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Apple-style bento: 1 large + 3–5 small tiles, generous gaps, each tile one idea (icon, number or mini UI); tiles assemble in a stagger.

- **When:** Recap of features near the end, or the "everything you get" beat.
- **Watch out:** Do not fill every tile with text; one visual and ≤ 5 words per tile.
- **Timing:** Tiles 0.4–0.5 s each, 60–100 ms stagger hero-first; hold 2–3 s; optional slow camera drift.
- **Also called:** bento, feature tiles, summary grid
- **Card:** https://skills.varg.ai/skills/bento-feature-grid/

### HyperFrames

```bash
npx hyperframes add mk-placeholder-grid
```
Use the hero-plus-two / 3×2 layouts; drop media into slots; `tl.from(".cell",{y:30,opacity:0,stagger:0.08})`.

### Remotion

```tsx
<div style={{display:'grid',gridTemplateColumns:'2fr 1fr 1fr',gridTemplateRows:'1fr 1fr',gap:24}}>
  {tiles.map((t,i)=>{const s=spring({frame:frame-i*3,fps,config:{damping:200}}); return <Tile style={{opacity:s,transform:`translateY(${(1-s)*30}px)`, gridArea:t.area}}/>})}
</div>
```

### CapCut

Templates → search "bento"/"grid collage"; or Layout split-screen templates with rounded masks.

### Components

- Rounded Media Grid (hyperframes): `npx hyperframes add mk-placeholder-grid` · https://skills.varg.ai/component/hf.mk-placeholder-grid/
- Grid Card Assemble (hyperframes): `npx hyperframes add grid-card-assemble` · https://skills.varg.ai/component/hf.grid-card-assemble/
- Dynamic Grid (hyperframes): `npx hyperframes add dynamic-grid` · https://skills.varg.ai/component/hf.dynamic-grid/

Sources: [SaaSFrame: understanding the bento layout trend](https://www.saasframe.io/blog/the-bento-layout-trend) · [freeCodeCamp: bento grids in web design](https://www.freecodecamp.org/news/bento-grids-in-web-design/) · [zero on X: Apple-keynote launch film prompt (Screen Studio zoom, no crossfades)](https://x.com/twoclipping/status/2103835273813496100)

## Camera Drifts Across a Bento

<a id="camera-drifts-bento"></a>An oversized grid of screenshots fills the frame and the camera drifts diagonally across it.

Built on [Infinite Bento Pan](https://remocn.dev/r/infinite-bento-pan.json) by Kapish Dima (remocn), MIT. The write-up and recipes are varg's.

Grid larger than the frame, slight tilt, vignette on edges; tiles may lift as the camera passes.

- **When:** Montage of many outputs (templates, generated images, user projects) behind a headline.
- **Watch out:** Do not drift too fast; at more than ~5% of frame width per second, nothing registers.
- **Timing:** Constant drift 3–6 s, linear or sine.inOut; vignette 30–40% at the edges.
- **Also called:** bento pan, infinite grid pan, 3D grid fly
- **Card:** https://skills.varg.ai/skills/camera-drifts-bento/

### HyperFrames

```bash
npx hyperframes add pan-stations
```
Or animate a large grid wrapper `x`/`y` with `ease:"none"` for the whole clip.

### Remotion

```tsx
// npx shadcn@latest add @remocn/infinite-bento-pan
const x = interpolate(frame,[0,durationInFrames],[0,-400]);
const y = interpolate(frame,[0,durationInFrames],[0,-240]);
```

### CapCut

Make a big grid image; keyframe Position diagonally over the clip; add a vignette effect.

### Components

- Infinite Bento Pan (remocn): `npx shadcn@latest add @remocn/infinite-bento-pan` · https://skills.varg.ai/component/remocn.infinite-bento-pan/
- On-Scroll 3D Grid Animations (codrops): `git clone https://github.com/codrops/Scroll3DGrid` · https://skills.varg.ai/component/codrops.scroll-3d-grid/
- Pan Stations (hyperframes): `npx hyperframes add pan-stations` · https://skills.varg.ai/component/hf.pan-stations/

Sources: [SaaSFrame: understanding the bento layout trend](https://www.saasframe.io/blog/the-bento-layout-trend)

## Tilted Screenshot Wall

<a id="tilted-screenshot-wall"></a>A wall of screenshots seen at an isometric angle, columns scrolling up and down at different speeds.

Built on [3D Marquee](https://ui.aceternity.com/components/3d-marquee) by aceternity, Aceternity License (free components). The write-up and recipes are varg's.

Dozens of product screenshots in rotated columns; alternating scroll directions; a dark gradient fades the wall at the top and bottom.

- **When:** Show breadth — many templates, pages or outputs — behind a title or CTA.
- **Watch out:** Do not put readable claims on the tiles; the wall is texture, the headline is the message.
- **Timing:** Columns move 20–60 px/s, alternating directions; tilt ~55° X, −45° Z.
- **Also called:** 3D marquee, isometric wall, screenshot wall
- **Card:** https://skills.varg.ai/skills/tilted-screenshot-wall/

### HyperFrames

```bash
npx hyperframes add perspective-marquee
```
Apply `transform: rotateX(55deg) rotateZ(-45deg)` on the wall wrapper and tween each column's `y` with `ease:"none"`.

### Remotion

```tsx
// npx shadcn@latest add @aceternity/3d-marquee  (replace its motion with frame-driven translateY per column)
const y = (i%2? 1:-1) * frame * 1.2;
```

### CapCut

Collage screenshots into columns, apply Basic → 3D rotate, keyframe Position Y; or use a 3D marquee template.

### Components

- 3D Marquee (aceternity): `npx shadcn@latest add @aceternity/3d-marquee` · https://skills.varg.ai/component/aceternity.3d-marquee/
- Perspective Marquee (hyperframes): `npx hyperframes add perspective-marquee` · https://skills.varg.ai/component/hf.perspective-marquee/

Sources: [Bohdan Motion: breakdown of the Replit Design launch video](https://x.com/bohdanmotion/status/2083248851750728188)

## Stacked Cards Fan Out

<a id="stacked-cards-fan"></a>A pile of cards or photos shuffles, then fans or settles one forward into focus.

Built on [Image Stack Intro Animation](https://github.com/codrops/ImageStackGrid) by codrops, MIT (per demo repo). The write-up and recipes are varg's.

Slightly rotated stacked cards with shadows; the top card lifts, others fan behind it, then one lands framed.

- **When:** Show several examples or customers, then pick one to explore.
- **Watch out:** Do not rotate cards more than ±8°; heavy rotation looks messy, not playful.
- **Timing:** Shuffle 0.6–1 s, fan 0.5 s with 50 ms stagger, settle 0.4 s back.out(1.3).
- **Also called:** card stack, image stack, shuffle
- **Card:** https://skills.varg.ai/skills/stacked-cards-fan/

### HyperFrames

```bash
npx hyperframes add keyframe-scrub-stack
```

### Remotion

```tsx
// npx shadcn@latest add @remocn/reel
cards.map((c,i)=>{const p=spring({frame:frame-i*2,fps,config:{damping:16}}); return <Img src={c} style={{transform:`rotate(${(i-2)*4*p}deg) translateY(${-i*6}px)`}}/>})
```

### CapCut

Stack image overlays with small rotations; keyframe Position/Rotation outward with offsets.

### Components

- Image Stack Intro Animation (codrops): `git clone https://github.com/codrops/ImageStackGrid` · https://skills.varg.ai/component/codrops.image-stack-intro/
- Keyframe Scrub Stack (hyperframes): `npx hyperframes add keyframe-scrub-stack` · https://skills.varg.ai/component/hf.keyframe-scrub-stack/
- Reel (remocn): `npx shadcn@latest add @remocn/reel` · https://skills.varg.ai/component/remocn.reel/

Sources: [Jitter template: The Edit, product launch](https://jitter.video/template/the-edit-product-launch/)

## App Screens on a Rail

<a id="app-screens-on-rail"></a>Two to five app screens ride a horizontal rail: one centered and sharp, neighbors smaller and receded.

Built on [Screen Flow Carousel](https://github.com/heygen-com/hyperframes/tree/main/registry/components/screen-flow-carousel) by HeyGen (HyperFrames), Apache-2.0. The write-up and recipes are varg's.

Phone-sized screens in a row; the rail slides with momentum and snaps the next screen to center with a small overshoot.

- **When:** Walk through an app flow (onboarding → home → detail) without device frames.
- **Watch out:** Do not let side screens compete; scale them to ~80% and dim them 30–40%.
- **Timing:** Slide 0.5–0.7 s with snap overshoot (back.out 1.2); 1.5–2.5 s per screen.
- **Also called:** screen carousel, app screens, screen flow
- **Card:** https://skills.varg.ai/skills/app-screens-on-rail/

### HyperFrames

```bash
npx hyperframes add screen-flow-carousel
```
Or `velocity-throw-snap` for a fast whip to the chosen screen.

### Remotion

```tsx
const idx = interpolate(frame,[0,60,120],[0,1,2],{extrapolateRight:'clamp'});
screens.map((s,i)=>{const d=i-idx; return <Img src={s} style={{transform:`translateX(${d*420}px) scale(${1-Math.min(Math.abs(d),1)*0.2})`, opacity:1-Math.min(Math.abs(d),1)*0.35}}/>})
```

### CapCut

Place screens in a row as one long image; keyframe Position X with snaps; add a blur mask on the sides.

### Components

- Screen Flow Carousel (hyperframes): `npx hyperframes add screen-flow-carousel` · https://skills.varg.ai/component/hf.screen-flow-carousel/
- Cuboid Carousel (hyperframes): `npx hyperframes add cuboid-carousel` · https://skills.varg.ai/component/hf.cuboid-carousel/
- Velocity Throw Snap (hyperframes): `npx hyperframes add velocity-throw-snap` · https://skills.varg.ai/component/hf.velocity-throw-snap/

Sources: [Rotato: 14 video mockup ideas and examples](https://rotato.app/blog/mockup-video-examples)

## Cards Orbit in a Ring

<a id="cards-orbit-ring"></a>Image cards ride a circle, larger in front and smaller behind, sweeping fast-slow-fast.

Built on [Circling Elements](https://github.com/danielpetho/fancy/blob/main/src/fancy/components/blocks/circling-elements.tsx) by fancy, MIT. The write-up and recipes are varg's.

Cards upright on an elliptical path with depth scaling and fade; the front card pauses briefly at center.

- **When:** Showcase outputs, templates or styles in a playful but tidy way.
- **Watch out:** Do not use more than ~10 cards; the back of the ring becomes noise.
- **Timing:** One sweep 2–4 s with a slow-in at the front; depth scale 0.6–1.0.
- **Also called:** circle carousel, ring gallery, orbit carousel
- **Card:** https://skills.varg.ai/skills/cards-orbit-ring/

### HyperFrames

```bash
npx hyperframes add carousel-circle-1
```

### Remotion

```tsx
const a = interpolate(frame,[0,90],[0,Math.PI*2]);
cards.map((c,i)=>{const t=a+i*2*Math.PI/cards.length; const z=(Math.cos(t)+1)/2; return <Img src={c} style={{transform:`translateX(${Math.sin(t)*500}px) scale(${0.6+z*0.4})`, zIndex:Math.round(z*100), opacity:0.4+z*0.6}}/>})
```

### CapCut

Hard natively; render in Remotion/HyperFrames, or use a "3D carousel" template from Templates.

### Components

- Circling Elements (fancy): `npx shadcn add @fancy/circling-elements` · https://skills.varg.ai/component/fancy.circling-elements/
- Circle Carousel 1 (hyperframes): `npx hyperframes add carousel-circle-1` · https://skills.varg.ai/component/hf.carousel-circle-1/
- Box Carousel (fancy): `npx shadcn add @fancy/box-carousel` · https://skills.varg.ai/component/fancy.box-carousel/

Sources: [Rotato: 14 video mockup ideas and examples](https://rotato.app/blog/mockup-video-examples)

## Rapid Screenshot Burst

<a id="rapid-screenshot-burst"></a>Full-screen images slam in one on top of another on the beat, landing on the final hero shot.

Built on [Rapid Image Layers Animation](https://github.com/codrops/RapidLayersAnimation) by codrops, MIT (per demo repo). The write-up and recipes are varg's.

6–12 images, each held 2–4 frames, slight scale punch per layer, then the last one holds and settles.

- **When:** Hype moments: "everything you can make" or the drop in the music.
- **Watch out:** Do not hold each image so short that colors strobe; 2 frames minimum at 30 fps, avoid high-contrast flashing.
- **Timing:** 2–4 frames per image (beat-synced), final settle 0.4 s.
- **Also called:** rapid layers, flash montage, image slam
- **Card:** https://skills.varg.ai/skills/rapid-screenshot-burst/

### FFmpeg

```bash
# 0.1 s per image from a list, then concat
ffmpeg -f concat -safe 0 -i list.txt -vf "fps=30,scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080" burst.mp4
# list.txt: file 'a.jpg'\nduration 0.1 ...
```

### HyperFrames

```bash
npx hyperframes add velocity-throw-snap
```
Or stack `<img class="clip">` elements with `data-start` on each beat and `data-duration` of 2–4 frames.

### Remotion

```tsx
<Series>{imgs.map((src,i)=><Series.Sequence key={i} durationInFrames={i===imgs.length-1?30:3}><Img src={src} style={{transform:`scale(${1.06 - (frame%3)*0.02})`}}/></Series.Sequence>)}</Series>
```

### CapCut

Drop images on the track, select all → set duration 0.1 s; use Beats (auto beat markers) to align; add a zoom-in animation.

### Components

- Rapid Image Layers Animation (codrops): `git clone https://github.com/codrops/RapidLayersAnimation` · https://skills.varg.ai/component/codrops.rapid-layers-animation/
- Velocity Throw Snap (hyperframes): `npx hyperframes add velocity-throw-snap` · https://skills.varg.ai/component/hf.velocity-throw-snap/

Sources: [Jamie on X: SFX breakdown of a launch video](https://x.com/jamiesmotion/status/2110099791958982703) · [Jitter template: The Edit, product launch](https://jitter.video/template/the-edit-product-launch/)

## Opposing Marquee Rows

<a id="opposing-marquee-rows"></a>Rows of tiles scroll sideways at different speeds and directions under a title.

Built on [Simple Marquee](https://github.com/danielpetho/fancy/blob/main/src/fancy/components/blocks/simple-marquee.tsx) by fancy, MIT. The write-up and recipes are varg's.

Three rows of rounded tiles (templates, outputs) moving left, right, left at 1×, 0.7×, 1.2×; edges fade.

- **When:** Background for a title or end card that needs life without stealing focus.
- **Watch out:** Do not run rows at the same speed; offset speeds create depth.
- **Timing:** Row loops 20–40 s; in a 4 s shot rows move 10–20% of their width.
- **Also called:** marquee wall, scrolling rows, tile rows
- **Card:** https://skills.varg.ai/skills/opposing-marquee-rows/

### HyperFrames

```bash
npx hyperframes add perspective-marquee
```
Or three flat rows with `tl.to(row,{xPercent: dir*-50, duration: 30/speed, ease:"none"},0)`.

### Remotion

```tsx
const x = (r:number) => (r%2? 1:-1) * ((frame * speeds[r]) % rowW);
```

### CapCut

Three long tile strips as overlays; keyframe Position X in alternating directions; mask the edges with gradient.

### Components

- Simple Marquee (fancy): `npx shadcn add @fancy/simple-marquee` · https://skills.varg.ai/component/fancy.simple-marquee/
- Marquee (magic-ui): `npx shadcn@latest add @magicui/marquee` · https://skills.varg.ai/component/magicui.marquee/
- Perspective Marquee (hyperframes): `npx hyperframes add perspective-marquee` · https://skills.varg.ai/component/hf.perspective-marquee/

Sources: [Magic UI: Marquee](https://magicui.design/docs/components/marquee)

## Filmstrip on a Curve

<a id="filmstrip-on-curve"></a>A ribbon of thumbnails snakes along a curved path across the frame.

Built on [Marquee Along SVG Path](https://github.com/danielpetho/fancy/blob/main/src/fancy/components/blocks/marquee-along-svg-path.tsx) by fancy, MIT. The write-up and recipes are varg's.

Tiles follow an S or arc path, rotating to its tangent, with depth scaling where the curve comes forward.

- **When:** Playful brand moments, creative tools, galleries of styles.
- **Watch out:** Do not make the path cross the headline; route it behind or around text.
- **Timing:** Travel 30–60 px/s along the path; 4–8 s visible.
- **Also called:** marquee along path, curved carousel, ribbon of tiles
- **Card:** https://skills.varg.ai/skills/filmstrip-on-curve/

### HyperFrames

```bash
npx hyperframes add carousel-path-1
```
Or GSAP MotionPath on each tile with staggered `start` offsets (seek-safe on the paused timeline).

### Remotion

```tsx
const pt = path.getPointAtLength(((frame*3 + i*gap) % len));
<Img src={tile} style={{transform:`translate(${pt.x}px,${pt.y}px)`}}/>
```

### CapCut

Not native; render the ribbon in code and import, or use a curved "film strip" sticker.

### Components

- Marquee Along SVG Path (fancy): `npx shadcn add @fancy/marquee-along-svg-path` · https://skills.varg.ai/component/fancy.marquee-along-svg-path/
- Path Carousel 1 (hyperframes): `npx hyperframes add carousel-path-1` · https://skills.varg.ai/component/hf.carousel-path-1/

Sources: [Codrops: 7 must-know GSAP animation tips](https://tympanus.net/codrops/2025/09/03/7-must-know-gsap-animation-tips-for-creative-developers/)
